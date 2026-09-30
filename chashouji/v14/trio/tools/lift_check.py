#!/usr/bin/env python3
"""挂件拆层（frames.py lift）之后，挂件甩开时原位置露出来的补画有没有脏块（G11 格格流苏，2026-09-30 审查）。

    python3 lift_check.py <图集.webp> <挂件.webp> <补画掩码.png> <出图.png> [角度 rad ...]      角度默认 −0.12 0.12

补画掩码 = frames.py build 时 lift 存的 preview/<挂件名>_holes.png（哪些像素是补出来的，按图集排）。
按 trio_bestie.js G11 的 parts（pivot、at[帧]）把挂件绕 pivot 转到给定角度贴回每一帧，只数挂件没盖住的补画像素里的灰块
（原画上手指、手臂边缘本来就有同色的像素，不算）：不透明、颜色离审查量到的灰块 RGB (190, 172, 165) < 30 —— 四周平均色填出来的直角块。
出图：每帧一列、每个角度一行，放大 6 倍，贴蓝底，灰块标红。"""
import sys, json, os, numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CELL, COLS = (315, 343), 4
NAMES = ['idle', 'raise', 'throw', 'follow', 'wind', 'tuck', 'kick', 'idle2']
PIVOT = (7, 0)
AT = {'idle': [80, 30], 'raise': [84.5, 24], 'throw': [107, 43], 'follow': [81, 30], 'wind': [54.5, 39], 'tuck': [135, 34], 'kick': [58.5, 39], 'idle2': [79, 34]}
GRAY = np.array([190, 172, 165], float)


def hang(part, ang, at, size):
    """挂件绕 pivot 转 ang（canvas rotate：正 = 屏幕上顺时针）、pivot 落在 at，画到 size 大的透明图上"""
    c, s = np.cos(ang), np.sin(ang)
    # 输出点 (u, v) ← 挂件点：先减 at、逆转 ang、再加 pivot
    m = (c, s, PIVOT[0] - c * at[0] - s * at[1], -s, c, PIVOT[1] + s * at[0] - c * at[1])
    return part.transform(size, Image.AFFINE, m, Image.BICUBIC)


def main():
    atlas, part, dst = Image.open(sys.argv[1]).convert('RGBA'), Image.open(sys.argv[2]).convert('RGBA'), sys.argv[4]
    holes = np.array(Image.open(sys.argv[3]).convert('L')) > 127
    angs = [float(v) for v in sys.argv[5:]] or [-0.12, 0.12]
    boxes = json.load(open(os.path.join(HERE, 'samples/G11_gege/frames.json')))['lift'][0]['box']
    cw, ch = CELL
    cols, tot = [], 0
    for i, fn in enumerate(NAMES):
        cell = atlas.crop(((i % COLS) * cw, (i // COLS) * ch, (i % COLS + 1) * cw, (i // COLS + 1) * ch))
        a = np.array(cell).astype(float)
        x0, y0, x1, y1 = boxes[fn]
        filled = holes[(i // COLS) * ch:(i // COLS + 1) * ch, (i % COLS) * cw:(i % COLS + 1) * cw]
        col = []
        for ang in angs:
            p = hang(part, ang, AT[fn], (cw, ch))
            gray = (a[..., 3] > 127) & (np.sqrt(((a[..., :3] - GRAY) ** 2).sum(-1)) < 30) & filled & ~(np.array(p)[..., 3] > 32)
            n = int(gray.sum()); tot += n
            print(f'{fn:7s} {ang:+.2f} rad  灰块露出 {n} px')
            comp = Image.new('RGBA', (cw, ch), (40, 90, 200, 255)); comp.alpha_composite(cell); comp.alpha_composite(p)
            c = np.array(comp); c[gray] = (255, 0, 0, 255)
            col.append(Image.fromarray(c).crop((x0 - 20, y0 - 14, x1 + 20, y1 + 20)).resize(((x1 - x0 + 40) * 6, (y1 - y0 + 34) * 6), Image.NEAREST))
        cols.append(col)
    print(f'合计 {tot} px')
    H = max(t.height for c in cols for t in c)
    out = Image.new('RGB', (sum(c[0].width for c in cols), H * len(angs)))
    x = 0
    for c in cols:
        for k, t in enumerate(c): out.paste(t, (x, k * H))
        x += c[0].width
    out.save(dst)


if __name__ == '__main__':
    main()
