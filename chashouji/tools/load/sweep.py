import asyncio, sys
from playwright.async_api import async_playwright
BASE=sys.argv[1]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox','--enable-unsafe-swiftshader'])
        ctx = await b.new_context(viewport={'width':540,'height':960})
        tot=0
        for g in range(1,11):
            pg = await ctx.new_page(); errs=[]
            pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
            await pg.goto(f'{BASE}?buddy={g}&bestie={g}', wait_until='load', timeout=0); await asyncio.sleep(4)
            for k in range(3):
                await pg.evaluate('document.querySelector(\'[data-shop="boom"][data-side="1"]\').click();document.querySelector(\'[data-shop="boom"][data-side="-1"]\').click()')
                await asyncio.sleep(3.5)
            st = await pg.evaluate("JSON.stringify([BuddyTrio.all.filter(m=>m.active()).map(m=>m.cfg.id),BestieTrio.all.filter(m=>m.active()).map(m=>m.cfg.id)])")
            fr = await pg.evaluate("new Promise(r=>{let n=0;const t=performance.now();const f=()=>{n++;performance.now()-t<1000?requestAnimationFrame(f):r(n)};requestAnimationFrame(f)})")
            print(g, st, 'fps', fr, 'errors', errs[:2], flush=True); tot+=len(errs)
            await pg.close()
        print('TOTAL errors', tot)
        await b.close()
asyncio.run(main())
