"""游戏手柄（档 2，灭迹党）—— 深色机身 + 一个青色摇杆 + 一个红色按键。

照搬 ammo.js ITEM.gamepad 的形，但机身色比矢量版亮了两档（理由见下面第二条）。

八条形状结论（第一、二条是量出来才看明白的）：

- **体积感的主尺是"剥掉外轮廓之后里面还剩多少描边"，不是转轴也不是转速。**
  上一版换了 lean、调了转速，用户还是说"不够 3D"。量出来才看明白：手柄内部结构
  密度只有 14%，花束 46% —— 花束 67 个独立零件，转起来每片花瓣的遮挡关系都在变；
  手柄就一块壳加两个点，转到哪都是一块壳。这一版正面是**双摇杆 + 十字键 +
  ABXY 底盘 + 两个肩键 + 两块握把防滑垫**、背面是**一排三块盖板 + 两块掌垫**，
  密度 15% → 26%、屏幕结构量 19 → 33（tools/3d/measure_volume.py）。

  **屏幕结构量 = 密度 × 屏幕px² / 100，而手柄的屏幕px 只有 111（八件里最小）。**
  main.js 给手柄的 GIFT.r 是 52，花束 76、奶茶 72、相框 68、戒指盒 64；px 进平方，
  所以同样的密度，手柄的结构量天然只有花束的 29%。密度这头也有天花板：
  按 g≥2W 的排布规矩（见下一条），内部填满条纹的极限是 W/(W+2W)=33%，
  实测最高的花束是 35%；而"墨占实心"要压在 45% 以下，手柄的墨占实心比密度
  高约 15 个点（外轮廓占的），于是密度实际封顶 30%、结构量封顶 36。
  **要把结构量做到 60，只能把 GIFT.gamepad.r 从 52 提到 67 左右**（main.js，
  不是这里能改的）—— 在 r=52 下"结构量≥60"和"墨占实心≤45%"互斥。
- **整件提亮两档：机身 #3d4450→#4c5566、正面 #5b6477→#6a748a、握把→#424b5c。**
  矢量版那个 #3d4450 跟描边 #3a2c26 的亮度反差只有 17%，八件最低 —— 等于描边
  白画了。更要命的是**它的暗面渲出来是 (47,59,75)，跟墨色 (58,44,38) 的距离只有
  41，比 measure_volume 判墨的阈值 46 还小**：尺子会把机身的暗面整片算成描边。
  上一版据此报的"密度 55%、墨占 65%"里有一大半是这个假阳性 —— 把墨色阈值从
  46 收到 20，那一版的墨占从 59% 掉到 34%，真描边只有一半。提亮到 #4c5566 之后
  暗面离墨色 67，尺子不再误判，同一套结构量出来是老实的 26%。
  **这不只是量得准不准：描边跟机身暗面一个色，观众那边也是看不见的。**
  提亮之后正面/侧壁/握把仍是三档材质分区，不多一条描边，剪影不变。
- **屏幕上排得下几个零件，是一道能算的题。** 描边在观众屏幕上恒定 W=2.8px
  （common.py 按 screen_r 倒推，跟渲染边长无关），手柄 1 单位 = 屏幕 52px，
  所以 W=0.0538 单位，**两个零件的边挨得近于 2W=0.108 单位就连成一条粗黑带**。
  正面横向 1.734 单位，按"4 个零件 + 3 道缝 + 2 个边距"算下来一排最多四个；
  竖向只有 0.62 单位(32px)，分不出上下两层 —— 四个凸起必须一字排开。
  十字键和 ABXY 各自试过配浅色底盘，底盘边和键边只隔 1.4px，一渲就糊，全去掉。
  **ABXY 的四个键也是这么被砍掉的**：四个分离的凸起要同时满足"外接半径≤0.155"
  和"相邻间距≥0.108"，解出来单个半径只剩 0.0326 单位（直径 3.4px），而描边就
  2.8px —— 整个凸起被描边吃光。这不是估的，是渲了 36 帧量的：**红色像素中位
  数 0，36 帧一个红点都没有**，识别色彻底消失。所以改成一块浅底盘 + 四个
  **材质分区**的色点 —— 材质分区不产生任何描边，不占间隙预算，颜色照样把
  "四个键"说清楚。色点半径第一版 0.05 时红色中位只有 13 个像素、两帧是 0，
  放大到 0.072 才稳（现在 36 帧最小 24 个，0 废帧）。
- **机身 + 两只握把是一块网格，不是三个物体叠出来的。** 第一轮把握把做成两颗独立
  椭球插进机身，两个面在交界处几乎相切，Freestyle 的可见轮廓在这一带来回跳，
  渲出来整条边是毛的。现在改成把"圆角条 ∪ 两根胶囊"当成一个 2D 有向距离场，
  沿射线找最外侧的边界点取出一条闭合外轮廓再放样 —— 一块封闭网格，
  轮廓是一条干净的线。
- **机身本体不做腰。** 第一轮给上下边中段各内收 0.055，加上两端的握把，
  剪影读成一根哑铃/骨头。腰交给握把之间那道天然的凹口，机身自己保持平直。
- **转轴用斜轴 lean=35 配一个大 roll=0.90，不是绕观察轴（lean=0）。** lean 是转轴从
  视线轴往屏幕横轴偏的度数，0 就是上一版那种纯屏幕内旋转 —— 物体自身根本没转，
  36 帧是同一姿态的 36 个副本，一张 2D 贴纸在打旋。手柄的内容只在正面（摇杆 + 按键），
  正面转过 180° 偏 2*lean，所以 lean 不能大：35 时最多偏到 70°，还是斜看着的手柄。
  **真正的坑是长轴跟转轴的夹角，不是 lean 本身。** 手柄长轴是屏幕横向，而转轴的屏幕
  投影也是横向，两者夹角只有 lean —— 长轴会扫到正对镜头，投影最短只剩
  1-sin(2·lean) 方向上的那点，lean=35 时是 34%，剪影收成一团。roll 绕视线轴，
  是把整个手柄在画面内斜过来，长轴和转轴的夹角就打开了：roll=0.90（51.6°）把最短投影
  抬到 56%。12 帧快测了 (35,r.20)/(35,r.62)/(35,r.90)/(30,r.90)/(40,r.75)
  （/tmp/q_gp_big.png、/tmp/q_gp2.png），最窄那两帧依次是"一团"→"能看出两端凸起"→
  "能看出摇杆和按键"，定 (35, 0.26, 0.90)。
  代价是背壳那两坨鼓包不再有正对背面的帧 —— 它们改为只在 3/4 角的外轮廓上鼓出来。
  拿"能认出是手柄"换"能看清背壳"，这笔是划算的。
- **正面平、背面鼓、背面在握把处再鼓一块。** 背面厚度乘一个以握把中轴为中心的
  高斯包（C∞ 的，不会长出折痕，理由见 pillow.py 第二条），翻到背面那十来帧
  看到的是拱背 + 两坨鼓包。抱枕高 1.68 是方的、手柄高 1.03 是横条，
  再加这两坨，两件档 2 的剪影彻底分得开。
- **摇杆和按键做成真的凸起，让 Freestyle 描上边。** 跟抱枕的缝线正好相反：
  那是"面上的花纹"（描边只会添乱），这是"面上支出来的东西"（描边就是它的存在感）。
  但**凸起的壁必须是斜的**：第一版摇杆是根直筒，正视时壁的法向正好垂直于视线，
  Freestyle 一条线都不画 —— 摇杆渲出来是一坨没有轮廓的浅蓝，对密度的贡献是零。
  现在做成蘑菇形（底盘 0.94r → 收腰 0.78r → 帽檐 1.00r，高 0.232），
  帽檐和底盘各是一条独立轮廓。同一件事 slab 的 taper 早就踩过。
- 整体高宽比压回矢量版的 1:0.48 —— 握把弧度正是它区别于圆角条的地方，
  但下摆不能长，长了读成靴子。

跑：blender -b --python gamepad.py -- 36 248 128 <out> 1
    pack_atlas.py <帧目录> gamepad_atlas.webp --cell 160

    **渲染边长按并集占比反推，就这一条。** common.py 把 `render.line_thickness`
    固定成 1.0、宽度只从 `linestyle.thickness` 一个入口进之后，描边在观众屏幕上
    恒定 2.8px，**跟渲染边长彻底无关**；res 回归它唯一的职责 —— 定图集分辨率：

        res = 单格边长 / 并集占比

    手柄的并集占比 0.645（先随便渲一轮量出来），档 2 的单格是 160，
    160/0.645 = 248。渲出来并集正好 160，cell 取 160，一比一不重采样。
    （历史坑：上一版 res 要在"内部线太细量不出"和"外轮廓糊死"之间找平衡，
    那是因为当时两个线宽入口都乘了倍率 k、线宽按 k² 跟着 res 涨。已由 owner
    在 common.py 里根治，那套 res 选法作废。）
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

# 机身 + 握把的尺寸。整体 2.00 × 0.956 = 高宽比 1:0.478，对上矢量版的 1:0.48；
# 第三轮握把探到 -0.63（1:0.53），下摆太长，剪影读成一只靴子而不是手柄
CEN  = (0.0, 0.089)                        # 轮廓缩放中心 = 机身中心
BAR  = (0.0, 0.089, 0.867, 0.311, 0.289)   # cx, cz, 半宽, 半高, 圆角
GRIP = [((-0.489, -0.044), (-0.711, -0.267), 0.289),
        (( 0.489, -0.044), ( 0.711, -0.267), 0.289)]
T_FRONT, T_BACK = 0.24, 0.28
GRIP_BULGE, GRIP_FALLOFF = 0.55, 0.33    # 背壳在握把处鼓多少 / 鼓包的高斯半径
N, M = 128, 26

init()
mat('body',  '#4c5566')   # 背面与机身侧壁。比矢量版的 #3d4450 亮一档，理由见开头
front_m = mat('front', '#6a748a')   # 正面再提亮一档：见开头"机身太深"那一条
grip_m  = mat('grip',  '#424b5c')   # 握把包胶，比机身再深一档
mat('panel', '#8b94a6')   # 按键底盘的浅灰，跟描边拉开 60% 亮度
mat('dpad',  '#2f3542')   # 十字键：提亮过的正面上的深色，反差最大的一处
stick_m = mat('stick', '#5cc9f2')   # 比矢量版 #8fe3ff 深一档：浅青渲出来是 (195,217,225) 的灰蓝
btn_m   = mat('btn',   '#f2564f')   # 同理，矢量版 #ff7a7a 渲出来会淡成藕粉


def sd_rrect(x, z, cx, cz, a, b, r):
    dx, dz = abs(x - cx) - (a - r), abs(z - cz) - (b - r)
    return math.hypot(max(dx, 0.0), max(dz, 0.0)) + min(max(dx, dz), 0.0) - r


def seg_dist(x, z, p, q):
    vx, vz, wx, wz = q[0] - p[0], q[1] - p[1], x - p[0], z - p[1]
    t = max(0.0, min(1.0, (wx * vx + wz * vz) / (vx * vx + vz * vz)))
    return math.hypot(wx - t * vx, wz - t * vz)


def sdf(x, z):
    d = sd_rrect(x, z, *BAR)
    for p, q, r in GRIP:
        d = min(d, seg_dist(x, z, p, q) - r)
    return d


def outline(n, rmax=1.6, steps=320):
    """沿每条射线取**最外侧**的入内点。射线扫描而不是二分：并集在握把根部有
       凹口，二分会掉进凹口里把轮廓啃掉一块；取最外侧交点等于把看不见的小凹口
       抹平，剪影反而更干净。"""
    pts = []
    for i in range(n):
        a = i * 2 * math.pi / n
        dx, dz = math.cos(a), math.sin(a)
        last = 0.0
        for k in range(1, steps + 1):
            r = rmax * k / steps
            if sdf(CEN[0] + dx * r, CEN[1] + dz * r) < 0.0:
                last = r
        lo, hi = last, last + rmax / steps
        for _ in range(28):                       # 细化到 1e-8
            mid = (lo + hi) / 2
            if sdf(CEN[0] + dx * mid, CEN[1] + dz * mid) < 0.0:
                lo = mid
            else:
                hi = mid
        pts.append((CEN[0] + dx * lo, CEN[1] + dz * lo))
    return pts


def meridian(m, ea, eb):
    """赤道 (1,0) → 极点 (0,1) 的超椭圆经线，按弧长均分。"""
    fine, p = 600, []
    for i in range(fine + 1):
        u = i / fine * math.pi / 2
        p.append((math.cos(u) ** ea, math.sin(u) ** eb))
    d = [0.0]
    for i in range(1, len(p)):
        d.append(d[-1] + math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]))
    out, j = [], 0
    for k in range(m + 1):
        tg = d[-1] * k / m
        while j < len(d) - 2 and d[j + 1] < tg:
            j += 1
        s = d[j + 1] - d[j]
        u = 0.0 if s < 1e-12 else (tg - d[j]) / s
        out.append((p[j][0] + (p[j + 1][0] - p[j][0]) * u,
                    p[j][1] + (p[j + 1][1] - p[j][1]) * u))
    out[0], out[-1] = (1.0, 0.0), (0.0, 1.0)
    return out


OUT = outline(N)
MER = {-1: meridian(M, 0.72, 0.50),    # 正面：指数 4，几乎是块平板
        1: meridian(M, 0.78, 0.64)}    # 背面：指数 3.1，拱起来
THK = {-1: T_FRONT, 1: T_BACK}


def back_bulge(x, z):
    d = min(seg_dist(x, z, p, q) for p, q, _ in GRIP)
    return 1.0 + GRIP_BULGE * math.exp(-(d / GRIP_FALLOFF) ** 2)


verts = [(x, 0.0, z) for x, z in OUT]
ring = {}
for sgn in (1, -1):
    for k in range(1, M):
        s, y = MER[sgn][k]
        ring[(sgn, k)] = len(verts)
        for ox, oz in OUT:
            x = CEN[0] + s * (ox - CEN[0])
            z = CEN[1] + s * (oz - CEN[1])
            t = THK[sgn] * (back_bulge(x, z) if sgn > 0 else 1.0)
            verts.append((x, sgn * y * t, z))
    ring[(sgn, M)] = len(verts)
    verts.append((CEN[0], sgn * THK[sgn] * (back_bulge(*CEN) if sgn > 0 else 1.0), CEN[1]))


def vid(sgn, k, i):
    return i % N if k == 0 else ring[(sgn, k)] + (i % N if k < M else 0)


def is_grip(x, z):
    """握把那两坨（含背面），用来分包胶色。"""
    return z < 0.02 and min(seg_dist(x, z, p, q) for p, q, _ in GRIP) < 0.30


faces, fmat = [], []
for sgn in (1, -1):
    for k in range(M):
        s_ = (MER[sgn][k][0] + MER[sgn][k + 1][0]) / 2
        for i in range(N):
            a, b = vid(sgn, k, i), vid(sgn, k, i + 1)
            c, d = vid(sgn, k + 1, i + 1), vid(sgn, k + 1, i)
            if k == M - 1:
                faces.append((a, d, b) if sgn > 0 else (a, b, d))
            else:
                faces.append((a, d, c, b) if sgn > 0 else (a, b, c, d))
            # 面心（近似）→ 正面提亮 / 握把包胶，全是同一块网格上的材质分区，不多一条描边
            ox = (OUT[i % N][0] + OUT[(i + 1) % N][0]) / 2
            oz = (OUT[i % N][1] + OUT[(i + 1) % N][1]) / 2
            fx = CEN[0] + s_ * (ox - CEN[0])
            fz = CEN[1] + s_ * (oz - CEN[1])
            fmat.append(2 if is_grip(fx, fz) else (1 if sgn < 0 else 0))

shell = add_mesh('shell', verts, faces, 'body')
shell.data.materials.append(front_m)
shell.data.materials.append(grip_m)
for p, m in zip(shell.data.polygons, fmat):
    p.material_index = m


def surf_y(x, z, sgn=-1):
    """壳面在 (x, z) 处的 y。sgn=-1 正面（朝镜头）、+1 背面。

    摇杆、十字键、底盘都要贴着这个面长出来，不能浮在空中；背面的中缝脊同理。"""
    ang = math.atan2(z - CEN[1], x - CEN[0])
    p = min(OUT, key=lambda q: abs(((math.atan2(q[1] - CEN[1], q[0] - CEN[0]) - ang
                                     + math.pi) % (2 * math.pi)) - math.pi))
    rr = math.hypot(p[0] - CEN[0], p[1] - CEN[1])
    s = min(1.0, math.hypot(x - CEN[0], z - CEN[1]) / rr)
    t = THK[sgn] * (back_bulge(x, z) if sgn > 0 else 1.0)
    mer = MER[sgn]
    for k in range(len(mer) - 1):
        if mer[k][0] >= s >= mer[k + 1][0]:
            u = (mer[k][0] - s) / max(1e-9, mer[k][0] - mer[k + 1][0])
            return sgn * (mer[k][1] + (mer[k + 1][1] - mer[k][1]) * u) * t
    return sgn * t


def face_y(x, z):
    return surf_y(x, z, -1)


def lathe(prof, seg, matname, name, loc):
    """(r, z) 剖面绕 Z 旋成一块封闭网格，摆到 loc 并把柱轴扳到 -Y（正对镜头）。

    摇杆和按键都带一圈**扎进机身里**的直裙边，而不是一颗球压在面上：球压在面上
    时球面和机身面在接触圈附近几乎相切，Freestyle 把那一圈判成忽有忽无的可见
    轮廓，渲出来摇杆周围长出一圈放射状的小黑睫毛。裙边是直穿过去的，
    交线是干净的一圈。（发卡的棒身当初也栽在同一件事上）"""
    verts, faces, ring = [], [], []
    for r, z in prof:
        if r <= 1e-9:
            ring.append(('p', len(verts))); verts.append((0.0, 0.0, z))
        else:
            ring.append(('r', len(verts)))
            for i in range(seg):
                a = i * 2 * math.pi / seg
                verts.append((r * math.cos(a), r * math.sin(a), z))
    for k in range(len(prof) - 1):
        (t0, b0), (t1, b1) = ring[k], ring[k + 1]
        for i in range(seg):
            j = (i + 1) % seg
            if t0 == 'p':
                faces.append((b0, b1 + j, b1 + i))
            elif t1 == 'p':
                faces.append((b0 + i, b0 + j, b1))
            else:
                faces.append((b0 + i, b0 + j, b1 + j, b1 + i))
    ob = add_mesh(name, verts, faces, matname)
    ob.location = loc
    ob.rotation_euler = (math.pi / 2, 0, 0)     # 局部 +Z → 世界 -Y，即朝着镜头
    return ob


def recalc(ob):
    """把法线统一朝外。凸台是手写的面表，顶/底/侧的绕向很容易写反 —— 法线朝里的话
       Toon 会把整块涂成暗面，Freestyle 的可见轮廓也跟着错位。"""
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')


def resample(pts, n):
    """闭合折线按弧长均分成 n 点。按参数均分会让长边稀、圆角密，凸台的侧壁
       跟着一起疏密不均。"""
    pts = list(pts) + [pts[0]]
    d = [0.0]
    for k in range(1, len(pts)):
        d.append(d[-1] + math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]))
    out, j = [], 0
    for k in range(n):
        tg = d[-1] * k / n
        while j < len(d) - 2 and d[j + 1] < tg:
            j += 1
        seg = d[j + 1] - d[j]
        u = 0.0 if seg < 1e-12 else (tg - d[j]) / seg
        out.append((pts[j][0] + (pts[j + 1][0] - pts[j][0]) * u,
                    pts[j][1] + (pts[j + 1][1] - pts[j][1]) * u))
    return out


def rr_poly(cx, cz, a, b, rad, n=72):
    """圆角矩形轮廓（XZ 平面）。"""
    ax, bz, K, p = a - rad, b - rad, 10, []
    for cnr, a0 in (((ax, bz), 0.0), ((-ax, bz), math.pi / 2),
                    ((-ax, -bz), math.pi), ((ax, -bz), 3 * math.pi / 2)):
        for k in range(K + 1):
            t = a0 + k / K * math.pi / 2
            p.append((cx + cnr[0] + rad * math.cos(t), cz + cnr[1] + rad * math.sin(t)))
    return resample(p, n)


def cross_poly(cx, cz, arm, w, n=80):
    """十字轮廓。12 个角点，不倒角 —— 十字就该是尖的，倒了在 111px 上直接读成圆点。"""
    p = [(w, w), (arm, w), (arm, -w), (w, -w), (w, -arm), (-w, -arm),
         (-w, -w), (-arm, -w), (-arm, w), (-w, w), (-w, arm), (w, arm)]
    return resample([(cx + x, cz + z) for x, z in p], n)


def slab(poly, depth, matname, name, sink=0.11, taper=0.012, sgn=-1,
         rings=5, extra=None, pick=None):
    """把一条闭合轮廓贴着壳面挤成一块凸台：顶面跟着壳面走、直壁扎进壳里。

    两处是踩出来的：

    - 顶面轮廓比底面**外扩** taper，侧壁做成微微悬挑。垂直壁在正视时法向正好
      垂直于视线，前后朝向符号不定，Freestyle 一帧描一帧不描地闪；悬挑之后顶边
      两侧稳定是一前一后两个面，描边才是一条连续的线。
    - 底面沉进壳里 sink，跟摇杆的直裙边同一招 —— 贴着面放会让两个面在接触圈
      附近几乎相切，那一圈会长出一排乱跳的小黑睫毛。

    顶面按同心环细分（不是从中心拉扇形）：扇形的三角又长又尖，面心落不准，
    ABXY 那四个色点没法用材质分区画出来。"""
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cz = sum(p[1] for p in poly) / n
    vs, fs, fm = [], [], []

    def top_pt(x, z, t):
        px, pz = cx + (x - cx) * t, cz + (z - cz) * t
        dx, dz = px - cx, pz - cz
        L = math.hypot(dx, dz) or 1.0
        ex, ez = px + dx / L * taper * t, pz + dz / L * taper * t
        return (ex, surf_y(px, pz, sgn) + sgn * depth, ez)

    idx = {}
    for r in range(rings):
        t = 1.0 - r / rings
        idx[r] = len(vs)
        for x, z in poly:
            vs.append(top_pt(x, z, t))
    vs.append((cx, surf_y(cx, cz, sgn) + sgn * depth, cz)); TC = len(vs) - 1
    B0 = len(vs)
    for x, z in poly:
        vs.append((x, surf_y(x, z, sgn) - sgn * sink, z))
    vs.append((cx, surf_y(cx, cz, sgn) - sgn * sink, cz)); BC = len(vs) - 1

    def mat_at(x, z):
        return pick(x, z) if pick else 0

    for r in range(rings):                       # 顶面：同心环
        t0, t1 = 1.0 - r / rings, 1.0 - (r + 1) / rings
        for i in range(n):
            j = (i + 1) % n
            mx = cx + (poly[i][0] - cx) * (t0 + t1) / 2
            mz = cz + (poly[i][1] - cz) * (t0 + t1) / 2
            if r == rings - 1:
                fs.append((idx[r] + i, idx[r] + j, TC) if sgn < 0 else (idx[r] + j, idx[r] + i, TC))
            else:
                fs.append((idx[r] + i, idx[r] + j, idx[r + 1] + j, idx[r + 1] + i) if sgn < 0
                          else (idx[r] + j, idx[r] + i, idx[r + 1] + i, idx[r + 1] + j))
            fm.append(mat_at(mx, mz))
    for i in range(n):                           # 底面
        j = (i + 1) % n
        fs.append((B0 + j, B0 + i, BC) if sgn < 0 else (B0 + i, B0 + j, BC))
        fm.append(0)
    for i in range(n):                           # 侧壁
        j = (i + 1) % n
        fs.append((idx[0] + i, B0 + i, B0 + j, idx[0] + j) if sgn < 0
                  else (idx[0] + j, B0 + j, B0 + i, idx[0] + i))
        fm.append(0)

    ob = add_mesh(name, vs, fs, matname)
    for m in (extra or []):
        ob.data.materials.append(m)
    if pick:
        for p, m in zip(ob.data.polygons, fm):
            p.material_index = m
    recalc(ob)
    return ob


def rbox(poly, y0, y1, matname, name):
    """一条闭合轮廓沿 y 拉伸成一块、两端封口 —— 肩键用。"""
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cz = sum(p[1] for p in poly) / n
    vs = [(x, y0, z) for x, z in poly] + [(x, y1, z) for x, z in poly]
    vs.append((cx, y0, cz)); C0 = len(vs) - 1
    vs.append((cx, y1, cz)); C1 = len(vs) - 1
    fs = []
    for i in range(n):
        j = (i + 1) % n
        fs.append((C0, j, i))
        fs.append((C1, n + i, n + j))
        fs.append((i, j, n + j, n + i))
    ob = add_mesh(name, vs, fs, matname)
    recalc(ob)
    return ob


# ---------------- 正面布局 ----------------
# 横向 1.734 单位 = 屏幕 96px，而屏幕描边实测 3.8px（screen_r 的 ×1.45 落到
# linestyle 和 render.line_thickness 两处、相乘）—— 两个零件的边挨得近于 0.12 单位
# (6.7px) 就会连成一条粗黑带。所以正面**最多排得下四个凸起**，一律 z 对齐、横向一排：
# 竖向只有 0.62 单位（34px），分不出上下两层。
SZ0 = 0.06                                  # 四件统一的竖向位置
L_STICK = (-0.62, SZ0, 0.160)               # 左摇杆
DPAD    = (-0.20, SZ0, 0.125, 0.0480)       # 十字键：臂长 / 臂半宽
R_STICK = ( 0.20, SZ0, 0.135)               # 右摇杆（本轮新增）
ABXY    = ( 0.61, SZ0, 0.155)               # ABXY：一块浅底盘 + 四个色点
# 色点第一版给到 0.050，渲出来红色像素中位只有 13 个、还有两帧是 0 —— 识别色判据
# 直接挂掉。4.2px 的点在这个尺寸上等于不存在，放大到 0.072（直径 6px）才数得出来。
DOT_R, DOT_OFF = 0.072, 0.075


def stick(x, z, r, name):
    """摇杆：一根扎进机身、顶面微鼓的短柱。裙边理由见 lathe 的注释。

    **柱壁必须外扩，不能是直的。** 第一版从 -0.12 到 0.045 都是同一个半径，
    正视时这段壁的法向正好垂直于视线，前后朝向符号不定 —— Freestyle 一条线
    都不画，渲出来摇杆是一坨没有轮廓的浅蓝，剥掉外轮廓之后它对结构密度的
    贡献是零。这跟 slab 的 taper 是同一件事，那边早就踩过。
    现在做成真的蘑菇形：底盘 0.94r → 收腰 0.78r → 帽檐 1.00r，高度从 0.125 拉到
    0.232（屏幕 12px）。收腰和帽檐各自是一条独立的可见轮廓，转到侧一点的角度
    两条线分得开（帽檐到底盘的投影落差 0.14 单位 = 7px > 2×描边 5.6px），
    一根摇杆在斜帧里能读出两三条线而不是一条。"""
    lathe([(0.0, -0.12), (r * 0.86, -0.12), (r * 0.94, 0.020), (r * 0.78, 0.090),
           (r * 0.86, 0.140), (r, 0.180), (r * 0.90, 0.205),
           (r * 0.62, 0.222), (0.0, 0.232)],
          24, 'stick', name, (x, face_y(x, z), z))


stick(L_STICK[0], L_STICK[1], L_STICK[2], 'stickL')
stick(R_STICK[0], R_STICK[1], R_STICK[2], 'stickR')

# 十字键：深色直接压在提亮过的正面上。不垫底盘 —— 底盘的边和十字的边只隔
# 0.025 单位(1.4px)，两条描边会糊成一坨；靠"深十字 vs 浅面"的色阶去读形状，
# 描边正好落在这条色界上。
slab(cross_poly(DPAD[0], DPAD[1], DPAD[2], DPAD[3]), 0.105, 'dpad', 'dpad')

# ABXY：四个分离的小凸起在这个尺寸上做不出来（每个 8px，相邻边距 0.12 单位以下
# 必糊），改成一块浅灰底盘 + 四个**材质分区**的色点 —— 材质分区不产生任何描边，
# 所以不占那 0.12 单位的间隙预算，颜色照样把"四个键"说清楚。
# 上下红、左右青：四个点两两相切，同色相切会连成一坨，异色才分得开
dots = [(0.0, DOT_OFF, 1), (0.0, -DOT_OFF, 1), (-DOT_OFF, 0.0, 2), (DOT_OFF, 0.0, 2)]


def abxy_pick(x, z):
    for ox, oz, m in dots:
        if math.hypot(x - (ABXY[0] + ox), z - (ABXY[1] + oz)) < DOT_R:
            return m
    return 0


slab(rr_poly(ABXY[0], ABXY[1], ABXY[2], ABXY[2], ABXY[2] * 0.999), 0.110,
     'panel', 'abxy', extra=[btn_m, stick_m], pick=abxy_pick, rings=7)

# 肩键：机身上沿探出去 0.10 单位，正面看是两个小包，剪影上也多两个角 ——
# 手柄的识别度反而更高。贯穿整个厚度，翻到侧面那几帧它还在。
for x0, x1, nm in ((-0.66, -0.30, 'lb'), (0.30, 0.66, 'rb')):
    rbox(rr_poly((x0 + x1) / 2, 0.418, (x1 - x0) / 2, 0.083, 0.050, 56),
         -0.145, 0.165, 'grip', nm)

# 握把上的防滑垫：正面两片小的（要避开摇杆），背面两片大的（背面没别的挡）。
# 握把那两坨是整件里最空的地方 —— 直径 0.58 单位(30px)，剥掉 6.3px 之后
# 里面还剩 17px 净空，正好塞得下一圈。
for sx in (-1, 1):
    slab(rr_poly(sx * 0.72, -0.320, 0.120, 0.120, 0.120, 52), 0.090,
         'grip', 'padF%d' % (sx > 0), rings=5)
    slab(rr_poly(sx * 0.70, -0.300, 0.145, 0.145, 0.145, 56), 0.034,
         'grip', 'padB%d' % (sx > 0), sgn=1, rings=6)

# 背面中央一排三块盖板（电池仓 + 左右两片）。
# 上一版这里是"一圈沿轮廓内缩 0.15 的背壳边框"，它有两个毛病：一是只离外轮廓
# 0.15 单位(7.8屏幕px)，而密度尺子要剥掉 6.3px，这条线一半落在剥掉的那一圈里；
# 二是它把整个背面占死了 —— 边框内侧到机身中线只剩 0.16 单位，按 g≥2W
# (0.108) 算里面再也放不下第二个零件。
# 换成一排盖板之后同样的地方能画 3 条闭合线而不是 1 条：背面可用宽度
# 1.734−2×0.108 = 1.518，切成三块、两道 0.108 的缝，每块 0.434 宽 —— 总线长
# 4.2 单位，是那一圈边框的两倍，而且每条都在深处，剥不掉。
for cx_ in (-0.542, 0.0, 0.542):
    slab(rr_poly(cx_, 0.089, 0.217, 0.135, 0.080, 64), 0.032,
         'body', 'back%+.0f' % (cx_ * 10), sgn=1, rings=6)

render_turntable('gamepad', active=shell, lean=35, tilt=0.26, roll=0.90, screen_r=52)
