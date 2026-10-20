import asyncio, sys
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader'])
        for s in [2.0,2.3,2.6,2.9,3.2,3.5,3.8,4.1]:
            pg = await b.new_page(viewport={'width': 1200, 'height': 900})
            await pg.goto(f'http://127.0.0.1:40236/index.html?zoom=1&auto=0&v=ia{s}&ammostrip=2&ammoms=16&ammosc=0.2&ammoskip={s}&ammogift=buddy&buddy=3&noshake=1&trioprobe=1')
            await pg.wait_for_function('window.trioFaces && window.trioFaces.length >= 2', timeout=30000)
            r = await pg.evaluate('''(() => { const c = trioProbe, x = c.getContext('2d'); const d = x.getImageData(0,0,c.width,c.height).data;
               let mx = 0, n = 0; for (let i = 3; i < d.length; i += 4) { if (d[i] > 0) n++; if (d[i] > mx) mx = d[i]; } return [mx, n, window.trioFrames.slice(-1)[0].join(), JSON.stringify(window.trioFaces.slice(-1)[0].hit)]; })()''')
            print(s, 'max alpha', r[0], '=', round(r[0]/255,3), 'px', r[1], r[2], r[3]); await pg.close()
        await b.close()
asyncio.run(main())
