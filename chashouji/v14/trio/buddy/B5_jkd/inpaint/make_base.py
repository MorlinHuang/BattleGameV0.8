"""B5 走路条蒙版重绘的底图 + 蒙版（审查_样板 7.2）。
底 = raw/walk_gen1.png 第一行两格（walk1 接地、walk4 过渡），头和躯干全程不动。
行 1：walk1 | walk4 —— 只重绘手臂（棍换到近侧手）
行 2：walk1 副本 | walk4 副本 —— 重绘腿 + 手臂，出 walk3（远侧腿在前）| walk2（近侧腿支撑、远侧腿提起）
行 3：原 taunt / idle，不动，只给模型看人。
蒙版：alpha 0 = 重绘，255 = 保留。"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
src = Image.open('raw/walk_gen1.png').convert('RGBA')
W, H = src.size
base = Image.new('RGBA', (W, H), (255, 0, 255, 255))
base.alpha_composite(src)
strip = base.crop((0, 5, W, 510))
base.paste(strip, (0, 515))
base.paste(Image.new('RGBA', (W, 5), (255, 0, 255, 255)), (0, 510))
base.convert('RGB').save('inpaint/base.png')

A = np.array(src)[..., 3] > 100
def torso(dx):   # 头 + 躯干（不含手臂），每格按 gen1 第一行量
    if dx == 0:
        return [(222, 15), (335, 15), (335, 105), (330, 140), (325, 190), (322, 240), (325, 285), (300, 305), (268, 300),
                (262, 260), (262, 200), (255, 150), (245, 115), (236, 80)]
    return [(680, 15), (785, 15), (785, 100), (790, 140), (790, 200), (795, 240), (790, 270), (740, 285), (722, 265),
            (720, 220), (715, 170), (705, 115), (695, 80)]
def legs(dx):
    m = np.zeros((H, W), bool)
    if dx == 0:
        m[300:505, 120:470] = A[300:505, 120:470]
        m[270:410, 198:238] = False        # 远侧手里的棍
    else:
        m[295:505, 640:802] = A[295:505, 640:802]
    return m
keep = Image.new('L', (W, H), 0)
d = ImageDraw.Draw(keep)
d.rectangle((0, 1022, W, H), fill=255)      # 行 3 全保留
for row, with_legs in ((0, True), (515, False)):
    for dx in (0, 512):
        d.polygon([(x, y + row) for x, y in torso(dx)], fill=255)
        if with_legs:
            lm = legs(dx)
            k = np.array(keep); k[lm] = 255; keep = Image.fromarray(k); d = ImageDraw.Draw(keep)
keep = keep.filter(ImageFilter.MaxFilter(5))
mask = Image.new('RGBA', (W, H), (0, 0, 0, 0))
mask.putalpha(keep)
mask.save('inpaint/mask.png')
vis = base.copy(); red = Image.new('RGBA', (W, H), (0, 200, 255, 110)); vis.paste(red, (0, 0), Image.fromarray(255 - np.array(keep)))
vis.convert('RGB').save('inpaint/mask_vis.jpg', quality=85)
