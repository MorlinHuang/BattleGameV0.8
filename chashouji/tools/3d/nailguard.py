"""护甲指套（档 3 三人组 G24 华妃式宫斗贵妃，把金护甲甩出去砸女生、"赏一丈红"，2026-09-30）。

## 形体

- 清宫金护甲：一根沿长轴收尖、往一侧弯的细长锥管（按中心线扫圆截面）+ 套口处 RINGS 道凸起环带
  + 甲面上一红一翠几颗凸起的宝石（独立小二十面体，半埋进甲身）。
- **环带和宝石都是真几何**：环带是比甲身粗一圈的短管段，宝石是半埋的小球，各自一圈轮廓；
  用材质分区画的话不产生描边（skill 坑 4b），就是一根金色的弯角。
- 这件最小最细（r 20，1 单位 ≈ 20px）：甲身不能按真护甲那么细，套口半径 MOUTH 放粗，
  环带间距按 g ≥ 2W（≈0.28 单位）只排得下两道，宝石半径 ~0.12 才占得住像素。
- 细长件：长轴竖放，lean 55 + roll 斜过来（skill 坑 5），长轴在画面里不横。

跑：blender -b --python nailguard.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy

L = 2.0
MOUTH = 0.34          # 套口半径
BEND = 0.5            # 尖端往 +x 偏多少
N = 28                # 中心线段数
init()
mat('gold', '#e8b848')
mat('band', '#f4d070')
mat('ruby', '#e0303a')
mat('jade', '#30b070')


def center(t):
    return Vector((BEND * t ** 2, 0, -L / 2 + L * t))


def rad(t):
    return MOUTH * (1 - t) ** 0.85 + 0.025


def tube(name, ts, rf, m, n=16):
    vs, fs = [], []
    for i, t in enumerate(ts):
        p = center(t)
        tg = (center(min(1, t + 1e-3)) - center(max(0, t - 1e-3))).normalized()
        s = tg.cross(Vector((0, 1, 0))).normalized()
        u = s.cross(tg)
        for j in range(n):
            a = 2 * math.pi * j / n
            vs.append(tuple(p + (s * math.cos(a) + u * math.sin(a)) * rf(t)))
    k = len(ts)
    for i in range(k - 1):
        for j in range(n):
            fs.append((i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j))
    fs.append(tuple(range(n))[::-1]); fs.append(tuple((k - 1) * n + j for j in range(n)))
    return add_mesh(name, vs, fs, m)


body = tube('body', [i / N for i in range(N + 1)], rad, 'gold')
for t0, t1 in ((0.0, 0.06), (0.17, 0.23)):                       # 套口两道环带
    tube('band', [t0, t1], lambda t: rad(t) + 0.07, 'band')


def gem(t, ang, r, m):
    p = center(t)
    d = Vector((math.sin(ang), -math.cos(ang), 0))                # ang=0 朝相机(−y)
    prim('ico_sphere', m, subdivisions=1, radius=r, location=tuple(p + d * (rad(t) * 0.85)))


gem(0.38, 0.0, 0.14, 'ruby')
gem(0.58, 0.0, 0.11, 'jade')
gem(0.46, math.pi, 0.12, 'jade')

ob = join_all(body)
render_turntable('nailguard', active=ob, lean=55, tilt=0.3, roll=0.45, screen_r=20)
