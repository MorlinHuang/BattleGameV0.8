"""立体感的改前 / 改后对比胶片（docs/三人组角色规范.md「立体感」）：同一组参数 + ?seed= 跑两遍，一遍 ?light=0（改前）、一遍 ?light=1（改后），
上下拼成一张、左边标「改前 / 改后」。seed 把 Math.random 定死，两遍每格抽到的人、出手时机、粒子都一样，只差光。
用法：python3 abfilm.py "<胶片参数（ammostrip=...）>" <输出.jpg> [base] [改后的 light 值，默认 1]   （桌面容器里跑；console error 两遍都打印，应为 []）"""
import asyncio, sys
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
Q, OUT = sys.argv[1], sys.argv[2]
BASE = sys.argv[3] if len(sys.argv) > 3 else 'http://127.0.0.1:40235/index.html'
AFTER = sys.argv[4] if len(sys.argv) > 4 else '1'   # 改后开哪几样：1 全开，或 shadow / grade / rim（逐项对比）


async def shot(p, q, path):
    b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader'])
    pg = await b.new_page(viewport={'width': 11600, 'height': 1800})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    await pg.goto(BASE + '?zoom=1&auto=0&' + q)
    await pg.wait_for_timeout(6000)
    await pg.locator('#stage canvas').screenshot(path=path)
    tf = await pg.evaluate('window.trioFrames || []')
    await b.close()
    return errs, tf


async def main():
    async with async_playwright() as p:
        e0, f0 = await shot(p, Q + '&light=0', OUT + '.a.png')
        e1, f1 = await shot(p, Q + '&light=' + AFTER, OUT + '.b.png')
    print('errors 改前', e0[:5], '改后', e1[:5])
    print('两遍帧名一致' if f0 == f1 else f'两遍帧名不一致！\n{f0}\n{f1}')
    a, b = Image.open(OUT + '.a.png').convert('RGB'), Image.open(OUT + '.b.png').convert('RGB')
    L = 64
    o = Image.new('RGB', (a.width + L, a.height + b.height + 8), (12, 14, 18))
    o.paste(a, (L, 0)); o.paste(b, (L, a.height + 8))
    d = ImageDraw.Draw(o)
    try: ft = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc', 28)
    except OSError: ft = ImageFont.load_default()
    for i, t in enumerate(('改前', '改后')):
        y = i * (a.height + 8) + a.height // 2
        for k, ch in enumerate(t): d.text((16, y - 34 + k * 36), ch, fill=(255, 211, 107), font=ft)
    o.save(OUT, quality=90)

asyncio.run(main())
