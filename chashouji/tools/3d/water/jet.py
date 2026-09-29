"""白娘子掌心喷出的水柱（2026-09-28 第二版）：3 渲 2 循环序列帧。
用户："不要用瓶子倒水，而是直接从手掌中喷水"；"水流美术风格太 Q 了，要更写实，做出类似 3 渲 2 的体积感"。
第一版是 crew.js drawStream 用粗线段连水滴：出口 40 像素宽、一段段圆头叠起来，读成一只倒扣的瓶子往下倒水。

这里是一股**高压水柱**：掌心处细（出口 r0），往前越喷越粗、越散（r1），表面三组往前滚的波纹（一组鼓包 + 两组反向螺旋），
中轴带一点摆；喷到 ~80% 长度开始碎：柱身收尖、断成水团，再往前是一群往外散的水珠。表面顺着水流的白色流痕（foam）、
出口那一截白（高速带气泡的水是白的），越往前越蓝（base）。所有运动都按 LOOP 整周期写，第 FRAMES 帧 = 第 0 帧。

画面：水柱沿 +X（掌心在左端 X0），正交侧视。引擎（crew.js）把它转到"掌心 → 落点"的方向、长度拉到两点距离。
跑法：blender -b --python jet.py -- <帧数> <采样> <输出目录>  → <目录>/jet_<帧>.png（720×240）
"""
import bpy, math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from waterkit import args, setup, ortho_camera, material, mesh, set_attr, render

FRAMES, SAMP, OUT, START, STEP = args((16, '/tmp/jet'))
W, H, PX = 720, 240, 120            # 画幅、每世界单位几像素（正交宽 = W / PX）
X0, LEN = -2.9, 5.9                 # 掌心在哪、整股（含水珠）多长
R0, R1 = 0.09, 0.40                 # 出口半径、碎开前最粗处半径
BREAK = (0.72, 0.84)                # 柱身在这段（占全长的比例）收尖断开
NU, NT = 170, 28                    # 柱身沿长度 / 一圈的细分
LOOP_N = 1                          # 引擎里一个循环 LOOP 秒（crew.js BAISU_JET.loop），这里只管"整周期"
# 不描边（2026-09-28）：原来 3.4 像素深蓝描边，引擎把水柱加粗 2.2 倍（crew.js JET_W）后描边跟着粗到 7 像素 ——
# 用户："水流描边太粗，有点假，参考真相女神的喷雾做柔一点"。边缘改在 pack_water.py 里往里羽化（EDGE_SOFT）
OUTLINE = 0
LIGHT = (-0.4, -0.6, 0.7)
TONES = [(0.0, 0.7), (0.3, 0.88), (0.65, 1.0), (0.88, 1.16)]
COLORS = ['e4f6ff', '8fd3fa', '4d9fe6', '2f79cf']   # base 0（出口）→ 1（末端）
TAU = 2 * math.pi


def radius(u):
    """柱身基准半径：出口细，往前按 u^0.75 胀到 R1"""
    return R0 + (R1 - R0) * min(1.0, u / BREAK[1]) ** 0.75


def smooth(a, b, x):
    k = max(0.0, min(1.0, (x - a) / (b - a)))
    return k * k * (3 - 2 * k)


def tube(t):
    """t：0~1 一个循环里的相位。返回 顶点、面、base、foam"""
    vs, base, foam = [], [], []
    for i in range(NU + 1):
        u = BREAK[1] * i / NU
        amp = smooth(0.0, 0.35, u)                       # 出口处波纹为 0（从掌心出来是光滑的一束），往前长满
        wob = 0.05 * amp * math.sin(TAU * (2 * u - t))   # 中轴轻轻摆
        cut = 1 - smooth(BREAK[0], BREAK[1], u)          # 末端收尖
        for j in range(NT):
            th = TAU * j / NT
            bulge = (0.16 * math.sin(TAU * (5 * u - 2 * t))
                     + 0.07 * math.sin(TAU * (9 * u - 3 * t) + 3 * th)
                     + 0.05 * math.sin(TAU * (13 * u - 4 * t) - 5 * th))
            rag = 1 + 0.35 * (1 - cut) * math.sin(5 * th + TAU * (7 * u - 2 * t))   # 断口处参差
            r = radius(u) * (1 + amp * bulge) * cut * rag
            x = X0 + LEN * u
            vs.append((x, r * math.cos(th), wob + r * math.sin(th)))
            base.append(u / BREAK[1] * 0.75)
            # 流痕：顺着水流、跟着表面一起往前走的细白条（7 条，随相位蜿蜒）；出口那一截整圈白
            # 第一版相位里带 sin(2π(2u − t))×1.4，条纹沿长度方向扭得太快，断成一截截等长的短划线（像虚线）
            st = math.sin(7 * th + 0.5 * math.sin(TAU * (u - t)) + TAU * 0.25 * u)
            gate = math.sin(TAU * (2.5 * u - 2 * t) + 2 * th)   # 偶尔断一下，断口跟着水往前走
            foam.append(1.0 if u < 0.05 or (st > 0.88 and gate > -0.55 and u > 0.08) else 0.0)
    fs = []
    for i in range(NU):
        for j in range(NT):
            a, b = i * NT + j, i * NT + (j + 1) % NT
            fs.append((a, b, b + NT, a + NT))
    fs.append(tuple(range(NT - 1, -1, -1)))                # 出口封口（藏在掌心水球里）
    return vs, fs, base, foam


# 水珠：碎开之后往外散的一群。每颗按 LOOP 整周期从柱身里冒出来、往前往外飞、变小；数值固定随机（每次渲出来一样）
rnd = random.Random(7)
DROPS = [dict(p=rnd.random(), j=rnd.choice((1, 1, 2)), th=rnd.uniform(0, TAU), r=rnd.uniform(0.05, 0.17),
              out=rnd.uniform(0.4, 1.8), white=rnd.random() < 0.3) for _ in range(30)]


def drops(t):
    """每颗水珠一个小二十面体（沿 X 拉长 1.5 倍）。返回 [(中心, 半径, u, 是否白色)]"""
    res = []
    for d in DROPS:
        k = (d['p'] + d['j'] * t) % 1.0                  # 0：刚从柱身末端冒出 → 1：飞到最远
        u = BREAK[0] - 0.04 + (1.0 - BREAK[0] + 0.04) * k
        rr = R1 * (0.25 + d['out'] * k)                  # 离中轴越来越远（散开）
        rad = d['r'] * (1 - 0.55 * k)                    # 越飞越小
        res.append(((X0 + LEN * u, rr * math.cos(d['th']), rr * math.sin(d['th'])), rad, u, d['white']))
    return res


def ico(center, rad, stretch=1.5):
    """二十面体细分两次（162 顶点：细分一次在屏幕上看得出棱角），沿 X 拉长"""
    g = (1 + 5 ** 0.5) / 2
    v = [(-1, g, 0), (1, g, 0), (-1, -g, 0), (1, -g, 0), (0, -1, g), (0, 1, g), (0, -1, -g), (0, 1, -g),
         (g, 0, -1), (g, 0, 1), (-g, 0, -1), (-g, 0, 1)]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
         (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    v = [tuple(c / math.sqrt(sum(q * q for q in p)) for c in p) for p in v]
    mid = {}
    def m(a, b):
        key = (min(a, b), max(a, b))
        if key not in mid:
            p = [(v[a][i] + v[b][i]) / 2 for i in range(3)]; n = math.sqrt(sum(q * q for q in p))
            v.append(tuple(q / n for q in p)); mid[key] = len(v) - 1
        return mid[key]
    for _ in range(2):
        f2 = []
        for a, b, c in f:
            ab, bc, ca = m(a, b), m(b, c), m(c, a)
            f2 += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        f, mid = f2, {}
    cx, cy, cz = center
    return [(cx + p[0] * rad * stretch, cy + p[1] * rad, cz + p[2] * rad) for p in v], f2


sc = setup(W, H, SAMP, OUTLINE)
ortho_camera(W / PX)
M = material('jet', COLORS, TONES, LIGHT)
os.makedirs(OUT, exist_ok=True)
for f in range(START, FRAMES, STEP):
    t = f / FRAMES
    for ob in list(bpy.data.objects):
        if ob.type == 'MESH': bpy.data.objects.remove(ob)
    vs, fs, base, foam = tube(t)
    ob = mesh('tube', vs, fs, M)
    set_attr(ob, 'base', base); set_attr(ob, 'foam', foam)
    DV, DF, DB, DW = [], [], [], []
    for c, rad, u, white in drops(t):
        v, fc = ico(c, rad)
        n = len(DV); DV += v; DF += [tuple(i + n for i in q) for q in fc]
        DB += [0.4] * len(v); DW += [1.0 if white else 0.0] * len(v)   # 水珠取中间的浅蓝（取末端色太深，一颗颗像蓝莓），三成是白的水沫
    od = mesh('drops', DV, DF, M)
    set_attr(od, 'base', DB); set_attr(od, 'foam', DW)
    render(os.path.join(OUT, 'jet_%03d' % f))
    print('JET frame', f, flush=True)
print('JET_DONE', flush=True)
