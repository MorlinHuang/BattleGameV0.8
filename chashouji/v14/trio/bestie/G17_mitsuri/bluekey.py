"""蓝幕 → 透明 png（frames.py 只认品红 / 绿幕；G17 一身粉 + 嫩绿，只能用蓝幕）。
键值 k = b − max(r, g)，alpha = 1 − (k − 40) / (150 − 40)（和 crewart.cut 同一套数），半透明带去溢色 b ≤ max(r, g)。
原图自带透明的先铺回 #0000FF 再抠（发缝里会夹着幕布色）。用法：python3 bluekey.py <入> <出>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
im = Image.open(sys.argv[1]).convert('RGBA')
bg = Image.new('RGBA', im.size, (0, 0, 255, 255)); bg.alpha_composite(im)
a = np.array(bg.convert('RGB')).astype(np.float32)
k = a[..., 2] - np.maximum(a[..., 0], a[..., 1])
al = np.clip(1 - (k - 40) / 110, 0, 1)
lab, n = ndimage.label(al > 0.05)
if n:
    sz = ndimage.sum(np.ones_like(al), lab, range(1, n + 1))
    al[np.isin(lab, np.nonzero(sz < 60)[0] + 1)] = 0
edge = al < 0.99
a[..., 2] = np.where(edge, np.minimum(a[..., 2], np.maximum(a[..., 0], a[..., 1])), a[..., 2])
Image.fromarray(np.dstack([a, al * 255]).clip(0, 255).astype(np.uint8), 'RGBA').save(sys.argv[2])
print(sys.argv[2], '不透明像素', int((al > 0.5).sum()))
