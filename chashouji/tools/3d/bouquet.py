"""玫瑰花束（档 3，查岗党）—— 试点那一件，现在改成走 common.py 的公共框架。

形状结论（试点时试出来的，改形先看这几条）：
- 花瓣排布半径必须**远小于**花瓣宽度，否则彼此够不着，渲出来是一堆散开的红碎片
- 花瓣顶边要压成弧、宽度走 sin 曲线；直顶边加卷曲就是一根尖刺，整团读成蓟花
- 花团要显著宽于扎口（真实捧花 2~3 倍）。圆锥从正底看的投影是它最宽处那个圆，
  底部收尖是白费功夫，底视好不好看全看花团比扎口宽多少
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy

init()
mat('rose_a', '#e63a62')   # 深玫红
mat('rose_b', '#ff5f86')   # 亮粉
mat('leaf',   '#5f8f57')   # 墨绿
mat('wrap',   '#e8c79e')   # 暖杏包装纸（比引擎矢量版的 f7e3cf 深一档，浅色在明亮底图上糊）


def petal_mesh(w, h, curl, nu=7, nv=5):
    """一片花瓣：下窄、中间最宽、顶部再收一点（sin 曲线），顶边压弧，横向卷成杯。"""
    verts, faces = [], []
    for j in range(nv):
        v = j / (nv - 1)
        wide = w * (0.26 + 0.74 * math.sin(v * 2.55))
        for i in range(nu):
            u = i / (nu - 1) * 2 - 1
            verts.append((u * wide, -curl * u * u * (0.35 + v), v * h - u * u * h * 0.16))
    for j in range(nv - 1):
        for i in range(nu - 1):
            a = j * nu + i
            faces.append((a, a + 1, a + nu + 1, a + nu))
    return verts, faces


def rose_head(R, m, seed=0):
    """一朵玫瑰：内外两层花瓣 + 一个堵中心的小球。
       花瓣数压到 8 片 —— 观众端这朵花只有十几像素，片数多了描边糊成一团黑。"""
    obs = []
    idx = 0
    for cnt, rad, tilt, scl in [(3, 0.09, 0.14, 0.58), (5, 0.30, 0.62, 1.00)]:
        for k in range(cnt):
            ang = idx * 2.39996 + seed      # 黄金角排布，避免对齐成十字
            idx += 1
            vs, fs = petal_mesh(R * 1.05 * scl, R * 1.25 * scl, R * 0.50 * scl)
            ob = add_mesh('petal', vs, fs, m)
            ob.matrix_world = (Matrix.Rotation(ang, 4, 'Z')
                               @ Matrix.Translation((0, -R * rad, -R * 0.18 * scl))
                               @ Matrix.Rotation(tilt, 4, 'X'))
            obs.append(ob)
    obs.append(prim('uv_sphere', m, segments=10, ring_count=6,
                    radius=R * 0.30, location=(0, 0, R * 0.16)))
    return obs


# 包装纸：倒锥
wrap = prim('cone', 'wrap', vertices=12, radius1=0.40, radius2=0.06,
            depth=0.66, location=(0, 0, -0.40))

# 叶子：压扁拉长的球
for a, r, z in [(0.5, 0.95, 0.10), (2.6, 0.95, -0.05), (4.3, 0.92, 0.14), (3.5, 0.80, 0.26)]:
    lf = prim('uv_sphere', 'leaf', segments=8, ring_count=5, radius=0.30,
              location=(math.cos(a) * r, math.sin(a) * r, z))
    lf.scale = (1.5, 0.55, 0.16)
    lf.rotation_euler = (0, 0.5, a)

# 七朵花头：中间一朵高，外圈六朵低，形成半球形捧花
HEADS = [(0.0, 0.0, 0.50, 0.46, 'rose_a', 0.0)]
for k in range(6):
    phi = k * math.pi / 3
    HEADS.append((phi, 0.70, 0.12, 0.40, 'rose_b' if k % 3 == 1 else 'rose_a', 0.66))
for i, (phi, rad, z, R, m, lean) in enumerate(HEADS):
    obs = rose_head(R, m, seed=i * 1.1)
    # 绕"垂直于径向的水平轴"倾斜，花顶就朝外倒；直接绕 X 转的话只有正东那朵是对的
    axis = Vector((-math.sin(phi), math.cos(phi), 0)) if rad > 0 else Vector((1, 0, 0))
    M = (Matrix.Translation((math.cos(phi) * rad, math.sin(phi) * rad, z))
         @ Matrix.Rotation(lean, 4, axis))
    for ob in obs:
        ob.matrix_world = M @ ob.matrix_world

render_turntable('bouquet', active=wrap, screen_r=76)