"""泥土方块（档 3 三人组 B14 我的世界史蒂夫，把一块草方块扔出去砸女生、打中碎成像素块，2026-09-30）。

## 形体

- 一块 MC 草方块：泥土褐的方块身 + 顶上一层草皮（比泥土外扩一圈 = 草层与泥土层之间一道台阶）
  + 草皮沿侧面往下不规则"滴落"几格 + 表面若干像素格凸起。
- **像素感全是真几何**：每个凸起的格子是一块独立小方块（带裙边扎进主体），格子台阶就是描边；
  用材质分区画像素格不产生描边（skill 坑 4b），就是一块贴了图的纸盒。
- 棱长 1.6（不是 NOMINAL 2.0）：立方体斜着转对角线是棱长的 √3 倍，2.0 的话 3.46 超出相机画幅 3.3、有几格被切掉一角。
  引擎里 r 按棱长 1.6 放大到 30，屏幕上方块还是 ~60px 宽。
- 格子别碎：一面 GRID×GRID = 4×4，每格 0.4 单位 ≈ 屏幕 12px（r 30、1 单位 ≈ 30px），
  只让大约三分之一的格子凸出，凸出格之间留出平的格子，免得台阶线挤成黑带（g ≥ 2W）。
- 近似各向同性：lean 75。

跑：blender -b --python dirtblock.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy

random.seed(11)
E = 0.8              # 半边长。整块 2.0 的话斜着转时对角线 3.46 超出相机画幅 3.3，第一版 90°~180° 那几格被切掉一角；缩到 1.6、r 相应放大到 30
GRID = 4
C = 2 * E / GRID     # 一格
CAP = 0.06           # 草皮外扩（台阶）
DRIP = 0.035         # 滴落草外扩（比草皮少一点，免得和草皮侧面共面）
BUMP = 0.06          # 凸起格高度
SK = 0.05            # 裙边扎进去的深度
P_BUMP = 0.33

init()
mat('dirt', '#9a6438')
mat('dirt2', '#b07848')
mat('grass', '#72b840')
mat('grass2', '#8ccc50')

n = [0]


def box(lo, hi, m):
    n[0] += 1
    x0, y0, z0 = lo; x1, y1, z1 = hi
    vs = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return add_mesh('b%d' % n[0], vs, fs, m)


ZG = E - C           # 草皮下沿（顶上一格是草）
core = box((-E, -E, -E), (E, E, ZG + 0.02), 'dirt')
box((-E - CAP, -E - CAP, ZG), (E + CAP, E + CAP, E), 'grass')


def face_cell(axis, sign, i, j, out, m, zr=None):
    """侧面/底面上第 (i,j) 格凸起 out。axis: 法向轴 0/1/2"""
    a0 = -E + i * C; a1 = a0 + C
    b0 = -E + j * C; b1 = b0 + C
    if zr: b0, b1 = zr
    lo, hi = [0, 0, 0], [0, 0, 0]
    u, v = [k for k in range(3) if k != axis]
    lo[u], hi[u] = a0, a1
    lo[v], hi[v] = b0, b1
    if sign > 0: lo[axis], hi[axis] = E - SK, E + out
    else: lo[axis], hi[axis] = -E - out, -E + SK
    box(tuple(lo), tuple(hi), m)


# 四个侧面：每列随机滴落 0/1/2 格草，其余格子随机凸起泥土
for axis in (0, 1):
    for sign in (-1, 1):
        for i in range(GRID):
            drip = random.choice((0, 1, 1, 2))
            if i in (0, GRID - 1): drip = min(drip, 1)          # 角上别滴太长，棱边会糊
            if drip:
                face_cell(axis, sign, i, 0, DRIP, 'grass2', zr=(ZG - drip * C * 0.5 - (C * 0.5 if drip == 2 else 0) * 0, ZG + 0.03))
            for j in range(GRID - 1):                            # 顶格是草皮
                zc = -E + (j + 0.5) * C
                if zc > ZG - drip * C * 0.5 - 0.01: continue
                if random.random() < P_BUMP:
                    face_cell(axis, sign, i, j, BUMP, 'dirt2')
# 底面
for i in range(GRID):
    for j in range(GRID):
        if random.random() < P_BUMP: face_cell(2, -1, i, j, BUMP, 'dirt2')
# 顶面：草格凸起
for i in range(GRID):
    for j in range(GRID):
        if random.random() < P_BUMP:
            box((-E + i * C, -E + j * C, E - SK), (-E + (i + 1) * C, -E + (j + 1) * C, E + BUMP), 'grass2')

ob = join_all(core)
render_turntable('dirtblock', active=ob, lean=75, tilt=0.45, roll=0.3, screen_r=30)
