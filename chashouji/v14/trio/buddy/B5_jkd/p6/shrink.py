"""上半身绕腰点 (xh, yh) 缩到 f：腰线以下原像素，腰线往上 ramp 像素内缩放倍数从 1 平滑过渡到 f（连续形变场，
不是两张图交叉淡化 —— p6ref/shrink.py 那种 24px 渐变在腰上会叠出两道轮廓）。
python3 p6/shrink.py <in> <out> <f> <xh> <yh> [ramp]"""
import sys, numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
src, dst, f, xh, yh = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
ramp = float(sys.argv[6]) if len(sys.argv) > 6 else 90
a = np.array(Image.open(src).convert('RGBA')).astype(np.float32)
H, W = a.shape[:2]
Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
t = np.clip((yh - Y) / ramp, 0, 1); t = t * t * (3 - 2 * t)
k = 1 + (f - 1) * t                                    # 输出处的缩放倍数
sx = xh + (X - xh) / k; sy = yh + (Y - yh) / k
pm = np.dstack([a[..., :3] * a[..., 3:] / 255, a[..., 3:]])
o = np.dstack([map_coordinates(pm[..., c], [sy, sx], order=1, mode='constant') for c in range(4)])
Image.fromarray(np.dstack([o[..., :3] * 255 / np.maximum(o[..., 3:], 1e-3), o[..., 3:]]).clip(0, 255).astype(np.uint8), 'RGBA').save(dst)
