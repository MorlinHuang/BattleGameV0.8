"""真相女神立绘第二版（2026-09-27）：品红底原图 → 抠像、去品红溢色、裁边、缩放、烘金色外发光 → 单层贴图，打印量点（输出贴图像素）。
用法：python3 v14/truth/make2.py        → web/assets/world/truth2_up.webp

为什么重画：用户要她"更大、更高、不跟闺蜜挤、像一个真正的女神"。第一版立绘（make.py / src1.png）罐子**横着**扛在肩上，
人一抬高、放大，要把罐口压下去对准男生的脸得整个人前倾 0.7~1 rad —— 身子甩出屏幕左上角，只剩一根罐子；
只转上身的话腰要折 1 rad，读成"扛着罐往下倒"（审查：shots/review/goddess/goddess_winline_spec.md）。
src2.png：同一个人、同一套衣服、同一罐「真相喷雾」，改成**竖直悬浮**、头发往后飘、罐子夹在腰侧**本来就斜朝右下**（罐轴约 29°）。
瞄准只剩小幅前后倾，人始终是竖着的。src2_alt.png 是同一轮的另一张备选。

**单层**：她整个人一起倾（crew.js whole），腿不用单独留着不动 —— 所以不切上下身，也就没有腰上的接缝。
**外发光烘进贴图**：三层有色金光（明亮底图上发光靠色相，不能靠 lighter 提亮，见 chashouji-fx）：
  剪影外扩 grow、模糊 blur、颜色 rgb，由外到内画，最后盖上本人。运行时的 ctx.filter 在 Safari 上不可用，所以离线烘。
  贴图四周留 PAD 像素给光晕。光芒、光环会转 / 会呼吸，运行时画（crew.js drawAura）。

量点都按 src2.png 原图像素，换原图要重量。
K：原图人高 ~1407 像素（发顶 31 → 靴底 1438），× 0.4 ≈ 563 = 画面里 s=1 时的身高；头半径 ~70 × 0.4 ≈ 28，跟女主的 30 相当。"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from build import load_cut, edge_extend

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, 'src2.png')
OUT = os.path.join(HERE, '../../web/assets/world/truth2_%s.webp')
CROP = (130, 28, 975, 1442)             # 原图裁边框 x0, y0, x1, y1（剪影包围盒外留几像素）
K = 0.4
PAD = 44                                # 输出贴图四周给外发光留的边（输出像素）
GLOW = [(21, 26, (255, 170, 40)),       # 外扩（MaxFilter 核，奇数）、模糊半径、颜色：橙金
        (9, 10, (255, 225, 120)),       # 金
        (3, 3, (255, 252, 220))]        # 白金（贴着轮廓的一圈亮边）
GLOW_A = 1.0                            # 外发光整体不透明度
# 量点（原图像素）
MUZZLE = (945, 752)                     # 喷嘴：红盖子正中那个出口孔
TAIL = (318, 405)                       # 罐尾：银色尾盖正中（尾焰从这喷出）
GRIP = (480, 493)                       # 罐轴上、前手握的位置 —— 罐轴 = TAIL → MUZZLE，约朝右下 29°
BODY = (440, 620)                       # 整个人前后倾的转轴：腰胯（人的重心附近，倾的时候头和脚一左一右摆，不整个甩出去）
FOOT = (420, 1438)                      # 靴底最低点（悬停时"脚底停在哪"就是它）
HEAD = (548, 112)                       # 头顶（光环悬在它上方）
CHEST = (505, 380)                      # 胸口（身后放射光芒的中心）

rgb, al = load_cut(SRC)
# 去品红溢色：只动半透明的过渡带（不透明的皮肤、白衣服、红盖子本身 R、B 高过 G 是正常颜色）
sp = np.clip(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1], 0, None) * (al < 0.99)
rgb[..., 0] -= sp; rgb[..., 2] -= sp
rgb = edge_extend(rgb, al)
x0, y0, x1, y1 = CROP
px = np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8)
im = Image.fromarray(px[y0:y1, x0:x1], 'RGBA')
im = im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS)

out = Image.new('RGBA', (im.width + 2 * PAD, im.height + 2 * PAD))
body = Image.new('RGBA', out.size); body.alpha_composite(im, (PAD, PAD))
sil = body.split()[3]
for grow, blur, rgb_ in GLOW:
    L = Image.new('RGBA', out.size, rgb_ + (0,))
    a = sil.filter(ImageFilter.MaxFilter(grow)).filter(ImageFilter.GaussianBlur(blur))
    L.putalpha(a.point(lambda v: round(v * GLOW_A)))
    out.alpha_composite(L)
out.alpha_composite(body)
out.save(OUT % 'up', 'WEBP', quality=90, method=6)

tr = lambda p: [round((p[0] - x0) * K + PAD), round((p[1] - y0) * K + PAD)]
import math
rest = -math.atan2(MUZZLE[1] - TAIL[1], MUZZLE[0] - TAIL[0])
print('size', out.size, 'foot', tr(FOOT), 'muzzle', tr(MUZZLE), 'tail', tr(TAIL), 'grip', tr(GRIP),
      'body', tr(BODY), 'head', tr(HEAD), 'chest', tr(CHEST), 'rest', round(rest, 3))
