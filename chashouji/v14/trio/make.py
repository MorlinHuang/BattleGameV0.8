"""档 3 三人组的新姿势立绘（2026-09-29，docs/帮手三人组.md）。原图 src/*.png（生图，品红 / 绿幕 / 自带透明）→ 抠像、裁到剪影、
缩到游戏里的屏幕像素（贴图像素 × 1 = 屏幕像素，运行时 s ≈ 1）→ web/assets/world/trio_<名>.webp。
道具 src/props.png 一张三件（玫瑰 / 绣球 / 胸罩），按连通块拆开 → trio_prop_<名>.webp。
每张另出一份 preview/<名>_grid.png（每 50 像素一条格线），量手 / 转轴这些点用。"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from crewart import cut, edge_extend
OUT = os.path.join(HERE, '../../web/assets/world')
# 名: (原图, 幕布, 按 'h' 高 / 'w' 宽 缩到多少屏幕像素)
CHARS = {
    'mask':     ('mask.png', 'green', 'h', 360),       # 假面绅士 扒墙
    'straw':    ('straw.png', 'magenta', 'h', 360),    # 草帽船长 扒墙
    'sakura':   ('sakura.png', 'magenta', 'w', 470),   # 樱木 扑地
    'goku':     ('goku.png', 'magenta', 'h', 300),     # 悟空 半跪
    'gege':     ('gege.png', 'green', 'h', 420),       # 格格 秋千（含绳）
    'fairy':    ('fairy.png', 'magenta', 'h', 420),    # 紫衣仙子 秋千（含绳）
    'explorer': ('explorer.png', 'magenta', 'w', 430), # 探险家 趴地
    'ninja':    ('ninja.png', 'alpha', 'h', 290),      # 忍者扇娘 半跪
}
PROPS = [('rose', 150), ('ball', 90), ('bra', 120)]    # 从左到右；缩到多宽（贴图像素，运行时再按 s 缩）
M = 4

def load(path, screen):
    if screen == 'alpha':
        a = np.array(Image.open(path).convert('RGBA')).astype(np.float32)
        return a[..., :3], a[..., 3] / 255
    return cut(path, screen, (40, 150))

def save(rgb, al, box, size, out):
    x0, y0, x1, y1 = box
    px = np.dstack([edge_extend(rgb.copy(), al), al * 255]).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(px[y0:y1, x0:x1], 'RGBA')
    k = size / (im.height if size_by == 'h' else im.width)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    im.save(out, 'WEBP', quality=90, method=6)
    return im, k

os.makedirs(os.path.join(HERE, 'preview'), exist_ok=True)
for name, (src, screen, size_by, size) in CHARS.items():
    rgb, al = load(os.path.join(HERE, 'src', src), screen)
    ys, xs = np.nonzero(al > 0.05)
    box = (max(0, xs.min() - M), max(0, ys.min() - M), min(al.shape[1], xs.max() + 1 + M), min(al.shape[0], ys.max() + 1 + M))
    im, k = save(rgb, al, box, size, os.path.join(OUT, f'trio_{name}.webp'))
    g = Image.new('RGBA', im.size, (235, 235, 235, 255)); g.alpha_composite(im); d = ImageDraw.Draw(g)
    for x in range(0, im.width, 50): d.line([(x, 0), (x, im.height)], fill=(0, 120, 255, 255) if x % 100 == 0 else (120, 200, 255, 255))
    for y in range(0, im.height, 50): d.line([(0, y), (im.width, y)], fill=(0, 120, 255, 255) if y % 100 == 0 else (120, 200, 255, 255))
    g.convert('RGB').resize((im.width * 2, im.height * 2)).save(os.path.join(HERE, 'preview', f'{name}_grid.png'))
    print(name, 'size', im.size, 'k', round(k, 4))

rgb, al = load(os.path.join(HERE, 'src', 'props.png'), 'green')
lab, n = ndimage.label(ndimage.binary_dilation(al > 0.05, iterations=12))
objs = sorted(ndimage.find_objects(lab), key=lambda s: s[1].start)
objs = [o for o in objs if (o[1].stop - o[1].start) > 60]
for (name, size), sl in zip(PROPS, objs):
    y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
    size_by = 'w'
    im, k = save(rgb, al * (lab[..., None][..., 0] == lab[sl][lab[sl] > 0][0]), (x0, y0, x1, y1), size, os.path.join(OUT, f'trio_prop_{name}.webp'))
    print('prop', name, im.size)
