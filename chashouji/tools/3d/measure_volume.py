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

**0. 内部结构密度** —— 后来才发现这把才是主尺，先看它。
   把外轮廓那一圈剥掉，只看剪影里面还剩多少描边：花瓣与花瓣的分界、盒盖与
   盒身的接缝都算在内。转动时眼睛真正读到的立体信号是**内部结构的遮挡关系在变**，
   外轮廓变化只说明"形状变了"，撑不起体积。实测花束 47%、奶茶 25%、手柄 13%、
   抱枕 4%、发卡 0% —— 再乘上屏幕面积，花束的可见结构量是手柄的 12 倍、
   抱枕的 28 倍。**转轴和转速都调不动这个数**（手柄换成花束那套转轴反而更糟）。

再加一把不是体积感、但决定看不看得见的尺子：

4. **每帧跳变** XOR/并集，按**引擎实际转速**换算到相邻两个渲染帧之间。
   跳太大眼睛就把它读成"闪"而不是"转"，体积感再足也传不到观众那里。

## 两种用法

    python3 measure_volume.py <图集目录>              # 量已打包的 webp，八件横着比
    python3 measure_volume.py --frames <帧目录> <件名> # 量刚渲出来的 PNG 序列，改完立刻能看
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
    'hairpin': (138, 1.42, 22, 8.8, 8),
    'seed':    (130, 1.34, 21, 8.8, 8),
    'pillow':  (160, 1.16, 56, 5.7, 1),
    'gamepad': (160, 1.06, 52, 5.7, 1),
}
N, COLS, FPS = 36, 6, 60
SZ = 96          # 统一缩到这个边长再比，快且不影响结论


def cells(path, cell):
    """按帧切出 RGBA 小图。path 是图集 webp，或一个装着 PNG 序列的目录。"""
    if os.path.isdir(path):
        import glob
        fs = sorted(glob.glob(os.path.join(path, '*.png')))
        return [np.array(Image.open(f).convert('RGBA')) for f in fs]
    a = np.array(Image.open(path).convert('RGBA'))
    return [a[(k // COLS) * cell:(k // COLS + 1) * cell,
              (k % COLS) * cell:(k % COLS + 1) * cell] for k in range(N)]


def frames(path, cell):
    """逐帧的剪影掩码，统一缩到 SZ 见方。"""
    out = []
    for g in cells(path, cell):
        m = g[..., 3] > 8
        out.append(np.array(Image.fromarray(m.astype(np.uint8) * 255).resize((SZ, SZ), Image.BILINEAR)) > 127)
    return out


INK = np.array([0x3a, 0x2c, 0x26])


def struct_density(path, cell, px):
    """内部结构密度：剥掉相当于 4 个屏幕像素的外轮廓，看里面还剩多少描边。

    剥的厚度按该件在屏幕上的缩放换算 —— 直接剥固定像素的话，大件剥得太浅会把
    外轮廓算进来，小件剥得太深会把内部结构一起剥没，八件就不可比了。"""
    from scipy.ndimage import binary_erosion
    ds = []
    for g in cells(path, cell):
        rgb, al = g[..., :3].astype(float), g[..., 3]
        solid = al > 200
        if solid.sum() < 80:
            continue
        t = max(2, int(round(4 * g.shape[0] / px)))
        inner = binary_erosion(solid, iterations=t)
        if inner.sum() < 40:
            continue
        isink = np.sqrt(((rgb - INK) ** 2).sum(-1)) < 46
        ds.append((isink & inner).sum() / inner.sum())
    return float(np.median(ds)) if ds else 0.0


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


def run(d, names, frames_dir=None):
    print('%-8s %7s %8s %6s %7s %7s %7s %7s' %
          ('件', '结构密度', '屏幕结构量', '贴纸残', '面积变', '细长变', '屏幕px', '每帧跳'))
    print('-' * 68)
    rows = []
    for nm in names:
        cell, scale, r, spin, _ = ENGINE[nm]
        p = frames_dir or os.path.join(d, nm + '_atlas.webp')
        if not os.path.exists(p):
            continue
        px = r * scale * 2
        dens = struct_density(p, cell, px)
        fs = frames(p, cell)
        nf = [norm(f) for f in fs]
        base = nf[0]
        ious = sorted(best_iou(base, f) for f in nf[1:] if f is not None)
        iou = ious[len(ious) // 2]

        ar = np.array([f.sum() for f in fs], float)
        elo = np.array([elong(f) for f in fs])

        # 引擎实际每帧转过几格，跳变按那个步长量。帧数按实际读到的算 ——
        # 快测常常只渲 8~12 帧，那时一格不是 10° 而是 30~45°
        nf_len = len(fs)
        step = max(1, round(spin / FPS / (2 * math.pi / nf_len)))
        xo = []
        for k in range(nf_len):
            a, b = fs[k], fs[(k + step) % nf_len]
            u = (a | b).sum()
            if u:
                xo.append((a ^ b).sum() / u)
        rows.append((nm, dens, iou, (ar.max() - ar.min()) / np.median(ar),
                     (elo.max() - elo.min()) / np.median(elo), px, np.median(xo)))
    # 按"屏幕上的结构量"排 —— 密度再高，画得太小也到不了观众眼里
    for nm, dn, iou, da, de, px, xo in sorted(rows, key=lambda t: -t[1] * t[5] * t[5]):
        print('%-8s %6.0f%% %8.0f %6.2f %6.0f%% %6.0f%% %7.0f %6.0f%%'
              % (nm, dn * 100, dn * px * px / 100, iou, da * 100, de * 100, px, xo * 100))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['--frames']:
        run('', [a[2]], frames_dir=a[1])
    else:
        run(a[0] if a else '.', a[1:] or list(ENGINE))
