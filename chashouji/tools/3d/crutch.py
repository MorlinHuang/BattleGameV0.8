"""腋下拐（档 3 三人组 B29 东北卖拐大叔，甩拐杖飞过去砸女生，2026-09-30）。

## 形体

- 木制腋下拐：两根并行的侧杆（上宽下窄，往下收拢到一个木接头）→ 接头下一根单杆 → 底端深灰橡胶脚套；
  顶部一块横向弧形腋托（两头上翘、比侧杆外扩），中段一根手握横档，杆上两道金属箍。
- **每个零件都是单独的一块真几何**（腋托垫 + 托座、横档、接头块、两道箍、脚套各自一圈描边）：
  细长件剥掉外轮廓后里面几乎不剩面积，内部结构只能靠沿长轴排开的这些独立零件 + 两根侧杆之间的开口。
- 屏幕上 r 34 → 整根长 68px，1 单位 = 34 屏幕 px，描边 2.8px ≈ 0.08 单位，g ≥ 2W ≈ 0.17 单位。
  所以零件都做胖：侧杆间开口最窄处也留 0.2 以上，腋托、接头、脚套做成 ≥ 0.25 单位的块，才剥得出内部面积。
- 长轴竖着（Z）。转轴 lean 45：长轴始终垂直于转轴，屏幕长度最短也有 cos45 ≈ 0.7，不会塌成一个点；
  两根侧杆张开的那个面最多偏 90°，一半帧看得到开口、一半帧看得到侧杆叠成一根的侧面。

跑：blender -b --python crutch.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector
import bpy

init()
mat('wood', '#e3a764')
mat('pad', '#c9b89c')
mat('metal', '#c9d0d8')
mat('rubber', '#5e5a66')


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
XT, XJ = 0.36, 0.17               # 侧杆中心线：顶端 ±XT，接头处 ±XJ
RR = 0.09                         # 侧杆半径
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

curved_block('pad', 0.92, 0.24, 0.3, TOP + 0.24, 0.08)       # 软垫：比托座外扩一圈
curved_block('wood', 0.76, 0.13, 0.22, TOP + 0.04, 0.06)       # 木托座

# 手握横档：两根侧杆之间，横档两头伸出侧杆一点点
ZG = 0.02
xg = XJ + (XT - XJ) * (ZG - JOINT) / (TOP - JOINT)
bar((-xg - 0.09, 0, ZG), (xg + 0.09, 0, ZG), 0.09, 'wood')

# 接头：两根侧杆收进一块木块，再往下是单杆
prim('cube', 'wood', size=1, location=(0, 0, JOINT), scale=(0.54, 0.22, 0.2))
bar((0, 0, JOINT), (0, 0, BOT + 0.2), 0.095, 'wood')
# 金属箍：单杆中段一道（比杆粗一圈、0.14 宽，才不被上下描边吃光）。
# 第一版接头正下方还有一道：和接头块贴着，68px 上并成一团黑疙瘩，删了
bar((0, 0, -0.60), (0, 0, -0.74), 0.13, 'metal', 16)
# 橡胶脚套：下端外扩的锥台
prim('cone', 'rubber', vertices=16, radius1=0.2, radius2=0.14, depth=0.24, location=(0, 0, BOT + 0.12))

ob = join_all()
render_turntable('crutch', active=ob, lean=45, tilt=0.25, roll=0.35, screen_r=34)
