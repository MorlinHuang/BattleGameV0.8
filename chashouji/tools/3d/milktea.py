"""奶茶（档 3，男方/灭迹党）—— 矢量版见 web/ammo.js 的 ITEM.milktea，配色照搬。

形状结论（改形先看这几条）：
- 轮廓必须**收拢**。对面那件是玫瑰花束（放射发散），两件飞在半空时观众只看得到
  纯色剪影，一个发散一个收拢才分得开。所以除了吸管，不让任何东西横着伸出去。
- 吸管是识别点，3D 版比矢量版吃亏：杯子不透明，插在杯里那半截看不见了。矢量版
  是把整根吸管画在杯子**上面**的，照抄长度会只剩一个小揪揪。所以露在封膜外面
  那一截要按"杯高的一半"给，不是按矢量版的比例给。
- 杯底那层珍珠做成**开口环带**贴在杯壁外面：开口网格只有 border 边，吃 1.1 的细线
  档。做成闭合圆台的话上沿会吃到 2.6 的外轮廓线，一条黑杠横在杯子中间。
- 再补一片珍珠色底盘：圆台从正底看的投影是它最宽处那个圆，杯底那一帧要是只剩
  一个空奶茶色圆就白翻了。
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Matrix
import bpy

init()
mat('tea',   '#efb877')   # 杯身奶茶色（矢量版 e8c9a0；这套灯打上去亮面会冲白，
                          #              不加一档暖黄就读成灰纸杯）
mat('pearl', '#4a3324')   # 珍珠
mat('film',  '#f7e6cf')   # 封膜
mat('straw', '#ff8fb8')   # 吸管

SEG = 26
RB, RT = 0.48, 0.68        # 杯底 / 杯口半径：上宽下窄
Z0, Z1 = -0.78, 0.58       # 杯身上下沿


def rad_at(z):
    return RB + (z - Z0) / (Z1 - Z0) * (RT - RB)


def band(name, z0, z1, matname, off=0.008, seg=SEG):
    """贴着杯壁的开口环带：只有侧壁没有盖，上下沿是 border → 细线。"""
    verts, faces = [], []
    for zz in (z0, z1):
        rr = rad_at(zz) + off
        for i in range(seg):
            a = i * 2 * math.pi / seg
            verts.append((math.cos(a) * rr, math.sin(a) * rr, zz))
    for i in range(seg):
        n = (i + 1) % seg
        faces.append((i, n, seg + n, seg + i))
    return add_mesh(name, verts, faces, matname)


def disc(name, z, r, matname, seg=SEG):
    """朝下的平圆盘。倒着绕一圈，法线才朝 -Z。"""
    verts = [(math.cos(-i * 2 * math.pi / seg) * r,
              math.sin(-i * 2 * math.pi / seg) * r, z) for i in range(seg)]
    return add_mesh(name, verts, [tuple(range(seg))], matname)


# 杯身：上宽下窄的圆台
cup = prim('cone', 'tea', vertices=SEG, radius1=RB, radius2=RT,
           depth=Z1 - Z0, location=(0, 0, (Z0 + Z1) / 2))

# 杯底珍珠：环带 + 底盘
band('pearls', Z0 - 0.006, -0.40, 'pearl')
disc('pearl_bottom', Z0 - 0.007, RB + 0.008, 'pearl')

# 封膜：压在杯口上、比杯口再宽一点的薄饼，边沿那圈就是热封的卷边
prim('cylinder', 'film', vertices=SEG, radius=RT + 0.04, depth=0.13,
     location=(0, 0, Z1 + 0.055))

# 吸管：斜插。倾角 0.40rad 往左上，跟矢量版同向；粗到 0.13 半径，
# 观众端只有几十像素，细了直接消失
TILT_S, LEN = 0.42, 1.18
d = (-math.sin(TILT_S), 0.0, math.cos(TILT_S))
base = (0.26, 0.0, 0.40)
mid = tuple(base[i] + d[i] * LEN / 2 for i in range(3))
straw = prim('cylinder', 'straw', vertices=14, radius=0.15, depth=LEN, location=mid)
straw.rotation_euler = (0, TILT_S * -1, 0)   # 绕 Y 负向 = 顶端往 -X 倒

# 转轴选 Z（绕杯子自己的竖轴转，像转盘上的杯子），不是默认的 X 翻滚。
# 依据是"内容朝哪些方向分布"：奶茶杯有天然正立方向，识别点（吸管、杯口、杯底那圈珍珠）
# 绕竖轴均匀分布，绕 Z 转就是杯子始终正立、吸管绕着转一圈但一帧不缺。
# 绕 X 翻滚会转到杯底朝前（只剩一个深棕圆盘）和正背面（没有吸管的圆柱，读成咖啡杯），
# 实测 8 个角度里只有 2 个读得出是奶茶。符号性 > 体积感。
#
# axis='Z' 时 tilt/roll 的含义跟着变（tilt 永远加在 (idx+1)%3 上）：
#   tilt -> 绕 X = 俯仰（看到一点杯口/杯底），roll -> 绕 Y=相机轴 = 屏幕内侧倾。
# 两个都在 Rz 里面，所以会随转角进动（杯子边转边点头），小幅度正好当飞行姿态。
render_turntable('milktea', active=cup, tilt=0.30, roll=0.30, axis='Z')
