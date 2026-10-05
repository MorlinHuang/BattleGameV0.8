"""v14 素材构建：长卷背景 + 姿势贴图 + 元数据。在 chashouji/ 下运行：python3 v14/build.py

产物全部写进 web/assets/world/，外加一份 world.json 给 main.js 读：
  room0/1/2.webp   三段房间（女生卧室｜客厅｜电竞房），高 1334
  pose_*.webp      抠好的角色贴图，已裁到外框
  world.json       房间宽度、客厅中点、每张贴图的锚点与手机位置

────────── 背景怎么拼 ──────────
三张房间图是分开生成的，每张在接缝那一侧都画了一扇被画面边缘切开的门：
女生卧室右边缘有门（左门框 + 透出客厅的门洞），客厅左边缘也有门（门洞 + 右门框）。
拼的时候**一扇门取两张图各一半**：卧室那张留到右边缘（左门框+门洞），客厅那张从它
自己的右门框开始 —— 于是接缝落在门洞里，读出来是"一扇门"，不是两张图硬拼。
电竞房那边同理。切点的像素位置是对着原图量出来的（CUT_*），换图必须重量。

────────── 角色贴图怎么对齐 ──────────
基准缩放 SCALE，被拉倒各档再按赢方的头补一个系数（head_scale）——生图时虽然写死了"站立身高约占画面 78%"，
扑倒/趴那几张实测还是画小了 5~9%。尺子只能用头，不能用面积 ——
坐在地上被拖的那个人面积本来就小，按面积放大就把他放成巨人。
锚点 = (外框中点 x, 脚底线 y)：引擎把锚点对到屏幕中线与地面线上。按外框而不是质心：
拖地姿势宽约 1000px，比屏幕还宽，按质心对齐会让一侧整整多出画 100 多像素。
僵持循环那几帧例外：脚是钉在地上不动的，所以水平按**脚那一截**的质心对齐，
否则上身前后倾会把整个人带着左右滑，读成"脚在冰上打滑"。

────────── 手机位置 ──────────
弹幕往手机那条竖线上打、聊天气泡从手机里冒出来，所以每张贴图都要知道手机在哪。
自动找：近黑像素的连通块里，挑"沿自身方向量的填充率高 + 长条"的那一块（手机可以斜着）。头发也是黑的，
但它是散的（填充率低）；裤子是黑的，但它是竖的、面积大。每次重跑都会把找到的
位置画到 v14/preview/phone_check.jpg 上，**必须看一眼**再部署。
"""
import json
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import ConvexHull
from scipy.signal import fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'web', 'assets', 'world')
H = 1707      # 画布高 = 960 宽下的 9:16（最终 1080×1920）。背景 *_ext.png 高 1818，缩放系数与原 1334/1421 一致
# 1536×1024 的生图 → 引擎像素。站立的人约 400 高。
# 原来是 0.66（约 600 高），用户嫌人占画面太大，要"镜头拉远、人变成现在的 2/3"：
# 人和房间一起缩 2/3（房间见 main() 里的 *_ext.png），不能只缩人 —— 沙发会比人大一圈
SCALE = 0.44
K = np.ones((3, 3), np.float32)

# 门的切点（原图 1659×948 坐标）：卧室留到右边缘；客厅从它左门的右门框起、
# 留到右边缘（含右门的左门框+门洞）；电竞房从它左门的右门框起
CUT_LIVING_L = 75
CUT_BOY_L = 140


def keyed(a):
    """品红度 m = min(R,B) - G，m 大 = 幕布。a 必须是有符号类型（uint8 相减会下溢）"""
    return np.minimum(a[..., 0], a[..., 2]) - a[..., 1]


def plant_feet(frame, base, mask):
    """步态帧的脚踩回地面。局部重绘出来的腿普遍比原图短一截（实测 20~55 原图像素），
    站着的那只脚悬在半空，播起来一步一飘（偶尔也有画长了、脚陷进地板的）。上半身不能往下挪 —— 扑倒/趴的那一档，输的人
    就贴在地上，整张下移他会陷进地板。所以只把蒙版那一块（胯以下）竖着拉长：蒙版顶边
    那一行不动（跟没重画的胯接得上），最低的那只脚落到原图的地面线上。"""
    ys, xs = np.nonzero(np.array(Image.open(mask))[..., 3] == 0)
    x0, x1, y0 = xs.min(), xs.max() + 1, ys.min()
    a = np.array(Image.open(frame).convert('RGB').resize(Image.open(base).size)).astype(np.int16)
    b = np.array(Image.open(base).convert('RGB')).astype(np.int16)

    def floor(img):
        return np.nonzero((keyed(img[:, x0:x1]) < 60).sum(1) > 2)[0].max()
    want, got = floor(b), floor(a)
    # 输出第 r 行取原图第 y0 + (r-y0)·(got-y0)/(want-y0) 行：r=want 正好取到脚底。
    # 脚画低了（got > want）同一个式子就是往回压，越出图底的行取品红底
    rows = y0 + (np.arange(y0, a.shape[0]) - y0) * (got - y0) / (want - y0)
    block = np.concatenate([a[:, x0:x1], np.tile(a[-1:, x0:x1], (80, 1, 1))]).astype(np.float32)
    lo = np.minimum(np.floor(rows).astype(int), len(block) - 2); t = (rows - lo)[:, None, None]
    a[y0:, x0:x1] = np.round(block[lo] * (1 - t) + block[lo + 1] * t).astype(np.int16)
    return a


def stride(base, mask):
    """原图里赢方两只脚之间的距离（原图像素）= 一步的长度。base 是双脚着地那一格：
    站地的脚在半个循环里正好从身后挪到身前，走过的就是这一段。
    取地面线往上 90 行里的前景列（前脚常比后脚高 40 多行，只取 40 行会漏掉它），按最大的空隙切成两只脚，量两块中心的距离。"""
    ys, xs = np.nonzero(np.array(Image.open(mask))[..., 3] == 0)
    x0, x1 = xs.min(), xs.max() + 1
    b = np.array(Image.open(base).convert('RGB')).astype(np.int16)[:, x0:x1]
    fg = keyed(b) < 60
    floor = np.nonzero(fg.sum(1) > 2)[0].max()
    cols = np.nonzero(fg[floor - 90:floor + 1].any(0))[0]
    cut = np.argmax(np.diff(cols))
    return cols[cut + 1:].mean() - cols[:cut + 1].mean()


def cutout(path, lo=60, hi=150):
    a = path if isinstance(path, np.ndarray) else np.array(Image.open(path).convert('RGB')).astype(np.int16)
    m = keyed(a)
    alpha = np.clip((hi - m) / (hi - lo), 0, 1)
    edge = ndimage.binary_dilation(alpha < 0.99, np.ones((3, 3))) & (alpha > 0.01)
    rgb = a.astype(np.float32)
    spill = np.clip((rgb[..., 0] + rgb[..., 2]) / 2 - rgb[..., 1], 0, None)
    for c in (0, 2):   # 去溢色只动半透明边缘，不透明的粉睡衣本身就偏红
        rgb[..., c] = np.where(edge, rgb[..., c] - spill * 0.6, rgb[..., c])
    return np.clip(rgb, 0, 255), alpha


def load_cut(path):
    """原图 → (rgb, alpha)。自带透明通道的（生图有时直接出透明底）直接用它；否则按品红幕布抠。
    不能把透明底铺回品红再抠：keyed / 去溢色把偏品红的颜色（粉色水枪、粉 / 淡紫平衡车、紫衬衫）当成幕布，
    抠成半透明、洗成土褐色（哥们 3 号第一版）。"""
    im = Image.open(path)
    if im.mode == 'RGBA':
        a = np.array(im).astype(np.float32)
        if a[..., 3].min() < 255:
            return a[..., :3], a[..., 3] / 255
    return cutout(path)


def edge_extend(rgb, al, iters=10):
    rgb = rgb.copy()
    mask = al > 0.03
    for _ in range(iters):
        m = mask.astype(np.float32)
        cnt = ndimage.convolve(m, K, mode='constant')
        acc = np.stack([ndimage.convolve(rgb[..., c] * m, K, mode='constant') for c in range(3)], -1)
        grown = cnt > 0
        fill = grown & ~mask
        if not fill.any():
            break
        rgb[fill] = (acc / np.maximum(cnt, 1)[..., None])[fill]
        mask |= grown
    return rgb


def find_phone(rgb, al):
    dark = (rgb.max(-1) < 70) & (al > 0.9)
    lab, n = ndimage.label(dark)
    best, score = None, 0
    h, w = al.shape
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        ys, xs = sl
        py, px = np.nonzero(lab[sl] == i)
        area = len(px)
        if not 0.0012 * h * w < area < 0.03 * h * w:
            continue
        if ys.start > h * 0.75:           # 拖鞋在最底下，手机不会在那
            continue
        # 长宽沿块自己的主方向量，不用水平外框：趴地那两张手机是斜着拿的，
        # 水平外框只填得满一半，会被当成散开的头发筛掉
        pts = np.stack([px, py], 1).astype(np.float32)
        pts -= pts.mean(0)
        _, vec = np.linalg.eigh(np.cov(pts.T))
        proj = pts @ vec
        ext = proj.max(0) - proj.min(0) + 1
        long_, short = ext.max(), ext.min()
        fill = area / (long_ * short)
        if not (1.3 < long_ / max(short, 1) < 3.6 and fill > 0.62):
            continue
        s = fill * area
        if s > score:
            score, best = s, (xs.start + px.mean(), ys.start + py.mean(), long_, short)
    return best


# 手机放大倍数（2026-09-27 用户定：样式不变、稍微放大；×1.5 机身两头会从拳头后面伸出一截，
# 斜拿的趴地姿势尤其像抓着一块板的中段，×1.3 两头刚好藏在拳头后面）
PHONE_K = 1.3
PHONE_PAD = 2     # 机身连通块外扩几像素：把它的描边和抗锯齿边一起带上
OLD_PAD = 9       # 旧机身凸包外扩几像素算旧机身（偏亮的边框、抗锯齿边、下沿阴影），这一圈里只盖回拳头


def enlarge_phone(rgb, al, ph):
    """原图分辨率下把手机放大 PHONE_K 倍贴回原位（中心不动，meta.phone 不变），点亮屏幕（light_phone），再把机身附近的手盖回最上面。
    必须在原图上先 find_phone 再调这里：屏幕亮了以后就不是"近黑长条"，找不到了。
    机身 = find_phone 找到的那块近黑连通块的凸包；手 = 机身附近、旧机身以外的不透明像素。"""
    cx, cy, long_, _ = ph
    dark = (rgb.max(-1) < 70) & (al > 0.9)
    lab, _ = ndimage.label(dark)
    i = lab[int(round(cy)), int(round(cx))]
    if i == 0:                            # 中心恰好落在高光上：取离中心最近的暗像素所在的块
        ys, xs = np.nonzero(dark)
        j = np.argmin((xs - cx) ** 2 + (ys - cy) ** 2)
        i = lab[ys[j], xs[j]]
    ys, xs = np.nonzero(lab == i)                 # 机身是凸的长方形：取暗块的凸包。偏亮的边框、屏幕反光不算"近黑"，
    hull = ConvexHull(np.stack([xs, ys], 1))       # 只拿暗块本身放大，边上会缺一排口子
    m = Image.new('L', (al.shape[1], al.shape[0])); ImageDraw.Draw(m).polygon([(xs[v], ys[v]) for v in hull.vertices], fill=1)
    core = np.array(m).astype(bool)
    body = ndimage.binary_dilation(core, iterations=PHONE_PAD) & (al > 0.03)
    r = int(long_ * PHONE_K)              # 只在机身周围这一块里动
    y0, y1 = max(0, int(cy) - r), min(al.shape[0], int(cy) + r)
    x0, x1 = max(0, int(cx) - r), min(al.shape[1], int(cx) + r)
    near = np.zeros(al.shape, bool); near[y0:y1, x0:x1] = True
    # 手机在两人的手后面：原图里旧机身以外的不透明像素（拳头、指缝阴影、手臂）全盖回最上面 ——
    # 只按肤色挑"手"会漏掉偏暗的指缝阴影，亮屏从那里透出来，整只拳头发灰。
    # 旧机身所在的那一圈（凸包外扩 OLD_PAD）里只盖回拳头：肤色外扩 3px（带上手指描边）。
    # 那一圈里的旧边框、反光、下沿阴影颜色五花八门（斜拿的还带色偏），按"灰 / 暗"去认总有漏的，漏一个就是屏上一个点；
    # 凸包本身又会把压在机身两头的指节包进去，整圈不盖的话亮屏会画在指节上
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    skin = ndimage.binary_dilation((R > 150) & (R > G + 10) & (G > B - 5) & (al > 0.5), iterations=3)
    hand = near & ~(ndimage.binary_dilation(core, iterations=OLD_PAD) & ~skin) & (al > 0.5)
    rgba = np.concatenate([rgb, al[..., None] * 255], -1).astype(np.float32)
    lay = np.where(body[..., None], rgba, 0)[y0:y1, x0:x1].astype(np.uint8)
    im = Image.fromarray(lay, 'RGBA')
    big = im.resize((round(im.width * PHONE_K), round(im.height * PHONE_K)), Image.BICUBIC)
    ox, oy = round(x0 + (cx - x0) * (1 - PHONE_K)), round(y0 + (cy - y0) * (1 - PHONE_K))   # 以机身中心为原点放大
    full = Image.fromarray(rgba.clip(0, 255).astype(np.uint8), 'RGBA')
    over = Image.new('RGBA', full.size); over.paste(big, (ox, oy))
    full.alpha_composite(over)
    big_core = np.array(over)[..., 3] > 127
    out = light_phone(full, big_core)
    out[hand] = rgba[hand]                # 手盖回最上面
    return out[..., :3], out[..., 3] / 255


# 亮屏（2026-09-27 用户：「手机屏幕可以亮着 然后软件是某聊天软件，但屏幕太小 不用具体显示聊天记录」）。
# 第一版读出"亮着"靠冷色渐变 + 机身外一圈蓝光晕 + 拳头染冷光，屏幕占满机身、黑边只剩 2px ——
# 用户：「手机现在发光，一眼看上去反而不像手机」：读成一块发光的浅蓝方块。手机之所以认得出是手机，靠的是
# **近白的屏 + 一圈明显的黑边框**这对反差、外加玻璃反光和前摄小圆点，不靠发光。所以光晕、染手都去掉了。
# 长度单位都是原图像素（贴图最后 ×SCALE≈0.44 上屏）。界面是固定图案、不随机，53 张帧一模一样，连播不闪。
SCREEN = {'w': 0.8, 'h': 0.68,                               # 屏幕占机身长 / 宽的比例（四周剩下的是黑边框：短边两头更宽）
          'bg': (245, 247, 250), 'round': 0.08,              # 近白屏底；屏幕圆角半径占屏宽几成
          'bar': (20, 200, 110), 'bar_h': 0.12,              # 顶栏：偏蓝的绿（跟真相喷雾的青柠 156,238,96 区分开）、占竖屏高（转过来在女生那头，大半压在她拳头下）
          'input_h': 0.1,                                    # 底部输入栏占竖屏高
          'rows': [('them', 0.55), ('me', 0.45), ('them', 0.7), ('me', 0.5), ('them', 0.4), ('me', 0.6)],   # 气泡：哪边、占屏宽几成
          'me': (58, 190, 120), 'them': (255, 255, 255),     # 右边自己发的绿气泡 / 左边对方的白气泡，都不写字
          'input': (205, 212, 220),                          # 底部输入栏
          'glass': 0.28, 'glass_w': 0.22,                    # 玻璃反光：一道斜白条的不透明度、宽占屏高几成
          'cam': 0.1}                                        # 前摄小圆点半径占机身宽几成（在顶栏那头的黑边上）


def screen_tex(w, h):
    """w×h（宽 < 高）的竖屏聊天界面：顶栏在上、气泡上下排、输入栏在下。没有字、没有真实 App 的 logo，
    远看读出"在聊天"就够。手机是被横着拽的，调用方把它整张转 90° 贴上去 —— 用户原话「聊天软件的方向在屏幕里
    应该是竖的，现在是横的」：按横屏画（顶栏在长边、气泡横排）真实手机不会这样显示。"""
    S = SCREEN
    im = Image.new('RGB', (w, h), S['bg'])
    g = ImageDraw.Draw(im)
    bh = round(h * S['bar_h'])
    g.rectangle((0, 0, w, bh), fill=S['bar'])
    r = min(bh, w) * 0.28
    g.ellipse((w * 0.18 - r, bh / 2 - r, w * 0.18 + r, bh / 2 + r), fill=(255, 255, 255))          # 头像
    g.rounded_rectangle((w * 0.18 + r * 1.6, bh / 2 - r * 0.4, w * 0.62, bh / 2 + r * 0.4), r * 0.4, fill=(255, 255, 255))  # 名字条
    ih = round(h * S['input_h'])
    g.rectangle((0, h - ih, w, h), fill=S['input'])
    g.rounded_rectangle((w * 0.1, h - ih * 0.75, w * 0.9, h - ih * 0.25), ih * 0.25, fill=(250, 252, 255))
    rows = S['rows']                                          # 气泡左白（对方）右绿（自己）上下排，占满中段：两头被拳头盖住
    lh = (h - bh - ih) / len(rows)
    for k, (side, ln) in enumerate(rows):
        y = bh + lh * (k + 0.2)
        x0 = w * 0.08 if side == 'them' else w * (0.92 - ln)
        g.rounded_rectangle((x0, y, x0 + w * ln, y + lh * 0.6), min(lh, w) * 0.3, fill=S[side])
    im = im.convert('RGBA')
    gl = Image.new('RGBA', (w, h)); a = round(255 * S['glass'])   # 玻璃反光：从左上往右下斜的一道白条（屏上叠一层，不改界面）
    t = h * S['glass_w']
    ImageDraw.Draw(gl).polygon([(0, h * 0.18), (0, h * 0.18 + t), (w, h * 0.18 + t - w * 0.9), (w, h * 0.18 - w * 0.9)], fill=(255, 255, 255, a))
    im.alpha_composite(gl)
    m = Image.new('L', (w, h)); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), w * S['round'], fill=255)
    im.putalpha(m)                                            # 屏幕圆角：四角露出机身的黑边
    return im


def light_phone(full, core):
    """full：已经贴上放大机身的整张 RGBA（PIL）；core：放大后的机身（bool）。
    机身上贴亮屏、黑边框上点前摄，返回 float 数组；手由调用方再盖回去。"""
    ys, xs = np.nonzero(core)
    pts = np.stack([xs, ys], 1).astype(np.float32); c = pts.mean(0)
    _, vec = np.linalg.eigh(np.cov((pts - c).T))
    u = vec[:, 1] * (1 if vec[0, 1] >= 0 else -1)            # 长轴，朝右
    proj = (pts - c) @ np.stack([u, [-u[1], u[0]]], 1)
    L, Wd = proj[:, 0].max() - proj[:, 0].min(), proj[:, 1].max() - proj[:, 1].min()
    base = full.copy()
    # 亮屏：沿机身长轴贴，斜拿的跟着斜
    SS = 4                                                   # 4 倍大画、4 倍大转，再缩回来：原尺寸直接转，斜拿的边和气泡锯齿成一排点
    tex = screen_tex(round(Wd * SCREEN['h']) * SS, round(L * SCREEN['w']) * SS)
    # 竖屏界面转成横拿：逆时针 90°，顶栏落到左边女生那头；再跟着机身斜
    tex = tex.rotate(90 - np.degrees(np.arctan2(u[1], u[0])), resample=Image.BICUBIC, expand=True)
    tex = tex.resize((round(tex.width / SS), round(tex.height / SS)), Image.LANCZOS)
    base.alpha_composite(tex, (round(c[0] - tex.width / 2), round(c[1] - tex.height / 2)))
    # 前摄：顶栏那头（竖屏的上方 = 转过来的左边，−u）黑边框正中一个深灰小圆点
    k = c - u * L * (0.5 - (1 - SCREEN['w']) / 4); r = Wd * SCREEN['cam'] / 2
    ImageDraw.Draw(base).ellipse((k[0] - r, k[1] - r, k[0] + r, k[1] + r), fill=(70, 78, 92, 255))
    return np.array(base).astype(np.float32)


# 量人有多大的尺子：赢的那一方的头，框是对着 pose_n0.webp 量的（换 n0 必须重量）。
# 头的大小不随姿势变；身高会被前倾压矮、睡衣面积会被两腿互相遮挡带偏（v13 吃过亏）
HEAD_AT = 0.66    # 下面这两个框是 SCALE=0.66 时量的，SCALE 变了按比例换算
# 2026-09-26 手臂缩短（v14/arms）后 n0 里女生右移 105、男生左移 30（原图像素），裁切左沿跟着女生走，
# 男生的头在裁切图里就左移了 135 × 0.66 = 89
HEAD = {'a': (115, 40, 205, 135), 'b': (651, 10, 771, 120)}


def _gray(im):
    c = Image.new('RGBA', im.size, (255, 255, 255, 255)); c.alpha_composite(im.convert('RGBA'))
    return np.array(c.convert('L')).astype(np.float32)


def head_find(ref, im, side):
    """在 im 里找 ref（僵持）里那张脸：多尺度归一化互相关，返回 (尺度, 脸中心 x, 脸中心 y, 半径)，
    坐标是 im 的像素。方差太小的窗口（白底）不算，否则分母趋零、分数爆到几十。
    side = 'a' 女生（左半边找）/ 'b' 男生（右半边找）。"""
    b = [round(v * SCALE / HEAD_AT) for v in HEAD[side]]
    T = _gray(ref)[b[1]:b[3], b[0]:b[2]]
    G = _gray(im); w = G.shape[1]
    off = 0 if side == 'a' else w // 2 - 60
    G = G[:, :w // 2 + 60] if side == 'a' else G[:, off:]
    best = (-1, 1.0, 0, 0, 0, 0)
    for k in np.arange(0.80, 1.12, 0.01):
        t = np.array(Image.fromarray(T).resize((round(T.shape[1] * k), round(T.shape[0] * k)), Image.LANCZOS))
        t = t - t.mean(); tt = (t ** 2).sum(); ones = np.ones_like(t)
        num = fftconvolve(G, t[::-1, ::-1], 'valid')
        s1 = fftconvolve(G, ones, 'valid'); s2 = fftconvolve(G ** 2, ones, 'valid')
        var = s2 - s1 * s1 / t.size
        r = np.where(var > 0.3 * tt, num / np.sqrt(np.maximum(var, 1) * tt), 0)
        i = np.unravel_index(r.argmax(), r.shape)
        if r[i] > best[0]:
            best = (r[i], k, i[1], i[0], t.shape[1], t.shape[0])
    _, k, x, y, tw, th = best
    return k, off + x + tw / 2, y + th / 2, tw / 2


def head_scale(ref, im, side):
    """im 里赢方的头是 ref（僵持）里的几倍。"""
    return head_find(ref, im, side)[0]


HIP_ROWS = 9      # 男生短裤上取几行做口红的落点


def hip_find(im):
    """男生的腰和大腿在 im 里的位置：他的藏青短裤（口红朝这里飞、粉点留在这里）。
    藏青是整张图里唯一偏蓝的暗色块（女生粉、衬衫浅蓝、头发黑），按色相直接抠，不用模板。
    返回 {'box': [x0, y0, x1, y1], 'pts': [[左沿, y, 右沿], ...]}：box 取 2%~98% 分位（去掉头发里
    零星的蓝黑像素），pts 是在短裤上下 10%~90% 之间均匀取 HIP_ROWS 行、每行**最靠左那一段**
    藏青（宽于 12 像素）的左右沿 —— 口红从左边飞来，先碰到的是这一段的左沿。"""
    a = np.array(im.convert('RGBA')).astype(int)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    nav = (al > 200) & (b > r + 25) & (b > g + 10) & (r < 110) & (b < 170)
    nav[:, :a.shape[1] // 3] = False
    ys, xs = np.nonzero(nav)
    x0, x1 = np.percentile(xs, [2, 98]); y0, y1 = np.percentile(ys, [2, 98])
    pts = []
    for y in np.linspace(y0 + 0.1 * (y1 - y0), y0 + 0.9 * (y1 - y0), HIP_ROWS).round().astype(int):
        row = nav[y]; x = 0
        while x < len(row):
            if row[x]:
                e = x
                while e < len(row) and row[e]: e += 1
                if e - x > 12:
                    pts.append([x, int(y), e - 1]); break
                x = e
            x += 1
    return {'box': [round(float(v), 1) for v in (x0, y0, x1, y1)], 'pts': pts}


# 被拉倒各档赢方的身体比僵持（n0）小多少：按 SCALE 出图时量的，身高（头顶到地）与衣服面积两种量法
# 取中间（前倾角度不同，单用身高会偏；衣服被手臂/头发挡住，单用面积会偏）。换了关键姿势必须重量。
BODY = {'aK': 0.920, 'aF': 0.756, 'aL': 0.797, 'bK': 0.909, 'bF': 0.855, 'bL': 0.827}

# 过渡帧：档名 → (从哪一档来, 贴回 base 的分界列，原图坐标 ≈ base 里手机中心)。见 main() 里「过渡帧」一段。
# a 档赢方（女生）在左：分界以左贴回；b 档赢方（男生）在右：分界以右贴回
TWEEN = {'aK': ('n0', 690), 'aF': ('aK', 580), 'aL': ('aF', 595),
         'bK': ('n0', 880), 'bF': ('bK', 990), 'bL': ('bF', 990)}
TWEEN_FEATHER = 20

EDGE_STEP = 6    # 轮廓按行采样的间距（引擎像素）
# 贴地段（2026-09-30 用户：「发生位移的帧……需要在地上留下痕迹（被拉的人留下的）」）：只量被拉倒的那个人
# （各档输方蒙版 tween/<档>/mask.png 的透明区 —— 关键帧、步态帧、过渡帧都是同一张原图的坐标，蒙版通用；
# 不按手机左右切：男生跪档的前脚会伸到手机左边）。取他自己最低的不透明像素，每列最低点离它不超过 GROUND_TOL
# 就算这一列贴着地（拖鞋底、膝盖、趴着的身子），相邻列连成段；同时给出这个人最低点离脚底线几像素（float）。
# 侧视角里画得高一点 = 离镜头远一点，所以引擎把痕印在 脚底线 − float 那条线上；float 太大（腾空的帧）引擎不印。
# 引擎拖动时把这些段按世界坐标印在地板上（main.js Scuff）。
GROUND_TOL = 8     # 离这个人最低点几像素内算贴地（引擎像素）；鞋底描边、脚尖翘起约 3~6
GROUND_GAP = 4     # 两段之间空不到几列就连成一段
GROUND_MIN = 6     # 比这窄的段不要（发梢、鞋尖一个角）


def ground_segs(solid, ay, ax):
    """solid：贴图里输方的不透明掩码；返回 (贴地段 [[x0, x1], ...] 相对锚点 ax, 这个人最低点离脚底线几像素)。"""
    h, w = solid.shape
    low = np.where(solid.any(0), h - 1 - np.argmax(solid[::-1], 0), -10 ** 6)
    bottom = int(low.max())
    on = low >= bottom - GROUND_TOL
    segs, x = [], 0
    while x < w:
        if on[x]:
            e = x
            while e < w and on[e:e + GROUND_GAP + 1].any():
                e += 1
            while not on[e - 1]:
                e -= 1
            if e - x >= GROUND_MIN:
                segs.append([round(x - ax, 1), round(e - ax, 1)])
            x = e
        x += 1
    return segs, int(ay - bottom)


def edges(solid, phone):
    """礼物打到哪儿才算"碰到人"：每 EDGE_STEP 行量一次两个人**朝着对方那一侧**的轮廓。
    a = 女生（左）最靠右的那个像素，灭迹党（从右边飞来）的礼物打在这里；
    b = 男生（右）最靠左的那个像素，查岗党的礼物打在这里。
    这一行没有那个人（头顶上方、趴下后的上半截）记 -1。飞来的礼物会先路过自己那一方
    的人，那不算碰到。

    分人不能按手机那条竖线一刀切：男生跪/扑的时候前脚会伸过手机线，切下来就算成了女生。
    两个人只在手机和四只手那里连着 —— 把手机周围一块挖掉，剩下的连通块里最大的两块就是
    两个人；零碎的（发梢、被挖断的手指）按离谁近归谁；挖掉的那一块里仍按手机中线分。
    连续不到 3 个像素的零星点（抗锯齿毛边）不算，不然礼物会在头发梢上空爆。

    top = 女生每 EDGE_STEP 列最高的那个像素（没有记 -1）：她倒地以后哥们的水从上往下浇在
    她的腿、背上，碰的是上沿不是前沿。topB = 男生的：榴莲鞋雨从天上掉，随机砸在他身上任意一处
    （站着是头、肩、胳膊，倒地是背、屁股、腿）。"""
    h, w = solid.shape
    px, py = phone
    cut = solid.copy()
    k = SCALE / HEAD_AT                        # 挖的这块是在 0.66 下定的：±90 × ±70
    bx0, bx1 = int(px - 90 * k), int(px + 90 * k)
    by0, by1 = int(py - 70 * k), int(py + 70 * k)
    cut[max(0, by0):by1, max(0, bx0):bx1] = False
    lab, n = ndimage.label(cut)
    sizes = ndimage.sum(cut, lab, range(1, n + 1))
    big = np.argsort(sizes)[::-1][:2] + 1
    cxs = ndimage.center_of_mass(cut, lab, big)
    girl, boy = (big[0], big[1]) if cxs[0][1] < cxs[1][1] else (big[1], big[0])
    cg, cb = ndimage.center_of_mass(cut, lab, [girl, boy])
    side = np.zeros(n + 1, np.int8)           # 1 = 女生，2 = 男生
    for k, c in enumerate(ndimage.center_of_mass(cut, lab, range(1, n + 1)), 1):
        side[k] = 1 if abs(c[1] - cg[1]) < abs(c[1] - cb[1]) else 2
    who = side[lab]
    xs = np.arange(w)[None, :]
    box = solid & ~cut
    who[box & (xs < px)] = 1
    who[box & (xs >= px)] = 2

    def run3(m):
        return m & np.roll(m, 1, 1) & np.roll(m, 2, 1)
    ga, bb = run3(who == 1), run3(np.roll(who == 2, -2, 1))
    a, b = [], []
    for y in range(0, h, EDGE_STEP):
        la, rb = np.nonzero(ga[y])[0], np.nonzero(bb[y])[0]
        a.append(int(la.max()) if len(la) else -1)
        b.append(int(rb.min()) if len(rb) else -1)
    def tops(m):
        out = []
        for x in range(0, w, EDGE_STEP):
            ys = np.nonzero(m[:, x])[0]
            out.append(int(ys.min()) if len(ys) else -1)
        return out
    return {'step': EDGE_STEP, 'a': a, 'b': b, 'top': tops(ga), 'topB': tops(run3(who == 2))}


# 被拖的人挣扎（2026-09-30 用户：「当前帧数还是太少 动作很僵硬」）：步态 8 格原来只重画了赢方的腿，被拖的那个人
# 8 格一模一样，被拖着走一路纹丝不动。struggle/<档>/ 下 s1~s3.png **只重画输方腰线以下**
# （小腿、膝盖、拖鞋在地上蹭、乱蹬；头、手臂、上身一个像素不动，免得循环起来一跳一跳）。
# 10-05 起重画：原图抹掉腿、贴上旧帧的拖鞋落点，[引导图, 原图] 两图生图（struggle/guide.py、prompt.py），挑好的由 struggle/comp.py 贴回原图。
# 构建时第 f 格步态取 s[f % 4]（0 = 原图的腿）：被拖一步，腿跟着蹬一下，停下不拖就不动（步态只随位移走）。
# 取用区域 = 输方蒙版（tween/<档>/mask.png）∩ 不在赢方步态蒙版里（外扩 STRUGGLE_KEEP，
# 赢方迈步的那只脚会伸进这一侧，挨着的地方贴生图会叠出两只拖鞋）∩ 不碰原图腿区 STRUGGLE_HIP 以外的身体（struggle_region）；接缝在 struggle/comp.py 里按 seam.py 对齐。
# 腿在哪：(这一行以下, 这一列起, 到这一列)，原图坐标。跪 / 扑倒按短裤下沿横切；趴着的两档腿在身后水平伸出，按短裤后沿竖切
STRUGGLE_HIP = {'aK': (745, 0, 1536), 'aF': (640, 0, 1536), 'aL': (0, 1190, 1536),
                'bK': (700, 0, 1536), 'bF': (700, 0, 1536), 'bL': (0, 0, 390)}
STRUGGLE_KEEP = 25
STRUGGLE_GUARD = 6


# 后退步态（2026-10-01 用户：「男女主后退的动作还是不对，帧数不够、距离与动作不匹配导致滑步。而且没有左右腿交替向后，看着特别假」）。
# 旧八格 gait/<档>/f1~f7 是让模型自己摆腿：前后两半是同一组姿势（f1 = f5 逐字节相同），同一条腿一直在往后踢；
# 站地那只脚每格的位置也是随机的，和背景卷过的距离对不上。新版 walk/<档>/（walk/guide.py）先算好一个循环 N 格（plan.json）里
# 两只拖鞋该在哪，各自一直在自己那条地面线上（近脚低、远脚高）—— 把拖鞋贴在这些位置上再让模型只画腿，挑拖鞋落位最准的候选（walk/score.py）。
# 10-05 起是拖步：两脚从不交叉，前半步后脚站地、前脚贴地往后拖，后半步前脚站地、后脚往后退（交叉走那几格腿必畸形，见 walk/guide.py）。
# 播哪一格按**量出来的**站地脚位置定（walk_load 的 at），不按格号平分：某一格站地脚比计划偏了几像素，就晚几像素再换到它。
WALK_SLIPPER_H = 80     # 拖鞋高度上限（原图像素）：地面带从抬脚最高处再往上留这么多


def slipper_blobs(a, mask, girl, band):
    """赢方拖鞋色块 [(中心 x, 鞋底 y)]：女生白兔拖鞋 = 亮且不偏色，男生黑猫拖鞋 = 暗。只在蒙版放开区的地面带 band = (y0, y1) 里找。
    地面带按 plan.json 的地面线定，不按蒙版底边往上数：蒙版一直放到图底，扑倒档拖鞋在 786~807 行，"蒙版底往上 200 行"一只都框不到（10-02 构建报错）"""
    r, g, b = (a[..., k].astype(int) for k in range(3))
    s = ((np.minimum(np.minimum(r, g), b) > 200) & (a.max(2).astype(int) - a.min(2) < 40)) if girl else (a.max(2) < 70)
    s &= mask
    s[:band[0]] = False
    s[band[1]:] = False
    lab, n = ndimage.label(ndimage.binary_fill_holes(ndimage.binary_opening(s, np.ones((5, 5)))))
    out = []
    for k in range(1, n + 1):
        yy, xx = np.nonzero(lab == k)
        if len(xx) >= 800:
            out.append((float(xx.mean()), int(yy.max())))
    return out


def walk_load(name):
    """walk/<档>/ → (帧路径 w01..w15, at, 一个循环人退多远 原图像素)。拖步（walk/guide.py）：前半步 0 号脚（后脚）站地、
    后半步 1 号脚（前脚）站地，站地脚相对身子往前挪多少，人就往后退多少。at[i] = 第 i 格（0 = base）在一个循环里的位置（0~1）
    = 到这一格为止站地脚累计挪了多少 / 一整圈挪了多少。全按**量出来的**拖鞋位置算：模型把拖鞋画得比计划近或远，
    这一圈就短一点或长一点，脚照样钉在地上；第 N/2 格换脚时两边量的是同一张图，接得上。"""
    d = os.path.join(HERE, 'walk', name)
    plan = json.load(open(os.path.join(d, 'plan.json')))
    N = plan['N']           # 一个循环几格（拖步 8 格：步子小，每格脚挪的距离和以前交叉走 16 格差不多）
    mask = np.array(Image.open(os.path.join(HERE, 'gait', name, 'mask.png')))[..., 3] == 0
    paths = [os.path.join(HERE, 'gait', name, 'base.png')] + [os.path.join(d, f'w{i:02d}.png') for i in range(1, N)]
    tgt = {0: {'0': dict(x=plan['back'], line=plan['lines'][0], lift=0), '1': dict(x=plan['front'], line=plan['lines'][1], lift=0)}}
    tgt.update({f['i']: f['feet'] for f in plan['frames']})
    h = N // 2
    band = (int(min(plan['lines']) - plan['lift'] - WALK_SLIPPER_H), int(max(plan['lines']) + 20))   # 抬到最高的拖鞋顶 ~ 最低鞋底
    def foot_x(i, foot):
        t = tgt[i][foot]
        blobs = slipper_blobs(np.array(Image.open(paths[i % N]).convert('RGB')), mask, name[0] == 'a', band)
        return min(blobs, key=lambda q: abs(q[0] - t['x']) + abs(q[1] - t['line']))[0]
    # 前半步量 0 号脚（第 0~h 格），后半步量 1 号脚（第 h~N 格，第 N 格 = 第 0 格）
    first = [abs(foot_x(i, '0') - foot_x(0, '0')) for i in range(h + 1)]
    second = [abs(foot_x(i % N, '1') - foot_x(h, '1')) for i in range(h, N + 1)]
    C = first[-1] + second[-1]
    at = first[:h] + [first[-1] + v for v in second[:-1]]
    return paths[1:], [round(v / C, 4) for v in at], C


def struggle_region(name, gait_mask):
    """挣扎帧的取用区域（布尔 H×W）：输方蒙版 ∩ 不在赢方步态蒙版里 ∩ 不碰原图腿区以外的身体。struggle/comp.py 也用它贴接缝"""
    lose = np.array(Image.open(LOSE(name)).getchannel('A')) < 128
    keep = ndimage.binary_dilation(np.array(Image.open(gait_mask).getchannel('A')) < 128, iterations=STRUGGLE_KEEP)
    y0, x0, x1 = STRUGGLE_HIP[name]
    legs = np.zeros_like(lose)
    legs[y0:, x0:x1] = True
    # 腿区以外只护住原图里有人的像素（上身、头发，外扩 STRUGGLE_GUARD）：踢起来的小腿会高过腰线伸进空白处，
    # 按腰线一刀切的话那截腿被切在羽化带里、跟原图的品红底一混，边上一道粉边（2026-09-30 男跪档截图）
    base = np.array(Image.open(os.path.join(HERE, 'struggle', name, 'base.png')).convert('RGB')).astype(np.int16)
    guard = ndimage.binary_dilation((keyed(base) < 60) & ~legs, iterations=STRUGGLE_GUARD)
    return lose & ~keep & ~guard


def struggle_load(name, gait_mask):
    """返回 ([s1, s2, s3 的 RGB int16 数组], 取用权重 H×W×1)；这一档没做挣扎帧返回 ([], None)。
    s<k>.png 是 struggle/comp.py 已经按 seam.py 贴回原图的整张（区域外 = 原图，接缝处已对齐、渐变），
    所以这里按区域硬取就行，不再羽化（10-05 之前在这里往里羽化 8 像素，生图的短裤边和原图错开一截照样看得见）"""
    d = os.path.join(HERE, 'struggle', name)
    fs = sorted([f for f in os.listdir(d) if f[0] == 's' and f[1:-4].isdigit()], key=lambda f: int(f[1:-4])) if os.path.isdir(d) else []
    if not fs:
        return [], None
    r = struggle_region(name, gait_mask)
    return [np.array(Image.open(os.path.join(d, f)).convert('RGB')).astype(np.int16) for f in fs], r[..., None].astype(np.float32)


LOSE = lambda name: os.path.join(HERE, 'tween', name, 'mask.png')     # 各档输方蒙版（贴地段用，见 ground_segs）


def build_pose(name, path, feet_align=False, anchor=None, scale=SCALE, lose=None):
    """path 可以是文件，也可以是处理过的 RGB 数组（步态帧踩地之后，见 plant_feet）。
    anchor：直接指定锚点在**原图**里的像素坐标 (x, 脚底 y)，不按本张自己算。
    步态帧用：它们只重画了腿，其余像素跟原姿势一模一样，锚点必须跟原姿势同一个点，
    按各自外框算的话腿一抬外框就变，整个人会跟着横跳。"""
    rgb, al = cutout(path)
    ph = find_phone(rgb, al)
    if ph:
        rgb, al = enlarge_phone(rgb, al, ph)
    rgb = edge_extend(rgb, al)
    im = Image.fromarray(np.concatenate([rgb, al[..., None] * 255], -1).astype(np.uint8), 'RGBA')
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    a = np.array(im)[..., 3].astype(np.float32) / 255
    ys, xs = np.where(a > 0.06)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    foot = y1
    if anchor:
        cx, foot = anchor[0] * scale, anchor[1] * scale
    elif feet_align:
        band = a[foot - int((foot - y0) * 0.08):foot]
        cx = (band.sum(0) * np.arange(a.shape[1])).sum() / band.sum()
    else:
        cx = (x0 + x1) / 2     # 拖地这类宽姿势比屏幕还宽，按质心对齐会让一侧整截出画
    im = im.crop((x0, y0, x1, y1))
    im.save(os.path.join(OUT, f'pose_{name}.webp'), quality=90, method=6)
    if lose:    # 被拉倒各档：输方的贴地段（拖痕），lose = 输方蒙版路径（透明 = 输方）
        # 输方蒙版扣掉赢方步态蒙版：a 档输方蒙版是 x≥800 一整块，女生前脚的拖鞋尖也在里面，会在男生前面印出一截痕
        lo = np.array(Image.open(lose).getchannel('A')) < 128
        gm = os.path.join(HERE, 'gait', name[:2], 'mask.png')
        if os.path.exists(gm):
            lo &= ~(np.array(Image.open(gm).getchannel('A')) < 128)
        who = Image.fromarray((lo * 255).astype(np.uint8))
        who = np.array(who.resize((round(who.width * scale), round(who.height * scale)), Image.NEAREST).crop((x0, y0, x1, y1))) > 0
        drag = ground_segs((a[y0:y1, x0:x1] > 0.5) & who, foot - y0, cx - x0)
    meta = {'w': int(x1 - x0), 'h': int(y1 - y0),
            'ax': round(float(cx - x0), 1), 'ay': int(foot - y0)}
    if lose:
        meta['drag'], meta['float'] = drag
    if ph:
        meta['phone'] = [round(ph[0] * scale - x0, 1), round(ph[1] * scale - y0, 1)]
        meta['edge'] = edges(np.array(im)[..., 3] > 127, meta['phone'])
    return meta, im, (cx / scale, foot / scale)


# 房间接缝的过渡段（2026-09-27 用户：「卧室与两个房间连接之处，过度的特别不自然」）。
# 三间房是分开生成的三张图，只"找门切开"硬拼：一条竖线从天花板切到画面最底、地板光影在同一列突变、
# 门只剩半扇、门洞里透出的家具跟门外紧挨着的那套重复。每处接缝以接缝为中心取 960 宽（9:16）一段，
# 中间一条竖带局部重绘成：有厚度的隔墙墙垛 + 左右门框都在的整扇门（门洞里只有暗的远景）+ 地板上一条
# 门槛压条，两边地板各自的光影在压条处收住（bg/seam/：seam*_src 拼好的原样、seam*_mask 蒙版、seam*_gen 生成图）。
# 只取竖带 [lo, hi]、两头 SEAM_FEATHER 渐变回原图，竖带外一个像素不动；房间宽度不变，world.json 的
# rooms / center、距离条、判胜都不受影响。
# seam0 右沿放宽到 770：生成图把梳妆台往右挪让出门的位置，在 680 就收会叠出两个半透明的梳妆台和门框；
# 从 740 起生成图和原图逐列一致（平均差 < 5）。
SEAM_W = 960
SEAM_BAND = [(280, 770), (280, 680)]     # 每处接缝取生成图的哪一段（过渡段内的 x）
SEAM_FEATHER = 25


def seam_bridge(imgs):
    """imgs：缩放到 H 高的三间房（原地改）。每处接缝把过渡段的竖带混进左右两张的边上。"""
    half = SEAM_W // 2
    for k, (lo, hi) in enumerate(SEAM_BAND):
        a, b = imgs[k], imgs[k + 1]
        cv = Image.new('RGB', (SEAM_W, H))
        cv.paste(a.crop((a.width - half, 0, a.width, H)), (0, 0)); cv.paste(b.crop((0, 0, half, H)), (half, 0))
        gen = Image.open(os.path.join(HERE, 'bg', 'seam', f'seam{k}_gen.png')).convert('RGB').resize((SEAM_W, H), Image.LANCZOS)
        x = np.arange(SEAM_W)
        w = np.clip(np.minimum(x - lo, hi - x) / SEAM_FEATHER, 0, 1)[None, :, None]
        out = Image.fromarray((np.array(cv, np.float32) * (1 - w) + np.array(gen, np.float32) * w).clip(0, 255).astype(np.uint8))
        a.paste(out.crop((0, 0, half, H)), (a.width - half, 0)); b.paste(out.crop((half, 0, SEAM_W, H)), (0, 0))


# 终点（2026-09-27 用户：「终点的概念是对的，但物件不符合整个美术画风，可以换个更搭场景的」）：
# 判胜是被拖到离客厅正中 ±GOAL_M 米（main.js NUM.END），世界 x = center ∓ GOAL_M × PX_PER_M（main.js P.pxPerM）。
# 第一版是引擎叠的方格带 + 光幕 + 字，跟手绘房间两层皮；改成把房间里本来就会有的东西**画进背景**：
#   卧室（女生终点）一条粉色长毛地毯、两边缠星星串灯（跟墙上的串灯一套）；电竞房（男生终点）一条青→品紫的 RGB 发光地垫。
# bg/goal/goal{k}_src.png 是从房间图上以终点为中心裁的 GOAL_W 宽，goal{k}_mask.png 透明的梯形（墙根 → 画面下沿，带透视）
# 交给局部重绘，goal{k}_gen.png 是挑中的生成图。只把梯形里（外沿羽化 GOAL_FEATHER）混回房间，梯形外一个像素不动。
GOAL_M = 30
PX_PER_M = 82 * 2 / 3
GOAL_W = 960
GOAL_TRAP = [(110, 860), (190, H)]        # 梯形：墙根处半宽、y；画面下沿处半宽、y（跟蒙版一致）
GOAL_FEATHER = 10


def goal_paint(imgs, center):
    """imgs：缩放到 H 高的三间房（原地改）。两处终点把生成图的梯形混进所在的房间。"""
    starts = np.cumsum([0] + [im.width for im in imgs])
    for k, d in enumerate((-1, +1)):
        gx = center + d * GOAL_M * PX_PER_M
        ri = int(np.searchsorted(starts, gx, side='right') - 1)
        im, x0 = imgs[ri], round(gx - starts[ri] - GOAL_W / 2)
        gen = Image.open(os.path.join(HERE, 'bg', 'goal', f'goal{k}_gen.png')).convert('RGB').resize((GOAL_W, H), Image.LANCZOS)
        (w0, y0), (w1, y1) = GOAL_TRAP
        m = Image.new('L', (GOAL_W, H)); c = GOAL_W / 2
        ImageDraw.Draw(m).polygon([(c - w0, y0), (c + w0, y0), (c + w1, y1), (c - w1, y1)], fill=255)
        w = ndimage.gaussian_filter(np.array(m, np.float32) / 255, GOAL_FEATHER / 2)[..., None]
        cv = im.crop((x0, 0, x0 + GOAL_W, H))
        out = (np.array(cv, np.float32) * (1 - w) + np.array(gen, np.float32) * w).clip(0, 255).astype(np.uint8)
        im.paste(Image.fromarray(out), (x0, 0))


def build_rooms():
    """三间房 → room{i}.webp（含接缝过渡段、终点地毯 / 地垫），返回 (每间宽, 客厅正中的世界 x)。"""
    bg = os.path.join(HERE, 'bg')
    G = Image.open(f'{bg}/girlroom_ext.png').convert('RGB')
    L = Image.open(f'{bg}/living_ext.png').convert('RGB')
    B = Image.open(f'{bg}/boyroom_ext.png').convert('RGB')
    # *_ext.png = 原图上面补画了 424 行墙面（到天花板顶角线）、下面补了 49 行地板（bg/ext/ 里是
    # 补画用的画布、蒙版和生成图）。镜头拉远 2/3 以后，原图只占屏幕 889 高，地面线仍在 GROUND，
    # 上面空出来的那一截要有东西。原图像素原样保留，补画部分做过顶角线对齐、接缝调色、门洞上方
    # 加了墙角线（两间房的墙色在那儿交界）。宽度没变，所以 CUT_* 仍按原图量
    s = H / G.height
    parts = [G, L.crop((CUT_LIVING_L, 0, L.width, L.height)), B.crop((CUT_BOY_L, 0, B.width, B.height))]
    imgs = [p.resize((round(p.width * s), H), Image.LANCZOS) for p in parts]
    seam_bridge(imgs)
    # 客厅中点 = 沙发正中 = 0 米。按原图客厅中线换算到拼接后的世界坐标
    center = imgs[0].width + round((L.width / 2 - CUT_LIVING_L) * s)
    goal_paint(imgs, center)
    rooms = []
    for i, r in enumerate(imgs):
        r.save(os.path.join(OUT, f'room{i}.webp'), quality=86, method=6)
        rooms.append(r.width)
    return rooms, center


def main():
    os.makedirs(OUT, exist_ok=True)
    rooms, center = build_rooms()

    poses = {}
    anchors = {}      # 每张关键姿势的锚点（原图坐标），步态帧沿用
    scales = {}       # 被拉倒各档按头补过的缩放，步态帧沿用
    sheet = []
    for name, f, feet in [
        ('n0', 'loop/n0.png', True), ('nL1', 'loop/nL1.png', True), ('nL2', 'loop/nL2.png', True),
        ('nR1', 'loop/nR1.png', True), ('nR2', 'loop/nR2.png', True),
        # 被拉倒三档：K 跪着 / F 往前扑倒 / L 趴在地上。a = 查岗党(女)占优、男方倒；b 反之。
        # 两人朝向永远不变：头朝对方、腿在身后（见 chashouji-art skill 的朝向铁律）
        ('aK', 'pose/21_女优_男跪.png', False), ('aF', 'pose/22_女优_男扑倒.png', False),
        ('aL', 'pose/23_女优_男趴.png', False),
        ('bK', 'pose/24_男优_女跪.png', False), ('bF', 'pose/25_男优_女扑倒.png', False),
        ('bL', 'pose/26_男优_女趴.png', False),
    ]:
        meta, im, raw = build_pose(name, os.path.join(HERE, f), feet)
        if name == 'n0':
            ref = im
        elif name[0] in 'ab':
            # 被拉倒三档是各自生成的，扑倒/趴那几张人整个被画小了（赢方身体只有僵持的 0.76~0.92）。
            # 礼物一砸动作掉进这几档、又因为回差要停好一阵，看着就是"人突然变小很久"。
            # 按**身体**把整张补回来（输的那个人一起放，他们是同一张画），不按头：这几张生图把头
            # 画大了、身体画小了，按头对齐（2026-09-26 之前）头是一样大了，身子还是小一圈，用户原话
            # "两个人都变得很小"。放大以后偏大的头由 v14/arms/heads.py 在原图里单独收回去。
            k = BODY[name]
            scales[name] = SCALE / k
            print(name, 'body %.3f  head %.2f' % (k, head_scale(ref, im, name[0])))
            meta, im, raw = build_pose(name, os.path.join(HERE, f), feet, scale=scales[name], lose=LOSE(name))
        # 两张脸在贴图里的位置（香蕉朝女生的脸飞、脸上的白点跟着脸走）：[x, y, 半径]
        ref_ = im if name == 'n0' else ref
        meta['face'] = {s_: [round(v, 1) for v in head_find(ref_, im, s_)[1:]] for s_ in 'ab'}
        meta['hip'] = hip_find(im)
        poses[name] = meta
        sheet.append((name, meta, im))
        print(name, meta)
        anchors[name] = raw

    # 步态循环：gait/<姿势>/ 下 base.png（= 该姿势原图，第 0 格）+ mask.png + f1~f7，八格一个循环（两步）：
    #   0 双脚着地 → 1 前脚跟离地 → 2 抬起的脚从站地那条腿旁边穿过 → 3 往身后伸、快落地
    #   → 4 两腿换位双脚着地 → 5~7 同 1~3 换另一条腿
    # 站地的那只脚从身后一路移到身前、抬起的那只从身前摆到身后，每格都挪一点 —— 四格版每格
    # 脚都要跳一大截，用户原话"后腿非常不连贯"。f* 都是拿 base 做蒙版局部重绘、**只重画赢的
    # 那一方的腿**得来的，其余像素原样，所以锚点直接沿用 base 那张 —— 各算各的外框会让上半身跟着腿横跳。
    gaits = {}
    for name, base_raw in anchors.items():
        d = os.path.join(HERE, 'gait', name)
        if not os.path.isdir(d):
            continue
        k = scales.get(name, SCALE)
        struggle, sw = struggle_load(name, os.path.join(d, 'mask.png'))
        frames = [name]
        wp = os.path.join(HERE, 'walk', name, 'plan.json')
        walk = os.path.isfile(wp) and all(os.path.isfile(os.path.join(HERE, 'walk', name, f'w{i:02d}.png'))
                                          for i in range(1, json.load(open(wp))['N']))   # 一整圈都挑好了才换新版
        if walk:
            # 新版后退步态：拖鞋是按计划贴好的、鞋底就在原地面线上，不用 plant_feet 拉腿（后半步站地的是远脚，
            # 最低点本来就该比近脚高，拉到同一条线反而错）
            srcs, at, C = walk_load(name)
            srcs = [np.array(Image.open(q).convert('RGB')).astype(np.int16) for q in srcs]
        else:
            srcs = [plant_feet(os.path.join(d, f'f{f}.png'), os.path.join(d, 'base.png'), os.path.join(d, 'mask.png')) for f in range(1, 8)]
        for f, img in enumerate(srcs, 1):
            g = f'{name}_g{f}'
            if struggle:
                j = f % (len(struggle) + 1)          # 格号是 (挣扎帧数+1) 的倍数的用原图的腿，其余轮着换挣扎帧
                if j:
                    img = np.round(img * (1 - sw) + struggle[j - 1] * sw).astype(np.int16)
            meta, im, _ = build_pose(g, img, anchor=base_raw, scale=k, lose=LOSE(name))
            meta['face'] = poses[name]['face']      # 只重画了腿，脸和 base 同一处
            meta['hip'] = hip_find(im)              # 腿换了，短裤跟着变，每格重量
            poses[g] = meta
            sheet.append((g, meta, im))
            frames.append(g)
        if walk:
            gaits[name] = {'frames': frames, 'cycle': round(C * k), 'at': at}
        else:
            gaits[name] = {'frames': frames, 'cycle': round(2 * stride(os.path.join(d, 'base.png'), os.path.join(d, 'mask.png')) * k)}
        cycle = gaits[name]['cycle']
        print(name, 'gait cycle', cycle, 'px')

    # 过渡帧（2026-09-30 用户：「男女主的动作切换还是太生硬……需要加中间帧」）：tween/<档>/ 下 base.png（= 该档原图）
    # + t1~tN（从上一档往这一档，按顺序），换档时引擎先把这几格播完再进步态，往回换倒着播。
    # t* 是拿 base 做蒙版局部重绘、**只重画输的那一方**得来的（赢方每张重画的话发丝衣褶都在变，一播就抖）。
    # 生图总会把没开放的区域也动一点，所以分界列靠赢方那一侧（赢方 + 手机）一律贴回 base 原像素，
    # 交界放在手机机身中段（纯黑平涂），过渡 TWEEN_FEATHER 像素看不出接缝；放在输方手腕上会错开一截手臂。
    # 缩放与脚底沿用这一档（赢方是 base 里同一个人），水平位置按格从上一档的手机偏移匀到这一档的，
    # 否则赢方会在上一档 → t1 那一下横跳（n0 → aK 手机相对锚点差 16 像素）。
    tweens = {}
    for name, (frm, cut) in TWEEN.items():
        d = os.path.join(HERE, 'tween', name)
        base = np.array(Image.open(os.path.join(d, 'base.png')).convert('RGB')).astype(np.float32)
        x = np.arange(base.shape[1])
        w = np.clip(((x - cut) if name[0] == 'a' else (cut - x)) / TWEEN_FEATHER, 0, 1)[None, :, None]   # 取生图的权重
        n = len([f for f in os.listdir(d) if f[0] == 't' and f[1:-4].isdigit()])
        k = scales.get(name, SCALE)
        dx = lambda m: m['phone'][0] - m['ax']
        frames = []
        for i in range(1, n + 1):
            img = np.array(Image.open(os.path.join(d, f't{i}.png')).convert('RGB').resize(base.shape[1::-1])).astype(np.float32)
            img = np.round(base * (1 - w) + img * w).astype(np.int16)
            t = i / (n + 1)
            want = dx(poses[name]) * t + dx(poses[frm]) * (1 - t)
            cx = anchors[name][0] - (want - dx(poses[name])) / k
            g = f'{name}_t{i}'
            meta, im, _ = build_pose(g, img, anchor=(cx, anchors[name][1]), scale=k, lose=LOSE(name))
            meta['face'] = {s_: [round(v, 1) for v in head_find(ref, im, s_)[1:]] for s_ in 'ab'}
            meta['hip'] = hip_find(im)
            poses[g] = meta
            sheet.append((g, meta, im))
            frames.append(g)
        tweens[name] = {'from': 'n' if frm[0] == 'n' else frm, 'frames': frames}   # from 写档名（main.js 的 FX.pose），僵持档叫 n
        print(name, 'tween', frames)

    json.dump({'rooms': rooms, 'center': center, 'height': H, 'poses': poses, 'gaits': gaits, 'tweens': tweens},
              open(os.path.join(OUT, 'world.json'), 'w'), ensure_ascii=False, indent=1)
    print('rooms', rooms, 'total', sum(rooms), 'center', center)

    # 手机位置自检图：每张贴图上画出锚点（绿）与手机（红圈）
    cw = 560
    out = Image.new('RGB', (cw * 3, 380 * ((len(sheet) + 2) // 3)), (40, 40, 40))
    for k, (name, meta, im) in enumerate(sheet):
        c = Image.new('RGBA', im.size, (250, 240, 150, 255)); c.alpha_composite(im)
        d = ImageDraw.Draw(c)
        d.line((meta['ax'], 0, meta['ax'], meta['h']), fill=(0, 160, 0), width=3)
        if 'phone' in meta:
            px, py = meta['phone']; d.ellipse((px - 26, py - 26, px + 26, py + 26), outline=(255, 0, 0), width=5)
        d.text((8, 8), name, fill=(0, 0, 0))
        c.thumbnail((cw, 380))
        out.paste(c.convert('RGB'), ((k % 3) * cw, (k // 3) * 380))
    out.save(os.path.join(HERE, 'preview', 'phone_check.jpg'), quality=88)


if __name__ == '__main__':
    main()
