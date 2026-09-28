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


def bake_frame(job):
    """原帧 + 人物遮罩 → RGBA。颜色不动，只算 alpha：
    a = max(人物 × 画框边软化, 环境画框边淡入 × 环境权重 × max(BG, GLOW × 亮部))"""
    src, msk, dst, env = job
    c = np.asarray(Image.open(src).convert('RGB')).astype(np.float32) / 255
    m = np.asarray(Image.open(msk).convert('L')).astype(np.float32) / 255
    h, w = m.shape
    yy, xx = np.mgrid[0:h, 0:w]
    u, v, asp = (xx + 0.5) / w, (yy + 0.5) / h, h / w
    e = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v) * asp)              # 到画框四边的距离（按宽量）
    ec = np.minimum(np.minimum(u, 1 - u), np.minimum(v, (1 - v) * 0.25) * asp)     # 人物：底边软得宽 4 倍
    hl = ss(0.62, 0.95, c.max(2))                                                  # 亮部：光柱、亮片、金光
    a = np.maximum(m * ss(0, EDGE, ec), ss(0, FEATHER, e) * env * np.maximum(BG, GLOW * hl))
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
