"""命中特效的粒子贴图 —— 七种形状，一个脚本按名字选。

    blender -b --python particle.py -- <帧数> <边长> <采样> <输出前缀> <超采样> <形状名>

## 为什么渲成白的

粒子颜色是**运行时逐颗定的**，而且带随机（羽毛 `i % 5 ? [252,250,250] : [250,232,236]`，
火花 `i % 4 ? EMBER : [255,238,150]`）。贴图要是带上颜色，配方就没法再调色了。

所以主体一律渲纯白：Toon 的硬边二分把它渲成"纯白亮面 + 中灰暗面"，
引擎那边用 multiply 把目标色乘上去 —— 亮面变成目标色本身、暗面变成它的暗调，
**二分光影原样保留**，这正是"有体积感"和"一个纯色几何图形"的差别。

描边不用角色线稿那个暖黑，改用中等深度的 `5a4a42`：它也会被 multiply 乘一遍，
用暖黑的话乘完直接黑死，粒子就成了一团墨点。

## 形状分两类

- **翻滚类**（feather / petal / debris）：在空中真的翻面，12 帧转盘，体积感就在这
- **符号类**（star / heart / card / pearl）：观众读的是"星星""爱心"这个符号本身，
  但它们也吃 vrot，所以同样出 12 帧 —— 有厚度的星星转起来跟一个五角形色块完全不是一回事

七种形状都做成最大尺寸 2.0 个 Blender 单位（common.py 的尺寸约定），
细长件的长边占满 2.0，短边自然就窄。
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

_A = sys.argv[sys.argv.index('--') + 1:]
SHAPE = _A[5] if len(_A) > 5 else 'petal'
# 第 7 个参数是转轴。相机架在 -Y 朝 +Y 看，所以：
#   X = 上下翻面（薄片在空中翻滚，默认）
#   Y = 屏幕平面内打转（**正面始终朝着观众**，配合 common 的固定倾角仍能看出厚度）
# 星星和爱心是**符号**，观众读的是"星星"这三个字而不是一个立体物件，
# 翻到侧面就只剩一团皱纸，符号性全没了 —— 它们走 Y。
AXIS = _A[6] if len(_A) > 6 else 'X'

init()
mat('white', '#ffffff')
# 描边也要参与 multiply 染色，暖黑乘完会黑死 —— 这里比角色线稿浅两档
import common
# 描边渲成**中性暖灰**，而不是角色线稿那个暖黑。
#
# 引擎那边是拿整张图去 multiply 染色的，描边像素也一起被乘。渲深色的话：
# 白羽毛乘白 = 描边还是那个深棕，在近白的羽毛上重得像瓜子壳；而配方原本给
# 羽毛指定的描边是浅灰紫 [138,118,122]。渲成 55% 灰之后，描边自动变成
# **主色乘 0.55**，也就是这颗粒子自己的暗调 —— 浅羽毛得到浅灰边、
# 深玫红花瓣得到暗红边，配方对描边色的控制就以另一种形式还回来了。
common.INK = '8c7d74'
# 描边宽度也要压。common 那套 2.6/1.1 是给 272px 的物品格子定的，
# 粒子格子只有 80px —— 同样的绝对宽度占比就是三倍，整颗粒子会被描边吃掉，
# 远看只剩一团深色。赛璐璐里小东西的线**相对**粗一点是对的，粗三倍不是。
common.OUTLINE_W = float(_A[7]) if len(_A) > 7 else 1.7
common.INNER_W = common.OUTLINE_W * 0.45


def sheet(w, h, curl, ridge=0.0, nu=9, nv=7, taper=2.55):
    """一片薄壳：横向卷成瓦、纵向宽度走 sin 曲线、可选中间一条脊。

    curl 是横向卷曲量 —— **薄片必须卷**，纯平面绕横轴翻到侧面那几帧只剩一条线，
    在 60fps 下就是每转半圈闪一下。卷成瓦之后任何角度都有可见面积。
    ridge>0 会把中轴抬起来，羽毛的羽轴靠它（Freestyle 的 border 线会沿脊画一道）。
    """
    verts, faces = [], []
    for j in range(nv):
        v = j / (nv - 1)
        wide = w * (0.26 + 0.74 * math.sin(v * taper))
        for i in range(nu):
            u = i / (nu - 1) * 2 - 1
            verts.append((u * wide,
                          -curl * u * u * (0.35 + v) + ridge * (1 - u * u),
                          v * h - u * u * h * 0.16))
    for j in range(nv - 1):
        for i in range(nu - 1):
            a = j * nu + i
            faces.append((a, a + 1, a + nu + 1, a + nu))
    return verts, faces


def extruded(outline, half_thick, bulge=0.0):
    """把一圈平面轮廓挤成有厚度的片，可选让上下两面鼓起来。

    bulge 是这类"符号件"体积感的来源：纯挤出是个冷冰冰的柱体，两面鼓一点
    才像一颗实心的星星/爱心。鼓的量给小 —— 给大了就滑向三维塑料感。
    """
    n = len(outline)
    verts = [(x, -half_thick, z) for x, z in outline] + \
            [(x, half_thick, z) for x, z in outline] + \
            [(0, -half_thick - bulge, 0), (0, half_thick + bulge, 0)]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))          # 侧壁
        faces.append((2 * n, j, i))                 # 底面扇
        faces.append((2 * n + 1, i + n, j + n))     # 顶面扇
    return verts, faces


def star_outline(k=5, ro=1.0, ri=0.42):
    pts = []
    for i in range(k * 2):
        a = math.pi / 2 + i * math.pi / k
        r = ro if i % 2 == 0 else ri
        pts.append((math.cos(a) * r, math.sin(a) * r))
    return pts


def heart_outline(n=26, s=0.062):
    """心形参数方程。手画贝塞尔在 3D 里不好挤，参数方程一圈点直接就能用。"""
    pts = []
    for i in range(n):
        t = i / n * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * s, y * s))
    return pts


def rounded_rect_outline(w, h, r, seg=4):
    """圆角矩形一圈点。照片卡的角是圆的，直角卡片在翻滚里读着像块砖。"""
    pts = []
    for cx, cz, a0 in ((w - r, h - r, 0), (-(w - r), h - r, math.pi / 2),
                       (-(w - r), -(h - r), math.pi), (w - r, -(h - r), 1.5 * math.pi)):
        for k in range(seg + 1):
            a = a0 + k / seg * math.pi / 2
            pts.append((cx + math.cos(a) * r, cz + math.sin(a) * r))
    return pts


# ---------------- 七种形状 ----------------
if SHAPE == 'petal':
    # 花瓣：杯状弧面，比花束上那片更舒展（它是被打散飞出来的）
    vs, fs = sheet(0.78, 1.9, 0.42)
    add_mesh('petal', vs, fs, 'white')

elif SHAPE == 'feather':
    # 羽毛：细长、卷得更狠、中轴抬起当羽轴。taper 调小让根部就开始收窄
    vs, fs = sheet(0.46, 2.0, 0.30, ridge=0.16, taper=2.2)
    add_mesh('feather', vs, fs, 'white')

elif SHAPE == 'debris':
    # 碎片：低面数球随机揉一下再压扁 —— 崩下来的东西不该是规则几何体。
    # 固定随机种子，重跑出来是同一块，不然每次重渲碎片都换个样
    random.seed(7)
    ob = prim('ico_sphere', 'white', subdivisions=1, radius=1.0)
    for v in ob.data.vertices:
        v.co *= 0.62 + random.random() * 0.55
    ob.scale = (1.0, 0.42, 0.78)

elif SHAPE == 'pearl':
    # 珍珠：略扁的球。球本身没有"角度"，但硬边二分的明暗交界会随转盘移动，
    # 连播起来就是一颗在滚的珠子，而不是一个贴死的圆点
    ob = prim('uv_sphere', 'white', segments=12, ring_count=8, radius=1.0)
    ob.scale = (1.0, 0.94, 0.96)

elif SHAPE == 'star':
    vs, fs = extruded(star_outline(), 0.13, bulge=0.15)
    add_mesh('star', vs, fs, 'white')

elif SHAPE == 'heart':
    vs, fs = extruded(heart_outline(), 0.16, bulge=0.22)
    add_mesh('heart', vs, fs, 'white')

elif SHAPE == 'card':
    # 照片卡：带厚度的圆角板 + 正面压一块略小的"相纸"，
    # 两者之间那圈落差会被 Freestyle 的 border 画成内框线，卡片就有了正反面
    vs, fs = extruded(rounded_rect_outline(0.78, 1.0, 0.16), 0.055)
    add_mesh('card', vs, fs, 'white')
    vs2, fs2 = extruded(rounded_rect_outline(0.62, 0.82, 0.08), 0.012)
    inner = add_mesh('card_face', vs2, fs2, 'white')
    inner.location = (0, -0.062, 0.04)

else:
    sys.exit('未知形状：' + SHAPE)

render_turntable(SHAPE, axis=AXIS)
