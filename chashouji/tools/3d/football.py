"""足球（档 2，灭迹党，臭袜子足球雨里重的那几下，2026-09-27）—— 黑白拼块的经典足球，从女生头顶掉下来砸她。

## 形体

- **截角二十面体**：12 块黑五边形 + 20 块白六边形。每一块做成**单独的一块厚片**（往里挤出一段），
  块与块之间留一道缝（GAP），缝底下是一颗深灰内球 —— 每块都有自己的一圈轮廓，转起来 32 块的遮挡、
  透视缩短一直在变，内部结构密度是四件里最高的。拼块贴着面放不留缝的话，没有任何内部描边
  （材质分区不产生描边），就是一个画了黑斑的白球。
- 拼块顶面鼓一点（按到球心的距离推到球面上，中心再细分一次），不然 32 个平面拼出来像多面体骰子。
- 各向同性：lean 90。

跑：blender -b --python football.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy, bmesh

R = 1.0            # 球半径（最后归一）
GAP = 0.07         # 拼块往自己中心缩多少（占该块外接半径的比例）→ 缝
THICK = 0.12       # 拼块厚度（往球心挤）

init()
mat('white', '#f4f4f0')
mat('black', '#2e2e34')
mat('core', '#55555c')

phi = (1 + 5 ** 0.5) / 2
base = [(0, 1, 3 * phi), (1, 2 + phi, 2 * phi), (phi, 2, 2 * phi + 1)]
pts = set()
for b in base:
    for (i, j, k) in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):          # 偶置换
        p = (b[i], b[j], b[k])
        for sx in (1, -1):
            for sy in (1, -1):
                for sz in (1, -1):
                    pts.add((p[0] * sx, p[1] * sy, p[2] * sz))
pts = [Vector(p) for p in pts]
rr = pts[0].length
pts = [p / rr * R for p in pts]
bm = bmesh.new()
vs = [bm.verts.new(p) for p in pts]
bmesh.ops.convex_hull(bm, input=vs)
bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(1), verts=bm.verts, edges=bm.edges)
faces = [[v.co.copy() for v in f.verts] for f in bm.faces]
bm.free()
print('FACES', len(faces), sorted(set(len(f) for f in faces)), flush=True)

verts, polys, mats = [], [], []
def add(poly, m):
    polys.append(poly); mats.append(m)
for f in faces:
    c = sum(f, Vector()) / len(f)
    ring = [c + (p - c) * (1 - GAP) for p in f]
    mid = [(ring[i] + ring[(i + 1) % len(ring)]) / 2 for i in range(len(ring))]
    top = []                                   # 顶面：角点 + 边中点，推到球面上（鼓起来）
    for i in range(len(ring)):
        top += [ring[i].normalized() * R, mid[i].normalized() * R]
    ctop = c.normalized() * R * 1.0
    bot = [p.normalized() * (R - THICK) for p in top]
    n = len(top); o = len(verts)
    verts += [tuple(p) for p in top] + [tuple(p) for p in bot] + [tuple(ctop)]
    m = 1 if len(f) == 5 else 0
    for i in range(n):                         # 顶面扇形（带中心点，按同心结构鼓）
        add((o + 2 * n, o + i, o + (i + 1) % n), m)
    add(tuple(o + n + (n - 1 - i) for i in range(n)), m)   # 底面
    for i in range(n):                         # 侧壁
        j = (i + 1) % n
        add((o + i, o + n + i, o + n + j, o + j), m)
ob = add_mesh('ball', verts, polys, 'white')
ob.data.materials.append(bpy.data.materials['black'])
for p, m in zip(ob.data.polygons, mats):
    p.material_index = m
prim('ico_sphere', 'core', subdivisions=3, radius=R - THICK * 0.5)

ob = join_all(ob)
s = NOMINAL / (2 * R)
ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0))
render_turntable('football', active=ob, lean=90, tilt=0.3, roll=0.2, screen_r=52)
