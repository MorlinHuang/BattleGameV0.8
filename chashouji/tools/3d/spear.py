"""红缨枪（档 3 三人组 G18 穆桂英式挂帅女将，甩出红缨枪旋转飞过去，命中时红缨炸开成一朵红花，2026-09-30）。

## 形体

- 长枪杆（棕红）+ 银色菱形枪头（带中脊的厚片：正反两面各两个斜面，八面体）+ 枪头下一道金属箍
  + 箍下一簇红缨（10 根独立的粗锥形缨穗，从箍下往外往下散开）+ 杆尾金属镦（圆柱 + 尖锥）。
- **红缨是这件的主要内部结构**：7 根缨穗各是一块真几何，转起来互相遮挡一直在变。
  枪杆本身是一根线（剥外轮廓后什么都不剩），内部描边只能来自红缨和枪头的中脊。
- （首版）r 40 → 1 单位 = 40 屏幕 px，g ≥ 2W ≈ 0.14 单位。**第一版杆半径 0.05、枪头宽 0.34、10 根缨穗根部 0.065**：
  杆在屏幕上 4px 宽、缨穗 5px 粗，整件 12/12 帧是墨块（非描边色不到实心的 15%），描边读成 6.9px。
  现在杆 0.075、枪头宽 0.5 长 0.55、缨穗 7 根根部 0.1 长 0.5：每一块都自己占得住几个像素的填色。
- 长轴竖着（Z），转轴 lean 45：长轴始终垂直于转轴，屏幕长度最短 cos45 ≈ 0.7；枪头是扁片（有正面），
  2×lean = 90° 的偏转让它一半帧看到菱形宽面、一半帧看到中脊侧面。

## 返工（2026-10-01，审查第五批 G18）

审查：屏幕长边 59~85px（中位 74），她身高 290px，飞出去读成一支小飞镖。要求屏幕长 ≥ 150px、长轴屏幕上 ≥ 0.76 倍长，r 和描边按新长度重算。
- r 40 → 95（整根 2 单位 = 190px），screen_r 跟着改（描边按新 r 算，屏幕上仍是 ~3px），不是只放大 scale。
- 长轴改横放（X）+ lean −75（同拐杖 / 哑铃，规范 7.4 第 2 条）：长轴绕转轴扫一个小圆锥、最多点头 30°，永远不会转到正对镜头缩成一团；
  枪头扁片的宽面 / 中脊侧面靠绕长轴的滚（roll）轮流出来。首版 lean 45 长轴竖着：一半帧长轴斜向纵深，短到 0.7。

跑：blender -b --python spear.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector
import bpy

init()
mat('shaft', '#9a4a32')
mat('steel', '#dfe5ec')
mat('brass', '#d8b04a')
mat('tassel', '#e8262e')


def bar(p0, p1, r0, r1, m, n=10):
    """圆锥/圆柱，从 p0 到 p1（r0 在 p0 端）。rotation 必须 apply，不然 join 后整件继承 QUATERNION 模式，转盘失效"""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    ob = prim('cone', m, vertices=n, radius1=r0, radius2=r1, depth=d.length, location=tuple((p0 + p1) / 2))
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bpy.ops.object.transform_apply(rotation=True)
    ob.rotation_mode = 'XYZ'
    return ob


# 枪杆
bar((0, 0, -0.9), (0, 0, 0.5), 0.075, 0.07, 'shaft')
# 枪头：带中脊的菱形厚片（八面体），宽面朝镜头
T0, T1, TW, TM, TD = 0.47, 1.0, 0.25, 0.64, 0.08
v = [(0, 0, T1), (0, 0, T0), (TW, 0, TM), (-TW, 0, TM), (0, -TD, TM), (0, TD, TM)]
f = [(0, 4, 2), (0, 3, 4), (0, 2, 5), (0, 5, 3), (1, 2, 4), (1, 4, 3), (1, 5, 2), (1, 3, 5)]
add_mesh('head', v, f, 'steel')
# 枪头与杆之间一截短颈 + 金属箍
bar((0, 0, 0.4), (0, 0, 0.5), 0.075, 0.05, 'steel')
bar((0, 0, 0.3), (0, 0, 0.42), 0.12, 0.12, 'brass', 14)
# 红缨：10 根粗锥从箍下散开，交替两种长度/张角
N = 7
for i in range(N):
    a = 2 * math.pi * (i + 0.25 * (i % 2)) / N
    L = 0.55 if i % 2 == 0 else 0.45
    sp = math.radians(34 if i % 2 == 0 else 22)
    d = Vector((math.cos(a) * math.sin(sp), math.sin(a) * math.sin(sp), -math.cos(sp)))
    root = Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.31))
    bar(root, root + d * L, 0.1, 0.02, 'tassel', 8)
# 杆尾镦：金属圆柱 + 尖锥
bar((0, 0, -0.82), (0, 0, -0.93), 0.1, 0.1, 'brass', 14)
bar((0, 0, -0.93), (0, 0, -1.0), 0.1, 0.03, 'brass', 14)

# 长轴横放：join 之前全选 apply 旋转（规范 7.4 第 3 条）
for o in bpy.context.scene.objects:
    if o.type == 'MESH': o.select_set(True)
bpy.context.view_layer.objects.active = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
bpy.ops.transform.rotate(value=-math.pi / 2, orient_axis='Y', center_override=(0, 0, 0))   # 枪头朝屏幕右（她往右扔，枪头一路朝前）
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
ob = join_all()
render_turntable('spear', active=ob, lean=-75, tilt=0.0, roll=0.35, screen_r=95)
