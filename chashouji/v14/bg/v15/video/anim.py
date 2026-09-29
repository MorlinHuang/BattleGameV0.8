"""即梦视频 → 游戏里的动区小视频。
每段视频：ORB 粗配准 → 每个动区用周围一圈静止区域精配准（u=a*x+b, v=c*y+d，视频像素←世界像素）
→ 把动区按世界像素重采样 → 按周围一圈的底图逐通道线性配色 → 羽化叠回底图（边缘就是底图本身）
→ 常驻：找首尾最像的一段再交叉淡化成无缝循环；偶发：首尾各淡入淡出，开头结尾都等于底图
→ H.264 小视频 + anim.json（世界坐标、类型）。引擎把它整块盖在底图上即可，不用再做遮罩。
用法：python3 anim.py <帧目录根> <输出目录>   帧目录根下每段一个子目录 f001.png…（ffmpeg -fps_mode passthrough 抽出）"""
import os, sys, json, glob, subprocess
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reg2 import load, load_tile, orb_init, refine, WORLD

FPS = 24
FEATHER = 14          # 动区边缘向内羽化的世界像素
RING = 40             # 配准/配色用的外圈宽度
XFADE = 18            # 循环接缝交叉淡化帧数
MIN_LOOP = 96         # 循环至少 4 秒（雨短了能看出重复）
EVENT_FADE = 8        # 偶发片段首尾淡入淡出帧数
# 名字: (视频, 取景图世界 x0, [(动区名, 类型, 世界框 x0,y0,x1,y1), ...])
CLIPS = {
    'T1_客厅': (1640, [('鱼缸', 'loop', (1675, 570, 1845, 700)), ('阳台雨', 'loop', (2400, 255, 2565, 810))]),
    'T2_女生_写真窗': (560, [('女生雨窗', 'loop', (655, 240, 880, 660)), ('写真', 'event', (1300, 210, 1485, 485))]),
    'T3_男生_猫': (2640, [('黑猫', 'loop', (3040, 580, 3184, 712))]),
    'T4_男生_雨窗': (3280, [('男生雨窗', 'loop', (3340, 230, 3655, 600))]),
    'T5_女生_床幔': (0, [('床幔', 'loop', (300, 215, 600, 850))]),
}
FILE = {'鱼缸': 'fish', '阳台雨': 'balcony', '女生雨窗': 'girl_window', '写真': 'photo', '黑猫': 'cat',
        '男生雨窗': 'boy_window', '床幔': 'canopy'}   # 线上素材文件名（不用中文路径）
RATE = {   # 引擎里的播放速率：床幔摆得比要的大，放慢显得轻
    '床幔': 0.7,
}

def even(b):
    x0, y0, x1, y1 = b
    return (x0, y0, x0 + (x1 - x0) // 2 * 2, y0 + (y1 - y0) // 2 * 2)

def sample(vid, p, xs, ys, blur):
    if blur: vid = np.stack([gaussian_filter(vid[..., k], blur) for k in range(3)], -1)
    return np.stack([map_coordinates(vid[..., k], [p[2] * ys + p[3], p[0] * xs + p[1]], order=1, mode='nearest') for k in range(3)], -1)

SHARP_SIGMA = 1.2
def hf(a):
    g = a @ np.array([.299, .587, .114], np.float32)
    return (g - gaussian_filter(g, SHARP_SIGMA)).std()

def sharpen_amount(f0, base):
    """720p 视频放大后比底图软：找让首帧高频能量追平底图的反锐化强度（只补不减）。"""
    target = hf(base)
    for amt in np.arange(0, 2.01, 0.1):
        if hf(f0 + amt * (f0 - np.stack([gaussian_filter(f0[..., k], SHARP_SIGMA) for k in range(3)], -1))) >= target:
            return round(float(amt), 1)
    return 2.0

def best_loop(F, w):
    """F: 帧×H×W×3，w: 权重图。找 i<j、j-i≥MIN_LOOP、i≥XFADE 且 F[i-XFADE..i) 与 F[j-XFADE..j) 最像的一对。"""
    N = len(F); small = F[:, ::2, ::2].astype(np.float32); ws = w[::2, ::2, None]
    best = None
    for i in range(XFADE, N - MIN_LOOP + 1):
        for j in range(i + MIN_LOOP, N + 1):
            d = np.mean([(np.abs(small[i - XFADE + k] - small[j - XFADE + k]) * ws).mean() for k in range(0, XFADE, 3)])
            if best is None or d < best[0]: best = (d, i, j)
    return best

def build(frames_root, out):
    os.makedirs(out, exist_ok=True)
    world = np.asarray(Image.open(WORLD).convert('RGB')).astype(np.float32)
    meta = []
    for clip, (x0, zones) in CLIPS.items():
        fs = sorted(glob.glob(f'{frames_root}/{clip}/f*.png'))
        tile = load_tile(x0); v1 = load(fs[0])
        A = orb_init(tile, v1)[0].params; p0 = np.array([A[0, 0], A[0, 2], A[1, 1], A[1, 2]])
        vids = [load(f) for f in fs]
        for name, kind, box in zones:
            bx0, by0, bx1, by1 = even(box); a, c = bx0 - x0, bx1 - x0
            ring = np.zeros(tile.shape[:2], bool)
            ring[max(0, by0 - RING):by1 + RING, max(0, a - RING):min(960, c + RING)] = True; ring[by0:by1, a:c] = False
            p = refine(tile, v1, p0, ring)[0]
            blur = max(0.0, (p[0] - 1) * 0.5)          # 视频比世界清晰（镜头拉近）时先模糊再缩小，防锯齿
            ys, xs = np.mgrid[by0 - RING:by1 + RING, a - RING:c + RING].astype(np.float32)
            F = np.stack([sample(v, p, xs, ys, blur) for v in vids])           # 带外圈的动区帧
            B = world[by0 - RING:by1 + RING, bx0 - RING:bx1 + RING]
            rin = np.zeros(B.shape[:2], bool); rin[:, :] = True; rin[RING:-RING, RING:-RING] = False
            rin &= (B.sum(-1) > 0)
            # 逐帧逐通道把均值、对比度对齐到底图（整块：动区 + 外圈）：即梦越往后越发灰，只配首帧不够
            ok = B.sum(-1) > 0; bm, bs = B[ok].mean(0), B[ok].std(0)
            F = np.stack([(f - f[ok].mean(0)) * (bs / f[ok].std(0)) + bm for f in F])[:, RING:-RING, RING:-RING]
            B = B[RING:-RING, RING:-RING]
            amt = sharpen_amount(F[0], B)
            if amt: F = np.stack([f + amt * (f - np.stack([gaussian_filter(f[..., k], SHARP_SIGMA) for k in range(3)], -1)) for f in F])
            h, w = B.shape[:2]
            yy, xx = np.mgrid[0:h, 0:w]
            d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)).astype(np.float32)
            if bx0 == 0: d = np.minimum(np.minimum(w - 1 - xx, yy), h - 1 - yy).astype(np.float32)  # 贴世界左边不羽化
            m = np.clip(d / FEATHER, 0, 1)[..., None]; m = m * m * (3 - 2 * m)
            N = len(F)
            if kind == 'loop':
                dist, i, j = best_loop(F, m[..., 0]); L = j - i
                seq = []
                for k in range(L):
                    f = F[i + k]
                    if k >= L - XFADE:
                        t = (k - (L - XFADE) + 1) / (XFADE + 1); f = f * (1 - t) + F[i + k - L] * t
                    seq.append(f)
                info = f'loop {i}..{j} ({L / FPS:.2f}s) 接缝差 {dist:.2f}'
            else:
                seq = []
                for k in range(N):
                    t = min(1.0, k / EVENT_FADE, (N - 1 - k) / EVENT_FADE)
                    seq.append(F[k] * t + B * (1 - t))
                info = f'event {N / FPS:.2f}s'
            tmp = f'/tmp/anim_{name}'; os.makedirs(tmp, exist_ok=True)
            for f in glob.glob(tmp + '/*.png'): os.remove(f)
            for k, f in enumerate(seq):
                Image.fromarray(np.clip(f * m + B * (1 - m), 0, 255).astype(np.uint8)).save(f'{tmp}/{k:03d}.png')
            ff = os.environ.get('FFMPEG', 'ffmpeg')
            subprocess.run([ff, '-v', 'error', '-y', '-framerate', str(FPS), '-i', f'{tmp}/%03d.png', '-c:v', 'libx264',
                            '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'slow', '-movflags', '+faststart', '-an',
                            f'{out}/{FILE[name]}.mp4'], check=True)
            print(clip, name, f'p={np.round(p, 3).tolist()}', f'锐化 {amt}', info, f'{os.path.getsize(f"{out}/{FILE[name]}.mp4") // 1024}KB')
            meta.append({'name': name, 'kind': kind, 'x': bx0, 'y': by0, 'w': bx1 - bx0, 'h': by1 - by0, 'src': f'{FILE[name]}.mp4', 'rate': RATE.get(name, 1)})
    json.dump(meta, open(f'{out}/anim.json', 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
