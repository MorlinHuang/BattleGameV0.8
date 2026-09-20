#!/usr/bin/env python3
"""量一套转盘图集"到底在不在三维里转"，八件横着比。

    python3 measure_volume.py <图集目录> [件名 ...]

三把尺子，都只看**剪影**（不看颜色）—— 体积感是形状给的，不是配色给的：

1. **贴纸残差**：把第 k 帧的剪影在画面内旋转+缩放，去尽量套住第 0 帧，取套得
   最好那一次的 IoU。一张 2D 图打转的话，随便哪一帧都能转回第 0 帧，IoU 接近 1；
   真在三维里转，透视一压就套不回去了。**这是判"贴纸 vs 立体"最直接的一把。**
   报的是 36 帧的中位数，越低越立体。
2. **面积变化率** (max-min)/median：转的时候迎光面积有没有真的变。
3. **细长比波动**：剪影二阶矩特征值之比开根 sqrt(λ1/λ2) 的 (max-min)/median。
   平面内打转不改变它，只有三维转动的透视压缩才会改。

再加一把不是体积感、但决定看不看得见的尺子：

4. **每帧跳变** XOR/并集，按**引擎实际转速**换算到相邻两个渲染帧之间。
   跳太大眼睛就把它读成"闪"而不是"转"，体积感再足也传不到观众那里。
"""
import sys, os, math
import numpy as np
from PIL import Image

# 引擎侧的实际参数（ammo.js SPRITE + main.js GIFT），量的时候要用到
ENGINE = {   # 件名: (cell, scale, r, spin, 每次齐射几颗)
    'bouquet': (272, 1.36, 76, 6.7, 1),
    'milktea': (264, 1.30, 72, 6.7, 1),
    'ringbox': (336, 1.61, 64, 6.7, 1),
    'photo':   (336, 1.38, 68, 6.7, 1),
    'hairpin': (96,  1.08, 22, 8.8, 8),
    'seed':    (96,  1.10, 21, 8.8, 8),
    'pillow':  (160, 1.18, 56, 5.7, 1),
    'gamepad': (160, 1.07, 52, 5.7, 1),
}
N, COLS, FPS = 36, 6, 60
SZ = 96          # 统一缩到这个边长再比，快且不影响结论


def frames(path, cell):
    im = Image.open(path).convert('RGBA')
    a = np.array(im)[..., 3] > 8
    out = []
    for k in range(N):
        g = a[(k // COLS) * cell:(k // COLS + 1) * cell, (k % COLS) * cell:(k % COLS + 1) * cell]
        out.append(np.array(Image.fromarray(g.astype(np.uint8) * 255).resize((SZ, SZ), Image.BILINEAR)) > 127)
    return out


def norm(m):
    """质心挪到中心、面积归一到固定值 —— 之后只剩形状的差别。"""
    ys, xs = np.where(m)
    if len(xs) < 8:
        return None
    im = Image.fromarray(m.astype(np.uint8) * 255)
    s = math.sqrt((SZ * SZ * 0.18) / m.sum())          # 统一到 18% 填充
    im = im.resize((max(8, int(SZ * s)), max(8, int(SZ * s))), Image.BILINEAR)
    b = np.array(im) > 127
    ys, xs = np.where(b)
    cy, cx = ys.mean(), xs.mean()
    out = np.zeros((SZ, SZ), bool)
    oy, ox = int(SZ / 2 - cy), int(SZ / 2 - cx)
    for y, x in zip(ys, xs):
        ny, nx = y + oy, x + ox
        if 0 <= ny < SZ and 0 <= nx < SZ:
            out[ny, nx] = True
    return out


def best_iou(a, b):
    """b 在画面内转一圈去套 a，取套得最好那一次的 IoU。"""
    best = 0.0
    bi = Image.fromarray(b.astype(np.uint8) * 255)
    for deg in range(0, 360, 4):
        r = np.array(bi.rotate(deg, resample=Image.BILINEAR)) > 127
        inter = (a & r).sum()
        uni = (a | r).sum()
        if uni:
            best = max(best, inter / uni)
    return best


def elong(m):
    ys, xs = np.where(m)
    x, y = xs - xs.mean(), ys - ys.mean()
    c = np.array([[(x * x).mean(), (x * y).mean()], [(x * y).mean(), (y * y).mean()]])
    w = np.linalg.eigvalsh(c)
    return math.sqrt(max(w[1], 1e-9) / max(w[0], 1e-9))


def run(d, names):
    print('%-8s %6s %7s %7s %7s %7s %7s' %
          ('件', '贴纸残', '面积变', '细长变', '屏幕px', '每帧跳', '跳几格'))
    print('-' * 58)
    rows = []
    for nm in names:
        p = os.path.join(d, nm + '_atlas.webp')
        if not os.path.exists(p):
            continue
        cell, scale, r, spin, _ = ENGINE[nm]
        fs = frames(p, cell)
        nf = [norm(f) for f in fs]
        base = nf[0]
        ious = sorted(best_iou(base, f) for f in nf[1:] if f is not None)
        iou = ious[len(ious) // 2]

        ar = np.array([f.sum() for f in fs], float)
        elo = np.array([elong(f) for f in fs])

        # 引擎实际每帧转过几格，跳变按那个步长量
        step = max(1, round(spin / FPS / (2 * math.pi / N)))
        xo = []
        for k in range(N):
            a, b = fs[k], fs[(k + step) % N]
            u = (a | b).sum()
            if u:
                xo.append((a ^ b).sum() / u)
        rows.append((nm, iou, (ar.max() - ar.min()) / np.median(ar),
                     (elo.max() - elo.min()) / np.median(elo),
                     r * scale * 2, np.median(xo), spin / FPS / (2 * math.pi / N)))
    for nm, iou, da, de, px, xo, gp in sorted(rows, key=lambda t: -t[1]):
        print('%-8s %6.2f %6.0f%% %6.0f%% %7.0f %6.0f%% %7.2f' % (nm, iou, da * 100, de * 100, px, xo * 100, gp))


if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else '.'
    ns = sys.argv[2:] or list(ENGINE)
    run(d, ns)
