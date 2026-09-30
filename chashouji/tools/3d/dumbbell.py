"""哑铃（档 3 三人组 B25 健身教练，单膝跪着把哑铃抡出去砸女生，2026-09-30）。

## 形体

- 一根握把 + 两头各两片铁片（大片在里、小片在外）+ 两头锁扣。**每片铁片是单独一块**（片与片之间留缝），
  转起来一片片的圆边轮廓互相遮挡、透视缩短一直在变 —— 读得出"一只在翻滚的哑铃"。
  铁片要是做成一整块圆柱，就是两个黑桶夹一根棍（材质分区不产生描边，skill 坑 4b）。
- 握把上两道凸环：同理，给握把一段内部结构。零件不能碎（见 PLATES 的注释）。
- 有朝向（长条），lean 60：翻跟头能看到端面的圆片，又不会整只缩成一个圆点。
- 屏幕上半径 24（web/trio_buddy.js B25 atk.r），整只长 48px，约是教练拳头的 2.5 倍。

跑：blender -b --python dumbbell.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Matrix
import bpy

init()
mat('plate', '#d8453a')      # 红色杠铃片：深色铁片跟描边色贴在一起，缩到 48px 就是一团黑（第一版实测）
mat('rim', '#e8ecf0')
mat('bar', '#b9c0c8')
mat('knurl', '#8a929c')

HALF = 1.0                          # 整只长 2.0（NOMINAL）
BAR_R = 0.07
prim('cylinder', 'bar', vertices=16, radius=BAR_R, depth=2 * HALF * 0.96, rotation=(0, math.pi / 2, 0))
for x in (-0.15, 0.15):                                # 握把两道环（第一版 5 道 + 每片铁片一圈凸环：48px 上描边叠满，整只是黑的，结构密度 74%）
    prim('cylinder', 'knurl', vertices=16, radius=BAR_R * 1.35, depth=0.045, location=(x, 0, 0), rotation=(0, math.pi / 2, 0))
PLATES = [(0.44, 0.18), (0.33, 0.14)]                 # (半径, 厚度)，从里往外：两片，片够厚才占得住像素
for s in (-1, 1):
    x = 0.44
    for r, t in PLATES:
        prim('cylinder', 'plate', vertices=28, radius=r, depth=t, location=(s * (x + t / 2), 0, 0), rotation=(0, math.pi / 2, 0))
        x += t + 0.04                                    # 片与片之间留缝
    prim('cylinder', 'rim', vertices=16, radius=0.12, depth=0.07, location=(s * (x + 0.035), 0, 0), rotation=(0, math.pi / 2, 0))   # 锁扣

ob = join_all()
render_turntable('dumbbell', active=ob, lean=60, tilt=0.5, roll=0.3, screen_r=24)
