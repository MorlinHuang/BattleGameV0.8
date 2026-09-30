"""G14 脚下的水晶城堡石台（审查第九批打回：两只金靴底悬在鱼缸玻璃中段；规范第十一轮修订第 1 条：站姿脚下必须有东西托着）。parts fixed: true, z −1。

为什么不站到鱼缸盖上（审查方案 A）：鱼缸是长卷背景的一部分，镜头随拖拽卷动（main.js FX.camX），三间房里也只有客厅有鱼缸；
人按屏幕 at 钉在原地，一拖动鱼缸就从她脚下滑走。场景层挂件跟人走，放到哪一间都托得住。

程序画，写法同 G18_mu/ledge.py：按 K 倍画、描深边，缩到格内像素（和帧同一个单位）。
一截浅灰紫石台（3/4 俯看有顶面）：
  · 顶面从 TOP 到 EDGE —— 前脚（右）靴底格内 y 425、后脚（左）429：两只脚都踩在顶面这条带里，前沿 EDGE = 429 = 后脚靴底最低一行；
  · 前沿一道淡青水晶镶边（名单"剑之公主"的水晶城堡：浅紫石 + 青色水晶），立面石块错缝 FACE px，最后 FADE px 渐隐；
  · 右端 X1 收一个墙角，墙角下挂一簇青水晶；左端出画（格内 X0，屏幕 x < 0）。
cfg：pivot [0, 0]，at [X0, TOP, 0]。改 at 要重跑。在 v14/trio/bestie/G14_shera 下：python3 ledge.py"""
import os
import numpy as np
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio')
K = 3
INK = (40, 36, 44, 255)
X0, X1, TOP, EDGE, FACE, FADE = -60, 290, 407, 429, 58, 30   # X0：at [170, 640, 0.77] 时左端屏幕 x −47（出画）
TOPC, TOPH, SEAM = (196, 190, 206, 255), (224, 220, 232, 255), (150, 144, 164, 255)
FACEC = [(150, 142, 170), (140, 132, 160), (158, 150, 178), (132, 126, 152)]
MORTAR = (96, 90, 114, 255)
CRY, CRYH, CRYD = (120, 220, 236, 255), (214, 250, 255, 255), (52, 150, 180, 255)

W, H = X1 - X0, EDGE - TOP + FACE
s = lambda v: int(round(v * K))
im = Image.new('RGBA', (s(W), s(H + 26)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
top_h = EDGE - TOP
# 顶面：浅灰紫石板，接缝近大远小
d.rectangle([0, 0, s(W), s(top_h)], fill=TOPC)
d.rectangle([0, s(top_h - 4), s(W), s(top_h)], fill=TOPH)                      # 前沿倒角高光：人踩的那条线读得清
d.line([(0, s(10)), (s(W), s(10))], fill=SEAM, width=s(0.8))
for x in range(0, W, 40):
    d.line([(s(x), s(10)), (s(x), s(top_h - 4))], fill=SEAM, width=s(0.8))
    d.line([(s(x + 20), 0), (s(x + 20), s(10))], fill=SEAM, width=s(0.6))
# 立面：石块错缝
rng = np.random.default_rng(14)
BW, BH = 34, 13
for r, y in enumerate(range(top_h, H, BH)):
    off = (BW // 2) if r % 2 else 0
    for x in range(-BW, W + BW, BW):
        c = FACEC[rng.integers(len(FACEC))] + (255,)
        d.rectangle([s(x + off), s(y), s(x + off + BW), s(y + BH)], fill=c, outline=MORTAR, width=s(1))
# 前沿水晶镶边：一条青带 + 等距菱形水晶钉
d.rectangle([0, s(top_h), s(W), s(top_h + 5)], fill=CRYD)
d.rectangle([0, s(top_h + 0.8), s(W), s(top_h + 2.4)], fill=CRY)
for x in range(12, W - 14, 30):
    cx, cy = x, top_h + 12
    d.polygon([(s(cx), s(cy - 5)), (s(cx + 4), s(cy)), (s(cx), s(cy + 5)), (s(cx - 4), s(cy))], fill=CRY, outline=INK)
    d.line([(s(cx - 1), s(cy - 3)), (s(cx - 2.6), s(cy))], fill=CRYH, width=s(0.9))
# 右端墙角：暗面 + 竖描边
d.rectangle([s(W - 9), s(top_h), s(W), s(H)], fill=(112, 106, 134, 255))
d.line([(s(W - 9), s(top_h)), (s(W - 9), s(H))], fill=INK, width=s(1.2))
d.line([(s(W) - 2, 0), (s(W) - 2, s(H))], fill=INK, width=s(2))
# 描边：后沿、前沿（人站的那条线描粗）
d.line([(0, 1), (s(W), 1)], fill=INK, width=s(1.5))
d.line([(0, s(top_h)), (s(W), s(top_h))], fill=INK, width=s(2))
a = np.array(im); h0 = s(H)
for y in range(s(H - FADE), a.shape[0]):                                        # 下半截渐隐（水晶簇之外）
    a[y, :, 3] = (a[y, :, 3] * max(0.0, 1 - (y - s(H - FADE)) / (h0 - s(H - FADE)))).astype(np.uint8)
im = Image.fromarray(a); d = ImageDraw.Draw(im)
# 墙角下挂一簇青水晶（画在渐隐之后，不跟着淡）
for bx, ln, wd in ((W - 30, 34, 9), (W - 18, 46, 11), (W - 6, 28, 8)):
    tip = (s(bx), s(top_h + 6 + ln))
    d.polygon([(s(bx - wd / 2), s(top_h + 6)), (s(bx + wd / 2), s(top_h + 6)), tip], fill=CRY, outline=INK, width=s(1.1))
    d.line([(s(bx - wd / 4), s(top_h + 9)), (s(bx - 0.5), s(top_h + 6 + ln * 0.8))], fill=CRYH, width=s(1.2))
    d.line([(s(bx + wd / 4), s(top_h + 8)), (s(bx + 1), s(top_h + 6 + ln * 0.75))], fill=CRYD, width=s(1))
im = im.resize((W, H + 26), Image.LANCZOS)
im = im.crop(im.getbbox()[:2] and (0, 0, W, im.getbbox()[3]))
im.save(os.path.join(OUT, 'G14_ledge.webp'), 'WEBP', quality=92)
al = np.array(im)[..., 3]
print('G14_ledge', im.size, '前沿那一行（图内 y %d）不透明 %d / %d' % (top_h, int((al[top_h] > 128).sum()), W), '-> at [%d, %d, 0]' % (X0, TOP))
