"""毒蝴蝶（档 3 三人组 G26 蝴蝶发饰剑士，一次放出一群扑过去，throw n 多颗，2026-09-30）。

## 形体

- 前翅、后翅左右各一片，**四片都是单独的厚片**（外扩一圈黑边的翅缘 = 真台阶，才有描边），
  翅膀呈 V 形上扬（二面角），转起来两边翅膀互相遮挡 —— 平贴在一个面上的话转起来就是一张纸片翻面。
- 翅面紫色、翅根淡紫（凸起一层的真台阶）；翅缘的黑边就是描边本身。
  第一版另做了一圈深紫翅缘厚片：r 16 上它和两侧描边并成一块，整只读成黑团，删了。
- 细长的身子（胶囊）+ 两根触角（细管，末端小球）。
- lean 25：蝴蝶是一片薄的，lean 60 有 7/12 帧侧对相机、读成一根黑棍；压到 25 正面最多偏 50°，
  翅膀一直看得见，V 形的两边翅膀转起来一宽一窄、互相遮挡，仍然有体积。
- 齐射件，r 22（屏幕 ≈ 48px 宽）：1 单位 ≈ 22px，2W ≈ 0.25 单位；翅上只排得下"一块紫 + 翅根一块浅紫"两层。

跑：blender -b --python butterfly.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Matrix, Vector

init()
mat('wing', '#a45cf0')
mat('root', '#e2c8ff')
mat('body', '#3a2848')
T = 0.06                                                   # 翅膀厚


def slab(name, pts, m, y0, y1):
    """翅面在 xz 平面（x 往外、z 往头，正对相机），pts（x, z）沿 y 挤出成 y0..y1 的厚片（−y 朝相机）"""
    n = len(pts)
    vs = [(x, y1, z) for x, z in pts] + [(x, y0, z) for x, z in pts]
    fs = [tuple(range(n))[::-1], tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return add_mesh(name, vs, fs, m)


def blob(cx, cz, rx, rz, rot, side, k=18):
    c, s = math.cos(rot), math.sin(rot)
    P = [(side * (cx + rx * math.cos(2 * math.pi * i / k) * c - rz * math.sin(2 * math.pi * i / k) * s),
          cz + rx * math.cos(2 * math.pi * i / k) * s + rz * math.sin(2 * math.pi * i / k) * c) for i in range(k)]
    return P if side > 0 else P[::-1]                      # 镜像后反一下顺序，法线不翻（不用负缩放）


def shrink(pts, f, cx, cz):
    return [(cx + (x - cx) * f, cz + (z - cz) * f) for x, z in pts]


for side in (1, -1):
    for cx, cz, rx, rz, rot in ((0.5, 0.35, 0.55, 0.36, 0.5), (0.38, -0.36, 0.38, 0.3, -0.5)):   # 前翅、后翅
        P = blob(cx, cz, rx, rz, rot, side)
        for ob in (slab('wing', P, 'wing', -T, T),
                   slab('root', shrink(P, 0.45, side * cx * 0.45, cz * 0.45), 'root', -T - 0.05, T)):
            ob.rotation_euler = (0, 0, side * 0.45)       # V 形：两边翅膀绕身子（z 轴）往相机这边折
body = prim('uv_sphere', 'body', radius=1.0, location=(0, -0.02, -0.05))
body.scale = (0.1, 0.1, 0.62)
for side in (1, -1):                                        # 触角
    a = prim('cylinder', 'body', radius=0.025, depth=0.5, location=(side * 0.12, -0.05, 0.75))
    a.rotation_euler = (0, side * 0.45, 0)
    prim('uv_sphere', 'body', radius=0.06, location=(side * 0.23, -0.05, 0.98))

ob = join_all(body)
render_turntable('butterfly', active=ob, lean=25, tilt=0.35, roll=0.3, screen_r=22)
