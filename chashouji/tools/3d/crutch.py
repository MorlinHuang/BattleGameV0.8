"""腋下拐（档 3 三人组 B29 东北卖拐大叔，甩拐杖飞过去砸女生，2026-09-30）。

## 形体

- 木制腋下拐：两根并行的侧杆（上宽下窄，往下收拢到一个木接头）→ 接头下一根单杆 → 底端深灰橡胶脚套；
  顶部一块横向弧形腋托（两头上翘、比侧杆外扩），中段一根手握横档，杆上两道金属箍。
- **每个零件都是单独的一块真几何**（腋托垫 + 托座、横档、接头块、两道箍、脚套各自一圈描边）：
  细长件剥掉外轮廓后里面几乎不剩面积，内部结构只能靠沿长轴排开的这些独立零件 + 两根侧杆之间的开口。
- 屏幕上 r 86 → 整根长 ~150~185px（B29 帧里画的那根 185~205px），1 单位 = 86 屏幕 px，描边 2.8px ≈ 0.033 单位。
- 起始长轴横放（X），转轴 lean −75（离屏幕横轴 15°、往纵深偏）：长轴绕它扫一个小圆锥，最多点头 30°，
  屏幕上永远 ≥ 0.8 倍长（lean −70 / r 80 首版量出最短一帧 139px，不到 150）；两根侧杆张开 / 叠成一根靠绕长轴的滚读出来（规范 7.4 第 2 条，哑铃、松果同法）。

## 返工（2026-10-01，审查第四批 B29）

审查：wind 帧里画的拐是浅木色双杆长拐（~185px），出手那一格换成 3D 拐只有 68~79px、深褐、描边占了大半，"一截黑短棍"。
- r 34 → 86（屏幕长边 ≥ 150），描边按新 r 重算（render_turntable screen_r=80：渲染描边跟着 r 变细，屏幕上仍是 2.8px），不是只放大 scale。
- 浅木色（#e8b574，帧里那根的颜色）双侧杆、灰腋托（#9a9590）、深灰胶头（#55535a）；杆细一点（半径 0.07 = 屏幕 5.6px，
  帧里画的杆 6~7px），零件在 160px 上都比两倍描边宽，不并成黑块。
- 首版 lean 45、长轴竖着：长轴转到对着镜头时整根缩成一小段；改成长轴横放 + lean −70。

跑：blender -b --python crutch.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector
import bpy

init()
mat('wood', '#e8b574')      # 浅木色（B29 帧里画的那根）
mat('pad', '#9a9590')       # 灰腋托 / 握把套
mat('metal', '#c9d0d8')
mat('rubber', '#55535a')    # 深灰胶头


def bar(p0, p1, r, m, n=12):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    ob = prim('cylinder', m, vertices=n, radius=r, depth=d.length, location=tuple((p0 + p1) / 2))
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bpy.ops.object.transform_apply(rotation=True)   # 不 apply 的话 join 后整件继承 QUATERNION 模式，转盘设 rotation_euler 全无效（第一版 12 帧一模一样）
    ob.rotation_mode = 'XYZ'
    return ob


TOP, JOINT, BOT = 0.64, -0.34, -1.0
XT, XJ = 0.24, 0.11               # 侧杆中心线：顶端 ±XT，接头处 ±XJ（返工收窄：帧里那根长宽比 ~5）
RR = 0.07                         # 侧杆半径（r 80 下 = 屏幕 5.6px）
for s in (-1, 1):
    bar((s * XT, 0, TOP), (s * XJ, 0, JOINT + 0.05), RR, 'wood')

# 腋托：一块横向弧形软垫（两头上翘），下面一块木托座，两块各自一圈轮廓
def curved_block(m, w, h, dep, z0, bend, nx=10):
    ob = prim('cube', m, size=1)
    ob.scale = (w, dep, h)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=nx)
    bpy.ops.object.mode_set(mode='OBJECT')
    for v in ob.data.vertices:
        x = v.co.x
        v.co.z += z0 + bend * (x / (w / 2)) ** 2
        v.co.y *= 1 + 0.25 * v.co.z * 0          # 保持平
    for p in ob.data.polygons: p.use_smooth = False
    return ob

curved_block('pad', 0.66, 0.2, 0.26, TOP + 0.22, 0.06)       # 软垫：比托座外扩一圈
curved_block('wood', 0.54, 0.12, 0.2, TOP + 0.04, 0.05)       # 木托座

# 手握横档：两根侧杆之间，横档两头伸出侧杆一点点
ZG = 0.02
xg = XJ + (XT - XJ) * (ZG - JOINT) / (TOP - JOINT)
bar((-xg - 0.07, 0, ZG), (xg + 0.07, 0, ZG), 0.075, 'pad')          # 握把：灰色套

# 接头：两根侧杆收进一块木块，再往下是单杆
prim('cube', 'wood', size=1, location=(0, 0, JOINT), scale=(0.34, 0.17, 0.16))
bar((0, 0, JOINT), (0, 0, BOT + 0.2), 0.075, 'wood')
# 金属箍：单杆中段一道（比杆粗一圈、0.14 宽，才不被上下描边吃光）。
# 第一版接头正下方还有一道：和接头块贴着，68px 上并成一团黑疙瘩，删了
bar((0, 0, -0.60), (0, 0, -0.70), 0.1, 'metal', 16)
# 橡胶脚套：下端外扩的锥台
prim('cone', 'rubber', vertices=16, radius1=0.15, radius2=0.1, depth=0.22, location=(0, 0, BOT + 0.11))

# 长轴横放：join 之前全选 apply 旋转（规范 7.4 第 3 条：prim 的 rotation 是物体变换，join 后网格留在 active 那件的局部坐标里）
for o in bpy.context.scene.objects:
    if o.type == 'MESH': o.select_set(True)
bpy.context.view_layer.objects.active = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
bpy.ops.transform.rotate(value=math.pi / 2, orient_axis='Y', center_override=(0, 0, 0))
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
ob = join_all()
render_turntable('crutch', active=ob, lean=-75, tilt=0.0, roll=0.35, screen_r=86)
