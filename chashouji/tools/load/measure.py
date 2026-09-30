"""首屏实测：新 Chrome 进程（空缓存 + setCacheDisabled），CDP Network.emulateNetworkConditions 限速，记每个请求的瀑布数据 + 页面里程碑。
用法：python3 measure.py <Mbps|0=不限> <RTT ms> <输出.json> [url]"""
import asyncio, json, sys, time
from playwright.async_api import async_playwright
MBPS, RTT, OUT = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
URL = sys.argv[4] if len(sys.argv) > 4 else 'http://1.14.252.30:40235/index.html'
HOOK = r"""
(() => {
  const T = window.__ld = { raf: null, frame: null, painted: null, click: null, boot: null };
  const raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = (cb) => { if (T.raf == null) T.raf = performance.now();
    return raf((t) => { if (T.frame == null) T.frame = performance.now(); cb(t); }); };
  const iv = setInterval(() => {
    const c = document.getElementById('bg'), h = document.getElementById('hitL');
    if (T.painted == null && c) { try { const d = c.getContext('2d').getImageData(480, 600, 1, 1).data; if (d[3] > 0) T.painted = performance.now(); } catch (e) {} }
    if (T.click == null && h && h.onclick) T.click = performance.now();
    if (T.boot == null) { const m = document.getElementById('msg'); if (m && m.textContent) T.boot = performance.now(); }
    if (T.painted != null && T.click != null) clearInterval(iv);
  }, 20);
})();
"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'])
        ctx = await b.new_context(viewport={'width': 540, 'height': 960})
        pg = await ctx.new_page()
        import os, re
        if os.environ.get('BLOCK'):
            rx = re.compile(os.environ['BLOCK'])
            await ctx.route(lambda u: bool(rx.search(u)), lambda route: route.abort())
        await pg.add_init_script(HOOK)
        cdp = await ctx.new_cdp_session(pg)
        await cdp.send('Network.enable'); await cdp.send('Network.setCacheDisabled', {'cacheDisabled': True})
        if MBPS > 0:
            await cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': RTT,
                           'downloadThroughput': MBPS * 1e6 / 8, 'uploadThroughput': 2e6 / 8})
        R, t0 = {}, [None]
        def on_req(e):
            if t0[0] is None: t0[0] = e['timestamp']
            R[e['requestId']] = {'url': e['request']['url'].split('40235/')[-1], 'type': e.get('type'), 'start': e['timestamp'], 'prio': e['request'].get('initialPriority')}
        def on_resp(e):
            r = R.get(e['requestId'])
            if r:
                h = {k.lower(): v for k, v in e['response']['headers'].items()}
                r.update(status=e['response']['status'], ttfb=e['timestamp'], proto=e['response'].get('protocol'), ce=h.get('content-encoding'),
                         cc=h.get('cache-control'), clen=int(h.get('content-length') or 0), mime=e['response'].get('mimeType'), conn=h.get('connection'))
        def on_fin(e):
            r = R.get(e['requestId'])
            if r: r.update(end=e['timestamp'], bytes=e['encodedDataLength'])
        def on_fail(e):
            r = R.get(e['requestId'])
            if r: r.update(end=e['timestamp'], failed=e.get('errorText'), canceled=e.get('canceled'))
        def on_data(e):
            r = R.get(e['requestId'])
            if r: r['rx'] = r.get('rx', 0) + e.get('encodedDataLength', 0); r['last_rx'] = e['timestamp']
        cdp.on('Network.dataReceived', on_data)
        cdp.on('Network.requestWillBeSent', on_req); cdp.on('Network.responseReceived', on_resp)
        cdp.on('Network.loadingFinished', on_fin); cdp.on('Network.loadingFailed', on_fail)
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        w0 = time.time()
        await pg.goto(URL, wait_until='commit', timeout=0)
        nav = None; ms = {}
        while time.time() - w0 < 900:
            await asyncio.sleep(0.5)
            ms = await pg.evaluate('window.__ld || {}')
            if ms.get('painted') and ms.get('click'): break
        ms['navStart'] = 0
        ms['rx_at_frame'] = sum(r.get('rx', 0) for r in R.values())
        paint = await pg.evaluate("performance.getEntriesByType('paint').map(e => [e.name, e.startTime])")
        dcl = await pg.evaluate("(() => { const n = performance.getEntriesByType('navigation')[0]; return n ? {dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd} : null })()")
        tp = await pg.evaluate('performance.timeOrigin')
        after = time.time()
        await asyncio.sleep(20)   # 首屏之后 20 秒里还在下什么（视频预加载等）
        json.dump({'mbps': MBPS, 'rtt': RTT, 'marks': ms, 'paint': paint, 'nav': dcl, 't0': t0[0], 'wall_s': after - w0, 'req': list(R.values()), 'errors': errs[:5]},
                  open(OUT, 'w'), ensure_ascii=False)
        print(OUT, 'marks', {k: (round(v) if isinstance(v, (int, float)) else v) for k, v in ms.items()}, 'paint', paint, 'nav', dcl, 'n_req', len(R), 'errors', errs[:3])
        await b.close()
asyncio.run(main())
