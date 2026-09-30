"""算盘（档 3 三人组 G5 佟湘玉式客栈老板娘，"额滴神"一声把算盘甩出去砸人，2026-09-30）。

## 形体

- 名单写的是"甩算盘珠子"，但单颗珠子做 3D 没有内部结构（一颗菱形转起来就是一个菱形），所以出整把小算盘：
  红木框（四根独立的框条）+ 一道横梁 + 3 根档（铜杆）+ 每档上 1 颗、下 2 颗算盘珠。**每颗珠子是单独的扁圆珠**，
  转起来一颗颗珠子的轮廓互相遮挡、透视缩短一直在变。
- **审查第三轮 6.7 返工**：上一版框内一片暗、珠子读成米粒，180° 几乎全黑。原因是三条叠在一起：
  1. 珠子是两头削平的菱形双锥（0.38 × 0.3），Toon 下半截整片是暗面，亮面只剩上半截一小条；
  2. 框条 0.2 宽、红木色，暗面跟描边贴成一片；
  3. 珠与珠、珠与框的缝 < 2W，描边并成一张网。
  改法：珠子换成**扁圆珠**（宽 0.38、高 0.27，腰线圆滑，亮面占大半），颜色提到**亮蜜黄**；框条收细到 0.16、框色压深一档，
  亮珠对深框，明暗拉得开；缝按 g ≥ 2W 重排（见下）。
- 零件间距：屏幕描边 2.8px，1 单位 ≈ 40px → 2W ≈ 0.14 单位。3 档档距 0.58：相邻两档珠子横向缝 0.2、边档珠子到框 0.08，
  每档下格只放 2 颗、按"拨了一个数"分开摆（相邻两档拨的颗数不同，同高的珠子不并排，下格里露出一段空档杆）——
  下格放 3 颗、珠宽 0.44 那一版框里 60% 是描边色，缝全被描边填死（快测）。
- 有正面，lean −20：正面最多偏 40°；取负、起始略往上抬是为了让正面一直在灯这一侧（见 cassette.py 的姿态注释）。
  上一版 lean 30 / tilt 0.3，180° 那几帧正面整个转进背光，框内全黑。
- 屏幕上半径 **40**（G5 atk.r 从 34 改成 40），整把宽 ~95px。r 34 时 1 单位只有 34px，档杆、框条、珠子的描边占掉一半面积，
  12 帧里 5 帧是墨块（快测）；放大到 40，同样 2.8px 的描边占比小一截。

跑：blender -b --python abacus.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

init()
mat('frame', '#8c3e24')      # 深红木框：比珠子深两档，亮珠对深框
mat('rod', '#d8c28a')        # 铜档
mat('bead', '#f6c850')       # 亮蜜黄木珠（识别色）

W, H, D = 2.0, 1.6, 0.14      # 宽（NOMINAL）、高、厚；相机沿 +Y 看，正面朝 −Y
FB = 0.16                    # 框条宽
for sx in (-1, 1):
    prim('cube', 'frame', size=1, location=(sx * (W / 2 - FB / 2), 0, 0), scale=(FB, D, H))
for sz in (-1, 1):
    prim('cube', 'frame', size=1, location=(0, 0, sz * (H / 2 - FB / 2)), scale=(W - 2 * FB + 0.02, D * 0.9, FB))

ZI = H / 2 - FB                 # 框内半高
BEAM_Z, BEAM_H = 0.26, 0.08
prim('cube', 'frame', size=1, location=(0, 0, BEAM_Z), scale=(W - 2 * FB + 0.02, D * 0.8, BEAM_H))

NROD = 3
PITCH = 0.58
XS = [(i - (NROD - 1) / 2) * PITCH for i in range(NROD)]
for x in XS:
    prim('cylinder', 'rod', vertices=8, radius=0.03, depth=2 * ZI + 0.04, location=(x, 0, 0))

BH, BR = 0.27, 0.19             # 珠高、珠腰半径
GAP = 0.012                     # 同档相邻两颗之间的缝（两颗各自一圈轮廓，不是一根糖葫芦）


def bead(x, z, n=20, m=8):
    """扁圆珠：一整块旋转体网格，截面是压扁的圆（腰最宽、上下两头收成小平顶穿档）"""
    v, f = [], []
    rings = []
    for j in range(m + 1):
        ph = -math.pi / 2 + math.pi * j / m
        r = max(0.05, BR * math.cos(ph))
        rings.append((r, BH / 2 * math.sin(ph)))
    for r, h in rings:
        for k in range(n):
            a = 2 * math.pi * k / n
            v.append((x + r * math.cos(a), r * math.sin(a), z + h))
    v += [(x, 0, z - BH / 2), (x, 0, z + BH / 2)]
    c0, c1 = len(v) - 2, len(v) - 1
    for j in range(m):
        for k in range(n):
            k2 = (k + 1) % n
            f.append((j * n + k, j * n + k2, (j + 1) * n + k2, (j + 1) * n + k))
    for k in range(n):
        k2 = (k + 1) % n
        f.append((c0, k2, k)); f.append((c1, m * n + k, m * n + k2))
    add_mesh('bead', v, f, 'bead')


# 每档拨的数：(上珠拨下来?, 下珠拨上去几颗) —— 相邻两档高低必须错开
NUM = [(1, 1), (0, 2), (1, 0)]
UP_LO, UP_HI = BEAM_Z + BEAM_H / 2, ZI           # 上格
LO_LO, LO_HI = -ZI, BEAM_Z - BEAM_H / 2          # 下格
NLOW = 2
for x, (u, n) in zip(XS, NUM):
    bead(x, UP_LO + BH / 2 + GAP if u else UP_HI - BH / 2 - GAP)
    for i in range(n):
        bead(x, LO_HI - GAP - BH / 2 - i * (BH + GAP))
    for i in range(NLOW - n):
        bead(x, LO_LO + GAP + BH / 2 + i * (BH + GAP))

bpy.ops.object.select_all(action='SELECT')           # 旋转烤进网格，join 后姿态确定（理由见 dumbbell.py）
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
ob = join_all()
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')      # 手拼的网格面朝向不一致：朝里的面 Toon 按背光画成近黑（珠子下半截整片黑），统一朝外
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
render_turntable('abacus', active=ob, lean=-20, tilt=-0.1, roll=0.2, screen_r=40)
