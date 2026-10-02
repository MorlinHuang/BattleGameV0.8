"""连点压测：真实点礼物按钮，记每秒最大帧间隔 / 长任务 / 堆 / 粒子数 / errors，定位"频繁送礼卡死"。
用法：python3 stress.py <url> <秒> <每秒点几次> <输出.json>"""
import asyncio, json, random, sys, time
from playwright.async_api import async_playwright
URL, DUR, RATE, OUT = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
HOOK = r"""
(() => { const T = window.__st = { last: 0, gaps: [], lt: [] }; const raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = (cb) => raf((t) => { if (T.last) T.gaps.push(t - T.last); T.last = t; cb(t); });
  try { new PerformanceObserver(l => l.getEntries().forEach(e => T.lt.push([e.startTime, e.duration]))).observe({ type: 'longtask', buffered: true }); } catch (e) {}
})();"""
PROBE = r"""(() => { const T = window.__st, g = T.gaps.splice(0), lt = T.lt.splice(0);
  const m = performance.memory ? performance.memory.usedJSHeapSize / 1048576 : -1;
  const cnt = (o) => { try { return o ? (o.length ?? o.size ?? Object.keys(o).length) : null; } catch (e) { return null; } };
  return { t: performance.now(), frames: g.length, maxGap: g.length ? Math.max(...g) : null,
    p50: g.length ? g.slice().sort((a,b)=>a-b)[g.length>>1] : null, longtasks: lt, heapMB: m,
    dom: document.getElementsByTagName('*').length,
    buddy: typeof BuddyTrio !== 'undefined' ? BuddyTrio.all.filter(m => m.active()).length : null,
    bestie: typeof BestieTrio !== 'undefined' ? BestieTrio.all.filter(m => m.active()).length : null,
    g4: typeof G4L !== 'undefined' ? [G4L.members.map(m => m.peek().length), G4R.members.map(m => m.peek().length)] : null,
  }; })()"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required', '--enable-precise-memory-info'])
        pg = await (await b.new_context(viewport={'width': 540, 'height': 960})).new_page()
        await pg.add_init_script(HOOK)
        errs = []
        pg.on('pageerror', lambda e: errs.append(['pageerror', time.time(), str(e), e.stack if hasattr(e, 'stack') else '']))
        pg.on('console', lambda m: errs.append(['console', time.time(), m.text]) if m.type in ('error', 'warning') else None)
        await pg.goto(URL, wait_until='load', timeout=0)
        await asyncio.sleep(8)
        shops = ['like', 'wand', 'mirror', 'boom', 'drop']
        log, clicks, t0, nxt = [], 0, time.time(), time.time() + 1
        while time.time() - t0 < DUR:
            shop, side = random.choice(shops), random.choice([1, -1])
            try:
                await pg.evaluate(f'document.querySelector(\'[data-shop="{shop}"][data-side="{side}"]\').dispatchEvent(new PointerEvent("pointerdown",{{bubbles:true}})) || document.querySelector(\'[data-shop="{shop}"][data-side="{side}"]\').click()', timeout=5000) if False else \
                await pg.evaluate(f'document.querySelector(\'[data-shop="{shop}"][data-side="{side}"]\').click()')
                clicks += 1
            except Exception as e:
                errs.append(['click', time.time(), repr(e)[:200]])
            await asyncio.sleep(1 / RATE)
            if time.time() >= nxt:
                nxt += 1
                try:
                    s = await asyncio.wait_for(pg.evaluate(PROBE), 10); s['sec'] = round(time.time() - t0, 1); s['clicks'] = clicks
                    log.append(s); print(json.dumps({k: s[k] for k in ('sec','frames','maxGap','heapMB','buddy','bestie','g4')}), flush=True)
                except Exception as e:
                    log.append({'sec': round(time.time() - t0, 1), 'probe_timeout': repr(e)[:100]}); print('PROBE TIMEOUT', round(time.time()-t0,1), flush=True)
        # 停点后再观察 10 秒，看能不能恢复
        for i in range(10):
            await asyncio.sleep(1)
            try:
                s = await asyncio.wait_for(pg.evaluate(PROBE), 10); s['sec'] = round(time.time() - t0, 1); s['after'] = 1; log.append(s)
                print('after', json.dumps({k: s[k] for k in ('sec','frames','maxGap','heapMB')}), flush=True)
            except Exception as e:
                print('after PROBE TIMEOUT', flush=True)
        json.dump({'log': log, 'errors': errs, 'clicks': clicks}, open(OUT, 'w'), ensure_ascii=False, indent=1)
        print('errors', len(errs), json.dumps(errs[:8], ensure_ascii=False)[:2000])
        await b.close()
asyncio.run(main())
