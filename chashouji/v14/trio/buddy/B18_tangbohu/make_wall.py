"""B18 墙头挂件：瓦檐（raw/wall.png，part.py 缩到 330 宽）下接一截白墙面，不然一条瓦檐浮在半空。
先跑：python3 tools/part.py buddy/B18_tangbohu/raw/wall.png B18_wall w 330（在 v14/trio 下），再跑本脚本（原地改 web/assets/trio/B18_wall.webp）。"""
import os
import numpy as np
from PIL import Image
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio/B18_wall.webp')
w = Image.open(P).convert('RGBA'); a = np.array(w)
H = w.height + 60; o = np.zeros((H, w.width, 4), np.uint8); o[:w.height] = a
y0 = np.nonzero(a[:, w.width // 2, 3] > 128)[0].max() - 2          # 瓦檐下沿
for y in range(y0, H):
    f = 1.0 if y < y0 + 28 else max(0.0, 1 - (y - y0 - 28) / 32)     # 30 px 实、30 px 渐隐
    x0, x1 = 8, w.width - 8
    row = o[y]; seg = np.zeros(w.width, bool); seg[x0:x1] = True; seg &= row[:, 3] < 200
    row[seg, :3] = [236, 230, 216]; row[seg, 3] = int(255 * f)
    for x in (x0, x0 + 1, x1 - 2, x1 - 1): row[x] = [40, 40, 45, int(255 * f)]   # 墙两侧描边
Image.fromarray(o).save(P, 'WEBP', quality=90)
print(w.size, '→', (w.width, H))
