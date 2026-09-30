"""G13 横绳右端的墙钉 + 绳结（审查第九批打回：绳右端停在墙画中间、什么都没拴）。parts fixed: true, z −1（引擎先画绳 drawSling、再画 z −1 场景层，钉和绳结压在绳头上）。

程序画，写法同 G18_mu/ledge.py：按 K 倍画、描深边，缩到格内像素（fixed 挂件和帧同一个单位，画的时候 × at.s）。
一块铁底板钉在墙上（钉头）、底板下挂一个铁环，绳头穿过铁环打一个结、结下垂一截绳尾。
pivot = 绳结中心 = enter.ends 右端（绳子画到这一点，结盖住绳头）。
摆放：绳右端屏幕 END（画框右沿 x ≈ 487 和挂钟左沿 x ≈ 543 之间的空墙，挂钟下沿 y ≈ 503），换成格内坐标 = anchor + (END − at.xy) / at.s。
改 at 或 ends 要重跑。在 v14/trio/bestie/G13_xiaolongnv 下：python3 peg.py"""
import os
import numpy as np
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio')
K = 4
S = 0.66                                  # G13 at.s
AT, ANCHOR, END = (175, 500), (206.5, 166.1), (515, 468)
INK = (40, 36, 38, 255)
IRON, IRONH, IRONS = (74, 76, 84, 255), (132, 136, 146, 255), (48, 50, 56, 255)
ROPE, ROPEE, ROPED = (185, 138, 78, 255), (90, 58, 26, 255), (150, 106, 56, 255)   # 同 enter.fill / edge

W, H = 24, 32                             # 屏幕像素（约 24 × 30，审查建议）
PX, PY = 12, 23                           # 绳结中心（屏幕像素，图内）
s = lambda v: int(round(v * K))
im = Image.new('RGBA', (s(W), s(H)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
# 铁底板 + 钉头
d.rounded_rectangle([s(7), s(0.8), s(17), s(11)], radius=s(2), fill=IRON, outline=INK, width=s(1.1))
d.line([(s(8.6), s(2.4)), (s(15.4), s(2.4))], fill=IRONH, width=s(0.8))
d.ellipse([s(10), s(3.6), s(14), s(7.6)], fill=IRONH, outline=INK, width=s(0.8))
# 铁环（从底板下沿挂下来）：外圈描边、里圈铁色、上半一道高光
d.ellipse([s(6.2), s(9.2), s(17.8), s(20.8) + s(2)], outline=INK, width=s(3.2))
d.ellipse([s(6.9), s(9.9), s(17.1), s(20.1) + s(2)], outline=IRONS, width=s(1.8))
d.arc([s(6.9), s(9.9), s(17.1), s(20.1) + s(2)], 200, 320, fill=IRONH, width=s(0.9))
# 绳尾：结下垂一截，往右飘一点
d.line([(s(PX), s(PY)), (s(PX + 2.5), s(PY + 5)), (s(PX + 3.5), s(H - 1.5))], fill=ROPEE, width=s(4.4), joint='curve')
d.line([(s(PX), s(PY)), (s(PX + 2.5), s(PY + 5)), (s(PX + 3.5), s(H - 1.5))], fill=ROPE, width=s(2.8), joint='curve')
# 绳结：一团缠在环底，两道缠绕纹
d.ellipse([s(PX - 5), s(PY - 4), s(PX + 5), s(PY + 4)], fill=ROPE, outline=ROPEE, width=s(1.4))
for dx in (-1.8, 1.4):
    d.arc([s(PX + dx - 3), s(PY - 4.5), s(PX + dx + 3), s(PY + 4.5)], 290, 70, fill=ROPED, width=s(1.1))
d.arc([s(PX - 4), s(PY - 3.4), s(PX + 2), s(PY + 1)], 200, 290, fill=(222, 184, 124, 255), width=s(0.9))   # 高光
k = 1 / S                                 # 屏幕 px → 格内 px
im = im.resize((round(W * k), round(H * k)), Image.LANCZOS)
im.save(os.path.join(OUT, 'G13_peg.webp'), 'WEBP', quality=92)
pv = (PX * k, PY * k)
at = (ANCHOR[0] + (END[0] - AT[0]) / S, ANCHOR[1] + (END[1] - AT[1]) / S)
print('G13_peg', im.size, 'pivot [%.1f, %.1f]' % pv, 'at [%.1f, %.1f, 0]' % at, '（屏幕绳端 %s）' % (END,))
