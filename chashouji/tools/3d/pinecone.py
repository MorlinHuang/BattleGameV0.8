"""松果（档 3 三人组 B8 伐木工光头强，抡胳膊把松果扔出去砸女生，2026-09-30）。

## 形体

- 一颗卵形松果：细长的深木色芯轴 + 按黄金角螺旋排开的一圈圈鳞片 + 顶上一小截梗。
- **每片鳞片是独立的一块楔形厚片**（根部窄薄、插进芯轴，外端宽厚、朝外朝下翘），
  像瓦片那样上一层压着下一层 —— 鳞片外端那一圈圈轮廓和互相遮挡就是结构，转起来一直在变。
  用材质分区在卵形上画鳞纹的话不产生描边（skill 坑 4b），就是一颗画了格子的棕色蛋。
- 鳞片数按 g ≥ 2W 定：屏幕直径 ~56px（r 26），1 单位 ≈ 28px，2W=5.6px ≈ 0.2 单位；
  **r 22、28 片那一版**：底端朝镜头的半圈帧是一团深褐（墨块 7/12，描边读成 6.7px），所以 r 放到 26（松果本来有拳头大）、
  鳞片减到 22、芯轴调亮。
- 芯轴颜色不能太深：measure_volume 按"离描边暖黑色差 < 46"数墨，深褐芯轴会被当成描边，密度虚高。
- 近似各向同性：lean 60（lean 80 时两端轮流正对镜头，端面是一圈鳞片尖 + 芯轴，最糊；60 时端面只斜着露出来）。

跑：blender -b --python pinecone.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy

SCALES = 22        # 鳞片数（黄金角螺旋）：40 片 + 放射楔块的第一版在 53px 上整颗是黑的（结构密度 86%）
H = 2.0            # 松果全长（NOMINAL，含梗）
GA = math.pi * (3 - math.sqrt(5))

init()
mat('scale', '#c07a40')
mat('core', '#a86a38')
mat('stem', '#7a5530')


def prof(t):
    """t=0 底尖、t=1 顶（梗那头）的卵形表面半径，最宽处偏下"""
    return 0.66 * math.sin(math.pi * (0.04 + 0.92 * t)) ** 0.7 * (1.0 - 0.22 * t)


def zof(t):
    return -H / 2 + 0.12 + (H - 0.5) * t


def surf(t, a):
    return Vector((math.cos(a) * prof(t), math.sin(a) * prof(t), zof(t)))


def shingle(t, a, i):
    """一片鳞：贴着卵形表面、根在上（t+DT）、尖在下并往外翘 LIFT 的瓦片，厚 TH，尖端收成菱形尖"""
    DT, LIFT, TH = 0.2, 0.2, 0.09
    r0, r1 = surf(min(1, t + DT), a) * 0.92, surf(t, a)
    d = Vector((math.cos(a), math.sin(a), 0))
    tip = r1 + d * LIFT
    root = Vector((r0.x, r0.y, r0.z))
    u = (tip - root).normalized()
    s = Vector((-d.y, d.x, 0))
    n = s.cross(u).normalized()               # 朝外
    wt = max(0.3, 2 * math.pi * prof(t) / 7 * 1.2)
    wr = wt * 0.55
    vs = []
    for p, w in ((root, wr), (tip - u * 0.12, wt)):
        for sd in (-1, 1):
            for hn in (-1, 1):
                vs.append(tuple(p + s * (sd * w / 2) + n * (hn * TH / 2)))
    vs.append(tuple(tip + n * TH * 0.5 * 0.4)); vs.append(tuple(tip - n * TH / 2))    # 尖端两个点（上/下）
    # 顶点：0 r-左-内 1 r-左-外 2 r-右-内 3 r-右-外 4 t-左-内 5 t-左-外 6 t-右-内 7 t-右-外 8 尖外 9 尖内
    f = [(0, 2, 3, 1), (1, 3, 7, 5), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2),
         (5, 7, 8), (4, 9, 6), (5, 8, 9, 4), (7, 6, 9, 8)]
    return add_mesh('sc%d' % i, vs, f, 'scale')


for i in range(SCALES):
    t = (i + 0.5) / SCALES * 0.9
    shingle(t, i * GA, i)

core = prim('uv_sphere', 'core', segments=16, ring_count=10, radius=1.0)
for v in core.data.vertices:
    t = (v.co.z + 1) / 2
    rr = max(0.02, prof(t * 0.95) * 0.9)
    q = Vector((v.co.x, v.co.y, 0))
    q = q.normalized() * rr if q.length > 1e-6 else q
    v.co = Vector((q.x, q.y, zof(t * 0.95)))
zt = zof(0.95)
prim('cylinder', 'stem', vertices=8, radius=0.08, depth=0.36, location=(0.04, 0, zt + 0.12), rotation=(0, 0.25, 0))

ob = join_all(core)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')      # 手拼的网格面朝向不一致：朝里的面 Toon 按背光画成近黑（珠子下半截整片黑），统一朝外
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
render_turntable('pinecone', active=ob, lean=60, tilt=0.35, roll=0.25, screen_r=26)
