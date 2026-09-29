"""哥们立绘：品红底原图 → 抠像、裁边、缩放 → 在腰上切成两层，打印 foot / muzzle / pivot。
用法：python3 v14/buddy/make.py [原图 编号]，默认 skate1.png 1；skate1~10.png → buddy1~10_up|lo.webp
网页用八个（crew.js Buddy.skins：skate1、skate4~10），点一次随机挑一个场上没人用的；
最早的 skate2（反戴红帽）、skate3（金发花衬衫）用户要求删掉，原图和贴图都已删（git 历史里还有）
（一次全出：for i in 1 4 5 6 7 8 9 10; do python3 v14/buddy/make.py skate$i.png $i; done）

2026-09-29 用户嫌三个"整体造型太相近"，留 skate1，加七个借 80/90 后熟知角色的形象（只留认人特征，发型服饰重新设计），
都是 skate1 改图换人，提示词写死"姿势、水枪、枪口、滑板不动，上身挂的东西不许垂过腰"（上身整块绕腰转，垂过裤腰的会断开）：
  skate4 金箍浪子（至尊宝：额头金箍、胡茬、破布短褂、虎纹沙滩裤）
  skate5 格格府贝勒（五阿哥：剃前额长辫到背中、瓜皮帽、敞开宝蓝短马褂）
  skate6 夜色假面绅士（夜礼服假面：高礼帽、白眼罩、叼玫瑰、短披风往后上飘）
  skate7 红发宿敌（八神庵：红发遮一只眼、敞开的黑色高领短夹克、酒红裤配大腿绑带、手上和水箱里的紫火；
         夹克上的新月换成三道爪痕）。第一版把"巴神"理解成了球星巴洛特利（skate7_v1_巴神误解.png），用户纠正是八神庵。
         紫火跟品红幕同色相，品红幕上出图火被键掉、洗成灰青 —— 改成绿幕出（skate7_green.png），
         crewart.cut(…, 'green', (40, 150)) 抠成透明底存 skate7.png（RGBA，load_cut 直接用）。
         火苗往左伸过枪口一点，量出来的 muzzle 比别人左 2 像素，不影响（水从共用的 muzzle 出，还在火里）。
  skate8 刺猬头武道家（悟空：黑刺猬炸毛、橙道服蓝腰带、自创漩涡标志；水枪改"气功水炮"）
  skate9 红发篮球少年（樱木花道：红寸头、红黑 7 号背心，无队名）
  skate10 草帽船长（路飞：草帽绿帽带、红底白扶桑花衬衫、无 X 疤；水枪漆成海盗炮）
实测枪、滑板都在原位（掩码重合 0.9 上下），共用一套常数。礼帽顶、炸毛发尖顶到原图上沿，CROP 上沿从 26 放到 0
（CUT / PIVOT 跟着 +10 输出像素，WAIST 横向不变）。

（已删的 skate2、skate3 当年）是 skate1 改图换人（发型、脸、肤色、衣服、滑板配色），姿势和枪没动 —— 实测枪口、腰、轮子都在
原位 ±2 像素，所以三个共用同一套 CUT / WAIST / PIVOT 和同一个裁边框 CROP（按 skate1 裁；skate3 的金发
高出 6 像素，被切掉的不到 1 个输出像素）。**裁边不能按每张图自己的外框**：头发高低不同，外框一变，
输出贴图里所有点都跟着挪，三个人的 foot / muzzle / pivot 就不一样了。

输出（同一张画布大小，叠起来就是原图）：
  web/assets/world/buddy_up.webp  上半身：头、躯干、双臂、水枪 —— 绕 pivot 转，让枪管对准水流
  web/assets/world/buddy_lo.webp  下半身：沙滩裤、腿、滑板 —— 不动，**画在上层之上**，裤腰盖住接缝
上半身层把肚皮往下补 BELLY 像素（垫在裤腰底下）：上半身一转，裤腰两边露出来的是肚皮不是空洞。

foot = 滑板轮子底边、前后两组轮子的正中（站地点），muzzle = 水枪最左端（枪口）的中点，都是输出贴图像素。
CUT / WAIST / PIVOT 是按 skate1.png ×K 的输出贴图量的（裤腰上沿 y≈193，横跨 228~306），换原图、改 CROP 要重量。"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from build import load_cut, edge_extend

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else 'skate1.png')
OUT = os.path.join(HERE, '../../web/assets/world/buddy%s_%%s.webp' % (sys.argv[2] if len(sys.argv) > 2 else '1'))
CROP = (33, 0, 1218, 1211)    # 原图裁边框 x0, y0, x1, y1（所有形象共用；上沿 0：礼帽、炸毛顶到原图上沿）
K = 0.37          # 缩放：按沙滩裤宽度对齐旧立绘（旧 src1 ×0.34），人一样大
CUT = 196         # 上下两层的分界 y：略低于裤腰上沿，两层在裤腰那几行重叠
WAIST = (226, 309)  # 肚皮往下补的横向范围（裤腰的左右端）
BELLY = 18        # 肚皮往下补多少行
PIVOT = (266, 200)  # 上半身的转轴：裤腰正中

rgb, al = load_cut(SRC)
rgb = edge_extend(rgb, al)
x0, y0, x1, y1 = CROP
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
