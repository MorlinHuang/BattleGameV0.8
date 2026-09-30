"""磁带（档 3 三人组 B24 霹雳舞，坐地把一盘磁带像飞盘一样甩出去砸女生，2026-09-30）—— 80 年代的认人点。

## 形体

- 一盘卡式磁带：外壳分上下两片（中间一道缝）+ 正面一大块标签 + 两个白卷盘。**每块都是单独的几何**，
  转起来卷盘、标签边、壳缝各自的轮廓在变；只做一块扁盒子贴张图的话就是一张会转的卡片（skill 坑 4b）。
  零件不能碎：44px 上每块都要自己占得住几个像素，不然描边叠满整面（见下面标签处的注释）。
- 有正面（标签那一面），lean 45：正面最多偏 90°，始终认得出是磁带，又能看到厚度。
- 屏幕上半径 22（web/trio_buddy.js B24 atk.r），宽 44px。

跑：blender -b --python cassette.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

init()
mat('shell', '#a9b3c0')      # 浅灰半透明壳色：黑壳跟描边色贴在一起，44px 上是一块黑砖（第一版实测）
mat('label', '#f2e6c8')
mat('stripe', '#e8457a')
mat('reel', '#f4f4f0')
mat('tape', '#5a3a28')
mat('screw', '#b9c0c8')

W, H, T = 2.0, 1.25, 0.26            # 宽（NOMINAL）、高、厚；相机沿 +Y 看，正面朝 −Y
for z0 in (-T / 2 + 0.065, T / 2 - 0.065):          # 上下两片外壳，中间留缝
    prim('cube', 'shell', size=1, location=(0, z0 * 0 - 0 + (0.07 if z0 > 0 else -0.07), 0), scale=(W, 0.12, H))
# 标签（正面）：一整块大标签，中间是窗口里的两个白卷盘。
# 第一版还做了粉色条、卷盘 6 个齿、磁头口、5 颗螺丝：44px 上每个小零件各画一圈描边，叠起来整面都是描边色，
# 读成一块黑砖（measure_volume 结构密度 98%）。只留能在 44px 上各自占几个像素的大块
FY = -0.135
prim('cube', 'label', size=1, location=(0, FY, 0.30), scale=(W * 0.84, 0.02, 0.42))
for sx in (-0.45, 0.45):
    prim('cylinder', 'reel', vertices=20, radius=0.2, depth=0.06, location=(sx, FY - 0.02, -0.18), rotation=(math.pi / 2, 0, 0))

ob = join_all()
render_turntable('cassette', active=ob, lean=45, tilt=0.3, roll=0.2, screen_r=22)
