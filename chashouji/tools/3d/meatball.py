"""濑尿牛丸（档 3 三人组 B27 食神，蹲着弹射出去砸女生、落地乱弹，2026-09-30）。

## 形体

- 牛丸不是光滑的球：手打牛肉丸表面是一粒一粒鼓起来的肉筋。做法 = 一颗略扁、表面按噪声起伏的主球
  + 一圈**单独的小肉粒**（小二十面体，半埋在主球里）+ 几粒深色的碎筋（更小，颜色更深）。
  每一粒都是一块自己的几何，转起来它们各自的轮廓、互相遮挡一直在变 —— 读得出"在滚的一颗肉丸"，
  而不是画了斑点的褐色圆片（材质分区画的点不产生描边，skill 坑 4b）。
- 各向同性：lean 90。屏幕上半径 18（web/trio_buddy.js B27 atk.r），直径 36px，比樱木的篮球（r 34）小一半：
  牛丸本来就是一口一个的东西，大了就读成铅球。
- 小肉粒不能太多太碎：36px 上每粒只有 4~5px，描边 2.8px 会把太碎的糊成一团黑。22 粒、半径占主球 0.3：
  第一版 16 粒、0.22，measure_volume 结构密度只有 16%（达标线 20%）。

跑：blender -b --python meatball.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix, noise
import bpy

R = 1.0
LUMPS = 22         # 表面鼓起的肉粒
LUMP_R = 0.3       # 肉粒半径（占主球）
SPECKS = 5         # 深色碎筋
random.seed(7)

init()
mat('meat', '#9a5a2e')
mat('lump', '#b06a38')
mat('speck', '#5a3018')

# 主球：略扁（真牛丸压过一下），表面按噪声起伏一点
core = prim('ico_sphere', 'meat', subdivisions=4, radius=R)
for v in core.data.vertices:
    p = v.co.normalized()
    v.co = p * R * (1 + 0.05 * noise.noise(p * 2.5)) * Vector((1, 1, 0.92))


def fib(n, i):
    """球面上均匀分布的第 i 个点（斐波那契螺旋），再抖一点免得排成格子"""
    y = 1 - 2 * (i + 0.5) / n
    r = math.sqrt(1 - y * y)
    a = i * math.pi * (3 - math.sqrt(5))
    return Vector((math.cos(a) * r + random.uniform(-.08, .08), y + random.uniform(-.08, .08), math.sin(a) * r)).normalized()


for i in range(LUMPS):
    d = fib(LUMPS, i)
    rr = LUMP_R * random.uniform(0.8, 1.15)
    prim('ico_sphere', 'lump', subdivisions=2, radius=rr, location=tuple(d * (R * 0.93)))
for i in range(SPECKS):
    d = fib(SPECKS, i + 0.5)
    prim('ico_sphere', 'speck', subdivisions=1, radius=0.1, location=tuple(Vector((d.x, -d.y, d.z)) * (R * 1.0)))

ob = join_all(core)
s = NOMINAL / (2 * R * 1.1)        # 肉粒让外轮廓比主球大一圈，按 1.1R 当标称半径
ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0))
render_turntable('meatball', active=ob, lean=90, tilt=0.35, roll=0.25, screen_r=18)
