"""算盘（档 3 三人组 G5 佟湘玉式客栈老板娘，"额滴神"一声把算盘甩出去砸人，2026-09-30）。

## 形体

- 名单写的是"甩算盘珠子"，但单颗珠子做 3D 没有内部结构（一颗菱形转起来就是一个菱形），所以出整把小算盘：
  红木框（四根独立的框条）+ 一道横梁（比框薄一截，框和梁之间有前后错层）+ 3 根档（细铜杆）
  + 每档上 1 颗、下 2 颗算盘珠（真算盘是 13 档 × 上 2 下 5，缩到屏幕 ~80px 只放得下 3 档，见下）。**每颗珠子是单独的菱形双锥**（两头削平），转起来一颗颗菱形的轮廓
  互相遮挡、透视缩短一直在变。
- 零件间距按 g ≥ 2W 算：屏幕描边 2.8px，1 单位 ≈ 40px → 零件间距要 ≥ 0.14 单位。
  **第一版 5 档、珠宽 0.30 × 高 0.21**：每颗珠子屏幕上 12×8px，两圈描边一占只剩墨，36 帧里 11/12 是墨块、描边宽读成 8px，
  整把是一块黑板。改成 3 档、珠子 0.42 × 0.28（屏幕 19×12px），档距 0.6（珠与珠横向留 0.18 = 8px）；
  框条 0.11 时屏幕上只有 5px、两边描边一占整圈是墨（第三版 12/12 墨块）：框条加粗到 0.2（9px，中间露出红木色），
  框厚收薄（0.18）、框色调亮。
  相邻两档的珠子同高时缝只有 0.12 → 并成横黑带，所以珠子按"拨了一个数"错开摆（每档拨上去的颗数不同），
  相邻两档高低错开。这也正是算盘本来的样子。
- 珠子用蜜黄木色（识别色）：传统黑珠子跟描边色贴死，64px 上就是一块黑板。
- 有正面，lean 30：lean 40 时有 4/12 帧转到侧对，整把只剩一根黑框条；30 时正面最多偏 60°。
- 屏幕上半径 34（G5 atk.r 按这个填），整把宽 ~80px。

跑：blender -b --python abacus.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

init()
mat('frame', '#c0643a')      # 红木框：深红木色在 toon 暗面里跟描边贴成一片（第二版框占了一半黑），调亮
mat('rod', '#c8b27a')        # 铜档
mat('bead', '#e0a24e')       # 蜜黄木珠（识别色）

W, H, D = 2.0, 1.6, 0.18      # 宽（NOMINAL）、高、厚；相机沿 +Y 看，正面朝 −Y
FB = 0.2                     # 框条宽
# 四根框条（上下两根夹在左右两根之间，外沿略收，左右框条顶底端各探出一点：角上有台阶，不是一个光滑的环）
for sx in (-1, 1):
    prim('cube', 'frame', size=1, location=(sx * (W / 2 - FB / 2), 0, 0), scale=(FB, D, H))
for sz in (-1, 1):
    prim('cube', 'frame', size=1, location=(0, 0, sz * (H / 2 - FB / 2 - 0.01)), scale=(W - 2 * FB + 0.02, D * 0.9, FB))

ZI = H / 2 - FB                 # 框内半高 0.62
BEAM_Z, BEAM_H = 0.22, 0.09
prim('cube', 'frame', size=1, location=(0, 0, BEAM_Z), scale=(W - 2 * FB + 0.02, D * 0.72, BEAM_H))

NROD = 3
PITCH = 0.52
XS = [(i - (NROD - 1) / 2) * PITCH for i in range(NROD)]
for x in XS:
    prim('cylinder', 'rod', vertices=8, radius=0.028, depth=2 * ZI + 0.04, location=(x, 0, 0))

BH, BR, BE = 0.3, 0.19, 0.07   # 珠高、珠腰半径、两头削平半径
GAP = 0.012                     # 同档相邻两颗之间的缝（留缝：两颗各自一圈轮廓，不是一根糖葫芦）


def bead(x, z, n=16):
    """一整块旋转体网格（两个圆锥拼的话腰线处两片盖面重合，Freestyle 会长小黑睫毛，skill 坑 7）"""
    rings = [(BE, -BH / 2), (BR, 0.0), (BE, BH / 2)]
    v = [(x, 0, z - BH / 2), (x, 0, z + BH / 2)]
    for r, h in rings:
        for k in range(n):
            a = 2 * math.pi * k / n
            v.append((x + r * math.cos(a), r * math.sin(a), z + h))
    f = []
    for k in range(n):
        k2 = (k + 1) % n
        f.append((0, 2 + k2, 2 + k))
        f.append((1, 2 + 2 * n + k, 2 + 2 * n + k2))
        for j in range(2):
            a0, b0 = 2 + j * n, 2 + (j + 1) * n
            f.append((a0 + k, a0 + k2, b0 + k2, b0 + k))
    add_mesh('bead', v, f, 'bead')


# 每档拨的数：(上珠拨下来?, 下珠拨上去几颗) —— 相邻两档高低必须错开
NUM = [(1, 1), (0, 2), (1, 0)]
UP_LO, UP_HI = BEAM_Z + BEAM_H / 2, ZI           # 上格
LO_LO, LO_HI = -ZI, BEAM_Z - BEAM_H / 2          # 下格
NLOW = 2
for x, (u, n) in zip(XS, NUM):
    # 上珠：拨下来就贴横梁，否则贴上框
    bead(x, UP_LO + BH / 2 + GAP if u else UP_HI - BH / 2 - GAP)
    # 下珠：拨上去的 n 颗从横梁往下排，其余从下框往上排
    for i in range(n):
        bead(x, LO_HI - GAP - BH / 2 - i * (BH + GAP))
    for i in range(NLOW - n):
        bead(x, LO_LO + GAP + BH / 2 + i * (BH + GAP))

ob = join_all()
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')      # 手拼的网格面朝向不一致：朝里的面 Toon 按背光画成近黑（珠子下半截整片黑），统一朝外
bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
render_turntable('abacus', active=ob, lean=30, tilt=0.30, roll=0.20, screen_r=34)
