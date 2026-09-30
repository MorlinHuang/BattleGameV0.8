"""巨型针筒（档 3 三人组 G25 针筒护士，把针筒当飞镖甩过去扎在他头上，2026-09-30）。

## 形体（长轴竖放，z 从推杆到针尖 −1 → +1）

- 推杆顶的圆按钮（厚片）+ 细推杆 + 针筒尾端两片**椭圆指托**（比筒身宽一大圈，转起来最能看出体积）
- 筒身：前半截粉色药水（旋转体，单独一段）、后半截近白的空筒；两段交界是深灰**橡胶活塞**（比筒身粗一圈的短环）
- 刻度环试过两道：40px 上每道两条描边，和活塞、筒嘴口沿挤在一起读成一排黑条纹，删了
- 锥形筒嘴 → 银色针座 → 针（屏幕上 ≈ 3px 粗，画成一根线）
- r 40（游戏里拿在手里 / 飞出去约 80px 长，1 单位 ≈ 40 屏幕 px）：2W ≈ 5.6px ≈ 0.14 单位，
  活塞、指托、筒嘴口沿之间都按 ≥ 0.18 排。
- 细长件：lean 40 + roll 斜过来（skill 坑 5；55 有近 1/3 帧缩成一截短筒，认不出针筒）。

跑：blender -b --python syringe.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

init()
mat('barrel', '#eef2f6')
mat('liquid', '#ff6aa8')
mat('rubber', '#4a4450')
mat('metal', '#c8ccd4')
mat('plunger', '#f6f6f6')
R = 0.2                                                    # 筒身半径


def lathe(name, prof, m, n=24, sx=1.0):
    """旋转体：prof = [(z, r), ...]，两端封口；sx 把截面沿 x 拉成椭圆（指托）"""
    vs, fs = [], []
    for z, r in prof:
        for j in range(n):
            a = 2 * math.pi * j / n
            vs.append((r * math.cos(a) * sx, r * math.sin(a), z))
    k = len(prof)
    for i in range(k - 1):
        for j in range(n):
            fs.append((i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j))
    fs.append(tuple(range(n))[::-1]); fs.append(tuple((k - 1) * n + j for j in range(n)))
    return add_mesh(name, vs, fs, m)


lathe('thumb', [(-1.0, 0.24), (-0.99, 0.27), (-0.94, 0.27), (-0.92, 0.2)], 'plunger')       # 推杆按钮
lathe('rod', [(-0.93, 0.07), (-0.46, 0.07)], 'plunger', n=12)                                 # 推杆
lathe('flange', [(-0.5, 0.2), (-0.49, 0.22), (-0.44, 0.22), (-0.43, 0.2)], 'barrel', sx=2.3)  # 指托（椭圆）
lathe('empty', [(-0.47, R), (-0.05, R)], 'barrel')                                            # 后半截空筒
body = lathe('liquid', [(-0.06, R), (0.52, R)], 'liquid')                                     # 前半截药水
lathe('stopper', [(-0.1, R + 0.03), (-0.02, R + 0.03)], 'rubber')                          # 橡胶活塞
lathe('nozzle', [(0.51, R), (0.53, R + 0.02), (0.56, R + 0.02), (0.68, 0.09)], 'barrel')     # 筒嘴（带一圈口沿）
lathe('hub', [(0.66, 0.11), (0.76, 0.11), (0.78, 0.06)], 'metal', n=12)                      # 针座
lathe('needle', [(0.77, 0.045), (0.97, 0.03), (1.02, 0.004)], 'metal', n=10)                 # 针

ob = join_all(body)
render_turntable('syringe', active=ob, lean=40, tilt=0.3, roll=0.45, screen_r=40)
