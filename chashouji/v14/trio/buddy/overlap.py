"""同组两个人的剪影会不会叠在一起（后排地面 × 地板）：两人在场的每一帧两两贴到屏幕上，剪影外扩 4px 后数相交像素。
用法：python3 overlap.py <名A> <ax,ay,as> <anchorA x,y> <帧A,...> <名B> <bx,by,bs> <anchorB x,y> <帧B,...>"""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage
W = '../../../web/assets/trio/'
def masks(n, at, anc, frames):
    j = json.load(open(W + n + '.json')); cw, ch = j['cell']; names = j['frames']
    im = Image.open(W + n + '.webp').convert('RGBA'); out = {}
    for f in frames:
        i = names.index(f); c = im.crop((i % 4 * cw, i // 4 * ch, i % 4 * cw + cw, i // 4 * ch + ch))
        s = at[2]; c = c.resize((max(1, round(cw * s)), max(1, round(ch * s))))
        m = np.zeros((1500, 1100), bool); a = np.array(c)[..., 3] > 128
        x0 = round(at[0] - anc[0] * s) + 50; y0 = round(at[1] - anc[1] * s) + 50
        ys, xs = np.nonzero(a); ys = ys + y0; xs = xs + x0; k = (ys >= 0) & (ys < 1500) & (xs >= 0) & (xs < 1100)
        m[ys[k], xs[k]] = True; out[f] = ndimage.binary_dilation(m, iterations=4)
    return out
p = lambda s: [float(v) for v in s.split(',')]
A = masks(sys.argv[1], p(sys.argv[2]), p(sys.argv[3]), sys.argv[4].split(','))
B = masks(sys.argv[5], p(sys.argv[6]), p(sys.argv[7]), sys.argv[8].split(','))
worst = max(((fa, fb, int((ma & mb).sum())) for fa, ma in A.items() for fb, mb in B.items()), key=lambda r: r[2])
print('最大相交', worst)
