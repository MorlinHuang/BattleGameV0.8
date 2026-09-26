"""闺蜜立绘：品红底原图 → 抠像、裁边、缩放 → 切成三层，打印 foot / muzzle / 两个转轴（输出贴图像素）。
用法：python3 v14/bestie/make.py [原图，默认 src2.png]

src2.png = src1.png 改图把喷雾罐放大到小灭火器那么大（用户要"更大更夸张"），人和平衡车没动。

输出（同一张画布，叠起来就是原图），画的顺序 arm → up → lo：
  web/assets/world/bestie_arm.webp  伸直的右臂 + 手 + 喷雾罐 —— 绕肩关节 PIVOT 转，喷口对准男生的脸
  web/assets/world/bestie_up.webp   腰以上（头、马尾、躯干、叉腰的左臂）—— 绕腰 WAIST_PIVOT 小幅转（前倾、后坐），
                                    **画在手臂层之上**，肩膀盖住手臂根；肚皮往下补 BELLY 行垫在下层底下
  web/assets/world/bestie_lo.webp   腰以下（比基尼、腿、平衡车）—— 不动，画在最上，盖住腰上的接缝
手臂层从 ARM_X0 起（比切线往里多留一截垫在肩膀底下），上身层从 ARM_X1 起不要手臂 ——
手臂一转，肩膀那里露出来的是手臂根不是空洞。

ARM / CAN / PIVOT / MUZZLE / CUT / WAIST 是按 src2.png 原图量的（手臂整条悬空，只在肩膀一处跟身体连着；
胸口从 y≈310 才开始，所以 y ≤ ARM_Y 的那一段只有手臂；罐子下半截低于 ARM_Y，单独按 CAN 框），换原图要重量。
K：她的头（不算马尾）半径约 75 原图像素，×0.4 = 30 = 女主在画面里的头半径（world.json face.a）。"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from build import cutout, edge_extend

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else 'src2.png')
OUT = os.path.join(HERE, '../../web/assets/world/bestie_%s.webp')
K = 0.4
ARM_X0, ARM_X1, ARM_Y = 630, 660, 300   # 手臂层从 x0 起、身体层到 x1 为止（原图像素），都只管 y ≤ ARM_Y
ARM_TOP, HAND_X = 222, 700              # 肩膀附近只取 y ≥ ARM_TOP 的几行（再往上是脸边那缕头发）；
                                        # 更高的行只有 x ≥ HAND_X 的手和罐子
FEATHER = 12                            # 身体层在切线处渐隐多少像素，底下的手臂层透上来补色，免得留一条硬边
CAN_X, CAN_Y = 935, 345                 # 罐子 + 握罐的手：x ≥ CAN_X、y ≤ CAN_Y 全归手臂层（罐底到 y≈332）
PIVOT = (650, 262)                      # 肩关节
MUZZLE = (1058, 50)                     # 喷头上两个红点的右端（朝右）
CUT = 505                               # 上身 / 下身分界 y：叉腰那只手的指尖之下、比基尼上沿之上
WAIST = (505, 672)                      # 这一行身体的左右端：肚皮往下补的横向范围
BELLY = 26                              # 肚皮往下补多少行（原图像素；上身前倾 ±0.25 rad，腰两端上下错开 ~20）
WAIST_PIVOT = (590, 505)                # 上身的转轴：腰正中

rgb, al = cutout(SRC)
rgb = edge_extend(rgb, al)
ys, xs = np.nonzero(al > 0.5)
x0, x1, y0, y1 = xs.min() - 4, xs.max() + 5, ys.min() - 4, ys.max() + 5
px = np.dstack([rgb, al * 255]).astype(np.uint8)
H, W = al.shape
yy, xx = np.mgrid[:H, :W]
arm = ((yy <= ARM_Y) & (((yy >= ARM_TOP) & (xx >= ARM_X0)) | (xx >= HAND_X))) | ((xx >= CAN_X) & (yy <= CAN_Y))
rot, up, lo = px.copy(), px.copy(), px.copy()
rot[~arm] = 0
ramp = np.clip((ARM_X1 - xx) / FEATHER, 0, 1)           # 切线往里 FEATHER 像素从 1 降到 0
fade = arm & (xx >= ARM_X1 - FEATHER)
up[..., 3] = np.where(fade, up[..., 3] * ramp, up[..., 3]).astype(np.uint8)
up[arm & (xx >= ARM_X1)] = 0
up[CUT:] = 0
row = px[CUT - 3, WAIST[0]:WAIST[1]].copy()             # 腰上那一行肚皮，往下复制
row[..., 3] = np.where(row[..., 3] > 0, 255, 0)
up[CUT:CUT + BELLY, WAIST[0]:WAIST[1]] = row
lo[:CUT - 4] = 0                                          # 下层从切线上方 4 行开始，盖住接缝


def save(a, name):
    im = Image.fromarray(a[y0:y1, x0:x1], 'RGBA')
    im = im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS)
    im.save(OUT % name, 'WEBP', quality=90, method=6)
    return im


save(rot, 'arm')
save(up, 'up')
im = save(px, 'all')                                      # 只用来量站地点，不输出给网页
os.remove(OUT % 'all')
save(lo, 'lo')
a = np.array(im)[..., 3] > 128
ys, xs = np.nonzero(a)
bot = ys.max(); w = xs[ys >= bot - 20]; fx = (w.min() + w.max()) / 2   # 平衡车两个轮子的中间
tr = lambda p: [round((p[0] - x0) * K), round((p[1] - y0) * K)]
print('size', im.size, 'foot', [round(fx), int(bot)], 'muzzle', tr(MUZZLE), 'pivot', tr(PIVOT), 'waist', tr(WAIST_PIVOT))
