#!/usr/bin/env python3
"""进场时同一帧停着的那几格人有没有在滑（修4，crawl / creep / walk 的"位移跟帧走"）。

    python3 crawl_check.py <胶片.jpg|png> <id> <图集.webp> <cellW>x<cellH> <cols> <帧名,…（图集顺序）> <at_x>,<at_y>,<s> <anchor_x>,<anchor_y>

读 film.py 写在胶片旁边的 <胶片>.json（每格画的哪一帧）。每一格拿**这一格实际画的那一帧**整张（alpha > 0.9 的像素）当模板，
在胶片这一格里做遮罩匹配（平方差最小，出画那部分不计），横向从画外到 at 全范围、竖向 ±30 px 搜，抛物线亚像素插值 → 这一格人的位置。
同一个人每一帧是刚体（进场不呼吸），所以整张的位移就是贴墙的手、贴地的手肘的位移。
打印每格位置，和"跟上一格同一帧名"时两格之间的位移（验收 ≤ 2 px）。"""
import sys, json, numpy as np
from PIL import Image
from scipy.signal import fftconvolve

film, aid, atlas, cell, cols, names, at, anc = sys.argv[1:9]
cw, ch = map(int, cell.split('x')); cols = int(cols); names = names.split(',')
ax, ay, s = map(float, at.split(',')); nx, ny = map(float, anc.split(','))
frames = json.load(open(film.rsplit('.', 1)[0] + '.json'))
im = np.array(Image.open(film).convert('RGB')).astype(np.float32) / 255
W = 960
A = np.array(Image.open(atlas).convert('RGBA')).astype(np.float32) / 255


def tmpl(fn):
    i = names.index(fn)
    c = A[(i // cols) * ch:(i // cols + 1) * ch, (i % cols) * cw:(i % cols + 1) * cw]
    if s != 1: c = np.array(Image.fromarray((c * 255).astype(np.uint8)).resize((round(cw * s), round(ch * s)), Image.LANCZOS)).astype(np.float32) / 255
    return c[..., :3], (c[..., 3] > 0.9).astype(np.float32)


def locate(I, T, M, ex, ey, R=(700, 30)):
    """模板左上角的屏幕位置：在期望位置 (ex, ey) 附近搜，画布外补 0、按有效像素数归一化"""
    th, tw = M.shape; PX, PY = R[0] + tw, R[1] + th
    P = np.zeros((I.shape[0] + 2 * PY, I.shape[1] + 2 * PX, 3), np.float32); V = np.zeros(P.shape[:2], np.float32)
    P[PY:PY + I.shape[0], PX:PX + I.shape[1]] = I; V[PY:PY + I.shape[0], PX:PX + I.shape[1]] = 1
    x0, y0 = int(ex) - R[0] + PX, int(ey) - R[1] + PY
    sub, sv = P[y0:y0 + th + 2 * R[1], x0:x0 + tw + 2 * R[0]], V[y0:y0 + th + 2 * R[1], x0:x0 + tw + 2 * R[0]]
    f = lambda a, k: fftconvolve(a, k[::-1, ::-1], mode='valid')
    n = f(sv, M); ssd = f(sv, M * (T ** 2).sum(-1)) * 0
    ssd = sum(f(sv * sub[..., c] ** 2, M) - 2 * f(sv * sub[..., c], M * T[..., c]) + f(sv, M * T[..., c] ** 2) for c in range(3))
    score = np.where(n > 0.25 * M.sum(), ssd / np.maximum(n, 1), np.inf)
    j, i = np.unravel_index(np.argmin(score), score.shape)
    def sub1(a, b, c): d = a - 2 * b + c; return 0.0 if not np.isfinite(d) or d <= 0 else 0.5 * (a - c) / d
    dy = sub1(score[j - 1, i], score[j, i], score[j + 1, i]) if 0 < j < score.shape[0] - 1 else 0
    dx = sub1(score[j, i - 1], score[j, i], score[j, i + 1]) if 0 < i < score.shape[1] - 1 else 0
    return x0 - PX + i + dx, y0 - PY + j + dy, float(score[j, i])


ex, ey = ax - nx * s, ay - ny * s                     # 到位时模板左上角在哪（进场时人在它左 / 右边的画外方向）
prev, worst = None, 0.0
for k, fr in enumerate(frames):
    fn = next((f.split(':', 1)[1] for f in fr if f.startswith(aid + ':')), None)
    if fn is None: print(f'格{k + 1:2d} （没画 {aid}）'); prev = None; continue
    T, M = tmpl(fn)
    x, y, sc = locate(im[:, k * W:(k + 1) * W], T, M, ex, ey)
    line = f'格{k + 1:2d} {fn:7s} 位置 ({x - ex:+8.1f}, {y - ey:+6.1f})  残差 {sc:.4f}'
    if prev and prev[0] == fn:
        d = float(np.hypot(x - prev[1], y - prev[2])); worst = max(worst, d); line += f'   同帧位移 {d:.2f} px'
    print(line); prev = (fn, x, y)
print(f'同一帧名连续格的最大位移 {worst:.2f} px（验收 ≤ 2）')
