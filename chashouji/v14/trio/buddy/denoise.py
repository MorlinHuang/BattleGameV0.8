"""透明底定妆去噪（审查 2）：生图直接给的 RGBA 透明底，四周散着 alpha 很低的噪点，包围盒会撑到画布边、缩放比例算错。
alpha < 0.05 的像素清零（RGB 一并清零），再按包围盒外扩 M 像素裁切，原地覆盖。
用法：python3 v14/trio/buddy/denoise.py B8 B14 …（只处理 RGBA；幕布原图没有这个问题，跳过）"""
import os, sys
import numpy as np
from PIL import Image
REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ref')
M = 16

for n in sys.argv[1:]:
    p = os.path.join(REF, f'{n}.png')
    im = Image.open(p)
    if im.mode != 'RGBA':
        print(n, 'skip', im.mode)
        continue
    px = np.array(im)
    px[px[..., 3] < round(0.05 * 255)] = 0
    ys, xs = np.nonzero(px[..., 3])
    h, w = px.shape[:2]
    box = (max(0, xs.min() - M), max(0, ys.min() - M), min(w, xs.max() + 1 + M), min(h, ys.max() + 1 + M))
    Image.fromarray(px).crop(box).save(p)
    print(n, 'bbox', (xs.min(), ys.min(), xs.max(), ys.max()), '->', Image.open(p).size)
