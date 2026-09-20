"""瓜子壳（档 1，灭迹党）—— 深棕水滴 + 中间一道浅色脊线。

照搬 ammo.js ITEM.seed：长 2r 的水滴、深棕 #6b5136、中线一道浅色脊。
脊线颜色取矢量版 rgba(255,240,220,.5) 压在 #6b5136 上的实际结果 ≈ #b5a089。

三条形状结论：

- **脊线用材质分区，不用凸起。** 凸出来的脊会被 Freestyle 当成可见轮廓描一圈，
  在观众端 56px 上就是顺着瓜子长边的两条黑线，整颗糊成一团黑。同一块网格上
  换材质既没有 border 边也没有 crease，描边一条都不会多，脊线是干净的色块。
- **转轴必须是 Y（绕观察轴自转），不能是 X（翻面）。** 判据 3 是按整条转盘判的，
  不是按最好那几帧判的：礼物飞过来 0.65 秒要转 1.45 圈，一半帧认不出就是不合格。
  按实际绘制尺寸铺到客厅米色底上数了一遍 —— 绕 X 8 帧里有 2 帧塌成一颗小豆子，6/8；绕 Y 8/8。
  花束绕 X 翻面好用是因为它各向同性，转到哪一面都是花；瓜子是细长件，
  绕 X 会在两个相位上正对镜头，长度压到两成。
  axis='Y' 时相机沿 +Y 看，世界 Y 就是相机轴，所以 Ry(θ) 是**画面内自转**：
  姿态不变、题材永远认得出，而光源仍然钉在世界坐标里不跟着转 —— 后面这半句
  才是换 3D 真正买到的东西（矢量版 ctx.rotate 会把光影一起转走）。
  厚度靠固定的 tilt/roll 给一点 3/4 角就够，不值得拿一半可读帧去换。
  注意 tilt/roll 是按 e[(idx+1)%3] / e[(idx+2)%3] 挂上去的，跟着 axis 滚：
  axis='Y' 时 tilt 变成绕屏幕竖轴的偏航、roll 变成物体自身的俯仰，
  数值跟 axis='X' 的那套不通用，是照着出图重调的。
- **横截面做成 0.74×0.50 的饱满椭圆**（矢量版是 2r×0.66r 的扁片）。扁片在 3/4 角
  上会薄成一条线，饱满壳任何角度都是一颗豆。
- 水滴不对称：一头尖一头圆钝。对称的梭形在小尺寸上读成"一粒米"，
  尖头 + 大头才是瓜子。

跑：blender -b --python seed.py -- 36 150 128 <out> 1
    pack_atlas.py <帧目录> seed_atlas.webp --cell 96

    渲染边长 150 = 单格 96 / 并集占比 0.640。common.py 说描边宽度是
    "最终像素的绝对值"，要真做到，得让 pack_atlas 不缩放 —— 也就是
    **并集边长正好等于单格**，反推出渲染边长 = 单格 / 并集占比。
    并集占比是先渲一轮量出来的（它跟分辨率无关，只跟形状和描边有关）。
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

render_turntable('seed', active=ob, axis='Y', tilt=0.38, roll=0.14)
