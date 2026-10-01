"""首屏实测：新 Chrome 进程，CDP Network.emulateNetworkConditions 限速，记每个请求的瀑布数据 + 页面里程碑（docs/首屏加载诊断.md 第 1 节）。
用法：python3 measure.py <Mbps|0=不限> <RTT ms> <输出.json> [url]
环境变量：
  BLOCK=<正则>  匹配的请求在页面层 abort（模拟"首屏不加载这些"）
  WAITALL=1     首帧之后等到预取队列跑完（#msg 写上内容）再收尾，记 all = 全部加载完的时刻
  REVISIT=1     回访：用一个新的用户目录（磁盘缓存），先不限速完整打开一次（等预取跑完、视频缓冲到能放），再限速 reload 一次，量第二次
  REVISIT=full  同上，第一次另外把出场视频整份下进缓存（模拟上次视频都放过）
首帧前实收 rx_at_frame = 在首帧时刻之前收完的请求的实收字节；rx_all = 整段收到的。"""
import asyncio, json, os, sys, time
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
    if (T.painted != null && T.click != null && T.boot != null) clearInterval(iv);
  }, 20);
})();
"""


async def main():
    async with async_playwright() as p:
        args = ['--no-sandbox', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required']
        revisit = bool(os.environ.get('REVISIT'))
        if revisit:   # 回访用真的用户目录（磁盘缓存）：临时 context 的缓存在内存里、单条有上限，5 MB 的视频存不下，量出来的不是真用户的回访
            import tempfile
            ctx = b = await p.chromium.launch_persistent_context(tempfile.mkdtemp(prefix='ld_prof_'), executable_path='/usr/bin/google-chrome', args=args,
                                                                 viewport={'width': 540, 'height': 960})
        else:
            b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=args)
            ctx = await b.new_context(viewport={'width': 540, 'height': 960})
        pg = ctx.pages[0] if revisit and ctx.pages else await ctx.new_page()   # 持久目录自带一个页签；再开一个新页签会被当成后台页（rAF / 媒体加载被节流）
        if os.environ.get('BLOCK'):
            import re
            rx = re.compile(os.environ['BLOCK'])
            await ctx.route(lambda u: bool(rx.search(u)), lambda route: route.abort())
        await pg.add_init_script(HOOK)
        cdp = await ctx.new_cdp_session(pg)
        await cdp.send('Network.enable')
        if revisit:                                 # 第一次：不限速、开缓存，完整打开、等预取跑完
            await pg.goto(URL, wait_until='commit', timeout=0)
            w = time.time()
            while time.time() - w < 300 and not (await pg.evaluate('window.__ld && window.__ld.boot')):
                await asyncio.sleep(0.5)
            # 出场视频：媒体栈只缓冲到能连续放完（canplaythrough）就停，缓存里只有前一截。模拟"上次把视频都看过了"：整份 fetch 一遍进 HTTP 缓存
            if os.environ.get('REVISIT') == 'full':
                await pg.evaluate("Promise.all([...document.querySelectorAll('video')].map(v => fetch(v.src).then(r => r.arrayBuffer())))")
            while time.time() - w < 300 and not (await pg.evaluate("[...document.querySelectorAll('video')].every(v => v.readyState >= 4)")):
                await asyncio.sleep(0.5)
            await asyncio.sleep(3)
        else:
            await cdp.send('Network.setCacheDisabled', {'cacheDisabled': True})
        if MBPS > 0:
            await cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': RTT,
                           'downloadThroughput': MBPS * 1e6 / 8, 'uploadThroughput': 2e6 / 8})
        R, t0 = {}, [None]
        def on_req(e):
            if t0[0] is None: t0[0] = e['timestamp']
            R[e['requestId']] = {'url': e['request']['url'].split('/', 3)[-1], 'type': e.get('type'), 'start': e['timestamp'], 'prio': e['request'].get('initialPriority')}
        def on_resp(e):
            r = R.get(e['requestId'])
            if r:
                h = {k.lower(): v for k, v in e['response']['headers'].items()}
                r.update(status=e['response']['status'], ttfb=e['timestamp'], proto=e['response'].get('protocol'), ce=h.get('content-encoding'),
                         cc=h.get('cache-control'), clen=int(h.get('content-length') or 0), mime=e['response'].get('mimeType'),
                         cache=e['response'].get('fromDiskCache') or e['response'].get('fromMemoryCache'))
        def on_data(e):
            r = R.get(e['requestId'])
            if r: r['rx'] = r.get('rx', 0) + e.get('encodedDataLength', 0)
        def on_fin(e):
            r = R.get(e['requestId'])
            if r: r.update(end=e['timestamp'], bytes=e['encodedDataLength'])
        def on_fail(e):
            r = R.get(e['requestId'])
            if r: r.update(end=e['timestamp'], failed=e.get('errorText'), canceled=e.get('canceled'))
        cdp.on('Network.requestWillBeSent', on_req); cdp.on('Network.responseReceived', on_resp)
        cdp.on('Network.dataReceived', on_data)
        cdp.on('Network.loadingFinished', on_fin); cdp.on('Network.loadingFailed', on_fail)
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        w0 = time.time()
        if revisit: await pg.reload(wait_until='commit', timeout=0)
        else: await pg.goto(URL, wait_until='commit', timeout=0)
        ms = {}
        while time.time() - w0 < 900:
            await asyncio.sleep(0.5)
            ms = await pg.evaluate('window.__ld || {}')
            if ms.get('painted') and ms.get('click'): break
        paint = await pg.evaluate("performance.getEntriesByType('paint').map(e => [e.name, e.startTime])")
        dcl = await pg.evaluate("(() => { const n = performance.getEntriesByType('navigation')[0]; return n ? {dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd} : null })()")
        if os.environ.get('WAITALL'):
            while time.time() - w0 < 900 and not (await pg.evaluate('window.__ld.boot')):
                await asyncio.sleep(0.5)
            ms = await pg.evaluate('window.__ld || {}')
        await asyncio.sleep(5 if os.environ.get('WAITALL') else 20)
        # 页面时间（performance.now，从导航起）↔ CDP 时间戳（秒）：导航请求 = 0
        fr = ms.get('frame') or 1e12
        ms['rx_at_frame'] = sum(r.get('rx', 0) for r in R.values() if r.get('end') and (r['end'] - t0[0]) * 1000 <= fr)
        ms['rx_all'] = sum(r.get('rx', 0) for r in R.values())
        ms['n_at_frame'] = sum(1 for r in R.values() if r.get('end') and (r['end'] - t0[0]) * 1000 <= fr)
        ms['msg'] = await pg.evaluate("document.getElementById('msg').textContent")
        json.dump({'mbps': MBPS, 'rtt': RTT, 'revisit': revisit, 'marks': ms, 'paint': paint, 'nav': dcl, 't0': t0[0], 'req': list(R.values()), 'errors': errs[:10]},
                  open(OUT, 'w'), ensure_ascii=False)
        print(OUT, 'marks', {k: (round(v) if isinstance(v, (int, float)) else v) for k, v in ms.items()}, 'paint', paint, 'n_req', len(R), 'errors', errs[:5])
        await b.close()
asyncio.run(main())
