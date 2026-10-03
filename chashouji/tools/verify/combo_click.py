"""连送计数「×N」验收：正式页 / 测试页里真点礼物按钮（闺蜜连点、口红连点、对面香蕉），截 6 张到 /tmp/cb_1..6.png。用法：python3 combo_click.py <页面 url>（桌面里跑）"""
import asyncio, sys
from playwright.async_api import async_playwright
URL = sys.argv[1]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--enable-unsafe-swiftshader"])
        pg = await b.new_page(viewport={"width": 540, "height": 960})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(9000)
        click = lambda shop, side: pg.evaluate(f"document.querySelector('[data-shop={shop}][data-side=\"{side}\"]').click()")
        shots = []
        async def shot(n):
            await pg.locator('#stage canvas').first.screenshot(path=f"/tmp/cb_{n}.png"); shots.append(n)
        await click('boom', '1'); await pg.wait_for_timeout(120); await shot(1)
        await pg.wait_for_timeout(900); await click('boom', '1'); await pg.wait_for_timeout(60); await shot(2)
        await click('wand', '1'); await pg.wait_for_timeout(500); await click('wand', '1'); await pg.wait_for_timeout(500)
        await click('wand', '1'); await click('wand', '-1'); await pg.wait_for_timeout(500); await click('wand', '-1')
        await click('boom', '1'); await pg.wait_for_timeout(100); await shot(3)
        await pg.wait_for_timeout(1500); await shot(4)
        await pg.wait_for_timeout(4000); await shot(5)
        # 等三人组离场后再送：应从 1 重数
        await pg.wait_for_timeout(15000); await click('boom', '1'); await pg.wait_for_timeout(300); await shot(6)
        print("errors", errs[:5])
        await b.close()
asyncio.run(main())
