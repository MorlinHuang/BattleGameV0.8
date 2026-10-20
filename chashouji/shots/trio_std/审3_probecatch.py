"""python3 probecatch.py <组> <skip> <ms> <tries> <out前缀>：同一窗口反复拍，哪次有格压男生脸>0 就截整条 + 存 json 后停"""
import asyncio, json, sys
from playwright.async_api import async_playwright
g, s, ms, N, out = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader'])
        for k in range(N):
            pg = await b.new_page(viewport={'width': 11600, 'height': 900})
            await pg.goto(f'http://127.0.0.1:40236/index.html?zoom=1&auto=0&v=pc{g}{k}&ammostrip=12&ammoms={ms}&ammosc=1&ammoskip={s}&ammogift=buddy&buddy={g}&noshake=1&trioprobe=1')
            await pg.wait_for_function('window.trioFaces && window.trioFaces.length >= 12', timeout=30000)
            await pg.wait_for_timeout(500)
            fc = await pg.evaluate('window.trioFaces'); fr = await pg.evaluate('window.trioFrames')
            hits = [(i + 1, f['hit']['B']) for i, f in enumerate(fc) if f['hit']['B'] > 0]
            if hits:
                await pg.locator('#stage canvas').screenshot(path=out + '.png')
                json.dump({'faces': fc, 'frames': fr}, open(out + '.json', 'w'))
                print('try', k, 'hits', hits); break
            await pg.close()
        else: print('no hit in', N)
        await b.close()
asyncio.run(main())
