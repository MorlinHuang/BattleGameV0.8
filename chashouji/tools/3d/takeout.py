"""外卖盒（档 3 三人组 B9 外卖小哥，把一盒外卖扔出去砸女生、汤汁溅开，2026-09-30）。

## 形体

- 长方形塑料餐盒：盒身是上大下小的斜壁台体（收口）+ 盒盖（比盒口外扩一圈的盖沿，悬挑）
  + 盖面中间一块凸起的盖心 + 盖上斜压一张订单小票 + 一包纸套筷子。**每样都是单独的几何**：
  盖沿悬挑、盖心台阶、小票和筷子包的厚边各自一圈轮廓，转起来互相遮挡在变。
- 斜壁 / 悬挑盖沿：垂直壁正视时法向垂直视线，描边一帧有一帧无地闪（skill 坑 4b 配套做法）。
- 盖与盒身是实心贴合（盒身顶面直接顶住盖底），不留夹缝：夹缝进不去光会渲纯黑（skill 坑 7）。
- 有正面（盖面）：lean 45。

跑：blender -b --python takeout.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy

init()
mat('body', '#eef0ec')
mat('lid', '#f8f8f4')
mat('ticket', '#f4d24a')
mat('ink', '#e2503a')
mat('chop', '#d8b078')
mat('sleeve', '#e84a3a')

n = [0]


def frustum(x0, y0, x1, y1, za, zb, m):
    """底 (±x0, ±y0) @ za，顶 (±x1, ±y1) @ zb 的台体"""
    n[0] += 1
    vs = [(-x0, -y0, za), (x0, -y0, za), (x0, y0, za), (-x0, y0, za),
          (-x1, -y1, zb), (x1, -y1, zb), (x1, y1, zb), (-x1, y1, zb)]
    fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return add_mesh('f%d' % n[0], vs, fs, m)


def plate(cx, cy, w, h, za, zb, ang, m):
    """盖面上的一块薄板（中心 cx,cy、绕 z 转 ang），底 za 扎进盖里"""
    n[0] += 1
    c, s = math.cos(ang), math.sin(ang)
    vs = []
    for z in (za, zb):
        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            x, y = a * w / 2, b * h / 2
            vs.append((cx + c * x - s * y, cy + s * x + c * y, z))
    fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return add_mesh('p%d' % n[0], vs, fs, m)


# 盒子"平放"时盖面朝上（+z）。整件最后绕 x 转 90° 让盖面朝相机（−y）
W, D = 1.0, 0.7              # 盒口半宽/半深（整件长 2.0 = NOMINAL 由盖沿撑到）
body = frustum(W * 0.86, D * 0.82, W * 0.95, D * 0.93, -0.36, 0.12, 'body')        # 斜壁盒身
frustum(W * 1.0, D * 1.0, W * 1.0, D * 1.0, 0.10, 0.18, 'lid')                      # 盖沿（外扩悬挑）
frustum(W * 0.82, D * 0.76, W * 0.76, D * 0.68, 0.16, 0.30, 'lid')                  # 盖心凸台（斜边）
plate(0.28, 0.08, 0.62, 0.8, 0.26, 0.34, 0.22, 'ticket')                             # 订单小票
plate(0.28, 0.2, 0.46, 0.1, 0.32, 0.37, 0.22, 'ink')                                 # 小票抬头的红条（凸起）
plate(-0.38, -0.02, 0.22, 1.2, 0.26, 0.40, -0.35, 'sleeve')                          # 筷子纸套

ob = join_all(body)
ob.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))       # 盖面转向 −y（相机）
render_turntable('takeout', active=ob, lean=45, tilt=0.3, roll=0.2, screen_r=26)
