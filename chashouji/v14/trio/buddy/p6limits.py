"""精美1：图集里每一帧摆到屏幕上的包围盒（屏幕坐标 = at + (格内点 − anchor) × s）。
用法：python3 p6limits.py <图集名> <at_x>,<at_y>,<s> [帧,帧,...]   （不给帧名 = 全部帧）
打印每帧 x0~x1、y0~y1，超出 0~960 横向或低过 1334 的标 ✗。"""
import json, sys
import numpy as np
from PIL import Image

W = '/workspace/art/chashouji/web/assets/trio/'
name = sys.argv[1]; ax, ay, s = [float(v) for v in sys.argv[2].split(',')]
want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
j = json.load(open(W + name + '.json')); cw, ch = j['cell']; cols = j.get('cols', 4); anx, any_ = j['anchor']
a = np.asarray(Image.open(W + name + '.webp').convert('RGBA'))[..., 3] > 40
for i, f in enumerate(j['frames']):
    if want and f not in want: continue
    c = a[i // cols * ch:(i // cols + 1) * ch, i % cols * cw:(i % cols + 1) * cw]
    ys, xs = np.nonzero(c)
    if not len(xs): print(f, 'empty'); continue
    X0, X1 = ax + (xs.min() - anx) * s, ax + (xs.max() - anx) * s
    Y0, Y1 = ay + (ys.min() - any_) * s, ay + (ys.max() - any_) * s
    bad = ' ✗' if X0 < 0 or X1 > 960 or Y1 > 1334 else ''
    print(f'{f:9s} x {X0:7.1f} ~ {X1:7.1f}   y {Y0:7.1f} ~ {Y1:7.1f}{bad}')
