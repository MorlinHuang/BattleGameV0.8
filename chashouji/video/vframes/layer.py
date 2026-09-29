"""场景背景的出场视频 → 透明图层（AI 抠人物 + 图层合成），以及尾帧对齐。

即梦生成的出场视频背景是场景（卧室、天空、光效），不是纯色幕布，按颜色抠不了。做法（2026-09-28 真相女神定下的标准）：
  1. matte：isnet-anime（二次元人物分割，rembg 同款模型）逐帧出人物遮罩；
  2. bake：人物不透明、只在画框边软掉（底边软得宽 4 倍：特写时人物被画框底边截断）；
     环境只留 BG、越靠画框边越淡，透出底下的游戏，没有矩形边；
     亮部（光柱、亮片、金光爆开）留 GLOW，光是这段视频的"特效"，要亮在游戏上面；
     离结尾 ENV_OFF[0]~ENV_OFF[1] 秒环境和光退干净，最后只剩人物，好交给游戏里的立绘。
     不退的话，自动保留的亮部会把尾帧整片金白过曝也留下来，成一块白板。
  3. align_end：立绘在尾帧里的位置（缩放 + 偏移），游戏里立绘就在这个位置现身，读起来是她从视频里走进游戏。
为什么烤进视频、不在游戏里用 WebGL 实时合成：桌面容器的 Chrome（无 GPU）里 WebGL 上下文一建就丢，
直播伴侣 / OBS 的环境同样没法保证；带 alpha 的 VP9 webm 用普通 <video> 就能放，Chromium 内核都支持。
"""
import os
import numpy as np
from PIL import Image

MODEL = os.environ.get('VFRAMES_MODEL', os.path.expanduser('~/isnet-anime.onnx'))

# 图层合成参数（真相女神上线版）
BG = 0.22                # 环境留多少不透明度
GLOW = 0.9               # 亮部留多少
FEATHER = 0.16           # 环境从画框边往里多宽淡进来（占画面宽的比例）
EDGE = 0.03              # 人物在画框边软掉多宽
ENV_OFF = (1.25, 0.45)   # 环境 + 光从离结尾几秒开始退、退到离结尾几秒退完

ALIGN_WARN = 40          # 尾帧对齐残差（0~255 平均色差）超过它就警告：真相女神对上时是 18


def model_ok():
    try:
        import onnxruntime  # noqa: F401
    except ImportError:
        return False
    return os.path.isfile(MODEL)


def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- 1. 人物遮罩

_sess = None


def matte_init(threads):
    global _sess
    import onnxruntime as ort
    o = ort.SessionOptions()
    o.intra_op_num_threads = threads
    o.inter_op_num_threads = 1
    _sess = ort.InferenceSession(MODEL, o, providers=['CPUExecutionProvider'])


def matte_frame(job):
    """一帧 → 同名灰度 PNG（255 = 人物）。模型输入 1024×1024 直接拉伸（跟 rembg 一致，不补边），
    减 mean (0.485, 0.456, 0.406)、std 1，输出 min-max 归一化。"""
    src, dst = job
    im = Image.open(src).convert('RGB')
    x = np.asarray(im.resize((1024, 1024), Image.LANCZOS)).astype(np.float32) / 255.0
    x = (x - np.array([0.485, 0.456, 0.406], np.float32)).transpose(2, 0, 1)[None]
    y = _sess.run(None, {_sess.get_inputs()[0].name: x})[0][0, 0]
    y = (y - y.min()) / max(1e-6, y.max() - y.min())
    Image.fromarray((y * 255).astype(np.uint8)).resize(im.size, Image.LANCZOS).save(dst)


# ---------------------------------------------------------------- 2. 图层合成

def env_weight(i, n, fps):
    """第 i 帧（共 n 帧）环境 + 光还留几成：离结尾 ENV_OFF[0] 秒起往下退，ENV_OFF[1] 秒退完。"""
    left = (n - i - 0.5) / fps
    return min(1.0, max(0.0, (left - ENV_OFF[1]) / (ENV_OFF[0] - ENV_OFF[1])))


def _vsmooth(a, r):
    """按列上下 2r+1 行求平均（累加和，O(像素数)）"""
    p = np.pad(a.astype(np.float32), ((r + 1, r), (0, 0))).cumsum(0)
    return (p[2 * r + 1:] - p[:-2 * r - 1]) / (2 * r + 1)


def _blur(a, r):
    """方框模糊两遍（近似高斯），边缘按最近像素延伸"""
    for _ in range(2):
        p = np.pad(a, ((r + 1, r), (0, 0)), mode='edge').cumsum(0)
        a = (p[2 * r + 1:] - p[:-2 * r - 1]) / (2 * r + 1)
        p = np.pad(a, ((0, 0), (r + 1, r)), mode='edge').cumsum(1)
        a = (p[:, 2 * r + 1:] - p[:, :-2 * r - 1]) / (2 * r + 1)
    return a


# 底部法术潮（2026-09-29 白娘子）：视频里从左边涌进来、最后铺在画面底部的大海 + 虾兵蟹将。
# 它是特效不是环境：整条保留、不随环境在结尾退掉 —— 游戏里的海在视频放完时原位接上（main.js / sea.js handoff）。
# 按颜色找：每一列最上面那段"成片的青蓝"就是海面（夜色湖面是灰蓝，G、B 比 R 高得少、饱和度也低，实测分得开），
# 海面往下到画面底边全算海；海面上方紧挨着的亮白（浪尖白沫）、橙红（骑在浪头上的虾兵蟹将）也算。
SEA = {
    'from': 0.35,        # 只在画面上沿往下这一成以下找海（掌心的蓝水球、发光在上半截）
    # 海水（青蓝）：饱和度、G−R、B−R 都要够，且 B−G 不能太大 —— 身上的冰蓝光晕是纯蓝（B 比 G 高一大截），
    # 暗处的湖面 G 比 R 高得不够；亮度太低的暗蓝也不算
    'sat': 0.45, 'gr': 0.15, 'br': 0.2, 'bg': 0.15, 'v': 0.3,
    'run': 6,            # 上下 2·run+1 行里三成以上是海水才算海面（零星的蓝点不算）
    'onset': 0.005,      # 整帧海水像素超过这个比例才算"海来了"（之前的帧不找海：夜色湖面零星会有几颗像海水的像素）
    # 不是雾的像素：雾是灰淡的浅蓝（饱和度 ~0.22、亮度 ~0.8）；白沫更亮、海水和兵更艳、阴影更暗
    'mist': (0.32, 0.9, 0.45),             # 饱和度 > 0.32 或 亮度 > 0.9 或 亮度 < 0.45 就不是雾
    # 或者有纹理：雾是平的（7×7 里亮度标准差 ~0.01），浪沫、浪花有纹理 —— 浪尖发灰的白沫跟雾一样亮、一样淡（亮度 0.67~0.87），
    # 只能靠这个认出来
    'tex': 0.03,
    'grow': 80,          # 浪尖白沫 / 飞沫：从海面往上最多长多少像素（只长在"不是雾、且下面一行已经是海"的地方）
    'mob': 30,           # 虾兵蟹将：橙红色块周围这么多像素以内、不是雾的都算（金盔、兵器、脸）
    'edge': 20,          # 海面轮廓的闭运算半径：比 2·edge 列窄的凹口填平（再大会把浪头上虾兵之间的雾也填成灰块）
    'col': 12,           # 海面高度按左右 2·col+1 列取中位数（去掉尖刺、补上整列都是白沫找不到海水的缝）
    'soft': 3,           # 边缘羽化半径
    'bottom': 0.02,      # 画框底边软掉多宽（占宽的比例）
}


def sea_mask(c, m):
    """RGB（0~1）+ 人物遮罩 → 海的遮罩（0~1）"""
    h, w = m.shape
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    mx = c.max(2)
    sat = (mx - c.min(2)) / np.maximum(mx, 1e-3)
    y0 = int(h * SEA['from'])
    water = ((sat > SEA['sat']) & (g - r > SEA['gr']) & (b - r > SEA['br']) & (b - g < SEA['bg'])
             & (mx > SEA['v']) & (m < 0.5))
    water[:y0] = False
    if water.mean() < SEA['onset']:
        return np.zeros((h, w), np.float32)
    core = _vsmooth(water, SEA['run']) > 0.3
    has = core.any(0)
    top = np.where(has, core.argmax(0), h).astype(np.float32)
    k = SEA['col']
    tp = np.pad(top, k, mode='edge')
    top = np.median(np.stack([tp[i:i + w] for i in range(2 * k + 1)]), 0)
    yy = np.arange(h)[:, None]
    sea = yy >= top[None, :]
    ms, mh, ml = SEA['mist']
    mean = _blur(mx, 3)
    tex = np.sqrt(np.maximum(_blur(mx * mx, 3) - mean * mean, 0))
    vivid = ((sat > ms) | (mx > mh) | (mx < ml)) & (m < 0.5)     # 按颜色不是雾
    solid = vivid | ((tex > SEA['tex']) & (m < 0.5))             # 按颜色或纹理不是雾（纹理在物体边上会往外带出几像素）
    solid[:y0] = False
    vivid[:y0] = False
    # 浪尖白沫、飞沫：从海面一行行往上长，只长在"不是雾、且正下方已经是海"的地方
    up = sea.copy()
    cols = np.arange(w)
    for d in range(1, SEA['grow'] + 1):
        row = (top - d).astype(int)
        ok = (row >= y0) & solid[np.clip(row, 0, h - 1), cols] & up[np.clip(row + 1, 0, h - 1), cols]
        up[row[ok], cols[ok]] = True
    # 骑在浪头上的虾兵蟹将：橙红色块，加上它周围一圈不是雾的（金盔、兵器、脸）
    # 海面轮廓：每列最上面那个海像素往下全填上（浪卷里面露出的雾、白沫里的小缺口都是海的一部分）；
    # 轮廓再做一次闭运算（先取左右 edge 列里最高的、再取最低的）：比 2·edge 窄的凹口填平，浪尖原样不削
    env_top = np.where(up.any(0), up.argmax(0), h).astype(np.float32)
    k = SEA['edge']
    win = lambda a, f: f(np.stack([np.pad(a, k, mode='edge')[i:i + w] for i in range(2 * k + 1)]), 0)
    env_top = win(win(env_top, np.min), np.max)
    up = yy >= env_top[None, :]
    # 虾兵蟹将只按颜色：它周围是雾，按纹理的话身边会带出一圈灰边
    orange = (r - g > 0.2) & (r - b > 0.25) & (sat > 0.5) & vivid
    near_mob = _blur(orange.astype(np.float32), SEA['mob']) > 0.01
    out = (up | orange | (near_mob & vivid)).astype(np.float32)
    return np.clip(_blur(out, SEA['soft']), 0, 1)


# 月夜银云海（2026-09-29 嫦娥）：深蓝 + 银白的云浪，玉兔、金蟾骑在浪上，从左边涌进来，最后铺在画面底部。
# 跟白娘子的海反过来认：背景是很匀的深蓝夜空（饱和度 ~0.69、亮度 ~0.40），云浪要么更亮（银白）、要么更暗（浪身深蓝），
# 所以"不像夜空"的就是云。浪身有几行深蓝跟夜空分不开，不要求整列连成一段，按"这一行往下一半以上是云"判。
CLOUD = {
    'from': 0.45,                   # 只在画面上沿往下这一成以下找（她在上半截）
    'sky_sat': 0.58, 'sky_v': (0.33, 0.48),   # 夜空：饱和度 > sky_sat、亮度在这个范围里（只按颜色 —— 浪头上方满天金色光点，按纹理会被当成云）
    'halo': 40,                     # 人物遮罩往外这么多像素都不算（她的外发光）
    'run': 8, 'dense': 0.6,         # 二维平滑半径 / 占比：零星的星点、金色光点连不成片
    'fill': 0.55,                   # 这一行往下到底边，云占这么多以上才算云海
    'min': 10,                      # 云海不到这么多行高的列不算
    'col': 12,                      # 云海高度按左右 2·col+1 列取中位数
    'grow': 120, 'bright': 0.55,    # 浪尖白沫、骑在浪上的玉兔（亮）/ 金蟾（金色）：从云海往上最多长多少像素，只长在亮的 / 金色的像素上
    'spike': 8,                     # 浪身轮廓开运算：比 2·spike 列窄的竖刺削掉
    'feather': 24,                  # 浪身左右两侧横向羽化多少列
    'soft': 3, 'bottom': 0.02,
    'side': -1,                     # 从哪边涌进来（−1 左 / +1 右）：只要从这一边的边缘连过来的那一片
}
# 奶盖泡泡海（2026-09-29 绿茶妹妹）：同云海的认法 —— 背景是很匀的暗粉紫夜色（饱和度 ~0.6、亮度 0.16~0.25），
# 奶白浅粉的泡沫浪亮（~0.95）、饱和度低（~0.15），"不像夜色"的就是浪；白莲花、奶茶杯、小白兔、爱心骑在浪上，亮，按 bright 往上长。
# 浪从右边涌进来。
TEA = {**CLOUD, 'sky_sat': 0.45, 'sky_v': (0.0, 0.34), 'side': +1}


def _vsmooth_edge(a, r):
    """同 _vsmooth，但上下边按最近一行延伸（底边几行不会被补的 0 平均掉）"""
    p = np.pad(a.astype(np.float32), ((r + 1, r), (0, 0)), mode='edge').cumsum(0)
    return (p[2 * r + 1:] - p[:-2 * r - 1]) / (2 * r + 1)


def cloud_mask(c, m, C=CLOUD):
    """RGB（0~1）+ 人物遮罩 → 云海（C = TEA：奶盖泡泡海）的遮罩（0~1）"""
    h, w = m.shape
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    mx = c.max(2)
    sat = (mx - c.min(2)) / np.maximum(mx, 1e-3)
    sky = (sat > C['sky_sat']) & (mx > C['sky_v'][0]) & (mx < C['sky_v'][1])
    near = _blur(m, C['halo']) > 0.02
    solid = ~sky & ~near
    y0 = int(h * C['from'])
    solid[:y0] = False
    core = _blur(solid.astype(np.float32), C['run']) > C['dense']
    below = np.cumsum(core[::-1], 0)[::-1] / np.arange(h, 0, -1)[:, None]
    ok = core & (below > C['fill'])
    top = np.where(ok.any(0), ok.argmax(0), h).astype(np.float32)
    top[(h - top) < C['min']] = h
    k = C['col']
    tp = np.pad(top, k, mode='edge')
    top = np.median(np.stack([tp[i:i + w] for i in range(2 * k + 1)]), 0)
    # 从哪边涌进来就只要从那边边缘连过来的那一片（嫦娥：右下角贴着她衣袖的蓝光不算）
    has = top < h
    if not has[0 if C['side'] < 0 else -1]:
        return np.zeros((h, w), np.float32)
    top[(np.cumprod(has) if C['side'] < 0 else np.cumprod(has[::-1])[::-1]) == 0] = h
    yy = np.arange(h)[:, None]
    body_top = top
    k = C['spike']
    win = lambda a, f: f(np.stack([np.pad(a, k, mode='edge')[i:i + w] for i in range(2 * k + 1)]), 0)
    body = yy >= win(win(top, np.max), np.min)[None, :]
    # 浪尖白沫、骑在浪上的玉兔金蟾：从云海往上长，只长在亮的 / 金色的像素上，长出来的只留它本身
    # （往下填满会把腾空的兔子和浪之间那段夜空也包进来）
    bright = ((mx > C['bright']) | ((r > g) & (g > b) & (sat > 0.35))) & ~near
    up = body.copy()
    cols = np.arange(w)
    for d in range(1, C['grow'] + 1):
        row = (body_top - d).astype(int)
        ok = (row >= y0) & bright[np.clip(row, 0, h - 1), cols] & up[np.clip(row + 1, 0, h - 1), cols]
        up[row[ok], cols[ok]] = True
    up = body | (up & bright)
    # 浪身左右两侧只横向羽化：浪刚涌进来时右半边深蓝跟夜空分不开，识别会竖着切一刀，
    # 100% 的浪挨着 22% 的环境，硬边一眼就看得出来；横向羽化不往上带出一圈夜空
    bf = body.astype(np.float32)
    k = C['feather']
    for _ in range(2):
        p = np.pad(bf, ((0, 0), (k + 1, k)), mode='edge').cumsum(1)
        bf = (p[:, 2 * k + 1:] - p[:, :-2 * k - 1]) / (2 * k + 1)
    return np.clip(np.maximum(_blur(up.astype(np.float32), C['soft']), np.minimum(1, bf * 1.6) * (yy >= top.min())), 0, 1)


# 底部法术潮：名字 → (遮罩函数, 参数)。vframes.py FX_NAMES 是给人看的名字
FX = {'sea': (sea_mask, SEA), 'cloud': (cloud_mask, CLOUD), 'tea': (lambda c, m: cloud_mask(c, m, TEA), TEA)}


def fx_cover(job):
    """法术潮盖掉再抠一次人物用的画面：大浪、玉兔进画面以后，isnet 会把注意力分给它们，人物被抠淡
    （嫦娥 5.9~6.5 秒人物像素从 15 万掉到几百）。把法术潮那片（往外扩一点）换成同一行里其余背景的中位色，
    写到 dst。这一帧没有法术潮返回 False（不用重抠）。"""
    src, msk, dst, fx = job
    c = np.asarray(Image.open(src).convert('RGB')).astype(np.float32) / 255
    m = np.asarray(Image.open(msk).convert('L')).astype(np.float32) / 255
    s = FX[fx][0](c, m)
    if s.max() < 0.02:
        return False
    cover = _blur((s > 0.02).astype(np.float32), 12) > 0.01
    bg = ~cover & (_blur(m, 20) < 0.02)
    fill, last = c.copy(), np.median(c[bg], 0) if bg.any() else c.reshape(-1, 3).mean(0)
    for y in range(c.shape[0]):
        if bg[y].sum() > 20:
            last = np.median(c[y][bg[y]], 0)
        fill[y] = last
    Image.fromarray((np.where(cover[..., None], fill, c) * 255).round().astype(np.uint8)).save(dst)
    return True


def sea_line(frame_png, matte_png, fx='sea'):
    """最后一帧里法术潮上沿的高度（视频像素）：遮罩每列最上沿，取有法术潮的那些列的中位数。没有返回 None。"""
    c = np.asarray(Image.open(frame_png).convert('RGB')).astype(np.float32) / 255
    m = np.asarray(Image.open(matte_png).convert('L')).astype(np.float32) / 255
    s = FX[fx][0](c, m) > 0.5
    has = s.any(0)
    return int(np.median(s.argmax(0)[has])) if has.mean() > 0.5 else None


def bake_frame(job):
    """原帧 + 人物遮罩 → RGBA。颜色不动，只算 alpha：
    a = max(人物 × 画框边软化, 环境画框边淡入 × 环境权重 × max(BG, GLOW × 亮部), 底部法术潮 × 底边软化)"""
    src, msk, dst, env, fx = job
    c = np.asarray(Image.open(src).convert('RGB')).astype(np.float32) / 255
    m = np.asarray(Image.open(msk).convert('L')).astype(np.float32) / 255
    h, w = m.shape
    yy, xx = np.mgrid[0:h, 0:w]
    u, v, asp = (xx + 0.5) / w, (yy + 0.5) / h, h / w
    e = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v) * asp)              # 到画框四边的距离（按宽量）
    ec = np.minimum(np.minimum(u, 1 - u), np.minimum(v, (1 - v) * 0.25) * asp)     # 人物：底边软得宽 4 倍
    hl = ss(0.62, 0.95, c.max(2))                                                  # 亮部：光柱、亮片、金光
    a = np.maximum(m * ss(0, EDGE, ec), ss(0, FEATHER, e) * env * np.maximum(BG, GLOW * hl))
    if fx:
        f, P = FX[fx]
        a = np.maximum(a, f(c, m) * ss(0, P['bottom'], (1 - v) * asp))
    Image.fromarray(np.dstack([(c * 255).round(), (a * 255).round()]).astype(np.uint8), 'RGBA').save(dst, compress_level=1)
    return int((m > 0.5).sum()), 0


# ---------------------------------------------------------------- 3. 尾帧对齐

def _diff(frame, rgb, al, x, y):
    """立绘（已缩放好的 rgb、不透明区 al）左上角放在 (x, y) 时，跟 frame 在立绘不透明处的平均色差（0~255）。
    立绘超出画面的部分不算；在画面里的不透明像素不到一半就当对不上。"""
    h, w = al.shape
    H, W = frame.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return 1e9
    sub = al[y0 - y:y1 - y, x0 - x:x1 - x]
    if sub.sum() < 0.5 * al.sum():
        return 1e9
    d = np.abs(frame[y0:y1, x0:x1] - rgb[y0 - y:y1 - y, x0 - x:x1 - x]).mean(2)
    return float(d[sub].mean())


def _search(frame, st, sa, s0, x0, y0, ds, ns, npx):
    """缩放在 s0 × (1 ± ns 步 × ds)、左上角在 (x0, y0) ± npx 像素里找色差最小的。"""
    best = (1e9, s0, round(x0), round(y0))
    for i in range(-ns, ns + 1):
        s = s0 * (1 + i * ds)
        w, h = max(1, round(st.size[0] * s)), max(1, round(st.size[1] * s))
        rgb = np.asarray(st.resize((w, h), Image.BILINEAR)).astype(np.float32)
        al = np.asarray(sa.resize((w, h), Image.BILINEAR)) > 200
        for y in range(round(y0) - npx, round(y0) + npx + 1):
            for x in range(round(x0) - npx, round(x0) + npx + 1):
                d = _diff(frame, rgb, al, x, y)
                if d < best[0]:
                    best = (d, s, x, y)
    return best


def align_end(frame_png, matte_png, standee_path):
    """立绘在尾帧里的位置：立绘缩放 s 倍、左上角放在视频像素 (x, y) 时跟尾帧重合。
    先用尾帧人物遮罩的外框和立绘不透明区的外框估一个初值，再按像素色差在初值附近细搜（先半分辨率粗搜、再原分辨率精搜）。
    返回 {'s', 'x', 'y', 'residual'}；residual 是平均色差（0~255），真相女神对上时 18。"""
    frame = np.asarray(Image.open(frame_png).convert('RGB')).astype(np.float32)
    m = np.asarray(Image.open(matte_png).convert('L')) > 128
    im = Image.open(standee_path).convert('RGBA')
    st, sa = im.convert('RGB'), im.getchannel('A')
    ys, xs = np.nonzero(m)
    ay, ax = np.nonzero(np.asarray(sa) > 128)
    if len(xs) == 0 or len(ax) == 0:
        return None
    # 初值：人物外框高 / 立绘外框高（身高最不容易被动作改变；宽度随手臂张合变）
    s = (ys.max() - ys.min() + 1) / (ay.max() - ay.min() + 1)
    x, y = xs.min() - ax.min() * s, ys.min() - ay.min() * s
    # 粗搜：半分辨率，缩放 ±12%（步长 1.5%），位置 ±12 半像素
    d, s2, x2, y2 = _search(frame[::2, ::2], st, sa, s / 2, x / 2, y / 2, 0.015, 8, 12)
    # 精搜：原分辨率，缩放 ±1.5%（步长 0.3%），位置 ±3 像素
    d, s, x, y = _search(frame, st, sa, s2 * 2, x2 * 2, y2 * 2, 0.003, 5, 3)
    return {'s': round(s, 3), 'x': int(x), 'y': int(y), 'residual': round(d, 1)}
