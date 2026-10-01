"""三人组角色的帧序列管线（2026-09-29，规范见 docs/三人组角色规范.md）。

动作条（一张图里同一个人的几个姿势，生图一次出）→ 抠像 → 按连通块切成一格一格 → 按头的大小统一缩放、按不动的部位配准 →
全部帧贴到同一块画布（锚点在每一帧都是同一个像素）→ 缩到屏幕像素 → 打成一张图集 web/assets/trio/<名>.webp + <名>.json。

为什么要配准：生图每一格都是重画的，同一张条里人的位置、大小也会漂（记忆 chashouji-keyframe-frames）。帧直接连播，
趴在地上的人会整个一跳一跳。所以：
  · 缩放按头：头在各个姿势里形状最稳（手脚、身体都在动），在每一格里多尺度找参考帧的头，取最像的那个倍数；
  · 平移按不动的部位（fixed）：趴着的人是屁股 + 大腿、秋千上的是座板 —— 它在动作里本来就不该动，拿它对齐，
    剩下的差异才是真正的动作。
两步都是模板匹配（skimage.match_template，归一化互相关），峰值做抛物线亚像素插值。

用法（在 v14/trio 下；<目录> = buddy/B21_sakura 这样的角色目录，<名> = 目录名 B21_sakura，图集和预览都用它命名）：
  python3 tools/frames.py <目录> cells   # 第一步：切格，出 preview/<名>_cells.png（每格编号 + 50 像素格线，原图像素）
                                         #   → 照它在 <目录>/frames.json 里填 head / fixed 两个框（参考帧的格内像素）
  python3 tools/frames.py <目录> build   # 第二步：配准、出图集；打印每帧的缩放、配准残差（输出像素，验收 ≤ 2）
出的预览（都在 preview/）：
  <名>_frames.png  每帧一格，输出像素、50 像素格线（量 hand / hold 这些点用；坐标就是 cfg 里要填的）
  <名>_onion.png   全部帧叠在一起（各 35%），不动的部位应该是一个清楚的影子，糊成几层 = 没对齐
  <名>_yellow.png  贴亮黄底（看抠像：紫边 / 绿边 / 被抠穿的洞在黄底上最刺眼）

frames.json：
{
  "sheets": [ {"src": "raw/act_a1.png", "screen": "auto", "frames": ["idle", "wind", "throw", "follow"]}, ... ],
      screen：auto（生图回来自带透明就直接用 alpha，否则看四角是绿幕还是品红幕）/ magenta / green；key 可选 [k0, k1]（见 crewart.cut）
      frames：这张条里的格按阅读顺序（先上后下、同一行先左后右）叫什么
  "ref": "idle",                    参考帧（head / fixed 框在它上面量）
  "head": [x0, y0, x1, y1],         参考帧里头的框（cells 预览上量，格内像素）
  "fixed": [x0, y0, x1, y1],        参考帧里不动部位的框
  "size": ["w", 470],               参考帧的剪影缩到多宽（"w"）/ 多高（"h"）的屏幕像素
  "anchor": [x, y],                 参考帧里的锚点（格内像素）—— 输出里所有帧共用，打印出来填 cfg.anchor
  "scale": [0.85, 1.2],             可选：头的缩放搜索范围
  "erase": {"hsv": [[h0, h1], [s0, s1], [v0, v1]], "grow": 5, "band": 30},   可选：把引擎自己画的东西（秋千座板）按颜色抠掉
  "check": [[x0, y0, x1, y1, "脚"], ...],   可选：另外量几个本该不动的部位（输出像素），打印每帧偏多少
  "graft": [{"from": "wind", "to": ["throw"], "box": [x0, y0, x1, y1], "feather": 30}]   可选：从好的一帧把一块搬到画走样的帧上（输出像素，左边 feather 宽渐变）
  "scale_by": "fixed",               可选：缩放也按 fixed 找（站在滑板 / 平衡车上的人：板长不变，头仰着转着按头找不准）；loose 帧取同一张条的中位数
  sheets[i].scale_as: "<帧>"          可选：这张条的缩放照抄那一帧（P6 局部重绘补帧：底图就是那一格的原像素）
  "scale_by": "sheet",               可选：每张条只在 scale_ref 帧（条上的 "scale_ref"，默认最后一格 = 重画的 idle）按头找一次缩放，整张条都用它
  "loose_scale": "sheet",            可选：只让 loose 帧的缩放取同一张条其它帧的中位数（B12 飞扑那帧头侧着按头找会顶到边界）
  "loose": ["walk1", ...],            可选：脚在动的帧（走路 / 跑 / 跳），不按 fixed 配：横向按头、竖向按脚底贴参考帧的地面线；残差表里不计
  "lift": [{"name": "G11_tassel", "from": "idle", "box": {"idle": [x0, y0, x1, y1], ...}, "hsv": [[[h0, h1], [s0, s1], [v0, v1]], ...]}]
      可选：挂着的东西碰到身体（流苏贴肩膀）时拆成挂件层（见 lift()），帧里原位置补画
}
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from skimage.feature import match_template

HERE = os.path.dirname(os.path.abspath(__file__))
TRIO = os.path.dirname(HERE)
sys.path.insert(0, os.path.dirname(TRIO))                 # v14/crewart.py
from crewart import cut, edge_extend

OUT = os.path.join(TRIO, '../../web/assets/trio')
PRE = os.path.join(TRIO, 'preview')
M = 16                                                     # 切格时每格四周留的边（原图像素）


def load_sheet(path, screen, key):
    """→ (rgb float32, alpha 0~1)。生图有时直接回透明底：有 alpha 就直接用，别铺回幕布再抠（粉 / 紫会被抠成半透明）"""
    im = Image.open(path)
    if screen == 'auto':
        a = np.array(im.convert('RGBA')).astype(np.float32)
        if a[..., 3].min() < 250:
            return a[..., :3], a[..., 3] / 255
        c = np.concatenate([a[:8, :8, :3].reshape(-1, 3), a[-8:, -8:, :3].reshape(-1, 3)]).mean(0)   # 四角取样认幕布
        screen = 'green' if c[1] > max(c[0], c[2]) else 'magenta'
    return cut(path, screen, key or (40, 150))


def split(rgb, al, n):
    """按连通块切格：最大的 n 块是 n 个人；其余小块（脱开的流苏、发梢、抠剩的碎点）并给离它最近的那个人，
    太远（> 40 像素）的当碎点扔掉。阅读顺序（行按竖直中心聚类）。每格只带自己那几块的像素"""
    lab, k = ndimage.label(ndimage.binary_dilation(al > 0.1, iterations=3))
    area = ndimage.sum(al > 0.1, lab, range(1, k + 1))
    big = list(np.argsort(area)[::-1][:n] + 1)
    if len(big) < n:
        raise SystemExit(f'只切出 {len(big)} 格，要 {n} 格')
    dist = [ndimage.distance_transform_edt(lab != b) for b in big]
    own = np.zeros(lab.shape, np.int32)
    for i, b in enumerate(big): own[lab == b] = i + 1
    for j in range(1, k + 1):
        if j in big: continue
        m = lab == j
        d = [dd[m].min() for dd in dist]
        if min(d) <= 40: own[m] = int(np.argmin(d)) + 1
    boxes = [(ndimage.find_objects((own == i + 1).astype(np.int32))[0], i + 1) for i in range(n)]
    hs = np.median([b[0][0].stop - b[0][0].start for b in boxes])
    boxes.sort(key=lambda b: (round(((b[0][0].start + b[0][0].stop) / 2) / (hs * 0.6)), b[0][1].start))
    cells = []
    for (sy, sx), li in boxes:
        y0, y1 = max(0, sy.start - M), min(al.shape[0], sy.stop + M)
        x0, x1 = max(0, sx.start - M), min(al.shape[1], sx.stop + M)
        a = al[y0:y1, x0:x1] * (own[y0:y1, x0:x1] == li)
        c = np.dstack([rgb[y0:y1, x0:x1], a * 255]).clip(0, 255).astype(np.uint8)
        cells.append(Image.fromarray(c, 'RGBA'))
    return cells


def gray(im):
    """匹配用的两个通道：灰度（贴中灰底，透明处 = 128，不然透明区的幕布色会参与匹配）+ alpha（剪影本身；
    只用灰度时短裤上的平行条纹会让横向匹配差一个条纹间距）"""
    a = np.array(im.convert('RGBA')).astype(np.float32) / 255
    rgb = a[..., :3] * a[..., 3:] + 0.5 * (1 - a[..., 3:])
    return np.dstack([rgb @ np.array([0.299, 0.587, 0.114], np.float32), a[..., 3]])


def peak(r):
    """匹配响应的峰：抛物线亚像素插值 → (y, x, 分数)"""
    y, x = np.unravel_index(np.argmax(r), r.shape)
    def sub(a, b, c):
        d = a - 2 * b + c
        return 0.0 if abs(d) < 1e-9 else 0.5 * (a - c) / d
    dy = sub(r[y - 1, x], r[y, x], r[y + 1, x]) if 0 < y < r.shape[0] - 1 else 0
    dx = sub(r[y, x - 1], r[y, x], r[y, x + 1]) if 0 < x < r.shape[1] - 1 else 0
    return y + dy, x + dx, r[y, x]


def find(img_g, tpl):
    if tpl.shape[0] > img_g.shape[0] or tpl.shape[1] > img_g.shape[1]:
        return None
    return peak(match_template(img_g, tpl)[..., 0])


def resize(im, s):
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def grid(im, step=50, z=2, label=None):
    g = Image.new('RGBA', im.size, (236, 236, 236, 255)); g.alpha_composite(im)
    d = ImageDraw.Draw(g)
    for x in range(0, im.width, step): d.line([(x, 0), (x, im.height)], fill=(0, 110, 255, 255) if x % 100 == 0 else (130, 200, 255, 255))
    for y in range(0, im.height, step): d.line([(0, y), (im.width, y)], fill=(0, 110, 255, 255) if y % 100 == 0 else (130, 200, 255, 255))
    g = g.convert('RGB').resize((im.width * z, im.height * z), Image.NEAREST)
    if label:
        d = ImageDraw.Draw(g); d.rectangle([0, 0, 12 * len(label) + 16, 22], fill=(0, 0, 0)); d.text((6, 5), label, fill=(255, 255, 0))
    return g


def tile(ims, cols, bg=(30, 30, 30)):
    w, h = max(i.width for i in ims), max(i.height for i in ims)
    rows = (len(ims) + cols - 1) // cols
    out = Image.new('RGB', (w * cols, h * rows), bg)
    for i, im in enumerate(ims):
        out.paste(im.convert('RGB') if im.mode != 'RGBA' else im, ((i % cols) * w, (i // cols) * h), im if im.mode == 'RGBA' else None)
    return out


def hsv(a):
    """RGBA float（0~255）→ (色相 0~1, 饱和度, 明度)"""
    rgb = a[..., :3] / 255
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    d = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    return hue, sat, mx


def in_hsv(a, ranges):
    """落在任一 [[h0, h1], [s0, s1], [v0, v1]] 里的像素"""
    h, s, v = hsv(a)
    m = np.zeros(a.shape[:2], bool)
    for (h0, h1), (s0, s1), (v0, v1) in ranges: m |= (h >= h0) & (h <= h1) & (s >= s0) & (s <= s1) & (v >= v0) & (v <= v1)
    return m


def grow(a, hole, known):
    """hole 里的像素从 known 往里一圈一圈补（每圈取已知邻居的平均，按 alpha 预乘）→ 预乘的 RGBA"""
    pm = np.dstack([a[..., :3] * a[..., 3:] / 255, a[..., 3:]]); pm[~known] = 0
    known = known.copy(); todo = hole & ~known
    k = np.ones((3, 3), np.float32)
    while todo.any():
        ring = ndimage.binary_dilation(known) & todo
        if not ring.any(): break
        n = ndimage.convolve(known.astype(np.float32), k, mode='constant')
        for c in range(4):
            sm = ndimage.convolve(pm[..., c] * known, k, mode='constant')
            pm[..., c] = np.where(ring, sm / np.maximum(n, 1), pm[..., c])
        known |= ring; todo &= ~ring
    return pm


def shoulder(op, hole):
    """挂件压着的那段身体轮廓（肩线）：hole 左右紧挨着的两列里，身体（op 不透明）在 hole 最低一行附近从哪一行开始，两点连线。
    往上找不超过 hole 的中线（再往上是帽子 / 头发，不是肩）；hole 底下那一行是透明的就往下找。两边都没有身体 → None"""
    ys, xs = np.nonzero(hole)
    xl, xr, yb, ym = xs.min() - 1, xs.max() + 1, ys.max(), (ys.min() + ys.max()) // 2

    def top(x):
        if op[yb + 1, x]:
            y = yb + 1
            while y - 1 > ym and op[y - 1, x]: y -= 1
            return y
        d = np.nonzero(op[yb + 1:yb + 40, x])[0]
        return yb + 1 + d[0] if len(d) else None
    yl, yr = top(xl), top(xr)
    if yl is None and yr is None: return None
    yl, yr = (yr if yl is None else yl), (yl if yr is None else yr)
    return (lambda x: yl + (yr - yl) * (x - xl) / (xr - xl)), [(x, y) for x, y in ((xl, yl), (xr, yr)) if op[y, x]]


def fill_in(a, hole):
    """挂件拆走以后把它原来挡着的地方（hole）补上。以被挡住那段肩线（shoulder）为界分两侧各补各的：
    贴身体那侧只从肩线以下的身体往里长（肤色 / 衣服），不透明、肩线那一行按覆盖率抗锯齿；
    外侧只从肩线以上往里长（背景 → 透明，帽子 / 头发照旧）。
    不分两侧、四周一起平均的话，流苏压着肩膀那一截会把肤色、描边和透明背景混成一块不透明的直角灰块（G11 审查 2026-09-30）"""
    op = (a[..., 3] > 127) & ~hole
    sh = shoulder(op, hole)
    line, ends = sh if sh else (None, [])
    Y, X = np.mgrid[0:hole.shape[0], 0:hole.shape[1]]
    below = Y + 0.5 >= line(X) if line else np.zeros_like(hole)
    body = hole & below
    pm = np.where(body[..., None], grow(a, body, op & below), grow(a, hole & ~below, ~hole & ~below))
    if ends:
        # 肩线上补一道描边：颜色取两头露在外面那段轮廓最外一像素（不描的话，肤色和描边平均出来是一条灰边）
        ink = np.mean([a[y, x, :3] for x, y in ends], axis=0)
        edge = body & (Y + 0.5 - line(X) < 1.5)
        pm[edge] = np.append(ink, 255.0)                  # 预乘：alpha 255，RGB 就是它本身
    # 外侧补出来的边硬一点（半透明的一团读成脏），开运算削掉两边往里长在中间碰头顶出的小尖角
    solid = ndimage.binary_opening(pm[..., 3] > 127, structure=np.ones((3, 3)), iterations=4)
    cov = np.clip(Y + 1 - line(X), 0, 1) if line else 0
    out = a.copy()
    out[..., :3] = np.where(hole[..., None], pm[..., :3] * 255 / np.maximum(pm[..., 3:], 1e-3), a[..., :3])
    out[..., 3] = np.where(hole, np.where(body, 255 * cov, np.where(solid, 255, 0)), a[..., 3])
    return out


def lift(outs, L):
    """挂件拆层（lift）：挂着的东西碰到身体（格格帽后的流苏下端贴着肩膀），flex 条带错位会把身体撕开 —— 把它从每一帧里拆出来，
    做成挂件层（运行时 cfg.parts 按 sway 甩），帧里它原来的位置补上（fill_in：贴身体那侧沿肩线补肤色，外侧补透明）。
    L = {"name", "from": 挂件图取哪一帧, "box": {帧: [x0, y0, x1, y1]} 每一帧里它在哪（输出像素，只框它，别框进身上同色的地方）,
         "hsv": [[[h0, h1], [s0, s1], [v0, v1]], ...] 它是什么颜色（几段取并集，描边自动带上）}
    → 挂件图 web/assets/trio/<name>.webp；打印 cfg.parts 那一条（pivot = 挂件图顶上正中，at[帧] = 那一帧里顶上正中的位置）"""
    at, part = {}, None
    names = list(outs); cols = min(4, len(names)); cw, ch = outs[names[0]].size
    holes = Image.new('L', (cw * cols, ch * ((len(names) + cols - 1) // cols)))     # 补过的像素，按图集排（lift_check.py 只数这些）
    for fn, (x0, y0, x1, y1) in L['box'].items():
        a = np.array(outs[fn]).astype(np.float32)
        box = np.zeros(a.shape[:2], bool); box[y0:y1, x0:x1] = True
        core = in_hsv(a, L['hsv']) & (a[..., 3] > 60) & box
        core = ndimage.binary_fill_holes(ndimage.binary_closing(core, iterations=2)) & box
        dark = hsv(a)[2] < 0.45
        m = core | (ndimage.binary_dilation(core, iterations=2) & (dark | (a[..., 3] < 250)) & box)   # 描边 + 外沿抗锯齿
        ys, xs = np.nonzero(m)
        top = ys.min(); cx = (xs[ys < top + 4].min() + xs[ys < top + 4].max()) / 2
        at[fn] = [round(float(cx), 1), float(top)]
        if fn == L['from']:
            p = a.copy(); p[..., 3] *= m
            part = Image.fromarray(p.clip(0, 255).astype(np.uint8), 'RGBA').crop((xs.min(), top, xs.max() + 1, ys.max() + 1))
            piv = [round(float(cx - xs.min()), 1), 0.0]
        outs[fn] = Image.fromarray(fill_in(a, m).clip(0, 255).astype(np.uint8), 'RGBA')
        i = names.index(fn); holes.paste(Image.fromarray((m * 255).astype(np.uint8)), ((i % cols) * cw, (i // cols) * ch))
    part.save(os.path.join(OUT, f"{L['name']}.webp"), 'WEBP', quality=92, method=6)
    os.makedirs(PRE, exist_ok=True); holes.save(os.path.join(PRE, f"{L['name']}_holes.png"))
    ats = ', '.join(f'{fn}: [{x}, {y}, 0]' for fn, (x, y) in at.items())
    print(f"挂件 {L['name']}：{part.width}x{part.height} → web/assets/trio/{L['name']}.webp")
    print(f"cfg.parts：{{ src: 'assets/trio/{L['name']}.webp', pivot: {piv}, z: 1, at: {{ {ats} }}, sway: [...] }}")


def erase(c, E):
    """把引擎自己画的东西（秋千座板）从帧里抠掉：按 HSV 范围取色块里最大的那一块，再往外吃掉 grow 像素以内的深色描边。
    生图每格的座板长短、位置都不一样，留在帧里连播会一闪一闪；由引擎画一块固定的，绳子也正好接在它两头"""
    a = np.array(c).astype(np.float32)
    v = hsv(a)[2]
    m = in_hsv(a, [E['hsv']]) & (a[..., 3] > 128)
    m = ndimage.binary_closing(m, iterations=2)
    lab, k = ndimage.label(m)
    if not k: return c
    # 座板被腿隔成几段：取最大那段，再把跟它在同一条水平带上（竖直中心差 < band）的木色块都算进来
    sz = ndimage.sum(m, lab, range(1, k + 1)); top = int(np.argmax(sz)) + 1
    ob = ndimage.find_objects(lab)
    cy = lambda o: (o[0].start + o[0].stop) / 2
    band = E.get('band', 30)
    keep = [j + 1 for j in range(k) if sz[j] >= 80 and abs(cy(ob[j]) - cy(ob[top - 1])) < band and ob[j][0].stop - ob[j][0].start < 2.5 * band]
    big = ndimage.binary_fill_holes(np.isin(lab, keep))
    dark = v < 0.42
    kill = big | (ndimage.binary_dilation(big, iterations=E.get('grow', 5)) & dark)
    kill = ndimage.binary_dilation(kill, iterations=1) & ndimage.binary_dilation(big, iterations=E.get('grow', 5) + 1)   # 描边外沿的抗锯齿半透明也带走
    a[..., 3] *= ~kill
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def cells_of(name, spec):
    got = {}
    for sh in spec['sheets']:
        rgb, al = load_sheet(os.path.join(TRIO, name, sh['src']), sh.get('screen', 'auto'), sh.get('key'))
        rgb = edge_extend(rgb, al)
        for fn, c in zip(sh['frames'], split(rgb, al, len(sh['frames']))):
            got[fn] = erase(c, spec['erase']) if spec.get('erase') else c
    return got


def cmd_cells(d, spec):
    got = cells_of(d, spec)
    name = os.path.basename(d)
    os.makedirs(PRE, exist_ok=True)
    ims = [grid(c, z=1, label=f'{fn} {c.width}x{c.height}') for fn, c in got.items()]
    tile(ims, 4).save(os.path.join(PRE, f'{name}_cells.png'))
    print('格：', ', '.join(f'{fn} {c.size}' for fn, c in got.items()), '→ preview/%s_cells.png' % name)


def cmd_build(d, spec):
    got = cells_of(d, spec)
    name = os.path.basename(d)
    ref = got[spec['ref']]
    hb, fb = spec['head'], spec['fixed']
    head_t = gray(ref.crop(hb)); fix_t = gray(ref.crop(fb))
    lo, hi = spec.get('scale', [0.85, 1.2])
    place = {}                                          # 帧 → (缩放 s, 这一格原点落在参考帧坐标的 (tx, ty))
    loose = set(spec.get('loose', []))
    ref_low = np.nonzero((np.array(ref)[..., 3] > 128).any(1))[0].max()
    byfix = spec.get('scale_by') == 'fixed'
    loose_med = byfix or spec.get('loose_scale') == 'sheet'   # loose 帧的缩放取同一张条的中位数（头在飞扑 / 急刹里仰着按头找不准）
    sheet_of = {fn: i for i, sh in enumerate(spec['sheets']) for fn in sh['frames']}
    fixed_s = {}                                        # scale_by fixed：每张条里按板找到的缩放（loose 帧取同一张条的中位数）
    # 按板找缩放时先做非 loose 帧，loose 帧（板翘起来、找不准）再取同一张条里其它帧的中位数：同一张条人一样大，头在急刹里仰着按头找不准
    # scale_by "sheet"：同一张条里的姿势是一起画的、人一样大；每张条只在它的 scale_ref 帧（画了一遍 idle 的那格）上按头找一次缩放，
    # 整张条都用它（G12 仰头、收腿那几格按头 / 按臀找都会偏 10%）
    bysheet = spec.get('scale_by') == 'sheet'
    sheet_ref = {i: (spec['ref'] if spec['ref'] in sh['frames'] else sh.get('scale_ref', sh['frames'][-1])) for i, sh in enumerate(spec['sheets'])}
    sheet_s = {sheet_of[spec['ref']]: 1.0}
    scale_as = {fn: sh['scale_as'] for sh in spec['sheets'] if sh.get('scale_as') for fn in sh['frames']}
    order = lambda q: (q[0] in scale_as, bysheet and q[0] != sheet_ref[sheet_of[q[0]]], loose_med and q[0] in loose)
    for fn, c in sorted(got.items(), key=order):
        if fn == spec['ref']:
            place[fn] = (1.0, 0.0, 0.0, 1.0); fixed_s.setdefault(sheet_of[fn], []).append(1.0); continue
        if bysheet and fn != sheet_ref[sheet_of[fn]]:
            s = sheet_s[sheet_of[fn]]
            if fn in loose:
                cs = resize(c, s); h = find(gray(cs), head_t); low = np.nonzero((np.array(cs)[..., 3] > 128).any(1))[0].max()
                place[fn] = (s, float(hb[0] - h[1]), float(ref_low - low), h[2]); print(f'  {fn:8s} 同条缩放 {s:.2f}  loose'); continue
            r = find(gray(resize(c, s)), fix_t)
            place[fn] = (s, fb[0] - r[1], fb[1] - r[0], r[2]); print(f'  {fn:8s} 同条缩放 {s:.2f}  不动部位匹配 {r[2]:.2f}'); continue
        if loose_med and fn in loose and fixed_s.get(sheet_of[fn]):
            s = float(np.median(fixed_s[sheet_of[fn]])); cs = resize(c, s); h = find(gray(cs), head_t)
            low = np.nonzero((np.array(cs)[..., 3] > 128).any(1))[0].max()
            place[fn] = (s, float(hb[0] - h[1]), float(ref_low - low), h[2])
            print(f'  {fn:8s} 同条中位缩放 {s:.2f}  loose：横按头、竖按脚底')
            continue
        if fn in scale_as:
            # 条上写 "scale_as": "<帧>"：缩放照抄那一帧（P6 补帧：蒙版局部重绘的单格条，腿 / 屁股就是那一格的原像素，
            # 头改了表情 / 姿势按头找会顶到搜索边界，腿跟着被放大 10%）。只做平移配准
            s = place[scale_as[fn]][0]; r = find(gray(resize(c, s)), fix_t)
            place[fn] = (s, fb[0] - r[1], fb[1] - r[0], r[2]); print(f'  {fn:8s} 缩放照抄 {scale_as[fn]} {s:.2f}  不动部位匹配 {r[2]:.2f}'); continue
        best = None
        # scale_by "fixed"：缩放也按不动的部位找（脚下的滑板 / 平衡车：长短不变，头在蓄力 / 出手里仰着转着，按头找会顶到搜索边界）
        sc_t = fix_t if spec.get('scale_by') == 'fixed' and fn not in loose else head_t
        for s in np.arange(lo, hi + 1e-6, 0.01):
            r = find(gray(resize(c, s)), sc_t)
            if r and (best is None or r[2] > best[1]): best = (s, r[2])
        s = best[0]
        if fn in loose:
            # 走路这类脚在动的帧：没有"不动的部位"可配。横向按头对齐，竖向按脚底（剪影最低行）落在参考帧的地面线上
            cs = resize(c, s); h = find(gray(cs), head_t)
            low = np.nonzero((np.array(cs)[..., 3] > 128).any(1))[0].max()
            place[fn] = (s, float(hb[0] - h[1]), float(ref_low - low), h[2])
            print(f'  {fn:8s} 头缩放 {s:.2f}（匹配 {best[1]:.2f}）  loose：横按头、竖按脚底')
            continue
        r = find(gray(resize(c, s)), fix_t)
        place[fn] = (s, fb[0] - r[1], fb[1] - r[0], r[2])
        if loose_med: fixed_s.setdefault(sheet_of[fn], []).append(s)
        if bysheet: sheet_s[sheet_of[fn]] = s
        print(f'  {fn:8s} {"板" if sc_t is fix_t else "头"}缩放 {s:.2f}（匹配 {best[1]:.2f}）  不动部位匹配 {r[2]:.2f}')
    # 统一画布：所有帧（缩放、平移后）的并集
    bx0 = min(tx for s, tx, ty, _ in place.values()); by0 = min(ty for s, tx, ty, _ in place.values())
    bx1 = max(place[f][1] + got[f].width * place[f][0] for f in got); by1 = max(place[f][2] + got[f].height * place[f][0] for f in got)
    W, H = int(np.ceil(bx1 - bx0)), int(np.ceil(by1 - by0))
    full = {}
    for fn, c in got.items():
        s, tx, ty, _ = place[fn]
        # 输出像素 (u, v) ← 格内 ((u + bx0 − tx) / s, (v + by0 − ty) / s)
        full[fn] = c.transform((W, H), Image.AFFINE, (1 / s, 0, (bx0 - tx) / s, 0, 1 / s, (by0 - ty) / s), Image.BICUBIC)
    # 裁到全部帧 alpha 的并集，再缩到屏幕像素
    un = np.zeros((H, W), bool)
    for im in full.values(): un |= np.array(im)[..., 3] > 8
    ys, xs = np.nonzero(un)
    cx0, cy0, cx1, cy1 = max(0, xs.min() - 4), max(0, ys.min() - 4), min(W, xs.max() + 5), min(H, ys.max() + 5)
    ra = np.array(ref)[..., 3] > 8; rys, rxs = np.nonzero(ra)
    sil = (rxs.max() - rxs.min() + 1) if spec['size'][0] == 'w' else (rys.max() - rys.min() + 1)
    K = spec['size'][1] / sil
    cw, ch = int(round((cx1 - cx0) * K)), int(round((cy1 - cy0) * K))
    outs = {fn: im.crop((cx0, cy0, cx1, cy1)).resize((cw, ch), Image.LANCZOS) for fn, im in full.items()}
    tr = lambda p: [round(float((p[0] - bx0 - cx0) * K), 1), round(float((p[1] - by0 - cy0) * K), 1)]
    # 移植（graft）：模型偶尔把"不动的部位"本身画走样（樱木出手那格腿短一截，短裤对齐了脚尖还差 20px）—— 配准救不了，
    # 从好的一帧把那块原样搬过来。框是输出像素（_frames.png 上量），切口放在有描边能盖住的地方（裤脚）
    # feather：框左边这么宽一条从原帧渐变到好帧 —— 渐变带要落在两帧本来就对齐的地方（配准用的那块），硬切口落在大腿上是一道竖线
    for G in spec.get('graft', []):
        x0, y0, x1, y1 = G['box']
        fe = G.get('feather', 0)
        wx = np.clip((np.arange(x0, x1) - x0 + 0.5) / fe, 0, 1) if fe else np.ones(x1 - x0)
        for fn in G['to']:
            t = np.array(outs[fn]).astype(np.float32); src = np.array(outs[G['from']]).astype(np.float32)
            a, b = t[y0:y1, x0:x1], src[y0:y1, x0:x1]
            w = wx[None, :, None]
            al = a[..., 3:] * (1 - w) + b[..., 3:] * w
            rgb = (a[..., :3] * a[..., 3:] * (1 - w) + b[..., :3] * b[..., 3:] * w) / np.maximum(al, 1e-3)   # 按 alpha 加权混色
            t[y0:y1, x0:x1] = np.dstack([rgb, al])
            outs[fn] = Image.fromarray(t.clip(0, 255).astype(np.uint8), 'RGBA')
    for L in spec.get('lift', []): lift(outs, L)
    # 自检：输出上再配准一遍，量残差（输出像素）。头的缩放比也再量一遍（1.00 = 与参考帧一样大）
    oref = outs[spec['ref']]
    ofb = [round(v) for v in tr(fb[:2]) + tr(fb[2:])]
    ohb = [round(v) for v in tr(hb[:2]) + tr(hb[2:])]
    ft, htt = gray(oref.crop(ofb)), gray(oref.crop(ohb))
    print(f'画布 {cw}x{ch}（K {K:.4f}）；配准残差 = 不动部位在该帧里的位置 − 参考帧（输出像素）：')
    worst = 0
    for fn, im in outs.items():
        g = gray(im)
        # 只在参考位置 ±12 像素里找（全图找会被身上相似的纹理拐走）
        x0, y0 = max(0, ofb[0] - 12), max(0, ofb[1] - 12)
        win = g[y0:ofb[3] + 12, x0:ofb[2] + 12]
        r = find(win, ft)
        dx, dy = r[1] + x0 - ofb[0], r[0] + y0 - ofb[1]
        hs = max(((s2, find(gray(resize(im, s2)), htt)) for s2 in np.arange(0.9, 1.1, 0.01)), key=lambda q: q[1][2] if q[1] else -1)[0]
        if fn in loose:                                  # 没按不动部位配，这里的数不算残差
            print(f'  {fn:8s} （loose，不计）  头 {1 / hs:.2f}'); continue
        worst = max(worst, abs(dx), abs(dy))
        print(f'  {fn:8s} dx {dx:+5.2f} dy {dy:+5.2f}  头 {1 / hs:.2f}')
    print(f'  最大残差 {worst:.2f}px（验收 ≤ 2）')
    # 另外几个本该不动的部位（check：[[x0, y0, x1, y1, "名"], ...]，输出像素）：配准只保证 fixed 那一块，别的部位被模型画长画短在这里现形
    for x0, y0, x1, y1, lab in spec.get('check', []):
        t = gray(oref.crop((x0, y0, x1, y1)))
        row = []
        for fn, im in outs.items():
            g = gray(im); wx, wy = max(0, x0 - 30), max(0, y0 - 30)
            r = find(g[wy:y1 + 30, wx:x1 + 30], t)
            row.append(f'{fn} {r[1] + wx - x0:+.1f},{r[0] + wy - y0:+.1f}')
        print(f'  {lab}：' + '  '.join(row))
    # 图集
    names = list(outs)
    cols = min(4, len(names)); rows = (len(names) + cols - 1) // cols
    atlas = Image.new('RGBA', (cw * cols, ch * rows))
    for i, fn in enumerate(names): atlas.paste(outs[fn], ((i % cols) * cw, (i // cols) * ch))
    os.makedirs(OUT, exist_ok=True)
    atlas.save(os.path.join(OUT, f'{name}.webp'), 'WEBP', quality=90, method=6)
    meta = {'cell': [cw, ch], 'cols': cols, 'frames': names, 'anchor': tr(spec['anchor']), 'residual': round(float(worst), 2),
            'head': ohb, 'ref': spec['ref']}                   # 参考帧头框（输出像素）：combo_scan.py 判"头被挡"用
    with open(os.path.join(OUT, f'{name}.json'), 'w') as f: json.dump(meta, f, ensure_ascii=False)
    kb = os.path.getsize(os.path.join(OUT, f'{name}.webp')) // 1024
    print(f'→ web/assets/trio/{name}.webp（{atlas.width}x{atlas.height}，{kb}KB，{cols} 列）')
    print(f'cfg：frames: {{ src: \'assets/trio/{name}.webp\', cell: [{cw}, {ch}], cols: {cols}, names: {json.dumps(names)} }}, anchor: {meta["anchor"]}')
    # 预览
    os.makedirs(PRE, exist_ok=True)
    tile([grid(outs[fn], label=fn) for fn in names], cols).save(os.path.join(PRE, f'{name}_frames.png'))
    on = Image.new('RGBA', (cw, ch), (255, 255, 255, 255))
    for im in outs.values():
        t = im.copy(); t.putalpha(Image.fromarray((np.array(im)[..., 3] * 0.35).astype(np.uint8))); on.alpha_composite(t)
    d = ImageDraw.Draw(on); d.rectangle(ofb, outline=(0, 160, 255, 255), width=2)
    ax, ay = meta['anchor']; d.ellipse([ax - 5, ay - 5, ax + 5, ay + 5], outline=(255, 0, 0, 255), width=2)
    on.convert('RGB').resize((cw * 2, ch * 2), Image.LANCZOS).save(os.path.join(PRE, f'{name}_onion.png'))
    tile([outs[fn] for fn in names], cols, bg=(255, 236, 40)).save(os.path.join(PRE, f'{name}_yellow.png'))


if __name__ == '__main__':
    d, cmd = sys.argv[1].rstrip('/'), sys.argv[2]
    with open(os.path.join(TRIO, d, 'frames.json')) as f: spec = json.load(f)
    {'cells': cmd_cells, 'build': cmd_build}[cmd](d, spec)
