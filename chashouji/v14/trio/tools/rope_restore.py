"""G12 kiss 帧：把秋千右绳换回 idle 那一根（审查第八轮 G12 打回，2026-10-01，引擎负责人）。

kiss 是在原立绘画布上局部重绘右臂（inpaint_paste.py），蒙版框从肩一直盖到右绳，生图把框里那段带叶带花的藤绳重出成一根 4 px 的光杆。
画在帧里的布景在场各帧要逐像素相同（第七轮修订第 1 条），所以：
  1. 绳带 = 沿右绳中心线 c(y) ±HW 的一条斜带（c(y) 在 idle 没被手臂挡住的行上量，两段直线拟合）；
  2. 人和绳分层：绳在人后面。KISS_BODY / IDLE_BODY 是两帧里绳带附近"人"（手臂 + 胸侧）的轮廓（原图像素，手量的：
     浅色藤绳芯和皮肤颜色分不开，按颜色自动分会把绳当成手臂）。绳带里 KISS_BODY 以内取 kiss，以外取 idle 的绳；
  3. idle 里被 IDLE_BODY 挡住、kiss 里又露出来的那段绳（手臂挪开了），用同一根绳上方（不够就下方）L 行那一节补齐（按中心线平移，藤蔓是连续的）。

用法：python3 rope_restore.py <idle.png/webp> <kiss.png> <输出.png>"""
import sys
import numpy as np
from PIL import Image, ImageDraw

HW = 14                     # 绳带半宽（绳 13 px 宽 + 叶子）
KISS_BODY = [(160, 100), (195, 103), (198, 100), (215, 102), (218, 109), (202, 117), (202, 126), (207, 145), (207, 171), (201, 177), (193, 182), (160, 182)]
IDLE_BODY = [(160, 100), (190, 104), (199, 133), (204, 141), (225, 120), (249, 105), (253, 114), (229, 134), (215, 158), (212, 183), (160, 183)]


def poly(P, W, H):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon(P, fill=255); return np.array(m) > 0


def centers(a, rows):
    out = []
    for y in rows:
        xs = np.nonzero(a[y, 165:230, 3] > 128)[0] + 165
        if len(xs): out.append((y, (xs.min() + xs.max()) / 2))
    return np.array(out)


def main(idle_p, kiss_p, out_p):
    I = np.array(Image.open(idle_p).convert('RGBA')).astype(np.float32)
    K = np.array(Image.open(kiss_p).convert('RGBA')).astype(np.float32)
    H, W = I.shape[:2]
    kb, ib = poly(KISS_BODY, W, H), poly(IDLE_BODY, W, H)
    # 中心线：手臂上方一段（y 5~60）+ 手臂下方一段（y 190~235）
    up, lo = centers(I, range(5, 60)), centers(I, range(190, 235))
    fit = lambda p: np.polyfit(p[:, 0], p[:, 1], 1)
    fu, fl = fit(up), fit(lo)
    c = lambda y: np.polyval(fu if y < 95 else fl, y)
    X = np.arange(W)
    band = np.zeros((H, W), bool)
    for y in range(0, 245): band[y] = np.abs(X - c(y)) <= HW
    need = band & ib & ~kb                      # idle 里被人挡住、kiss 里要露出来的绳
    rows = sorted(set(np.nonzero(need)[0]))
    rope = I.copy()
    if rows:
        L = rows[-1] - rows[0] + 6
        for y in rows:
            ys = y - L if y - L >= 0 else y + L                  # 上面不够就取下面那一节
            dx = int(round(c(y) - c(ys)))
            src = np.roll(I[ys], dx, axis=0); m = need[y]
            rope[y][m] = src[m]
    O = K.copy()
    sel = band & ~kb
    O[sel] = rope[sel]
    Image.fromarray(O.clip(0, 255).astype(np.uint8), 'RGBA').save(out_p)
    print('中心线 上段', fu.round(3), '下段', fl.round(3), '补的行', (rows[0], rows[-1]) if rows else None, '补的像素', int(need.sum()))


if __name__ == '__main__':
    main(*sys.argv[1:4])
