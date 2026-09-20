"""求婚戒指盒（档 4，女方/查岗党）—— 矢量版见 web/ammo.js 的 ITEM.ringbox，配色照搬。

形状结论（改形先看这几条）：
- **开着盖**。合着的盒子只是个方块，跟档 2 的抱枕撞剪影；掀开的盖子给了它一个
  别人没有的折角。
- 盖子和盒身必须**咬在同一条合页边上**。矢量版第一版盖子平移出去开了道缝，
  230px 宽的东西飞过去读成两个分开的粉方块。3D 版靠"绕合页边旋转"根治：
  不管开多大角，两块永远接在一起。开角 112°，再大就往后躺平、正面读不出折角了。
- 盒身挖成**带矩形凹腔的单一闭合网格**（不是实心块 + 贴上去的绒布片）：
  实心块上没法放绒布槽，戒指也就没地方坐，整件读成"盒子上摆着个圈"。
  五个方块拼的托盘也不行 —— 每块自带一圈 2.6 的外轮廓，内部叠成一团黑。
- 戒指（环 + 菱形钻）比真实比例大一圈：环外径给到盒宽的 40%。按真比例做，
  飞起来只剩"一个粉盒子"。钻用菱形，圆的会读成又一颗珠子。
- 整体宽高比收在 1:0.9 上下（盒子是横着的），跟竖长 1:1.3 的相框剪影分得开。
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Matrix
import bpy, bmesh

init()
mat('lid',    '#c1416b')   # 盖子外壳（深玫）
mat('lining', '#ffa8c4')   # 盖子内衬（矢量版 ffe6ef 在这套灯下亮面冲成白卡纸，
                           #             读成一面镜子；压两档才还是粉的）
mat('body',   '#d4527d')   # 盒身
mat('velvet', '#8f2d4f')   # 绒布槽
mat('gold',   '#ffd35a')   # 戒环
mat('gem',    '#eaf7ff')   # 钻

W, D, BH = 1.90, 1.34, 0.62    # 盒身 宽(X) 深(Y) 高(Z)
WALL, CAV = 0.17, 0.36         # 腔壁厚 / 腔深
ZTOP = -0.12                   # 盒口平面
DL, TL = 1.10, 0.26            # 盖子 深 / 厚
OPEN = -1.78                   # 开盖角（绕合页边的 X 轴转角，负=往后掀）。
                               # 112° 太躺：从背面看盖子几乎平贴着相机，整件读成两块分开的粉板。
                               # 收到 102°，盖子立起来，正面能看到内衬面、背面能看到一个直角折。


def fix(ob):
    """from_pydata 不管绕向，法线朝里的面在 Toon 下会死黑。统一朝外重算。"""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def tray(name, w, d, h, wall, cav, ztop, matname):
    """带矩形凹腔的实心盒，单一闭合网格：只在外轮廓和腔口留线。"""
    ox, oy, ix, iy = w / 2, d / 2, w / 2 - wall, d / 2 - wall
    zb, zf = ztop - h, ztop - cav
    V = ([(-ox, -oy, ztop), (ox, -oy, ztop), (ox, oy, ztop), (-ox, oy, ztop)] +
         [(-ix, -iy, ztop), (ix, -iy, ztop), (ix, iy, ztop), (-ix, iy, ztop)] +
         [(-ix, -iy, zf), (ix, -iy, zf), (ix, iy, zf), (-ix, iy, zf)] +
         [(-ox, -oy, zb), (ox, -oy, zb), (ox, oy, zb), (-ox, oy, zb)])
    F = []
    for i in range(4):
        j = (i + 1) % 4
        F.append((i, j, 4 + j, 4 + i))            # 顶面那圈边框
        F.append((4 + i, 4 + j, 8 + j, 8 + i))    # 腔壁
        F.append((12 + i, 12 + j, j, i))          # 外侧壁
    F.append((8, 9, 10, 11))                      # 腔底
    F.append((12, 13, 14, 15))                    # 盒底
    return fix(add_mesh(name, V, F, matname))


def gem_mesh(name, z_tip, z_belt, z_top, rad, matname, seg=6):
    """菱形钻：上下两个尖 + 中间一圈腰。Y 方向压扁一点，免得转到侧面变成球。"""
    V = [(0, 0, z_tip)]
    for i in range(seg):
        a = i * 2 * math.pi / seg + math.pi / seg
        V.append((math.cos(a) * rad, math.sin(a) * rad * 0.72, z_belt))
    V.append((0, 0, z_top))
    F = []
    for i in range(seg):
        j, k = i + 1, (i + 1) % seg + 1
        F.append((0, j, k))
        F.append((seg + 1, k, j))
    return fix(add_mesh(name, V, F, matname))


def quad_xy(name, hx, hy, cy, z, matname):
    """XY 平面上的平片，法线朝 -Z（盖子内衬用）。平片只有 border 边 → 细线。"""
    V = [(-hx, cy - hy, z), (-hx, cy + hy, z), (hx, cy + hy, z), (hx, cy - hy, z)]
    return add_mesh(name, V, [(0, 1, 2, 3)], matname)


# 盒身
body = tray('body', W, D, BH, WALL, CAV, ZTOP, 'body')

# 绒布槽：压扁的椭圆柱，坐在腔底，顶面刚好低于盒口
vel = prim('cylinder', 'velvet', vertices=22, radius=0.66, depth=0.32)
vel.matrix_world = (Matrix.Translation((0, 0, ZTOP - CAV + 0.16))
                    @ Matrix.Diagonal((1.0, 0.60, 1.0, 1.0)))

# 戒指：立起来的环，下半截埋进绒布里
prim('torus', 'gold', major_radius=0.42, minor_radius=0.080,
     major_segments=22, minor_segments=8,
     location=(0, 0, 0.10), rotation=(math.pi / 2, 0, 0))
gem_mesh('gem', 0.42, 0.70, 0.98, 0.31, 'gem')

# 盖子：先按"合上"的姿势建，再整体绕合页边转开
HINGE = Matrix.Translation((0, D / 2, ZTOP)) @ Matrix.Rotation(OPEN, 4, 'X') \
        @ Matrix.Translation((0, -D / 2, -ZTOP))
# 注意：不能先 .scale 再读 matrix_world —— 那时依赖图还没更新，读回来是旧矩阵。
# 一律自己拼矩阵。
lid = prim('cube', 'lid', size=1)
lid.matrix_world = (HINGE @ Matrix.Translation((0, D / 2 - DL / 2, ZTOP + TL / 2))
                    @ Matrix.Diagonal((W, DL, TL, 1.0)))
lining = quad_xy('lining', W / 2 - 0.15, DL / 2 - 0.15, D / 2 - DL / 2, ZTOP - 0.012, 'lining')
lining.matrix_world = HINGE @ lining.matrix_world

# 转轴用 lean=40，不是绕视线轴。绕视线轴（axis='Y'）正面锁死朝观众 = 贴纸打旋。
# 40° 实测是这件的最佳档：可见面积波动最大（最小/最大 53%，32°是 64%、46°是 45%但细长比反而掉），
# 细长比 1.08~1.81（波动 68%，三档里最高），而"看不见金环"的帧只有 1/12。
# 再大就翻过去看盒盖外侧，金环消失得比体积感涨得快：46° 废 2/12、55° 废 3/12。
# 盒子厚、开着盖，斜轴转起来依次看到盒内绒布槽、盒口、盒盖外侧、盒底，立体感是这三件里最足的。
#
# lean 模式下 tilt/roll 是固定姿态偏置（先摆好姿势再整个绕斜轴转），不跟着转轴滚。
render_turntable('ringbox', active=body, tilt=0.26, roll=0.20, lean=40)
