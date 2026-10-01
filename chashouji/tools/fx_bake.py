"""三人组特效贴图离线烘焙（trio_fx.js 用），2026-10-01。

    python3 tools/fx_bake.py        → web/assets/fx/trio/{beam,glow,ring,frag,dust,slash,band}.webp + atlas.json

全部贴图是**灰度值 + alpha**：RGB 三通道相同，存的是"这一点在色带上的位置" v（0 = 暗边 / 描边，0.45 = 本色，
0.8 = 亮色，1 = 白高光），颜色在运行时由 trio_fx.js 的 ramp() 按调色板映射（每人 beam 的 glow / edge / layers、
每个配方的碎片色）。所以同一张水滴图能出水、焦糖、西瓜汁、辣椒水，一张光束条能出悟空的蓝、排山倒海的橙。

为什么明暗烧在贴图里、颜色不烧：明亮客厅底图上 lighter 加不出来（skill chashouji-fx），发光只能靠"白芯 → 饱和本色 →
深一档的暗边"这条色带自己撑起对比；实体靠暗描边。两件事都是 v 的分布决定的，跟具体颜色无关。

超采样 SS 倍画再平均（alpha 加权），边缘是干净的抗锯齿；噪声全用 FFT 低通白噪声 —— 天然周期，光束条横向无缝平铺。
固定随机种子，逐字节可复现。
"""
import json
import os
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), '..', 'web', 'assets', 'fx', 'trio')
SS = 4
rng = np.random.default_rng(20261001)


# ---------- 工具 ----------

def periodic_noise(h, w, sx, sy, seed):
    """周期噪声 [0,1]：白噪声在频域乘各向异性高斯（sx / sy 是两个方向的特征长度，像素）。sx > sy 拉成横向条纹"""
    r = np.random.default_rng(seed)
    n = r.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    k = np.exp(-((fx * sx) ** 2 + (fy * sy) ** 2) * 2 * np.pi ** 2)
    o = np.real(np.fft.ifft2(np.fft.fft2(n) * k))
    o = (o - o.mean()) / (o.std() + 1e-9)
    return np.clip(0.5 + o * 0.22, 0, 1)


def coords(w, h):
    """超采样网格，像素中心坐标（输出像素单位）"""
    ys, xs = np.mgrid[0:h * SS, 0:w * SS]
    return (xs + 0.5) / SS, (ys + 0.5) / SS


def down(v, a, w, h):
    """超采样 → 输出：alpha 平均，值按 alpha 加权平均（不然边缘的值被透明像素拉黑，描边变粗）"""
    a4 = a.reshape(h, SS, w, SS).mean(axis=(1, 3))
    va = (v * a).reshape(h, SS, w, SS).mean(axis=(1, 3))
    v4 = np.where(a4 > 1e-4, va / np.maximum(a4, 1e-4), 0)
    return v4, a4


def over(v0, a0, v1, a1):
    """(v1, a1) 盖在 (v0, a0) 上"""
    a = a1 + a0 * (1 - a1)
    v = np.where(a > 1e-6, (v1 * a1 + v0 * a0 * (1 - a1)) / np.maximum(a, 1e-6), 0)
    return v, a


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def to_img(v, a):
    v8 = np.clip(np.round(v * 255), 0, 255).astype(np.uint8)
    a8 = np.clip(np.round(a * 255), 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([v8, v8, v8, a8]), 'RGBA')


def poly_sdf(px, py, pts):
    """多边形有符号距离（内负外正），pts 逆 / 顺时针都行"""
    d = np.full(px.shape, 1e9)
    s = np.ones(px.shape)
    n = len(pts)
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        wx, wy = px - ax, py - ay
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
        dx, dy = wx - ex * t, wy - ey * t
        d = np.minimum(d, dx * dx + dy * dy)
        c1 = py >= ay
        c2 = py < by
        c3 = ex * wy > ey * wx
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
    return s * np.sqrt(d)


def solid(sdf, shade, ink=1.6, ink_v=0.04):
    """实体：sdf ≤ 0 是本体（值 = shade），外面一圈 ink 像素的暗描边 —— 赛璐璐角色有线稿，碎片也要有（skill：实体靠轮廓）"""
    a_body = smooth(0.5, -0.5, sdf)
    a_ink = smooth(ink + 0.5, ink - 0.5, sdf)
    v, a = over(np.full(sdf.shape, ink_v), a_ink, shade, a_body)
    return v, a


# ---------- 光束条：外晕 / 中层 / 芯（横截面高斯）+ 光身（平顶带暗边），横向周期噪声 ----------

def bake_beam():
    W, H = 256, 64
    y = (np.arange(H) + 0.5) / H * 2 - 1           # -1..1
    Y = np.repeat(y[:, None], W, axis=1)
    # 外晕：宽的高斯，被低频噪声啃出一缕缕（宽度本身随噪声胀缩 —— 不是一条直边的光管）
    n1 = periodic_noise(H, W, 34, 10, 1)
    n1b = periodic_noise(H, W, 90, 30, 2)
    sig = 0.42 * (0.75 + 0.6 * n1b)
    a_h = np.exp(-(Y / sig) ** 2) * (0.2 + 1.3 * n1)
    a_h = np.clip(a_h, 0, 1) * smooth(1.0, 0.82, np.abs(Y))
    v_h = 0.18 + 0.32 * np.exp(-(Y / 0.35) ** 2) * n1       # 外晕偏暗：映射到 edge 色（暗一档的饱和色，托在亮底图上）
    # 中层：横向拉长的条纹（流动感主要靠它）
    n2 = periodic_noise(H, W, 26, 3.5, 3)
    a_m = np.exp(-(Y / 0.40) ** 2) * (0.25 + 1.35 * n2)
    a_m = np.clip(a_m, 0, 1) * smooth(1.0, 0.7, np.abs(Y))
    v_m = 0.42 + 0.38 * np.exp(-(Y / 0.22) ** 2) + 0.15 * (n2 - 0.5)
    # 芯：窄、亮、几乎不断，有一点细丝
    n3 = periodic_noise(H, W, 18, 2.5, 4)
    a_c = np.clip(np.exp(-(Y / 0.30) ** 2) * (0.85 + 0.35 * n3), 0, 1) * smooth(1.0, 0.75, np.abs(Y))
    v_c = 0.78 + 0.22 * np.exp(-(Y / 0.16) ** 2)
    # 光身：平顶的管子，边上 2~3 px 暗边（亮底图上光束的轮廓靠它 —— 旧的平涂反而因为最外一层暗色立得住），
    # 里面本色往中线提亮，横向条纹在值上（不在 alpha 上：管子本身是实的，流动是亮纹在走）；边缘随低频噪声轻轻起伏
    n4 = periodic_noise(H, W, 30, 4, 5)
    n5 = periodic_noise(H, W, 70, 200, 6)
    Yw = np.abs(Y) * (1 + 0.12 * (n5 - 0.5))
    a_b = smooth(0.95, 0.86, Yw)
    inner = np.clip(1 - Yw / 0.84, 0, 1)
    v_b = np.where(Yw > 0.84, 0.06, 0.4 + 0.42 * inner ** 1.2 + 0.32 * (n4 - 0.5))
    im = Image.new('RGBA', (W, H * 4))
    for i, (v, a) in enumerate([(v_h, a_h), (v_m, a_m), (v_c, a_c), (v_b, a_b)]):
        im.paste(to_img(np.clip(v, 0, 1), a), (0, i * H))
    return im, {n: [0, i * H, W, H] for i, n in enumerate(['halo', 'mid', 'core', 'body'])}


# ---------- 光：四角星闪光、光粒、锥形火花 ----------

def bake_glow():
    cells = {}
    S = 128
    im = Image.new('RGBA', (S * 3, S))
    # 四角星：十字长芒 + 斜向短芒 + 中心光团
    X, Y = coords(S, S)
    x, y = (X - S / 2) / (S / 2), (Y - S / 2) / (S / 2)
    r = np.hypot(x, y)

    def ray(u, w_):           # u 沿芒，w_ 横向
        L = np.clip(1 - np.abs(u), 0, 1)
        return L ** 1.6 * np.exp(-(w_ / (0.012 + 0.07 * L)) ** 2)
    xd, yd = (x + y) / np.sqrt(2), (x - y) / np.sqrt(2)
    I = np.maximum.reduce([ray(x, y), ray(y, x), 0.55 * ray(xd * 1.8, yd), 0.55 * ray(yd * 1.8, xd),
                           np.exp(-(r / 0.16) ** 2), 0.5 * np.exp(-(r / 0.38) ** 2)])
    a = np.clip(I * 1.25, 0, 1)
    v = np.clip(0.25 + 0.75 * np.sqrt(np.clip(I, 0, 1)), 0, 1)
    v4, a4 = down(v, a, S, S)
    im.paste(to_img(v4, a4), (0, 0))
    cells['flare'] = [0, 0, S, S]
    # 光粒：圆形，中心白、往外是本色、最外一圈暗边（一颗颗小光点在米色地板上要靠那圈暗边）
    I = np.exp(-(r / 0.42) ** 2)
    a = np.clip(I * 1.15, 0, 1) * smooth(1.0, 0.9, r)
    v = np.clip(0.15 + 0.85 * I ** 0.7, 0, 1)
    v4, a4 = down(v, a, S, S)
    im.paste(to_img(v4, a4), (S, 0))
    cells['mote'] = [S, 0, S, S]
    # 锥形火花（朝 +x 飞）：头宽尾尖、尾巴渐隐，头部白、中段本色、尾巴暗
    W2, H2 = 128, 32
    X, Y = coords(W2, H2)
    u = X / W2                                      # 0 尾 .. 1 头
    yy = (Y - H2 / 2) / (H2 / 2)
    head = 0.88
    wid = np.where(u < head, 0.12 + 0.75 * (u / head) ** 1.3, 0.87 * np.sqrt(np.clip(1 - ((u - head) / (1 - head)) ** 2, 0, 1)))
    inside = np.abs(yy) < wid
    core = np.exp(-(yy / np.maximum(wid, 1e-3) / 0.55) ** 2)
    a = np.where(inside, 1, 0) * np.clip(u ** 1.2 * 1.3, 0, 1) * (0.55 + 0.45 * core)
    a = a * smooth(0.0, 0.08, wid - np.abs(yy) + 0.04)
    v = np.clip(0.12 + 0.88 * u ** 1.5 * core, 0, 1)
    v4, a4 = down(v, a, W2, H2)
    im.paste(to_img(v4, a4), (S * 2, 0))
    cells['spark'] = [S * 2, 0, W2, H2]
    return im, cells


# ---------- 冲击波环：有厚度，内沿亮、往外压暗，最外一道暗边 ----------

def bake_ring():
    S = 256
    X, Y = coords(S, S)
    x, y = (X - S / 2) / (S / 2), (Y - S / 2) / (S / 2)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    # 沿圆周一点不匀（不是圆规画的线）：周期噪声按角度取
    nz = periodic_noise(64, 256, 22, 6, 7)[32]
    jit = np.interp((th + np.pi) / (2 * np.pi) * 256, np.arange(257), np.append(nz, nz[0]))
    r_in, r_pk, r_out = 0.56, 0.66 + 0.03 * (jit - 0.5), 0.97
    rise = smooth(r_in, r_pk, r)
    fall = smooth(r_out, r_pk + 0.06, r)
    a = rise * fall * (0.8 + 0.25 * jit)
    # 值：内沿 1（白）→ 0.55 本色 → 外沿 0.05（暗边）
    t = np.clip((r - r_pk) / (r_out - r_pk), 0, 1)
    v = np.where(r < r_pk, 1.0, np.clip(1.0 - 1.05 * t ** 0.8, 0.04, 1))
    a = np.clip(a * 1.1, 0, 1)
    v4, a4 = down(v, a, S, S)
    return to_img(v4, a4), {'ring': [0, 0, S, S]}


# ---------- 实体碎片（64 格）----------

def dome_shade(sdf, R, light=(-0.55, -0.65), amb=0.42, spec=None):
    """把 sdf 当成一块"鼓起来"的东西打光：离边越远越高。light 是光从哪边来（屏幕左上）"""
    h = np.clip(-sdf / R, 0, 1)
    hz = np.sqrt(1 - (1 - h) ** 2)
    gy, gx = np.gradient(hz)
    nx, ny = -gx * R, -gy * R
    nz = np.ones_like(nx)
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    lx, ly = light
    lz = 0.6
    ln = np.sqrt(lx * lx + ly * ly + lz * lz)
    d = (nx * lx + ny * ly + nz * lz) / n / ln
    return np.clip(amb + 0.45 * d, 0, 1)


def bake_frag():
    C = 64
    names = []
    tiles = []

    def cell():
        X, Y = coords(C, C)
        return X - C / 2, Y - C / 2

    def add(name, v, a):
        v4, a4 = down(np.clip(v, 0, 1), np.clip(a, 0, 1), C, C)
        names.append(name)
        tiles.append(to_img(v4, a4))

    # 液滴：头朝 +x（顺着速度画），尾巴往后拉尖；半透明身子 + 实的暗边 + 白高光（水 / 焦糖 / 西瓜汁 / 辣椒水共用，调色板定颜色）
    for k, (L, R) in enumerate([(22, 10), (16, 9)]):
        x, y = cell()
        cx = 6
        d_circle = np.hypot(x - cx, y) - R
        tail = np.where(x < cx, np.abs(y) - R * np.clip((x - (cx - L)) / L, 0, 1) ** 0.8, 1e9)
        sdf = np.minimum(d_circle, np.where(x < cx, tail, 1e9))
        sdf = np.where(x < cx - L, 1e9, sdf)
        sh = dome_shade(sdf * SS, R * SS)
        body = 0.32 + 0.45 * sh
        rim = smooth(-3.5, -1.0, sdf)                         # 贴边那一圈深（液体折射的暗边）
        v = body * (1 - rim) + 0.12 * rim
        a = 0.62 + 0.38 * rim
        hl = np.exp(-(((x - cx + 3.5) / 3.2) ** 2 + ((y + R * 0.45) / 1.8) ** 2))
        hl2 = np.exp(-(((x - cx + 9) / 4) ** 2 + ((y + R * 0.15) / 1.0) ** 2)) * 0.6
        v = np.maximum(v, np.clip(hl + hl2, 0, 1) * 1.0)
        a = np.maximum(a, np.clip(hl + hl2, 0, 1))
        v, a2 = solid(sdf, v, ink=1.2, ink_v=0.05)
        a = a2 * np.where(sdf <= 0, a, 1)
        add(f'drop{k}', v, a)

    # 西瓜籽：小、实心、几乎黑，带一道白高光
    for k, (L, R) in enumerate([(24, 12), (20, 10)]):
        x, y = cell()
        d_circle = np.hypot(x - 6, y) - R
        tail = np.where(x < 6, np.abs(y) - R * np.clip((x - (6 - L)) / L, 0, 1) ** 0.9, 1e9)
        sdf = np.minimum(d_circle, tail)
        sdf = np.where(x < 6 - L, 1e9, sdf)
        sh = dome_shade(sdf * SS, R * SS, amb=0.35)
        v = 0.25 + 0.3 * sh
        hl = np.exp(-(((x - 3) / 6) ** 2 + ((y + R * 0.4) / 2.2) ** 2))
        v = np.maximum(v, hl)
        v, a = solid(sdf, v, ink=1.4, ink_v=0.0)
        add(f'seed{k}', v, a)

    # 木屑：不规则三角 / 四边形薄片，两个面一明一暗（翻转时读出是片），木纹，暗描边
    for k in range(3):
        x, y = cell()
        n = 3 + (k == 2)
        ang = np.sort(rng.uniform(0, 2 * np.pi, n)) if k else np.array([0.3, 2.3, 4.1])
        rad = rng.uniform(15, 25, n)
        pts = [(np.cos(t) * r_ * 1.15, np.sin(t) * r_ * 0.75) for t, r_ in zip(ang, rad)]
        sdf = poly_sdf(x, y, pts)
        split = (x * 0.4 + y) > rng.uniform(-4, 4)
        grain = 0.5 + 0.5 * np.sin(x * 0.9 + 1.5 * np.sin(y * 0.25 + k))
        v = np.where(split, 0.72, 0.46) - 0.1 * grain
        edge_hl = smooth(-2.5, -0.5, sdf) * np.where(split, 0.2, 0.0)
        v = v + edge_hl
        v, a = solid(sdf, v, ink=1.6)
        add(f'chip{k}', v, a)

    # 塑料 / 石子碎块：斜切面（三块面三档亮）
    for k in range(2):
        x, y = cell()
        ang = np.sort(rng.uniform(0, 2 * np.pi, 5))
        pts = [(np.cos(t) * rng.uniform(12, 19), np.sin(t) * rng.uniform(10, 16)) for t in ang]
        sdf = poly_sdf(x, y, pts)
        th = np.arctan2(y, x)
        v = np.where(th < -1.2, 0.85, np.where(th < 1.0, 0.55, 0.36))
        v = np.where(sdf > -4, v * 0.9 + 0.08, 0.6 + 0.0 * v)          # 中间平台 + 一圈斜面
        v, a = solid(sdf, v, ink=1.6)
        add(f'shard{k}', v, a)

    # 花瓣：尖头圆尾（尖朝 +x），根部深、瓣尖亮，一条中脉，轻描边
    for k, (L, W_) in enumerate([(25, 15), (22, 13), (26, 11)]):
        x, y = cell()
        u = (x + L) / (2 * L)                                             # 0 根 .. 1 尖
        half = W_ * np.sin(np.pi * np.clip(u, 0, 1) ** 0.75) * (1 - 0.25 * u)
        sdf = np.where((u >= 0) & (u <= 1), np.abs(y + 3 * np.sin(u * 3.1) * (k - 1)) - half, 1e9)
        sdf = np.minimum(sdf, 50)
        notch = np.hypot(x - L + 1, y) - 4                               # 瓣尖一个小缺口（真花瓣的样子）
        sdf = np.maximum(sdf, -notch)
        cup = 1 - np.abs(y) / np.maximum(half, 1)
        v = 0.38 + 0.38 * u + 0.12 * cup
        vein = np.exp(-(y / 0.8) ** 2) * (u > 0.1) * (u < 0.8)
        v = v - 0.12 * vein
        v, a = solid(sdf, np.clip(v, 0, 1), ink=1.2, ink_v=0.08)
        add(f'petal{k}', v, a)

    # 羽毛：羽轴 + 两侧羽片（斜向羽枝纹），尖朝 +x，根部一截绒
    for k in range(2):
        x, y = cell()
        L = 28
        u = (x + L) / (2 * L)
        half = 10 * np.sin(np.pi * np.clip(u, 0, 1) ** 0.6) * (1.0 - 0.15 * k)
        bend = 2.5 * np.sin(u * 3.1) * (1 if k else -1)
        yy = y - bend
        sdf = np.where((u >= 0.0) & (u <= 1), np.abs(yy) - half * (0.86 + 0.14 * np.abs(np.sin(x * 0.9 + np.sign(yy) * 1.3))), 1e9)
        sdf = np.minimum(sdf, 50)
        barb = 0.5 + 0.5 * np.sin((x - np.abs(yy) * 1.6) * 1.3)
        v = 0.9 - 0.26 * barb * (np.abs(yy) / np.maximum(half, 1))
        shaft = np.exp(-(yy / 0.9) ** 2) * (u > 0.02)
        v = v - 0.4 * shaft
        fluff = (u < 0.25)
        v = np.where(fluff, v + 0.08, v)
        v, a = solid(sdf, np.clip(v, 0, 1), ink=1.1, ink_v=0.12)
        add(f'feather{k}', v, a)

    # 金星：五角星，每个角劈成一明一暗两个面（倒角）—— 最便宜的"立体"
    for k, R in enumerate([25, 22]):
        x, y = cell()
        pts = []
        for i in range(10):
            t = -np.pi / 2 + i * np.pi / 5
            rr = R if i % 2 == 0 else R * 0.45
            pts.append((np.cos(t) * rr, np.sin(t) * rr + 2))
        sdf = poly_sdf(x, y, pts)
        th = np.arctan2(y - 2, x) + np.pi / 2
        seg = np.mod(th, 2 * np.pi / 5) / (2 * np.pi / 5)          # 每个角里的相位，0.5 = 角的中线
        face = np.where(seg < 0.5, 1.0, 0.0)
        ang_c = (np.floor(np.mod(th, 2 * np.pi) / (2 * np.pi / 5)) + 0.5) * 2 * np.pi / 5 - np.pi / 2
        lit = np.cos(ang_c - (-2.3))                                    # 光从左上
        v = 0.52 + 0.16 * lit + np.where(face > 0, 0.14, -0.1)
        hl = np.exp(-(((x + 4) / 4) ** 2 + ((y - 0) / 3) ** 2)) * 0.5
        v = np.clip(v + hl, 0, 1)
        v, a = solid(sdf, v, ink=1.8)
        add(f'star{k}', v, a)

    # 珍珠 / 球：球面打光 + 高光
    x, y = cell()
    R = 15
    sdf = np.hypot(x, y) - R
    sh = dome_shade(sdf * SS, R * SS, amb=0.3)
    v = 0.25 + 0.55 * sh
    v = np.maximum(v, np.exp(-(((x + 5) / 3.5) ** 2 + ((y + 6) / 2.5) ** 2)))
    v, a = solid(sdf, v, ink=1.4)
    add('pearl', v, a)

    # 西瓜皮：弯的一条，外侧深（皮）、里侧浅（白瓤边）
    for k in range(2):
        x, y = cell()
        Rr = 40 + 8 * k
        cy = Rr - 6
        r = np.hypot(x, y - cy)
        th = np.arctan2(x, -(y - cy))
        span = 0.42 - 0.06 * k
        sdf = np.maximum(np.abs(r - Rr + 3) - 6, (np.abs(th) - span) * Rr)
        v = np.where(r > Rr - 1.5, 0.2, np.where(r > Rr - 5, 0.55, 0.92))
        v, a = solid(sdf, v, ink=1.5)
        add(f'rind{k}', v, a)

    cols = 8
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new('RGBA', (cols * C, rows * C))
    cells = {}
    for i, (n, t) in enumerate(zip(names, tiles)):
        cx, cy = (i % cols) * C, (i // cols) * C
        im.paste(t, (cx, cy))
        cells[n] = [cx, cy, C, C]
    return im, cells


# ---------- 尘土：一团团鼓起来的烟，上亮下暗（有体积），边缘被噪声啃软 ----------

def bake_dust():
    S = 128
    im = Image.new('RGBA', (S * 4, S))
    cells = {}
    for k in range(4):
        X, Y = coords(S, S)
        x, y = (X - S / 2) / (S / 2), (Y - S / 2) / (S / 2)
        r2 = np.random.default_rng(100 + k)
        dens = np.zeros_like(x)
        for _ in range(7):
            bx, by = r2.uniform(-0.38, 0.38), r2.uniform(-0.2, 0.3)
            br = r2.uniform(0.22, 0.4)
            dens += np.exp(-(((x - bx) ** 2 + (y - by) ** 2) / br ** 2) * 1.6)
        nz = periodic_noise(S * SS, S * SS, 40, 40, 200 + k)
        dens = dens * (0.65 + 0.7 * nz)
        a = np.clip((dens - 0.35) * 1.4, 0, 1) ** 0.9 * smooth(1.0, 0.75, np.hypot(x, y))
        # 上亮下暗：拿密度场往左上方挪一点的差当"受光"
        sh = np.clip(0.55 - 0.45 * y + 0.35 * (nz - 0.5), 0, 1)
        v = 0.25 + 0.6 * sh
        v4, a4 = down(v, a * 0.9, S, S)
        im.paste(to_img(v4, a4), (k * S, 0))
        cells[f'dust{k}'] = [k * S, 0, S, S]
    return im, cells


# ---------- 刀光序列帧：4 帧（划开 → 满弧 → 拉丝 → 碎散）----------

def bake_slash():
    W, H = 256, 160
    N = 4
    im = Image.new('RGBA', (W * N, H))
    cells = {}
    X, Y = coords(W, H)
    cx, cy, R = W / 2, H * 1.0, H * 0.74
    x, y = X - cx, Y - cy
    r = np.hypot(x, y)
    th = np.arctan2(x, -y)                       # 0 = 正上，往右正
    span = 1.05
    u = (th + span) / (2 * span)                 # 0 弧头（起刀） .. 1 弧尾
    streak = periodic_noise(64, 512, 40, 1.5, 9)
    for f in range(N):
        reach = [0.55, 1.0, 1.0, 1.0][f]         # 划到哪儿
        thick = [0.16, 0.2, 0.13, 0.08][f] * R
        tail0 = [0.0, 0.0, 0.25, 0.5][f]         # 弧根开始收掉
        # 月牙：厚度在弧中段最大，两头尖；刀口在内沿（亮），外沿拖成暗色
        prof = np.sin(np.pi * np.clip((u - tail0) / max(1e-3, reach - tail0), 0, 1)) ** 0.8
        w_ = thick * prof
        d = r - R
        inside = (u >= tail0) & (u <= reach) & (d > -w_ * 0.35) & (d < w_)
        t = np.clip((d + w_ * 0.35) / np.maximum(w_ * 1.35, 1e-3), 0, 1)
        si = np.interp(np.clip(u, 0, 1) * 511, np.arange(512), streak[20 + f * 8])
        # 横截面：刀口（内沿）白 → 本色 → 外沿一道暗边，整条是实的（第一版外沿一路淡出，粉睡衣上读成一团绿雾）
        a = inside * smooth(1.0, 0.86, t) * (0.65 + 0.5 * si if f >= 2 else 1.0)
        a = a * smooth(0, 0.04, u - tail0) * smooth(0, 0.05, reach - u)
        v = np.where(t < 0.16, 1.0, np.where(t < 0.74, 0.85 - 0.5 * (t - 0.16) / 0.58, 0.06))
        if f >= 2:                                # 拉丝：沿弧的细线，一缕缕
            fil = np.clip((si - 0.45) * 3, 0, 1) * smooth(R + thick * 1.6, R, r) * smooth(R - thick * 0.8, R, r)
            a = np.maximum(a, fil * (0.8 if f == 2 else 0.5) * (u > tail0) * (u < 1))
            v = np.where(fil > a * 0.9, 0.6, v)
        v4, a4 = down(v, np.clip(a, 0, 1), W, H)
        im.paste(to_img(v4, a4), (f * W, 0))
        cells[f'slash{f}'] = [f * W, 0, W, H]
    return im, cells


# ---------- 带状物贴图条（第二批，P4②③ / P10）：沿长度平铺（横向周期），横截面烧明暗 ----------
# 每条 256×64：x 沿带子长度（运行时按弧长取，周期 256），y 横截面（行 0 / 64 = 两条边，32 = 中线）。
# 描边不烧进来：带子按段铺，每段宽度不一样（绸子扭转、末梢渐细），烧在贴图里的边对不上段的边 —— 描边由 trio_fx.js 沿两条边各描一笔。

def bake_band():
    W, H = 256, 64
    X, Y = coords(W, H)
    y = (Y - H / 2) / (H / 2)                       # -1 .. 1（-1 = 上边，光从上来）
    ay = np.abs(y)
    edge_a = smooth(1.0, 0.9, ay)                   # 两条边抗锯齿
    strips = {}

    def cyl(light=0.55):
        """圆柱横截面的明暗：法线 (y, sqrt(1 - y²))，光从上前方来"""
        nz = np.sqrt(np.clip(1 - y * y, 0, 1))
        return np.clip(light * nz + 0.45 * (-y) * 0.9 + 0.25, 0, 1)

    def tile(seed, sx, sy):                         # 输出分辨率的周期噪声放大到超采样网格（横向周期保持 256）
        n = periodic_noise(H, W, sx, sy, seed)
        return np.repeat(np.repeat(n, SS, axis=0), SS, axis=1)

    # 绸：中间略鼓（亮）、两边卷边压暗，沿长度一缕缕的织纹光泽（低频、细长）。正反面共用，运行时换调色板
    n = tile(31, 60, 3)
    v = 0.5 + 0.1 * (1 - ay) + 0.16 * (n - 0.5)
    v = np.where(ay > 0.82, 0.3 + 0.1 * (n - 0.5), v)
    strips['silk'] = (v, edge_a)
    # 光泽：绸面上一条软的高光带（中线偏上），沿长度断续 —— 运行时按扭转角调透明度叠上去
    n = tile(32, 70, 8)
    a = np.exp(-((y + 0.15) / 0.38) ** 2) * np.clip(0.2 + 1.2 * n, 0, 1) * edge_a
    strips['sheen'] = (np.full(y.shape, 0.97), np.clip(a, 0, 1))
    # 剑身（软鞭剑，金属）：暗边 → 下斜面 → 血槽 → 上斜面亮 → 一条白刃光
    n = tile(33, 90, 4)
    v = np.where(y < -0.3, 0.74, 0.5) + 0.05 * (n - 0.5)
    v = np.where(ay < 0.13, 0.36, v)
    v = np.maximum(v, np.exp(-((y + 0.56) / 0.07) ** 2))
    v = np.where(ay > 0.84, 0.07, v)
    strips['blade'] = (np.clip(v, 0, 1), edge_a)
    # 竹：圆柱明暗 + 细纤维 + 每 64 px 一个竹节（暗缝 + 亮棱）
    n = tile(34, 50, 1.2)
    v = 0.2 + 0.62 * cyl() + 0.08 * (n - 0.5)
    m = np.mod(X, 64)
    v = np.where(m < 2.2, 0.12, np.where(m < 4.6, np.maximum(v, 0.9 - 0.2 * ay), v))
    v = np.where(ay > 0.86, 0.06, v)
    strips['bamboo'] = (np.clip(v, 0, 1), edge_a)
    # 皮肤（橡皮臂）：圆柱明暗，每 64 px 一道弯的褶（拉长时运行时把 u 放稀，褶跟着拉开 = 拉伸纹）
    v = 0.24 + 0.62 * cyl(0.5)
    crease = np.mod(X - 10 * y * y, 64)
    v = v - 0.18 * np.exp(-((crease - 32) / 1.3) ** 2) * (ay < 0.75)
    v = np.where(ay > 0.86, 0.06, v)
    strips['skin'] = (np.clip(v, 0, 1), edge_a)
    # 麻绳：三股斜绞（股间暗缝）+ 毛刺纤维，边缘被毛刺啃得不齐
    n = tile(35, 5, 1.0)
    ph = np.mod(X / 21.33 + y * 0.7, 1.0)
    strand = np.sin(np.pi * ph) ** 0.6
    v = 0.12 + 0.5 * strand * cyl(0.6) + 0.25 * cyl(0.6) + 0.1 * (n - 0.5)
    v = np.where(ay > 0.84, 0.08, v)
    rough = smooth(1.0, 0.88, ay + 0.06 * (n - 0.5))
    strips['rope'] = (np.clip(v, 0, 1), rough)
    # 水柱：半透明水身（中间透、边缘一圈折射暗边更实），上沿一条断续的白高光、下沿一道淡的，水身里流动的明暗
    n = tile(36, 30, 6)
    n2 = tile(37, 40, 3)
    body_a = 0.5 + 0.35 * smooth(0.55, 0.9, ay) + 0.12 * (n - 0.5)
    v = 0.55 + 0.18 * (n - 0.5)
    v = np.where(ay > 0.8, 0.14, v)
    hl = np.exp(-((y + 0.42) / 0.09) ** 2) * np.clip((n2 - 0.45) * 4, 0, 1)
    hl2 = np.exp(-((y - 0.5) / 0.06) ** 2) * np.clip((n2 - 0.6) * 3, 0, 1) * 0.6
    v = np.maximum(v, np.clip(hl + hl2, 0, 1))
    a = np.maximum(body_a, np.clip(hl + hl2, 0, 1)) * edge_a
    strips['water'] = (np.clip(v, 0, 1), np.clip(a, 0, 1))
    # 拖尾：一缕软光（中间亮、两边淡），沿长度被噪声扯成一丝丝（火尾、拖光共用，运行时调色板定颜色）
    n = tile(38, 28, 6)
    a = np.exp(-(y / 0.5) ** 2) * np.clip(0.4 + 0.9 * n, 0, 1) * smooth(1.0, 0.8, ay)
    v = 0.2 + 0.8 * np.exp(-(y / 0.3) ** 2) * (0.7 + 0.3 * n)
    strips['trail'] = (np.clip(v, 0, 1), np.clip(a, 0, 1))

    names = list(strips)
    im = Image.new('RGBA', (W, H * len(names) + 64))
    cells = {}
    for i, k in enumerate(names):
        v4, a4 = down(*strips[k], W, H)
        im.paste(to_img(v4, a4), (0, i * H))
        cells[k] = [0, i * H, W, H]
    # 金铃（G13 白绸梢）：铃身（上圆下张口）+ 口沿一道厚边 + 一道开缝 + 顶上的环，圆鼓鼓地打光
    C = 64
    X2, Y2 = coords(C, C)
    x, y = X2 - C / 2, Y2 - C / 2 - 2
    pts = [(-17, 14), (-14, 6), (-12, -6), (-8, -13), (0, -16), (8, -13), (12, -6), (14, 6), (17, 14)]
    body = poly_sdf(x, y, pts + [(17, 17), (-17, 17)])
    loop = np.abs(np.hypot(x, y + 21) - 5) - 1.8
    sdf = np.minimum(body, loop)
    sh = dome_shade(body * SS, 12 * SS, amb=0.38)
    v = 0.3 + 0.62 * sh
    v = np.where(y > 13, 0.42 + 0.3 * smooth(17, 13, y), v)                              # 口沿
    slot = (np.abs(x) < 9) & (np.abs(y - 9) < 1.4)
    v = np.where(slot, 0.06, v)
    v = np.where(loop < 0, 0.62, v)
    v = np.maximum(v, np.exp(-(((x + 6) / 2.6) ** 2 + ((y + 6) / 4.5) ** 2)))           # 高光
    v, a = solid(sdf, np.clip(v, 0, 1), ink=1.5)
    v4, a4 = down(v, a, C, C)
    im.paste(to_img(v4, a4), (0, H * len(names)))
    cells['bell'] = [0, H * len(names), C, C]
    return im, cells


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    for name, fn in [('beam', bake_beam), ('glow', bake_glow), ('ring', bake_ring), ('frag', bake_frag), ('dust', bake_dust), ('slash', bake_slash), ('band', bake_band), ('beam2', bake_beam2), ('rip', bake_rip)]:
        im, cells = fn()
        p = os.path.join(OUT, name + '.webp')
        if name == 'rip':                                       # 42 格序列帧，无损 425 KB；软的东西有损看不出来（q82 + alpha q60）
            im.save(p, 'WEBP', quality=82, alpha_quality=60, method=6)
        else:
            im.save(p, 'WEBP', lossless=True, method=6)
        meta[name] = {'src': f'assets/fx/trio/{name}.webp', 'size': list(im.size), 'cells': cells}
        print(f'{name:6s} {im.size[0]}x{im.size[1]} {os.path.getsize(p) / 1024:.1f} KB')
    with open(os.path.join(OUT, 'atlas.json'), 'w') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)



# ====================================================================================================================
# 精特1b（2026-10-01 用户："光束圈太规范的圆、直线光束太直太死板"）：去规则的冲击波与光束。三条路并排比：
#   A  程序化：冲击波 = 极坐标噪声位移的涟漪序列帧（外缘不圆、粗细不匀、随时间断成弧段、两三道波前错时扩散、内部能量纹）；
#      光束 = 边缘被噪声啃毛的贴图条（外晕一缕缕、光身边缘起伏、芯亮度沿长度不匀）+ 运行时横向波动 / 脉动 / 游丝 / 电弧（trio_fx.js）
#   B  生图：generate_image 出的冲击波、光束能量流（tools/fx_src/gen_*.png，品红幕布 / 自带 alpha），抠像转成色带位置 v + alpha
#   AB A 管形状和动、B 管质感：涟漪序列帧的波带里按极坐标贴 B 冲击波的纹理；光束 A 的网格 + B 的束身贴图
# 产物：beam2.webp（光束条）、rip.webp（冲击波序列帧 + B 单帧）
# ====================================================================================================================

SRC = os.path.join(os.path.dirname(__file__), 'fx_src')


def gen_va(path):
    """生图 → (v, alpha)，0..1 浮点、原尺寸。自带 alpha 的直接用；品红幕布按"品红度" min(R, B) − G 抠（int16，防 uint8 下溢）。
    v = 亮度拉伸到色带位置（深蓝描边 → 0.1 上下、青色本体 → 0.5、白芯 → 1）：颜色在运行时由调色板重新给"""
    im = np.array(Image.open(path).convert('RGBA')).astype(np.int16)
    r, g, b, a = im[..., 0], im[..., 1], im[..., 2], im[..., 3]
    if a.min() < 250:
        al = a / 255.0
    else:
        m = np.minimum(r, b) - g
        al = np.clip(1 - (m - 40) / 120.0, 0, 1)
        r = np.where(al < 1, np.minimum(r, g + 40), r)       # 去色溢：只动过渡带
        b = np.where(al < 1, np.minimum(b, g + 40), b)
    lum = (0.3 * r + 0.59 * g + 0.11 * b) / 255.0
    v = np.clip((lum - 0.06) / 0.86, 0, 1)
    return v, al


def resize_va(v, a, w, h):
    """带 alpha 的缩放：v 预乘 alpha 缩，再除回去（不让透明处的 v 渗进边缘）"""
    A = np.array(Image.fromarray((a * 65535).astype(np.uint32).astype(np.int32), 'I').resize((w, h), Image.LANCZOS)).astype(float) / 65535
    VA = np.array(Image.fromarray(((v * a) * 65535).astype(np.uint32).astype(np.int32), 'I').resize((w, h), Image.LANCZOS)).astype(float) / 65535
    A = np.clip(A, 0, 1)
    return np.clip(np.where(A > 1e-3, VA / np.maximum(A, 1e-3), 0), 0, 1), A


def loopx(v, a, W):
    """横向首尾交叉淡化成周期 W 的条（输入宽 > W）：x ∈ [0, W)，尾部 ov 列与开头淡化相接"""
    n = v.shape[1]
    ov = n - W
    out_v, out_a = v[:, :W].copy(), a[:, :W].copy()
    k = np.linspace(0, 1, ov)[None, :]
    out_a[:, :ov] = a[:, :ov] * k + a[:, W:W + ov] * (1 - k)
    out_v[:, :ov] = (v[:, :ov] * a[:, :ov] * k + v[:, W:W + ov] * a[:, W:W + ov] * (1 - k)) / np.maximum(out_a[:, :ov], 1e-4)
    return out_v, out_a


def bake_beam2():
    W, H = 256, 64
    X, Y = coords(W, H)
    y = (Y - H / 2) / (H / 2)
    ay = np.abs(y)
    strips = {}

    def tile(seed, sx, sy):
        n = periodic_noise(H, W, sx, sy, seed)
        return np.repeat(np.repeat(n, SS, axis=0), SS, axis=1)

    # 外晕（被啃毛）：一缕缕往外飘的软光，边缘按噪声阈值侵蚀 —— 不是一条直边的光管
    n1, n2, n3 = tile(51, 30, 7), tile(52, 80, 20), tile(53, 12, 3)
    reach = 0.55 + 0.4 * n2                                        # 这一列外晕伸多远
    a = np.exp(-(y / (0.5 * reach)) ** 2) * (0.25 + 1.2 * n1)
    a = a * smooth(0.25, 0.55, n3 + 0.5 * (1 - ay / np.maximum(reach, 0.2)))   # 侵蚀：越往外越容易被啃掉
    a = np.clip(a, 0, 1) * smooth(1.0, 0.85, ay)
    v = 0.16 + 0.35 * np.exp(-(y / 0.35) ** 2) * n1
    strips['haloE'] = (np.clip(v, 0, 1), a)
    # 光身（毛边）：平顶管，边缘半宽按低频噪声起伏 ±18%，再被高频噪声啃出缺口和外溢的小火苗；暗边照旧（亮底图靠它立住）
    n4, n5, n6 = tile(54, 26, 4), tile(55, 40, 64), tile(56, 6, 2)
    edge = 0.78 + 0.16 * (n5 - 0.5) * 2 + 0.06 * (n6 - 0.5) * 2
    a = smooth(edge + 0.1, edge, ay)
    tongue = smooth(0.62, 0.8, n6) * smooth(edge + 0.22, edge, ay) * (ay > edge)          # 外溢的小火苗
    a = np.maximum(a, tongue * 0.9)
    inner = np.clip(1 - ay / np.maximum(edge - 0.08, 0.1), 0, 1)
    v = np.where(ay > edge - 0.08, 0.07, 0.4 + 0.42 * inner ** 1.2 + 0.32 * (n4 - 0.5))
    v = np.where(tongue > 0.3, 0.55, v)
    strips['bodyE'] = (np.clip(v, 0, 1), np.clip(a, 0, 1))
    # 中层（亮纹）：拉长的条纹，强度沿长度有大块明暗（一股股往前推）
    n7, n8 = tile(57, 24, 3.5), tile(58, 120, 64)
    a = np.exp(-(y / 0.42) ** 2) * (0.15 + 1.4 * n7) * (0.5 + 0.9 * n8)
    a = np.clip(a, 0, 1) * smooth(1.0, 0.7, ay)
    v = 0.42 + 0.4 * np.exp(-(y / 0.22) ** 2) + 0.18 * (n7 - 0.5)
    strips['midE'] = (np.clip(v, 0, 1), a)
    # 芯：亮度沿长度不匀（低频噪声调宽度和亮度），偶尔细到一线
    n9, n10 = tile(59, 70, 64), tile(60, 16, 2.5)
    wid = 0.2 + 0.18 * n9
    a = np.clip(np.exp(-(y / wid) ** 2) * (0.7 + 0.5 * n10), 0, 1) * smooth(1.0, 0.75, ay)
    v = 0.7 + 0.3 * np.exp(-(y / (wid * 0.5)) ** 2) * (0.6 + 0.4 * n9)
    strips['coreE'] = (np.clip(v, 0, 1), a)
    names = list(strips)
    rows = []
    for k in names:
        rows.append(down(*strips[k], W, H))
    # B：生图束身。a 当光身（带深蓝暗边），b 只留亮丝当中层。束身大约在图高 30%~70%，取中间一条、按 64 行缩、横向交叉淡化成 256 周期
    for name, path, only_hot in [('bodyB', 'gen_beam_a.png', False), ('midB', 'gen_beam_b.png', True)]:
        v, a = gen_va(os.path.join(SRC, path))
        hh = v.shape[0]
        rr = np.where(a.mean(axis=1) > 0.05)[0]
        y0, y1 = max(0, rr[0] - 8), min(hh, rr[-1] + 8)
        v, a = v[y0:y1], a[y0:y1]
        Wn = int(round(v.shape[1] * H / (y1 - y0)))
        v, a = resize_va(v, a, Wn, H)
        v, a = loopx(v, a, W)
        if only_hot:
            a = a * smooth(0.45, 0.8, v)
        rows.append((v, a))
        names.append(name)
    im = Image.new('RGBA', (W, H * len(names)))
    cells = {}
    for i, (k, (v, a)) in enumerate(zip(names, rows)):
        im.paste(to_img(v, a), (0, i * H))
        cells[k] = [0, i * H, W, H]
    return im, cells


def ring_band_tex(path, NT=512, NR=48):
    """B 冲击波按极坐标展开成"波带纹理"：每个角度找这一圈的内外沿（alpha 加权的径向分布），把这一段拉成 NR 行 → (NR, NT) 的 v / alpha"""
    v, a = gen_va(path)
    h, w = v.shape
    cy, cx = h / 2, w / 2
    th = np.linspace(-np.pi, np.pi, NT, endpoint=False)
    rs = np.linspace(0, min(cx, cy) * 0.98, 400)
    xs = cx + np.cos(th)[None, :] * rs[:, None]
    ys = cy + np.sin(th)[None, :] * rs[:, None]
    xi, yi = np.clip(xs.astype(int), 0, w - 1), np.clip(ys.astype(int), 0, h - 1)
    A, Vv = a[yi, xi], v[yi, xi]                                   # (400, NT)
    cum = np.cumsum(A, axis=0)
    tot = cum[-1] + 1e-6
    r_in = rs[np.argmax(cum > tot * 0.04, axis=0)]
    r_out = rs[np.argmax(cum > tot * 0.97, axis=0)]
    t = np.linspace(0, 1, NR)[:, None]
    rr = r_in[None, :] * (1 - t) + r_out[None, :] * t
    xi = np.clip((cx + np.cos(th)[None, :] * rr).astype(int), 0, w - 1)
    yi = np.clip((cy + np.sin(th)[None, :] * rr).astype(int), 0, h - 1)
    return v[yi, xi], a[yi, xi]                                    # 行 0 = 内沿、NR−1 = 外沿


def bake_rip():
    """冲击波：A 序列帧 2 变体 × 10 帧、AB 序列帧 2 × 10、B 单帧 2 张。格 192（运行时最大画到 ~300 px，软的东西放大不露怯）"""
    C, NF = 192, 10
    X, Y = coords(C, C)
    x, y = (X - C / 2) / (C / 2), (Y - C / 2) / (C / 2)
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    u = (th + np.pi) / (2 * np.pi)                                 # 0..1 绕一圈
    tiles, names = [], []
    btex = [ring_band_tex(os.path.join(SRC, p)) for p in ('gen_ring_a.png', 'gen_ring_b.png')]

    def polar(nz, tau, rows):
        """周期噪声表 nz（rows × 256，行 = 时间、列 = 角度）在 (u, tau) 处插值 → 与 u 同形"""
        fr = tau * (rows - 1)
        r0 = int(np.floor(fr)); r1 = min(rows - 1, r0 + 1); k = fr - r0
        row = nz[r0] * (1 - k) + nz[r1] * k
        return np.interp(u * 256, np.arange(257), np.append(row, row[0]))

    for var in range(2):
        nzR = periodic_noise(64, 256, 14, 10, 300 + var)            # 波前半径起伏
        nzT = periodic_noise(64, 256, 9, 8, 310 + var)              # 粗细
        nzG = periodic_noise(64, 256, 7, 6, 320 + var)              # 断成弧段
        nzR2 = periodic_noise(64, 256, 11, 10, 330 + var)
        nzW = periodic_noise(64, 256, 3, 14, 340 + var)             # 外沿甩出的游丝（沿角度细长）
        tex = periodic_noise(C * SS, C * SS, 30, 30, 350 + var)     # 波带里的能量纹（A）
        for mode in ('A', 'AB'):
            bv, ba = btex[var]
            for f in range(NF):
                tau = (f + 0.5) / NF
                grow = 1 - (1 - tau) ** 2.4
                # 主波前：半径随角度起伏 ±10%，粗细 0.45~1.55 倍、越扩越薄；后期按阈值断开成弧段
                R1 = (0.26 + 0.6 * grow) * (1 + 0.2 * (polar(nzR, tau, 64) - 0.5))
                T1 = (0.12 * (1 - tau) ** 0.7 + 0.02) * (0.45 + 1.1 * polar(nzT, tau, 64))
                gate = smooth(-0.07, 0.07, polar(nzG, tau, 64) - (0.12 + 0.55 * tau ** 1.3))
                d = r - R1
                bt = np.clip((d + T1 * 0.35) / (T1 * 1.35), 0, 1)       # 0 内沿 .. 1 外沿
                inb = smooth(-T1 * 0.35 - 0.012, -T1 * 0.35 + 0.012, d) * smooth(T1 + 0.012, T1 - 0.012, d)
                if mode == 'A':
                    tx = 0.75 + 0.5 * (tex - 0.5) * 2
                    a1 = inb * gate * np.clip(tx, 0.2, 1)
                    v1 = np.where(bt < 0.2, 1.0, np.where(bt < 0.78, 0.9 - 0.45 * (bt - 0.2) / 0.58, 0.06))
                    v1 = np.clip(v1 + 0.12 * (tex - 0.5), 0, 1)
                else:                                                     # AB：波带里贴 B 冲击波的纹理（按角度、带内位置取）
                    NR, NT = bv.shape
                    ti = np.clip((bt * (NR - 1)).astype(int), 0, NR - 1)
                    ui = ((u * 1.0 + 0.13 * var) % 1 * NT).astype(int) % NT
                    sbv, sba = bv[ti, ui], ba[ti, ui]
                    a1 = inb * gate * np.clip(0.25 + 0.95 * sba, 0, 1)
                    v1 = np.where(bt > 0.8, 0.06, np.clip(0.2 + 0.85 * sbv, 0, 1))
                    v1 = np.where(bt < 0.12, np.maximum(v1, 0.92), v1)
                # 第二道波前（晚一点、细、淡）
                tau2 = max(0.0, (tau - 0.18) / 0.82)
                R2 = (0.18 + 0.5 * (1 - (1 - tau2) ** 2.4)) * (1 + 0.24 * (polar(nzR2, tau, 64) - 0.5))
                T2 = (0.06 * (1 - tau2) + 0.01) * (0.5 + polar(nzT, 1 - tau, 64))
                d2 = r - R2
                a2 = smooth(T2 + 0.01, T2 - 0.01, np.abs(d2)) * smooth(-0.1, 0.1, polar(nzG, 1 - tau, 64) - 0.3) * 0.65 * (tau > 0.12)
                v2 = np.where(d2 > T2 * 0.4, 0.1, 0.85)
                # 游丝：外沿往外甩出的细长弧丝，越晚越长越淡
                wl = (0.03 + 0.09 * tau) * polar(nzW, tau, 64)
                a3 = smooth(0.55, 0.75, polar(nzW, tau, 64)) * smooth(T1 + wl + 0.01, T1, d) * smooth(T1 - 0.01, T1 + 0.01, d) * (1 - tau) * gate
                v3 = 0.5
                # 早期中心能量雾
                a4 = (tex * 0.16) * smooth(R1 * 0.9, R1 * 0.4, r) * max(0.0, 1 - tau / 0.3)
                v4 = 0.85
                vv, aa = over(np.full(r.shape, v4), a4, np.full(r.shape, v3), a3)
                vv, aa = over(vv, aa, v2, a2)
                vv, aa = over(vv, aa, v1, a1)
                v4_, a4_ = down(np.clip(vv, 0, 1), np.clip(aa, 0, 1) * smooth(1.0, 0.96, r), C, C)
                tiles.append(to_img(v4_, a4_))
                names.append(f'rip{mode}{var}_{f}')
    # B 单帧：生图冲击波缩到格子里（整圈 0.92 半径）
    for k, p in enumerate(('gen_ring_a.png', 'gen_ring_b.png')):
        v, a = gen_va(os.path.join(SRC, p))
        ys_, xs_ = np.where(a > 0.05)
        cy, cx = v.shape[0] / 2, v.shape[1] / 2
        R = max(np.abs(xs_ - cx).max(), np.abs(ys_ - cy).max()) / 0.94
        c = (int(cx - R), int(cy - R), int(cx + R), int(cy + R))
        pad = lambda m: np.pad(m, ((max(0, -c[1]), max(0, c[3] - m.shape[0])), (max(0, -c[0]), max(0, c[2] - m.shape[1]))))
        vv, aa = pad(v), pad(a)
        o0, o1 = max(0, c[1]), max(0, c[0])
        vv, aa = vv[o0:o0 + c[3] - c[1], o1:o1 + c[2] - c[0]], aa[o0:o0 + c[3] - c[1], o1:o1 + c[2] - c[0]]
        vv, aa = resize_va(vv, aa, C, C)
        tiles.append(to_img(vv, aa))
        names.append(f'ringB{k}')
    cols = 10
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new('RGBA', (cols * C, rows * C))
    cells = {}
    for i, (n, t) in enumerate(zip(names, tiles)):
        cx_, cy_ = (i % cols) * C, (i // cols) * C
        im.paste(t, (cx_, cy_))
        cells[n] = [cx_, cy_, C, C]
    return im, cells


if __name__ == '__main__':
    main()
