"""被拉倒各档的头收回到僵持（n0）一样大（2026-09-26）。

build.py 现在按**身体**把这几档整张放大（BODY 表），可这几张生图本来就是头大身小 ——
身体对齐了，头就大出 8%~20%。这里在原图上对每个人的头做一次局部收缩（液化里的"缩拢"）：
- 中心放在脸中心往下巴挪半个半径处，头顶往下收、脖子只被轻轻拉一点，头不会跟身子脱开；
- 半径 R0 以内整体缩 f，R0 到 R1 = 2.1·R0 之间平滑过渡回原样（smoothstep），外面一个像素不动。
  头发、肩膀在过渡带里渐变，不会出现切口。
- base 和 7 格步态用同一组参数（步态只重画了腿，头和 base 一模一样）。

头量法：把原图按 build.py 出图时的缩放缩小，跟 n0 的成品贴图做多尺度 NCC（build.head_find 的做法，
但尺度放宽到 0.8~1.4 —— build 里上限 1.12，这几张的头正好顶到上限，读数被截断）。
缩到 1.03 以内的不动。原图备份在各目录 old_heads1/。
"""
import os, sys, shutil, json
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.signal import fftconvolve

V14 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(V14, 'build.py')).read()
B = {'__file__': os.path.join(V14, 'build.py')}
exec(compile(src[:src.index("if __name__")], 'build.py', 'exec'), B)

POSES = {'aK': 'pose/21_女优_男跪.png', 'aF': 'pose/22_女优_男扑倒.png', 'aL': 'pose/23_女优_男趴.png',
         'bK': 'pose/24_男优_女跪.png', 'bF': 'pose/25_男优_女扑倒.png', 'bL': 'pose/26_男优_女趴.png'}
TOL = 1.03


def head_find(ref, im, side, ks=np.arange(0.80, 1.41, 0.01)):
    b = [round(v * B['SCALE'] / B['HEAD_AT']) for v in B['HEAD'][side]]
    T = B['_gray'](ref)[b[1]:b[3], b[0]:b[2]]
    G = B['_gray'](im); w = G.shape[1]
    off = 0 if side == 'a' else w // 2 - 60
    G = G[:, :w // 2 + 60] if side == 'a' else G[:, off:]
    best = (-1, 1.0, 0, 0, 0, 0)
    for k in ks:
        t = np.array(Image.fromarray(T).resize((round(T.shape[1] * k), round(T.shape[0] * k)), Image.LANCZOS))
        t = t - t.mean(); tt = (t ** 2).sum(); ones = np.ones_like(t)
        num = fftconvolve(G, t[::-1, ::-1], 'valid')
        s1 = fftconvolve(G, ones, 'valid'); s2 = fftconvolve(G ** 2, ones, 'valid')
        var = s2 - s1 * s1 / t.size
        r = np.where(var > 0.3 * tt, num / np.sqrt(np.maximum(var, 1) * tt), 0)
        i = np.unravel_index(r.argmax(), r.shape)
        if r[i] > best[0]:
            best = (r[i], k, i[1], i[0], t.shape[1], t.shape[0])
    _, k, x, y, tw, th = best
    return k, off + x + tw / 2, y + th / 2, tw / 2


def measure(name):
    """原图坐标下每个人头的 (k, cx, cy, r)"""
    ref = Image.open(os.path.join(V14, '..', 'web', 'assets', 'world', 'pose_n0.webp')).convert('RGBA')
    s = B['SCALE'] / B['BODY'][name]
    rgb, al = B['cutout'](os.path.join(V14, POSES[name]))
    im = Image.fromarray(np.concatenate([rgb, al[..., None] * 255], -1).astype(np.uint8), 'RGBA')
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    out = {}
    for side in 'ab':
        k, cx, cy, r = head_find(ref, im, side)
        out[side] = (k, cx / s, cy / s, r / s)
    return out


def pinch(rgb, cx, cy, r, f):
    """以 (cx, cy) 为心、r 为头半径，把头缩 f（<1）。反向映射：输出半径 ρ 取源半径 ρ·g(ρ)"""
    H, W = rgb.shape[:2]
    R0, R1 = r * 1.05, r * 2.1
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = xx - cx, yy - cy
    rho = np.sqrt(dx * dx + dy * dy)
    a = R0 * f                                   # 输出里头的边
    t = np.clip((rho - a) / (R1 - a), 0, 1); t = t * t * (3 - 2 * t)
    g = (1 / f) * (1 - t) + t
    sx, sy = cx + dx * g, cy + dy * g
    out = np.stack([ndimage.map_coordinates(rgb[..., c].astype(np.float32), [sy, sx], order=1, mode='nearest')
                    for c in range(3)], -1)
    return np.clip(out.round(), 0, 255).astype(np.uint8)


def apply(path, heads):
    rgb = np.array(Image.open(path).convert('RGB'))
    for side, (k, cx, cy, r) in heads.items():
        if k > TOL:
            rgb = pinch(rgb, cx, cy + 0.5 * r, r, 1 / k)
    Image.fromarray(rgb).save(path)


if __name__ == '__main__':
    names = [n for n in sys.argv[1:] if n != '--dry'] or list(POSES)
    dry = '--dry' in sys.argv
    for n in names:
        h = measure(n)
        print(n, {s: 'k %.2f' % v[0] for s, v in h.items()}, flush=True)
        if dry:
            p = f'/tmp/heads_{n}.png'; shutil.copy2(os.path.join(V14, POSES[n]), p); apply(p, h); continue
        paths = [os.path.join(V14, POSES[n])] + [os.path.join(V14, 'gait', n, f + '.png')
                                                  for f in ['base'] + [f'f{i}' for i in range(1, 8)]]
        for p in paths:
            d = os.path.join(os.path.dirname(p), 'old_heads1'); os.makedirs(d, exist_ok=True)
            if not os.path.exists(os.path.join(d, os.path.basename(p))):
                shutil.copy2(p, d)
            apply(p, h)
