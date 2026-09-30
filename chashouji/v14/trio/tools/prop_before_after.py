#!/usr/bin/env python3
"""3D 道具返工前后对照：每件一行，左边旧图集 4 个角度、右边新图集 4 个角度（转盘 0° / 90° / 180° / 270°），
按各自引擎里的屏幕尺寸（直径 2r × scale）×2 画在地板米色上，行尾写结构密度 / 墨块帧 / 屏幕外轮廓描边 / KB（prop_check.py 同一套量法）。

    python3 v14/trio/tools/prop_before_after.py <旧图集目录> [输出.png]      # 在 chashouji/ 下跑；默认 shots/trio_std/3d返工_前后.png
    旧图集目录：git show <返工前的提交>:chashouji/web/assets/trio/prop_<名>.webp 存出来的那几张

ITEMS 里 old / new 是 (cell, scale, r)：旧的是返工前数据里填的，新的是 docs/三人组角色规范.md 7.1 表里的。
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../tools/3d'))
from measure_volume import struct_density, cells, INK
from prop_check import ink_width

ITEMS = [   # 件名, 标题, 旧 (cell, scale, r), 新 (cell, scale, r)
    ('cassette', 'B24 磁带', (84, 1.31, 22), (84, 1.31, 22)),
    ('dumbbell', 'B25 哑铃', (75, 1.08, 24), (75, 1.06, 28)),
    ('pinecone', 'B8 松果', (76, 1.04, 26), (76, 1.25, 26)),
    ('necklace', 'G15 海洋之心', (79, 1.09, 26), (79, 1.39, 26)),
    ('abacus', 'G5 算盘', (115, 1.35, 34), (115, 1.35, 40)),
    ('mouse', 'B26 有线鼠标', (88, 1.37, 22), (88, 1.46, 22)),
]
Z, TW, TH = 2, 175, 260
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
BG = (233, 222, 200)


def stats(path, cell, scale, r):
    ims = cells(path, cell)
    px = 2 * r * scale
    blob = 0
    for g in ims:
        solid = g[..., 3] > 200
        ink = np.sqrt(((g[..., :3].astype(float) - INK) ** 2).sum(-1)) < 60
        blob += (solid & ~ink).sum() < 0.15 * max(1, solid.sum())
    return '密度 %.0f%%  墨块帧 %d/36  描边 %.1fpx  %dKB' % (struct_density(path, cell, px) * 100, blob, ink_width(ims, px), os.path.getsize(path) // 1024)


def row(im, d, f, path, cell, scale, r, x0, y0):
    a = Image.open(path).convert('RGBA')
    px = int(round(2 * r * scale * Z))
    for j, i in enumerate((0, 9, 18, 27)):
        g = a.crop(((i % 6) * cell, (i // 6) * cell, (i % 6 + 1) * cell, (i // 6 + 1) * cell)).resize((px, px), Image.LANCZOS)
        im.paste(g, (x0 + j * TW + TW // 2 - px // 2, y0 + 112 - px // 2), g)
    d.text((x0 + 8, y0 + TH - 34), f'r {r}  cell {cell}  scale {scale}   ' + stats(path, cell, scale, r), fill=(40, 30, 20), font=f)


def main(old_dir, out):
    f, fb = ImageFont.truetype(FONT, 17), ImageFont.truetype(FONT, 22)
    W = 8 * TW + 60
    im = Image.new('RGB', (W, len(ITEMS) * (TH + 36) + 70), BG)
    d = ImageDraw.Draw(im)
    d.text((16, 12), '3D 道具返工前后（审查第三轮 6.7）：左 = 返工前，右 = 返工后；转盘 0° / 90° / 180° / 270°，引擎屏幕尺寸 ×2', fill=(40, 30, 20), font=fb)
    d.text((16, 42), '篮球样板：密度 26%  墨块帧 0/36  描边 3.9px', fill=(90, 70, 50), font=f)
    for k, (n, title, old, new) in enumerate(ITEMS):
        y0 = 70 + k * (TH + 36)
        d.text((16, y0), title, fill=(40, 30, 20), font=fb)
        row(im, d, f, os.path.join(old_dir, f'prop_{n}.webp'), *old, 10, y0 + 30)
        row(im, d, f, f'web/assets/trio/prop_{n}.webp', *new, 4 * TW + 50, y0 + 30)
        d.line((4 * TW + 30, y0 + 30, 4 * TW + 30, y0 + TH + 20), fill=(150, 130, 110), width=2)
    im.save(out)
    print(out, im.size)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'shots/trio_std/3d返工_前后.png')
