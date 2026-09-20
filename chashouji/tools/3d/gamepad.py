"""游戏手柄（档 2，灭迹党）—— 深色机身 + 一个青色摇杆 + 一个红色按键。

照搬 ammo.js ITEM.gamepad：横向扁机身 #3d4450、左侧青摇杆、右侧偏上红按键。

五条形状结论（第二条是第一轮渲出来才发现的）：

- **机身 + 两只握把是一块网格，不是三个物体叠出来的。** 第一轮把握把做成两颗独立
  椭球插进机身，两个面在交界处几乎相切，Freestyle 的可见轮廓在这一带来回跳，
  渲出来整条边是毛的。现在改成把"圆角条 ∪ 两根胶囊"当成一个 2D 有向距离场，
  沿射线找最外侧的边界点取出一条闭合外轮廓再放样 —— 一块封闭网格，
  轮廓是一条干净的线。
- **机身本体不做腰。** 第一轮给上下边中段各内收 0.055，加上两端的握把，
  剪影读成一根哑铃/骨头。腰交给握把之间那道天然的凹口，机身自己保持平直。
- **转轴必须是 Y（绕观察轴自转），不能是 X（翻面）。** 判据 3 是按整条转盘判的，
  不是按最好那几帧判的：礼物飞过来 0.65 秒要转 1.45 圈，一半帧认不出就是不合格。
  按实际绘制尺寸铺到客厅米色底上数了一遍 —— 绕 X（连 tilt=0 把转轴扳平都试过）只有 4/8：
  转到底沿是根深色棒、转到背面是块光板，摇杆按键全不见了；绕 Y 8/8。
  花束绕 X 翻面好用是因为它各向同性，转到哪一面都是花；手柄的内容全在正面（摇杆 + 按键），
  背面是一块光板，属于"内容只朝一个方向"那一类，翻过去就是白丢一半帧。
  axis='Y' 时相机沿 +Y 看，世界 Y 就是相机轴，所以 Ry(θ) 是**画面内自转**：
  姿态不变、题材永远认得出，而光源仍然钉在世界坐标里不跟着转 —— 后面这半句
  才是换 3D 真正买到的东西（矢量版 ctx.rotate 会把光影一起转走）。
  厚度靠固定的 tilt/roll 给一点 3/4 角就够，不值得拿一半可读帧去换。
  注意 tilt/roll 是按 e[(idx+1)%3] / e[(idx+2)%3] 挂上去的，跟着 axis 滚：
  axis='Y' 时 tilt 变成绕屏幕竖轴的偏航、roll 变成物体自身的俯仰，
  数值跟 axis='X' 的那套不通用，是照着出图重调的。
  代价是背壳那两坨鼓包不再有正对背面的帧 —— 它们改为只在 3/4 角的外轮廓上
  鼓出来。拿"能认出是手柄"换"能看清背壳"，这笔是划算的。
- **正面平、背面鼓、背面在握把处再鼓一块。** 背面厚度乘一个以握把中轴为中心的
  高斯包（C∞ 的，不会长出折痕，理由见 pillow.py 第二条），翻到背面那十来帧
  看到的是拱背 + 两坨鼓包。抱枕高 1.68 是方的、手柄高 1.03 是横条，
  再加这两坨，两件档 2 的剪影彻底分得开。
- **摇杆和按键做成真的凸起，让 Freestyle 描上边。** 跟抱枕的缝线正好相反：
  那是"面上的花纹"（描边只会添乱），这是"面上支出来的东西"（描边就是它的存在感），
  摇杆凸出 0.18 之后连侧视帧都看得见它支在那儿。
- 两个彩色点是唯一的识别点，直径给足（观众端 139px 上摇杆 39px、按键 29px），
  不加十字键肩键 —— 那个尺寸下全是噪点。整体高宽比压回矢量版的
  1:0.48 —— 握把弧度正是它区别于圆角条的地方，但下摆不能长，长了读成靴子。

跑：blender -b --python gamepad.py -- 36 245 128 <out> 1
    pack_atlas.py <帧目录> gamepad_atlas.webp --cell 160

    渲染边长 245 = 单格 160 / 并集占比 0.653。common.py 说描边宽度是
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
mat('body',  '#3d4450')
mat('stick', '#5cc9f2')   # 比矢量版 #8fe3ff 深一档：浅青渲出来是 (195,217,225) 的灰蓝
mat('btn',   '#f2564f')   # 同理，矢量版 #ff7a7a 渲出来会淡成藕粉


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


faces = []
for sgn in (1, -1):
    for k in range(M):
        for i in range(N):
            a, b = vid(sgn, k, i), vid(sgn, k, i + 1)
            c, d = vid(sgn, k + 1, i + 1), vid(sgn, k + 1, i)
            if k == M - 1:
                faces.append((a, d, b) if sgn > 0 else (a, b, d))
            else:
                faces.append((a, d, c, b) if sgn > 0 else (a, b, c, d))

shell = add_mesh('shell', verts, faces, 'body')


def face_y(x, z):
    """正面在 (x, z) 处的 y —— 摇杆/按键要贴着面长出来，不能浮在空中。"""
    ang = math.atan2(z - CEN[1], x - CEN[0])
    p = min(OUT, key=lambda q: abs(((math.atan2(q[1] - CEN[1], q[0] - CEN[0]) - ang
                                     + math.pi) % (2 * math.pi)) - math.pi))
    rr = math.hypot(p[0] - CEN[0], p[1] - CEN[1])
    s = min(1.0, math.hypot(x - CEN[0], z - CEN[1]) / rr)
    mer = MER[-1]
    for k in range(len(mer) - 1):
        if mer[k][0] >= s >= mer[k + 1][0]:
            u = (mer[k][0] - s) / max(1e-9, mer[k][0] - mer[k + 1][0])
            return -(mer[k][1] + (mer[k + 1][1] - mer[k][1]) * u) * T_FRONT
    return -T_FRONT


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


# 摇杆：一根扎进机身、顶面微鼓的短柱
SX, SZ, SR = -0.489, 0.067, 0.278
sy = face_y(SX, SZ)
lathe([(0.0, -0.12), (SR, -0.12), (SR, 0.045), (SR * 0.96, 0.070),
       (SR * 0.84, 0.095), (SR * 0.58, 0.115), (0.0, 0.125)],
      20, 'stick', 'stick', (SX, sy, SZ))

# 按键：同样带裙边，但只微微凸出来
BX, BZ, BR = 0.489, 0.178, 0.211
by = face_y(BX, BZ)
lathe([(0.0, -0.12), (BR, -0.12), (BR, 0.0), (BR * 0.92, 0.028),
       (BR * 0.70, 0.052), (BR * 0.38, 0.068), (0.0, 0.075)],
      18, 'btn', 'btn', (BX, by, BZ))

render_turntable('gamepad', active=shell, axis='Y', tilt=0.40, roll=0.24)
