"""闺蜜立绘：品红底原图 → 抠像、裁边、缩放 → 切成两层，打印 foot / muzzle / pivot（输出贴图像素）。
用法：python3 v14/bestie/make.py [原图，默认 src1.png]

输出（同一张画布，叠起来就是原图）：
  web/assets/world/bestie_rot.webp  伸直的右臂 + 手 + 喷雾罐 —— 绕肩关节 pivot 转，喷口对准男生的脸
  web/assets/world/bestie_fix.webp  其余（身体、头、平衡车）—— 不动，**画在手臂层之上**，肩膀盖住手臂根
手臂层从 ARM_X0 起（比切线往里多留一截垫在肩膀底下），身体层从 ARM_X1 起不要手臂 ——
手臂一转，肩膀那里露出来的是手臂根不是空洞。

ARM / PIVOT / MUZZLE 是按 src1.png 原图量的（手臂整条悬空，只在肩膀一处跟身体连着；
胸口从 y≈310 才开始，所以 y ≤ ARM_Y 的那一段只有手臂），换原图要重量。
K：她的头（不算马尾）半径约 75 原图像素，×0.4 = 30 = 女主在画面里的头半径（world.json face.a）。"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from build import cutout, edge_extend

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else 'src1.png')
OUT = os.path.join(HERE, '../../web/assets/world/bestie_%s.webp')
K = 0.4
ARM_X0, ARM_X1, ARM_Y = 630, 660, 300   # 手臂层从 x0 起、身体层到 x1 为止（原图像素），都只管 y ≤ ARM_Y
ARM_TOP, HAND_X = 222, 700              # 肩膀附近只取 y ≥ ARM_TOP 的几行（再往上是脸边那缕头发）；
                                        # 更高的行只有 x ≥ HAND_X 的手和罐子
FEATHER = 12                            # 身体层在切线处渐隐多少像素，底下的手臂层透上来补色，免得留一条硬边
PIVOT = (650, 262)                      # 肩关节
MUZZLE = (1030, 150)                    # 喷头上那个红点（朝右）

rgb, al = cutout(SRC)
rgb = edge_extend(rgb, al)
ys, xs = np.nonzero(al > 0.5)
x0, x1, y0, y1 = xs.min() - 4, xs.max() + 5, ys.min() - 4, ys.max() + 5
px = np.dstack([rgb, al * 255]).astype(np.uint8)
H, W = al.shape
yy, xx = np.mgrid[:H, :W]
arm = (yy <= ARM_Y) & (((yy >= ARM_TOP) & (xx >= ARM_X0)) | (xx >= HAND_X))
rot, fix = px.copy(), px.copy()
rot[~arm] = 0
ramp = np.clip((ARM_X1 - xx) / FEATHER, 0, 1)           # 切线往里 FEATHER 像素从 1 降到 0
fade = arm & (xx >= ARM_X1 - FEATHER)
fix[..., 3] = np.where(fade, fix[..., 3] * ramp, fix[..., 3]).astype(np.uint8)
fix[arm & (xx >= ARM_X1)] = 0


def save(a, name):
    im = Image.fromarray(a[y0:y1, x0:x1], 'RGBA')
    im = im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS)
    im.save(OUT % name, 'WEBP', quality=90, method=6)
    return im


save(rot, 'rot')
im = save(fix, "fix")
a = np.array(im)[..., 3] > 128
ys, xs = np.nonzero(a)
bot = ys.max(); w = xs[ys >= bot - 20]; fx = (w.min() + w.max()) / 2   # 平衡车两个轮子的中间
tr = lambda p: [round((p[0] - x0) * K), round((p[1] - y0) * K)]
print('size', im.size, 'foot', [round(fx), int(bot)], 'muzzle', tr(MUZZLE), 'pivot', tr(PIVOT))
