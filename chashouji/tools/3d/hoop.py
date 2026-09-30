"""荧光呼啦圈（档 3 三人组 G28 80 年代健美操女，甩荧光呼啦圈飞过去套住他，2026-09-30）。

## 形体

- 一根细圆环（torus，荧光紫）+ 6 段单独的凸起胶带环（荧光粉/荧光绿/荧光黄交替），每段是比圈管粗一圈的
  torus 弧段，端面封口。胶带用材质分区的话不产生描边（skill 坑 4b），就是一个彩色的圈。
- r 36 → 1 单位 = 36 屏幕 px，描边 2.8px，g ≥ 2W ≈ 0.16 单位：6 段各占 22°、间隔 38°，沿圈弧长间隔 0.66 单位 ≈ 24px，远大于 2W。
- 环形件，lean 见 render_turntable 那一行的注释。

跑：blender -b --python hoop.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

init()
mat('hoop', '#a45cff')
mat('pink', '#ff3fa4')
mat('green', '#7af03a')
mat('yellow', '#ffe53a')

R = 1.0 - 0.09          # 圈中心线半径：外缘（含胶带）正好 1.0 → 直径 2.0 = NOMINAL


def tube(a0, a1, rm, m, nu, nv=10):
    """圈平面 = XZ（正对相机），a0~a1 弧段，管半径 rm；不是整圈时两端封口"""
    full = abs(a1 - a0) >= 2 * math.pi - 1e-6
    nu_ = nu if full else nu + 1
    verts, faces = [], []
    for i in range(nu_):
        a = a0 + (a1 - a0) * i / nu
        c, s = math.cos(a), math.sin(a)
        for j in range(nv):
            b = 2 * math.pi * j / nv
            rr = R + rm * math.cos(b)
            verts.append((rr * c, rm * math.sin(b), rr * s))
    for i in range(nu if full else nu):
        i1 = (i + 1) % nu_ if full else i + 1
        for j in range(nv):
            faces.append((i * nv + j, i * nv + (j + 1) % nv, i1 * nv + (j + 1) % nv, i1 * nv + j))
    if not full:
        faces.append(tuple(range(nv))[::-1])
        faces.append(tuple(nu * nv + j for j in range(nv)))
    return add_mesh('t', verts, faces, m)


tube(0, 2 * math.pi, 0.06, 'hoop', 72)
cols = ['pink', 'green', 'yellow']
NS, SW = 6, math.radians(22)
for k in range(NS):
    a = 2 * math.pi * k / NS + 0.3
    tube(a - SW / 2, a + SW / 2, 0.09, cols[k % 3], 6)

ob = join_all()
render_turntable('hoop', active=ob, lean=60, tilt=0.45, roll=0.2, screen_r=36)
