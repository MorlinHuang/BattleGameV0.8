"""棒球棍（档 3 三人组 G10 小丑女式坏女孩，甩棒球棍旋转飞过去，打中蹦 BAM 字，2026-09-30）。

## 形体

- 木棒球棍：一整根车床旋出来的回转体（尾部球形握把帽 knob → 细握柄 → 锥形过渡 → 粗棍身），
  棍头端面一圈外扩的凸缘；握柄上三圈凸起的胶带（粉/蓝/粉，小丑女配色），棍身再套两圈粉蓝彩带。
- 棍身用 lathe 一次旋成一整块网格，不拿圆柱+圆锥+球拼：同半径拼接处两面几乎相切，Freestyle 会长小黑睫毛（skill 坑 7）。
- **胶带环、彩带环、端面凸缘都是单独的真几何**（比杆粗一圈的短圆柱）：细长件剥掉外轮廓后里面剩的面积很小，
  内部描边只能靠沿长轴排开的这些环。材质分区画的色环不产生描边（skill 坑 4b），就是一根画了花纹的棍子。
- r 32 → 1 单位 = 32 屏幕 px，描边 2.8px，g ≥ 2W ≈ 0.18 单位：环宽 ≥ 0.14、环间距 ≥ 0.2，不然两环的描边连成黑带（skill 坑 4）。
- 长轴竖着（Z），转轴 lean 45：长轴始终垂直于转轴，屏幕长度最短 cos45 ≈ 0.7，不会端面朝镜头缩成一个圆；
  回转体本身没有正面，lean 再大只会多出几帧"一个圆盘"的废帧。

跑：blender -b --python bat.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

init()
mat('wood', '#e6b877')
mat('pink', '#ff4fa3')
mat('blue', '#3aa6ff')
mat('end', '#c98f4e')


def lathe(name, prof, m, seg=20):
    """prof: [(半径, z)] 从下到上，两端自动封口"""
    verts, faces = [], []
    n = len(prof)
    for r, z in prof:
        for k in range(seg):
            a = 2 * math.pi * k / seg
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(n - 1):
        for k in range(seg):
            a, b = i * seg + k, i * seg + (k + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    verts.append((0, 0, prof[0][1])); verts.append((0, 0, prof[-1][1]))
    c0, c1 = len(verts) - 2, len(verts) - 1
    for k in range(seg):
        faces.append((c0, (k + 1) % seg, k))
        faces.append((c1, (n - 1) * seg + k, (n - 1) * seg + (k + 1) % seg))
    return add_mesh(name, verts, faces, m)


def ring(r, z0, z1, m, seg=20):
    return prim('cylinder', m, vertices=seg, radius=r, depth=z1 - z0, location=(0, 0, (z0 + z1) / 2))


# 棍身轮廓：knob（-1.0~-0.86）→ 握柄 0.085 → 锥形 → 棍身 0.2
prof = [(0.0, -1.0), (0.12, -0.99), (0.16, -0.95), (0.165, -0.91), (0.14, -0.87), (0.09, -0.84),
        (0.085, -0.25), (0.10, -0.05), (0.14, 0.2), (0.185, 0.45), (0.2, 0.6), (0.2, 0.93), (0.19, 0.95)]
lathe('bat', prof, 'wood')
# 棍头端面凸缘：一圈外扩的薄环
ring(0.225, 0.9, 0.98, 'end')
# 握柄三圈胶带
for i, (z, m) in enumerate(((-0.74, 'pink'), (-0.52, 'blue'), (-0.30, 'pink'))):
    ring(0.125, z - 0.07, z + 0.07, m, 16)
# 棍身两圈彩带
ring(0.235, 0.40, 0.54, 'blue')     # 锥形段上略大一圈，下半截扎进棍身
ring(0.23, 0.70, 0.83, 'pink')

ob = join_all()
render_turntable('bat', active=ob, lean=45, tilt=0.25, roll=0.35, screen_r=32)
