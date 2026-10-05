"""候选 vs 计划：量两只拖鞋（白/黑鞋色块）的位置，和 plan 里第 i 格的目标比。
用法 score.py <档> <i> <候选…>；黑底（左上角不是品红）直接判废。"""
import sys, os, json, numpy as np
W = os.path.dirname(os.path.abspath(__file__))       # v14/walk
from PIL import Image
from scipy import ndimage
name, i = sys.argv[1], int(sys.argv[2])
G = os.path.join(W, '..', 'gait')
p = json.load(open(f'{W}/{name}/plan.json'))
fr = [f for f in p['frames'] if f['i'] == i][0]['feet']
M = np.array(Image.open(f'{G}/{name}/mask.png'))[..., 3] == 0
A = name[0] == 'a'
def slippers(a):
    r, g, b = [a[..., k].astype(int) for k in range(3)]
    if A:   # 白兔拖鞋：亮、低饱和
        s = (np.minimum(np.minimum(r, g), b) > 200) & (np.max(a, 2).astype(int) - np.min(a, 2) < 40)
    else:   # 黑猫拖鞋：暗
        s = np.max(a, 2) < 70
    s &= M
    s = ndimage.binary_opening(s, np.ones((5, 5)))
    lab, n = ndimage.label(ndimage.binary_fill_holes(s))      # 填鞋面上的眼睛胡须；不用闭运算——贴着的两只拖鞋会被粘成一只
    out = []
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if len(xs) < 800: continue
        out.append((float(xs.mean()), int(ys.max()), len(xs)))
    return out
for f in sys.argv[3:]:
    a = np.array(Image.open(f).convert('RGB').resize((1536, 1024)))
    if not (a[3, 3, 0] > 200 and a[3, 3, 1] < 60): print(f[-10:], 'BLACK'); continue
    got = slippers(a)
    tg = sorted([(v['x'], v['line'] - v['lift'], v['lift']) for v in fr.values()], key=lambda t: t[2])   # 站地脚在前
    # 一对一配：站地脚先挑最近的鞋，摆动脚从剩下的里挑
    err, left = [], list(got)
    for tx, ty, _ in tg:
        if not left: err.append(999); continue
        d = min(left, key=lambda q: abs(q[0] - tx) + abs(q[1] - ty)); left.remove(d)
        err.append(round(abs(d[0] - tx) + 0.5 * abs(d[1] - ty)))
    print(f[-10:], 'n', len(got), 'err', err, [(round(x), y) for x, y, _ in got], 'tgt', [(round(x), round(y)) for x, y, _ in tg], '(err 先站地脚、后摆动脚)')
