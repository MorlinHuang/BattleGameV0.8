"""每段 上一档 → t1…tN → 本档 输方头中心的 y（原图像素，按本档缩放折算到同一尺度），看哪两格之间落差最大。
用法：python3 gaps.py [档 ...]"""
import os, sys
sys.argv, args = sys.argv[:1], sys.argv[1:]
import check as C
FROM = {'aK': 'n0', 'aF': 'aK', 'aL': 'aF', 'bK': 'n0', 'bF': 'bK', 'bL': 'bF'}
for name in args or list(FROM):
    d = os.path.join(C.HERE, name)
    ts = sorted([f for f in os.listdir(d) if f[0] == 't' and f[1:-4].isdigit()], key=lambda f: int(f[1:-4]))
    seq = [os.path.join(d, f) for f in ts] + [os.path.join(d, 'base.png')]
    ys = [C.head(p, name)[2] for p in seq]
    print(name, ' '.join(f'{os.path.basename(p)[:-4]}:{y:.0f}' for p, y in zip(seq, ys)),
          ' 落差', [round(b - a) for a, b in zip(ys, ys[1:])], flush=True)
