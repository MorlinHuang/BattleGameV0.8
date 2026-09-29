"""法术潮贴图的共用函数（2026-09-29 从 v14/sea2/make.py 抽出来）：生图 → 抠像（半透明按 alpha 反解幕布色）→ 补洞 → 横向无缝长条。
白娘子的海（sea2/make.py）和真相女神 / 灭迹恶魔 / 嫦娥 / 后羿的潮（tides/make.py）共用。每个函数的来由见各自的注释。
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crewart import cut, edge_extend

OVER, FEATHER = 320, 10          # 无缝拼接：首尾叠多少列、缝两边羽化几像素


def load(path, screen='magenta', key=(40, 150)):
    """→ (前景 rgb, alpha)。半透明像素（浪尖飞沫、白沫边）按 alpha 把幕布色反解掉：c = a·前景 + (1 − a)·幕布。
    crewart.cut 的去溢色是减掉品红度，半透明的白沫减完是灰到黑（浪尖一圈黑点）；反解出来是白的。
    a < 0.3 的反解不稳，连同全透明的一起用 edge_extend 从周围取色（fill_holes 补满的水沫缝要用这个颜色）。"""
    im = Image.open(path)
    if im.mode == 'RGBA' and np.array(im)[..., 3].min() == 0:      # 生图已经给了透明底
        a = np.array(im).astype(np.float32)
        rgb, al = a[..., :3], a[..., 3] / 255
    else:
        _, al = cut(path, screen, key)
        c = np.array(im.convert('RGB')).astype(np.float32)
        M = np.median(c[al == 0], axis=0)
        rgb = np.clip((c - (1 - al[..., None]) * M) / np.maximum(al[..., None], 0.3), 0, 255)
        # 反解后还剩一点幕布色（幕布色估得不准、生图笔触本身带一点）：品红幕 → R、B 同时高出 G 的部分减掉（海水 R 远低于 G，
        # 只动发紫的白沫）；绿幕 → G 高出 max(R,B) 的部分减掉（烟 / 云 / 火身上本来没有那么绿的）
        if screen == 'magenta':
            sp = np.clip(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1], 0, None)
            rgb[..., 0] -= sp; rgb[..., 2] -= sp
        else:
            rgb[..., 1] = np.minimum(rgb[..., 1], np.maximum(rgb[..., 0], rgb[..., 2]))
    rgb = edge_extend(rgb, np.where(al >= 0.3, al, 0), it=40)
    return rgb, al


def solid(al):
    """水身不能有透的洞（白沫、浪尖反光处偶尔被键吃掉一点）：被水整圈包住的洞补满。
    第一版按列补（每列最上面一个不透明像素往下全补）：浪尖上方飞着的水沫也算"最上面"，水沫和浪尖之间的幕布被补成水，
    那里的颜色是去过溢色的品红 ≈ 黑，浪尖上全是黑点。"""
    solid = ndimage.binary_fill_holes(al > 0.5)
    return np.where(solid, np.maximum(al, 1.0 * solid), al)


def seam(rgb, al):
    """横向首尾相接：返回宽 W − OVER 的无缝长条"""
    H, W = al.shape
    A = np.dstack([rgb, al[..., None] * 255])
    L, R = A[:, :OVER], A[:, W - OVER:]
    err = ((L - R) ** 2).sum(-1)
    # 动态规划：每行一个列号，相邻两行最多差 1 列，总误差最小
    cost = err.copy(); back = np.zeros_like(err, dtype=np.int32)
    for y in range(1, H):
        prev = cost[y - 1]
        cand = np.stack([np.r_[np.inf, prev[:-1]], prev, np.r_[prev[1:], np.inf]])
        k = cand.argmin(0)
        cost[y] += cand[k, np.arange(OVER)]
        back[y] = np.arange(OVER) + k - 1
    path = np.zeros(H, np.int32); path[-1] = cost[-1].argmin()
    for y in range(H - 1, 0, -1): path[y - 1] = back[y, path[y]]
    xs = np.arange(OVER)[None, :]
    w = np.clip((xs - path[:, None]) / FEATHER + 0.5, 0, 1)[..., None]     # 0：取右端，1：取左端
    head = R * (1 - w) + L * w
    out = np.concatenate([head, A[:, OVER:W - OVER]], 1)
    print(f'  缝：列 {path.min()}~{path.max()}，缝上平均误差 {err[np.arange(H), path].mean():.0f}')
    return out
