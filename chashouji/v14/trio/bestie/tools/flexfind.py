"""在图集的某一帧里找 flex 框（规范 8.4：钉住那一边以外的三条边全透明）。
用法：python3 flexfind.py <图集名> <帧名> <钉住边 t/b/l/r> <外框 x0,y0,x1,y1>（框只在外框里找）[步长=2]
打印框里不透明像素最多的几个（越多 = 摆起来的那一块越大）。在 chashouji 下跑"""
import json, sys
import numpy as np
from PIL import Image
n, fn, pin, lim = sys.argv[1:5]; st = int(sys.argv[5]) if len(sys.argv) > 5 else 2
j = json.load(open(f'web/assets/trio/{n}.json')); cw, ch = j['cell']; C = j['cols']; i = j['frames'].index(fn)
A = np.array(Image.open(f'web/assets/trio/{n}.webp').convert('RGBA'))[..., 3][i // C * ch:(i // C + 1) * ch, i % C * cw:(i % C + 1) * cw] > 128
X0, Y0, X1, Y1 = map(int, lim.split(','))
I = np.pad(A.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
area = lambda x0, y0, x1, y1: I[y1, x1] - I[y0, x1] - I[y1, x0] + I[y0, x0]
row = lambda y, x0, x1: A[y, x0:x1 + 1].any()
col = lambda x, y0, y1: A[y0:y1 + 1, x].any()
out = []
for x0 in range(X0, X1, st):
    for x1 in range(x0 + 10, X1 + 1, st):
        for y0 in range(Y0, Y1, st):
            for y1 in range(y0 + 10, Y1 + 1, st):
                e = {'t': row(y0, x0, x1), 'b': row(y1, x0, x1), 'l': col(x0, y0, y1), 'r': col(x1, y0, y1)}
                if any(v for k, v in e.items() if k != pin) or not e[pin]: continue
                out.append((int(area(x0, y0, x1, y1)), x0, y0, x1, y1))
out.sort(reverse=True)
for o in out[:4]: print(n, fn, pin, '框 [%d, %d, %d, %d]' % o[1:], '不透明 %d px' % o[0])
