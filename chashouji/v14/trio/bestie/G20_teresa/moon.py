"""G20 月亮拆成挂件层（审查第八批打回 / 规范第七轮修订第 1 条：布景在场各帧逐像素相同）。写法照 G19 无人机：一张图、八帧同一个位置，z −1 垫在人后面。
每次 frames.py build 之后跑一次（在 v14/trio 下：python3 bestie/G20_teresa/moon.py）；已经拆过的图集再跑会直接退出（先重新 build）。

生图每一格都重画了一遍月亮：上角尖 x 差到 7 格内 px、背弧也不一样（审10_G20_月亮逐帧不同）。这里：
  · 月牙 = 两个圆之差。每帧在月亮的外轮廓（贴着透明的那圈边）上拟合外圆、内圆（残差 ≈ 1 px），HULL = 外圆内、内圆外，各放宽 MARGIN；
  · 帧里的月亮 = HULL 里的金色（色相 44~74、饱和 > 0.12，含那道近白的高光）连成的大块，再在 HULL 里顺着金色 / 暗金描边 / 半透明外沿长 GROW 圈
    （月尖是暗橙、描边是暗金）。两腿之间露出来的小三角也是金色、也在 HULL 里，一起拿掉。人身上的金色滚边压在月亮上的那一截会被一起拿掉 ——
    金滚边叠在金月亮上，拿掉以后由挂件的月亮垫着，看不出来；HULL 外面的滚边不动；
  · 挂件 = idle 的月亮；idle 里被人挡住的那部分（换别的帧会露出来：臀部坐点、头发边、两腿之间）按月牙极坐标补：
    θ = 绕外圆圆心的角度、t = 在内外两道边之间的相对位置（0 内边 ~ 1 外边），月亮的明暗基本只随 t 变、沿 θ 缓变，
    用 idle 露出来的像素做 (θ, t) 表（预乘 alpha），每一行 t 沿 θ 线性插值补空格，被挡的像素查表；
  · 人：在月亮上的坐点各帧画得不一样（生图重画），按月亮配准以后人和 idle 差 DX、DY：量臀部 + 大腿（SEAT 框，月亮拿掉以后）的偏移，
    整格平移到和 idle 对齐（亚像素，双线性），这样人坐在同一张月亮上的接触线各帧一致；
  · 图集 json 加 moon 字段（说明 + 各帧平移），cfg 里 parts 那一条按打印的抄。"""
import json
import os
import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.optimize import least_squares
from skimage.feature import match_template

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, '../../../../web/assets/trio')
P, META = os.path.join(WEB, 'G20_teresa.webp'), os.path.join(WEB, 'G20_teresa.json')
PART = os.path.join(WEB, 'G20_moon.webp')
MARGIN, GROW, EDGE, AWAY = 2.5, 25, 3, 5
SPECK = 40                             # 拿掉月亮以后人那一层跟人不连着的碎块（月亮外沿的残渣）小于这个 px 的扔掉
SEAT = (40, 170, 200, 260)            # 臀部 + 交叠的大腿（格内 x0, y0, x1, y1）：人坐在月亮上的那一块，配准人用
# wave 一手扶着月尖：压在月亮上的那截前臂生图画成了淡黄（色相 50、饱和 0.25），和月亮的高光分不开。
# 框里（格内，平移前）饱和度 < 0.45、并且跟真正肤色连着的算人（手、前臂），只拿掉饱和的金色（手指缝里的月尖）和月亮的高光
KEEP = {'wave': (50, 5, 95, 60)}
TB, AB = 48, 1.0                       # (θ, t) 表：t 分几档、θ 每档几度


def hsv(c):
    r, g, b = (c[..., i] / 255 for i in range(3))
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0), mx


def circle(x, y):
    p0 = [x.mean(), y.mean(), np.hypot(x - x.mean(), y - y.mean()).mean()]
    return least_squares(lambda p: np.hypot(x - p[0], y - p[1]) - p[2], p0, loss='soft_l1', f_scale=1.0).x


def core(c):
    """金色大块（含近白高光）：开运算去掉细滚边，≥ 120 px 的块"""
    h, s, v = hsv(c)
    y = (c[..., 3] > 20) & (h >= 44) & (h < 74) & (s > 0.12) & (v > 0.55)
    y = nd.binary_opening(y, np.ones((4, 4)))
    lab, k = nd.label(y)
    return np.isin(lab, 1 + np.nonzero(nd.sum(y, lab, range(1, k + 1)) >= 120)[0])


def grow(c, seed, allow, n):
    """顺着月亮自己的颜色往外长：金 / 暗金 / 月尖的暗橙（v > 0.5），外轮廓那圈深描边和半透明外沿只收贴着透明背景的（EDGE px 内）——
    人压在月亮上的描边（腿、裙边）是深色、不贴透明，长不进去，人那一层的描边就不会被拿掉"""
    h, s, v = hsv(c)
    edge = nd.binary_dilation(c[..., 3] < 20, iterations=EDGE)
    cand = allow & (c[..., 3] > 0) & (((h >= 22) & (h < 74) & (s > 0.42) & (v > 0.5)) | (edge & ((s > 0.42) | (c[..., 3] < 200))))
    m = seed.copy()
    for _ in range(n):
        m |= nd.binary_dilation(m) & cand
    return m


def fit(c):
    """外圆、内圆：只用贴着透明的那圈边（贴着人的边不是月亮的轮廓）"""
    m = grow(c, core(c), np.ones(c.shape[:2], bool), GROW)
    ey, ex = np.nonzero(m & nd.binary_dilation(c[..., 3] < 20, iterations=2))
    ex, ey = ex.astype(float), ey.astype(float)
    po = circle(ex, ey)
    sel = np.hypot(ex - po[0], ey - po[1]) > po[2]
    for _ in range(3):
        po = circle(ex[sel], ey[sel]); sel = np.abs(np.hypot(ex - po[0], ey - po[1]) - po[2]) < 3
    inn = np.hypot(ex - po[0], ey - po[1]) < po[2] - 8
    pi = circle(ex[inn], ey[inn])
    for _ in range(2):
        s2 = inn & (np.abs(np.hypot(ex - pi[0], ey - pi[1]) - pi[2]) < 3); pi = circle(ex[s2], ey[s2])
    return po, pi


def geom(shape, po, pi):
    yy, xx = np.mgrid[:shape[0], :shape[1]].astype(float)
    do = po[2] - np.hypot(xx - po[0], yy - po[1])          # 在外边以内多深
    di = np.hypot(xx - pi[0], yy - pi[1]) - pi[2]          # 在内边以外多远
    hull = (do > -MARGIN) & (di > -MARGIN)
    t = np.clip(di / np.maximum(di + do, 1e-6), -0.2, 1.2)  # 0 内边 ~ 1 外边（外沿半透明那一圈略超出）
    th = np.degrees(np.arctan2(yy - po[1], xx - po[0]))
    return hull, t, th


def moon_mask(c, keep=None):
    """帧里的月亮：HULL 里长；HULL 外面（画的月尖比两圆之差更细更长）只在离「确定是人」AWAY px 以外长。
    确定是人 = 不透明、不是金色（低饱和的皮肤 / 白裙、蓝花、黑发），月亮那道近白高光（黄绿色相、亮）除外"""
    po, pi = fit(c)
    hull, _, _ = geom(c.shape[:2], po, pi)
    h, s, v = hsv(c)
    person = (c[..., 3] > 200) & ((s < 0.36) | (h < 20) | (h > 80)) & ~((h >= 44) & (h < 74) & (v > 0.55))
    allow = hull | ~nd.binary_dilation(person, iterations=AWAY)
    # 两腿之间露出来的小三角：金色、装得下 3 × 3 的块（旗袍的金滚边只有 1~2 px 宽，进不来；滚边外侧那道深描边也挡住了往里长）
    gold = nd.binary_opening((c[..., 3] > 60) & (h >= 38) & (h < 74) & (s > 0.4) & (v > 0.55) & hull, np.ones((3, 3)))
    if keep:
        x0, y0, x1, y1 = keep
        box = np.zeros(c.shape[:2], bool); box[y0:y1, x0:x1] = True
        pale = box & (s < 0.45) & (h < 57.5) & (v > 0.55) & (c[..., 3] > 200)   # 月亮高光是黄绿（色相 58~65），手臂偏橙
        lab, k = nd.label(pale)
        arm = np.isin(lab, np.unique(lab[pale & (h < 44)]))       # 跟真正肤色（手指、月亮外面那截前臂）连着的那一块；高光条是黄绿色相，连不上
        allow &= ~nd.binary_dilation(arm, iterations=2)                 # 连同手臂压在月亮上的那道金褐描边
    return grow(c, (core(c) & allow) | gold, allow, GROW), (po, pi)


def fill_part(c, m, po, pi):
    """idle 的月亮层。样本 = 确定是月亮的像素：m 开运算后的大块（去掉压在月亮上的金滚边这类细线）+ 贴透明背景的外轮廓，
    离人 2 px 以外；HULL 里其余的（被人挡住的、滚边、贴着人的混色）全按 (θ, t) 表补。透明的像素（HULL 放宽的那一圈）也是样本，外沿的 alpha 就能接上"""
    hull, t, th = geom(c.shape[:2], po, pi)
    person = (c[..., 3] > 0) & ~m
    edge = nd.binary_dilation(c[..., 3] < 20, iterations=EDGE)
    sure = (nd.binary_opening(m, np.ones((3, 3))) | (m & edge)) & ~nd.binary_dilation(person, iterations=2)
    known = hull & (sure | (c[..., 3] == 0))
    pm = np.concatenate([c[..., :3] * c[..., 3:] / 255, c[..., 3:]], -1)      # 预乘
    pm[~(known | (sure & ~hull))] = 0                        # HULL 外面只留月尖（sure），不做表的样本
    TB_, NA = TB, int(360 / AB)
    ti = np.clip(np.round((t + 0.2) / 1.4 * (TB_ - 1)).astype(int), 0, TB_ - 1)
    ai = np.round((th + 180) / AB).astype(int) % NA
    acc = np.zeros((TB_, NA, 4)); cnt = np.zeros((TB_, NA))
    np.add.at(acc, (ti[known], ai[known]), pm[known]); np.add.at(cnt, (ti[known], ai[known]), 1)
    tab = np.where(cnt[..., None] > 0, acc / np.maximum(cnt[..., None], 1), np.nan)
    # 月牙只占两个月尖之间那一段角度：展开时从缺口正中切开（缺口朝着内圆圆心那一边），别跨过缺口插值
    gap = int(round((np.degrees(np.arctan2(pi[1] - po[1], pi[0] - po[0])) + 180) / AB)) % NA
    order = (np.arange(NA) + gap) % NA
    idx = np.arange(NA)
    for r in range(TB_):
        row = tab[r, order]; ok = ~np.isnan(row[:, 0])
        if ok.sum() < 2: continue
        for k in range(4):
            row[:, k] = np.interp(idx, idx[ok], row[ok, k], left=np.nan, right=np.nan)
        tab[r, order] = row
    hole = hull & ~known
    pm[hole] = np.nan_to_num(tab[ti[hole], ai[hole]])
    out = np.zeros_like(c)
    al = pm[..., 3]
    out[..., :3] = np.where(al[..., None] > 0, pm[..., :3] * 255 / np.maximum(al[..., None], 1e-6), 0)
    out[..., 3] = al
    return out, hole & (pm[..., 3] > 0)


def shift(c, dx, dy):
    """整格亚像素平移（预乘 alpha 双线性）"""
    pm = np.concatenate([c[..., :3] * c[..., 3:] / 255, c[..., 3:]], -1)
    pm = np.stack([nd.shift(pm[..., k], (dy, dx), order=1, mode='constant') for k in range(4)], -1)
    al = pm[..., 3:]
    return np.concatenate([np.where(al > 0, pm[..., :3] * 255 / np.maximum(al, 1e-6), 0), al], -1)


def seat_offset(ref, c):
    """人（月亮已经拿掉）在 SEAT 框里相对 idle 偏多少（亚像素，归一化互相关 + 抛物线）"""
    g = lambda a: (a[..., :3].mean(-1) * a[..., 3] / 255)
    x0, y0, x1, y1 = SEAT; R = 8
    t = g(ref)[y0:y1, x0:x1]
    w = g(c)[y0 - R:y1 + R, x0 - R:x1 + R]
    r = match_template(w, t)
    iy, ix = np.unravel_index(np.argmax(r), r.shape)
    def sub(a, i):
        if 0 < i < len(a) - 1:
            d = a[i - 1] - 2 * a[i] + a[i + 1]
            return i + (0.5 * (a[i - 1] - a[i + 1]) / d if d else 0)
        return float(i)
    return sub(r[iy], ix) - R, sub(r[:, ix], iy) - R      # c 里的人在 idle 的 (dx, dy) 处


if __name__ == '__main__':
    meta = json.load(open(META))
    if 'moon' in meta:
        raise SystemExit('月亮已经拆过（json 有 moon）：先 python3 tools/frames.py bestie/G20_teresa build 再跑')
    CW, CH = meta['cell']; COLS = meta['cols']; NAMES = meta['frames']
    a = np.array(Image.open(P).convert('RGBA')).astype(float)
    cell = lambda n: (slice(NAMES.index(n) // COLS * CH, NAMES.index(n) // COLS * CH + CH),
                      slice(NAMES.index(n) % COLS * CW, NAMES.index(n) % COLS * CW + CW))
    people, moved = {}, {}
    for n in NAMES:
        c = a[cell(n)]
        m, (po, pi) = moon_mask(c, KEEP.get(n))
        if n == meta['ref']:
            part, hole = fill_part(c, m, po, pi)
            geo = (po, pi)
        p = c.copy(); p[m, 3] = 0; p[m, :3] = 0
        lab, k = nd.label(nd.binary_dilation(p[..., 3] > 20))
        sz = nd.sum(p[..., 3] > 20, lab, range(1, k + 1))
        crumbs = (lab > 0) & (sz[np.maximum(lab, 1) - 1] < SPECK)
        p[crumbs] = 0
        people[n] = p
        print('%-6s 外圆 (%.1f, %.1f) r %.1f  内圆 (%.1f, %.1f) r %.1f  拿掉 %d px' % (n, *po, *pi, int(m.sum())))
    ref = people[meta['ref']]
    for n in NAMES:
        if n == meta['ref']: moved[n] = [0.0, 0.0]; continue
        dx, dy = seat_offset(ref, people[n])
        people[n] = shift(people[n], -dx, -dy)
        r2 = seat_offset(ref, people[n])
        moved[n] = [round(-dx, 2), round(-dy, 2)]
        print('%-6s 人（坐点）相对 idle 偏 %+.2f, %+.2f → 平移回去，余 %+.2f, %+.2f' % (n, dx, dy, *r2))
        a[cell(n)] = people[n]
    a[cell(meta['ref'])] = ref
    Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8)).save(P, 'WEBP', quality=90, method=6)   # 同 frames.py
    # 挂件：裁到包围盒；pivot = 锚点（月亮弯里的中心）在挂件图上的位置，at = 锚点（格内），八帧一样
    ys, xs = np.nonzero(part[..., 3] > 0)
    x0, y0 = xs.min(), ys.min()
    im = Image.fromarray(np.clip(part[y0:ys.max() + 1, x0:xs.max() + 1] + 0.5, 0, 255).astype(np.uint8), 'RGBA')
    im.save(PART, 'WEBP', quality=92, method=6)
    ax, ay = meta['anchor']
    piv = [round(float(ax - x0), 1), round(float(ay - y0), 1)]
    meta['moon'] = 'bestie/G20_teresa/moon.py：月亮拆成挂件 G20_moon.webp（idle 那一份，被挡处按月牙极坐标补 %d px），人按坐点平移 %s' % (int(hole.sum()), json.dumps(moved))
    json.dump(meta, open(META, 'w'), ensure_ascii=False)
    ats = ', '.join('%s: [%s, %s, 0]' % (n, ax, ay) for n in NAMES)
    print('挂件 %dx%d → web/assets/trio/G20_moon.webp（补 %d px）' % (im.width, im.height, int(hole.sum())))
    print("cfg.parts：{ src: 'assets/trio/G20_moon.webp', pivot: %s, z: -1, at: { %s } }" % (piv, ats))
