"""松果（档 3 三人组 B8 伐木工光头强，抡胳膊把松果扔出去砸女生，2026-09-30；审查第三轮 6.7 返工同日）。

## 形体

- **上尖下圆的长卵形**：长 2.0（NOMINAL）、最粗 1.24，长宽比 1.6。梗那头（底）是半个椭圆的圆头，往尖头那边一路收细。
  首版是长宽比 ~1.5 的卵形，但 lean 60 让长轴大半时间对着镜头，屏幕上就是一颗圆球，鳞片读成斑点 ——
  跟同屏的 B27 牛丸是同一种"棕色麻点球"（审查第三轮 6.7）。
- **鳞片一圈圈错位排**：每圈 6 齿、5 圈，相邻两圈错开半齿再拧一点，斜着看就是一条条螺旋；每圈是一整块带厚度的"裙子"，
  上沿藏在上一圈底下，下沿往梗那头翘出去、剪成人字齿。上一圈压着下一圈的那道人字边就是结构，转起来遮挡一直在变。**片尖那一截用浅色**（材质分区，不产生描边，只管"认得出"）：一圈圈浅色人字尖排下来，才是松果。
- 鳞片大小按 g ≥ 2W 定：屏幕直径 ~56px（r 26），1 单位 ≈ 27px，2W = 5.6px ≈ 0.21 单位；最粗那圈一片宽 0.56 单位（15px）、
  每圈露出 0.3 单位（8px），每片露出的那一截里填色 > 描边。
- 芯轴颜色不能太深：measure_volume 按"离描边暖黑色差 < 46"数墨，深褐芯轴会被当成描边，密度虚高。
- 转法同哑铃：长轴在 X 上，转轴离屏幕横轴 20°（lean −70），长轴在屏幕上永远 ≥ 0.76 倍长，尖头一直朝一边、看得出是长条。

跑：blender -b --python pinecone.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector
import bpy

LEN, RMAX, TB = 2.0, 0.62, 0.3      # 全长（不含梗）、最粗半径、最粗处离底多远（占全长）
ROWS, PER = 5, 6                    # 鳞片圈数、每圈几片

init()
mat('scale', '#8a3a10')           # 亮面渲出来会褪成粉肉色（#a8501c 亮面落成 e6b48c，快测），底色给深一档；再深暗面就贴近描边色
mat('tip', '#f4b060')               # 片尖提亮：比片身亮一档的橙黄（米黄 #f8d8a0 亮面褪成白，整颗像一张白网，快测）
mat('core', '#9a6034')
mat('stem', '#7a5530')


def prof(t):
    """t=0 底（梗那头，圆）、t=1 尖头的表面半径"""
    if t < TB:
        return RMAX * math.sqrt(max(0.0, 1 - ((TB - t) / TB) ** 2))
    return RMAX * max(0.0, 1 - ((t - TB) / (1 - TB)) ** 1.4)


def xof(t):
    return -LEN / 2 + LEN * t


def pt(t, a, lift=0.0):
    r = prof(t) + lift
    return Vector((xof(t), math.cos(a) * r, math.sin(a) * r))


def skirt(t0, t1, twist, row):
    """一圈鳞：一整块带厚度的"裙子"，下沿（靠梗那头）是 PER 个人字齿、往外翘 LIFT，上沿藏进上一圈底下。
    一圈是一整块网格：齿与齿之间不出描边，只有齿沿那道人字线和它压住下一圈的遮挡线 —— 5 圈就是 5 道人字折线，
    一眼是松果的鳞纹。一片片独立的鳞（上一版）每片上下两面各出一圈剪影线，24 片在 65px 上整颗 75% 是描边色（快测）。
    齿沿那一带（u < TIPU）用浅色：片尖提亮"""
    LIFT, TH, TOOTH, TIPU = 0.13, 0.06, 0.14, 0.2
    NA, NU = PER * 4, 4
    outer, inner = [], []
    for j in range(NU + 1):
        u = j / NU
        for k in range(NA):
            ph = (k % 4) / 4                                   # 一齿四个点：谷、半、尖、半
            tooth = TOOTH * (1 - abs(ph - 0.5) * 2)            # 谷 0 → 尖 TOOTH
            t = (t0 - tooth) * (1 - u) + t1 * u
            a = 2 * math.pi * (k - 2) / NA + twist
            lift = LIFT * (1 - u) ** 1.5
            outer.append(pt(t, a, lift))
            inner.append(pt(t, a, lift - TH))
    vs = [tuple(v) for v in outer + inner]
    M = len(outer)
    f, m = [], []
    for j in range(NU):
        for k in range(NA):
            k2 = (k + 1) % NA
            q = (j * NA + k, j * NA + k2, (j + 1) * NA + k2, (j + 1) * NA + k)
            f.append(q); m.append(1 if j / NU < TIPU else 0)
            f.append(tuple(M + x for x in q[::-1])); m.append(0)
    for k in range(NA):                                        # 齿沿、上沿的厚度面
        k2 = (k + 1) % NA
        f.append((k2, k, M + k, M + k2)); m.append(1)
        top = NU * NA
        f.append((top + k, top + k2, M + top + k2, M + top + k)); m.append(0)
    ob = add_mesh('row%d' % row, vs, f, 'scale')
    ob.data.materials.append(bpy.data.materials['tip'])
    for p_, mi in zip(ob.data.polygons, m):
        p_.material_index = mi
    return ob


for row in range(ROWS):
    t0 = 0.1 + row * (0.8 / ROWS)                     # 齿沿位置：从底往尖头一圈圈排
    skirt(t0, min(0.97, t0 + 0.8 / ROWS * 1.6), (math.pi / PER) * (row % 2) + row * 0.15, row)

# 芯轴：旋转体，比鳞片表面收进去一点；尖头收成一个尖
cv, cf, NS = [], [], 16
TS = [k / 20 for k in range(21)]
for t in TS:
    r = max(0.015, prof(t) * 0.86)
    for k in range(NS):
        a = 2 * math.pi * k / NS
        cv.append((xof(t), math.cos(a) * r, math.sin(a) * r))
for j in range(len(TS) - 1):
    for k in range(NS):
        k2 = (k + 1) % NS
        cf.append((j * NS + k, j * NS + k2, (j + 1) * NS + k2, (j + 1) * NS + k))
cv += [(xof(0) - 0.02, 0, 0), (xof(1) + 0.03, 0, 0)]
b0, b1 = len(cv) - 2, len(cv) - 1
for k in range(NS):
    k2 = (k + 1) % NS
    cf.append((b0, k2, k)); cf.append((b1, (len(TS) - 1) * NS + k, (len(TS) - 1) * NS + k2))
core = add_mesh('core', cv, cf, 'core')
prim('cylinder', 'stem', vertices=8, radius=0.08, depth=0.3, location=(xof(0) - 0.12, 0.03, 0), rotation=(0, math.pi / 2 + 0.25, 0))

bpy.ops.object.select_all(action='SELECT')           # 旋转烤进网格：长轴确定在 X（理由见 dumbbell.py）
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
ob = join_all(core)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')      # 手拼的网格面朝向不一致：朝里的面 Toon 按背光画成近黑，统一朝外
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
render_turntable('pinecone', active=ob, lean=-70, tilt=0.0, roll=0.1, screen_r=26)
