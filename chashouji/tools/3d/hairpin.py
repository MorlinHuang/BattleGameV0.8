"""发卡（档 1，查岗党）—— **带齿的鸭嘴夹**，不是最早那版"一根粉棒 + 一颗珠"。

## 为什么换形体

一根光棒加一颗珠子剥掉外轮廓之后里面是空的（内部结构密度 0%、屏幕结构量 0），不管怎么转、
转多快，中间那块看上去都一样。走花束那条路：**靠零件数量堆遮挡关系**。

两个方案横着比过（同尺寸、同转轴）：

| 方案 | 结构密度 | 贴纸残 | 粉色像素 中位 / 最少 | 判断 |
|---|---|---|---|---|
| 鸭嘴夹（两片夹片 + 一排齿 + 铰点珠） | 41% | 0.51 | 1223 / 943 | **选它** |
| 蝴蝶结（两环 + 束带 + 两条带尾） | 70% | 0.71 | 一半不到 | 否掉 |

蝴蝶结的结构密度数字更高，但那是**被描边喂出来的**：密度量的是"剥掉外轮廓后里面还剩多少墨"，
糊成一团黑的东西天然得高分。看粉色像素就露馅 —— 同尺寸下只剩鸭嘴夹一半的可见粉色。
根因是**零件数除不开**：蝴蝶结要在 2.0 的框里塞两个环 + 一个结 + 两条尾，每个零件只剩
0.3~0.4 宽，而描边按屏幕绝对像素画，瘦零件会被自己那两条边吃光。

## 尺寸是被描边宽度定死的

描边 OUTLINE_W=2.8 是**观众屏幕上的像素**，而这件东西在屏幕上只有 63px、主体标称直径 44px。
夹片归一化后宽 0.66 单位 = 屏幕 14.5px，两条描边吃掉 5.6px，剩 9px 填色。实测四档：

| 夹片宽 BARW | 齿 | 结构密度 | 屏幕结构量 | 墨占实心 | 粉色像素中位 |
|---|---|---|---|---|---|
| 0.64（窄） | 3 | 41% | 16 | 67% | 1223 |
| **0.95（本版）** | **3** | **39%** | **16** | **63%** | **1485** |
| 0.95 | 3 齿距 0.64 长夹片 | 43% | 16 | 66% | — |
| 0.85 | 2 | 35% | 14 | 62% | 1556 |

夹片加宽 + 张口收窄，结构量一点没掉，墨占降了 4 个点、可见粉色多了两成 —— 同一件东西
**把零件做粗是纯赚的**，只要长轴还竖着（见下）。齿从 3 颗减到 2 颗则是纯亏：墨少 1 个点，
结构量掉 2，而"带齿"是这东西的第一识别点。

**齿距 0.42 是上一轮在 k² 粗描边下被否掉的方案，描边修好之后重试了一次**（0.42 × 4 颗齿）：
结构密度 47% vs 41%、墨占 70% vs 67%、粉色像素 1053 vs 1223 —— 密度确实涨了，但涨的是墨，
齿之间的缝在 63px 上并不成立，读成一条毛边。**不成立，维持 0.62 的齿距 × 3 颗。**

## 形状结论（改形先看这几条）

- **零件一律做粗**，可见宽度必须大于两条描边宽才留得住填色。夹片 0.95 宽、厚 0.72，齿高 0.36。
- **张口角决定宽高比，必须跟夹片长度一起调。** 张口 0.24rad 配短夹片时下沿甩出去 ±1.15，
  归一化之后变成**横着的**，"长轴竖着"那条就破了。本版夹片加宽以后同样要补偿：
  张口收到 0.13、夹片长到 z=-1.75，量出来 x2.77 × z2.88，长轴仍在竖向。
  **改 BARW 必须看脚本打印的 BBOX 那行，z 要是最大的那个。**
- **铰点压一颗浅粉珠**，既把两片咬在一起，也接上了最早那版"一端一颗珠"的配色记忆。
- **长轴保持竖着（Z）。** 细长件长轴竖着绕斜轴不会塌：转轴在 xy 平面里、长轴是 Z，
  两者永远垂直，最短投影还剩 cos(lean)=64%；横着放会转到正对镜头塌成一坨。

## 转轴与渲染边长

`lean=50, tilt=0.25, roll=0.15` 沿用量出来的档，换形体后复量过（贴纸残差 0.54，八件里最低），
没理由动。

跑：blender -b --python hairpin.py -- 36 160 128 <out> 1
    pack_atlas.py <帧目录> hairpin_atlas.webp --cell <并集>

渲染边长按 `res = 单格 / 并集占比` 反推：并集占比 0.87，要 139 的单格就渲 160。
**描边宽度与渲染边长无关**（cell 在 `屏幕描边 = 渲染描边 × px/side` 里正好约掉），
挑边长只影响图集清晰度。ss 一律留 1。
"""

import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy

init()
mat('bar',  '#ff7aab')   # 夹片
mat('bead', '#ffb8d4')   # 铰点珠

TH = 0.72        # 夹片厚度（Y，朝镜头的深度）——做成块不是片，片在 3/4 角会消失
BARW = 0.95      # 夹片本体宽度（X）
TOOTH = 0.36     # 齿高（X）
PITCH = 0.62     # 齿距（Z）。小于两条描边宽就并成一团（0.42 试过，读成毛边）
NT = 3           # 每片几颗齿
OPEN = 0.13      # 张口角（rad），绕上端铰点往两边张。加宽夹片必须同时收小它
ZBOT = -1.75     # 夹片下沿。跟 OPEN 一起把长轴保持在竖向


def slab(name, pts, th, matname):
    """XZ 平面的多边形（逆时针给点）沿 Y 挤出成块。"""
    n = len(pts)
    verts = [(x, -th / 2, z) for x, z in pts] + [(x, th / 2, z) for x, z in pts]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    return add_mesh(name, verts, faces, matname)


def jaw(name, sign):
    """一片夹片：上端铰点、下端张口，内缘自下而上 NT 颗齿。sign=+1 右片 / -1 左片。"""
    x0, ztop, zbot = 0.12, 0.74, ZBOT
    x1 = x0 + BARW
    pts = [(x0, ztop), (x1, ztop), (x1, zbot), (x0 + TOOTH * 0.3, zbot)]
    for k in range(NT):
        z0 = zbot + 0.20 + k * PITCH
        pts += [(x0 + TOOTH, z0 + 0.04), (x0, z0 + 0.24)]
    pts.append((x0, ztop - 0.36))
    pts = [(sign * x, z) for x, z in pts]
    return slab(name, pts if sign > 0 else pts[::-1], TH, 'bar')


for s, nm in ((1, 'jaw_r'), (-1, 'jaw_l')):
    ob = jaw(nm, s)
    ob.matrix_world = (Matrix.Translation((0, 0, 0.74)) @ Matrix.Rotation(-s * OPEN, 4, 'Y')
                       @ Matrix.Translation((0, 0, -0.74))) @ ob.matrix_world

prim('uv_sphere', 'bead', segments=16, ring_count=10, radius=0.38, location=(0, 0, 0.80))

# 整件归一到 NOMINAL：量所有顶点的世界坐标包围盒，按最长边缩
obs = list(bpy.data.objects)
lo, hi = [1e9] * 3, [-1e9] * 3
for ob in obs:
    for v in ob.data.vertices:
        w = ob.matrix_world @ v.co
        for i in range(3):
            lo[i], hi[i] = min(lo[i], w[i]), max(hi[i], w[i])
dim = [hi[i] - lo[i] for i in range(3)]
# 改 BARW / OPEN / ZBOT 以后盯这一行：z 必须是最大的那个，否则长轴躺倒了
print('BBOX x%.2f y%.2f z%.2f' % tuple(dim), flush=True)
s = NOMINAL / max(dim)
for ob in obs:
    ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0)) @ ob.matrix_world

render_turntable('hairpin', active=bpy.data.objects['jaw_r'],
                 lean=50, tilt=0.25, roll=0.15, screen_r=22)
