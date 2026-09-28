"""白娘子的海面（2026-09-28 第三版）：三张手绘海浪生图 → 抠像 → 做成横向无缝循环的长条 → 远 / 中 / 近三层贴图。
用户："水波纹体积感还是做得太假，水波纹不适合做体积感，还是回到 2D 的感觉，但不要太 Q，需要写实些表现"。
第一版 canvas 现画的正弦色带（太 Q）、第二版 Blender 3 渲 2 的 Gerstner 海面（硬切明暗 + 描边，读成塑料）都被否。
这一版是动画电影背景那种手绘写实海浪（浪尖透光的青绿、笔刷画的白沫、深处藏青），动起来靠 sea.js：各层反向平移 + 按列起伏。

原图（生图，品红幕布；far_src 生图时直接出了透明底）：far_src.png / mid_src.png / near_src.png，1659×948 左右。
无缝循环：长条右端 OVER 列和左端 OVER 列叠在一起，沿一条竖向"差最小"的缝（动态规划找）拼接 —— 缝左取右端、缝右取左端，
再沿缝羽化 FEATHER 像素。直接首尾交叉淡化的话浪的剪影会在那一段重影（两道浪线叠在一起）。
跑法：python3 make.py → web/assets/world/sea2_<far|mid|near>.webp，并打印 sea.js SEA2 要填的尺寸。
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from crewart import cut, edge_extend

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'web', 'assets', 'world')
OVER, FEATHER = 320, 10
# 层：原图、输出缩放（= 屏幕上的大小，引擎不再缩放）、往哪个颜色压多少（远处空气透视：发白发灰；近处压暗一点）
LAYERS = [
    ('far',  'far_src.png',  0.40, ((150, 196, 226), 0.30)),
    ('mid',  'mid_src.png',  0.52, ((60, 120, 180), 0.08)),
    ('near', 'near_src.png', 0.66, ((10, 30, 70), 0.12)),
]
KEY = (40, 150)          # 品红度 min(R,B) − G：水里最"品红"的是浪尖透光带边上的一点紫，实测 < 40


def load(name):
    """→ (前景 rgb, alpha)。半透明像素（浪尖飞沫、白沫边）按 alpha 把幕布色反解掉：c = a·前景 + (1 − a)·幕布。
    crewart.cut 的去溢色是减掉品红度，半透明的白沫减完是灰到黑（浪尖一圈黑点）；反解出来是白的。
    a < 0.3 的反解不稳，连同全透明的一起用 edge_extend 从周围取色（fill_holes 补满的水沫缝要用这个颜色）。"""
    im = Image.open(os.path.join(HERE, name))
    if im.mode == 'RGBA' and np.array(im)[..., 3].min() == 0:      # 生图已经给了透明底
        a = np.array(im).astype(np.float32)
        rgb, al = a[..., :3], a[..., 3] / 255
    else:
        _, al = cut(os.path.join(HERE, name), 'magenta', KEY)
        c = np.array(im.convert('RGB')).astype(np.float32)
        M = np.median(c[al == 0], axis=0)
        rgb = np.clip((c - (1 - al[..., None]) * M) / np.maximum(al[..., None], 0.3), 0, 255)
        # 反解后白沫里还剩一点淡紫（幕布色估得不准、生图笔触本身带粉）：R、B 同时高出 G 的部分减掉。
        # 海水 R 远低于 G（min(R,B) < G），这一步只动发紫的白沫
        sp = np.clip(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1], 0, None)
        rgb[..., 0] -= sp; rgb[..., 2] -= sp
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


for name, src, K, (tint, tk) in LAYERS:
    print(name)
    rgb, al = load(src)
    al = solid(al)
    rgb = rgb * (1 - tk) + np.array(tint, np.float32) * tk
    A = seam(rgb, al)
    ys = np.nonzero(A[..., 3].max(1) > 8)[0]
    A = A[ys.min():]
    im = Image.fromarray(A.clip(0, 255).astype(np.uint8), 'RGBA')
    im = im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS)
    im.save(os.path.join(OUT, f'sea2_{name}.webp'), 'WEBP', quality=88, method=6)
    a = np.array(im)[..., 3]
    top = np.argmax(a > 128, axis=0)
    print(f'  sea2_{name}.webp {im.width}×{im.height}  浪上沿 y {top.min()}~{top.max()}  {os.path.getsize(os.path.join(OUT, f"sea2_{name}.webp")) // 1024}KB')
