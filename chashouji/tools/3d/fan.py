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
- 有正面，lean −20 / tilt −0.1 / roll 0.2（规范 7.4 第 1 条：转轴往光那边偏、正面往上抬，每一帧扇面都是亮面）。
- 屏幕上半径 45（web/trio_buddy.js B18 atk.r），整把宽 ~90px。

## 返工（2026-10-01，审查第四批 B18 ③）

审查：背后挂件是白纸面水墨山水 + 红穗、屏幕上约 90px；抽出来换成 3D 扇那一格变成深褐扇骨占满、纸面几条浅缝、41~65px ——
"抽出来的一瞬间，扇子缩掉一半，还变成了一块黑的"。照挂件改：
- 扇面白纸（#f4f1ea），上面水墨山：按扇面上的位置 (u 横向、v 径向) 给面分材质 —— 两座山头浓墨、山脚淡墨一层雾、左上一簇松、
  右边两列题字小块。材质分区不出描边，不增加墨块；每个折面横向再切 3 份，山的轮廓才不是一折一格。
- 扇骨深褐（#4a3426）、隔一根浅一根（材质分区读出一根根骨），纸面面积远大于扇骨（纸 0.40~1.0、骨 0~0.43）。
- 扇钉下挂红穗：一小段绳 + 一颗结 + 一束穗（锥），深红 #c8202a。
- 姿态按灯定（lean 25 / tilt 0.3 时正面有一半帧离光 > 65°，整面落进暗面发黑 —— 这就是审查看到的"一块黑的"）。
- 折深 ±45° → ±20°：描边只有剪影一档，折面翻到背面才出线；lean −20 时正面最多偏 40°，±20° 的折面不翻面、不出线，
  一深一浅的 Toon 明暗照样读得出折痕（±45° 的首版快测：每条折脊一道黑线，纸面读成一根根扇骨）。

跑：blender -b --python fan.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Matrix
import bpy

init()
mat('paper', '#f4f1ea')      # 白纸扇面（挂件图同色）
mat('ink', '#4b4f56')        # 浓墨：山头、松、题字（纯黑会跟描边贴成一条）
mat('ink2', '#a3a8ae')       # 淡墨：山脚的雾
mat('bamboo', '#4a3426')     # 深褐扇骨
mat('bamboo2', '#6b4d38')    # 隔一根浅一点的骨（材质分区读出一根根骨）
mat('pin', '#b9c0c8')
mat('tassel', '#c8202a')     # 红穗

SPAN = math.radians(150)
N = 12                        # 折面数
R0, R1 = 0.40, 1.0            # 扇面内外半径
DEP = 0.5 * math.tan(SPAN / N) * 0.36  # 折深系数：折面 ±20°（返工前 ±45°：一转斜一半折面翻背面，每条折脊一道描边，白纸切成一条条黑线）
T = 0.018                     # 扇面厚度


def pt(phi, r, y):
    """扇面在 XZ 平面，扇钉在原点、开口朝 +Z；相机沿 +Y 看，正面朝 −Y"""
    return (r * math.sin(phi), y, r * math.cos(phi))


# ---- 扇面：径向 12 圈、N 折、每折横向 4 份（山的轮廓按这个网格分材质）----
RINGS = [R0 + (R1 - R0) * i / 12 for i in range(13)]
SUB = 4
def ink_of(u, v):
    """扇面上 (u 横向 0~1 左→右, v 径向 0~1 扇根→外沿) 这一格是什么：0 白纸 / 1 浓墨 / 2 淡墨"""
    h = 0.12 + 0.72 * math.exp(-((u - 0.30) / 0.11) ** 2) + 0.50 * math.exp(-((u - 0.60) / 0.09) ** 2)   # 两座山的山脊（峰谷拉开）
    if 0.82 < u < 0.93 and 0.50 < v < 0.92 and (int(u * 48) % 3 != 1) and int(v * 12) % 2 == 0: return 1  # 右边两列题字
    if u < 0.16 and v > 0.70 and int(u * 40 + v * 12) % 3 == 0: return 1                                  # 左上一簇松
    if h > 0.25 and h - 0.17 < v < h: return 1                                                             # 山头浓墨
    if h > 0.3 and 0.05 < v < h - 0.17: return 2                                                           # 山脚雾
    return 0
verts, faces, fmat = [], [], []
nr = len(RINGS); NC = N * SUB + 1
def vid(side, c, j): return side * NC * nr + c * nr + j
for side in (0, 1):                               # 前后两层（厚度）
    for c in range(NC):
        k, f = divmod(c, SUB)
        if k == N: k, f = N - 1, SUB
        phi0 = -SPAN / 2 + k * SPAN / N
        phi = phi0 + f / SUB * SPAN / N
        s0 = -1 if k % 2 == 0 else 1              # 偶数折点在前（−Y），两边边骨贴着它
        for r in RINGS:
            y = (s0 + (-2 * s0) * f / SUB) * DEP * r  # 折面是平的：在两条折线之间线性插
            verts.append(pt(phi, r, y + (T if side else 0)))
for c in range(NC - 1):
    for j in range(nr - 1):
        u = (c + 0.5) / (NC - 1); v = ((RINGS[j] + RINGS[j + 1]) / 2 - R0) / (R1 - R0)
        m = ink_of(1 - u, v)                       # 相机从 −Y 看，phi 增大在屏幕左边
        a, b, cc, d = vid(0, c, j), vid(0, c + 1, j), vid(0, c + 1, j + 1), vid(0, c, j + 1)
        faces.append((a, d, cc, b)); fmat.append(m)
        a, b, cc, d = vid(1, c, j), vid(1, c + 1, j), vid(1, c + 1, j + 1), vid(1, c, j + 1)
        faces.append((a, b, cc, d)); fmat.append(0)
# 封边
for c in range(NC - 1):
    for j in (0, nr - 1):
        a, b = vid(0, c, j), vid(0, c + 1, j)
        cc, d = vid(1, c + 1, j), vid(1, c, j)
        faces.append((a, b, cc, d) if j == 0 else (a, d, cc, b)); fmat.append(0)
for c in (0, NC - 1):
    for j in range(nr - 1):
        a, b = vid(0, c, j), vid(0, c, j + 1)
        cc, d = vid(1, c, j + 1), vid(1, c, j)
        faces.append((a, b, cc, d) if c == 0 else (a, d, cc, b)); fmat.append(0)
leaf = add_mesh('leaf', verts, faces, 'paper')
leaf.data.materials.append(bpy.data.materials['ink']); leaf.data.materials.append(bpy.data.materials['ink2'])
for p, m in zip(leaf.data.polygons, fmat): p.material_index = m
# 法线统一朝外
bpy.context.view_layer.objects.active = leaf
leaf.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
leaf.select_set(False)


# ---- 扇根：实心竹色扇形块（扇骨并成一整块）----
M = 14
rv, rf = [], []
for side, y in ((0, -0.035), (1, 0.035)):
    rv.append((0, y, 0.0))
    for k in range(M + 1):
        phi = -SPAN / 2 + k * SPAN / M
        rv.append(pt(phi, R0 + 0.03, y))
c = M + 2
rm = []
for k in range(M):
    rf.append((0, k + 2, k + 1)); rf.append((c, c + k + 1, c + k + 2))
    rf.append((k + 1, k + 2, c + k + 2, c + k + 1)); rm += [k % 2, 0, 0]
rf.append((0, 1, c + 1, c)); rf.append((0, c, c + M + 1, M + 1)); rm += [0, 0]
root = add_mesh('root', rv, rf, 'bamboo')
root.data.materials.append(bpy.data.materials['bamboo2'])
for p, m in zip(root.data.polygons, rm): p.material_index = m

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

# ---- 红穗：扇钉往下一小段绳、一颗结、一束穗（锥，尖朝上）。挂件图上红穗挂在扇钉正下方 ----
prim('cylinder', 'tassel', vertices=10, radius=0.035, depth=0.22, location=(0, -0.02, -0.16))
prim('uv_sphere', 'tassel', segments=12, ring_count=8, radius=0.075, location=(0, -0.02, -0.30))
prim('cone', 'tassel', vertices=14, radius1=0.12, radius2=0.04, depth=0.34, location=(0, -0.02, -0.52))

ob = join_all(leaf)
dims = ob.dimensions
s = NOMINAL / max(dims)
ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0))
render_turntable('fan', active=ob, lean=-20, tilt=-0.10, roll=0.20, screen_r=45)
