"""用法: python3 probescan.py <buddy组号> <skip起> <skip止> <ms> [base]  —— 每次加载拍 12 格(不截图)，skip 按 12*ms 递进，打印每格帧名+hit"""
import asyncio, json, sys
from playwright.async_api import async_playwright
g, s0, s1, ms = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
base = sys.argv[5] if len(sys.argv) > 5 else 'http://127.0.0.1:40236/index.html'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader'])
        s = s0; out = []
        while s < s1 - 1e-6:
            pg = await b.new_page(viewport={'width': 1200, 'height': 900})
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.goto(f'{base}?zoom=1&auto=0&v=ps{g}{s}&ammostrip=12&ammoms={ms}&ammosc=0.2&ammoskip={s:.3f}&ammogift=buddy&buddy={g}&noshake=1&trioprobe=1')
            await pg.wait_for_function('window.trioFaces && window.trioFaces.length >= 12', timeout=30000)
            fr = await pg.evaluate('window.trioFrames'); fc = await pg.evaluate('window.trioFaces')
            for i in range(12):
                t = s + (i and (i * ms / 1000)) 
                out.append((round(t, 3), ' '.join(fr[i]), (fc[i] or {}).get('hit'), (fc[i] or {}).get('b')))
            if errs: print('ERR', errs[:2])
            await pg.close(); s += 12 * ms / 1000
        await b.close()
    for r in out: print(r[0], r[1], json.dumps(r[2]), r[3])
asyncio.run(main())
