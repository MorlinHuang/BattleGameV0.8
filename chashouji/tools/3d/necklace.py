"""心形蓝宝石项链（档 3 三人组 G15 船头红发少女，泰坦尼克 Rose 式，把"海洋之心"扔出去砸男生，2026-09-30）。

## 形体

- "海洋之心"：一颗厚的心形蓝宝石（正反两面各两圈台阶收到顶面，刻面宝石的样子）+ 外面一圈银色包边（独立的扁环）
  + 包边外一圈独立的小白钻（每颗一个八面体）+ 顶上一个挂环 + 一截粗银珠链。
- 体积感来自**一颗颗独立的小白钻**和包边：转起来每颗钻各自的轮廓、跟宝石的遮挡一直在变。
  宝石本身的刻面不产生描边（Freestyle 在这套用法下只画剪影和自遮挡线，skill 坑 2），只管"认得出"。
- 钻石颗数按 g ≥ 2W 定：r 26 → 1 单位 ≈ 26 屏幕 px，2W = 5.6px ≈ 0.22 单位；
  心形外圈周长 ~4.3 单位，9 颗、每颗宽 0.2 → 颗与颗之间 ~0.28 单位，不会连成一圈黑。
- 链子不做细链（细链在 50px 上就是一根墨线），做 7 颗大银珠从挂环往上排成一个 V 字的一小截。
- 有正面，lean 25：lean 40 时 5/12 帧转到侧对，心形缩成一根带钻的线；25 时最多偏 50°，始终认得出是心。
- 屏幕上半径 26（G15 atk.r 按这个填）。

跑：blender -b --python necklace.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

init()
mat('gem', '#2a6fd6')         # 宝石蓝（识别色）
mat('gem2', '#5ea2f0')        # 顶面亮一档
mat('silver', '#c9d0d8')
mat('diamond', '#f4f8ff')

SC = 0.55                     # 心形半宽（单位）；整件竖着 ~2.0 = NOMINAL（心 + 挂环 + 珠链）
NP = 40


def heart(t):
    """标准心形曲线，归一到半宽 1"""
    x = 16 * math.sin(t) ** 3
    z = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
    return x / 16, (z + 2) / 16


OUT = [heart(2 * math.pi * i / NP) for i in range(NP)]


def ring_pts(k, y):
    return [(x * SC * k, y, z * SC * k) for x, z in OUT]


# 宝石：外沿（k 1.0，厚 ±0.07）→ 台阶（k 0.72，厚 ±0.16）→ 顶面（k 0.45，厚 ±0.2），正反对称；顶面用亮一档的材质
LAY = [(1.0, 0.07), (0.72, 0.16), (0.45, 0.2)]
verts, faces, mats = [], [], []
rings = []
for side in (-1, 1):
    rs = []
    for k, t in LAY:
        o = len(verts); verts += ring_pts(k, side * t); rs.append(o)
    c = len(verts); verts.append((0, side * 0.2, 0.0)); rs.append(c)
    rings.append(rs)
for side, rs in zip((-1, 1), rings):
    for j in range(2):
        a, b = rs[j], rs[j + 1]
        for i in range(NP):
            i2 = (i + 1) % NP
            f = (a + i, a + i2, b + i2, b + i)
            faces.append(f if side < 0 else f[::-1]); mats.append(0)
    a, c = rs[2], rs[3]
    for i in range(NP):
        i2 = (i + 1) % NP
        f = (a + i, a + i2, c)
        faces.append(f if side < 0 else f[::-1]); mats.append(1)
a, b = rings[0][0], rings[1][0]                      # 外沿侧壁
for i in range(NP):
    i2 = (i + 1) % NP
    faces.append((a + i2, a + i, b + i, b + i2)); mats.append(0)
gem = add_mesh('gem', verts, faces, 'gem')
gem.data.materials.append(bpy.data.materials['gem2'])
for p, m in zip(gem.data.polygons, mats):
    p.material_index = m

# 银包边：心形外沿外面一圈扁带（外 1.14、内 0.98，厚 ±0.1），比宝石外沿厚，正面看是一圈台阶
bv, bf = [], []
for k, t in ((1.14, 0.1), (0.98, 0.1)):
    bv += ring_pts(k, -t) + ring_pts(k, t)
O, I = 0, 2 * NP
for i in range(NP):
    i2 = (i + 1) % NP
    bf += [(O + i, O + i2, O + NP + i2, O + NP + i),            # 外壁
           (I + i2, I + i, I + NP + i, I + NP + i2),            # 内壁
           (O + i2, O + i, I + i, I + i2),                      # 正面（−Y）
           (O + NP + i, O + NP + i2, I + NP + i2, I + NP + i)]  # 背面
add_mesh('bezel', bv, bf, 'silver')

# 小白钻：沿心形外面一圈，9 颗八面体（心尖、心窝各留空）
ND, DR = 9, 0.1
for j in range(ND):
    t = 2 * math.pi * (j + 0.5) / ND
    if abs(t - math.pi) < 0.25: t += 0.3              # 心尖那一颗往旁边挪
    x, z = heart(t)
    cx, cz = x * SC * 1.3, z * SC * 1.3
    v = [(cx + DR, 0, cz), (cx - DR, 0, cz), (cx, 0, cz + DR), (cx, 0, cz - DR), (cx, -DR * 0.8, cz), (cx, DR * 0.8, cz)]
    f = [(4, 0, 2), (4, 2, 1), (4, 1, 3), (4, 3, 0), (5, 2, 0), (5, 1, 2), (5, 3, 1), (5, 0, 3)]
    add_mesh('dia', v, f, 'diamond')

# 挂环（心窝上方）+ 7 颗大银珠排成 V 字
TOP = heart(0)[1] * SC * 1.14
prim('torus', 'silver', major_radius=0.12, minor_radius=0.045, location=(0, 0, TOP + 0.14), rotation=(math.pi / 2, 0, 0))
for j in range(1, 4):
    for s in (-1, 1):
        prim('uv_sphere', 'silver', segments=12, ring_count=8, radius=0.075, location=(s * 0.15 * j, 0, TOP + 0.24 + 0.16 * j))
prim('uv_sphere', 'silver', segments=12, ring_count=8, radius=0.075, location=(0, 0, TOP + 0.3))

ob = join_all(gem)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')      # 手拼的网格面朝向不一定一致：Toon 明暗靠法线，统一朝外
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
render_turntable('necklace', active=ob, lean=25, tilt=0.3, roll=0.2, screen_r=26)
