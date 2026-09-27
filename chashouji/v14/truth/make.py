"""真相喷雾闺蜜立绘：品红底原图 → 抠像、去品红溢色、裁边、缩放 → 切成两层，打印 foot / muzzle / 转轴（输出贴图像素）。
用法：python3 v14/truth/make.py        → web/assets/world/truth1_up.webp / truth1_lo.webp

src1.png 是用户认可的两张概念图（concept/gift-spray/spray_girl_draft_skirt_A/B.png）改图出的游戏立绘：
同一个人、同一套赛车服短裙过膝靴、同一罐「真相喷雾」，改成侧身朝右、罐子扛在右肩上横着指向右边。
src_alt.png 是同一轮的另一张（罐子短一点、手位不同），备选。

跟平衡车闺蜜（v14/bestie）不同，她是**双手扛着罐子**：两条手臂和罐子缠在一起，分不开单独转手臂，
所以按哥们的做法切两层 —— 腰以上整个（头、头发、躯干、双臂、罐子）绕腰转，腰以下（短裙、腿、靴子）不动：
  web/assets/world/truth1_up.webp  腰以上 + 罐子。**往下垂过腰的长发也归这层**（左边一大片、右边一缕），
                                   不然上身一转，头发在腰那一行被切开错位
  web/assets/world/truth1_lo.webp  腰以下，画在上层之上，盖住腰上的接缝
上身层在腰带下沿往下补 BELLY 行（复制腰那一行），上身转的时候接缝底下垫着的是衣服不是空洞。

量点都按 src1.png 原图像素，换原图要重量。
K：她的头半径约 65 原图像素，×0.46 ≈ 30 = 女主在画面里的头半径（world.json poses.n0.face.a）。"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from build import load_cut, edge_extend

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, 'src1.png')
OUT = os.path.join(HERE, '../../web/assets/world/truth1_%s.webp')
CROP = (250, 6, 1392, 1008)            # 原图裁边框 x0, y0, x1, y1
K = 0.46
CUT = 408                               # 腰以上 / 以下分界 y：腰带下沿、短裙上沿
HAIR_L = (432, 465)                     # 左边长发：x < 432、y < 465 的都归上身层（短裙左沿在 x≈436）
HAIR_R = (660, 460)                     # 右边那缕绿挑染：x ≥ 660、y < 460 归上身层（短裙右沿在 x≈652）
WAIST = (436, 628)                      # 腰那一行躯干的左右端：往下补肚皮的横向范围
BELLY = 22                              # 往下补多少行
WAIST_PIVOT = (545, 405)                # 上身转轴：腰带正中
MUZZLE = (1384, 142)                    # 喷嘴：红盖子最右端、出口那个孔的高度
FOOT_Y, FOOT_X = 1003, 590              # 站地点：前脚靴底那一行，横向取两只脚中间

rgb, al = load_cut(SRC)
# 去品红溢色：红、蓝都高过绿的部分就是幕布渗进来的（金发内侧阴影发粉）。皮肤、白衣服、红盖子都不满足，不受影响
sp = np.clip(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1], 0, None)
rgb[..., 0] -= sp; rgb[..., 2] -= sp
rgb = edge_extend(rgb, al)
x0, y0, x1, y1 = CROP
px = np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8)
H, W = al.shape
yy, xx = np.mgrid[:H, :W]
upm = (yy < CUT) | ((xx < HAIR_L[0]) & (yy < HAIR_L[1])) | ((xx >= HAIR_R[0]) & (yy < HAIR_R[1]))
up, lo = px.copy(), px.copy()
up[~upm] = 0
row = px[CUT - 3, WAIST[0]:WAIST[1]].copy()             # 腰上那一行，往下复制垫在接缝底下
row[..., 3] = np.where(row[..., 3] > 0, 255, 0)
blk = up[CUT:CUT + BELLY, WAIST[0]:WAIST[1]]
up[CUT:CUT + BELLY, WAIST[0]:WAIST[1]] = np.where(blk[..., 3:] > 0, blk, row)
lo[upm & ~(yy >= CUT - 4)] = 0                          # 下层从切线上方 4 行开始，盖住接缝
lo[(yy >= CUT - 4) & upm & ~((xx >= WAIST[0]) & (xx < WAIST[1]))] = 0   # 垂下来的头发只在上层


def save(a, name):
    im = Image.fromarray(a[y0:y1, x0:x1], 'RGBA')
    im = im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS)
    im.save(OUT % name, 'WEBP', quality=90, method=6)
    return im


im = save(up, 'up')
save(lo, 'lo')
tr = lambda p: [round((p[0] - x0) * K), round((p[1] - y0) * K)]
print('size', im.size, 'foot', tr((FOOT_X, FOOT_Y)), 'muzzle', tr(MUZZLE), 'waist', tr(WAIST_PIVOT))
