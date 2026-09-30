"""打赏小火箭（档 3 三人组 G19 网红主播，坐无人机直播，甩出打赏小火箭砸男生、打中炸彩纸，2026-09-30）。

## 形体

- 直播打赏礼物那种卡通火箭：白色机身（圆柱，肚子略鼓）+ 红色尖头 + 三片独立的红色尾翼（厚三角片）
  + 机身侧面一个圆舷窗（凸起的银框 + 蓝色窗面）+ 机身中段一道红色腰带（凸环）+ 尾部灰色喷口（外扩的截锥）。
- **尾翼、舷窗框、腰带、喷口都是单独的几何**：转起来三片尾翼轮流转到前面、舷窗一会儿正对一会儿转到侧面，
  互相遮挡一直在变。只做一根白棍画个窗的话就是一根会转的粉笔。
- 零件间距按 g ≥ 2W：r 28 → 1 单位 ≈ 30 屏幕 px，2W ≈ 0.19 单位；尾翼厚 0.08（侧对时是一条线，但三片错开 120°，
  总有两片斜着露出面）、舷窗框外径 0.2（屏幕 12px）。
- 细长件，长轴竖着（Z），lean 45：长轴始终垂直于转轴，屏幕长度最短 cos45 ≈ 0.7，不会缩成一个点。
- 屏幕上半径 28（G19 atk.r 按这个填）。

跑：blender -b --python rocket.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

init()
mat('body', '#f4f4f0')
mat('red', '#e8384a')         # 识别色
mat('glass', '#6ac8f0')
mat('frame', '#c9d0d8')
mat('nozzle', '#8a929c')

R = 0.3                        # 机身半径；整根长 2.0（NOMINAL）：喷口 −1.0 → 尖头 +1.0


def lathe(prof, m, n=24):
    """回转体（绕 Z）：prof = [(r, z)]，r=0 收成一点"""
    v, rings = [], []
    for r, z in prof:
        if r < 1e-6: rings.append([len(v)]); v.append((0, 0, z)); continue
        rg = []
        for i in range(n):
            a = 2 * math.pi * i / n
            rg.append(len(v)); v.append((r * math.cos(a), r * math.sin(a), z))
        rings.append(rg)
    f = []
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1: f += [(A[0], B[(i + 1) % n], B[i]) for i in range(n)]
        elif len(B) == 1: f += [(A[i], A[(i + 1) % n], B[0]) for i in range(n)]
        else: f += [(A[i], A[(i + 1) % n], B[(i + 1) % n], B[i]) for i in range(n)]
    return add_mesh('lathe', v, f, m)


body = lathe([(0, -0.62), (R * 0.9, -0.62), (R, -0.4), (R * 1.08, 0.0), (R, 0.35), (R * 0.95, 0.42), (0, 0.42)], 'body')
lathe([(0, 0.4), (R * 0.97, 0.4), (R * 0.8, 0.65), (R * 0.45, 0.85), (0, 1.0)], 'red')            # 尖头（底比机身口略大一圈 = 台阶）
lathe([(0, -0.2), (R * 1.14, -0.2), (R * 1.14, -0.06), (0, -0.06)], 'red')                         # 腰带
lathe([(0, -0.6), (R * 0.7, -0.6), (R * 0.95, -1.0), (R * 0.6, -1.0), (0, -0.9)], 'nozzle')        # 喷口
# 三片尾翼：厚三角片，根贴机身下段，外缘往下斜
for k in range(3):
    a = 2 * math.pi * k / 3 + 0.3
    c, s = math.cos(a), math.sin(a)
    pts = [(R * 0.9, -0.2), (R * 0.9, -0.75), (R + 0.42, -0.95), (R + 0.36, -0.55)]   # (径向, z)
    v = []
    for t in (-0.04, 0.04):
        for r, z in pts:
            v.append((r * c - t * s, r * s + t * c, z))
    f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    add_mesh('fin', v, f, 'red')
# 舷窗：侧面（−Y 朝镜头）一个凸起的银框 + 蓝色窗面
prim('torus', 'frame', major_radius=0.14, minor_radius=0.045, location=(0, -R * 1.04, 0.16), rotation=(math.pi / 2, 0, 0))
prim('cylinder', 'glass', vertices=20, radius=0.12, depth=0.06, location=(0, -R * 1.0, 0.16), rotation=(math.pi / 2, 0, 0))

ob = join_all(body)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')      # 手拼的网格面朝向不一定一致：Toon 明暗靠法线，统一朝外
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
render_turntable('rocket', active=ob, lean=45, tilt=0.25, roll=0.35, screen_r=28)
