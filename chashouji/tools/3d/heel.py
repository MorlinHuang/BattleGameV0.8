"""高跟鞋（档 1，查岗党，榴莲鞋雨里的四只鞋，2026-09-27）—— 一只写实比例的尖头细跟浅口鞋。
用户：鞋"太 Q 了，写实一点"，又要"参考口红、香蕉做成有体积感的"。

## 形体

- **鞋身 = 一段放样体减去鞋口**：外形按长度方向每个截面给 [鞋底高 hb, 鞋帮高 hw, 半宽 w]，
  超椭圆截面放样成一个实心；再用一个稍小一圈、底面抬高 LINER 的放样体做布尔差，挖出鞋口 ——
  露出来的鞋垫和内壁换米色（鞋垫是识别点：没有它就是一块红色的楔子）。
  鞋口前沿收成 U 形（挖的那块往前按 sqrt 收窄），不是一刀直切。
- **足弓**：前掌贴地，从 ARCH_X 往后按 smoothstep 抬到后跟 HEEL_H 高 —— 侧面剪影这道弯是第二识别点。
- **鞋跟比真鞋粗一档**（顶 0.13、底 0.075）：屏幕上鞋长 ~110px，真鞋那么细的跟两条描边一夹就没了
  （零件宽要 > 2 条描边宽，见 danmu-3d-sprite 坑 4）。跟底一小截黑色鞋钉。
- 鞋底朝下的面换深色（翻过来看得到底）。只渲红色一版，粉 / 黑在图集上调色（rain.js 用）。
- 有正面（侧面剪影）：lean 24 + roll，长轴横着斜过来（同手柄的救法）。lean 38 时有 3/8 帧转到正对鞋尖 /
  鞋跟，剪影缩成一根细条；鞋身也比真鞋宽一档（半宽 0.31~0.46），俯仰时鞋口和米色鞋垫才露得出来。

跑：blender -b --python heel.py -- 36 <边长> 128 <out> 1
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from mathutils import Vector, Matrix
import bpy

X0, X1 = -1.2, 1.25        # 后跟 → 鞋尖
ARCH_X, HEEL_H = 0.25, 0.95
THROAT = 0.42              # 鞋口前沿
WALL, LINER = 0.055, 0.06  # 鞋帮厚、鞋垫比鞋底面高多少
NX, NU = 40, 20

init()
mat('upper', '#e0202c')
mat('liner', '#e8c9a0')
mat('sole', '#4a2024')
mat('tip', '#1e1a1c')
bpy.context.scene.view_settings.view_transform = 'Standard'   # AgX 把正红压成砖红

def smooth(t):
    t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)

def hb(x):   # 鞋底面高度
    return HEEL_H * smooth((ARCH_X - x) / (ARCH_X - X0 - 0.15))

def w(x):    # 半宽：后跟圆、前掌最宽、鞋尖收尖
    u = (x - X0) / (X1 - X0)
    back = math.sqrt(max(0.0, min(1.0, (x - X0) / 0.22)))
    front = max(0.0, (X1 - x) / (X1 - 0.45)) ** 0.8 if x > 0.45 else 1.0
    return (0.31 + 0.15 * math.sin(math.pi * min(1, u * 1.1))) * back * front

def hw(x):   # 鞋帮高（鞋底面往上）
    if x < -0.4:
        return 0.30 + 0.25 * smooth((-0.4 - x) / 0.8)
    if x < THROAT:
        return 0.26 + 0.06 * smooth((x + 0.4) / 0.8)
    return 0.32 * max(0.0, (X1 - x) / (X1 - THROAT)) ** 0.7 + 0.03

def loft(name, xs, sec, matname):
    verts, faces = [], []
    for x in xs:
        for i in range(NU):
            verts.append(sec(x, 2 * math.pi * i / NU))
    for j in range(len(xs) - 1):
        for i in range(NU):
            a, b = j * NU + i, j * NU + (i + 1) % NU
            faces.append((a, b, b + NU, a + NU))
    faces.append(tuple(range(NU))[::-1])
    faces.append(tuple((len(xs) - 1) * NU + i for i in range(NU)))
    return add_mesh(name, verts, faces, matname)

def se(a, p=3.0):   # 超椭圆：更方一点的圆
    c, s = math.cos(a), math.sin(a)
    return math.copysign(abs(c) ** (2 / p), c), math.copysign(abs(s) ** (2 / p), s)

xs = [X0 + (X1 - X0) * (j / (NX - 1)) for j in range(NX)]
xs[0] += 0.002; xs[-1] -= 0.002
def outer(x, a):
    cy, cz = se(a)
    h = hw(x); b = hb(x)
    return (x, cy * max(w(x), 0.01), b + h / 2 + cz * h / 2)
body = loft('shoe', xs, outer, 'upper')

cx0, cx1 = X0 + WALL, THROAT
cxs = [cx0 + (cx1 - cx0) * (j / (NX - 1)) for j in range(NX)]
def inner(x, a):
    cy, cz = se(a)
    k = math.sqrt(max(0.0, min(1.0, (cx1 - x) / 0.35)))        # 前沿 U 形
    k *= math.sqrt(max(0.0, min(1.0, (x - X0) / 0.2)))         # 后跟圆
    b = hb(x) + LINER
    return (x, cy * max((w(x) - WALL) * k, 0.005), b + 1.0 + cz * 1.0)
cut = loft('cut', cxs, inner, 'liner')

m = body.modifiers.new('open', 'BOOLEAN')
m.operation = 'DIFFERENCE'; m.object = cut; m.solver = 'EXACT'
m.material_mode = 'TRANSFER'
bpy.context.view_layer.objects.active = body
bpy.ops.object.modifier_apply(modifier='open')
bpy.data.objects.remove(cut)
# 鞋底：朝下的面
names = [s.material.name for s in body.material_slots]
if 'sole' not in names:
    body.data.materials.append(bpy.data.materials['sole'])
si = [s.material.name for s in body.material_slots].index('sole')
for p in body.data.polygons:
    if p.normal.z < -0.6 and p.center.z < hb(p.center.x) + 0.03:
        p.material_index = si
    p.use_smooth = False

# 鞋跟：后跟底下一根往下收的锥，跟底一截黑钉
HX = X0 + 0.2
prim('cone', 'upper', vertices=12, radius1=0.075, radius2=0.13, depth=HEEL_H - 0.02,
     location=(HX - 0.04, 0, (HEEL_H - 0.02) / 2 + 0.06), rotation=(0, -0.08, 0))
prim('cylinder', 'tip', vertices=12, radius=0.078, depth=0.08, location=(HX - 0.08, 0, 0.04))

ob = join_all(body)
lo = [1e9] * 3; hi = [-1e9] * 3
for v in ob.data.vertices:
    for k in range(3):
        lo[k], hi[k] = min(lo[k], v.co[k]), max(hi[k], v.co[k])
print('BBOX', [round(hi[k] - lo[k], 2) for k in range(3)], flush=True)
mid = Vector([(lo[k] + hi[k]) / 2 for k in range(3)])
s = NOMINAL / max(hi[k] - lo[k] for k in range(3))
ob.matrix_world = Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation(-mid)

render_turntable('heel', active=ob, lean=24, tilt=0.45, roll=0.3, screen_r=42)
