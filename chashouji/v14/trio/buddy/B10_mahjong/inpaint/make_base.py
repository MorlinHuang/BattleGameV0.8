"""B10 走路条蒙版重绘底图 + 蒙版（同 B5，审查_样板 7.2 的做法）。
底 = raw/walk_gen1.png 第一行：walk1（远侧腿在前、近侧腿在后踮脚，近侧手拎马扎在身后）、walk2（近侧腿提起过渡）。头和躯干全程不动。
行 1：walk1 不动 | walk2 只重绘近侧手臂 + 马扎（手垂在胯边）
行 2：walk1 副本 → walk3（近侧腿在前）| walk2 副本 → walk4（近侧腿撑地、远侧腿提起）：腿 + 两臂 + 马扎重绘
行 3：原 plop / idle 不动。蒙版 alpha 0 = 重绘。"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
src = Image.open('raw/walk_gen1.png').convert('RGBA'); W, H = src.size
base = Image.new('RGBA', (W, H), (255, 0, 255, 255)); base.alpha_composite(src)
row2 = base.crop((0, 0, W, 515)); cut = Image.new('RGBA', (W, 515), (255, 0, 255, 255)); base.paste(cut, (0, 515)); base.paste(row2, (0, 515))
base.convert('RGB').save('inpaint/base.png')
A = np.array(src)[..., 3] > 100
T1 = [(190, 12), (312, 12), (312, 110), (305, 140), (308, 200), (322, 250), (340, 290), (345, 330), (195, 330), (188, 280), (185, 220), (192, 170), (195, 110)]
T2 = [(x + 480, y) for x, y in T1]
keep = np.zeros((H, W), bool)
def poly(p, dy=0):
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).polygon([(x, y + dy) for x, y in p], fill=255); return np.array(m) > 0
keep[:515, :512] = A[:515, :512] | (np.arange(512)[None, :] >= 0)          # 行 1 左：walk1 整格保留
k2 = poly(T2); legs2 = np.zeros((H, W), bool); legs2[330:510, 600:845] = A[330:510, 600:845]
fist2 = np.zeros((H, W), bool); fist2[240:310, 630:700] = A[240:310, 630:700]
keep |= k2 | legs2 | fist2                                                   # 行 1 右：躯干 + 腿 + 远侧拳保留，重绘近侧臂 + 马扎
keep |= poly(T1, 515) | poly(T2, 515)                                        # 行 2：只保留头 + 躯干
keep[1025:, :] = True                                                         # 行 3 全保留
k = Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
mask = Image.new('RGBA', (W, H), (0, 0, 0, 0)); mask.putalpha(k); mask.save('inpaint/mask.png')
vis = base.copy(); vis.paste(Image.new('RGBA', (W, H), (0, 200, 255, 255)), (0, 0), Image.fromarray(255 - np.array(k)))
vis.convert('RGB').resize((W // 2, H // 2)).save('inpaint/mask_vis.jpg', quality=85)
