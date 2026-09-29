"""绿茶妹妹出场视频的参考图（2026-09-29）。用法：python3 video/sister/make_refs.py
全部按游戏里的真实位置算：档 4 视频区 box [0, 130, 960, 1280]（3:4），参考图 1080×1440 = box × 1.125。
  她：main.js G4STAND.sister [848, 1136, 1.0]，贴图 sister1_up.webp 的 foot [279, 984] → 贴图左上 (569, 152)；
  手机：FX.phoneX/Y = (454, 898)（男女主抢的那部，她从这部手机里蹦出来）；
  奶盖泡泡海：sea.js TeaTide（top 1190，三层 y 20 / 73 / 115，小兵按 TIDE_MOBS）。
出：ref_1_角色.png（灰底立绘）、ref_2_尾帧构图.png、ref_3_奶盖泡泡海.png、ref_4_首帧构图.png、layout_示意.jpg。"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'v14'))
from crewart import cut, edge_extend
WORLD = os.path.join(ROOT, 'web', 'assets', 'world')
BOX = (0, 130, 960, 1280); K = 1080 / 960
W, H = 1080, 1440
STAND, FOOT = (848, 1136), (279, 984)
PHONE = (454, 898)
TOP, LAYERS = 1190, [('far', 20), ('mid', 73), ('near', 115)]
MOBS = [(0.08, 0, 2, 0.75), (0.42, 0, 0, 0.75), (0.76, 0, 3, 0.75), (0.22, 1, 1, 0.95), (0.58, 1, 2, 0.95), (0.92, 1, 0, 0.95)]
KINDS = ['lotus', 'cup', 'bunny', 'heart']


def night():
    """昏暗的粉紫色夜晚卧室：竖向渐变 + 几颗小而暗的光斑（22% 环境，结尾退掉）"""
    y = np.linspace(0, 1, H)[:, None, None]
    a = np.array([34, 20, 44], np.float32) * (1 - y) + np.array([64, 32, 62], np.float32) * y
    im = Image.fromarray(np.broadcast_to(a, (H, W, 3)).astype(np.uint8), 'RGB').convert('RGBA')
    L = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(L)
    rng = np.random.default_rng(7)
    for _ in range(14):
        x, yy, r = rng.uniform(0, W), rng.uniform(0, H * 0.75), rng.uniform(10, 26)
        c = [(255, 150, 200), (200, 160, 255), (255, 210, 230)][rng.integers(3)]
        d.ellipse((x - r, yy - r, x + r, yy + r), fill=c + (70,))
    im.alpha_composite(L.filter(ImageFilter.GaussianBlur(6)))
    return im


def g2r(x, y):                     # 游戏坐标 → 参考图坐标
    return (x - BOX[0]) * K, (y - BOX[1]) * K


def tide(canvas, y0=BOX[1], k=K):
    """游戏里的奶盖泡泡海（静帧：不起伏，各层整排平铺），画进 canvas（y0、k：画布对应的游戏上沿和缩放）"""
    def put(im, x, y):
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        canvas.alpha_composite(im, (round(x * k), round((y - y0) * k)))
    lay = {n: Image.open(os.path.join(WORLD, f'tide_tea_{n}.webp')).convert('RGBA') for n, _ in LAYERS}
    crest = {}
    for n, dy in LAYERS:
        a = np.array(lay[n])[..., 3]; top = np.argmax(a > 128, axis=0)
        crest[n] = lambda x, top=top, w=lay[n].width, dy=dy: TOP + dy + top[int(x) % w]
    mob = [Image.open(os.path.join(WORLD, f'tide_tea_{k_}.webp')).convert('RGBA') for k_ in KINDS]

    def mobs(row):
        n = ['mid', 'near'][row]
        for fx, r, kk, s in MOBS:
            if r != row: continue
            m = mob[kk].resize((round(mob[kk].width * s), round(mob[kk].height * s)), Image.LANCZOS)
            x = fx * 960; y = crest[n](x) - m.height * (1 - 0.22)
            put(m, x - m.width / 2, y)
    for n, dy in LAYERS:
        for x in range(0, 960, lay[n].width): put(lay[n], x, TOP + dy)
        if n == 'mid': mobs(0)
        if n == 'near': mobs(1)


def her(canvas):
    """她 + 身后的粉光（crew.js drawSisterAura 的意思），按游戏悬停位"""
    sp = Image.open(os.path.join(WORLD, 'sister1_up.webp')).convert('RGBA')
    # 贴图四边的外发光是截断的（边上 alpha 还有 26~32，所有档 4 贴图都这样）：游戏的亮底图上看不出，
    # 这里的深色夜景上是一个矩形框，模型会照着画 —— 四边 40 像素羽化到 0
    a = np.array(sp).astype(np.float32); h, w = a.shape[:2]
    f = np.minimum.outer(np.minimum(np.arange(h), np.arange(h)[::-1]), np.minimum(np.arange(w), np.arange(w)[::-1])) / 40
    a[..., 3] *= np.clip(f, 0, 1); sp = Image.fromarray(a.astype(np.uint8), 'RGBA')
    x0, y0 = STAND[0] - FOOT[0], STAND[1] - FOOT[1]
    cx, cy = g2r(x0 + 154, y0 + 319)
    G = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(G); R = 330 * K
    for i in range(20, 0, -1):
        r = R * i / 20; d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 150, 200, int(10 + 3 * (20 - i))))
    canvas.alpha_composite(G.filter(ImageFilter.GaussianBlur(30)))
    sp = sp.resize((round(sp.width * K), round(sp.height * K)), Image.LANCZOS)
    x, y = g2r(x0, y0); canvas.alpha_composite(sp, (round(x), round(y)))


def phone(canvas, c, w):
    """一部粉色手机，屏幕朝镜头、亮着一小团粉光，屏上一颗爱心（不画字）"""
    h = w * 2.05; x0, y0 = c[0] - w / 2, c[1] - h / 2
    G = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(G)
    d.ellipse((c[0] - w * 1.3, c[1] - w * 1.6, c[0] + w * 1.3, c[1] + w * 1.6), fill=(255, 150, 200, 110))
    canvas.alpha_composite(G.filter(ImageFilter.GaussianBlur(w * 0.45)))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=w * 0.16, fill=(255, 176, 206, 255), outline=(200, 90, 140, 255), width=3)
    m = w * 0.07
    d.rounded_rectangle((x0 + m, y0 + m * 1.4, x0 + w - m, y0 + h - m * 1.4), radius=w * 0.11, fill=(255, 236, 244, 255))
    r = w * 0.2; hx, hy = c[0], c[1] - w * 0.1
    d.polygon([(hx, hy + r * 1.1), (hx - r * 1.2, hy - r * 0.1), (hx, hy - r * 0.2), (hx + r * 1.2, hy - r * 0.1)], fill=(255, 110, 170, 255))
    d.ellipse((hx - r * 1.2, hy - r * 0.9, hx, hy + r * 0.3), fill=(255, 110, 170, 255))
    d.ellipse((hx, hy - r * 0.9, hx + r * 1.2, hy + r * 0.3), fill=(255, 110, 170, 255))


def main():
    # ① 灰底立绘（游戏同一张原图，不带外发光）
    rgb, al = cut(os.path.join(ROOT, 'v14', 'sister', 'pose', 'P3a.png'), 'green', (40, 150)); rgb = edge_extend(rgb, al)
    ys, xs = np.nonzero(al > 0.5)
    A = Image.fromarray(np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8)[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 'RGBA')
    k = 960 / A.height; A = A.resize((round(A.width * k), 960), Image.LANCZOS)
    r1 = Image.new('RGBA', (1024, 1024), (128, 128, 128, 255)); r1.alpha_composite(A, ((1024 - A.width) // 2, 32))
    r1.convert('RGB').save(os.path.join(HERE, 'ref_1_角色.png'))
    # ② 尾帧：夜色 + 她在悬停位 + 底部奶盖泡泡海
    r2 = night(); her(r2); tide(r2); r2.convert('RGB').save(os.path.join(HERE, 'ref_2_尾帧构图.png'))
    # ③ 奶盖泡泡海一条（游戏 y 1100~1500）
    r3 = Image.new('RGBA', (W, 450), (46, 26, 52, 255)); tide(r3, 1100); r3.convert('RGB').save(os.path.join(HERE, 'ref_3_奶盖泡泡海.png'))
    # ④ 首帧：夜色 + 游戏里那部手机的位置（放大成手掌大，约画面宽 1/7）
    r4 = night(); pc = g2r(*PHONE); phone(r4, pc, 150); r4.convert('RGB').save(os.path.join(HERE, 'ref_4_首帧构图.png'))
    print('手机中心', [round(v) for v in pc])
    # 示意：整张游戏画布，灰色是视频区
    L = Image.new('RGBA', (960, 1707), (28, 28, 34, 255)); d = ImageDraw.Draw(L)
    d.rectangle((BOX[0], BOX[1], BOX[0] + BOX[2], BOX[1] + BOX[3]), fill=(62, 60, 66, 255))
    v = Image.new('RGBA', (W, H)); her(v); tide(v); phone(v, g2r(*PHONE), 150)
    v = v.resize((960, 1280), Image.LANCZOS); L.alpha_composite(v, (0, 130))
    d = ImageDraw.Draw(L); d.rectangle((BOX[0], BOX[1], BOX[0] + BOX[2] - 1, BOX[1] + BOX[3] - 1), outline=(230, 190, 60, 255), width=4)
    L.convert('RGB').save(os.path.join(HERE, 'layout_示意.jpg'), quality=90)


main()
