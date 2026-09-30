"""G22 探险家：翘起来的两条小腿 + 靴子拆成挂件层（cfg.parts，绕膝上那一截来回晃 = 趴着懒洋洋地晃脚）。

为什么不用 flex / lift：她朝右趴，脚在左边、从膝盖往上翘 —— 挂住的是下端（膝），自由端在上面。flex 只有钉顶 't' / 钉左 'l'，
钉哪边都会把膝盖处撕开；frames.py 的 lift 是给往下挂的东西（流苏）用的，pivot 固定取顶上。所以这里自己拆：
取 idle 那一帧的小腿（框 LEG，y < CUT 的那一截），四个在场帧（idle / wind / throw / follow）里把这一块清掉，由挂件层统一画。
配准按屁股 + 大腿（fixed），四帧的小腿本来就在同一处，只是模型每格画得略有出入（均差 5~10 / 255），统一用 idle 的反而更一致。
切口在小腿中段（y = CUT）：挂件绕切口正中转，sway 给小（0.05 rad），切口两侧最多错开 ~1 px，被描边盖住。

**frames.py build 之后必须再跑一遍这个**（build 会重写图集）：
  python3 v14/trio/bestie/G22_explorer/legs.py
→ 改写 web/assets/trio/G22_explorer.webp（清掉四帧的小腿）、出 web/assets/trio/G22_legs.webp，打印 cfg.parts。"""
import os
import numpy as np
from PIL import Image

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio')
CW, CH, COLS = 467, 185, 4
FRAMES = ['idle', 'wind', 'throw', 'follow']          # 图集前四格（在场帧）
LEG = (0, 0, 150, 100)                                 # 小腿 + 靴子（输出像素）；下沿 = 切口
CUT = LEG[3]

atlas = np.array(Image.open(os.path.join(WEB, 'G22_explorer.webp')).convert('RGBA'))
x0, y0, x1, y1 = LEG
part = atlas[y0:y1, x0:x1].copy()                     # idle 在第 0 格
ys, xs = np.nonzero(part[..., 3] > 8)
if not len(xs): raise SystemExit('idle 帧的 LEG 框里没有小腿 —— 图集是不是没重新 build 过、或者已经清过了')
bx0, by0, bx1 = xs.min(), ys.min(), xs.max() + 1
cut_x = np.nonzero(part[CUT - 1, :, 3] > 128)[0]
pivot = [round(float((cut_x.min() + cut_x.max()) / 2 - bx0), 1), float(CUT - by0)]
Image.fromarray(part[by0:, bx0:bx1]).save(os.path.join(WEB, 'G22_legs.webp'), 'WEBP', quality=92, method=6)
for i, fn in enumerate(FRAMES):
    cx, cy = (i % COLS) * CW, (i // COLS) * CH
    atlas[cy + y0:cy + y1, cx + x0:cx + x1, 3] = 0
Image.fromarray(atlas).save(os.path.join(WEB, 'G22_explorer.webp'), 'WEBP', quality=90, method=6)
at = [round(float(pivot[0] + bx0 + x0), 1), float(CUT)]
print(f"→ G22_legs.webp {bx1 - bx0}x{CUT - by0}；cfg.parts：{{ src: 'assets/trio/G22_legs.webp', pivot: {pivot}, z: 1, "
      f"at: {{ {', '.join(f'{fn}: [{at[0]}, {at[1]}, 0]' for fn in FRAMES)} }}, sway: [0.05, 0.6, 0] }}")
