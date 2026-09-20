"""合照相框（档 4，男方/灭迹党）—— 矢量版见 web/ammo.js 的 ITEM.photo，配色照搬。

形状结论（改形先看这几条）：
- 竖长比守在 1:1.3（外框 1.54 x 2.00）。跟戒指盒的 1:0.8 差 1.6 倍，剪影才分得开。
- 相框是**扁的**，这是三件里最难的一条：纯平板绕横轴翻滚会有几帧薄得几乎看不见。
  三手一起上 ——
    ① 框做成真有厚度的矩形环柱（0.34 厚），不是一张纸；
    ② 相纸**凹进去** 0.12，转到斜角时能看到框的内壁，那一圈暗面就是体积；
    ③ 背后加一块斜撑（真实相框都有的那块支脚）。翻到正侧面时框本身只剩 0.34 宽
       的一条，全靠斜撑撑出一个三角形轮廓 —— 那一帧才还看得出是个摆件。
- 浅相纸在明亮底图上看不见，靠**加粗的深棕框**撑住可见度（规律是"靠轮廓"，
  不是"别用浅色"）。所以边框宽度给到 0.22（外框宽的 14%），木色也比矢量版压深一档。
- 里面两个小人影不画脸：这个尺寸画脸只会糊成两个点。肩线靠在一起、半身直接
  切到相纸下沿，读起来才是"一张合照"而不是"两颗豆子"。
- 人影/爱心/相纸都做成**平片**：平片只有 border 边，吃 1.1 的细线档。做成薄片体
  会各自带一圈 2.6 的外轮廓，相纸里面叠成一团黑。
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Matrix
import bpy, bmesh

init()
mat('wood',  '#a46b39')   # 外框（矢量版 b8864f，压深一档撑明亮底图）
mat('card',  '#7d5128')   # 背板：框里那块衬纸，比框再深，翻到背面不会糊成一片浅色
mat('paper', '#f0e0c0')   # 相纸（这套灯亮面冲白，矢量版 fdf6ea 照搬会读成一面镜子）
mat('figure', '#6f88ad')  # 人影（比矢量版压一档，冲白之后才还压得住相纸）
mat('heart', '#ff5f86')   # 右上角那颗心

W, H, D = 1.54, 2.00, 0.40     # 外框 宽 高 厚
BAR, REC = 0.22, 0.12          # 边框宽 / 相纸凹进去的深度
IW, IH = W - BAR * 2, H - BAR * 2
FY = -D / 2                    # 框的正面
PY = FY + REC                  # 相纸所在的平面


def fix(ob):
    """from_pydata 不管绕向，法线朝里的面在 Toon 下会死黑。闭合网格统一朝外重算。"""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def frame_ring(name, w, h, iw, ih, d, matname):
    """矩形环柱：外框 + 内框 + 前后两个面 + 内外侧壁，单一闭合网格。"""
    ox, oz, ix, iz = w / 2, h / 2, iw / 2, ih / 2
    V = []
    for y in (-d / 2, d / 2):
        V += [(-ox, y, -oz), (ox, y, -oz), (ox, y, oz), (-ox, y, oz)]
        V += [(-ix, y, -iz), (ix, y, -iz), (ix, y, iz), (-ix, y, iz)]
    F = []
    for i in range(4):
        j = (i + 1) % 4
        F.append((i, j, 4 + j, 4 + i))                  # 正面那一圈
        F.append((8 + i, 8 + j, 12 + j, 12 + i))        # 背面那一圈
        F.append((i, j, 8 + j, 8 + i))                  # 外侧壁
        F.append((4 + i, 4 + j, 12 + j, 12 + i))        # 内侧壁（凹腔的墙）
    return fix(add_mesh(name, V, F, matname))


def plate(name, hx, hz, y, matname, cx=0.0, cz=0.0):
    """XZ 平面上的矩形平片，法线朝 -Y（对着相机）。"""
    V = [(cx - hx, y, cz - hz), (cx + hx, y, cz - hz),
         (cx + hx, y, cz + hz), (cx - hx, y, cz + hz)]
    return add_mesh(name, V, [(0, 1, 2, 3)], matname)


def poly(name, pts, y, matname):
    """XZ 平面上的任意凸多边形平片（按逆时针给点，法线就朝 -Y）。"""
    V = [(x, y, z) for x, z in pts]
    return add_mesh(name, V, [tuple(range(len(V)))], matname)


def head_pts(cx, cz, r, seg=16):
    return [(cx + math.cos(i * 2 * math.pi / seg) * r,
             cz + math.sin(i * 2 * math.pi / seg) * r) for i in range(seg)]


def bust_pts(cx, cz, rx, rz, zbot, seg=14):
    """半身：上面一个圆顶，下面直接切到相纸下沿 —— 合照就是这么被框切掉的。"""
    p = [(cx + math.cos(i * math.pi / seg) * rx,
          cz + math.sin(i * math.pi / seg) * rz) for i in range(seg + 1)]
    return p + [(cx - rx, zbot), (cx + rx, zbot)]


def heart_pts(cx, cz, s, seg=22):
    p = []
    for i in range(seg):
        t = -i * 2 * math.pi / seg      # 倒着绕：心形参数式本身是顺时针，法线会朝背面
        p.append((cx + s * 16 * math.sin(t) ** 3,
                  cz + s * (13 * math.cos(t) - 5 * math.cos(2 * t)
                            - 2 * math.cos(3 * t) - math.cos(4 * t))))
    return p


# 框 + 背板（背板比内框小一丝，免得跟内侧壁共面打架）
fr = frame_ring('frame', W, H, IW, IH, D, 'wood')
# 背板后沿要**超出**框背面一丝：跟框背面齐平就是两张共面的脸，会打架闪烁
back = prim('cube', 'card', size=1)
BZ = D / 2 + 0.012
back.matrix_world = (Matrix.Translation((0, (PY + BZ) / 2, 0))
                     @ Matrix.Diagonal((IW - 0.012, BZ - PY, IH - 0.012, 1.0)))

# 相纸：凹在腔底，四边顶到内侧壁
plate('paper', IW / 2 - 0.01, IH / 2 - 0.01, PY - 0.006, 'paper')

# 两个挨在一起的人影。肩膀互相压住，所以错开一点 Y，不然共面打架、描边穿帮
for k, sx in enumerate((-1, 1)):
    y = PY - 0.016 - k * 0.012
    poly('bust%d' % k, bust_pts(sx * 0.28, -0.34, 0.30, 0.40, -(IH / 2 - 0.01)), y, 'figure')
    poly('head%d' % k, head_pts(sx * 0.28, 0.18, 0.19), y, 'figure')

# 右上角那颗小心，把"这是合照"点破
poly('heart', heart_pts(0.35, 0.58, 0.0115), PY - 0.02, 'heart')

# 背后的支脚：翻到正侧面那几帧全靠它撑出体积。
# 做成**实心楔块**，不是斜着的一块薄板 —— 薄板跟框背面之间夹出一个封闭的口袋，
# 场上只有一盏太阳 + 环境光，光进不去，那几帧就烧出一片**纯黑**（实测最高 14% 的
# 像素是 0,0,0）。这套画风里最深的颜色是描边的 3a2c26，突然出现一块纯黑会读成
# "破了个洞"，而且那是三维打光的漏子，不是赛璐璐的二分明暗。实心块没有内腔，
# 看到的永远是被照到的外表面。
# 宽度给到接近开口那么宽：窄板条在正侧面会读成"框里插了块牌子"，宽到这个程度
# 才读成"相框背后的支脚"，正侧面的剪影也才是一个实心三角。
SW, SY0, SY1, SZ0, SZ1 = 0.98, D / 2 - 0.02, D / 2 + 0.50, 0.52, -0.86


def wedge(name, hw, y0, y1, z0, z1, matname):
    """三棱柱：竖直面贴着框背（往里埋一点，不跟框背共面打架），斜面朝后下。"""
    V = []
    for x in (-hw, hw):
        V += [(x, y0, z0), (x, y0, z1), (x, y1, z1)]
    F = [(0, 1, 2), (3, 4, 5),
         (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)]
    return fix(add_mesh(name, V, F, matname))


wedge('stand', SW / 2, SY0, SY1, SZ0, SZ1, 'card')

# 转轴用 lean=40，不是绕视线轴。绕视线轴（axis='Y'）时相框正面锁死朝观众，
# 实测细长比全程只波动 9%、可见面积只波动 9% —— 整条转盘就是同一张图在平面里打旋。
# 斜轴 40°：细长比 1.21~2.48（波动 105%），可见面积最小/最大 56%，框会真的侧过去、
# 木框厚度和背后那块楔形支脚依次露出来。
# 25/35/40/45 四档实测，"人影像素少于中位数 12%"的帧数是 0/0/1/4 —— 45° 一下废 4/12（整整
# 三分之一只剩一根木条），40° 只废 1 帧，而细长比波动比 35° 多一半（105% vs 70%），所以取 40。
#
# lean 模式下 tilt/roll 是固定姿态偏置（先摆好姿势再整个绕斜轴转），不跟着转轴滚。
render_turntable('photo', active=fr, tilt=0.26, roll=0.20, lean=40, screen_r=68)