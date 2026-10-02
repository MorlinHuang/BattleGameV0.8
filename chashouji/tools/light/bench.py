"""立体感的性能（docs/三人组角色规范.md「立体感 · 性能」）：桌面里真 GUI Chrome（DISPLAY=:1，非 headless、无虚拟时间）跑 ?bench=1&benchtrio=1，
两边三人组常驻 + 男女主，?light=0 / ?light=1 交替各跑 N 遍，读页面 #stat 那一行（main.js bench 的读数）。
用法：DISPLAY=:1 python3 bench.py <base url> <N> "<额外参数>" ["0;1" 或 "0;shadow;grade;rim;1"]
     交替的不是 light 而是别的开关时，变体直接写成参数："triofx2=0;triofx2=1"（精引3 第二批件整页增量，light 照默认开）
口径：每帧 = 逻辑 + 底版层 + 角色层 + 特效层（main.js bench）；立体感只动角色层，差值 = 它的代价。
这台桌面没有 GPU（SwiftShader 软渲染），绝对毫秒数不代表手机；看的是开 / 关的相对差和占比。"""
import asyncio, os, re, sys, time
from playwright.async_api import async_playwright
BASE, N, EXTRA = sys.argv[1], int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else ''
VARS = (sys.argv[4] if len(sys.argv) > 4 else '0,1').split(';')   # 交替跑哪几种 light 值（分项：0;shadow;grade;rim;1）


async def one(p, light):
    b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=False,
                                args=['--no-sandbox', '--disable-dev-shm-usage', '--enable-unsafe-swiftshader', '--force-device-scale-factor=1'])
    pg = await b.new_page(viewport={'width': 1000, 'height': 960})
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    var = light if '=' in light else f'light={light}'
    await pg.goto(f'{BASE}?bench=1&benchtrio=1&benchframes=600&seed=9&{var}&{EXTRA}', timeout=900000)
    await pg.wait_for_function("document.title === 'BENCHDONE'", timeout=900000)
    st = await pg.evaluate("document.getElementById('stat').textContent")
    await b.close()
    return st, errs


def nums(st):
    g = lambda k: [float(x) for x in re.search(k + r'\s+([\d.]+)\s+([\d.]+)', st).groups()]
    md = re.search(r'中位 每帧 ([\d.]+) 角色层 ([\d.]+)', st)
    return {'all': g('每帧总计'), 'ch': g('角色层'), 'p95': float(re.search(r'p95 ([\d.]+)', st).group(1)), 'med': float(md.group(1)), 'medch': float(md.group(2))}


async def main():
    res = {v: [] for v in VARS}
    async with async_playwright() as p:
        for i in range(N):
            for light in VARS:
                st, errs = await one(p, light)
                r = nums(st); res[light].append(r)
                print(f'light={light} 第{i + 1}遍  每帧 {r["all"][0]:.2f} 峰 {r["all"][1]:.1f}  角色层 {r["ch"][0]:.2f} 峰 {r["ch"][1]:.1f}  中位 每帧 {r["med"]:.2f} 角色层 {r["medch"]:.2f}  p95 {r["p95"]:.2f}  errors {errs[:3]}', flush=True)
    for light in VARS:
        rs = res[light]; m = lambda f: sorted(f(r) for r in rs)[len(rs) // 2]
        print(f'light={light} 各遍取中：每帧均值 {m(lambda r: r["all"][0]):.2f} ms  角色层均值 {m(lambda r: r["ch"][0]):.2f} ms  每帧中位 {m(lambda r: r["med"]):.2f} ms  角色层中位 {m(lambda r: r["medch"]):.2f} ms  p95 {m(lambda r: r["p95"]):.2f} ms')

asyncio.run(main())
