"""G10 待机扛着的球棒：3D 球棒图集的一格静帧做成挂件层（审查第八批打回：球棒太小读成瓶子；规范第十轮修订第 2 条：手持道具屏幕长边 ≥ 人高 1/3）。
写法同 G5 腰挂算盘（G5_tong/abacus_part.py）：挂件图和出手时飞出去的 3D 图集是同一个造型、同一个长度、同一个颜色。

为什么不用 hold.idle：引擎画手里的 3D 道具是在 hold 点居中、按一个随机的初始角挑格子再慢慢转（b.hang），摆不出"握把在拳里、棍身斜着"。
取 prop_bat_v2.webp 里棍身最竖、粗头朝上的那一格（二阶矩主轴），转正成竖直再往前倒 TILT 度（粗头往右上，让开脸），
缩到和飞出去那一刻一样长：3D 每格 cell 168 画成 2 r × scale = 142.8 屏幕 px（0.85 屏幕 px / 格内 px），挂件跟人一起按 at.s 缩，所以挂件图 = 格内 × 0.85 / S。
pivot = 握把上离尾端 GRIP 那一点（拳头中心），挂在 idle 的拳头上、画在人后面（z −1），拳头正好盖住握把 = 握在拳里。
idle 帧的拳头举在下巴前：棍身往后斜靠肩的话大半藏在头和马尾后面（或者横过脸），认不出是球棒；所以往前倒一点立在拳头上，全长露在背景上。
人的 at.s 改了要重跑（S）。在 v14/trio/bestie/G10_harley 下：python3 bat_part.py"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, '../../../../web/assets/trio')
CELL, COLS, N = 168, 6, 36
R, SCALE = 68, 1.05                     # trio_bestie.js G10 atk：r 68、atlas.scale 1.05
S = 0.86                                # G10 at.s
TILT = 16                               # 竖直往前（右）倒多少度
GRIP = 0.13                             # 拳头中心离尾端多远（占全长）

a = Image.open(os.path.join(WEB, 'prop_bat_v2.webp')).convert('RGBA')
best = None
for i in range(N):
    c = a.crop((i % COLS * CELL, i // COLS * CELL, i % COLS * CELL + CELL, i // COLS * CELL + CELL))
    al = np.array(c)[..., 3] > 40
    ys, xs = np.nonzero(al)
    x, y = xs - xs.mean(), ys - ys.mean()
    ang = 0.5 * np.degrees(np.arctan2(2 * (x * y).mean(), (x * x).mean() - (y * y).mean()))   # 主轴相对水平（图像 y 朝下）
    off = abs(abs(ang) - 90)                                                                # 离竖直多少度
    top = (y < 0).sum() and np.abs(x[y < -y.std()]).mean() > np.abs(x[y > y.std()]).mean()  # 粗头（上半截更宽）朝上
    length = np.hypot(x, y).max() * 2
    if top and (best is None or off < best[0]): best = (off, i, c, ang, length)
off, FRAME, c, ang, length = best
c = c.rotate(-(90 - abs(ang)) * np.sign(ang) if ang else 0, resample=Image.BICUBIC, expand=True)   # 主轴转成竖直
c = c.crop(c.getbbox())
k = (2 * R * SCALE / CELL) / S                                                          # 格内 px → 挂件 px
c = c.resize((round(c.width * k), round(c.height * k)), Image.LANCZOS)
w, h = c.size
gx, gy = w / 2, h * (1 - GRIP)                                                          # 握点（竖直时）
out = c.rotate(-TILT, resample=Image.BICUBIC, expand=True)
# rotate(expand) 把画布扩大了：握点的新位置 = 绕原图中心转 −TILT 以后再平移到新画布中心
th = np.radians(TILT)
cx, cy = w / 2, h / 2
dx, dy = gx - cx, gy - cy
px = out.width / 2 + dx * np.cos(th) - dy * np.sin(th)
py = out.height / 2 + dx * np.sin(th) + dy * np.cos(th)
bb = out.getbbox(); out = out.crop(bb); px -= bb[0]; py -= bb[1]
out.save(os.path.join(WEB, 'G10_bat.webp'), 'WEBP', quality=92, method=6)
print('图集第 %d 格（离竖直 %.1f°）→ 挂件 %dx%d  pivot [%.1f, %.1f]  屏幕长边 %.0f px（× S）' % (FRAME, off, out.width, out.height, px, py, h * S))
