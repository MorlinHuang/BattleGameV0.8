"""西瓜（档 3 三人组 B28 猪八戒，把一整颗西瓜扔出去砸女生、砸中红瓤带籽溅开，2026-09-30）。

## 形体

- 一颗略长的椭圆西瓜：浅绿瓜皮主体 + 从瓜蒂到瓜脐的 STRIPES 条深绿锯齿条纹 + 顶上一截卷曲瓜蒂。
- **条纹是凸起的独立条带**（同篮球的分片）：一层略大的椭球壳只留条纹那部分面、往里挤出厚度，
  条带边缘自己一圈轮廓 —— 转起来一条条深绿带的遮挡、透视缩短一直在变，读得出是一颗在滚的瓜。
  条纹用材质分区画的话不产生描边（skill 坑 4b），就是一个画了花纹的绿蛋。
- 锯齿：条带半宽按高度走三角波，真西瓜那种毛边条纹。
- 条纹间距按 g ≥ 2W：屏幕 1 单位 ≈ 32px，赤道一圈 8 条，条宽 ~0.3、间隔 ~0.35 单位（各 10px 左右）。
- 长轴竖放、lean 90：绕屏幕横轴翻，长轴在画面上始终竖着，不会横过来。

跑：blender -b --python watermelon.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy, bmesh

A, B = 1.0, 0.84      # 长半轴（z）、短半轴
STRIPES = 8
HW = 0.13             # 条纹角半宽（弧度 × 半径，赤道处）
ZIG = 0.06            # 锯齿振幅
ZF = 7.0              # 锯齿频率（沿 z）
THICK = 0.06          # 条带凸起高度

init()
mat('rind', '#9ad060')
mat('stripe', '#2e7a2a')
mat('stem', '#7a8a3a')


def tri(x):
    x = x - math.floor(x)
    return 4 * abs(x - 0.5) - 1          # -1..1 三角波


def in_stripe(p):
    x, y, z = p
    zn = z / A
    if abs(zn) > 0.93:                     # 两极留一小片浅绿（瓜蒂/瓜脐）
        return False
    a = math.atan2(y, x)
    k = STRIPES * a / (2 * math.pi)
    da = abs(k - round(k)) * 2 * math.pi / STRIPES      # 离最近一条中心线的角距
    rr = math.sqrt(max(1e-6, 1 - zn * zn))                # 该纬度的相对半径
    w = (HW + ZIG * tri(zn * ZF + round(k) * 0.37)) / B / max(rr, 0.35)
    w *= min(1.0, rr / 0.5) ** 0.5                         # 往两极收窄
    return da < w


body = prim('uv_sphere', 'rind', segments=40, ring_count=24, radius=1.0)
for v in body.data.vertices:
    v.co = Vector((v.co.x * B, v.co.y * B, v.co.z * A))      # 直接改顶点：设 obj.scale 的话 join_all 后被 matrix_world 覆盖掉

bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=6, radius=1.0)
for v in bm.verts:
    v.co = Vector((v.co.x * (B + THICK * 0.5), v.co.y * (B + THICK * 0.5), v.co.z * (A + THICK * 0.5)))
kill = [f for f in bm.faces if not in_stripe(f.calc_center_median())]
bmesh.ops.delete(bm, geom=kill, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
me = bpy.data.meshes.new('stripes'); bm.to_mesh(me); bm.free()
st = bpy.data.objects.new('stripes', me); bpy.context.scene.collection.objects.link(st)
st.data.materials.append(bpy.data.materials['stripe'])
for p in st.data.polygons: p.use_smooth = False
sol = st.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = THICK * 1.6; sol.offset = -1.0; sol.use_even_offset = False
bpy.context.view_layer.objects.active = st
bpy.ops.object.modifier_apply(modifier='sol')


def tube(name, pts, radii, matname, n=8):
    """沿折线扫一个圆截面的管子，两头封口"""
    vs, fs = [], []
    up = Vector((1, 0, 0))
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        s = t.cross(up)
        if s.length < 1e-3: s = t.cross(Vector((0, 1, 0)))
        s.normalize(); u = s.cross(t)
        for j in range(n):
            a = 2 * math.pi * j / n
            vs.append(tuple(p + (s * math.cos(a) + u * math.sin(a)) * radii[i]))
    m = len(pts)
    for i in range(m - 1):
        for j in range(n):
            fs.append((i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j))
    fs.append(tuple(range(n))[::-1]); fs.append(tuple((m - 1) * n + j for j in range(n)))
    return add_mesh(name, vs, fs, matname)


# 瓜蒂：从顶上插进去，先往上再卷一圈
pts, rad = [], []
for i in range(12):
    t = i / 11
    if t < 0.4:
        p = Vector((0.0, 0, A - 0.12 + t / 0.4 * 0.3))
    else:
        a = (t - 0.4) / 0.6 * math.pi * 1.3
        p = Vector((0.16 - 0.16 * math.cos(a), 0.0, A + 0.18 + 0.16 * math.sin(a)))
    pts.append(p); rad.append(0.075 * (1 - 0.45 * t))
tube('stem', pts, rad, 'stem')

ob = join_all(body)
s = NOMINAL / (2 * (A + 0.1))
ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0))
render_turntable('watermelon', active=ob, lean=90, tilt=0.35, roll=0.3, screen_r=30)
