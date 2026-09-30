"""G27 杉菜：把 wind、follow 两帧里的前腿（右腿小腿 + 帆布鞋）横着挪回 idle 的位置。

为什么：动作条里模型每格把两腿的间距画得不一样 —— wind 的前脚比 idle 靠左 4.4 px、follow 靠左 3.7 px（输出像素，
frames.json 的 check "前脚" 量的）。fixed 只能按一条腿配：按后腿（跪地的膝盖 + 小腿，面积大、离锚点近）配准后残差 0.33，
但前脚在这两帧里会横跳 ~4 px（规范 check ≤ 2）。

试过 frames.py 的 graft（从 idle 整块搬前腿过来）：
  · follow 的拳头正压在前膝上，搬的框一碰到膝盖就把拳头切掉半截；框往下挪到小腿中段，小腿两条轮廓在框上沿错开一个台阶；
  · 框左沿的渐变带里留一道小腿轮廓的虚影。
所以改成**局部横向拉伸**：膝盖以上不动（y < Y0），往下到 Y1 渐渐加到整段位移 D，Y1 以下整体平移 D；
横向只动 X0 右边（X0~X1 渐入），跪地的后腿、裙摆不受影响。小腿轮廓是连续弯过去的，没有接缝。

wind 的前鞋鞋尖在原图里就被画布右沿截掉了（raw/act_a1.png 第 684~708 行白到 x 1023，审查签字 G27）：挪完之后
把 idle 那只前鞋（脚踝以下）盖到 wind 上，脚踝 SY0~SY1 这几行竖向渐变（光小腿皮肤，没有轮廓线）；横向先按鞋跟那一截配准。

**frames.py build 之后必须再跑一遍这个**（build 会重写图集）：
  python3 v14/trio/bestie/G27_shancai/fixleg.py
"""
import os
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio')
CW, CH, COLS = 332, 314, 4
NAMES = ['idle', 'wind', 'throw', 'follow', 'tackle', 'rise', 'wind2', 'idle2']
SHIFT = {'wind': 4.4, 'follow': 3.7}          # 前脚要往右挪多少（= −check 读数）
Y0, Y1 = 205, 245                               # 膝盖下沿 → 小腿中段：位移从 0 渐到 D
X0, X1 = 150, 178                               # 后腿 / 裙摆与前小腿之间的空隙：横向渐入

path = os.path.join(WEB, 'G27_shancai.webp')
atlas = np.array(Image.open(path).convert('RGBA')).astype(np.float32)
yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
sy = np.clip((yy - Y0) / (Y1 - Y0), 0, 1); sy = sy * sy * (3 - 2 * sy)
sx = np.clip((xx - X0) / (X1 - X0), 0, 1); sx = sx * sx * (3 - 2 * sx)
for fn, D in SHIFT.items():
    i = NAMES.index(fn)
    ox, oy = (i % COLS) * CW, (i // COLS) * CH
    cell = atlas[oy:oy + CH, ox:ox + CW]
    src_x = xx - D * sy * sx                   # 反向取样：目标像素从左边 D 处取
    pre = cell[..., :3] * cell[..., 3:4] / 255  # 预乘 alpha 再插值，边缘不带黑边
    out = np.dstack([map_coordinates(pre[..., c], [yy, src_x], order=1, mode='constant') for c in range(3)]
                    + [map_coordinates(cell[..., 3], [yy, src_x], order=1, mode='constant')])
    a = out[..., 3:4]
    out[..., :3] = np.where(a > 0, out[..., :3] * 255 / np.maximum(a, 1e-3), 0)
    atlas[oy:oy + CH, ox:ox + CW] = out
# wind 前鞋鞋尖：换成 idle 的鞋
SX0, SX1, SY0, SY1 = 165, 262, 266, 278           # 前脚一带（后面跪地的腿在 x < 150）；脚踝渐变带
idle, wind = atlas[0:CH, 0:CW], atlas[0:CH, CW:2 * CW]
heel = lambda c, d: c[282:300, 172 + d:212 + d, 3]
dx = min(range(-3, 4), key=lambda d: np.abs(heel(wind, 0) - heel(idle, d)).sum())   # wind 鞋跟 = idle 鞋跟往右挪 −dx
src = np.roll(idle, -dx, axis=1)
w = np.clip((yy - SY0) / (SY1 - SY0), 0, 1); w = (w * w * (3 - 2 * w))[..., None] * ((xx >= SX0) & (xx < SX1))[..., None]
pa, pb = wind[..., :3] * wind[..., 3:] / 255, src[..., :3] * src[..., 3:] / 255
al = wind[..., 3:] * (1 - w) + src[..., 3:] * w
rgb = (pa * (1 - w) + pb * w) * 255 / np.maximum(al, 1e-3)
atlas[0:CH, CW:2 * CW] = np.dstack([np.where(al > 0, rgb, 0), al])
print(f'→ wind 前鞋换成 idle 的鞋（鞋跟配准 dx {dx}）')
Image.fromarray(atlas.clip(0, 255).astype(np.uint8)).save(path, 'WEBP', quality=90, method=6)
print('→ G27_shancai.webp：', ', '.join(f'{k} 前腿右移 {v}px' for k, v in SHIFT.items()))
