"""麻将牌·红中（档 3 三人组 B10 麻将大叔，一把甩出 2~3 张牌砸女生、喊"胡了"，2026-09-30）。

## 形体

- 一张立方牌：前半是象牙白牌身、后半是绿色牌背，**两块单独的圆角方块**，绿背每边比白身收进一圈，
  交界处是一道真台阶 —— 侧着转时台阶那条线在变，读得出"白绿两层的一块牌"。
  两层要是一块方块分两种材质，交界不出描边（skill 坑 4b），就是一块涂了两色的肥皂。
- 正面的"红中"：一个口字框（四根粗条）+ 一竖贯穿，全是凸起的棱柱，顶面外扩一点（悬挑，
  正对镜头时侧壁法向背着相机，笔画一圈描边稳定不闪）。笔画宽 0.28 单位 ≈ 屏幕 5.6px ≥ 两倍描边：
  再细的话笔画整根被描边吃成墨线，红色没了。口字里被一竖切开的两个小空当约 4px，会读成两个暗点，
  那是"中"字本来就有的结构，留着。
- 有正面，lean 40：正面最多偏 80°，始终看得到红中，又能看到白绿两层的厚度。
- 屏幕上半径 20（B10 atk.r），牌高 40px。

跑：blender -b --python mahjong.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

init()
mat('ivory', '#f3ecd6')
mat('green', '#2f9a5a')
mat('red', '#d8282c')

H, W, D = 2.0, 1.46, 1.0     # 高（NOMINAL）、宽、厚；正面朝 −Y
D_IVORY = 0.60
STEP = 0.10                  # 绿背每边收进多少（台阶）


def rbox(name, matname, cx, cy, cz, sx, sy, sz, bevel):
    ob = prim('cube', matname, size=1, location=(cx, cy, cz), scale=(sx, sy, sz))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    m = ob.modifiers.new('bv', 'BEVEL'); m.width = bevel; m.segments = 2; m.limit_method = 'ANGLE'
    bpy.ops.object.modifier_apply(modifier='bv')
    for p in ob.data.polygons: p.use_smooth = False
    return ob


FRONT = -D / 2
body = rbox('ivory', 'ivory', 0, FRONT + D_IVORY / 2, 0, W, D_IVORY, H, 0.12)
rbox('green', 'green', 0, FRONT + D_IVORY + (D - D_IVORY) / 2 - 0.01, 0, W - 2 * STEP, D - D_IVORY + 0.02, H - 2 * STEP, 0.10)


def stroke(cx, cz, w, h, out=0.05, sink=0.03, flare=-0.035):
    """凸起的笔画：底面扎进牌面 sink，顶面（朝 −Y）凸出 out，顶面每边外扩 flare（悬挑）"""
    y0, y1 = FRONT + sink, FRONT - out
    x0, x1, z0, z1 = cx - w / 2, cx + w / 2, cz - h / 2, cz + h / 2
    f = flare
    verts = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
             (x0 - f, y1, z0 - f), (x1 + f, y1, z0 - f), (x1 + f, y1, z1 + f), (x0 - f, y1, z1 + f)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return add_mesh('stroke', verts, faces, 'red')


S = 0.30                      # 笔画宽
KW, KH, KZ = 1.16, 0.86, 0.06  # 口字框外宽、外高、中心高度
stroke(0, KZ + KH / 2 - S / 2, KW, S)          # 口 上横
stroke(0, KZ - KH / 2 + S / 2, KW, S)          # 口 下横
stroke(-KW / 2 + S / 2, KZ, S, KH)             # 口 左竖
stroke(KW / 2 - S / 2, KZ, S, KH)              # 口 右竖
stroke(0, 0.0, S, 1.66)                        # 中间一竖贯穿

ob = join_all(body)
render_turntable('mahjong', active=ob, lean=36, tilt=0.2, roll=0.2, screen_r=20)
