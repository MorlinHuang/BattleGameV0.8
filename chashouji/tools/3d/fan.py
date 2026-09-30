"""题诗折扇（档 3 三人组 B18 唐伯虎式摇扇才子，把一把题了诗的折扇甩出去砸女生，2026-09-30）。

## 形体

- 展开 150° 的折扇。**扇面是真的折痕**：12 个折面一正一反交替倾斜 ±45°（锯齿形），整片按圆锥缩放
  （折深跟半径成正比，越近扇钉越浅），再加一点厚度做成封闭网格。
  正对时折面全朝前、不出线；一转斜，背光那一半折面翻成背面，每条折脊都长出一条描边 —— 侧着转时
  锯齿侧影就是它的体积。折面在外沿屏幕宽 ~7px（g ≥ 2W = 5.6px），再多就并成黑带。
- 两根较粗的大骨（边骨，竹色）贴在扇面两边外侧，顺着折深斜着走；扇钉处一颗穿透的小圆钉。
- 扇面下半截（扇钉到扇面之间）是一块实心的竹色扇根：真扇子这里是一排扇骨，但在 64px 上骨距只有
  3~5px，g < 2W 必并成黑块，所以并成一整块。
- 扇面上方一排题字色块（材质分区，只管认得出，不产生描边）。
- 有正面，lean 25：lean 45 时有一半帧转到侧对，扇面只剩一根折线、整帧是墨块（6/12）；
  25 时正面最多偏 50°，扇形始终展开，折痕的锯齿靠 tilt 斜着看出来。
- 屏幕上半径 30（web/trio_buddy.js B18 atk.r），整把宽 ~64px。

跑：blender -b --python fan.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Matrix
import bpy

init()
mat('paper', '#f3e6c0')      # 米白淡黄扇面
mat('ink', '#6a5a4e')        # 题字色块：淡墨（真墨黑会跟描边贴成一条）
mat('bamboo', '#d2a45a')     # 竹色扇骨
mat('pin', '#b9c0c8')

SPAN = math.radians(150)
N = 12                        # 折面数
R0, R1 = 0.40, 1.0            # 扇面内外半径
DEP = 0.5 * math.tan(SPAN / N) * 1.0   # 折深系数：面在屏幕上的弧宽 × tan45 的一半 → y = ±DEP·r
T = 0.018                     # 扇面厚度


def pt(phi, r, y):
    """扇面在 XZ 平面，扇钉在原点、开口朝 +Z；相机沿 +Y 看，正面朝 −Y"""
    return (r * math.sin(phi), y, r * math.cos(phi))


# ---- 扇面：径向 4 圈（最外一圈到 0.9 是题字带），N 折 ----
RINGS = [R0, 0.70, 0.90, R1]
verts, faces, fmat = [], [], []
for side in (0, 1):                               # 前后两层（厚度）
    for k in range(N + 1):
        phi = -SPAN / 2 + k * SPAN / N
        s = -1 if k % 2 == 0 else 1               # 偶数折点在前（−Y），两边边骨贴着它
        for r in RINGS:
            verts.append(pt(phi, r, s * DEP * r + (T if side else 0)))
nr = len(RINGS)
def vid(side, k, j): return side * (N + 1) * nr + k * nr + j
for k in range(N):
    for j in range(nr - 1):
        a, b, c, d = vid(0, k, j), vid(0, k + 1, j), vid(0, k + 1, j + 1), vid(0, k, j + 1)
        faces.append((a, d, c, b)); fmat.append(1 if (j == 1 and 3 <= k <= 8) else 0)
        a, b, c, d = vid(1, k, j), vid(1, k + 1, j), vid(1, k + 1, j + 1), vid(1, k, j + 1)
        faces.append((a, b, c, d)); fmat.append(0)
# 封边
for k in range(N):
    for j in (0, nr - 1):
        a, b = vid(0, k, j), vid(0, k + 1, j)
        c, d = vid(1, k + 1, j), vid(1, k, j)
        faces.append((a, b, c, d) if j == 0 else (a, d, c, b)); fmat.append(0)
for k in (0, N):
    for j in range(nr - 1):
        a, b = vid(0, k, j), vid(0, k, j + 1)
        c, d = vid(1, k, j + 1), vid(1, k, j)
        faces.append((a, b, c, d) if k == 0 else (a, d, c, b)); fmat.append(0)
leaf = add_mesh('leaf', verts, faces, 'paper')
leaf.data.materials.append(bpy.data.materials['ink'])
for p, m in zip(leaf.data.polygons, fmat): p.material_index = m
# 法线统一朝外
bpy.context.view_layer.objects.active = leaf
leaf.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
leaf.select_set(False)


# ---- 扇根：实心竹色扇形块（扇骨并成一整块）----
M = 10
rv, rf = [], []
for side, y in ((0, -0.035), (1, 0.035)):
    rv.append((0, y, 0.0))
    for k in range(M + 1):
        phi = -SPAN / 2 + k * SPAN / M
        rv.append(pt(phi, R0 + 0.03, y))
c = M + 2
for k in range(M):
    rf.append((0, k + 2, k + 1)); rf.append((c, c + k + 1, c + k + 2))
    rf.append((k + 1, k + 2, c + k + 2, c + k + 1))
rf.append((0, 1, c + 1, c)); rf.append((0, c, c + M + 1, M + 1))
root = add_mesh('root', rv, rf, 'bamboo')

# ---- 两根边骨：粗竹条，顺着折深斜着贴在扇面两边前侧 ----
for sgn in (-1, 1):
    phi = sgn * (SPAN / 2 + math.radians(2.5))
    L = R1 + 0.10
    # 边骨从扇钉下方 0.1 到外沿；随半径往前（−Y）斜，贴着偶数折点
    y_mid = -DEP * (L / 2) - 0.035
    tilt = math.atan(DEP)
    ob = prim('cube', 'bamboo', size=1, location=pt(phi, L / 2 - 0.08, y_mid), scale=(0.10, 0.07, L + 0.06))
    ob.rotation_euler = (0, 0, 0)
    ob.matrix_world = (Matrix.Translation(pt(phi, L / 2 - 0.08, y_mid)) @ Matrix.Rotation(phi, 4, 'Y')
                       @ Matrix.Rotation(tilt, 4, 'X') @ Matrix.Diagonal((0.10, 0.07, L + 0.06, 1.0)))

# ---- 扇钉：穿透前后的小圆钉 ----
prim('cylinder', 'pin', vertices=16, radius=0.075, depth=0.26, location=(0, -0.02, 0.0), rotation=(math.pi / 2, 0, 0))

ob = join_all(leaf)
dims = ob.dimensions
s = NOMINAL / max(dims)
ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0))
render_turntable('fan', active=ob, lean=25, tilt=0.30, roll=0.20, screen_r=30)
