"""男赢锚点 v3（2026-10-06）：在 anchor/v2 的 n0 / bK / bF / bL 上修两件女赢踩过的坑，出到 anchor/v3c/。

1. 输方贴地。v2 的 bF、bL 里女生是悬空的：bL 整个人是一块脚和胯都离地 ~60 像素的板，bF 的膝盖和脚离地 ~30。
   女赢的 aL 就是这样（男生悬空），视频中段模型按"自然"把人画在地上、最后 0.8 秒为了对上尾帧又抬起来，
   游戏里读成"趴下以后体型一变"（10-06 用户两次指出）。锚点先贴好地，视频就没有这一抬。
   做法：女生整个人绕握手机的手刚体旋转到最低处落地（见 ground）。v3b 是"整体下挪、手机附近渐入"，
   渐入那段正好压在头、手臂、头发上，把它们斜着拉变形了（10-06 用户指出），已作废。
2. 人放大 SCALE 倍。v2 里人只占画面高度的 45%（站着约 480 像素），视频出成 720P 时人只剩 320 像素高，
   进游戏还要放大 1.26 倍 —— 糊、抠像毛边（10-06 用户）。四张图同一个中心、同一个倍数放大（地面线不动），
   循环段尾帧再整体右移 SHIFT（= 女赢的 360 × SCALE，游戏里一圈的位移不变），所有图加尾帧都还在画面里。

3. 女生手臂缩短（v3d，10-06 用户「女生的手臂普遍被拉长，有点怪异」）。bK、bF、bL 里女生两臂伸直、比躯干长一截。
   女生手臂中段（拳头往肩方向 ARM_T 那一截：量过垂直于手臂的截面，只有两条手臂、碰不到头和头发）沿手臂方向压短 ARM_D，
   拳头不动，压短的这段以外、整个人刚体往手的方向挪 ARM_D；挪完再按 1 贴地。手是直的，沿轴压短看不出变形，
   身上其余部分一个像素不变形。肩→拳约短 12%。

4. 清晰度：每个像素只从生图原件（v2/<档>_gen.png）取一次。v2 本身是原件缩到裁切框（×0.79）再缩 ZOOM（×0.8）的，
   v3c/v3d 第一版在 v2 上转、压、再放大 1.3 倍，女生前后被插值三四次、等于从 0.63 倍的小图放大回来 —— 糊（10-06 用户
  「女生看着很模糊」）。现在 v2 只用来量几何（女生掩码、转角、手机），成图时把 放大⁻¹ → 贴地⁻¹ → 压短⁻¹ → v2→原件
   串成一个逆映射，在原件上三次样条采样一次（原件→成图净缩放 ≈0.82，是缩小）。点亮的手机屏原件里没有，那一块取 v2 点亮版。
   v2→原件的映射照 anchor.uncrop 的变换反推，uncrop 里按赢方脚做的横移没存下来，按 v2_raw 对原件逐像素搜出来记在 UNCROP_DX
   （对上后平均误差 0.1~0.2 灰度）。

用法：python3 anchor_b3.py   → anchor/v3d/{n0,bK,bF,bL}.png + 各自 .json（手机中心）；循环尾帧 {bK,bF,bL}_右移468；
      过渡尾帧 {bK,bF,bL}_右移156、bK_左移156、n0_左移156（见 STEP）
"""
import os, json
import numpy as np
from PIL import Image
from scipy import ndimage
import anchor

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'anchor', 'v2')
OUT = os.path.join(HERE, 'anchor', 'v3d')
G = 968            # 地面线（v2 七张图的脚底都在 967~970）
SCALE = 1.3
CX = 959.5         # 放大中心 x：v2 四张 + 右移 360 的尾帧合起来横跨 264~1655，取中点 → 放大后 55~1864
SHIFT = round(360 * SCALE)
STEP = SHIFT // 3   # 一步 = 循环一圈（三步）的三分之一。过渡段的尾帧也挪一步：倒下那几段被拖着往右（赢方那边）挪一步，
                    # 往回爬的跪起、站起两段往左挪一步 —— 女赢的过渡段原地不动，播的 4 秒里地面不能卷、画面落后几米，播完再追（10-06 用户）
# 循环段尾帧两种：10 秒的片走三步（SHIFT = 468），4~5 秒的片走两步（2·STEP = 312）—— 4 秒里走三步太赶，
# 模型会把多出来的时间拿去往回滑（10-06 第 12 段试片：女生跪着往自己那边倒滑、再瞬移回首帧）
SHIFTS = {'n0': [-STEP], 'bK': [SHIFT, 2 * STEP, STEP, -STEP], 'bF': [SHIFT, 2 * STEP, STEP], 'bL': [SHIFT, 2 * STEP, STEP]}
GRIP = 70          # 转轴：手机中心往左多少（两只手握的地方）
MAG = np.array([255, 0, 255], np.float32)
# anchor.uncrop 的变换常数（见那边 place()），用来把 v2 坐标换回生图原件坐标
U_ZOOM, U_PAD, U_CX, U_GY = 0.8, 600, 1920 / 2 + 67, 1080 - 110
UNCROP_DX = {'n0': 0, 'bK': -99, 'bF': -49, 'bL': -1}
CROP_BOX = json.load(open(os.path.join(HERE, 'anchor', 'stage', 'crop_box.json')))
# 女生手臂（见文件头 3）。坐标是在 v3c 成图（放大后）里量的：拳头中心 H、肩 S；ARM_T = 压短段离拳头的距离范围；ARM_D = 压短多少
# 锚点里张嘴喊的脸换成闭嘴（游戏无声，10-06 用户：人物不说话，只要表情）：档 → (补丁 RGBA, 贴在 dx=0 那张上的左上角)。
# bF 原图女生张大嘴喊（第 13 段扑倒后整段跟着张嘴）；补丁是生图局部重绘嘴+下巴、只取蒙版那块，alpha 已羽化。
MOUTH = {'bF': ('bF.png', (823, 618))}
ARM = {'bK': ((1110, 505), (895, 575), (30, 132), 27),
       'bF': ((1025, 580), (800, 680), (30, 162), 30),
       'bL': ((920, 640), (750, 785), (30, 142), 27)}


def fg_mask(a):
    return (np.minimum(a[..., 0], a[..., 2]) - a[..., 1]) < 100


def woman_mask(a, ph):
    """去掉手机一圈（手握着的地方两人连着）后，含最右前景像素的那一块是男生；女生 = 手机中心以左、不属于男生、
    不是纯品红的所有像素 —— 飞散的细发丝跟头发主体不连着，按连通块取会漏掉，挪完原位置留一道道残影（试过）"""
    fg = fg_mask(a)
    cut = fg.copy()
    cut[int(ph[1]) - 70:int(ph[1]) + 70, int(ph[0]) - 90:int(ph[0]) + 90] = False
    lab, n = ndimage.label(cut)
    ys, xs = np.nonzero(cut)
    i = xs.argmax()
    man = lab == lab[ys[i], xs[i]]
    # 外扩 6 收进男生轮廓上的混色像素 —— 但不许扩进女生的块里：bF、bL 女生的手离男生的手不到 6 像素，
    # 扩进去女生手臂的边就被当成男生、转的时候留在原地，手臂变细、边上一道残影（v3c 第一版）
    man = ndimage.binary_dilation(man, iterations=6) & ~ndimage.binary_dilation(cut & ~man, iterations=2)
    w = (np.abs(a.astype(np.float32) - MAG).sum(-1) > 30) & ~man
    w[:, int(ph[0]):] = False
    # 手机本身不算女生（转她的时候手机不能跟着转、撕成两半）：手机一圈框里不是皮肤色的像素
    x, y = int(ph[0]), int(ph[1])
    b = a[y - 60:y + 60, x - 110:x].astype(int)
    # 手机是冷色/无彩（黑边、白屏、绿气泡、R≈B），手和手臂连同深色勾线都是暖色（R 比 B 高一截）
    warm = (b[..., 0] > b[..., 2] + 12) & (b[..., 0] >= b[..., 1])
    phone = ndimage.binary_opening(~warm, iterations=1)
    w[y - 60:y + 60, x - 110:x] &= ~phone
    return w, man


def ground_phi(xs, ys, gx, gy):
    """女生贴地（见文件头 1），必须是刚体变换 —— 女生身上一个像素都不许变形：
    - 按列各挪各的：跪着的胸口被压到地上、腿挪成波浪（试过）；
    - 整体下移、只在手机往左 KEEP~KEEP+RAMP 之间渐入（v3b 第一版）：渐入那一段正好是头、手臂、头发，
      头被斜着压扁、手臂折弯拉长（10-06 用户「参考图中女生的头、手臂、头发是不是有变形」）。
    现在：女生整个人绕握手机的那一点 (gx, gy) 刚体旋转 φ，φ 取到最低那一处正好落地。返回 φ（弧度）。
    手离转轴不到一个手掌、几乎不动，脚落地；胸口离手近、只降一点 —— 趴着被拽着手往前拖，肩和胸本来就被拽离地面。"""
    def low(phi):          # 转 phi 之后女生最低点的 y
        return (gy + (ys - gy) * np.cos(phi) - (xs - gx) * np.sin(phi)).max()
    if low(0) >= G - 1:
        return 0.0
    lo_, hi_ = 0.0, 0.3
    for _ in range(40):
        mid = (lo_ + hi_) / 2
        lo_, hi_ = (mid, hi_) if low(mid) < G - 1 else (lo_, mid)
    return lo_


class Arm:
    """女生手臂缩短（见文件头 3），v2 坐标。t = 离拳头沿手臂往肩的距离：t < t1（拳头）不动，t1~t2 压成 t2−t1−d，再往后整个人挪 d"""
    def __init__(self, H, S, t1, t2, d):
        self.H = np.array(H, np.float64)
        self.u = (self.H - S) / np.linalg.norm(self.H - S)
        self.n = np.array([-self.u[1], self.u[0]])
        self.t1, self.t2, self.d = t1, t2, d
        self.k = (t2 - t1 - d) / (t2 - t1)

    def _map(self, x, y, f):
        px, py = x - self.H[0], y - self.H[1]
        t = -(px * self.u[0] + py * self.u[1])
        sn = px * self.n[0] + py * self.n[1]
        t = f(t)
        return self.H[0] - t * self.u[0] + sn * self.n[0], self.H[1] - t * self.u[1] + sn * self.n[1]

    def fwd(self, x, y):   # 原图点 → 压短后
        t1, t2, d, k = self.t1, self.t2, self.d, self.k
        return self._map(x, y, lambda t: np.where(t < t1, t, np.where(t < t2, t1 + (t - t1) * k, t - d)))

    def inv(self, x, y):   # 压短后的点 → 原图
        t1, t2, d, k = self.t1, self.t2, self.d, self.k
        return self._map(x, y, lambda t: np.where(t < t1, t, np.where(t < t2 - d, t1 + (t - t1) / k, t + d)))


def v2_to_gen(name, x, y):
    """v2 画布坐标 → 生图原件坐标：倒着走一遍 anchor.uncrop（原件缩到裁切框 → 放进加宽画布 → 以 (U_CX, U_GY) 为中心缩 U_ZOOM
    → 横移 UNCROP_DX → 去掉 U_PAD）。PIL 缩放按像素中心对齐：(X + 0.5) = (Xc + 0.5) × 倍数"""
    b = CROP_BOX[name]
    ox, oy = round((U_CX + U_PAD) * (1 - U_ZOOM)), round(U_GY * (1 - U_ZOOM))
    xc = (x + U_PAD - UNCROP_DX[name] - ox + 0.5) / U_ZOOM - 0.5 - (b[0] + U_PAD)
    yc = (y - oy + 0.5) / U_ZOOM - 0.5 - b[1]
    return (xc + 0.5) * 1536 / (b[2] - b[0]) - 0.5, (yc + 0.5) * 1024 / (b[3] - b[1]) - 0.5


def load_gen(name):
    """生图原件 → 抠像再铺回纯品红（跟 anchor.uncrop 一样走 build.cutout）：原件的幕布有噪点，不抠直接用，背景四到六成像素不是纯品红"""
    g = Image.open(os.path.join(SRC, name + '_gen.png')).convert('RGBA')
    bg = Image.new('RGBA', g.size, (255, 0, 255, 255)); bg.alpha_composite(g)      # 生图偶尔直接出透明底（bF）
    rgb, al = anchor.build.cutout(np.asarray(bg.convert('RGB')).astype(np.int16))
    return anchor.on_magenta(rgb, al).astype(np.float32)


class Source:
    """按 v2 坐标取色：一律从生图原件三次样条采样；点亮的手机屏（v2 点亮版和未点亮版不同的那一块）取 v2 点亮版"""
    def __init__(self, name, lit, raw):
        self.name = name
        self.gen = [ndimage.spline_filter(c, order=3) for c in load_gen(name).transpose(2, 0, 1)]
        self.lit = [ndimage.spline_filter(c, order=3) for c in lit.astype(np.float32).transpose(2, 0, 1)]
        scr = ndimage.binary_dilation(np.abs(lit.astype(int) - raw.astype(int)).sum(-1) > 30, iterations=3)
        self.scr = ndimage.gaussian_filter(scr.astype(np.float32), 1.0)

    def __call__(self, x, y):
        gx, gy = v2_to_gen(self.name, x, y)
        smp = lambda chans, a, b: np.stack([ndimage.map_coordinates(c, [b, a], order=3, prefilter=False, cval=MAG[i])
                                            for i, c in enumerate(chans)], -1)
        out = smp(self.gen, gx, gy)
        m = ndimage.map_coordinates(self.scr, [y, x], order=1, cval=0)[..., None]
        if m.max() > 0:
            out = out * (1 - m) + smp(self.lit, x, y) * m
        return out


def render(name, src, woman, dx):
    """成图 (v3 坐标，整体右移 dx) 每个像素：逆放大 → v2 点 q。底图 = q 处的原件（女生原位置抹成幕布）；
    女生 = q 逆贴地、逆压短回 v2 的点处的原件，按女生掩码合成。全程只采样原件一次（见文件头 4）"""
    yy, xx = np.mgrid[0:1080, 0:1920].astype(np.float64)
    qx, qy = CX + (xx - dx - CX) / SCALE, G - (G - yy) / SCALE
    out = src(qx, qy)
    if woman is not None:
        w, clear, (gx, gy, phi), arm = woman
        cl = ndimage.map_coordinates(clear.astype(np.float32), [qy, qx], order=1, cval=0)[..., None]
        out = out * (1 - cl) + MAG * cl
        c, s_ = np.cos(phi), np.sin(phi)
        px, py = gx + (qx - gx) * c - (qy - gy) * s_, gy + (qy - gy) * c + (qx - gx) * s_   # 逆贴地：转 −phi
        if arm is not None:
            px, py = arm.inv(px, py)
        al = ndimage.map_coordinates(w.astype(np.float32), [py, px], order=1, cval=0)[..., None]
        out = out * (1 - al) + src(px, py) * al
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))


def main():
    os.makedirs(OUT, exist_ok=True)
    v2 = lambda x, y: (CX + (x - CX) / SCALE, G - (G - y) / SCALE)       # v3 坐标 → v2 坐标（ARM 是在 v3c 成图里量的）
    for name in ['n0', 'bK', 'bF', 'bL']:
        lit = np.array(Image.open(os.path.join(SRC, name + '.png')).convert('RGB'))
        raw = np.array(Image.open(os.path.join(SRC, name + '_raw.png')).convert('RGB'))
        ph = json.load(open(os.path.join(SRC, name + '.json')))['phone']
        src = Source(name, lit, raw)
        woman = None
        if name != 'n0':
            w, man = woman_mask(lit.astype(np.int16), ph)
            # 原位置抹成幕布时外扩 2 像素：轮廓上那圈跟幕布混色的像素不够"非品红"、不在 w 里，不抹掉就在原处留一道浅色残影（试过）
            clear = ndimage.binary_dilation(w, iterations=2) & ~man
            x0, y0 = int(ph[0]), int(ph[1])
            clear[y0 - 60:y0 + 60, x0 - 110:] &= w[y0 - 60:y0 + 60, x0 - 110:]     # 手机一圈不外扩（会啃掉手机边）
            arm = None
            if name in ARM:
                (hx, hy), (sx, sy), (t1, t2), d = ARM[name]
                arm = Arm(v2(hx, hy), np.array(v2(sx, sy)), t1 / SCALE, t2 / SCALE, d / SCALE)
            ys, xs = np.nonzero(w)
            xs, ys = (xs.astype(np.float64), ys.astype(np.float64)) if arm is None else arm.fwd(xs, ys)
            gx, gy = ph[0] - GRIP, ph[1]
            phi = ground_phi(xs, ys, gx, gy)
            print(name, '女生绕手转 %.2f 度' % np.degrees(phi))
            woman = (w, clear, (gx, gy, phi), arm)
        for suf, dx in [('', 0)] + [(('_右移%d' if dx > 0 else '_左移%d') % abs(dx), dx) for dx in SHIFTS[name]]:
            im = render(name, src, woman, dx)
            if name in MOUTH:
                f, (mx, my) = MOUTH[name]
                patch = Image.open(os.path.join(HERE, 'anchor', 'mouth', f))
                im.paste(patch.convert('RGB'), (mx + dx, my), patch.getchannel('A'))
            im.save(os.path.join(OUT, name + suf + '.png'))
            ph2 = [round(CX + (ph[0] - CX) * SCALE + dx, 1), round(G - (G - ph[1]) * SCALE, 1)]
            json.dump({'phone': ph2}, open(os.path.join(OUT, name + suf + '.json'), 'w'))
            fg = fg_mask(np.asarray(im).astype(np.int16))
            ys_, xs_ = np.nonzero(fg)
            print('  %-10s 外框 x %d~%d y %d~%d  手机 %s' % (name + suf, xs_.min(), xs_.max(), ys_.min(), ys_.max(), ph2))


if __name__ == '__main__':
    main()
