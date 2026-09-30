"""G7 飞刀补描边（审查第五批打回 / 规范第七轮修订第 3 条：平面细长道具要有深色描边，屏幕上最细的地方 ≥ 3 px）。

raw/knife_180.png = 原来那张 trio_g7_knife.webp（knife_src.png 经 crewart.cut 抠出、缩到 180 px 长），这里只加两件事：
  · 刀身提亮一档：低饱和（银色）的像素往白拉 LIFT；金护手、黑柄不动；
  · 深紫褐描边 EDGE（#2a1020）：alpha 往外扩 OUT px 垫在底下。cfg scale 0.65 时 OUT 3 ≈ 屏幕 2 px，
    刀尖最细 1 px 的地方加上两边描边 = 7 × 0.65 ≈ 4.5 屏幕 px。
尖头仍朝右（cfg atk.aim: true）。在 v14/trio/bestie/G7_yor 下：python3 knife.py"""
import os, numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT, LIFT, EDGE = 3, 0.3, (0x2a, 0x10, 0x20)

k = np.array(Image.open(os.path.join(HERE, 'raw/knife_180.png')).convert('RGBA')).astype(float)
rgb, al = k[..., :3], k[..., 3]
mx, mn = rgb.max(-1), rgb.min(-1)
silver = (al > 0) & ((mx - mn) / np.maximum(mx, 1) < 0.12) & (mx > 110)   # 黑柄（暗）、金护手（饱和）不算
rgb[silver] += (255 - rgb[silver]) * LIFT
k = np.pad(k, ((OUT, OUT), (OUT, OUT), (0, 0)))
a = k[..., 3] / 255
ring = nd.binary_dilation(a > 0.25, structure=nd.generate_binary_structure(2, 1), iterations=OUT)   # 4 邻域一圈圈扩（圆角），描边不透明
out = np.zeros_like(k)
out[..., :3] = k[..., :3] * a[..., None] + np.array(EDGE) * (1 - a[..., None])
out[..., 3] = np.maximum(ring, a) * 255
Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(
    os.path.join(HERE, '../../../../web/assets/world/trio_g7_knife.webp'), 'WEBP', quality=92, method=6)
print('knife', out.shape[1], 'x', out.shape[0], 'silver px', int(silver.sum()))
