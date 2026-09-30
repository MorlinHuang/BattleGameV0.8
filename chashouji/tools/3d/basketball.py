"""篮球（档 3 三人组，樱木趴在地上甩出去砸女生，2026-09-29）—— 三人组 3D 道具的样板（docs/三人组角色规范.md 第七节）。

## 形体

- 标准篮球 8 块皮：两条互相垂直的大圆缝（x = 0、z = 0）+ 两条绕 ±y 极的弯缝。
- **每块皮做成单独的一块厚片**（同足球）：缝那一圈的面删掉，剩下的按连通块各自往里挤出一段，缝底下是一颗深褐内球。
  这样每块皮都有自己的一圈轮廓 —— 转起来缝线的遮挡、透视缩短一直在变，读得出是一个在滚的球；
  缝用材质分区画的话不产生描边（skill 坑 4b），就是一个画了黑线的橙色圆片。
- 各向同性：lean 90。屏幕上直径 ~68px（trio.js Sakura atk.r 34），缝宽按 skill 坑 4 的 g ≥ 2W 留：
  缝本身就该是一条黑线，所以反过来用 g < 2W：缝窄到两边皮的描边正好并成一条（SEAM 0.022）。
  第一版 SEAM 0.07：缝 + 两条描边在 68px 上是 10px 的黑带，球读成一个黑十字。
- 删面留下的缝边是二十面体的台阶（锯齿缝），删完把缝边顶点沿梯度投影回精确的等距线上（proj）。

跑：blender -b --python basketball.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy, bmesh

R = 1.0
SEAM = 0.022       # 缝的半宽（球面上到缝中心线的距离，占半径）：窄到两边皮的描边并成一条 ~4px 的黑缝线（真篮球就是细黑线）
THICK = 0.1        # 皮的厚度（往球心挤）
LAT = 0.62         # 弯缝离 ±y 极的"纬度"（|y| 的基准值）
WARP = 0.3         # 弯缝的扭：|y| = LAT + WARP × (z² − x²) —— 在 x 大圆那边往极点缩、z 大圆那边往赤道张，是篮球那条马鞍形缝

init()
mat('skin', '#e8742a')
mat('core', '#3b2418')


def seam_dist(p):
    x, y, z = p
    return min(abs(x), abs(z), abs(abs(y) - (LAT + WARP * (z * z - x * x))))


bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=6, radius=R)
kill = [f for f in bm.faces if seam_dist(f.calc_center_median()) < SEAM]
bmesh.ops.delete(bm, geom=kill, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')


def proj(co):
    """把缝边顶点挪到 seam_dist = SEAM 上（数值梯度走几步，每步拉回球面）"""
    p = Vector(co)
    for _ in range(8):
        f = seam_dist(p) - SEAM
        g = Vector([(seam_dist(p + Vector(d) * 1e-4) - seam_dist(p - Vector(d) * 1e-4)) / 2e-4 for d in ((1, 0, 0), (0, 1, 0), (0, 0, 1))])
        if g.length_squared < 0.25: break          # 缝交叉点附近 min() 的梯度退化，不挪（那里本来就是缝的拐角）
        step = g * (f / g.length_squared)
        if step.length > 0.03: step *= 0.03 / step.length   # 限步长：一步最多挪半个面宽
        p = (p - step).normalized() * R
    return p


for v in bm.verts:
    if any(e.is_boundary for e in v.link_edges): v.co = proj(v.co)
bmesh.ops.dissolve_degenerate(bm, dist=1e-3, edges=bm.edges)   # 投影把缝边的一些面压成细条，留着会让 Solidify 挤出尖刺
me = bpy.data.meshes.new('skin'); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new('skin', me); bpy.context.scene.collection.objects.link(ob)
ob.data.materials.append(bpy.data.materials['skin'])
for p in ob.data.polygons: p.use_smooth = False
sol = ob.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = THICK; sol.offset = -1.0; sol.use_even_offset = False   # even_offset 在细长面上按 1/sin 放大厚度，挤出一根根尖刺
bpy.context.view_layer.objects.active = ob
bpy.ops.object.modifier_apply(modifier='sol')
print('PANELS faces', len(ob.data.polygons), flush=True)

prim('ico_sphere', 'core', subdivisions=4, radius=R - THICK * 0.6)

ob = join_all(ob)
s = NOMINAL / (2 * R)
ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0))
render_turntable('basketball', active=ob, lean=90, tilt=0.35, roll=0.25, screen_r=34)
