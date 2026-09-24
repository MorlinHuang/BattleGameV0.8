"""补帧用：把一张新生成的帧按"缩放+平移"对齐到上一帧，报告对齐后的异位像素比例。
生图每次会把整组人推远拉近、左右挪，不对齐的话差异里大半是镜头，不是姿态。"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage, optimize


def alpha(path, w=384):
    x = np.array(Image.open(path).convert('RGB').resize((w, w * 2 // 3))).astype(np.int16)
    return ((np.minimum(x[..., 0], x[..., 2]) - x[..., 1]) < 100).astype(np.float32)


def warp(a, s, dx, dy):
    h, w = a.shape
    c = np.array([h, w]) / 2
    return ndimage.affine_transform(a, [1 / s, 1 / s], offset=c - (c + [dy, dx]) / s, order=1)


def register(ref, mov):
    f = lambda v: ((warp(mov, *v) - ref) ** 2).sum()
    best = min((optimize.minimize(f, [s, 0, 0], method='Powell', bounds=[(0.7, 1.4), (-120, 120), (-120, 120)]) for s in (0.9, 1.0, 1.1)), key=lambda r: r.fun)
    return best.x


def diff(a, b):
    A, B = a > .5, b > .5
    return (A ^ B).sum() / max(A.sum(), B.sum())


if __name__ == '__main__':
    ref = alpha(sys.argv[1])
    for p in sys.argv[2:]:
        mov = alpha(p)
        s, dx, dy = register(ref, mov)
        print(f'{p[-24:]:>24}  原始 {diff(ref, mov):5.1%}  对齐后 {diff(ref, warp(mov, s, dx, dy)):5.1%}  缩放 {s:.3f} 平移 ({dx*4:+.0f},{dy*4:+.0f})px')
