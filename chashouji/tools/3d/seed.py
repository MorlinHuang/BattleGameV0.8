"""瓜子壳（档 1，灭迹党）—— 深棕水滴 + 中间一道浅色脊线。

照搬 ammo.js ITEM.seed：长 2r 的水滴、深棕 #6b5136、中线一道浅色脊。
脊线颜色取矢量版 rgba(255,240,220,.5) 压在 #6b5136 上的实际结果 ≈ #b5a089。

三条形状结论：

- **脊线用材质分区，不用凸起。** 凸出来的脊会被 Freestyle 当成可见轮廓描一圈，
  在观众端 56px 上就是顺着瓜子长边的两条黑线，整颗糊成一团黑。同一块网格上
  换材质既没有 border 边也没有 crease，描边一条都不会多，脊线是干净的色块。
- **转轴用斜轴 lean=50，不是绕观察轴（lean=0）。** 上一版四件全是 lean=0，那是
  纯屏幕内旋转、物体自身根本没转 —— 36 帧只是同一个姿态的 36 个副本，看上去就是
  一张 2D 贴纸在打旋，3D 白渲了。lean 是转轴从视线轴往屏幕横轴偏的度数，0（贴纸）
  和 90（绕横轴翻跟头）之间连续可选。瓜子是细长件，长轴放 Z（屏幕竖向）、转轴在
  xy 平面里，两者永远垂直，投影最短剩 cos(lean)，不会像 axis='X' 那样正对镜头塌成一豆。
  12 帧快测过 35/50/65（/tmp/q_hs_big.png 第 4~6 行）：35 的脊线一直朝着观众、变化偏弱；
  65 有 3 帧缩成小豆读不出；50 长度在 100%~64% 之间伸缩，脊线在正面 → 掠过 → 转走
  之间循环，12/12 可读，定 50。**脊线转不转得走，是这件东西有没有体积感的全部证据** ——
  它朝 ±y（正对镜头）贴在宽面上，lean=0 时它永远在画面中央，看不出任何翻转。
  lean 模式下 tilt/roll 是**物体的固定姿态偏置**（先摆好姿势，再整个绕斜轴转），
  不跟着转轴滚，且两个都只能给小值：它们把长轴从屏幕竖向拽开，最短投影会更短。
- **横截面做成 0.74×0.50 的饱满椭圆**（矢量版是 2r×0.66r 的扁片）。扁片在 3/4 角
  上会薄成一条线，饱满壳任何角度都是一颗豆。
- 水滴不对称：一头尖一头圆钝。对称的梭形在小尺寸上读成"一粒米"，
  尖头 + 大头才是瓜子。

跑：blender -b --python seed.py -- 36 144 128 <out> 1
    pack_atlas.py <帧目录> seed_atlas.webp --cell 96

    渲染边长 144 = 单格 96 / 并集占比 0.667。common.py 说描边宽度是
    "最终像素的绝对值"，要真做到，得让 pack_atlas 不缩放 —— 也就是
    **并集边长正好等于单格**，反推出渲染边长 = 单格 / 并集占比。
    并集占比是先渲一轮 36 帧量出来的（它跟分辨率无关，只跟形状、转轴和描边有关，
    **换了 lean 就得重量一遍**；8 帧量会偏小，细长件尤其）。
    ss 一律留 1。common.py 的 `_freestyle(ss)` 把 ss 同时乘进了
    `render.line_thickness` 和 `linestyle.thickness`，而这两个值在 ABSOLUTE 模式下
    是**相乘**的，所以描边宽度按 ss² 长：实测同一场景 ss=1/2/3 描边 4 / 14 / 30 像素。
    ss=3 时那 30px 是绝对像素、不随渲染边长缩，发卡的棒才 0.55 单位宽，
    整根被描边吞成一条纯墨色的胶囊。common.py 不许改，所以超采样这条路直接不走：
    Cycles 每像素 128 个采样本身就带足了抗锯齿，锯齿并不是实际问题。
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

L, W, T = 2.00, 0.74, 0.50     # 长 / 宽(x) / 厚(y)。长轴放 Z 才会翻滚，见 hairpin.py
NU, NV = 24, 22                # 环向 / 纵向段数
RIDGE_HALF = 8.0               # 脊线半角（度）。10° 渲出来是一大块浅色楔形，
                               # 读成高光而不是结构线 —— 高光正是这个项目的高压线
RIDGE_T0, RIDGE_T1 = 0.14, 0.90

init()
mat('shell', '#6b5136')
ridge_m = mat('ridge', '#ae9570')   # 比矢量版的 50% 浅色叠加深一档：渲染会再往白里抬


def prof(t):
    """纵剖半宽：t=0 尖头，t≈0.76 最宽，t=1 收成圆钝的大头。"""
    return (t ** 0.9) * max(0.0, 1.0 - t ** 3) ** 0.45


FMAX = max(prof(i / 400.0) for i in range(401))

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
    """面心落在 y 极值（宽面）中线附近、且不在两头 —— 那一圈就是脊。"""
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

ob = add_mesh('seed', verts, faces, 'shell')
ob.data.materials.append(ridge_m)
for p, m in zip(ob.data.polygons, fmat):
    p.material_index = m

render_turntable('seed', active=ob, lean=50, tilt=0.25, roll=0.15)
