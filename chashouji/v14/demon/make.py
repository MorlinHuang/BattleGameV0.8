"""灭迹恶魔立绘（男生档 4，2026-09-27）：绿幕原图 → 抠像、去绿溢色、裁边、缩放、烘三层外发光 → 单层贴图，打印量点（输出贴图像素）。
用法：python3 v14/demon/make.py        → web/assets/world/demon1_up.webp

用户：「男生这边可以召唤一个男恶魔，对应对方的女神」。跟真相女神（v14/truth/make2.py）左右对称：竖直悬浮、面朝左，
腰侧夹一罐「一键清空」、罐口本来就斜朝左下（罐轴约 28°），瞄准只剩小幅前后倾；蝙蝠翼、小角、尾巴，黑 + 暗紫 + 酒红。
src1.png 是挑中的那张。src_alt_glow.png 是同一轮另一张（自带透明底，但模型把紫光晕画进了图里，不好调，只留作参考）。

**用绿幕不用品红**：他一身暗紫、酒红，品红度 min(R,B) − G 在紫色翅膀上高达 100+，按品红抠会把翅膀和衬衫抠成半透明。
绿键 k = G − max(R,B)：角色身上没有绿色，k 只在幕布上大。
外发光烘进贴图（运行时 ctx.filter 在 Safari 上不可用）：由外到内 暗红 → 紫 → 品红（明亮底图上发光靠色相）。
量点都按 src1.png 原图像素，换原图要重量。K：原图人高 ~1453（角尖 26 → 靴底 1479），× 0.35 ≈ 510。"""
import os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, 'src1.png')
OUT = os.path.join(HERE, '../../web/assets/world/demon1_%s.webp')
CROP = (20, 20, 1016, 1485)             # 原图裁边框 x0, y0, x1, y1
K = 0.35
PAD = 44                                # 四周给外发光留的边（输出像素）
KEY = (40, 90)                          # 绿键：k ≤ 40 全不透明，k ≥ 130 全透明，中间线性
GLOW = [(21, 26, (160, 20, 60)),        # 外扩（MaxFilter 核，奇数）、模糊半径、颜色：暗红
        (9, 10, (170, 60, 230)),        # 紫
        (3, 3, (255, 120, 220))]        # 品红（贴着轮廓的一圈亮边）
MUZZLE = (47, 767)                      # 喷嘴：紫盖子正中那个出口孔
TAIL = (715, 405)                       # 罐尾：银色尾盖正中
BODY = (510, 630)                       # 前后倾的转轴：腰胯
FOOT = (590, 1479)                      # 靴尖最低点
HEAD = (478, 62)                        # 头顶（两只角中间；角的光运行时画在这）
CHEST = (470, 330)                      # 胸口（身后烟雾、裂光的中心）

a = np.array(Image.open(SRC).convert('RGB')).astype(np.int16)   # int16：uint8 相减会下溢（genimage-magenta-cutout）
k = a[..., 1] - np.maximum(a[..., 0], a[..., 2])
al = np.clip(1 - (k - KEY[0]) / KEY[1], 0, 1)
rgb = a.astype(np.float32)
edge = al < 0.99                        # 去绿溢色只动半透明过渡带
rgb[..., 1] = np.where(edge, np.minimum(rgb[..., 1], np.maximum(rgb[..., 0], rgb[..., 2])), rgb[..., 1])
# 边缘颜色扩散：透明区的 RGB 仍是整片绿，LANCZOS 缩放会把它混进边缘（同 build.py edge_extend）
mask = al > 0.03
for _ in range(10):
    m = mask.astype(np.float32); ker = np.ones((3, 3), np.float32)
    cnt = ndimage.convolve(m, ker, mode='constant')
    acc = np.stack([ndimage.convolve(rgb[..., c] * m, ker, mode='constant') for c in range(3)], -1)
    fill = (cnt > 0) & ~mask
    if not fill.any(): break
    rgb[fill] = (acc / np.maximum(cnt, 1)[..., None])[fill]; mask |= cnt > 0
x0, y0, x1, y1 = CROP
px = np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8)
im = Image.fromarray(px[y0:y1, x0:x1], 'RGBA')
im = im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS)

out = Image.new('RGBA', (im.width + 2 * PAD, im.height + 2 * PAD))
body = Image.new('RGBA', out.size); body.alpha_composite(im, (PAD, PAD))
sil = body.split()[3]
for grow, blur, c in GLOW:
    L = Image.new('RGBA', out.size, c + (0,))
    L.putalpha(sil.filter(ImageFilter.MaxFilter(grow)).filter(ImageFilter.GaussianBlur(blur)))
    out.alpha_composite(L)
out.alpha_composite(body)
out.save(OUT % 'up', 'WEBP', quality=90, method=6)

import math
tr = lambda p: [round((p[0] - x0) * K + PAD), round((p[1] - y0) * K + PAD)]
rest = -math.atan2(MUZZLE[1] - TAIL[1], TAIL[0] - MUZZLE[0])   # 朝左的仰角（朝下为负）
print('size', out.size, 'foot', tr(FOOT), 'muzzle', tr(MUZZLE), 'tail', tr(TAIL), 'body', tr(BODY),
      'head', tr(HEAD), 'chest', tr(CHEST), 'rest', round(rest, 3))
