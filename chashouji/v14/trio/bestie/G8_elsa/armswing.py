"""G8 出手瞬间帧（release）：throw 帧伸出去的右臂绕肩往上转 ROT 度（精闺1 / 自检 4.4：G8 要补一张手的运动方向 ≈ −23° 的出手帧）。
生图对这一张一直拒（content policy），而这张只需要改手臂角度：throw 帧里 x ≥ CUT 那一截手臂整段落在透明背景上，抠出来绕肩点转，
原位置清掉，转完贴回 —— 肩口那一列本来就连着，转轴放在切口上不会断。
出手方向：手臂过顶往前抡、绕肩转，离手那一刻手的速度沿圆弧切线 = 手臂角 − 90°（手臂 67.5° → −22.5°）。
蓄力手 → 出手手的位移（审查的近似口径）在这里不适用：肩比蓄力手低 128 px，手臂再长也凑不出 −23° 的位移。
输出 raw/add_release.png（整格 RGBA，addframes.json 里 paste: "cell"）。在 v14/trio 下：python3 bestie/G8_elsa/armswing.py"""
import json, math, os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); WEB = os.path.join(HERE, '../../../../web/assets/trio')
PIV, CUT, ROT = (452, 148), 457, 54            # 肩点（格内）、切口 x、往上转多少度
BAND = (100, 166)                               # 手臂所在行（切口右边这几行里只有手臂）
m = json.load(open(os.path.join(WEB, 'G8_elsa.json'))); a = Image.open(os.path.join(WEB, 'G8_elsa.webp')).convert('RGBA')
cw, ch = m['cell']; C = m['cols']; i = m['frames'].index('throw')
cell = a.crop((i % C * cw, i // C * ch, i % C * cw + cw, i // C * ch + ch))
A = np.array(cell)
arm = np.zeros_like(A); arm[BAND[0]:BAND[1], CUT:] = A[BAND[0]:BAND[1], CUT:]
rest = A.copy(); rest[BAND[0]:BAND[1], CUT:] = 0
r = Image.fromarray(arm).rotate(ROT, resample=Image.BICUBIC, center=PIV)    # PIL：正 = 逆时针 = 往上
out = Image.fromarray(rest); out.alpha_composite(r)
out.save(os.path.join(HERE, 'raw', 'add_release.png'))
# 手（原 throw 帧最右的手指尖附近 (535, 128)）转过去的位置
th = math.radians(ROT); dx, dy = 535 - PIV[0], 128 - PIV[1]
hx, hy = PIV[0] + dx * math.cos(th) + dy * math.sin(th), PIV[1] - dx * math.sin(th) + dy * math.cos(th)
print('release 手 ≈ (%.0f, %.0f)，蓄力手 (420, 20) → 位移方向 %.1f°，手臂指向 %.1f°' % (hx, hy, -math.degrees(math.atan2(hy - 20, hx - 420)), -math.degrees(math.atan2(hy - PIV[1], hx - PIV[0]))))
