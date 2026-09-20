"""抱枕（档 2，查岗党）—— 圆角方枕 + 缝线 + 两点兔耳。

照搬 ammo.js ITEM.pillow：2r × 1.68r 的圆角方（圆角 0.4r）、内缩一圈缝线、
两枚竖椭圆当兔耳。

五条形状结论（第二条、第三条是第一轮渲出来才发现的）：

- **体积感的主尺是"剥掉外轮廓之后里面还剩多少描边"。** 上一版抱枕这个数只有 4%，
  八件最低（花束 46%）—— 缝线和兔耳全是材质分区，而**材质分区不产生任何描边**，
  剥掉外轮廓之后里面是空的，转起来自然没有体积感。这一版补的全是真几何：
  **一块缩到轮廓 75.5% 的枕面板**（边正好顶着缝线内缘，周长 300 屏幕px，
  是整件最长的一条内部结构线）+ **四块贴在上面的拼布**，而且**两面都做**
  （抱枕能给到 lean=90 全靠两面对称，上一版只贴了正面，翻过去十几帧是光板）。
  密度 4% → 24%、屏幕结构量 7 → 42（tools/3d/measure_volume.py，36 帧）。
- **主体再压深一档到 #e9b6cf。** 抱枕的明暗反差只有 8%，八件最低：白色物体在这套
  明亮灯光下本来就没有明暗，再加上描边反差不够，它连第二条线索都没有。
- **直边要凹、四角要鼓。** 填充物把角撑出去，直边就被拽得凹进来 —— 这条凹弧是
  "软"的全部来源。但第一轮给到 0.052/0.060 渲出来是个四角星，一眼读不出抱枕；
  现在压到 0.020/0.024，凹得出来又不喧宾夺主。
- **不许给四角单独加厚。** 第一轮试过"角上的经线厚 20%"，结果圆角和直边的交界
  变成一道折痕，Freestyle 在掠射角上把它当可见轮廓描了出来 —— 正面那八条从中心
  放射出去的黑线就是它。软硬过渡只能靠外轮廓形状和经线指数，不能靠局部加厚：
  **任何 C0 不连续的地方都会长出一条描边。**
- **正面要平，中心再微微塌一点。** 经线用超椭圆（指数 3.4）而不是圆：从边缘滚上来
  以后很快接近满厚度，中间一大片是平的；正中再压 7% 做出"被压过"的窝。
  纯半圆经线就是个气球，那是塑料感的来源。
- **转轴给到 lean=90（等于绕屏幕横轴翻跟头），这是四件里最大的一档。** lean 是转轴
  从视线轴往屏幕横轴偏的度数，0 就是上一版那种纯屏幕内旋转 —— 物体自身根本没转，
  36 帧是同一姿态的 36 个副本，一张 2D 贴纸在打旋。抱枕反直觉的地方在于**越大越好**：
  12 帧快测了 50/65/75/90 四档（/tmp/q_pl_big.png、/tmp/q_pl2.png），不可读的"侧沿帧"
  依次是 5 / 3 / 4 / 2 帧。因为扁平件绕任何斜轴都必然扫过一次侧沿，lean 决定的是
  **在侧沿上停留多久**：正面偏角随 θ 走 cos(angle)=cos²a+sin²a·cosθ，a 越小这条曲线
  在 90° 附近越平（磨蹭），a=90 时它退化成 angle=θ，一穿而过。
  抱枕两面对称（缝线兔耳都贴在两面上），翻过去还是抱枕，所以没有"翻到背面就丢题材"
  的代价 —— 手柄不能这么干，它的内容只在正面。
  tilt/roll 在 lean 模式下是固定姿态偏置：给到 0.55/0.45 比 0.30/0.25 多 1 帧可读，
  而且转出了"能看见顶面"的 3/4 角，体积感最足。
- **缝线和兔耳用材质分区，不做凸起几何 —— 不是偷懒，是放不下。** 描边在观众
  屏幕上恒 2.8px，抱枕 1 单位 = 56px，所以 W=0.05 单位、两个零件的边挨得近于
  2W=0.10 单位就连成粗黑带。兔耳要是做成压在拼布块顶面的真几何，按这条算下来
  只剩 0.042 × 0.067 单位（4.7 × 7.5 屏幕px），而它自己的描边就 2.8px —— 渲出来
  是个黑圈里一点粉，比材质分区的粉椭圆还难认（实渲对比在 /tmp/retry.png）。
  缝线同理：凸起会被描一圈黑边，观众端 130px 上就是一圈脏线。
- 主体保持粉白、可见度靠外轮廓那 2.8px 描边撑住。素材色比矢量版的
  #fdf2f6 深两档是**为了渲出来一样**：公共灯光往每个通道加一大份白，
  #fdf2f6 实测渲成 (222,220,221) 的中性灰，粉味被洗干净了。

跑：blender -b --python pillow.py -- 36 227 128 <out> 1
    pack_atlas.py <帧目录> pillow_atlas.webp --cell 160

    **渲染边长按并集占比反推，就这一条**（理由见 gamepad.py 同一段）：描边宽度
    现在跟渲染边长无关，res 只管图集分辨率，`res = 单格边长 / 并集占比`。
    抱枕的并集占比 0.705，160/0.705 = 227，渲出来并集正好 160，cell 取 160。
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

A, C, RAD = 1.00, 0.84, 0.42   # 半宽 / 半高 / 圆角，比例照搬矢量版 1 : 0.84
THICK     = 0.34               # 半厚。翻到侧面剪影仍有 2.0 × 0.68，不会薄成一条
N, M      = 128, 30            # 轮廓点数 / 单面经线环数（兔耳要这个密度才不是锯齿块）
PINCH_X, PINCH_Z = 0.020, 0.024
SEAM_LO, SEAM_HI = 0.755, 0.825   # 缝线落在轮廓的 ~79%，对上矢量版内缩的那一圈
EAR_X, EAR_Z, EAR_RX, EAR_RZ = 0.26, 0.16, 0.135, 0.30

init()
mat('body', '#e9b6cf')              # 比上一版再压深一档：见开头"明暗反差八件最低"那一条
seam_m   = mat('seam',   '#ff86b4')
ear_m    = mat('ear',    '#f4589b')  # 兔耳压深：贴在浅拼布上，只差一档看不出来
corner_m = mat('corner', '#ffa8c9')  # 四角角标
patch_m  = mat('patch',  '#fbe2ee')  # 拼布：浅的那一格
patch2_m = mat('patch2', '#f5d3e4')  # 拼布：深的那一格，棋盘交替


def _resample(pts, n, closed):
    d = [0.0]
    for i in range(1, len(pts)):
        d.append(d[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    out, j = [], 0
    for k in range(n if closed else n + 1):
        tg = d[-1] * k / n
        while j < len(d) - 2 and d[j + 1] < tg:
            j += 1
        seg = d[j + 1] - d[j]
        u = 0.0 if seg < 1e-12 else (tg - d[j]) / seg
        a, b = pts[j], pts[j + 1]
        out.append(tuple(a[m] + (b[m] - a[m]) * u for m in range(len(a))))
    return out


def rrect(a, c, rad, n, px, pz):
    """等弧长采样的圆角矩形轮廓（XZ 平面）。直边中点往里压 px/pz。"""
    ax, cz, K, d = a - rad, c - rad, 24, []

    def arc(cx, cy, a0):
        for k in range(K + 1):
            t = a0 + k / K * math.pi / 2
            d.append((cx + rad * math.cos(t), cy + rad * math.sin(t)))

    def edge(p0, p1, ax_, amt):
        for k in range(K + 1):
            s = k / K
            x = p0[0] + (p1[0] - p0[0]) * s
            z = p0[1] + (p1[1] - p0[1]) * s
            dd = amt * math.sin(math.pi * s)
            if ax_ == 'x':
                x -= math.copysign(dd, x)
            else:
                z -= math.copysign(dd, z)
            d.append((x, z))

    edge((a, -cz), (a, cz), 'x', px);   arc(ax, cz, 0.0)
    edge((ax, c), (-ax, c), 'z', pz);   arc(-ax, cz, math.pi / 2)
    edge((-a, cz), (-a, -cz), 'x', px); arc(-ax, -cz, math.pi)
    edge((-ax, -c), (ax, -c), 'z', pz); arc(ax, -cz, 3 * math.pi / 2)
    d.append(d[0])
    return _resample(d, n, True)


def meridian(m, ea, eb, t, ref):
    """赤道 (s=1, y=0) 到极点 (s=0, y=1) 的超椭圆经线，按**弧长**均分成 m 段。
       按参数均分会让赤道那一圈只剩一两个面，边缘就滚不起来。"""
    fine, p = 600, []
    for i in range(fine + 1):
        u = i / fine * math.pi / 2
        p.append((math.cos(u) ** ea * ref, math.sin(u) ** eb * t))
    out = _resample(p, m, False)
    out[0], out[-1] = (ref, 0.0), (0.0, t)
    return [(x / ref, y / t) for x, y in out]


OUT = rrect(A, C, RAD, N, PINCH_X, PINCH_Z)
MER = meridian(M, 0.833, 0.588, THICK, A)     # 指数 2.4 / 3.4：方一点、正面平一点


def dimple(s):
    """正中压 7%：抱枕不是气球，中间总有个被压过的窝。"""
    return 1.0 - 0.07 * math.exp(-(s / 0.42) ** 2)


def P(x, y, z):
    """绕 Y 转 -90°：建模时的长边 X 摆成 object-Z，抱枕在画面里是竖着的。

    lean=90 的转轴就是屏幕横轴，长边竖着意味着它会扫过视线方向 —— 扁平件的侧沿帧
    躲不掉（横着摆只是把侧沿帧的条从 1.68 换成 2.0，一样是条）。竖着摆换来的是
    跟手柄的剪影彻底分开：抱枕 1.68 宽 × 2.0 高的竖方块，手柄 2.0 × 0.96 的横条。"""
    return (-z, y, x)


verts = [P(x, 0.0, z) for x, z in OUT]         # 赤道，两面共用
ring = {}
for sgn in (1, -1):
    for k in range(1, M):
        s, y = MER[k]
        ring[(sgn, k)] = len(verts)
        for x, z in OUT:
            verts.append(P(s * x, sgn * y * THICK * dimple(s), s * z))
    ring[(sgn, M)] = len(verts)
    verts.append(P(0.0, sgn * THICK * dimple(0.0), 0.0))


def vid(sgn, k, i):
    return i % N if k == 0 else ring[(sgn, k)] + (i % N if k < M else 0)


def face_mat(k, i):
    """面心的正面坐标 → 缝线 / 四角角标 / 本体，全是同一块网格上的材质分区。

    兔耳从这里挪走了 —— 它现在画在左右两块拼布上（见下面 patch 的 pick）：
    拼布是独立凸块，压在主体上，画在主体上的兔耳会被盖掉一半。"""
    s = (MER[k][0] + MER[k + 1][0]) / 2
    ox = (OUT[i % N][0] + OUT[(i + 1) % N][0]) / 2 * s
    oz = (OUT[i % N][1] + OUT[(i + 1) % N][1]) / 2 * s
    if SEAM_LO <= s <= SEAM_HI:
        return 1
    if abs(ox) > 0.60 * A and abs(oz) > 0.46 * C:
        return 3                                  # 四角角标：缝在角上的小布片
    return 0


faces, fmat = [], []
for sgn in (1, -1):
    for k in range(M):
        for i in range(N):
            a, b = vid(sgn, k, i), vid(sgn, k, i + 1)
            c, d = vid(sgn, k + 1, i + 1), vid(sgn, k + 1, i)
            if k == M - 1:                       # 极点退化成一个顶点
                faces.append((a, d, b) if sgn > 0 else (a, b, d))
            else:
                faces.append((a, d, c, b) if sgn > 0 else (a, b, c, d))
            fmat.append(face_mat(k, i))

ob = add_mesh('pillow', verts, faces, 'body')
for m in (seam_m, ear_m, corner_m):
    ob.data.materials.append(m)
for p, m in zip(ob.data.polygons, fmat):
    p.material_index = m


# ============ 拼布分块：这件东西的内部结构全在这儿 ============
# 上一版的抱枕剥掉外轮廓之后内部结构密度只有 4%（八件最低，花束 46%）——
# 缝线和兔耳都是材质分区，材质分区**不产生任何描边**，所以里面是空的。
# 结构只能来自真几何：四块压在枕面上的独立凸块，块与块之间留真的缝。
#
# 块为什么这么小（0.31 × 0.37 单位 = 屏幕 17 × 21px）：屏幕描边恒 2.8px = 0.05
# 单位，两条边挨得近于 2W=0.10 单位就连成一条粗黑带。
PATCH_A, PATCH_C, PATCH_R = 0.155, 0.185, 0.115  # 半宽(世界x) / 半高(世界z) / 圆角
# 圆角给到 0.115（半宽的 74%）：0.09 的时候四块方方正正，整件读成一块华夫饼而不是
# 抱枕。抱枕的软全在圆角上，贴在上面的拼布块也得跟着圆。
# **块心往里收了 0.04，块间缝从 0.20 收到 0.11。** 卡住这四块的不是"块与块之间
# 的缝"（那道缝原来 0.20 单位，是 2W=0.10 的两倍，宽得很用不完），而是**块的外角
# 到内圈绗缝线的距离**：上一版块角落在 (0.40, 0.46)，到 FACE_S2=0.60 那一圈的
# 有向距离只有 0.066 单位（3.7屏幕px），比 2W 还窄 —— 角和圈的两条描边在那儿
# 连成了黑疙瘩。缝收窄腾出来的余量只能往**内**用（块心内移），不能往外放大块：
# 一放大块角就顶到内圈。收到块心 (0.21, 0.24)、半径 (0.155, 0.185) 之后，
# 块角到内圈 0.115、块间缝 0.11，两头都过线。
PATCH_CX, PATCH_CZ = 0.21, 0.24                  # 块心 → 块间缝 0.11 单位（6.2px）
PATCH_D, PATCH_SINK = 0.072, 0.13                # 凸起 / 扎进枕体多深
FACE_S, FACE_D = 0.755, 0.034                    # 枕面板：缩到轮廓的 75.5%，正好顶着缝线内缘
FACE_S2 = 0.60                                   # 面板里再压一圈内框（绗缝的第二道）


def surf_y(X, Z, sgn=-1):
    """枕面在世界 (X, Z) 处的 y。建模坐标经 P 转过 90°，这里转回去再查经线。"""
    ox, oz = Z, -X
    ang = math.atan2(oz, ox)
    p = min(OUT, key=lambda q: abs(((math.atan2(q[1], q[0]) - ang + math.pi)
                                    % (2 * math.pi)) - math.pi))
    rr = math.hypot(p[0], p[1])
    s = min(1.0, math.hypot(ox, oz) / max(1e-9, rr))
    for k in range(len(MER) - 1):
        if MER[k][0] >= s >= MER[k + 1][0]:
            u = (MER[k][0] - s) / max(1e-9, MER[k][0] - MER[k + 1][0])
            y = MER[k][1] + (MER[k + 1][1] - MER[k][1]) * u
            return sgn * y * THICK * dimple(s)
    return sgn * THICK * dimple(0.0)


def recalc(o):
    """把法线统一朝外。凸块是手写的面表，绕向写反的话 Toon 会把整块涂成暗面，
       Freestyle 的可见轮廓也跟着错位。"""
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')


def rr_poly(cx, cz, a, b, rad, n=64):
    ax, bz, K, p = a - rad, b - rad, 10, []
    for cnr, a0 in (((ax, bz), 0.0), ((-ax, bz), math.pi / 2),
                    ((-ax, -bz), math.pi), ((ax, -bz), 3 * math.pi / 2)):
        for k in range(K + 1):
            t = a0 + k / K * math.pi / 2
            p.append((cx + cnr[0] + rad * math.cos(t), cz + cnr[1] + rad * math.sin(t)))
    return _resample(p + [p[0]], n, True)


def slab(poly, depth, matname, name, sink, sgn=-1, taper=0.010, rings=5, extra=None, pick=None):
    """把一条闭合轮廓贴着枕面挤成一块凸块：顶面跟着枕面走、直壁扎进枕体。

    顶面轮廓比底面**外扩** taper，侧壁做成微微悬挑 —— 垂直壁在正视时法向正好
    垂直于视线，前后朝向符号不定，Freestyle 一帧描一帧不描地闪。
    底面沉进枕体 sink，不让两个面在接触圈附近相切（相切会长出一圈小黑睫毛）。
    顶面按同心环细分而不是拉扇形，扇形的三角又长又尖，兔耳那块材质分区画不准。

    （跟 gamepad.py 里那份是同一套工具。公共框架 common.py 不许改，
      两件各带一份比让它们互相 import 稳妥。）"""
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cz = sum(p[1] for p in poly) / n
    vs, fs, fm, idx = [], [], [], {}
    for r in range(rings):
        t = 1.0 - r / rings
        idx[r] = len(vs)
        for x, z in poly:
            px, pz = cx + (x - cx) * t, cz + (z - cz) * t
            dx, dz = px - cx, pz - cz
            L = math.hypot(dx, dz) or 1.0
            vs.append((px + dx / L * taper * t, surf_y(px, pz, sgn) + sgn * depth,
                       pz + dz / L * taper * t))
    vs.append((cx, surf_y(cx, cz, sgn) + sgn * depth, cz)); TC = len(vs) - 1
    B0 = len(vs)
    for x, z in poly:
        vs.append((x, surf_y(x, z, sgn) - sgn * sink, z))
    vs.append((cx, surf_y(cx, cz, sgn) - sgn * sink, cz)); BC = len(vs) - 1
    for r in range(rings):
        t0, t1 = 1.0 - r / rings, 1.0 - (r + 1) / rings
        for i in range(n):
            j = (i + 1) % n
            mx = cx + (poly[i][0] - cx) * (t0 + t1) / 2
            mz = cz + (poly[i][1] - cz) * (t0 + t1) / 2
            if r == rings - 1:
                fs.append((idx[r] + i, idx[r] + j, TC))
            else:
                fs.append((idx[r] + i, idx[r] + j, idx[r + 1] + j, idx[r + 1] + i))
            fm.append(pick(mx, mz) if pick else 0)
    for i in range(n):
        j = (i + 1) % n
        fs.append((B0 + j, B0 + i, BC)); fm.append(0)
    for i in range(n):
        j = (i + 1) % n
        fs.append((idx[0] + i, B0 + i, B0 + j, idx[0] + j)); fm.append(0)
    o = add_mesh(name, vs, fs, matname)
    for m in (extra or []):
        o.data.materials.append(m)
    if pick:
        for p, m in zip(o.data.polygons, fm):
            p.material_index = m
    recalc(o)
    return o


# 兔耳：上面两块各一枚竖椭圆，材质分区画在块顶面上，不多一条描边。
# 上一版画成"一块上并排两只小耳朵"，每只才 6px，在 112px 的抱枕上整个糊没了。
EAR_W, EAR_H = 0.105, 0.135


def ear_pick(cx, cz):
    def f(x, z):
        return 1 if ((x - cx) / EAR_W) ** 2 + ((z - cz) / EAR_H) ** 2 < 1.0 else 0
    return f


# **两面都要做**。抱枕能给到 lean=90 全靠两面对称，上一版只在正面贴了拼布，
# 翻过去那十几帧背面是一块光板，密度全丢在那儿。
#
# 先铺一块"枕面板"：把轮廓缩到 75.5% 挤成一整块凸台，它的边正好顶着缝线内缘 ——
# 这一条线周长 300 屏幕px，是整件里最长的一条内部结构线，比四块拼布加起来还长。
# 缝线本身留在主体上当材质分区（判据要数那一圈粉），面板压不到它。
# 两圈：外圈顶着缝线内缘，内圈再压一道（真抱枕的绗缝也是一圈套一圈）。
# 两圈之间留 0.13 单位(7.3px)，内圈到拼布块的最近点（块的外角）0.115 单位(6.4px)
# —— 都大于 2W=0.10，两条线之间还剩浅色，不会连成一条。
for sgn in (-1, 1):
    for tag, ss_ in (('a', FACE_S), ('b', FACE_S2)):
        slab([(-oz * ss_, ox * ss_) for ox, oz in OUT], FACE_D,
             'body', 'face%s%d' % (tag, sgn > 0), 0.10, sgn=sgn, rings=10)

for sgn in (-1, 1):
    for iz, sz in enumerate((1, -1)):
        for ix, sx in enumerate((-1, 1)):
            cx, cz = sx * PATCH_CX, sz * PATCH_CZ
            light = (ix + iz) % 2 == 0      # 棋盘交替，两格深浅差一档
            slab(rr_poly(cx, cz, PATCH_A, PATCH_C, PATCH_R), PATCH_D,
                 'patch' if light else 'patch2',
                 'patch%d%d%d' % (sgn > 0, ix, iz), PATCH_SINK, sgn=sgn,
                 extra=[ear_m], pick=ear_pick(cx, cz) if sz > 0 else None, rings=11)

render_turntable('pillow', active=ob, lean=90, tilt=0.55, roll=0.45, screen_r=56)
