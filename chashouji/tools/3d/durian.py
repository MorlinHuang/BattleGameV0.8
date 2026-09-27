"""榴莲（档 2，查岗党，榴莲鞋雨里重的那几下，2026-09-27）—— 一颗长满锥刺的榴莲，从男生头顶掉下来砸他。
用户要"参考口红、香蕉做成有体积感的"：之前是生图平面贴纸在画面里打转。

## 形体

- **刺是真几何**：每根刺一个锥体，底座扎进果身（带直裙边，不贴面放 —— 贴着放两个面在接触圈几乎相切，
  Freestyle 长一圈乱跳的黑睫毛）。转起来前后刺互相遮挡、正对镜头的刺描成一个个圆，这就是体积感的来源
  （主尺是内部结构密度，外轮廓变化撑不起来）。
- **刺短、粗、密**：第一版 38 根长尖刺（高 0.34）剪影是一颗黄色的星星 / 病毒球，认不出榴莲。
  现在 64 根（斐波那契球面均布）、底座半径 0.13、露出 0.19 —— 果身是一颗球、表面一层密刺。
  间距按描边算：屏幕直径约 120px、描边 2.8px，底座间距 ~13px > 2 条描边宽，刺根不连成黑带。
- 颜色偏橄榄（第一版亮黄绿读成网球 / 毛球）。
- 果身略扁（z 0.93），刺尖两色：果身深一档黄绿、刺亮一档，暗面也分得清刺和身子；顶上一截短果柄。
- 各向同性、没有正面：lean 90（翻跟头，体积感最足）。

跑：blender -b --python durian.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy

R_BODY = 0.74      # 果身半径
SQUASH = 0.93      # 果身 z 向压扁
N = 64             # 刺数
R_SPIKE, H_SPIKE, SINK = 0.13, 0.19, 0.06   # 刺底座半径、露在外面的高、扎进果身多深

init()
mat('body', '#7f9632')
mat('spike', '#a9bb44')
mat('stem', '#6b4a2a')
bpy.context.scene.view_settings.view_transform = 'Standard'   # 同香蕉：AgX 把黄绿压成土绿

prim('uv_sphere', 'body', segments=32, ring_count=16, radius=R_BODY, scale=(1, 1, SQUASH))
ga = math.pi * (3 - math.sqrt(5))
for i in range(N):
    z = 1 - 2 * (i + 0.5) / N
    r = math.sqrt(1 - z * z)
    n = Vector((r * math.cos(ga * i), r * math.sin(ga * i), z))
    if n.z > 0.93:            # 顶上留给果柄
        continue
    surf = Vector((n.x * R_BODY, n.y * R_BODY, n.z * R_BODY * SQUASH))
    depth = H_SPIKE + SINK
    c = surf + n * (depth / 2 - SINK)
    rot = n.to_track_quat('Z', 'Y').to_euler()
    prim('cone', 'spike', vertices=8, radius1=R_SPIKE, radius2=0.0, depth=depth, location=tuple(c), rotation=tuple(rot))
prim('cylinder', 'stem', vertices=8, radius=0.07, depth=0.34,
     location=(0.03, 0, R_BODY * SQUASH + 0.1), rotation=(0, 0.25, 0))

ob = join_all()
lo = [1e9] * 3; hi = [-1e9] * 3
for v in ob.data.vertices:
    for k in range(3):
        lo[k], hi[k] = min(lo[k], v.co[k]), max(hi[k], v.co[k])
mid = Vector([(lo[k] + hi[k]) / 2 for k in range(3)])
s = NOMINAL / max(hi[k] - lo[k] for k in range(3))
ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation(-mid)

render_turntable('durian', active=ob, lean=90, tilt=0.3, roll=0.2, screen_r=52)
