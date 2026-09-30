"""银元（档 3 三人组 B6 上海滩许文强，礼帽长风衣，拇指一弹把银元抛出去砸女生，2026-09-30）。

## 形体

- 民国银元：一整块回转体（车床轮廓）做币身 —— 两面各一圈凸起的外缘圈 + 下沉的币面。
  外缘圈内壁做成**内倒扣**（顶面半径比根部小，悬挑一点），正对镜头时这圈内壁法向背着相机，
  圈内侧稳定出一圈内轮廓；垂直内壁的话法向正好垂直视线，描边一帧有一帧无地闪（skill 坑 4b 悬挑那条）。
- 两面中间各一枚凸起的大五角星（单独的棱柱，顶面外扩 8% 同样是悬挑，底部扎进币面免得相切长睫毛）。
  五角星只有 5 个粗角，零件不碎；嘉禾麦穗那种细叶片在 40px 上会被描边吃光（skill 坑 4）。
- 侧边 10 道粗齿槽（真缺口）：抛硬币就是在空中翻，侧边转到正面时要看得出厚度和齿。
  齿距按 g ≥ 2W 定：周长 6.3 单位、屏幕约 20px/单位，10 道每道间隔 ~12px。
- lean 80：抛硬币就是绕横轴翻，两面内容一样（都是星），翻到背面也认得出。
- 屏幕上半径 20（B6 atk.r），直径 40px。

跑：blender -b --python coin.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Matrix
import bpy

init()
mat('silver', '#d9dde3')
mat('relief', '#eef0f3')

R = 1.0
FIELD = 0.12          # 币面半厚
RIM_T = 0.22          # 外缘圈顶面半厚
RIM_IN = 0.66         # 外缘圈内沿（顶面）半径
SEG = 60
NOTCH = 0            # 侧边齿槽数
NOTCH_W = 0.16        # 齿槽宽（弧长）
NOTCH_D = 0.07        # 齿槽深


def lathe(prof, seg, matname, name, rfun=None):
    """prof: [(r, z)] 从一极到另一极；r=0 的点收成一个顶点"""
    verts, rings = [], []
    for r, z in prof:
        if r < 1e-6:
            rings.append([len(verts)]); verts.append((0, 0, z)); continue
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            rr = rfun(r, a) if rfun else r
            ring.append(len(verts)); verts.append((rr * math.cos(a), rr * math.sin(a), z))
        rings.append(ring)
    faces = []
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1:
            faces += [(A[0], B[i], B[(i + 1) % seg]) for i in range(seg)]
        elif len(B) == 1:
            faces += [(A[i], B[0], A[(i + 1) % seg]) for i in range(seg)]
        else:
            faces += [(A[i], B[i], B[(i + 1) % seg], A[(i + 1) % seg]) for i in range(seg)]
    return add_mesh(name, verts, faces, matname)


def notch(r, a):
    """外圈（r≥R-1e-3）上开齿槽：落在槽里的顶点往里收"""
    if r < R - 1e-3 or not NOTCH: return r
    k = (a * NOTCH / (2 * math.pi)) % 1.0
    return r - NOTCH_D if abs(k - 0.5) * 2 * math.pi * R / NOTCH < NOTCH_W / 2 else r


# 从 +z 极到 −z 极：币面 → 内倒扣的外缘内壁 → 缘顶 → 侧边 → 反面同样
prof = [(0, FIELD), (RIM_IN + 0.05, FIELD), (RIM_IN, RIM_T), (R - 0.03, RIM_T), (R, RIM_T - 0.03),
        (R, -RIM_T + 0.03), (R - 0.03, -RIM_T), (RIM_IN, -RIM_T), (RIM_IN + 0.05, -FIELD), (0, -FIELD)]
body = lathe(prof, SEG * 2, 'silver', 'body', rfun=notch)


def star(z0, z1, flip, ro=0.40, ri=0.18, top=1.08):
    """五角星棱柱：底在 z0（扎进币面），顶在 z1，顶面外扩 top 倍（悬挑）"""
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        r = ro if i % 2 == 0 else ri
        pts.append((r * math.cos(a), r * math.sin(a)))
    n = len(pts)
    verts = [(x, y, z0) for x, y in pts] + [(x * top, y * top, z1) for x, y in pts] + [(0, 0, z0), (0, 0, z1)]
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    faces += [((i + 1) % n, i, 2 * n) for i in range(n)] + [(n + i, n + (i + 1) % n, 2 * n + 1) for i in range(n)]
    if flip:
        verts = [(x, -y, -z) for x, y, z in verts]
    return add_mesh('star', verts, faces, 'relief')


star(FIELD - 0.03, RIM_T - 0.01, False)
star(FIELD - 0.03, RIM_T - 0.01, True)

ob = join_all(body)
ob.data.transform(Matrix.Rotation(math.pi / 2, 4, 'X'))     # 币面朝相机（−Y）
render_turntable('coin', active=ob, lean=80, tilt=0.35, roll=0.2, screen_r=20)
