"""口红（档 1，查岗党，2026-09-26 替换发卡）—— 一支旋出膏体的口红，一次礼物扔三支、间隔 0.5 秒，
朝男生的腰和大腿（短裤那一块）飞。用户要"飞行弹幕为淡红色"，所以管身整支是淡红，不用金属色管。

## 形体

- **斜切的膏体是第一识别点**：没有那道斜面就是一根粉色圆棒（发卡最早那版吃过这个亏）。
  膏体比管身深一档红，斜面朝 +X，转起来斜面时有时无，读得出是口红。
- **三段**：管身（淡红，最粗最长）→ 一圈金色腰箍（分段线，也是唯一的暖色点）→ 内管（淡红，
  略细）→ 膏体（深红，更细，顶上斜切）。三段三个粗细，侧面剪影是台阶状，不会塌成一根棍。
- **粗细**：管身半径 0.42、全长约 2.4 → 粗细比 1:2.9。再细，档 1 屏幕上只有 60 多像素，
  内管和膏体会被两条描边吃光（发卡文档里"零件做粗"那条）。
- **长轴竖着（Z）**，转轴 lean 20：细长件竖着绕斜轴转不会塌成一个圆（同香蕉）。

跑：blender -b --python lipstick.py -- 36 <边长> 128 <out> 1
"""

import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy

init()
mat('case',   '#ff9aa2')   # 管身 / 内管：淡红
mat('bullet', '#e8364e')   # 膏体：深一档的红，斜面靠它和管身分开
mat('band',   '#f2c14e')   # 腰箍：金
# 视图变换改 Standard（同香蕉）：AgX 把 #ff9aa2 压成灰扑扑的豆沙粉，读不成"淡红"
bpy.context.scene.view_settings.view_transform = 'Standard'

SEG = 20
R_CASE, H_CASE = 0.42, 1.15   # 管身
R_BAND, H_BAND = 0.46, 0.24   # 腰箍（比管身略粗一圈）。0.14 被上下两条描边吃光，只剩一条金线
R_IN, H_IN = 0.36, 0.40       # 内管
R_BUL, H_BUL = 0.27, 0.72     # 膏体（斜切前的最高处）
SLANT = 0.55                  # 斜面在直径上的落差（占膏体高）

z = -1.2
prim('cylinder', 'case', vertices=SEG, radius=R_CASE, depth=H_CASE, location=(0, 0, z + H_CASE / 2)); z += H_CASE
prim('cylinder', 'band', vertices=SEG, radius=R_BAND, depth=H_BAND, location=(0, 0, z + H_BAND / 2)); z += H_BAND
prim('cylinder', 'case', vertices=SEG, radius=R_IN, depth=H_IN, location=(0, 0, z + H_IN / 2)); z += H_IN

# 膏体：圆柱，顶面按 x 斜切（x=+R 最低、x=-R 最高）
verts, faces = [], []
for i in range(SEG):
    a = 2 * math.pi * i / SEG
    x, y = R_BUL * math.cos(a), R_BUL * math.sin(a)
    verts.append((x, y, z))
    verts.append((x, y, z + H_BUL * (1 - SLANT * (x / R_BUL + 1) / 2)))
for i in range(SEG):
    j = (i + 1) % SEG
    faces.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
faces.append(tuple(2 * i for i in reversed(range(SEG))))
faces.append(tuple(2 * i + 1 for i in range(SEG)))
add_mesh('bullet', verts, faces, 'bullet')

ob = join_all()
lo = [1e9] * 3; hi = [-1e9] * 3
for v in ob.data.vertices:
    for k in range(3):
        lo[k], hi[k] = min(lo[k], v.co[k]), max(hi[k], v.co[k])
print('BBOX', [round(hi[k] - lo[k], 2) for k in range(3)], flush=True)
mid = Vector([(lo[k] + hi[k]) / 2 for k in range(3)])
s = NOMINAL / max(hi[k] - lo[k] for k in range(3))
ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation(-mid)

render_turntable('lipstick', active=ob, lean=20, tilt=0.25, roll=0.15, screen_r=34)
