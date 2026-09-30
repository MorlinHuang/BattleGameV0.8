"""规范 8.4「flex 框三边透明」逐帧检查：python3 flexcheck.py <图集名> <帧名> x0,y0,x1,y1 [...]（可连写多组 帧名 框）"""
import sys, json
import numpy as np
from PIL import Image
n = sys.argv[1]
j = json.load(open(f'web/assets/trio/{n}.json')); cw, ch = j['cell']; names = j['frames']
a = np.array(Image.open(f'web/assets/trio/{n}.webp').convert('RGBA'))[..., 3]
args = sys.argv[2:]
for f, box in zip(args[::2], args[1::2]):
    x0, y0, x1, y1 = map(int, box.split(',')); i = names.index(f)
    C = a[i // 4 * ch:(i // 4 + 1) * ch, i % 4 * cw:(i % 4 + 1) * cw]
    print(n, f, box, {'t': int((C[y0, x0:x1 + 1] > 128).sum()), 'b': int((C[y1, x0:x1 + 1] > 128).sum()),
                      'l': int((C[y0:y1 + 1, x0] > 128).sum()), 'r': int((C[y0:y1 + 1, x1] > 128).sum())})
