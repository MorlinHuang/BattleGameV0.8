"""P6 补帧底图：从 raw/act_a1.png 切出 idle / hitA / hitB 原像素格，贴到 1024x1024 品红画布（人不缩放）。
记录每张底图里格的原点（raw 坐标 → 画布坐标的平移），写 p6/place.json。"""
import sys, json, numpy as np
sys.path.insert(0, '/workspace/art/chashouji/v14'); sys.path.insert(0, '/workspace/art/chashouji/v14/trio/tools')
from crewart import cut
from scipy import ndimage
from PIL import Image
rgb, al = cut('raw/act_a1.png', 'magenta', (40, 150))
lab, k = ndimage.label(ndimage.binary_dilation(al > 0.1, iterations=3))
area = ndimage.sum(al > 0.1, lab, range(1, k + 1))
big = list(np.argsort(area)[::-1][:4] + 1)
objs = {b: ndimage.find_objects((lab == b).astype(int))[0] for b in big}
# 阅读顺序
big.sort(key=lambda b: (objs[b][0].start > 700, objs[b][1].start))
names = ['idle', 'wind', 'hitA', 'hitB']
place = {}
for n, b in zip(names, big):
    sy, sx = objs[b]
    print(n, 'raw bbox', sx.start, sy.start, sx.stop, sy.stop)
    if n == 'wind': continue
    w, h = sx.stop - sx.start, sy.stop - sy.start
    ox = (1024 - w) // 2 + (60 if n != 'idle' else 0); oy = 1024 - 24 - h   # 人贴底，上面留出举棍的空
    ox = min(ox, 1024 - w - 8)
    m = (lab[sy, sx] == b) * al[sy, sx]
    c = rgb[sy, sx]
    can = np.zeros((1024, 1024, 3), np.float32); can[..., 0] = 255; can[..., 2] = 255
    reg = can[oy:oy + h, ox:ox + w]
    can[oy:oy + h, ox:ox + w] = c * m[..., None] + reg * (1 - m[..., None])
    Image.fromarray(can.clip(0, 255).astype(np.uint8)).save(f'raw/p6_{ {"idle":"idle2","hitA":"hitC","hitB":"hitD"}[n] }_base.png')
    a = np.zeros((1024, 1024), np.float32); a[oy:oy + h, ox:ox + w] = m
    np.save(f'p6/{n}_alpha.npy', a)
    place[n] = [int(ox - sx.start), int(oy - sy.start)]
json.dump(place, open('p6/place.json', 'w'))
print(place)
