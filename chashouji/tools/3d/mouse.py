"""有线鼠标（档 3 三人组 B26 电竞宅男，把鼠标攥着线当流星锤甩出去砸女生，2026-09-30）。

## 形体

- 电竞鼠标：一个前窄后宽、背上拱起的壳（缩放的球 + 顶点按长轴收窄）+ 两片独立的按键 + 一个红色大滚轮 + 壳底一圈青色 RGB 灯带
  + 屁股上一截线头。线本身由引擎画（atk.tether），这里只留线头。
- **按键是认鼠标的关键**：第一版没做按键（怕 36px 上叠黑），渲出来是一颗带蓝边的灰蛋，结构密度 16%。
  现在做法同篮球：壳顶前半截的面按"左键 / 右键 / 中缝"切开，两片键各自往外挤一层厚度（键比壳高一个台阶，
  前沿和后沿各一圈轮廓），中缝放宽到 0.24、缝底下是一颗深灰内芯，红滚轮嵌在缝里拱出来（顶面朝镜头时滚轮要宽到 ~7px 才不被描边吃光）。
- 壳用浅灰（#d9dde3）：黑壳跟描边色贴在一起，36px 上是一块黑砖（磁带第一版的教训）。
- 零件不能碎：屏幕上 r 22（web/trio_buddy.js B26 atk.r），长 44px，1 单位 ≈ 22px：r 18 时灯带、滚轮都被描边吃掉，只剩一颗灰蛋（快测）。
  灯带粗 0.32 单位（~7px）、整圈露出壳外。
- 有正面（按键朝上那一面）。**审查第三轮 6.7 返工**：lean 50 / tilt 0.3 那一版起始是侧面、转半圈正面偏 100°，
  只有 0° 认得出，90° 像带斜线的球、180° 像碗、270° 底面朝镜头成了一片扁椭圆。改成 **起始按键面朝镜头（tilt 1.1，
  顶面往镜头倒 63°）+ lean −20**：顶面离视线 2~44°，36 帧都看得到按键中缝和红滚轮 —— 就是"鼠标"那个图标的样子，
  底面永远转不到前面；lean 取负、起始往光那边偏，是为了让顶面一直在灯这一侧（见 cassette.py 的姿态注释）。
- 前端线头加长加粗（半径 0.085、长 0.46，往下弯一点）：引擎的 tether 从手拉到鼠标中心，线头从鼠标前沿伸出来，
  两段接起来读成一根线。

跑：blender -b --python mouse.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy, bmesh

init()
mat('shell', '#d9dde3')
mat('btn', '#eef0f3')
mat('core', '#4a4e58')
mat('wheel', '#e0403a')
mat('rgb', '#35d6f0')
mat('cable', '#3a3f48')

L, W, H = 1.0, 0.6, 0.55          # 半长（NOMINAL 方向）、半宽、半高；长轴 = X，前端朝 −X
SEAM = 0.12                       # 中缝半宽（占 W 的单位）：滚轮嵌在里面，要容得下滚轮的宽度
BTN_X = 0.12                      # 按键后沿（x < BTN_X 的壳顶是按键）
BTN_Z = 0.12                      # 按键下沿（z > BTN_Z）
LIFT = 0.05                       # 按键比壳高多少（台阶）


def shape(co):
    """单位球 → 鼠标壳：缩放、前窄后宽、底面压平"""
    x, y, z = co.x * L, co.y * W, co.z * H
    y *= 1 - 0.22 * (-x / L)
    if z < -0.25: z = -0.25 - (z + 0.25) * 0.15
    return x, y, z


bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=1)
for v in bm.verts: v.co = shape(v.co)
parts = {'body': [], 'L': [], 'R': []}
for f in bm.faces:
    c = f.calc_center_median()
    if c.x < BTN_X and c.z > BTN_Z:
        if c.y > SEAM: parts['L'].append(f)
        elif c.y < -SEAM: parts['R'].append(f)
        # 中缝的面删掉（露出内芯）
    else:
        parts['body'].append(f)


def sub(faces, name, m, lift=0.0):
    """把一组面拷成独立网格；lift > 0 时沿法向挤出一层厚度（按键台阶）"""
    b2 = bmesh.new()
    vm = {}
    for f in faces:
        vs = []
        for v in f.verts:
            if v not in vm: vm[v] = b2.verts.new(v.co)
            vs.append(vm[v])
        b2.faces.new(vs)
    me = bpy.data.meshes.new(name); b2.to_mesh(me); b2.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(bpy.data.materials[m])
    for p in ob.data.polygons: p.use_smooth = False
    if lift:
        sol = ob.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = lift; sol.offset = 1.0
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier='sol')
    return ob


body = sub(parts['body'], 'body', 'shell')
sub(parts['L'], 'btnL', 'btn', LIFT)
sub(parts['R'], 'btnR', 'btn', LIFT)
bm.free()
core = prim('uv_sphere', 'core', segments=24, ring_count=12, radius=1)
for v in core.data.vertices:
    x, y, z = shape(v.co); v.co = (x * 0.94, y * 0.94, z * 0.94)
# 滚轮：嵌在中缝里，从两片键中间拱出来
prim('cylinder', 'wheel', vertices=20, radius=0.24, depth=0.24, location=(-0.42, 0, 0.45), rotation=(math.pi / 2, 0, 0))
# 滚轮宽 0.24（屏幕 ~7px）、顶比按键高 0.14。上一版宽 0.12、嵌在 0.07 宽的缝里：顶面朝镜头时是一个 3px 宽的条，
# 两边描边一夹全是墨，36 帧里一个红像素都没有（快测）。中缝跟着放宽到 0.24
# RGB 灯带：底边一圈扁环
ring = prim('torus', 'rgb', major_radius=1, minor_radius=0.16, location=(0.02, 0, -0.2))   # primitive_torus_add 不收 scale
ring.scale = (L * 0.99, W * 1.0, 1)                 # 比壳那一圈略大，灯带整圈露在外面
prim('cylinder', 'cable', vertices=12, radius=0.085, depth=0.3, location=(-L - 0.08, 0, 0.0), rotation=(0, math.pi / 2, 0))
prim('cylinder', 'cable', vertices=12, radius=0.085, depth=0.22, location=(-L - 0.27, 0, -0.06), rotation=(0, math.pi / 2 - 0.5, 0))   # 线头往下弯一截

bpy.ops.object.select_all(action='SELECT')           # 旋转烤进网格，join 后姿态确定（理由见 dumbbell.py）
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

ob = join_all(body)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')      # 手拼的网格面朝向不一定一致：Toon 明暗靠法线，统一朝外
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
render_turntable('mouse', active=ob, lean=-20, tilt=1.1, roll=0.5, screen_r=22)
