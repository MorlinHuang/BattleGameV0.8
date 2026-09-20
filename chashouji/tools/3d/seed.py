"""瓜子（档 1，灭迹党）—— **一小撮五颗**。

## 为什么是一撮

单颗瓜子剥掉外轮廓之后里面是空的（内部结构密度 1%、屏幕结构量 0）。转动时眼睛真正读到的
立体信号是**内部结构的遮挡关系在变**，一颗光溜溜的水滴不管怎么转，中间那块看上去都一样，
调转轴调转速都救不了。走花束那条路：**靠零件数量堆遮挡关系**。

## 这一撮怎么排

- **颗与颗必须在投影里互相压住，但只能斜着压。** 散开成互不相连的小豆子，每块都被自己那圈
  外轮廓吃光，剥完什么都不剩、密度反而是 0；两颗**平行贴着**压则两条外轮廓并成一条黑杠。
  所以交叉着压。
- **朝向用黄金角 2.39996 打散**（跟花束的花瓣一个做法），排整齐了转半圈还是那个图形。
- **摊开一点比挤成团好。** 同一张摆位表把间距从 ×1.00 拉到 ×1.45，结构密度 25%→30%：
  挤成一团时外圈几颗把中心那几条接缝盖住了，接缝在剥层里剩不下来。间距再往上走
  并集占比掉得比密度涨得快（屏幕结构量 = 密度 × 屏幕px²），×1.45 是实测的拐点。
- **整撮的外接尺寸归一到 NOMINAL=2.0**（脚本末尾自动量 bbox 再缩），框架靠这个反算 scale。

## 单颗的尺寸是被描边宽度定死的

描边是**按观众屏幕上的绝对像素**画的（OUTLINE_W=2.8），而这件东西在屏幕上只有 57px、
主体标称直径才 42px。一颗瓜子归一化后宽 0.78 单位 = 屏幕 16px，两条描边吃掉 5.6px，
剩 10px 填色 —— 这已经是下限附近。实测三档：

| 版本 | 单颗宽 | 结构密度 | 屏幕结构量 | 墨占实心 | 壳色像素中位 |
|---|---|---|---|---|---|
| 五颗瘦（W=0.39） | 屏幕 9px | 48% | 19 | **78%** | **826** |
| 五颗（W=0.74，本版） | 屏幕 16px | 30% | 10 | 61% | 1926 |
| 四颗胖（W=0.74，挤成团） | 屏幕 17px | 21% | 7 | 55% | 2143 |

五颗瘦那版是**上一轮在 k² 粗描边下被否掉的方案，描边修好之后重试了一次**：结构密度最高，
但那是糊出来的 —— 可见壳色只剩别版的 43%，观众端是一坨带尖角的深色星星，读不出瓜子。
**结构密度会被黑块骗，必须配识别色像素一起看。**

单颗的形状结论（一直有效）：
- **脊线用材质分区，不用凸起。** 凸出来的脊会被 Freestyle 当成可见轮廓描一圈，
  在观众端就是顺着长边的两条黑线，整颗糊成一团黑。同一块网格换材质不会多出任何描边。
- **厚度 T 是结构量的杠杆**：T=0.44/0.48/0.52 三档，屏幕结构量 10/9/8，壳色 1926/1974/2086。
  再厚一点可读性只多一点点，结构量却掉出达标线，取 0.44。
- **水滴不对称**：一头尖一头圆钝，对称梭形读成"一粒米"。

## 转轴与渲染边长

`lean=50, tilt=0.25, roll=0.15` 沿用量出来的档，换形体后复量过（贴纸残差 0.77），没理由动。

跑：blender -b --python seed.py -- 36 160 128 <out> 1
    pack_atlas.py <帧目录> seed_atlas.webp --cell <并集>

渲染边长按 `res = 单格 / 并集占比` 反推：并集占比 0.82，要 131 的单格就渲 160。
**描边宽度与渲染边长无关**（`屏幕描边 = 渲染描边 × px/side`，cell 正好约掉），
所以这里挑边长只影响图集清晰度，不影响观感里的线粗。ss 一律留 1，超采样那条路别走。
"""

import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy

L, W, T = 1.50, 0.74, 0.44      # 单颗 长 / 宽(x) / 厚(y)。宽度有下限：描边按屏幕像素画，
                                # 太瘦的零件会被自己那两条边吃光（见上表五颗瘦那一版）
NU, NV = 20, 18                 # 环向 / 纵向段数
RIDGE_HALF = 8.0                # 脊线半角（度）。10° 渲出来是一大块浅色楔形，读成高光
RIDGE_T0, RIDGE_T1 = 0.14, 0.90

init()
mat('shell', '#6b5136')
ridge_m = mat('ridge', '#ae9570')   # 比矢量版的 50% 浅色叠加深一档：渲染会再往白里抬


def prof(t):
    """纵剖半宽：t=0 尖头，t≈0.76 最宽，t=1 收成圆钝的大头。"""
    return (t ** 0.9) * max(0.0, 1.0 - t ** 3) ** 0.45


FMAX = max(prof(i / 400.0) for i in range(401))


def one_seed(name):
    """一颗瓜子：长轴 Z，脊线朝 ±y（宽面）。"""
    verts, faces, fmat = [(0.0, 0.0, -L / 2)], [], []
    for j in range(1, NV - 1):
        t = j / (NV - 1.0)
        k = prof(t) / FMAX
        for i in range(NU):
            ang = i * 2 * math.pi / NU
            verts.append((W / 2 * k * math.cos(ang), T / 2 * k * math.sin(ang), -L / 2 + L * t))
    verts.append((0.0, 0.0, L / 2))
    TOP = len(verts) - 1

    def vid(j, i):
        return 1 + (j - 1) * NU + i % NU

    def is_ridge(j, i):
        t = (j + 0.5) / (NV - 1.0)
        if not (RIDGE_T0 <= t <= RIDGE_T1):
            return False
        a = math.degrees((i + 0.5) * 2 * math.pi / NU)
        return min(abs(a - 90.0), abs(a - 270.0)) <= RIDGE_HALF

    for i in range(NU):                                   # 尖头扇面
        faces.append((0, vid(1, i + 1), vid(1, i))); fmat.append(0)
    for j in range(1, NV - 2):                            # 中段四边形
        for i in range(NU):
            faces.append((vid(j, i), vid(j, i + 1), vid(j + 1, i + 1), vid(j + 1, i)))
            fmat.append(1 if is_ridge(j, i) else 0)
    for i in range(NU):                                   # 大头扇面
        faces.append((TOP, vid(NV - 2, i), vid(NV - 2, i + 1))); fmat.append(0)

    ob = add_mesh(name, verts, faces, 'shell')
    ob.data.materials.append(ridge_m)
    for p, m in zip(ob.data.polygons, fmat):
        p.material_index = m
    return ob


# 五颗的摆位：(中心, 绕Z旋, 绕Y倒)。中心那颗横躺着当底、另外四颗斜插在它上面，
# 交叉着压不顺着压。中心已经按 ×1.45 摊开过（见上面"摊开一点比挤成团好"）。
GOLD = 2.39996
PLACE = [
    (( 0.000, -0.174,  0.029), 0.00,     1.48),   # 底下横躺的一颗，另外四颗压在它上面
    ((-0.203,  0.261,  0.290), GOLD * 1, 1.02),
    (( 0.261, -0.348,  0.145), GOLD * 2, 2.05),
    (( 0.000,  0.377, -0.377), GOLD * 3, 0.55),
    ((-0.348, -0.116, -0.203), GOLD * 4, 1.78),
]
obs = []
for k, (pos, rz, ry) in enumerate(PLACE):
    ob = one_seed('seed%d' % k)
    ob.matrix_world = (Matrix.Translation(pos)
                       @ Matrix.Rotation(rz, 4, 'Z')
                       @ Matrix.Rotation(ry, 4, 'Y'))
    obs.append(ob)

# 整撮归一到 NOMINAL：量所有顶点的世界坐标包围盒，按最长边缩
lo = [1e9] * 3
hi = [-1e9] * 3
for ob in obs:
    for v in ob.data.vertices:
        w = ob.matrix_world @ v.co
        for i in range(3):
            lo[i], hi[i] = min(lo[i], w[i]), max(hi[i], w[i])
s = NOMINAL / max(hi[i] - lo[i] for i in range(3))
for ob in obs:
    ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0)) @ ob.matrix_world

render_turntable('seed', active=obs[0], lean=50, tilt=0.25, roll=0.15, screen_r=21)
