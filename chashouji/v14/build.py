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
    out = light_phone(full, big_core, hand, rgba)
    out[hand] = rgba[hand]                # 手盖回最上面
    d = ndimage.distance_transform_edt(~(big_core & ~hand))   # 屏幕照到手：按离**露出来的**屏幕多远算，压在机身上的整只拳头不算"贴着屏幕"
    k = np.where(hand, np.clip(1 - d / HAND_LIT['range'], 0, 1) * HAND_LIT['a'], 0)[..., None]
    out[..., :3] = out[..., :3] * (1 - k) + np.array(HAND_LIT['rgb'], np.float32) * k
    return out[..., :3], out[..., 3] / 255


# 亮屏（2026-09-27 用户：「手机屏幕可以亮着 然后软件是某聊天软件，但屏幕太小 不用具体显示聊天记录」）。
# 只涂浅色在明亮底图上读成"一块白东西"（用户："屏幕并没有发亮"）：读出亮着靠冷色 + 机身外一圈光晕 + 照到手。
# 长度单位都是原图像素（贴图最后 ×SCALE≈0.44 上屏）。界面是固定图案、不随机，53 张帧一模一样，连播不闪。
SCREEN = {'w': 0.86, 'h': 0.8,                               # 屏幕占机身长 / 宽的比例（四周剩下的是黑边框）
          'mid': (250, 255, 255), 'edge': (150, 215, 255),   # 冷色渐变：中心发白 → 边缘淡蓝
          'bar': (20, 200, 110), 'bar_h': 0.2,               # 顶栏：偏蓝的绿（跟真相喷雾的青柠 156,238,96 区分开）、占屏高
          'me': (58, 190, 120), 'them': (255, 255, 255),     # 右边自己发的绿气泡 / 左边对方的白气泡，都不写字
          'input': (205, 212, 220)}                          # 底部输入栏
GLOW = {'rgb': (80, 200, 255), 'grow': 9, 'blur': 20, 'a': 0.75}   # 光晕：机身轮廓外扩、高斯模糊、透明度，画在机身后面
HAND_LIT = {'range': 10, 'a': 0.3, 'rgb': (190, 235, 255)}                        # 屏幕照到手：离机身多近的手染冷光、最多染几成（0.45 整只拳头发蓝像戴手套）


def screen_tex(w, h):
    """w×h 的聊天界面（横拿：上边是顶栏）。没有字、没有真实 App 的 logo，远看读出"在聊天"就够。"""
    S = SCREEN
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.clip(np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / 1.2, 0, 1)[..., None]
    im = Image.fromarray((np.array(S['mid']) * (1 - d) + np.array(S['edge']) * d).astype(np.uint8), 'RGB')
    g = ImageDraw.Draw(im)
    bh = round(h * S['bar_h'])
    g.rectangle((0, 0, w, bh), fill=S['bar'])
    r = bh * 0.32
    g.ellipse((w * 0.2 - r, bh / 2 - r, w * 0.2 + r, bh / 2 + r), fill=(255, 255, 255))          # 头像
    g.rounded_rectangle((w * 0.2 + r * 1.8, bh / 2 - r * 0.45, w * 0.55, bh / 2 + r * 0.45), r * 0.45, fill=(255, 255, 255))  # 名字条
    ih = round(h * 0.14)
    g.rectangle((0, h - ih, w, h), fill=S['input'])
    g.rounded_rectangle((w * 0.22, h - ih * 0.78, w * 0.78, h - ih * 0.22), ih * 0.28, fill=(250, 252, 255))
    lh = (h - bh - ih) / 4                                    # 三条气泡：对方 / 自己 / 对方，中段两头会被拳头盖住，留在正中
    for k, (side, ln) in enumerate([('them', 0.34), ('me', 0.3), ('them', 0.26)]):
        y = bh + lh * (k + 0.55)
        x0 = w * 0.2 if side == 'them' else w * (0.8 - ln)
        g.rounded_rectangle((x0, y, x0 + w * ln, y + lh * 0.62), lh * 0.3, fill=S[side])
    return im


def light_phone(full, core, hand, rgba):
    """full：已经贴上放大机身的整张 RGBA（PIL）；core：放大后的机身（bool）。
    机身后垫光晕、机身上贴亮屏，返回 float 数组；手由调用方再盖回去、再染冷光。"""
    ys, xs = np.nonzero(core)
    pts = np.stack([xs, ys], 1).astype(np.float32); c = pts.mean(0)
    _, vec = np.linalg.eigh(np.cov((pts - c).T))
    u = vec[:, 1] * (1 if vec[0, 1] >= 0 else -1)            # 长轴，朝右
    proj = (pts - c) @ np.stack([u, [-u[1], u[0]]], 1)
    L, Wd = proj[:, 0].max() - proj[:, 0].min(), proj[:, 1].max() - proj[:, 1].min()
    # 光晕：垫在机身后面（先画光晕、再把人和机身整张叠上去）
    g = ndimage.gaussian_filter(ndimage.binary_dilation(core, iterations=GLOW['grow']).astype(np.float32), GLOW['blur'] / 2)
    glow = np.zeros(core.shape + (4,), np.uint8)
    glow[..., :3] = GLOW['rgb']; glow[..., 3] = np.clip(g * GLOW['a'] * 255, 0, 255)
    base = Image.fromarray(glow, 'RGBA'); base.alpha_composite(full)
    # 亮屏：沿机身长轴贴，斜拿的跟着斜
    SS = 4                                                   # 4 倍大画、4 倍大转，再缩回来：原尺寸直接转，斜拿的边和气泡锯齿成一排点
    tex = screen_tex(round(L * SCREEN['w']) * SS, round(Wd * SCREEN['h']) * SS).convert('RGBA')
    tex = tex.rotate(-np.degrees(np.arctan2(u[1], u[0])), resample=Image.BICUBIC, expand=True)
    tex = tex.resize((round(tex.width / SS), round(tex.height / SS)), Image.LANCZOS)
    base.alpha_composite(tex, (round(c[0] - tex.width / 2), round(c[1] - tex.height / 2)))
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

EDGE_STEP = 6     # 轮廓按行采样的间距（引擎像素）


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


def build_pose(name, path, feet_align=False, anchor=None, scale=SCALE):
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
    meta = {'w': int(x1 - x0), 'h': int(y1 - y0),
            'ax': round(float(cx - x0), 1), 'ay': int(foot - y0)}
    if ph:
        meta['phone'] = [round(ph[0] * scale - x0, 1), round(ph[1] * scale - y0, 1)]
        meta['edge'] = edges(np.array(im)[..., 3] > 127, meta['phone'])
    return meta, im, (cx / scale, foot / scale)


def main():
    os.makedirs(OUT, exist_ok=True)
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
    rooms = []
    for i, p in enumerate(parts):
        r = p.resize((round(p.width * s), H), Image.LANCZOS)
        r.save(os.path.join(OUT, f'room{i}.webp'), quality=86, method=6)
        rooms.append(r.width)
    # 客厅中点 = 沙发正中 = 0 米。按原图客厅中线换算到拼接后的世界坐标
    center = rooms[0] + round((L.width / 2 - CUT_LIVING_L) * s)

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
            meta, im, raw = build_pose(name, os.path.join(HERE, f), feet, scale=scales[name])
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
        frames = [name]
        for f in range(1, 8):
            g = f'{name}_g{f}'
            img = plant_feet(os.path.join(d, f'f{f}.png'), os.path.join(d, 'base.png'), os.path.join(d, 'mask.png'))
            meta, im, _ = build_pose(g, img, anchor=base_raw, scale=k)
            meta['face'] = poses[name]['face']      # 只重画了腿，脸和 base 同一处
            meta['hip'] = hip_find(im)              # 腿换了，短裤跟着变，每格重量
            poses[g] = meta
            sheet.append((g, meta, im))
            frames.append(g)
        cycle = round(2 * stride(os.path.join(d, 'base.png'), os.path.join(d, 'mask.png')) * k)
        gaits[name] = {'frames': frames, 'cycle': cycle}
        print(name, 'gait cycle', cycle, 'px')

    json.dump({'rooms': rooms, 'center': center, 'height': H, 'poses': poses, 'gaits': gaits},
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
