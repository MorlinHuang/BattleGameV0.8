"""平底锅（档 3 三人组 G6 蜡笔小新妈式主妇，抡起平底锅扔过去、打中"当"一声，2026-09-30）。

## 形体

- 锅身是一整块旋转体（车削一条闭合轮廓：外底 → 外壁 → 外翻卷口 → 内壁 → 内底），有真厚度；
  **卷口外翻**成一圈凸唇，**内底一道凸圈**（半圆截面的圆环），两者都是轮廓上的真起伏，
  转起来各自一圈描边在变。
- 长柄：锅壁伸出一截金属柄脚（扎进锅壁）→ 一道金属箍 → 木柄（渐宽的扁柄，柄尾布尔真开一个挂孔）。
  锅内壁在柄那一侧 2 颗半埋的铆钉（球心落在壁面上，交角 90°，不会长相切睫毛）。
- 颜色：外壳深灰、锅内浅灰银、木柄棕。**锅不能全黑**：黑色跟描边贴死成一团（dumbbell/cassette 都踩过）。
- 细长件（锅 + 柄横着放）：按 skill 坑 5，lean 40 + roll 斜过来，别让它转成一根线。锅口朝相机、
  tilt 让锅口斜着露出来 —— 锅内那块银色圆面是认人的主面。
- 屏幕上半径 30（web/trio_buddy.js G6 atk.r），连柄长 ~64px。

跑：blender -b --python pan.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Matrix
import bpy

init()
mat('shell', '#4a4e58')      # 外壳深灰
mat('inner', '#c9ced6')      # 锅内浅灰银
mat('wood', '#a8683a')       # 木柄（识别色）
mat('metal', '#9aa2ac')      # 柄脚/箍/铆钉

# ---- 锅身：车削轮廓 (r, z)，建在 Z 轴上、锅口朝 +Z，最后整体转成朝相机 ----
OUT = [(0.0, 0.0), (0.43, 0.0), (0.47, 0.025), (0.55, 0.165),
       (0.59, 0.185), (0.615, 0.205), (0.60, 0.225), (0.565, 0.225)]      # 外底→外壁→外翻卷口
IN = [(0.53, 0.205), (0.445, 0.045), (0.42, 0.03)]                      # 内壁
RING = [(0.30 + 0.035 * math.cos(a), 0.03 + 0.035 * math.sin(a))          # 内底凸圈：半圆截面
        for a in [math.radians(d) for d in (0, 30, 60, 90, 120, 150, 180)]]
PROF = OUT + IN + RING + [(0.0, 0.03)]
N_OUT = len(OUT) - 1         # 前 N_OUT 段是外壳，其后是锅内
SEG = 48
verts, faces, fm = [], [], []
# 首尾两点在轴上，各一个顶点
verts.append((0, 0, PROF[0][1]))
for r, z in PROF[1:-1]:
    for k in range(SEG):
        a = 2 * math.pi * k / SEG
        verts.append((r * math.cos(a), r * math.sin(a), z))
verts.append((0, 0, PROF[-1][1]))
M = len(PROF) - 2
def v(j, k): return 1 + j * SEG + (k % SEG)
for k in range(SEG):
    faces.append((0, v(0, k + 1), v(0, k))); fm.append(0)
    for j in range(M - 1):
        faces.append((v(j, k), v(j, k + 1), v(j + 1, k + 1), v(j + 1, k))); fm.append(0 if j + 1 < N_OUT else 1)
    faces.append((len(verts) - 1, v(M - 1, k), v(M - 1, k + 1))); fm.append(1)
body = add_mesh('body', verts, faces, 'shell')
body.data.materials.append(bpy.data.materials['inner'])
for p, m in zip(body.data.polygons, fm): p.material_index = m
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
body.select_set(False)

# ---- 柄：沿 +X 伸出，略上扬 ----
RISE = math.radians(12)
def along(x, z0=0.13):
    """柄轴线上离锅心 x 处的点"""
    return (x, 0.0, z0 + (x - 0.55) * math.tan(RISE))


def bar(mname, x0, x1, w, h):
    c = along((x0 + x1) / 2)
    ob = prim('cube', mname, size=1)
    ob.matrix_world = Matrix.Translation(c) @ Matrix.Rotation(-RISE, 4, 'Y') @ Matrix.Diagonal((x1 - x0, w, h, 1.0))
    return ob


bar('metal', 0.48, 0.80, 0.13, 0.055)                  # 柄脚，扎进锅壁
bar('metal', 0.78, 0.86, 0.19, 0.12)                   # 金属箍（比木柄粗一圈，凸台）
# 木柄：渐宽的扁柄，放样 8 个截面
X0, X1 = 0.84, 1.42
secs = []
for i in range(9):
    t = i / 8
    x = X0 + (X1 - X0) * t
    w = 0.15 + 0.09 * t                                # 越往尾越宽，挂孔那里够宽
    h = 0.10 - 0.02 * t
    secs.append((x, w, h))
hv, hf = [], []
OCT = [(0.35, 1), (1, 0.45), (1, -0.45), (0.35, -1), (-0.35, -1), (-1, -0.45), (-1, 0.45), (-0.35, 1)]   # 削角扁八边形截面
nx, nz = -math.sin(RISE), math.cos(RISE)                # 柄截面里"上"的方向
for x, w, h in secs:
    cx, _, cz = along(x)
    for dy, dz in OCT:
        hv.append((cx + nx * h / 2 * dz, w / 2 * dy, cz + nz * h / 2 * dz))
S = 8
for i in range(len(secs) - 1):
    for k in range(S):
        a, b = i * S + k, i * S + (k + 1) % S
        hf.append((a, b, b + S, a + S))
hf.append(tuple(range(S))[::-1]); hf.append(tuple(range((len(secs) - 1) * S, len(secs) * S)))
handle = add_mesh('handle', hv, hf, 'wood')
bpy.context.view_layer.objects.active = handle
handle.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
handle.select_set(False)
# 柄尾挂孔：布尔真开孔
hx, _, hz = along(1.30)
cut = prim('cylinder', 'wood', vertices=16, radius=0.055, depth=0.6, location=(hx, 0, hz))
cut.rotation_euler = (0, -RISE, 0)
bo = handle.modifiers.new('hole', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = cut
bpy.context.view_layer.objects.active = handle
bpy.ops.object.modifier_apply(modifier='hole')
bpy.data.objects.remove(cut, do_unlink=True)

# 铆钉：锅内壁柄那一侧两颗，球心落在内壁面上（半埋）
zr = 0.125
rr = 0.445 + (0.53 - 0.445) * (zr - 0.045) / (0.205 - 0.045)
for y in (-0.085, 0.085):
    prim('uv_sphere', 'metal', segments=12, ring_count=8, radius=0.05, location=(math.sqrt(rr * rr - y * y), y, zr))

ob = join_all(body)
# 锅口转向相机（−Y），并缩放到最长 2.0：必须烘进网格 —— render_turntable 会覆盖 rotation_euler
ob.data.transform(Matrix.Rotation(math.radians(90), 4, 'X'))
ob.data.update()
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS'); ob.location = (0, 0, 0)
s = NOMINAL / max(ob.dimensions)
ob.data.transform(Matrix.Diagonal((s, s, s, 1.0)))
render_turntable('pan', active=ob, lean=40, tilt=0.55, roll=0.55, screen_r=30)
