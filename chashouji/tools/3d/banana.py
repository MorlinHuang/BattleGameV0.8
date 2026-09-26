"""香蕉（档 1，灭迹党）—— 一根弯香蕉，一次礼物扔三根、间隔 1 秒，朝女生的脸飞。

## 转轴

lean=20：香蕉的识别点是侧面那道弯，lean=45 会转到两头正对镜头（一个黄圆点，认不出）。

## 形体

- **弯是第一识别点。** 中心线是一段圆弧（ARC 度），直的读成黄瓜/玉米。
- **五棱截面**：半径按 cos(5θ) 起伏 BUMP，转起来明暗面一块一块地换，比圆管有体积感。
  棱线不做成凸脊 —— 凸出来会被 Freestyle 当轮廓描黑（瓜子那边踩过），只靠平面着色的明暗分面。
- **两端收尖**：一头是深色果柄（STEM），一头是深褐色小尖（TIP）。两头颜色不同，
  翻过去也分得清头尾。
- 整根归一到 NOMINAL（最长边），框架靠这个反算 scale。

跑：blender -b --python banana.py -- 36 <边长> 128 <out> 1
"""

import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy

ARC = 80.0        # 中心线弧度（度）
RAD = 1.35        # 中心线半径
THICK = 0.19      # 最粗处半径（长约 1.9，粗细比 1:5 才读成香蕉，0.30 读成瓜子仁）
BUMP = 0.09       # 五棱起伏
NU, NV = 20, 28   # 环向 / 纵向段数
STEM_T = 0.13     # 果柄占全长的比例（t<STEM_T 用果柄材质）
TIP_T = 0.94      # t>TIP_T 用尖头材质

init()
mat('peel', '#ffc61f')
# 视图变换改 Standard（只这一件）：Blender 4 默认 AgX 会把高亮的黄压成土黄/芥末色 ——
# #ffc21a 亮面只剩 (230,200,148)；往橙里偏会洗成肉粉，往暗里压又是芥末。其余七件是粉/蓝/棕/白，
# AgX 下差别不大；黄色对它最敏感。明暗二分和描边都不受这一项影响。
bpy.context.scene.view_settings.view_transform = 'Standard'
mat('stem', '#5e6a1e')
mat('tip', '#3a2616')


def prof(t):
    """纵向半径：果柄那头细长、中段饱满、尖头收拢。"""
    if t < STEM_T:
        return 0.36 + 0.12 * t / STEM_T                     # 果柄：细，略往身子方向变粗
    u = (t - STEM_T) / (1 - STEM_T)
    return max(0.05, math.sin(math.pi * min(1.0, u * 0.92 + 0.04)) ** 0.55)


def center(t):
    a = math.radians(-ARC / 2 + ARC * t)
    return Vector((RAD * math.sin(a), 0.0, RAD * (1 - math.cos(a)))), a


verts, faces, fmat = [], [], []
c0, _ = center(0.0)
verts.append(tuple(c0 + Vector((-0.02, 0, 0))))          # 果柄端盖中心
for j in range(1, NV):
    t = j / NV
    c, a = center(t)
    tang = Vector((math.cos(a), 0.0, math.sin(a)))
    nrm = Vector((-math.sin(a), 0.0, math.cos(a)))
    bin_ = Vector((0.0, 1.0, 0.0))
    r = THICK * prof(t)
    for i in range(NU):
        th = i * 2 * math.pi / NU
        rr = r * (1 + BUMP * math.cos(5 * th))
        p = c + nrm * (rr * math.cos(th)) + bin_ * (rr * math.sin(th))
        verts.append(tuple(p))
c1, a1 = center(1.0)
verts.append(tuple(c1))
TOP = len(verts) - 1


def vid(j, i):
    return 1 + (j - 1) * NU + i % NU


def zone(t):
    return 1 if t < STEM_T else 2 if t > TIP_T else 0


for i in range(NU):
    faces.append((0, vid(1, i + 1), vid(1, i))); fmat.append(1)
for j in range(1, NV - 1):
    t = (j + 0.5) / NV
    for i in range(NU):
        faces.append((vid(j, i), vid(j, i + 1), vid(j + 1, i + 1), vid(j + 1, i)))
        fmat.append(zone(t))
for i in range(NU):
    faces.append((TOP, vid(NV - 1, i), vid(NV - 1, i + 1))); fmat.append(2)

ob = add_mesh('banana', verts, faces, 'peel')
ob.data.materials.append(bpy.data.materials['stem'])
ob.data.materials.append(bpy.data.materials['tip'])
for p, m in zip(ob.data.polygons, fmat):
    p.material_index = m

# 归一：包围盒最长边 = NOMINAL，并把中心挪到原点
lo = [1e9] * 3; hi = [-1e9] * 3
for v in ob.data.vertices:
    for k in range(3):
        lo[k], hi[k] = min(lo[k], v.co[k]), max(hi[k], v.co[k])
mid = Vector([(lo[k] + hi[k]) / 2 for k in range(3)])
s = NOMINAL / max(hi[k] - lo[k] for k in range(3))
ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation(-mid)

render_turntable('banana', active=ob, lean=20, tilt=0.25, roll=0.15, screen_r=40)
