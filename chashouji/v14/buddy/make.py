"""哥们立绘：品红底原图 → 抠像、裁边、缩放 → web/assets/world/buddy.webp，并打印 foot / muzzle。
用法：python3 v14/buddy/make.py [原图，默认 skate1.png]
foot = 滑板轮子底边、前后两组轮子的正中（站地点），muzzle = 水枪最左端（枪口）的中点，都是输出贴图像素。"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from build import cutout, edge_extend

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else 'skate1.png')
OUT = os.path.join(HERE, '../../web/assets/world/buddy.webp')
K = 0.37          # 缩放：按沙滩裤宽度对齐旧立绘（旧 src1 ×0.34），人一样大

rgb, al = cutout(SRC)
rgb = edge_extend(rgb, al)
ys, xs = np.nonzero(al > 0.5)
x0, x1, y0, y1 = xs.min() - 4, xs.max() + 5, ys.min() - 4, ys.max() + 5
im = Image.fromarray(np.dstack([rgb, al * 255]).astype(np.uint8)[y0:y1, x0:x1], 'RGBA')
im = im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS)
im.save(OUT, 'WEBP', quality=90, method=6)
a = np.array(im)[..., 3] > 128
ys, xs = np.nonzero(a)
bot = ys.max(); w = xs[ys >= bot - 20]; fx = (w.min() + w.max()) / 2   # 两组轮子的中间
lft = xs.min(); my = ys[xs <= lft + 3].mean()
print('size', im.size, 'foot', [round(fx), int(bot)], 'muzzle', [int(lft), round(my)])
