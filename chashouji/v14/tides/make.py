"""档 4 另外四个人的法术潮（2026-09-29）：对应白娘子的海（sea2/make.py）、法海的经卷（scroll/make.py）。
用法：python3 v14/tides/make.py → web/assets/world/tide_<潮>_{far,mid,near}.webp（三层长条）+ tide_<潮>_<兵>.webp（小兵），打印 sea.js 要填的尺寸。

用户："给真相女神和恶魔添加类似水面和卷轴的效果"；"新增一对人物，嫦娥 vs 后羿，主题为月和日，制作规格和白娘子法海一致"。题材（用户选的）：
  truth 真相女神 → 真相云海：翠绿发光云浪，浮着聊天气泡；小兵是放大镜、带翅膀的手机、聊天气泡、相机小精灵（朝右冲男生）；
  demon 灭迹恶魔 → 碎纸黑烟：紫黑浓烟浪，夹着碎纸屑；小兵是小恶魔、吃纸垃圾桶、碎纸机、橡皮擦（朝左冲女生）；
  （嫦娥原来也在这：月夜银云海 + 玉兔金蟾。2026-09-29 用户"太像水面了，跟白娘子的重复"，换成明月银河 v14/moonsky/make.py，这里删了）
  sun   后羿     → 只剩小兵：四只三足金乌（朝左），给烈日火空用（sea.js SunSky；原来的太阳火云海 2026-09-29 换掉了，同嫦娥）。
每片潮只生一张图（<潮>_src.png，<潮>_alt.png 是同一轮另一张）：远 / 中 / 近三层用同一张，中层水平翻过来，各层缩放、压色不同，
引擎里各层反向平移、起伏也不同 —— 海是三张各生的，这四片省成一张，叠起来看不出是同一张。
幕布：真相云海是翠绿，用品红幕；另三片用绿幕（紫黑烟、淡紫光在品红上抠穿；火的粉红光晕品红度能到 20+）。
小兵是 2×2 一张（<潮>_mobs.png），按连通块切成四张（同 scroll/beasts.py），烘一圈本潮颜色的外发光。
恶魔、玉兔、金乌三张生图直接给了透明底（alpha 身子里 250~254、外圈 1~31 的虚边）→ alpha 按 (32, 240) 拉满 / 清零。
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from tidekit import load, solid, seam
from crewart import cut, edge_extend

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'web', 'assets', 'world')

# 潮：幕布、键、三层 [(名, 缩放, 是否水平翻, (压向的颜色, 压多少))]。缩放按原图 1536 宽（拼缝后 1216）→ 远 535 / 中 693 / 近 888，同海
LAYERS = lambda far, mid, near: [('far', 0.44, False, far), ('mid', 0.57, True, mid), ('near', 0.73, False, near)]
TIDES = {
    'truth': ('magenta', (40, 150), LAYERS(((215, 255, 225), 0.30), ((20, 90, 50), 0.06), ((5, 40, 20), 0.15))),
    'demon': ('green', (40, 150), LAYERS(((175, 150, 205), 0.30), ((40, 10, 60), 0.06), ((10, 0, 20), 0.15))),
}
# 小兵：幕布（透明底的填 None）、四格的名字（按在原图里的格子 列, 行）、外发光颜色
MOBS = {
    'truth': ('magenta', {(0, 0): 'magnifier', (1, 0): 'phone', (0, 1): 'bubble', (1, 1): 'camera'}, (120, 255, 140)),
    'demon': (None, {(0, 0): 'imp', (1, 0): 'bin', (0, 1): 'shredder', (1, 1): 'eraser'}, (200, 90, 240)),
    'sun':   (None, {(0, 0): 'crow1', (1, 0): 'crow2', (0, 1): 'crow3', (1, 1): 'crow4'}, (255, 150, 40)),
}
HGT, PAD = 150, 18               # 小兵剪影高（同虾兵、神兽；引擎里再按远近乘 0.75 / 0.95）、外发光留边


def tide(name, screen, key, layers):
    rgb0, al0 = load(os.path.join(HERE, f'{name}_src.png'), screen, key)
    al0 = solid(al0)
    for lname, K, flip, (tint, tk) in layers:
        rgb, al = (rgb0[:, ::-1], al0[:, ::-1]) if flip else (rgb0, al0)
        rgb = rgb * (1 - tk) + np.array(tint, np.float32) * tk
        A = seam(rgb, al)
        ys = np.nonzero(A[..., 3].max(1) > 8)[0]
        A = A[ys.min():]
        im = Image.fromarray(A.clip(0, 255).astype(np.uint8), 'RGBA')
        im = im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS)
        p = os.path.join(OUT, f'tide_{name}_{lname}.webp')
        im.save(p, 'WEBP', quality=88, method=6)
        a = np.array(im)[..., 3]
        top = np.argmax(a > 128, axis=0)
        print(f'  tide_{name}_{lname}.webp {im.width}×{im.height}  上沿 y {top.min()}~{top.max()} 中位 {int(np.median(top))}  {os.path.getsize(p) // 1024}KB')


def mobs(name, screen, names, glow):
    src = os.path.join(HERE, f'{name}_mobs.png')
    if screen is None:
        im = np.array(Image.open(src).convert('RGBA')).astype(np.float32)
        rgb, al = im[..., :3], np.clip((im[..., 3] - 32) / (240 - 32), 0, 1)
    else:
        rgb, al = cut(src, screen, (40, 150))
        rgb = edge_extend(rgb, al)
    lab, n = ndimage.label(al > 0.5)
    sz = ndimage.sum(np.ones_like(al), lab, range(1, n + 1))
    H, W = al.shape
    for i in np.argsort(sz)[::-1][:4]:
        ys, xs = np.nonzero(lab == i + 1)
        cell = (int(xs.mean() > W / 2), int(ys.mean() > H / 2))
        x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        keep = ndimage.binary_dilation(lab == i + 1, iterations=4)[y0:y1, x0:x1]   # 只要这一块，邻居的虚边不要
        px = np.dstack([rgb[y0:y1, x0:x1], al[y0:y1, x0:x1] * keep * 255]).clip(0, 255).astype(np.uint8)
        sp = Image.fromarray(px, 'RGBA')
        sp = sp.resize((round(sp.width * HGT / sp.height), HGT), Image.LANCZOS)
        res = Image.new('RGBA', (sp.width + 2 * PAD, sp.height + 2 * PAD))
        body = Image.new('RGBA', res.size); body.alpha_composite(sp, (PAD, PAD))
        sil = body.split()[3]
        for grow, blur, c, k in [(15, 12, glow, 0.8), (5, 4, tuple(min(255, v + 60) for v in glow), 0.9)]:
            L = Image.new('RGBA', res.size, c + (0,))
            L.putalpha(sil.filter(ImageFilter.MaxFilter(grow)).filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * k)))
            res.alpha_composite(L)
        res.alpha_composite(body)
        res.save(os.path.join(OUT, f'tide_{name}_{names[cell]}.webp'), 'WEBP', quality=90, method=6)
        print(f'  tide_{name}_{names[cell]}.webp {res.size[0]}×{res.size[1]}')


for name, (screen, key, layers) in TIDES.items():
    print(name)
    tide(name, screen, key, layers)
for name in MOBS:
    mobs(name, *MOBS[name])
