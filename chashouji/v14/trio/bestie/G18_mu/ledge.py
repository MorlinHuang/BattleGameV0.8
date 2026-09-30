"""G18 墙沿场景层（审查第五批打回 / 规范第七轮修订第 4 条：名单写"单膝落在墙沿"，墙沿要画出来）。parts fixed: true, z −1。

程序画（上沿要逐像素落在脚底那一行，生图做不到），写法同 buddy/make_ledges.py：按 K 倍画、描深边，缩到格内像素（和帧同一个单位）。
一截城墙顶，侧着看有厚度：
  · 墙顶面（青砖铺地，浅灰）从 TOP 到 EDGE —— 站姿是 3/4 侧身，后脚（近）脚底在格内 y 346、前脚（远）在 323，
    两只脚都要踩在墙顶上，所以墙顶面是一条带：前沿 EDGE = 346 = land 单膝 / 脚尖、idle 后脚、rise 后脚的最低一行，后沿 TOP = 314；
  · 墙面（青砖错缝，深灰）从 EDGE 往下 FACE px，最后 FADE px 渐隐（不然一截墙浮在半空）；
  · 左端出画（格内 x X0，屏幕 x < 0），右端 X1 收一个墙角（竖描边 + 暗面）。
修12（2026-10-01 主控拍板方案 A：落脚区 G18 × G8，G8 蓄力瞄男主的冰锥扫过 G18 左靴，只改 at 无解）：人挪到 at [496, 640, 0.88]，
墙往左接长 134（X0 −206 → −340），左端仍在屏幕 x −44 出画。砖缝 / 方砖按格内坐标铺（原点仍是旧左端 X0_OLD），
原来那 536 格内 px 的墙逐砖同色（同一个 rng 同一个顺序），新接的一截砖色用另一个 rng —— 人脚下那一段和已签版逐像素一致。
cfg：pivot [0, 0]，at [X0, TOP, 0]。在 v14/trio/bestie/G18_mu 下：python3 ledge.py"""
import os
import numpy as np
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio')
K = 3
INK = (40, 36, 38, 255)
X0, X1, TOP, EDGE, FACE, FADE = -340, 330, 314, 346, 64, 34     # X0：at x 496 时左端在屏幕 x −44（出画）
X0_OLD = -206                                                   # 已签版的左端：砖缝、砖色都从这里起铺（OX = 往左接出来的那一截）
TOPC, TOPH, SEAM = (178, 180, 182, 255), (206, 208, 210, 255), (132, 134, 138, 255)
FACEC = [(118, 120, 126), (108, 110, 116), (126, 128, 134), (100, 102, 108)]
MORTAR = (80, 82, 88, 255)

W, H = X1 - X0, EDGE - TOP + FACE
OX, WO = X0_OLD - X0, X1 - X0_OLD
s = lambda v: int(round(v * K))
im = Image.new('RGBA', (s(W), s(H)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
rng, rng_ext = np.random.default_rng(18), np.random.default_rng(1818)
top_h = EDGE - TOP
# 墙顶面：浅灰，方砖接缝往远处（上）收窄一点，后沿一道细亮边
d.rectangle([0, 0, s(W), s(top_h)], fill=TOPC)
d.rectangle([0, s(top_h - 5), s(W), s(top_h)], fill=TOPH)                      # 前沿倒角高光：人踩的那条线读得清
for j, y in enumerate((9, 19)):
    d.line([(0, s(y)), (s(W), s(y))], fill=SEAM, width=s(0.8))
for x in range(-(OX // 34 + 1) * 34 + OX, W, 34):                              # 方砖竖缝（近大远小：上面错开半块）；x 取 OX + 34k（按旧左端起铺）
    d.line([(s(x), s(19)), (s(x), s(top_h - 5))], fill=SEAM, width=s(0.8))
    d.line([(s(x + 17), s(9)), (s(x + 17), s(19))], fill=SEAM, width=s(0.7))
    d.line([(s(x + 8), 0), (s(x + 8), s(9))], fill=SEAM, width=s(0.6))
# 墙面：青砖错缝，每块颜色抖一点
BW, BH = 30, 11
ext = range(-BW - ((OX + BW) // BW + 1) * BW, -BW, BW)                          # 接出来那一截的砖（旧坐标，在旧左端再往左）
for r, y in enumerate(range(top_h, H, BH)):
    off = (BW // 2) if r % 2 else 0
    cols = [(x, rng) for x in range(-BW, WO + BW, BW)] + [(x, rng_ext) for x in ext]   # 旧砖先抽色（顺序同已签版），新砖后抽
    for x, g in cols:
        c = FACEC[g.integers(len(FACEC))] + (255,)
        d.rectangle([s(x + OX + off), s(y), s(x + OX + off + BW), s(y + BH)], fill=c, outline=MORTAR, width=s(1))
d.rectangle([0, s(top_h), s(W), s(top_h + 4)], fill=(90, 92, 98, 255))       # 墙顶压在墙面上的一道影
# 右端墙角：暗面 + 竖描边
d.rectangle([s(W - 8), s(top_h), s(W), s(H)], fill=(84, 86, 92, 255))
d.line([(s(W - 8), s(top_h)), (s(W - 8), s(H))], fill=INK, width=s(1.2))
d.line([(s(W) - 2, 0), (s(W) - 2, s(H))], fill=INK, width=s(2))
# 描边：后沿、前沿（人站的那条线描粗）
d.line([(0, 1), (s(W), 1)], fill=INK, width=s(1.5))
d.line([(0, s(top_h)), (s(W), s(top_h))], fill=INK, width=s(2))
a = np.array(im); h = a.shape[0]
for y in range(s(H - FADE), h):                                                 # 下半截渐隐
    a[y, :, 3] = (a[y, :, 3] * max(0.0, 1 - (y - s(H - FADE)) / (h - s(H - FADE)))).astype(np.uint8)
im = Image.fromarray(a).resize((W, H), Image.LANCZOS)
im.save(os.path.join(OUT, 'G18_ledge.webp'), 'WEBP', quality=92)
al = np.array(im)[..., 3]
print('G18_ledge', im.size, '前沿那一行（图内 y %d）不透明 %d / %d' % (top_h, int((al[top_h] > 128).sum()), W), '-> at [%d, %d, 0]' % (X0, TOP))
