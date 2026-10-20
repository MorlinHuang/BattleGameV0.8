"""闺蜜定妆（审查 3）里要单独分层的部件：人一层、部件各一层，同一张画布，叠起来就是 ref/G<n>.png（总览用）。
做法同哥们 B18 折扇（buddy/b18_layers.py）：人和部件分开生图，抠像后按锚点摆放。
  G5   算盘      ref/G5_body.png   + ref/G5_abacus.png   （算盘在人前，横挂腰侧；拍算盘那帧要用）
  G13  麻绳      ref/G13_body.png  + ref/G13_rope.png    （程序画的麻绳，局部重绘生图被拒两次；绳子层在人前，已扣掉被腿/脚/手臂挡住的部分）
  G18  翎子/靠旗 ref/G18_body.png  + ref/G18_feathers.png + ref/G18_flags.png（两层都在人身后）
  G29  竹棒      ref/G29_body.png  + ref/G29_staff.png   （斜背在背后，在人身后；出手那帧隐藏）
叠放顺序：每层标 'back'/'front'。存盘时裁到所有层的包围盒再四周留 PAD（G13 的绳子故意两端出画，裁回原画布）。
原图：src/<名>_body_src.png（人），src/props_src.png（四件部件一张，透明底：靠旗、翎子、算盘、竹棒，从左到右）。"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../..'))
from crewart import cut, edge_extend
REF, SRC = os.path.join(HERE, 'ref'), os.path.join(HERE, 'src')
PAD = 60

def cut_blue(path, key=(40, 150)):
    """蓝幕抠像（crewart.cut 只有品红 / 绿）：键值 b − max(r, g)，其余同 crewart.cut —— 软阈值、清 60 px 以下碎块、只在半透明过渡带去溢色。
    角色身上同时有粉紫和绿的用蓝幕（G17 粉绿发、G9 粉丝巾 + 绿叶衬衫）。"""
    a = np.array(Image.open(path).convert('RGB')).astype(np.int16)
    k = a[..., 2] - np.maximum(a[..., 0], a[..., 1])
    al = np.clip(1 - (k - key[0]) / (key[1] - key[0]), 0, 1).astype(np.float32)
    lab, n = ndimage.label(al > 0.05)
    if n:
        sz = ndimage.sum(np.ones_like(al), lab, range(1, n + 1))
        al[np.isin(lab, np.nonzero(sz < 60)[0] + 1)] = 0
    rgb = a.astype(np.float32)
    rgb[..., 2] = np.where(al < 0.99, np.minimum(rgb[..., 2], np.maximum(rgb[..., 0], rgb[..., 1])), rgb[..., 2])
    return rgb, al

def rgba_cut(path, screen):
    if screen == 'blue':
        rgb, al = cut_blue(path)
        return Image.fromarray(np.dstack([edge_extend(rgb, al), al * 255]).clip(0, 255).astype(np.uint8), 'RGBA')
    if screen == 'alpha':      # 生图直接给了透明底：用它自带的 alpha
        return Image.open(path).convert('RGBA')
    rgb, al = cut(path, screen, (40, 150))
    return Image.fromarray(np.dstack([edge_extend(rgb, al), al * 255]).clip(0, 255).astype(np.uint8), 'RGBA')

def props():
    """props_src.png 按连通块拆成四件，从左到右：flags, feathers, abacus, staff。每件裁到自身包围盒。"""
    im = Image.open(os.path.join(SRC, 'props_src.png')).convert('RGBA'); a = np.array(im)
    lab, n = ndimage.label(ndimage.binary_dilation(a[..., 3] > 20, iterations=6))
    ids = [i + 1 for i, o in enumerate(ndimage.find_objects(lab)) if (o[0].stop - o[0].start) * (o[1].stop - o[1].start) > 5000]
    ids.sort(key=lambda i: np.nonzero(lab == i)[1].mean())
    out = {}
    for name, i in zip(['flags', 'feathers', 'abacus', 'staff'], ids):
        b = a.copy(); b[lab != i, 3] = 0
        p = Image.fromarray(b, 'RGBA'); out[name] = p.crop(p.getbbox())
    return out

def place(canvas_size, part, height=None, width=None, angle=0, anchor=(0.5, 0.5), at=(0, 0)):
    """把部件缩放（按高或宽）、绕 anchor（部件内比例坐标）逆时针转 angle 度，让 anchor 落在画布 at 点。返回整张画布大小的层。"""
    k = height / part.height if height else width / part.width
    p = part.resize((max(1, round(part.width * k)), max(1, round(part.height * k))), Image.LANCZOS)
    ax, ay = anchor[0] * p.width, anchor[1] * p.height
    m = max(p.width, p.height)                     # 转动用的方形底板，按长边留足，细长件转斜了也不被裁
    big = Image.new('RGBA', (p.width + 2 * m, p.height + 2 * m)); big.paste(p, (m, m))
    big = big.rotate(angle, resample=Image.BICUBIC, center=(ax + m, ay + m))
    layer = Image.new('RGBA', canvas_size)
    layer.alpha_composite(big, (round(at[0] - ax - m), round(at[1] - ay - m)))
    return layer

def upright(part):
    """把细长部件（竹棒）按 alpha 主轴转成竖直，再裁到包围盒。"""
    a = np.array(part)[..., 3] > 20; ys, xs = np.nonzero(a)
    c = np.cov(np.stack([xs - xs.mean(), ys - ys.mean()]))
    w, v = np.linalg.eigh(c); vx, vy = v[:, -1]
    ang = math.degrees(math.atan2(vy, vx))             # 主轴与 +x 的夹角（图像坐标，y 向下）
    r = part.rotate(ang - 90 if ang > 0 else ang + 90, resample=Image.BICUBIC, expand=True)
    return r.crop(r.getbbox())

def rope_layer(size, co, thick=18):
    """G13 麻绳：沿抛物线 y = co(x) 画一根黄褐绞股麻绳，4 倍超采样。左右两端出画。"""
    S = 4; W, H = size[0] * S, size[1] * S
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    xs = np.arange(-20, size[0] + 21, 2.0)
    ys = np.polyval(co, xs)
    # 每条色带画成"中心线沿法线两侧偏移"围成的多边形。不用多点粗线 d.line：线段短（8 px）、线宽大（88 px）时，
    # PIL 在折点之间留楔形缺口（joint='curve' 也补不上），绳子边上一排透光刻痕，绳身里还有半透明竖条
    dy = np.gradient(ys); nx, ny = -dy / np.hypot(1, dy), 1 / np.hypot(1, dy)   # 单位法线（指向 y 增大一侧）
    def strip(off, half, fill):
        up = [((x + nx_ * (off - half)) * S, (y + ny_ * (off - half)) * S) for x, y, nx_, ny_ in zip(xs, ys, nx, ny)]
        dn = [((x + nx_ * (off + half)) * S, (y + ny_ * (off + half)) * S) for x, y, nx_, ny_ in zip(xs, ys, nx, ny)]
        d.polygon(up + dn[::-1], fill=fill)
    strip(0, thick / 2 + 2, (40, 26, 14, 255))                        # 描边（两侧各 2 px）
    strip(0, thick / 2, (196, 146, 82, 255))                          # 麻色
    strip(thick * 0.22, thick * 0.2, (160, 112, 58, 255))             # 下半暗部
    strip(-thick * 0.27, thick * 0.08, (226, 186, 122, 255))          # 上缘高光
    # 绞股纹：沿绳每 11 px 一道斜线（切线方向转 55°）
    L = np.concatenate([[0], np.cumsum(np.hypot(np.diff(xs), np.diff(ys)))])
    for s in np.arange(0, L[-1], 11):
        x = np.interp(s, L, xs); y = np.interp(s, L, ys)
        t = math.atan2(np.polyval(np.polyder(co), x), 1)
        a = t + math.radians(55); h = thick / 2 / math.sin(math.radians(55))
        d.line([((x - h * math.cos(a)) * S, (y - h * math.sin(a)) * S), ((x + h * math.cos(a)) * S, (y + h * math.sin(a)) * S)],
               fill=(92, 60, 30, 255), width=round(1.6 * S))
    return im.resize(size, Image.LANCZOS)

GROW = 900   # 摆部件前先把人的画布四周扩这么多，伸出原图的翎子 / 靠旗 / 竹棒才不被裁；存盘时再裁到包围盒 + PAD

def grow(im):
    out = Image.new('RGBA', (im.width + 2 * GROW, im.height + 2 * GROW)); out.alpha_composite(im, (GROW, GROW)); return out

def at(x, y):
    """原图坐标 → 扩边后画布坐标。"""
    return (x + GROW, y + GROW)

def save(name, body, layers, keep_edges=False):
    """layers: [(层名, 层, 'back'/'front')]，都和 body 同画布（已 grow）。裁到所有层的包围盒 + PAD 后保存各层 + 合成图。
    keep_edges：故意出画的（G13 绳子两端出画），裁回原图画布。"""
    ims = [body] + [l for _, l, _ in layers]
    boxes = [i.getbbox() for i in ims]
    box = (min(b[0] for b in boxes) - PAD, min(b[1] for b in boxes) - PAD, max(b[2] for b in boxes) + PAD, max(b[3] for b in boxes) + PAD)
    if keep_edges:
        box = (GROW, GROW, body.width - GROW, body.height - GROW)
    body_p, lay_p = body.crop(box), [l.crop(box) for _, l, _ in layers]
    body_p.save(os.path.join(REF, f'{name}_body.png'))
    out = Image.new('RGBA', body_p.size)
    for (ln, _, side), l in zip(layers, lay_p):
        l.save(os.path.join(REF, f'{name}_{ln}.png'))
        if side == 'back': out.alpha_composite(l)
    out.alpha_composite(body_p)
    for (ln, _, side), l in zip(layers, lay_p):
        if side == 'front': out.alpha_composite(l)
    out.save(os.path.join(REF, f'{name}.png'))
    a = np.array(out)[..., 3] > 8; ys, xs = np.nonzero(a)
    print(name, 'canvas', out.size, 'margin L/T/R/B', xs.min(), ys.min(), out.width - 1 - xs.max(), out.height - 1 - ys.max())
    return out

if __name__ == '__main__':
    P = props()
    only = sys.argv[1:]

    if not only or 'G5' in only:
        body = grow(rgba_cut(os.path.join(SRC, 'G5_body_src.png'), 'green'))
        # 腰宽：y 650 那行约 256~704 = 448（含褙子）；算盘宽取 0.62 倍 ≈ 280
        # 挂点在左侧腰带（y≈640，身后那侧的胯边），算盘斜挂、上沿中点吊在绳下 50 px；绳子画在算盘层里
        hang, ang = at(318, 640), 14
        ab = place(body.size, P['abacus'], width=280, angle=ang, anchor=(0.5, 0.0), at=(hang[0] - 6, hang[1] + 50))
        d = ImageDraw.Draw(ab)
        d.line([hang, (hang[0] - 6, hang[1] + 54)], fill=(40, 20, 16, 255), width=7)
        d.line([hang, (hang[0] - 6, hang[1] + 54)], fill=(200, 40, 50, 255), width=4)
        save('G5', body, [('abacus', ab, 'front')])

    if not only or 'G29' in only:
        body = grow(rgba_cut(os.path.join(SRC, 'G29_body_src.png'), 'alpha'))
        # 蹲姿包围盒高 1156；站立身高按 1.55 倍估 ≈ 1790，棒长取 0.8 倍 ≈ 1430。
        # 斜背在背后：从左肩后上方斜到右腰后下方（左上 → 右下），竖直棒逆时针转 25°；下端藏在臀胯后面，不从两腿之间穿出来
        st = place(body.size, upright(P['staff']), height=1430, angle=25, anchor=(0.5, 0.5), at=at(258, 152))
        save('G29', body, [('staff', st, 'back')])

    if not only or 'G18' in only:
        body = grow(rgba_cut(os.path.join(SRC, 'G18_body_src.png'), 'magenta'))
        # 半蹲包围盒高 1423，站立身高按 /0.9 估 ≈ 1580；每根翎子弧长约 0.6 倍 ≈ 950。
        # 翎子素材两根弧长 ≈ 1.25 × 包围盒高，所以包围盒高取 950 / 1.25 ≈ 760。根部插在盔头顶后侧，整对往后（左）仰 15°
        fe = place(body.size, P['feathers'], height=760, angle=15, anchor=(0.5, 1.0), at=at(430, 125))
        # 靠旗：插座在后背肩胛之间，四面扇形朝上，高出盔头约一个头，往后仰 12°
        fl = place(body.size, P['flags'], height=720, angle=12, anchor=(0.5, 1.0), at=at(335, 470))
        save('G18', body, [('flags', fl, 'back'), ('feathers', fe, 'back')])

    if not only or 'G13' in only:
        # 麻绳：局部重绘生图两次 422（躺姿 + 编辑模式被拒），改为程序画。中心线 = 原图细绳拟合的抛物线（绳子两端出画、中间下垂）。
        CO = (-7.10200401e-05, 1.59854088e-01, 3.98340456e+02)
        LEG_X = 1300    # 这以右是小腿到脚跟，压在绳子上
        src = rgba_cut(os.path.join(SRC, 'G13_v1.png'), 'green'); a = np.array(src)
        H, W = a.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]
        yc = np.polyval(CO, xx)
        near = np.abs(yy - yc) <= 7
        r, g, b = [a[..., i].astype(int) for i in range(3)]
        fg = a[..., 3] > 128
        # 人这层：去掉悬在幕布上的那段细绳（上下 12 px 外都是幕布），压在衣服 / 头发上的留着，被新绳盖住
        # 取 ±16 px：拟合中心线在最左端比原细绳高约 10 px，±7 会漏掉一截旧绳，从新绳下面露出来
        over_bg = (np.abs(yy - yc) <= 16) & ~np.roll(fg, 12, 0) & ~np.roll(fg, -12, 0)
        a[over_bg, 3] = 0
        skin = (r > 200) & (g > 150) & (b > 110) & (r - b > 25) & (r - b < 100) & (r > g) & (g > b)
        skin = ndimage.binary_opening(skin, iterations=2)
        skin = ndimage.binary_fill_holes(ndimage.binary_closing(skin, iterations=3))
        skin = ndimage.gaussian_filter(skin.astype(float), 2) > 0.5          # 边缘磨圆，手肘压绳处不留缺口
        # x ≥ LEG_X：小腿压在绳子上。逐列找小腿下沿（从绳带上方一路往下连续是皮肤的最低点），沿 x 中值平滑成一条干净的轮廓；
        # 人层在绳带里只保留小腿（下沿以上，颜色取正上方的皮肤），原图的细绳、它的描边碎块、绿幕溢色一律清掉
        band = np.abs(yy - yc) <= 12
        bottom = np.full(W, -1)
        for x in range(LEG_X, W):
            y0 = int(yc[0, x]) - 12
            if not skin[y0, x]: continue
            y = y0
            while y + 1 < H and skin[y + 1, x] and y + 1 <= y0 + 24: y += 1
            bottom[x] = y
        has = bottom >= 0
        seg = np.nonzero(has)[0]                               # 下沿只在有小腿的列上平滑：中值去尖刺 + 高斯去台阶
        sm = ndimage.gaussian_filter1d(ndimage.median_filter(bottom[seg].astype(float), size=15), 6)
        bottom = np.full(W, -1); bottom[seg] = np.round(sm).astype(int)
        bottom[:LEG_X] = -1
        leg = (yy <= bottom[None, :]) & band & (bottom[None, :] >= 0)
        clear = band & (xx >= LEG_X) & ~leg
        a[clear, 3] = 0
        for x in np.nonzero(bottom >= 0)[0]:                   # 小腿在带子里的像素统一取带子上沿的皮肤色，盖掉被细绳压着的那几行
            y0 = int(yc[0, x]) - 12
            a[y0:bottom[x] + 1, x, :3] = a[y0 - 1, x, :3]; a[y0:bottom[x] + 1, x, 3] = 255
        body = grow(Image.fromarray(a, 'RGBA'))
        # 遮挡（绳子在这些东西后面）：x < LEG_X 是手肘、大腿，按肤色（已闭运算 + 填洞）；x ≥ LEG_X 是小腿，按上面的下沿
        occ = np.where(xx < LEG_X, skin, leg | ((yy < yc) & (a[..., 3] > 128) & ~band))
        rope = np.array(rope_layer((W, H), CO, thick=18))
        drawn = rope[..., 3] > 0
        rope[occ, 3] = 0
        # 截断的边补 2 px 深棕描边（小腿、手肘的下轮廓原图被细绳压着没有线）。
        # 按"绳子画到的地方"（alpha > 0，含抗锯齿边）算：小腿下沿刚好贴着绳子上缘的那几列，绳子抗锯齿边半透明，不补就是一条透光缝
        edge = (rope[..., 3] > 0) & ndimage.binary_dilation(occ & drawn, iterations=2)
        rope[edge, :3] = (40, 26, 14); rope[edge, 3] = 255
        save('G13', body, [('rope', grow(Image.fromarray(rope, 'RGBA')), 'front')], keep_edges=True)
