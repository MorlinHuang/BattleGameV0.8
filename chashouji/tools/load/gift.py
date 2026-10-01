"""送礼回归（docs/首屏加载诊断.md「改后」）：真实点礼物按钮，按时间截舞台 + 记三人组 / 档 4 / 预取队列的状态，收 console error。
用法：python3 gift.py <url> <Mbps|0> <early|full> <输出前缀>
  early：空缓存、限速，首帧一出来立刻送两边档 3 + 档 4（素材多半还没到），之后 0.3~12 秒截 10 张
  early12：同上，送两边档 1 + 档 2，截 5 张（看矢量画法）
  full ：等预取队列跑完（#msg 写上），两边档 1、档 2 各一次，档 3 两边各 2 轮，档 4 两边各一次，每次送完截几张
输出：<前缀>_NN.png（舞台截图）、<前缀>.json（每张的时刻、动作、状态、errors）"""
import asyncio, json, sys, time
from playwright.async_api import async_playwright
URL, MBPS, MODE, OUT = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4]
HOOK = r"""
(() => { const T = window.__ld = { frame: null }; const raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = (cb) => raf((t) => { if (T.frame == null) T.frame = performance.now(); cb(t); }); })();
"""
STATE = r"""(() => {
  const trio = (T) => T.all.filter(m => m.active()).map(m => `${m.cfg.id}:${m.phase()}${m.ready() ? '' : '(未加载)'}${m.frame() ? '/' + m.frame() : ''}`);
  const g4 = (G) => G.members.map((m, i) => m.peek().map(b => `#${i}${b.hold ? ' 候场(视频)' : ''} t${b.t.toFixed(2)}`)).flat();
  const st = Preload.stats();
  return { t: performance.now(), buddy: trio(BuddyTrio), bestie: trio(BestieTrio), g4L: g4(G4L), g4R: g4(G4R),
           g4ready: [Preload.ready('g4L'), Preload.ready('g4R')], items: Preload.ready('items'),
           video: IntroVideo.playing(), preload: `${st.done}/${st.n}`, phase: S.phase };
})()"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'])
        ctx = await b.new_context(viewport={'width': 540, 'height': 960})
        pg = await ctx.new_page()
        await pg.add_init_script(HOOK)
        cdp = await ctx.new_cdp_session(pg)
        await cdp.send('Network.enable'); await cdp.send('Network.setCacheDisabled', {'cacheDisabled': True})
        if MBPS > 0:
            await cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 50, 'downloadThroughput': MBPS * 1e6 / 8, 'uploadThroughput': 2e6 / 8})
        errs, log, k = [], [], [0]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.goto(URL, wait_until='commit', timeout=0)
        w0 = time.time()
        while not await pg.evaluate('window.__ld.frame') and time.time() - w0 < 300: await asyncio.sleep(0.05)
        frame = await pg.evaluate('window.__ld.frame')

        async def give(shop, side, what):
            await pg.click(f'[data-shop="{shop}"][data-side="{side}"]')
            log.append({'act': what, 't': await pg.evaluate('performance.now()')})

        async def snap(note=''):
            await pg.locator('#stage').screenshot(path=f'{OUT}_{k[0]:02d}.png')
            s = await pg.evaluate(STATE); s.update(n=k[0], note=note); log.append(s); k[0] += 1

        if MODE == 'early12':     # 首帧即送档 1 + 档 2（图集还没到：ammo.js / rain.js 的矢量画法）
            await give('mirror', 1, '档2 榴莲鞋雨'); await give('mirror', -1, '档2 臭袜子足球')
            await give('wand', 1, '档1 口红'); await give('wand', -1, '档1 香蕉')
            t0 = time.time()
            for at in (0.25, 0.45, 0.65, 0.9, 1.2):
                await asyncio.sleep(max(0, at - (time.time() - t0))); await snap(f'送礼后 {at}s')
        elif MODE == 'early':
            await give('boom', 1, '档3 闺蜜'); await give('boom', -1, '档3 哥们')
            await give('drop', 1, '档4 查岗党'); await give('drop', -1, '档4 灭迹党')
            t0 = time.time()
            for at in (0.3, 0.8, 1.5, 2.5, 3.5, 5, 6.5, 8, 10, 12):
                await asyncio.sleep(max(0, at - (time.time() - t0))); await snap(f'送礼后 {at}s')
        else:
            while not await pg.evaluate("document.getElementById('msg').textContent") and time.time() - w0 < 600: await asyncio.sleep(0.5)
            await asyncio.sleep(1)
            plan = [('wand', 1, '档1 口红'), ('wand', -1, '档1 香蕉'), ('mirror', 1, '档2 榴莲鞋雨'), ('mirror', -1, '档2 臭袜子足球'),
                    ('boom', 1, '档3 闺蜜 第1轮'), ('boom', -1, '档3 哥们 第1轮'), ('boom', 1, '档3 闺蜜 第2轮'), ('boom', -1, '档3 哥们 第2轮'),
                    ('drop', 1, '档4 查岗党'), ('drop', -1, '档4 灭迹党')]
            gaps = {'wand': (0.6, 1.4), 'mirror': (0.5, 1.2), 'boom': (1.2, 3.0, 8.5), 'drop': (1.0, 3.5, 7.0)}
            for i in range(0, len(plan), 2):
                (s1, d1, w1), (s2, d2, w2) = plan[i], plan[i + 1]
                await give(s1, d1, w1); await give(s2, d2, w2)
                t0 = time.time()
                for at in gaps[s1]:
                    await asyncio.sleep(max(0, at - (time.time() - t0))); await snap(f'{w1} + {w2} 后 {at}s')
        json.dump({'url': URL, 'mbps': MBPS, 'mode': MODE, 'frame': frame, 'log': log, 'errors': errs}, open(OUT + '.json', 'w'), ensure_ascii=False, indent=1)
        print('frame', round(frame), 'errors', errs[:5])
        for e in log: print(json.dumps(e, ensure_ascii=False))
        await b.close()
asyncio.run(main())
