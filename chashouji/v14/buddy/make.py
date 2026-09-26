"""哥们立绘：品红底原图 → 抠像、裁边、缩放 → 在腰上切成两层，打印 foot / muzzle / pivot。
用法：python3 v14/buddy/make.py [原图，默认 skate1.png]

输出（同一张画布大小，叠起来就是原图）：
  web/assets/world/buddy_up.webp  上半身：头、躯干、双臂、水枪 —— 绕 pivot 转，让枪管对准水流
  web/assets/world/buddy_lo.webp  下半身：沙滩裤、腿、滑板 —— 不动，**画在上层之上**，裤腰盖住接缝
上半身层把肚皮往下补 BELLY 像素（垫在裤腰底下）：上半身一转，裤腰两边露出来的是肚皮不是空洞。

foot = 滑板轮子底边、前后两组轮子的正中（站地点），muzzle = 水枪最左端（枪口）的中点，都是输出贴图像素。
CUT / WAIST / PIVOT 是按 skate1.png ×K 的输出贴图量的（裤腰上沿 y≈183，横跨 228~306），换原图要重量。"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from build import cutout, edge_extend

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else 'skate1.png')
OUT = os.path.join(HERE, '../../web/assets/world/buddy_%s.webp')
K = 0.37          # 缩放：按沙滩裤宽度对齐旧立绘（旧 src1 ×0.34），人一样大
CUT = 186         # 上下两层的分界 y：略低于裤腰上沿，两层在裤腰那几行重叠
WAIST = (226, 309)  # 肚皮往下补的横向范围（裤腰的左右端）
BELLY = 18        # 肚皮往下补多少行
PIVOT = (266, 190)  # 上半身的转轴：裤腰正中

rgb, al = cutout(SRC)
rgb = edge_extend(rgb, al)
ys, xs = np.nonzero(al > 0.5)
x0, x1, y0, y1 = xs.min() - 4, xs.max() + 5, ys.min() - 4, ys.max() + 5
im = Image.fromarray(np.dstack([rgb, al * 255]).astype(np.uint8)[y0:y1, x0:x1], 'RGBA')
im = im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS)
px = np.array(im)
up, lo = px.copy(), px.copy()
up[CUT:] = 0
row = px[CUT - 3, WAIST[0]:WAIST[1]].copy()          # 裤腰上方那一行肚皮，往下复制
row[..., 3] = np.where(row[..., 3] > 0, 255, 0)
up[CUT:CUT + BELLY, WAIST[0]:WAIST[1]] = row
lo[:CUT - 4] = 0                                       # 下层从裤腰上沿开始
Image.fromarray(up).save(OUT % 'up', 'WEBP', quality=90, method=6)
Image.fromarray(lo).save(OUT % 'lo', 'WEBP', quality=90, method=6)
a = px[..., 3] > 128
ys, xs = np.nonzero(a)
bot = ys.max(); w = xs[ys >= bot - 20]; fx = (w.min() + w.max()) / 2   # 两组轮子的中间
lft = xs.min(); my = ys[xs <= lft + 3].mean()
print('size', im.size, 'foot', [round(fx), int(bot)], 'muzzle', [int(lft), round(my)], 'pivot', list(PIVOT))
