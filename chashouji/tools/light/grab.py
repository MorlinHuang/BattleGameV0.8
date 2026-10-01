"""取画面的三层（背景 / 角色 / 特效）分别存 PNG，给 measure_lum.py 量人物和背景的亮度、饱和度（docs/三人组角色规范.md「立体感」）。
用法：python3 grab.py "<URL 参数>" <输出前缀> [base]
  走 ?live=1&liveStop=1：预热到 livet 秒停住，三张画布还在 DOM 里（胶片 ammostrip 会把三层合成一张，分不开人和背景）。
  例：python3 grab.py "live=1&livet=3&liveEvery=9&liveGA=bestie&liveGB=buddy&liveN=1&liveStop=1&buddy=B9.B17.B21&bestie=G8.G18.G28&pos=0" /tmp/g_living
输出：<前缀>_bg.png / _ch.png / _fx.png，console error 打印出来（应为 []）"""
import asyncio, base64, sys
from playwright.async_api import async_playwright
Q, OUT = sys.argv[1], sys.argv[2]
BASE = sys.argv[3] if len(sys.argv) > 3 else 'http://127.0.0.1:40235/index.html'


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 1000, 'height': 1800})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.goto(BASE + '?zoom=1&auto=0&' + Q)
        await pg.wait_for_function("document.getElementById('msg') && document.getElementById('msg').textContent", timeout=240000)
        await pg.wait_for_timeout(1500)
        for k in ('bg', 'ch', 'fx'):
            d = await pg.evaluate(f"document.getElementById('{k}').toDataURL('image/png')")
            open(f'{OUT}_{k}.png', 'wb').write(base64.b64decode(d.split(',', 1)[1]))
        print('errors', errs[:5])
        await b.close()

asyncio.run(main())
