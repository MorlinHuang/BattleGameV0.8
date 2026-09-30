"""拍三人组胶片（桌面容器里跑，docs/三人组角色规范.md 第八节）。跟 /tmp/strip.py 一样截整条胶片，另外把每一格三人组帧序列角色
画的是哪一帧（main.js 胶片分支记的 window.trioFrames）写到 <输出>.json —— drift.py 按它给每格取对应那一帧的模板。
用法：python3 film.py "<URL 参数>" <输出.png>
  例：python3 film.py "ammostrip=12&ammoms=60&ammosc=1&ammoskip=1.4&ammogift=buddy&buddy=6&noshake=1" /tmp/f_sak.png
页面上的 console error 会打印出来（验收要求为空）。"""
import asyncio, json, sys
from playwright.async_api import async_playwright


async def main(q, out):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 11600, 'height': 900})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.goto('http://127.0.0.1:40235/index.html?zoom=1&auto=0&' + q)
        await pg.wait_for_timeout(6000)
        await pg.locator('#stage canvas').screenshot(path=out)
        tf = await pg.evaluate('window.trioFrames || []')
        with open(out.rsplit('.', 1)[0] + '.json', 'w') as f: json.dump(tf, f, ensure_ascii=False)
        print('errors', errs[:5])
        for i, r in enumerate(tf): print(f'格{i + 1:2d}', ' '.join(r))
        await b.close()

asyncio.run(main(sys.argv[1], sys.argv[2]))
