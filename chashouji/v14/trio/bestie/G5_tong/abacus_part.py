"""G5 腰挂算盘换成 3D 算盘的一格静帧（审查第五批打回 / 规范第七轮修订第 2 条：挂件图和同一件东西的 3D 图集是同一个造型）。

取 prop_abacus.webp 最正面那一格（FRAME，框和 3 × 3 颗大珠全露、侧转最少），按二阶矩转正（长边水平），
缩到屏幕长边 LONG px：3D 那张每格 cell 115 画成 2 r × scale = 108 屏幕 px（0.939 屏幕 px / 格内 px），
这一格转正以后本体长边 × 0.939 = 87 屏幕 px；审查按外框量的 3D 长边（36 格转着量）是 97~108、中位 107。
取 90：比本体大 3%、比外框中位小 16%，两种量法都在 ±20% 里（96 时 follow 帧挂件下沿碰到地板 G29 的头，combo_scan 认人点 31 px）。挂件跟人一起按 at.s 缩，所以挂件图长边 = LONG / S。上沿中间画一根红吊绳（V 形两股收到一个结），pivot = 绳结。
人的 at.s 改了要重跑（S）。在 v14/trio/bestie/G5_tong 下：python3 abacus_part.py"""
import os, numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, '../../../../web/assets/trio')
FRAME, CELL, COLS = 0, 115, 6
R, SCALE = 40, 1.35                     # trio_bestie.js G5 atk：r 40、atlas.scale 1.35
S = 0.84                                # G5 at.s
LONG = 90                               # 屏幕长边（不算绳）
ROPE_H, ROPE = 10, (192, 40, 36)        # 绳结在框上沿往上多高（挂件像素）、红绳颜色

a = Image.open(os.path.join(WEB, 'prop_abacus.webp')).convert('RGBA')
c = a.crop((FRAME % COLS * CELL, FRAME // COLS * CELL, FRAME % COLS * CELL + CELL, FRAME // COLS * CELL + CELL))
al = np.array(c)[..., 3] > 40
ys, xs = np.nonzero(al)
x, y = xs - xs.mean(), ys - ys.mean()
ang = 0.5 * np.degrees(np.arctan2(2 * (x * y).mean(), (x * x).mean() - (y * y).mean()))   # 长轴相对水平的角（图像 y 朝下）
c = c.rotate(ang, resample=Image.BICUBIC, expand=True)
c = c.crop(c.getbbox())
k = LONG / S / max(c.size)
c = c.resize((round(c.width * k), round(c.height * k)), Image.LANCZOS)
w, h = c.size
out = Image.new('RGBA', (w + 4, h + ROPE_H + 4), (0, 0, 0, 0))
out.alpha_composite(c, (2, ROPE_H + 2))
d = ImageDraw.Draw(out)
knot = (2 + w // 2, 2)
for fx in (0.3, 0.7):                   # 两股：先描深边再画红
    p = [(2 + round(w * fx), ROPE_H + 6), knot]
    d.line(p, fill=(60, 12, 12, 255), width=5)
for fx in (0.3, 0.7):
    d.line([(2 + round(w * fx), ROPE_H + 6), knot], fill=ROPE + (255,), width=3)
d.ellipse((knot[0] - 4, knot[1], knot[0] + 4, knot[1] + 7), fill=ROPE + (255,), outline=(60, 12, 12, 255), width=1)
out.alpha_composite(c, (2, ROPE_H + 2))    # 框压在绳脚上面（绳子从框后面穿出来）
out.save(os.path.join(WEB, 'G5_abacus.webp'), 'WEBP', quality=90, method=6)
print('本体 × 0.939 = %.0f 屏幕 px；' % (max(c.size) / k * 2 * R * SCALE / CELL), end='')
print('rot %.1f°  part %dx%d  pivot [%d, %d]  屏幕长边 %.0f px（× S）' % (ang, out.width, out.height, knot[0], knot[1] + 1, w * S))
