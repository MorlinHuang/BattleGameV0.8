"""心形蓝宝石项链（档 3 三人组 G15 船头红发少女，泰坦尼克 Rose 式，把"海洋之心"扔出去砸男生，2026-09-30）。

## 形体

- "海洋之心"：一颗厚的心形蓝宝石（正反两面各两圈台阶收到顶面，刻面宝石的样子）+ 外面一圈银色包边（独立的扁环）
  + 顶上一个挂环 + **一圈大珍珠链**（4 颗米白大珠串在一根银链上，从挂环往上绕成一个环）。
- **审查第三轮 6.7 返工**：首版心形外面贴着包边排了 9 颗小白钻（八面体、屏幕 ~5px），每颗一圈描边、跟包边的描边并在一起，
  外轮廓读成一圈黑疙瘩（屏幕描边 8.3px，24 件里最粗），心形像带刺的水雷；链子是 7 颗小银珠，缩到 57px 看不见。
  改法：**小白钻去掉**（贴着外沿放多少颗都会并进外轮廓：钻与包边的缝要 ≥ 2W = 0.22 单位，整件就放不下心形了），
  心形放大（半宽 0.55 → 0.62）、银包边加宽到 0.2 单位；链子换成 4 颗大珍珠（直径 0.38 单位 ≈ 11px），浅色、跟蓝心拉开。
- 体积感来自包边、挂环和一颗颗独立的珍珠：转起来珠子之间、珠子和心形的遮挡一直在变。
  宝石本身的刻面不产生描边（skill 坑 2），只管"认得出"。
- 有正面，**lean −20**：正面最多偏 40°；取负、起始略往上抬是为了让正面一直在灯这一侧（sun 从镜头这侧右上方打，Toon 离光 ~65° 以外整面落暗，
  见 cassette.py）：36 帧里心形正面离光最多 58°。
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
mat('pearl', '#f4ecdc')      # 米白大珍珠

SC = 0.62                     # 心形半宽（单位）；整件竖着 ~2.0 = NOMINAL（心 + 挂环 + 珠链）
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
LAY = [(1.0, 0.15), (0.72, 0.19), (0.45, 0.22)]      # 外沿跟包边内沿同高：两块面接平，包边内沿不出剪影线
verts, faces, mats = [], [], []
rings = []
for side in (-1, 1):
    rs = []
    for k, t in LAY:
        o = len(verts); verts += ring_pts(k, side * t); rs.append(o)
    c = len(verts); verts.append((0, side * 0.22, 0.0)); rs.append(c)
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

# 银包边：心形外沿外面一圈扁带（外 1.3 厚 ±0.11 → 内 0.98 厚 ±0.15，往里拱），内沿跟宝石外沿同高、正面接平。
# 包边比宝石外沿厚一截的话，包边内壁在正面是一道剪影线：0.2 单位宽的银边两边各一道描边，屏幕上只剩 1px 银色（快测）
# 外 1.14 时带宽 0.1 单位（屏幕 3px），整条被描边吃掉，心形外面是一道粗黑框（快测）；放到 0.2 单位，银色露得出来
bv, bf = [], []
for k, t in ((1.3, 0.11), (0.98, 0.15)):
    bv += ring_pts(k, -t) + ring_pts(k, t)
O, I = 0, 2 * NP
for i in range(NP):
    i2 = (i + 1) % NP
    bf += [(O + i, O + i2, O + NP + i2, O + NP + i),            # 外壁
           (I + i2, I + i, I + NP + i, I + NP + i2),            # 内壁
           (O + i2, O + i, I + i, I + i2),                      # 正面（−Y）
           (O + NP + i, O + NP + i2, I + NP + i2, I + NP + i)]  # 背面
add_mesh('bezel', bv, bf, 'silver')

# 挂环（心窝上方）+ 珍珠链：一根银链绕成环（细圆环，屏幕上就是一道线），6 颗大珠串在上面，最下面挂环那一段空着
TOP = heart(0)[1] * SC * 1.3
prim('torus', 'silver', major_radius=0.12, minor_radius=0.05, location=(0, 0, TOP + 0.12), rotation=(math.pi / 2, 0, 0))
CR, CZ, PR = 0.52, TOP + 0.24 + 0.52, 0.19       # 链环半径、圆心高、珍珠半径
prim('torus', 'silver', major_radius=CR, minor_radius=0.035, location=(0, 0, CZ), rotation=(math.pi / 2, 0, 0))
for j in range(4):
    a = math.radians(j * 60)                     # 0° / 60° / 120° / 180°：珠距 0.52，缝 0.14 单位（6 颗那一版缝 0.11，珠子并成一串黑圈，快测）
    prim('uv_sphere', 'pearl', segments=16, ring_count=10, radius=PR, location=(CR * math.cos(a), 0, CZ + CR * math.sin(a)))

bpy.ops.object.select_all(action='SELECT')           # 旋转烤进网格，join 后姿态确定（理由见 dumbbell.py）
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
ob = join_all(gem)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')      # 手拼的网格面朝向不一定一致：Toon 明暗靠法线，统一朝外
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
render_turntable('necklace', active=ob, lean=-20, tilt=-0.1, roll=0.2, screen_r=26)
