"""哑铃（档 3 三人组 B25 健身教练，单膝跪着把哑铃抡出去砸女生，2026-09-30；审查第三轮 6.7 返工同日）。

## 形体

- 一根握把 + **两头各一片厚铁片** + 两头锁扣。铁片、锁扣、握把各是单独一块，转起来铁片的圆边轮廓、
  端面的圆片和握把的遮挡一直在变 —— 读得出"一只在翻滚的哑铃"。
- **一侧只留一片、加厚加大**（审查第三轮 6.7 / 规范 7.3）：美术首版一侧两片（大片在里、小片在外）+ 握把两道环，
  r 24 屏幕 52px 上片与片、片与锁扣的间距小于 2 倍描边，描边并成一片 —— 36 帧里 20 帧是墨块（红片只剩一圈），
  四个角度都读成深色的蘑菇 / 螺栓。现在一片厚 0.34（屏幕 ~9px），片外只有一个锁扣，r 放到 28。
- 铁片用亮红 + 外侧一块浅色圆台（独立几何，贴片面带裙边扎进去，skill 坑 4b）：铁片端面转到镜头前时认得出是一张圆片，
  不是一个红桶。
- 长条件的转法：转轴离屏幕横轴 20°（lean −70），起始姿态长轴横放。长轴绕转轴扫的是一个 ~40° 的圆锥，
  屏幕上的长度永远 ≥ 0.76 倍 —— 美术首版 lean 60 时长轴会转到正对镜头，整只缩成一个圆点（"蘑菇"）。
- 屏幕上半径 28（web/trio_buddy.js B25 atk.r 要从 24 改成 28）。

跑：blender -b --python dumbbell.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

init()
mat('plate', '#e0503f')      # 红色杠铃片：深色铁片跟描边色贴在一起，缩到 48px 就是一团黑（首版实测）
mat('rim', '#f0e6dc')
mat('bar', '#c9d0d8')

HALF = 1.0                          # 整只长 2.0（NOMINAL）
BAR_R = 0.1
PR, PT, PX = 0.56, 0.34, 0.46       # 铁片半径、厚、内侧面离中心
prim('cylinder', 'bar', vertices=16, radius=BAR_R, depth=2 * HALF * 0.9, rotation=(0, math.pi / 2, 0))
for s in (-1, 1):
    prim('cylinder', 'plate', vertices=32, radius=PR, depth=PT, location=(s * (PX + PT / 2), 0, 0), rotation=(0, math.pi / 2, 0))
    # 片外侧面贴一块浅色圆台（半径 0.36、凸出 0.05，往片里扎 0.04 当裙边）：端面转到背光那一侧时红片落成深红，
    # 浅色圆台落成灰米色，仍是"一张有边的圆片"。第一版用半埋的圆环，只露出几段碎弧，读成白色划痕
    prim('cylinder', 'rim', vertices=32, radius=0.36, depth=0.09, location=(s * (PX + PT + 0.005), 0, 0), rotation=(0, math.pi / 2, 0))
    prim('cylinder', 'bar', vertices=16, radius=0.17, depth=0.1, location=(s * (PX + PT + 0.09), 0, 0), rotation=(0, math.pi / 2, 0))   # 锁扣

# prim 的 rotation 是物体变换不是网格：join 之后网格留在 active 那件的局部坐标里，而转盘会覆盖 rotation_euler，
# 长轴就不知道落在哪根轴上（上一版因此起始是竖的）。先把旋转、缩放烤进网格，长轴确定是 X
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
ob = join_all()
# 转轴 lean −70、起始几乎横放：长轴扫的圆锥最低仍有 0.76 倍长；朝镜头的那张片面大多落在光这一侧（sun 从镜头这侧右上方打，
# Toon 离光 ~65° 以外整面落暗）。lean 90 + roll 0.7 那一版端面朝镜头的帧里 17/36 是背光的黑圆片（快测）
render_turntable('dumbbell', active=ob, lean=-70, tilt=0.0, roll=0.1, screen_r=28)
