"""双肩书包（档 3 三人组 G27 杉菜式暴脾气平民女孩，抡书包砸过去，2026-09-30）。

## 形体

- 包身（藏青）+ 盖在上半截的翻盖（酒红，比包身外扩一圈、往前悬挑，真厚度）+ 下半截一个前兜（独立凸块）
  + 翻盖下沿两个浅灰扣子 + 前兜拉链头 + 两侧水壶侧袋 + 顶上一个提手环 + 背面两条肩带（凸起的带子，整条贴着包背）。
- **每块都是单独的几何**：翻盖的前沿和侧沿、前兜的一圈、扣子、提手、肩带各自一圈轮廓，
  转起来互相遮挡（翻盖挡住包身上沿、前兜挡住下半截）—— 这就是体积感。
  翻盖要是用材质分区画在包身上，就是一块会转的双色砖头（skill 坑 4b）。
- 零件间距按 g ≥ 2W：r 30 → 1 单位 ≈ 32 屏幕 px，2W = 5.6px ≈ 0.18 单位；
  翻盖下沿到前兜上沿留 0.3、扣子宽 0.2，都占得住。
- 肩带贴着包背做成凸起的带子，**不留空**：肩带和包背之间留缝的话是一个封闭的口袋，只有一盏灯，里面渲成纯黑（skill 坑 7）。
- 配色学生气，都不用近黑色（黑包跟描边贴死，60px 上是一块黑砖，磁带第一版的教训）。
- 有正面（翻盖那一面），lean 45：正面最多偏 90°，一半帧看得到翻盖和前兜、一半帧看到侧面厚度和背后的肩带。
- 屏幕上半径 30（G27 atk.r 按这个填）。

跑：blender -b --python schoolbag.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

init()
mat('body', '#34508c')        # 藏青包身
mat('flap', '#c0364e')        # 酒红翻盖（识别色）
mat('pocket', '#4a68a8')      # 前兜亮一档
mat('buckle', '#d9dde3')
mat('strap', '#2a3f70')

W, D, H = 1.4, 0.6, 1.9       # 宽、厚、高（高 ≈ NOMINAL）；相机沿 +Y 看，正面朝 −Y


def box(m, cx, cy, cz, sx, sy, sz, bevel=0.0):
    ob = prim('cube', m, size=1, location=(cx, cy, cz), scale=(sx, sy, sz))
    bpy.ops.object.transform_apply(scale=True)
    if bevel:                                    # 倒一点角：包是软的，四个直角的铁盒读起来不像包
        bv = ob.modifiers.new('bv', 'BEVEL'); bv.width = bevel; bv.segments = 2
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier='bv')
    return ob


body = box('body', 0, 0, 0, W, D, H, 0.12)
# 翻盖：盖住上沿和前面上半截，外扩 0.05、厚 0.08（顶上一块 + 前面一块，拼成一个 L）
box('flap', 0, -0.02, H / 2 + 0.02, W + 0.1, D + 0.1, 0.1, 0.03)
box('flap', 0, -D / 2 - 0.05, H / 2 - 0.4, W + 0.1, 0.1, 0.84, 0.03)
# 扣子：翻盖下沿两个
for x in (-0.38, 0.38):
    box('buckle', x, -D / 2 - 0.12, H / 2 - 0.78, 0.22, 0.06, 0.16)
# 前兜：下半截一个凸块，上沿离翻盖下沿 0.3
box('pocket', 0, -D / 2 - 0.1, -H / 2 + 0.42, W * 0.72, 0.24, 0.62, 0.06)
# 两侧各一个水壶侧袋（凸块）：侧面转过来时也有结构（第一版只有前面有东西，结构密度 20%，卡在线上）
for x in (-1, 1):
    box('pocket', x * (W / 2 + 0.07), 0, -H / 2 + 0.38, 0.16, D * 0.7, 0.55, 0.04)
# 前兜上一条浅灰拉链头
box('buckle', 0.22, -D / 2 - 0.24, -H / 2 + 0.66, 0.2, 0.05, 0.1)
# 提手：顶上一个半环
prim('torus', 'strap', major_radius=0.22, minor_radius=0.05, location=(0, 0, H / 2 + 0.08), rotation=(math.pi / 2, 0, 0))
# 肩带：背面两条凸起的带子，整条贴着包背（不留空，免得夹出纯黑口袋）
for x in (-0.35, 0.35):
    box('strap', x, D / 2 + 0.06, -0.05, 0.2, 0.14, H * 0.8, 0.03)

ob = join_all(body)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')      # 手拼的网格面朝向不一定一致：Toon 明暗靠法线，统一朝外
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
render_turntable('schoolbag', active=ob, lean=45, tilt=0.3, roll=0.2, screen_r=30)
