#!/usr/bin/env python3
"""视频抽帧工具：一条命令把一段 mp4 变成游戏能用的两套素材，供"直接放视频 / 抽帧成帧动画"两个方案对比。

    python3 vframes.py 输入.mp4                 # 默认：均衡档、自动判断要不要抠像
    python3 vframes.py 输入.mp4 -p 高清 -k magenta -o 输出目录

产物（输出目录下）：
    frames/0001.png ...      帧动画用的逐帧 PNG（抠过像就是透明底、每帧各自裁到人物外框，偏移记在 manifest）
    atlas/sheet_0.webp ...   同一套帧拼成的图集（网页引擎直接用），≤4096×4096 一张
    manifest.json            帧率、帧数、每帧在图集里的位置和在画面里的偏移、音频、方案一文件——引擎只读这一个
    audio.m4a                原片音轨（没有音轨就没有这个文件）
    scheme1/video.mp4        方案一：原片转成网页友好的 H.264（faststart）
    scheme1/alpha.webm       方案一：抠像后的透明视频（VP9 alpha，Chrome / OBS 浏览器源可用；没抠像就不出）
                             场景背景（不是纯色幕布）用 AI 抠人物 + 图层合成（layer.py）：人物不透明、环境淡淡透出、
                             光效保留、最后一秒只剩人物——真相女神出场视频就是这么做的
    preview.html             两个方案叠在游戏画面上同步播放的对比页，带体积与内存数字
    <名字>_vframes.zip       以上全部打包

附上立绘（--standee，透明底 PNG/WebP）时，还会量出立绘在尾帧里的位置（manifest.intro），
游戏里立绘就在这个位置现身，接上视频最后一帧——填进 web/intro.js 的 CLIPS 即可。

处理顺序是定死的：原分辨率抠像 → 透明区颜色外扩 → 再缩放。
反过来先缩放再抠，缩放会把幕布色混进人物边缘，抠完一圈色边。
"""
import argparse, json, math, os, shutil, subprocess, sys, tempfile, time, zipfile
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image
import layer

HERE = os.path.dirname(os.path.abspath(__file__))

# 游戏里视频区的位置（1080×1920 竖屏，上面留 HUD、下面留评论区），预览页按它摆
DISPLAY = {'screen': [1080, 1920], 'x': 0, 'y': 225, 'w': 1080, 'h': 1440}

# 预设：帧动画的帧率与宽度。宽度是整段视频画面的宽（不是裁切后人物的宽），高按比例
PRESETS = {
    '高清':   {'fps': 24, 'width': 1080},
    '均衡':   {'fps': 15, 'width': 720},
    '省内存': {'fps': 12, 'width': 540},
}
MAX_WORK_W = 1080          # 抠像与方案一视频的工作分辨率上限（游戏里视频区就是 1080 宽）
MAX_WORK_FPS = 30          # 工作帧率上限；原片更高就降到 30
SHEET_MAX = 4096           # 图集单张边长上限（移动端 GPU 普遍支持的最大纹理）
GUTTER = 1                 # 图集里每帧四周复制一圈边缘像素，GPU 双线性采样到格子边上不会串到隔壁帧
SPILL_R = 3                # 去色溢的范围：离透明区这么多像素以内。视频的色度是 2×2 抽样再压缩的，
                           # 幕布色会渗进人物边缘 1~3 像素，这些像素 alpha 已经是 1，只看 alpha 抓不到
HOLE_R = 4                 # 离全透明区超过这么远的半透明像素算"人物身上被抠穿的洞"
HOLE_WARN = 0.005          # 洞占人物像素的比例超过它就警告（实测干净抠像 ≤0.06%，绿幕+青柠绿衣服 3.2%）
MAX_DURATION = 60          # 超过这个秒数拒绝处理——出场视频是几秒的东西，60 秒已经是误传

# 幕布色的判定：通道优势 k（绿 = G − max(R,B)，品红 = min(R,B) − G，蓝 = B − max(R,G)）
KEYS = {
    'green':   lambda r, g, b: g - np.maximum(r, b),
    'magenta': lambda r, g, b: np.minimum(r, b) - g,
    'blue':    lambda r, g, b: b - np.maximum(r, g),
}
KEY_NAMES = {'green': '绿幕', 'magenta': '品红幕', 'blue': '蓝幕', 'ai': 'AI 抠人物（场景背景）', None: '不抠像'}
KEY_CHOICES = ('auto', 'none', 'ai', *KEYS)
FX_NAMES = {'sea': '海浪 + 虾兵蟹将（白娘子）', 'cloud': '月夜云海 + 玉兔金蟾（嫦娥）', 'tea': '奶盖泡泡海 + 莲花奶茶兔（绿茶妹妹）'}   # 底部法术潮（layer.py FX）


class VFError(Exception):
    """给用户看的错误：消息本身就要说清楚怎么办。"""


def cpu_budget():
    """真正能用的核数。容器里 os.cpu_count() 报的是宿主机的核数（桌面容器报 72，配额只有 8），
    按它开进程会被 CFS 配额节流，开得越多越慢。"""
    n = len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else (os.cpu_count() or 1)
    if os.path.isfile('/sys/fs/cgroup/cpu.max'):                  # cgroup v2："配额 周期" 或 "max 周期"
        quota, period = open('/sys/fs/cgroup/cpu.max').read().split()[:2]
        if quota != 'max':
            n = min(n, int(quota) // int(period))
    elif os.path.isfile('/sys/fs/cgroup/cpu/cpu.cfs_quota_us'):   # cgroup v1：配额 -1 表示不限
        quota = int(open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us').read())
        period = int(open('/sys/fs/cgroup/cpu/cpu.cfs_period_us').read())
        if quota > 0:
            n = min(n, quota // period)
    return max(1, n)


def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        tail = p.stderr.decode('utf-8', 'replace').strip().splitlines()[-6:]
        raise VFError('ffmpeg 处理失败：\n' + '\n'.join(tail))
    return p.stdout


def fraction(s):
    try:
        n, d = s.split('/')
        return float(n) / float(d) if float(d) else 0.0
    except (ValueError, AttributeError):
        return 0.0


def frame_rate(path, v):
    """按什么帧率采样才既不丢帧、也不凭空多出重复帧。元数据里的两个帧率都靠不住：
      · 平均帧率会被停顿拉低：可变帧率（VFR）的片子帧都落在 1/24 秒的格子上、中间有停顿，
        平均只有 11.2，按它采样会把动作快的段落丢帧；
      · 基准帧率会被时间戳取整抬高：即梦的片子是 24.07 帧/秒匀速，但时间戳按 1/60 秒取整，
        帧间隔 1/30、1/20 交替，基准帧率报 60，按 30 采样多出 25% 重复帧（抠像白算、动作一顿一顿）。
    看实际的帧时间戳来分：所有间隔都是最小间隔的整数倍 → 是格子上带停顿，按最小间隔采样；
    否则是取整出来的抖动，按 帧数 ÷ 时长 采样。读不到时间戳就退回元数据里大的那个。"""
    p = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'packet=pts_time',
                        '-of', 'csv=p=0', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t = sorted(float(x) for x in p.stdout.decode().split() if x.strip().replace('.', '', 1).isdigit())
    d = [b - a for a, b in zip(t, t[1:]) if b - a > 1e-4]
    if len(d) >= 2:
        base = min(d)
        on_grid = all(abs(x / base - round(x / base)) < 0.1 for x in d)
        fps = 1 / base if on_grid else len(d) / (t[-1] - t[0])
        if 1 <= fps <= 240:
            return fps
    # 有的封装（mkv 等）基准帧率会报成 1000，超出合理范围的不用
    rates = [x for x in (fraction(v.get('avg_frame_rate')), fraction(v.get('r_frame_rate'))) if 1 <= x <= 240]
    return max(rates) if rates else 30.0


def probe(path):
    """读视频信息。旋转元数据要算进宽高——手机竖拍的视频常是 1920×1080 + 旋转 90°。"""
    p = subprocess.run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', path],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise VFError('读不出这个文件，它可能不是视频，或者文件已损坏。')
    info = json.loads(p.stdout)
    fmt = info.get('format', {}).get('format_name', '')
    if fmt.endswith('_pipe') or fmt == 'image2':
        raise VFError('这是一张图片，不是视频。')
    vs = [s for s in info.get('streams', []) if s.get('codec_type') == 'video'
          and not s.get('disposition', {}).get('attached_pic')]
    if not vs:
        raise VFError('文件里没有视频画面（可能是纯音频或图片）。')
    v = vs[0]
    w, h = int(v.get('width') or 0), int(v.get('height') or 0)
    if w < 16 or h < 16:
        raise VFError(f'视频尺寸异常（{w}×{h}）。')
    rot = 0
    for sd in v.get('side_data_list', []) or []:
        if 'rotation' in sd:
            rot = int(float(sd['rotation']))
    rot = int(v.get('tags', {}).get('rotate', rot) or rot)
    if abs(rot) % 180 == 90:
        w, h = h, w
    dur = float(v.get('duration') or info.get('format', {}).get('duration') or 0)
    if dur <= 0:
        raise VFError('读不出视频时长，文件可能不完整（下载没下完？）。')
    if dur > MAX_DURATION:
        raise VFError(f'视频长 {dur:.1f} 秒，超过 {MAX_DURATION} 秒上限。出场视频一般 4~15 秒，请确认传对了文件。')
    fps = frame_rate(path, v)
    audio = any(s.get('codec_type') == 'audio' for s in info.get('streams', []))
    return {'width': w, 'height': h, 'fps': round(fps, 3), 'duration': round(dur, 3),
            'audio': audio, 'codec': v.get('codec_name'), 'rotation': rot}


# ---------------------------------------------------------------- 抠像

def detect_key(paths):
    """看边框一圈的颜色：八成以上像素接近同一个饱和色 → 是幕布，按那个颜色抠；否则不抠。
    只看边框、不看画面中间：人物可能从画外飞进来，中间哪一帧都可能是人。"""
    ring = []
    for p in paths:
        a = np.asarray(Image.open(p).convert('RGB')).astype(np.int32)
        h, w = a.shape[:2]
        t = max(2, min(h, w) // 50)
        ring.append(np.concatenate([a[:t].reshape(-1, 3), a[-t:].reshape(-1, 3),
                                    a[:, :t].reshape(-1, 3), a[:, -t:].reshape(-1, 3)]))
    ring = np.concatenate(ring)
    c = np.median(ring, axis=0)
    close = np.sqrt(((ring - c) ** 2).sum(1)) < 60
    frac = float(close.mean())
    r, g, b = c
    best = max(KEYS, key=lambda k: KEYS[k](r, g, b))
    strength = float(KEYS[best](r, g, b))
    if frac >= 0.8 and strength >= 80:
        return best, {'color': [int(x) for x in c], 'uniform': round(frac, 3), 'strength': round(strength)}
    return None, {'color': [int(x) for x in c], 'uniform': round(frac, 3), 'strength': round(strength)}


def key_color_strength(paths, key):
    """强制指定幕布色时，从边框里取那种颜色最典型的强度，定阈值用。"""
    vals = []
    for p in paths:
        a = np.asarray(Image.open(p).convert('RGB')).astype(np.int32)
        t = max(2, min(a.shape[:2]) // 50)
        ring = np.concatenate([a[:t].reshape(-1, 3), a[-t:].reshape(-1, 3)])
        vals.append(KEYS[key](ring[:, 0], ring[:, 1], ring[:, 2]))
    v = np.concatenate(vals)
    s = float(np.percentile(v, 75))
    return s if s >= 60 else 200.0


def box_blur(a, r):
    """(H, W, C) 按 (2r+1)² 方框求均值的和（积分图，O(像素数)，跟半径无关）。"""
    # float64：积分图的尾部是整帧像素值之和（上亿），float32 只有 7 位有效数字，大数相减会在
    # 远离人物的地方算出假的非零权重，填进乱色（实测 720×960 一帧 360 个像素填错、57 个超出 0~255）
    p = np.pad(a.astype(np.float64), ((r + 1, r), (r + 1, r), (0, 0)), mode='constant').cumsum(0).cumsum(1)
    return p[2 * r + 1:, 2 * r + 1:] - p[:-2 * r - 1, 2 * r + 1:] - p[2 * r + 1:, :-2 * r - 1] + p[:-2 * r - 1, :-2 * r - 1]


EXTEND_RADII = (2, 6, 16)


def extend_edges(rgb, alpha, radii=EXTEND_RADII):
    """把不透明像素的颜色往透明区外扩。缩放和 GPU 双线性采样会把透明区的 RGB 混进边缘，
    透明区如果还是幕布色，缩小后就是一圈色边。
    做法：按 alpha 加权模糊（预乘色 ÷ alpha 的模糊），由小到大几个半径，先近后远地填满透明像素。"""
    rgb = rgb.astype(np.float32)
    w = (alpha.astype(np.float32) / 255)[..., None]
    out = rgb.copy()
    todo = alpha == 0
    for r in radii:
        acc = box_blur(np.concatenate([rgb * w, w], 2), r)
        ok = todo & (acc[..., 3] > 1e-3)
        out[ok] = acc[ok][:, :3] / acc[ok][:, 3:4]
        todo &= ~ok
        if not todo.any():
            break
    return out


def near(mask, r):
    """离 mask 为真的像素不超过 r 个像素（切比雪夫距离）的区域。"""
    return box_blur(mask.astype(np.float32)[..., None], r)[..., 0] > 0.5


def key_frame(job):
    """抠一帧：k ≥ hi 的全透明，k ≤ lo 的不透明，中间线性过渡。
    去色溢只做在人物边缘（离不完全不透明的像素 SPILL_R 以内）：不透明像素的颜色是角色本身的，
    粉衣服的 R、B 天然高于 G，在内部去色溢会把它压成灰；但视频色度抽样把幕布色渗进了边缘几个
    alpha 已经是 1 的像素，只做过渡带的话发丝边上会留下零星紫点。
    去色溢、颜色外扩、找洞都只在人物外框再往外 max(EXTEND_RADII)+1 像素的范围里算：外扩够不到更远，
    结果跟整幅算逐像素相同；整幅算的话大半时间花在人物根本不在的背景上。
    返回 (人物像素数, 人物身上被抠穿的洞的像素数)。"""
    src, dst, key, strength = job
    full = np.asarray(Image.open(src).convert('RGB'))
    k = KEYS[key](*full.astype(np.int32).transpose(2, 0, 1)).astype(np.float32)
    lo, hi = 0.22 * strength, 0.55 * strength
    alpha_full = np.clip((hi - k) / (hi - lo), 0, 1)
    a8_full = np.round(alpha_full * 255).astype(np.uint8)
    rgba = np.dstack([full, a8_full])
    ys, xs = np.nonzero(a8_full)
    if len(xs) == 0:
        Image.fromarray(rgba, 'RGBA').save(dst, compress_level=1)
        return 0, 0
    m = max(EXTEND_RADII) + 1
    win = (slice(max(0, ys.min() - m), ys.max() + 1 + m), slice(max(0, xs.min() - m), xs.max() + 1 + m))
    a = full[win].astype(np.int32)
    k, alpha = k[win], alpha_full[win]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    band = near(alpha < 1, SPILL_R) & (k > 0)
    out = a.copy()
    if key == 'green':
        out[..., 1] = np.where(band, np.minimum(g, np.maximum(r, b)), g)
    elif key == 'blue':
        out[..., 2] = np.where(band, np.minimum(b, np.maximum(r, g)), b)
    else:
        m = np.clip(np.minimum(r, b) - g, 0, None)
        out[..., 0] = np.where(band, r - m, r)
        out[..., 2] = np.where(band, b - m, b)
    a8 = a8_full[win]
    rgba[win + (slice(0, 3),)] = np.clip(extend_edges(np.clip(out, 0, 255), a8), 0, 255).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(dst, compress_level=1)
    holes = (a8 > 0) & (a8 < 255) & ~near(a8 == 0, HOLE_R)
    return int((a8 > 0).sum()), int(holes.sum())


def resize_frame(job):
    """工作帧整幅缩到帧动画大小，再裁到这一帧自己的人物外框（外扩 1 像素透明边，贴边的不外扩）。
    先整幅缩放再裁，偏移就是整数像素，帧与帧之间不会有亚像素抖动。
    返回 [x, y, w, h]：这一帧在整幅画面里的位置；这一帧全透明时 w = h = 0。"""
    src, dst, size = job
    im = Image.open(src)
    if im.size != tuple(size):
        im = im.resize(tuple(size), Image.LANCZOS)
    box = [0, 0, *im.size]
    if im.mode == 'RGBA':
        ys, xs = np.nonzero(np.asarray(im)[..., 3])
        if len(xs) == 0:
            Image.new('RGBA', (1, 1)).save(dst)
            return [0, 0, 0, 0]
        box = [max(0, int(xs.min()) - 1), max(0, int(ys.min()) - 1),
               min(im.size[0], int(xs.max()) + 2), min(im.size[1], int(ys.max()) + 2)]
        im = im.crop(box)
    im.save(dst, compress_level=6)
    return [box[0], box[1], box[2] - box[0], box[3] - box[1]]


def pack(sizes, limit):
    """按帧的顺序一行一行往图集里摆（相邻帧大小相近，按顺序摆就很紧），满一张换下一张。
    sizes：每帧的 (w, h)，已含 GUTTER。返回每帧的 (第几张, x, y) 和每张的 (宽, 高)。"""
    places, sheets = [], []
    x = y = row_h = used_w = 0
    for w, h in sizes:
        if x + w > limit:                       # 这一行放不下，换行
            x, y, row_h = 0, y + row_h, 0
        if y + h > limit:                       # 这一张放不下，换张
            sheets.append((used_w, y))
            x = y = row_h = used_w = 0
        places.append((len(sheets), x, y))
        x += w
        row_h = max(row_h, h)
        used_w = max(used_w, x)
    sheets.append((used_w, y + row_h))
    return places, sheets


def build_sheet(job):
    """拼一张图集：每帧贴到自己的位置，四周复制一圈边缘像素做间隔。"""
    dst, size, mode, items = job
    sheet = np.zeros((size[1], size[0], len(mode)), np.uint8)
    for png, x, y in items:
        a = np.asarray(Image.open(png).convert(mode))
        a = np.pad(a, ((GUTTER, GUTTER), (GUTTER, GUTTER), (0, 0)), mode='edge')
        sheet[y:y + a.shape[0], x:x + a.shape[1]] = a
    Image.fromarray(sheet, mode).save(dst, quality=90, alpha_quality=100, method=4)
    return os.path.getsize(dst)


def is_previous_output(d):
    """d 是本工具之前的输出目录（或空目录）才允许清掉重做——别的目录一律不删。"""
    if not os.path.isdir(d):
        return False
    mf = os.path.join(d, 'manifest.json')
    if not os.listdir(d):
        return True
    if not os.path.isfile(mf):
        return False
    with open(mf, encoding='utf-8') as f:
        try:
            return str(json.load(f).get('tool', '')).startswith('vframes')
        except ValueError:
            return False


# ---------------------------------------------------------------- 主流程

def process(src, out_dir, preset='均衡', key='auto', progress=None, workers=None, tmp_root=None, standee=None, fx=None):
    """src → out_dir 全部产物。progress(步骤名, 0~1) 给网页版报进度。返回 manifest。
    standee：立绘文件（透明底），给了就量尾帧对齐。
    fx：视频底部带的法术潮（'sea' = 白娘子的海 + 虾兵蟹将），AI 抠人物时整条保留、不随环境在结尾退掉（layer.SEA）。
    失败时 out_dir 整个删掉，不留半套产物。中间帧放在 tmp_root（默认系统临时目录）下，结束就删。"""
    t_start = time.time()
    say = progress or (lambda step, pct: print(f'[{pct * 100:5.1f}%] {time.time() - t_start:6.1f}s  {step}', flush=True))
    if preset not in PRESETS:
        raise VFError(f'没有「{preset}」这个预设，可选：{"、".join(PRESETS)}')
    if key not in KEY_CHOICES:
        raise VFError(f'抠像方式只能是 {" / ".join(KEY_CHOICES)}')
    if fx not in (None, *FX_NAMES):
        raise VFError(f'底部法术潮只能是 {" / ".join(FX_NAMES)}')
    if key == 'ai' and not layer.model_ok():
        raise VFError(f'AI 抠人物要用的模型或 onnxruntime 不在这台机器上（模型路径 {layer.MODEL}）。')
    if standee:
        try:
            with Image.open(standee) as im:
                if im.mode not in ('RGBA', 'LA', 'PA') and 'transparency' not in im.info:
                    raise VFError('立绘要透明底（PNG / WebP 带透明通道），这张没有透明通道。')
        except OSError:
            raise VFError('立绘文件读不出来，要透明底的 PNG / WebP 图片。')
    if not os.path.isfile(src):
        raise VFError(f'找不到文件：{src}')
    # 绝对路径：以 - 开头的相对路径会被 ffprobe 当成选项，带 xxx: 前缀的会被 ffmpeg 当成协议
    src = os.path.abspath(src)
    if os.path.exists(out_dir) and not is_previous_output(out_dir):
        raise VFError(f'输出目录已存在，而且不是本工具之前的输出：{out_dir}\n为免误删里面的东西，不会覆盖，请换一个输出目录。')
    P = PRESETS[preset]
    workers = workers or cpu_budget()

    say('读取视频信息', 0.02)
    info = probe(src)
    work_w = min(MAX_WORK_W, info['width']) // 2 * 2
    work_fps = round(min(MAX_WORK_FPS, info['fps']), 3)      # 不取整：24.07 按 24 采样，8 秒里会跳掉半帧
    anim_fps = min(P['fps'], work_fps)
    anim_w = min(P['width'], work_w)

    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)
    tmp = tempfile.mkdtemp(prefix='vframes_', dir=tmp_root)
    ok = False
    try:
        # 1. 按工作分辨率、工作帧率解出全部帧（ffmpeg 自动按旋转元数据摆正）
        say('解帧', 0.05)
        raw = os.path.join(tmp, 'raw')
        os.makedirs(raw)
        run(['ffmpeg', '-v', 'error', '-y', '-i', src,
             '-vf', f'fps={work_fps},scale={work_w}:-2:flags=lanczos,format=rgb24',
             '-compression_level', '1', os.path.join(raw, '%05d.png')])
        raws = sorted(os.listdir(raw))
        if not raws:
            raise VFError('一帧都没解出来，视频可能已损坏。')
        # 截断的文件（下载没下完）头部信息还是完整的时长，ffmpeg 解到断处就停、不报错，
        # 不查的话会静默出半段素材
        expect = info['duration'] * work_fps
        if len(raws) < expect - max(2, 0.05 * expect):
            raise VFError(f'文件标称 {info["duration"]:.1f} 秒，实际只解出 {len(raws) / work_fps:.1f} 秒画面，'
                          '文件不完整（下载没下完或被截断），请重新下载后再试。')
        work_h = Image.open(os.path.join(raw, raws[0])).size[1]

        # 2. 判断 / 执行抠像
        say('判断背景', 0.15)
        probe_frames = [os.path.join(raw, raws[i]) for i in sorted({0, len(raws) // 2, len(raws) - 1})]
        detect_color, detect = detect_key(probe_frames)
        warnings = []
        if key == 'auto':
            # 纯色幕布按颜色抠（快、边缘准）；不是幕布就是场景背景，用 AI 抠人物做成图层
            key_used = detect_color or ('ai' if layer.model_ok() else None)
            if not key_used:
                warnings.append('背景不是纯色幕布，这台机器上又没有 AI 抠像模型，所以没抠像，方案一只能整块放视频。')
        elif key == 'none':
            key_used = None
        else:
            key_used = key
        strength = (0 if key_used in (None, 'ai') else detect['strength'] if key_used == detect_color
                    else key_color_strength(probe_frames, key_used))

        full = raw
        mattes = None
        if key_used == 'ai':
            # AI 抠人物：一帧 1 秒多，是整个流程最慢的一步。每个进程 1 个线程最快
            # （8 核配额实测 24 帧：8×1 线程 26 秒，4×2 线程 45 秒，2×4 线程 44 秒；单进程一帧约 9 秒）
            mattes = os.path.join(tmp, 'matte')
            full = os.path.join(tmp, 'keyed')
            os.makedirs(mattes)
            os.makedirs(full)
            with ProcessPoolExecutor(workers, initializer=layer.matte_init, initargs=(1,)) as ex:
                for i, _ in enumerate(ex.map(layer.matte_frame, [(os.path.join(raw, f), os.path.join(mattes, f)) for f in raws])):
                    if i % 6 == 0:
                        say(f'AI 抠人物 {i}/{len(raws)} 帧（还要约 {(len(raws) - i) * 9 // workers + 5} 秒）',
                            0.2 + 0.2 * i / len(raws))
            if fx:
                # 法术潮进画面的帧：把它盖成背景色再抠一次人物（layer.fx_cover：不盖的话人物会被抠淡）
                say('法术潮进画面的帧重抠人物', 0.4)
                covered = os.path.join(tmp, 'covered')
                os.makedirs(covered)
                cj = [(os.path.join(raw, f), os.path.join(mattes, f), os.path.join(covered, f), fx) for f in raws]
                with ProcessPoolExecutor(workers) as ex:
                    redo = [f for f, hit in zip(raws, ex.map(layer.fx_cover, cj, chunksize=4)) if hit]
                with ProcessPoolExecutor(workers, initializer=layer.matte_init, initargs=(1,)) as ex:
                    list(ex.map(layer.matte_frame, [(os.path.join(covered, f), os.path.join(mattes, f)) for f in redo]))
            say('图层合成（人物清晰、环境淡淡透出、光效保留）', 0.4)
            jobs = [(os.path.join(raw, f), os.path.join(mattes, f), os.path.join(full, f),
                     layer.env_weight(i, len(raws), work_fps), fx) for i, f in enumerate(raws)]
            with ProcessPoolExecutor(workers) as ex:
                stats = list(ex.map(layer.bake_frame, jobs, chunksize=4))
            if not sum(s[0] for s in stats):
                raise VFError('AI 在整段视频里都没找到人物。这个工具是给人物出场视频用的。')
        elif key_used:
            say(f'抠像（{KEY_NAMES[key_used]}）', 0.2)
            full = os.path.join(tmp, 'keyed')
            os.makedirs(full)
            jobs = [(os.path.join(raw, f), os.path.join(full, f), key_used, strength) for f in raws]
            with ProcessPoolExecutor(workers) as ex:
                stats = list(ex.map(key_frame, jobs, chunksize=4))
            subject = sum(s[0] for s in stats)
            if not subject:
                raise VFError(f'按{KEY_NAMES[key_used]}抠完画面全空了。背景可能不是{KEY_NAMES[key_used]}，'
                              '换成「不抠像」或别的颜色再试。')
            if subject > 0.99 * len(raws) * work_w * work_h:
                raise VFError(f'按{KEY_NAMES[key_used]}抠完几乎什么都没抠掉（人物占满了整个画面）。'
                              f'背景可能不是{KEY_NAMES[key_used]}，换成「自动判断」或别的颜色再试。')
            holes = sum(s[1] for s in stats) / subject
            if holes > HOLE_WARN:
                other = '品红幕' if key_used != 'magenta' else '绿幕'
                warnings.append(f'人物身上有接近{KEY_NAMES[key_used]}的颜色，被抠成了半透明'
                                f'（占人物 {holes * 100:.1f}%）。把背景亮黄的预览放大看就能看到。'
                                f'换成{other}重新生成视频才能根治，调抠像参数救不回来。')

        # 尾帧对齐：立绘在视频最后一帧里的位置
        intro = None
        if standee:
            if not key_used:
                warnings.append('没抠像就量不了尾帧里人物在哪，尾帧对齐跳过了。')
            else:
                say('量尾帧对齐（立绘在最后一帧里的位置）', 0.43)
                last = raws[-1]
                end = layer.align_end(os.path.join(raw, last), os.path.join(mattes or full, last), standee)
                if not end:
                    warnings.append('最后一帧里没有人物，尾帧对齐跳过了（出场视频最后一帧要停在人物上）。')
                else:
                    intro = {'vw': work_w, 'end': {k: end[k] for k in ('s', 'x', 'y')}, 'residual': end['residual']}
                    if end['residual'] > layer.ALIGN_WARN:
                        warnings.append(f'立绘和视频最后一帧对不太上（平均色差 {end["residual"]}，真相女神是 18）：'
                                        '视频可能没按这张立绘生成、或最后一帧姿势变了。游戏里换立绘那一下会看得出跳。')

        # 底部法术潮在最后一帧里的海面高度：游戏里的海从这个高度接上、再落回自己的位置（sea.js handoff）
        tide = None
        if fx:
            if key_used != 'ai':
                warnings.append('底部法术潮只在 AI 抠人物时保留，这次没用上。')
            else:
                y = layer.sea_line(os.path.join(raw, raws[-1]), os.path.join(mattes, raws[-1]), fx)
                if y is None:
                    warnings.append('最后一帧里没找到海，游戏里的海没法从视频里接上。')
                else:
                    tide = {'fx': fx, 'y': y, 'vw': work_w}

        # 3. 帧动画：按时间从工作帧里挑帧，整幅缩到目标大小，再各自裁到人物外框
        say('生成帧动画', 0.45)
        n_anim = max(1, int(math.floor(info['duration'] * anim_fps + 1e-6)))
        pick = sorted({min(len(raws) - 1, int(round(i * work_fps / anim_fps))) for i in range(n_anim)})
        sc = anim_w / work_w
        canvas = (anim_w, max(2, round(work_h * sc)))
        fdir = os.path.join(out_dir, 'frames')
        os.makedirs(fdir)
        pngs = [os.path.join(fdir, f'{i + 1:04d}.png') for i in range(len(pick))]
        jobs = [(os.path.join(full, raws[j]), pngs[i], canvas) for i, j in enumerate(pick)]
        with ProcessPoolExecutor(workers) as ex:
            boxes = list(ex.map(resize_frame, jobs, chunksize=4))

        # 4. 图集：每帧只占自己外框那么大的格子
        say('拼图集', 0.6)
        biggest = max(max(b[2], b[3]) for b in boxes) + 2 * GUTTER
        if biggest > SHEET_MAX:
            raise VFError('单帧比图集上限还大，换小一档预设。')
        drawn = [i for i, b in enumerate(boxes) if b[2]]
        if not drawn:
            raise VFError('帧动画抽到的帧全是空的：人物只在两次抽帧之间一闪而过。换高一档预设（帧率更高）再试。')
        places, sheet_sizes = pack([(boxes[i][2] + 2 * GUTTER, boxes[i][3] + 2 * GUTTER) for i in drawn], SHEET_MAX)
        mode = 'RGBA' if key_used else 'RGB'
        frames = [{'sheet': 0, 'x': 0, 'y': 0, 'w': 0, 'h': 0, 'ox': 0, 'oy': 0} for _ in boxes]
        items = [[] for _ in sheet_sizes]
        for i, (si, x, y) in zip(drawn, places):
            ox, oy, w, h = boxes[i]
            frames[i] = {'sheet': si, 'x': x + GUTTER, 'y': y + GUTTER, 'w': w, 'h': h, 'ox': ox, 'oy': oy}
            items[si].append((pngs[i], x, y))
        os.makedirs(os.path.join(out_dir, 'atlas'))
        sheets = [{'file': f'atlas/sheet_{si}.webp', 'size': list(sz)} for si, sz in enumerate(sheet_sizes)]
        with ProcessPoolExecutor(min(workers, len(sheets))) as ex:
            sheet_bytes = sum(ex.map(build_sheet, [(os.path.join(out_dir, s['file']), s['size'], mode, it)
                                                   for s, it in zip(sheets, items)]))

        # 5. 音轨
        say('导出音频', 0.7)
        audio = None
        if info['audio']:
            run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-c:a', 'aac', '-b:a', '160k',
                 os.path.join(out_dir, 'audio.m4a')])
            audio = 'audio.m4a'

        # 6. 方案一：原片转网页 mp4；抠过像的再出一份透明 webm
        say('方案一：转网页视频', 0.75)
        s1 = os.path.join(out_dir, 'scheme1')
        os.makedirs(s1)
        run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', f'scale={work_w}:-2:flags=lanczos,format=yuv420p',
             '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-movflags', '+faststart',
             *(['-c:a', 'aac', '-b:a', '160k'] if info['audio'] else ['-an']),
             os.path.join(s1, 'video.mp4')])
        scheme1 = {'mp4': 'scheme1/video.mp4'}
        if key_used:
            say('方案一：透明视频（VP9 alpha，最慢的一步）', 0.82)
            run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(work_fps), '-i', os.path.join(full, '%05d.png'),
                 *(['-i', src, '-map', '0:v', '-map', '1:a', '-c:a', 'libopus', '-b:a', '128k']
                   if info['audio'] else []),
                 # 画质按真相女神上线版：crf 26 / cpu-used 2（crf 30 在光柱、亮片上能看出色块）
                 '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '26',
                 '-row-mt', '1', '-deadline', 'good', '-cpu-used', '2', '-auto-alt-ref', '0',
                 '-shortest', os.path.join(s1, 'alpha.webm')])
            scheme1['webm_alpha'] = 'scheme1/alpha.webm'

        # 7. manifest + 预览页 + 打包
        say('写清单与预览页', 0.95)
        size_of = lambda rel: os.path.getsize(os.path.join(out_dir, rel))
        decoded = sum(s['size'][0] * s['size'][1] * 4 for s in sheets)
        manifest = {
            'tool': 'vframes 2',
            'source': {'file': os.path.basename(src), **info},
            'preset': preset,
            'key': key_used, 'key_detect': detect,
            'warnings': warnings,
            # 尾帧对齐（附了立绘才有）：立绘缩放 end.s、左上角放在视频像素 (end.x, end.y) 跟最后一帧重合；vw 是视频宽
            'intro': intro,
            # 底部法术潮（有 fx 才有）：最后一帧里海面（每列最上沿的中位数）在视频像素的 y
            'tide': tide,
            'fps': anim_fps, 'count': len(frames), 'duration': round(len(frames) / anim_fps, 3),
            'canvas': list(canvas),   # 帧动画所在的整幅画面（坐标系），跟方案一视频画面一一对应
            # 每帧：图集第 sheet 张的 (x, y, w, h) 那块，画到整幅画面的 (ox, oy)；w = h = 0 是空帧，什么都不画。
            # frames/NNNN.png 就是这一块（空帧是 1×1 透明图），偏移同样按 ox, oy
            'frames': frames,
            'sheets': sheets,
            'frame_pngs': 'frames/%04d.png',
            'audio': audio,
            'scheme1': scheme1,
            'display': DISPLAY,
            'stats': {
                'atlas_bytes': sheet_bytes,
                'atlas_decoded_bytes': decoded,
                'scheme1_bytes': {k: size_of(v) for k, v in scheme1.items()},
                'seconds': round(time.time() - t_start, 1),
            },
        }
        with open(os.path.join(out_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=1)
        shutil.copy(os.path.join(HERE, 'assets', 'game_bg.jpg'), os.path.join(out_dir, 'game_bg.jpg'))
        # 嵌进 <script> 的 JSON 要把 < 转义：文件名里的 </script> 会提前结束脚本块
        embed = json.dumps(manifest, ensure_ascii=False).replace('<', '\\u003c')
        with open(os.path.join(HERE, 'preview.html'), encoding='utf-8') as f:
            page = f.read().replace('/*MANIFEST*/null', embed)
        with open(os.path.join(out_dir, 'preview.html'), 'w', encoding='utf-8') as f:
            f.write(page)

        stem = os.path.splitext(os.path.basename(src))[0] or 'video'
        zpath = os.path.join(out_dir, f'{stem}_vframes.zip')
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_STORED) as z:   # png/webp/mp4 本来就压过，再压只是费时间
            for root, _, files in os.walk(out_dir):
                for fn in files:
                    p = os.path.join(root, fn)
                    if p != zpath:
                        z.write(p, os.path.relpath(p, out_dir))
        manifest['zip'] = os.path.basename(zpath)
        manifest['stats']['seconds'] = round(time.time() - t_start, 1)
        with open(os.path.join(out_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=1)
        say('完成', 1.0)
        ok = True
        return manifest
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if not ok:
            shutil.rmtree(out_dir, ignore_errors=True)


def intro_snippet(m):
    """填进 web/intro.js CLIPS 的那一条（src 和 box 按游戏里的放法改）"""
    i = m['intro']
    return (f"vw: {i['vw']}, end: {{ s: {i['end']['s']}, x: {i['end']['x']}, y: {i['end']['y']} }}"
            f"（色差 {i['residual']}）")


def main():
    ap = argparse.ArgumentParser(description='视频抽帧工具：mp4 → 帧动画图集 + 方案一网页视频 + 对比预览')
    ap.add_argument('video')
    ap.add_argument('-o', '--out', help='输出目录（默认：视频旁边的 <名字>_vframes/）')
    ap.add_argument('-p', '--preset', default='均衡', choices=list(PRESETS))
    ap.add_argument('-k', '--key', default='auto', choices=list(KEY_CHOICES),
                    help='抠像：auto 自动判断（默认；纯色幕布按颜色抠，场景背景用 AI） / none 不抠 / ai / green / magenta / blue')
    ap.add_argument('--fx', choices=list(FX_NAMES), help='视频底部带的法术潮（整条保留）：sea = 白娘子的海 + 虾兵蟹将，cloud = 嫦娥的月夜云海 + 玉兔金蟾，tea = 绿茶妹妹的奶盖泡泡海')
    ap.add_argument('-s', '--standee', help='立绘（透明底 PNG/WebP）：给了就量它在视频最后一帧里的位置')
    a = ap.parse_args()
    out = a.out or os.path.splitext(a.video)[0] + '_vframes'
    try:
        m = process(a.video, out, a.preset, a.key, standee=a.standee, fx=a.fx)
    except VFError as e:
        print('失败：' + str(e), file=sys.stderr)
        sys.exit(1)
    st = m['stats']
    print(f"\n完成（{st['seconds']} 秒）→ {out}")
    big = max(m['frames'], key=lambda f: f['w'] * f['h'])
    print(f"  抠像：{KEY_NAMES[m['key']]}；帧动画 {m['count']} 帧 @ {m['fps']}fps，画面 {m['canvas'][0]}×{m['canvas'][1]}，最大一帧 {big['w']}×{big['h']}")
    print(f"  图集 {len(m['sheets'])} 张，{st['atlas_bytes'] / 1e6:.1f} MB，解码后占内存 {st['atlas_decoded_bytes'] / 1e6:.0f} MB")
    if m['intro']:
        print(f"  尾帧对齐：{intro_snippet(m)}")
    if m['tide']:
        print(f"  尾帧海面：视频像素 y {m['tide']['y']}")
    for w in m['warnings']:
        print('  ⚠ ' + w)
    print(f"  打开 {os.path.join(out, 'preview.html')} 对比两个方案")


if __name__ == '__main__':
    main()
