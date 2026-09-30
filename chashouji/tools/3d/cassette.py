"""磁带（档 3 三人组 B24 霹雳舞，坐地把一盘磁带像飞盘一样甩出去砸女生，2026-09-30）—— 80 年代的认人点。

## 形体

- 一盘卡式磁带：一整块外壳 + 正面一大块标签 + 两个白卷盘。**每块都是单独的几何**，
  转起来卷盘、标签边、壳缝各自的轮廓在变；只做一块扁盒子贴张图的话就是一张会转的卡片（skill 坑 4b）。
  零件不能碎：44px 上每块都要自己占得住几个像素，不然描边叠满整面（见下面标签处的注释）。
- 有正面（标签那一面），**lean −25**（取负见文末姿态注释）：正面最多偏 50°，永远不侧对。lean 45 那一版（美术首版）转到侧对的一半帧只剩一条壳边，
  壳厚 0.26 在 58px 上 7px、两边描边一占全是墨（17/36 墨块帧，审查第三轮 6.7：90°、180° 是两块黑板条）。
  25 时侧面只斜着露出一条，厚度仍看得到。
- 屏幕上半径 22（web/trio_buddy.js B24 atk.r），宽 44px。

跑：blender -b --python cassette.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

init()
mat('shell', '#c9d2de')      # 浅灰壳色：黑壳跟描边色贴在一起，44px 上是一块黑砖（第一版实测）；#a9b3c0 的壳边在 Toon 暗面里还是发黑，再提亮一档
mat('label', '#f2e6c8')
mat('stripe', '#e8457a')
mat('reel', '#f4f4f0')
mat('tape', '#5a3a28')
mat('screw', '#b9c0c8')

W, H, T = 2.0, 1.25, 0.2             # 宽（NOMINAL）、高、厚；相机沿 +Y 看，正面朝 −Y
# 外壳一整块。美术首版是上下两片、中间留 0.02 的缝：斜着看侧面时缝又是一条描边，侧面那一条整个是墨；
# 厚 0.26 时侧面斜露 ~6px、两边描边一夹也全是墨。收到 0.2、去掉缝，侧面读成一道粗边线
prim('cube', 'shell', size=1, location=(0, 0, 0), scale=(W, T, H))
# 标签（正面）：一整块大标签，中间是窗口里的两个白卷盘。
# 第一版还做了粉色条、卷盘 6 个齿、磁头口、5 颗螺丝：44px 上每个小零件各画一圈描边，叠起来整面都是描边色，
# 读成一块黑砖（measure_volume 结构密度 98%）。只留能在 44px 上各自占几个像素的大块
FY = -T / 2 - 0.005
prim('cube', 'label', size=1, location=(0, FY, 0.30), scale=(W * 0.84, 0.02, 0.42))
for sx in (-0.45, 0.45):
    prim('cylinder', 'reel', vertices=20, radius=0.2, depth=0.06, location=(sx, FY - 0.02, -0.18), rotation=(math.pi / 2, 0, 0))

ob = join_all()
# 姿态按灯定：sun 从镜头这侧右上方打（common.py），Toon 在法线偏离光线 ~65° 以外整面落进暗面，浅灰壳也发黑。
# lean +25 / tilt 0.3 那一版标签面有 5/12 帧偏离 70~83°，整面是深褐的（快测）。转轴往光的水平投影那边偏（lean 取负），
# 起始姿态让标签面朝上抬（tilt 负），36 帧里标签面离光最多 56°，每帧都是亮面；离视线 7~43°，厚度照样露得出来
render_turntable('cassette', active=ob, lean=-25, tilt=-0.4, roll=0.8, screen_r=22)
