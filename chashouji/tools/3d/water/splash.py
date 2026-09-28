"""白娘子水柱打中时的水花（2026-09-28）：3 渲 2 序列帧，播一遍（不循环）。
第一版命中只有粒子（蓝白小圆点 + 深蓝环），跟 3 渲 2 的水柱放在一起是两套画风。

一朵水冠：一圈水膜从撞击点往外、往上张开（绕 AXIS 的旋转面，剖面往上卷），边上拉出 FINGERS 根水指，指尖甩出水珠；
后半段水膜从里往外收成一圈（S0），只剩水指和飞散的水珠。AXIS 朝上偏向镜头 —— 看得到冠口里面，读成"溅开"不是"一根竖管"。
跑法：blender -b --python splash.py -- <帧数> <采样> <输出目录> → <目录>/splash_<帧>.png（320×320）
"""
import bpy, math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from waterkit import args, setup, ortho_camera, material, mesh, set_attr, render
from mathutils import Vector

FRAMES, SAMP, OUT, START, STEP = args((10, '/tmp/splash'))
W = H = 320
SCALE = 4.0                            # 画面宽 = 4 世界单位（80 像素 / 单位）
AXIS = Vector((0, -0.45, 1)).normalized()   # 水冠张开的方向：朝上、往镜头偏
FINGERS = 11
NS, NP = 22, 88                        # 水膜：径向 / 一圈的细分
OUTLINE = 3.0
LIGHT = (-0.4, -0.6, 0.7)
TONES = [(0.0, 0.7), (0.3, 0.88), (0.65, 1.0), (0.88, 1.16)]
COLORS = ['e4f6ff', '8fd3fa', '4d9fe6']
TAU = 2 * math.pi
ORIGIN = Vector((0, 0, -0.9))          # 撞击点在画面中下（水冠往上长）


def frame_of(axis):
    a = axis
    t = Vector((1, 0, 0)) if abs(a.x) < 0.9 else Vector((0, 1, 0))
    u = a.cross(t).normalized(); v = a.cross(u)
    return u, v


U, V = frame_of(AXIS)


def smooth(a, b, x):
    k = max(0.0, min(1.0, (x - a) / (b - a)))
    return k * k * (3 - 2 * k)


def crown(e):
    """e：0~1 播放进度。水膜 = 旋转面；s 从内沿 s0 到冠口 1"""
    R = 0.25 + 1.25 * (1 - (1 - e) ** 2)               # 冠口半径：先快后慢张开
    Hh = 0.65 * math.sin(math.pi * min(1.0, e * 1.3)) + 0.1   # 冠高：先长高再塌（1.1 时深得像一只碗）
    s0 = 0.2 + 0.5 * smooth(0.45, 0.95, e)             # 后半段水膜从里往外收（收到 0.95 时只剩一圈描边）
    vs, base, foam = [], [], []
    for i in range(NS + 1):
        s = s0 + (1 - s0) * i / NS
        for j in range(NP):
            ph = TAU * j / NP
            fing = max(0.0, math.cos(FINGERS * ph + 0.6 * math.sin(3 * ph))) ** 4 * s ** 6   # 水指：只在冠口那一截往外伸
            r = R * s ** 0.8 * (1 + 0.35 * fing * min(1.0, e * 2))   # s^0.8：往外张得快，冠口外翻
            z = Hh * s * s * (1 + 0.5 * fing)
            p = ORIGIN + U * (r * math.cos(ph)) + V * (r * math.sin(ph)) + AXIS * z
            vs.append(tuple(p)); base.append(0.15 + 0.5 * s)
            foam.append(1.0 if s > 0.93 or fing > 0.5 else 0.0)   # 冠口一圈、水指是白的（碎开的水沫）
    fs = [(i * NP + j, i * NP + (j + 1) % NP, (i + 1) * NP + (j + 1) % NP, (i + 1) * NP + j) for i in range(NS) for j in range(NP)]
    return vs, fs, base, foam, R, Hh


rnd = random.Random(3)
DROPS = [dict(k=k, jit=rnd.uniform(-0.15, 0.15), v=rnd.uniform(0.9, 1.6), up=rnd.uniform(0.3, 1.0), r=rnd.uniform(0.06, 0.13))
         for k in range(FINGERS) for _ in range(2)]


def sphere(c, rad, n=10):
    vs = [(c[0] + rad * math.sin(math.pi * i / n) * math.cos(TAU * j / (2 * n)),
           c[1] + rad * math.sin(math.pi * i / n) * math.sin(TAU * j / (2 * n)),
           c[2] + rad * math.cos(math.pi * i / n)) for i in range(n + 1) for j in range(2 * n)]
    fs = [(i * 2 * n + j, i * 2 * n + (j + 1) % (2 * n), (i + 1) * 2 * n + (j + 1) % (2 * n), (i + 1) * 2 * n + j) for i in range(n) for j in range(2 * n)]
    return vs, fs


sc = setup(W, H, SAMP, OUTLINE)
ortho_camera(SCALE)
M = material('splash', COLORS, TONES, LIGHT)
os.makedirs(OUT, exist_ok=True)
for f in range(START, FRAMES, STEP):
    e = (f + 0.5) / FRAMES
    for ob in list(bpy.data.objects):
        if ob.type == 'MESH': bpy.data.objects.remove(ob)
    vs, fs, base, foam, R, Hh = crown(e)
    ob = mesh('crown', vs, fs, M)
    set_attr(ob, 'base', base); set_attr(ob, 'foam', foam)
    # 水珠：从各根水指尖上甩出去（e > 0.3 起），带重力往下掉、变小
    if e > 0.3:
        DV, DF, DW = [], [], []
        for d in DROPS:
            k = e - 0.3
            ph = TAU * d['k'] / FINGERS + d['jit']
            out = R * 1.25 + d['v'] * k * 1.3               # 飞得太远（×2.2）会出画框被裁
            z = Hh * 1.4 + d['up'] * k * 2.2 - 3.5 * k * k
            c = ORIGIN + U * (out * math.cos(ph)) + V * (out * math.sin(ph)) + AXIS * z
            v, fc = sphere(tuple(c), d['r'] * (1 - 0.5 * k))
            n = len(DV); DV += v; DF += [tuple(i + n for i in q) for q in fc]
            DW += [1.0 if d['r'] < 0.08 else 0.0] * len(v)
        od = mesh('drops', DV, DF, M)
        set_attr(od, 'base', [0.35] * len(DV)); set_attr(od, 'foam', DW)
    render(os.path.join(OUT, 'splash_%03d' % f))
    print('SPLASH frame', f, flush=True)
print('SPLASH_DONE', flush=True)
