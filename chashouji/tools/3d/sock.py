"""臭袜子（档 1，灭迹党，臭袜子足球雨里的四只袜子，2026-09-27 替换手柄）—— 一只 L 形的白色运动长筒袜，
袜口两道彩条、脚跟脚尖一块脏灰褐，从女生头顶掉下来砸她。大小参考高跟鞋（引擎里同一个 r）。

## 形体

- **沿一条 L 形中心线放样的管子**：袜筒竖着、在脚跟处拐弯、脚掌横着，鞋尖圆头收口 —— L 形剪影是第一识别点。
  袜筒顶上封口，封口面换深一档（袜子里面）。
- **袜口是台阶**：罗纹口比袜筒粗一圈（CUFF_R），再往下两道彩条也各凸一点 —— 台阶产生真描边（内部结构），
  光换材质不凸的话转起来就是一根白管子（材质分区不产生描边）。
- 脏：脚跟、脚尖两块灰褐（材质分区，只管认得出"臭"，体积靠形）。
- 袜筒有点塌（中心线带一点弯），不是直挺挺的。
- 有正面（侧面 L 形）：lean 38 + roll（同高跟鞋）。

跑：blender -b --python sock.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy

NU, NV = 18, 56
R_LEG, R_FOOT = 0.30, 0.29
CUFF_R, CUFF_T = 0.345, 0.14      # 罗纹口：半径、占全长（从顶往下）
STRIPES = [(0.17, 0.22, 'red'), (0.25, 0.30, 'blue')]   # 两道彩条（全长比例区间）
STRIPE_R = 0.318

init()
mat('white', '#f2efe6')
mat('red', '#e0404a')
mat('blue', '#3a6fd0')
mat('dirt', '#8f8468')
mat('inside', '#b9b3a4')

# 中心线：袜筒顶 → 脚跟拐弯 → 脚尖（控制点 + Catmull-Rom）
CP = [Vector(p) for p in [(-0.12, 0, 1.25), (-0.06, 0, 0.75), (-0.02, 0, 0.3), (0.12, 0, 0.02),
                           (0.55, 0, -0.1), (1.0, 0, -0.1), (1.3, 0, -0.06)]]
def cr(t):
    n = len(CP) - 1; f = t * n; i = min(n - 1, int(f)); u = f - i
    p0, p1, p2, p3 = CP[max(0, i - 1)], CP[i], CP[i + 1], CP[min(n, i + 2)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)

def radius(t):
    if t < CUFF_T:
        return CUFF_R
    for a, b, _ in STRIPES:
        if a <= t < b:
            return STRIPE_R
    r = R_LEG + (R_FOOT - R_LEG) * min(1, max(0, (t - 0.4) / 0.3))
    if t > 0.9:                                   # 鞋尖圆头
        r *= math.sqrt(max(0.0, 1 - ((t - 0.9) / 0.1) ** 2))
    return max(r, 0.01)

def zone(t):
    if t < CUFF_T:
        return 'white'
    for a, b, m in STRIPES:
        if a <= t < b:
            return m
    if 0.47 < t < 0.6 or t > 0.9:
        return 'dirt'
    return 'white'

ts = [j / (NV - 1) for j in range(NV)]
ts[-1] = 0.999
# 台阶：在分段处复制一圈（同一个 t 两个半径），截面才是真的台阶不是斜坡
cuts = [CUFF_T] + [x for a, b, _ in STRIPES for x in (a, b)]
ts = sorted(set(ts + [c - 1e-4 for c in cuts] + [c + 1e-4 for c in cuts]))
verts, faces, fm = [], [], []
prev_n = None
for t in ts:
    c = cr(t)
    tg = (cr(min(1, t + 0.01)) - cr(max(0, t - 0.01))).normalized()
    side = Vector((0, 1, 0))
    nrm = side.cross(tg).normalized()
    r = radius(t)
    for i in range(NU):
        a = 2 * math.pi * i / NU
        verts.append(tuple(c + nrm * (r * math.cos(a)) + side * (r * 1.0 * math.sin(a))))
M = ['white', 'red', 'blue', 'dirt', 'inside']
for j in range(len(ts) - 1):
    tm = (ts[j] + ts[j + 1]) / 2
    for i in range(NU):
        a, b = j * NU + i, j * NU + (i + 1) % NU
        faces.append((a, b, b + NU, a + NU)); fm.append(M.index(zone(tm)))
faces.append(tuple(range(NU))[::-1]); fm.append(M.index('inside'))
last = (len(ts) - 1) * NU
faces.append(tuple(last + i for i in range(NU))); fm.append(M.index('dirt'))
ob = add_mesh('sock', verts, faces, 'white')
for mname in M[1:]:
    ob.data.materials.append(bpy.data.materials[mname])
for p, m in zip(ob.data.polygons, fm):
    p.material_index = m

lo = [1e9] * 3; hi = [-1e9] * 3
for v in ob.data.vertices:
    for k in range(3):
        lo[k], hi[k] = min(lo[k], v.co[k]), max(hi[k], v.co[k])
print('BBOX', [round(hi[k] - lo[k], 2) for k in range(3)], flush=True)
mid = Vector([(lo[k] + hi[k]) / 2 for k in range(3)])
s = NOMINAL / max(hi[k] - lo[k] for k in range(3))
ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation(-mid)

render_turntable('sock', active=ob, lean=38, tilt=0.35, roll=0.25, screen_r=42)
