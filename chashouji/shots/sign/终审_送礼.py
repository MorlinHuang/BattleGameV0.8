"""终审真实送礼：正式页不带任何参数，点真实礼物按钮（data-shop=boom，档 3），每边 3 轮：
   轮 1 新召、轮 2 在场续送、轮 3 等全员离场后再送（重抽）。每轮等到本轮三人里任一人进 throw 帧截整屏。
   用法: python3 live13.py <side: buddy|bestie> <outdir>"""
import asyncio, json, sys, time
from playwright.async_api import async_playwright
SIDE, OUT = sys.argv[1], sys.argv[2]
SD = '-1' if SIDE == 'buddy' else '1'
CREW = 'BuddyTrio' if SIDE == 'buddy' else 'BestieTrio'
STATE = f"""(() => {{ const c = {CREW}.current(); return Object.entries(c).filter(([k,x])=>x).map(([k,x]) => [k, x.id, x.m.phase(), x.m.frame()]); }})()"""

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 1000, 'height': 1800})
        errs = []
        pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.goto('http://127.0.0.1:40235/index.html')
        await pg.wait_for_timeout(9000)
        btn = pg.locator(f'button[data-shop="boom"][data-side="{SD}"]')
        label = await btn.text_content()
        log = {'side': SIDE, 'button': label, 'rounds': []}
        for rnd in (1, 2, 3):
            if rnd == 3:   # 等全员离场
                t0 = time.time()
                while await pg.evaluate(f'{CREW}.active()') and time.time() - t0 < 30: await pg.wait_for_timeout(200)
                await pg.wait_for_timeout(500)
            before = await pg.evaluate(STATE)
            await btn.click()
            t0 = time.time(); shot = None; trace = []
            await pg.wait_for_timeout(150)
            while time.time() - t0 < 25:
                st = await pg.evaluate(STATE); trace.append([round(time.time() - t0, 2), st])
                if any(f and 'throw' in str(f) for _, _, ph, f in st):
                    fn = f'{OUT}/终审_送礼_{SIDE}_{rnd}.png'
                    await pg.screenshot(path=fn, full_page=True)
                    shot = {'file': fn, 't': round(time.time() - t0, 2), 'state': st}
                    break
                await pg.wait_for_timeout(40)
            after = await pg.evaluate(STATE)
            log['rounds'].append({'round': rnd, 'before': before, 'drawn': after, 'shot': shot, 'errors_so_far': list(errs)})
            print(rnd, 'before', before, '\n  drawn', [x[1] for x in after], '\n  shot', shot and (shot['t'], shot['state']), flush=True)
            if rnd == 2: pass
            await pg.wait_for_timeout(600 if rnd == 1 else 300)
        log['errors'] = errs
        json.dump(log, open(f'{OUT}/终审_送礼_{SIDE}.json', 'w'), ensure_ascii=False, indent=1)
        print('errors', errs)
        await b.close()
asyncio.run(main())
