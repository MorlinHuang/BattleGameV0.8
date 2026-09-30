"""胶片上量锚点漂移（docs/三人组角色规范.md 第八节）。

量法：从图集里取参考帧（idle）上"不动的部位"那一块 + 它的 alpha，按 cfg 的 at / anchor / s 算出它在屏幕上应该在哪；
到胶片每一格的这个位置 ±R 像素里做**遮罩匹配**（只比 alpha > 0.9 的像素，平方差最小），抛物线亚像素插值，
打印每格实际位置 − 应在位置（屏幕像素）。只比人身上的像素，所以背后的地板在滚（镜头跟人走）、飞过去的球挡一下都不影响；
平移 + 模型重画的走样都会现形（樱木出手那格腿短 20px 就是这么量出来的）。

用法（胶片 ammosc=1）：
  python3 drift.py <胶片.png> <格数> <图集.webp> <cellW>x<cellH> <cols> <参考帧下标> x0,y0,x1,y1 <at_x>,<at_y>,<s> <anchor_x>,<anchor_y> [R=12]
  框是参考帧里的格内像素。例（樱木，短裤 + 大腿）：
  python3 drift.py f_sak_atk.png 12 web/assets/trio/B21_sakura.webp 555x208 4 0 330,150,440,200 712,1330,0.95 300.1,199.2
秋千上的人一直绕转轴摆：再给 pivot=<格内 x>,<y> 和 rot=<最大角 rad>，每格先搜摆角（0.005 rad 一档）再搜平移，
打印的 dx / dy 是扣掉摆动之后剩下的位移（= 帧与帧之间人相对秋千漂了多少），ang 是量到的摆角。
  python3 drift.py f_gege_stay.png 12 web/assets/trio/G11_gege.webp 315x343 4 0 60,188,130,214 170,640,1 128,212.3 12 pivot=128,-530 rot=0.25
再给 id=<名单编号> names=<帧名,逗号分隔（图集顺序）>：读胶片旁边 film.py 写的 <胶片>.json，每一格按这一格实际画的那一帧取模板
（出手帧和待机帧的轮廓不一样，拿 idle 当模板去比出手帧，残差大、位置也会被拐走）。参考帧下标只在 json 里没记这个人时用。
"""
import sys
import numpy as np
from PIL import Image
from scipy.signal import fftconvolve

film, n, atlas, cell, cols, idx, box, at, anc = sys.argv[1:10]
R = int(sys.argv[10]) if len(sys.argv) > 10 and '=' not in sys.argv[10] else 24
n, cols, idx = int(n), int(cols), int(idx)
cw, ch = map(int, cell.split('x'))
x0, y0, x1, y1 = map(int, box.split(','))
ax, ay, s = map(float, at.split(','))
kx, ky = map(float, anc.split(','))

A = Image.open(atlas).convert('RGBA')   # 模板 = 参考帧那一块，按 s 缩到屏幕像素
im = np.array(Image.open(film).convert('RGB')).astype(np.float32) / 255
W = im.shape[1] // n
kw = dict(a.split('=') for a in sys.argv[11:] if '=' in a)
piv = tuple(map(float, kw['pivot'].split(','))) if 'pivot' in kw else None
angs = np.arange(-float(kw.get('rot', 0)), float(kw.get('rot', 0)) + 1e-9, 0.004) if piv else [0.0]


def sub(a, b, c):
    d = a - 2 * b + c
    return 0.0 if abs(d) < 1e-12 else 0.5 * (a - c) / d


def search(tile, tc, m, cx, cy):
    """模板中心应在 (cx, cy)，±R 里找带遮罩平方差最小的位置 → (dx, dy, 误差)。
    Σm(I−T)² = Σm·I² − 2Σ(m·T)·I + Σm·T²，前两项是相关，用 FFT 一次算完整个窗口"""
    h, w = m.shape
    ix, iy = int(round(cx - w / 2)), int(round(cy - h / 2))
    win = tile[max(0, iy - R):iy + h + R, max(0, ix - R):ix + w + R]
    oy, ox = max(0, iy - R) - (iy - R), max(0, ix - R) - (ix - R)
    if win.shape[0] < h or win.shape[1] < w: return np.nan, np.nan, np.inf   # 这个摆角下它在画外
    mf = m.astype(np.float32)
    E = sum(fftconvolve(win[..., c] ** 2, mf[::-1, ::-1], mode='valid') - 2 * fftconvolve(win[..., c], (mf * tc[..., c])[::-1, ::-1], mode='valid')
            + (mf * tc[..., c] ** 2).sum() for c in range(3)) / mf.sum()
    y, x = np.unravel_index(np.argmin(E), E.shape)
    e = E[y, x]
    fy = sub(E[y - 1, x], E[y, x], E[y + 1, x]) if 0 < y < E.shape[0] - 1 else 0
    fx = sub(E[y, x - 1], E[y, x], E[y, x + 1]) if 0 < x < E.shape[1] - 1 else 0
    return x + fx - R + ox + (ix - (cx - w / 2)), y + fy - R + oy + (iy - (cy - h / 2)), e


# 各个摆角下的模板（绕模板中心转）+ 它中心应在的屏幕位置（绕 pivot 转）
cx0, cy0 = ax + ((x0 + x1) / 2 - kx) * s, ay + ((y0 + y1) / 2 - ky) * s


def frame_patch(k):
    f = A.crop(((k % cols) * cw, (k // cols) * ch, (k % cols) * cw + cw, (k // cols) * ch + ch)).crop((x0, y0, x1, y1))
    return f.resize((round(f.width * s), round(f.height * s)), Image.LANCZOS)


def templates(fr):
  tpls = []
  for a in angs:
      im_t = fr.rotate(-np.degrees(a), resample=Image.BICUBIC, expand=True)
      t = np.array(im_t).astype(np.float32) / 255
      if piv:
          pxs, pys = ax + (piv[0] - kx) * s, ay + (piv[1] - ky) * s
          c, sn = np.cos(a), np.sin(a)
          cx, cy = pxs + (cx0 - pxs) * c - (cy0 - pys) * sn, pys + (cx0 - pxs) * sn + (cy0 - pys) * c
      else:
          cx, cy = cx0, cy0
      tpls.append((a, t[..., :3], t[..., 3] > 0.9, cx, cy))
  return tpls


names = kw['names'].split(',') if 'names' in kw else None
log = None
if 'id' in kw:
    import json, os
    jf = film.rsplit('.', 1)[0] + '.json'
    log = json.load(open(jf)) if os.path.exists(jf) else None
cache = {}

worst = 0
for i in range(n):
    tile = im[:, i * W:(i + 1) * W]
    k, lab = idx, ''
    if log and names:
        hit = [e.split(':')[1] for e in log[i] if e.split(':')[0] == kw['id']]
        if not hit: print(f'格{i + 1:2d}  （不在场）'); continue
        k, lab = names.index(hit[0]), hit[0]
    if k not in cache: cache[k] = templates(frame_patch(k))
    tpls = cache[k]
    best = min(((a,) + search(tile, tc, m, cx, cy) for a, tc, m, cx, cy in tpls), key=lambda q: q[3])
    a, dx, dy, e = best
    worst = max(worst, abs(dx), abs(dy))
    print(f'格{i + 1:2d}  {lab:7s} dx {dx:+6.2f}  dy {dy:+6.2f}' + (f'  摆角 {a:+.3f}' if piv else '') + f'  残差 {e:.4f}')
print(f'最大漂移 {worst:.2f}px')
