"""真相女神在场循环视频：即梦原片（品红底，首尾帧 = 真相女神_循环_首尾帧.png）→ 游戏用的透明循环 webm + 每帧量点。
用法：python3 video/truth_loop/make_loop.py 原片.mp4
  → web/assets/video/truth_loop_alpha.webm + truth_loop.json（beats、罐口每帧偏移；crew.js LoopVideo 运行时读）

**每一帧都摆在立绘 truth2_up.webp 的坐标系里**（放大 UP 倍：立绘 K=0.4，原片里人是原图的 ~0.6 倍，UP=1.5 正好不丢细节），
所以游戏里拿它直接顶替立绘画（crew.js drawOne：put 进同一个框），foot / muzzle / head / chest 这些量点一个都不用改。
外发光照 v14/truth/make2.py 一样逐帧烘（核和模糊半径 × UP）。

原片 → 原图 src2.png 的换算：参考图是 src2 往右下挪 (88, 32) 补成 1200×1600，再裁 (202, 42) 起、缩 0.86、放到 (243, 207)
（第二版参考图，头顶留边），即梦按 834 宽出片 —— 这串是名义值，第一帧跟参考图按剪影再拟合一次缩放和平移（fit）。

beats：罐子往后猛震的时刻（罐口在原片里一帧往回跳 > 12 像素），游戏在这些时刻给喷口焰炸一下、重开一段"呲——"。
cap：每帧罐口（红盖子的红色部分形心）相对第一帧挪了多少（立绘像素），喷雾的出口跟着它。
"""
import os, sys, json, subprocess, tempfile
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageFilter
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../v14'))
from build import cutout, edge_extend
sys.path.insert(0, os.path.join(HERE, '../../v14/truth'))

FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT = os.path.join(HERE, '../../web/assets/video/truth_loop_alpha.webm')
REF = os.path.join(HERE, '真相女神_循环_首尾帧.png')
FPS = 24                                  # 即梦原片 24.06 fps（容器标 60，按 60 解码每帧重复 2~3 次）
UP = 1.5
# 立绘（make2.py）
CROP0, K, PAD, SIZE = (130, 28), 0.4, 44, (426, 654)
GLOW = [(21, 26, (255, 170, 40)), (9, 10, (255, 225, 120)), (3, 3, (255, 252, 220))]
MUZZLE_SPR = (370, 334)                   # crew.js TRUTH.spr.muzzle


def odd(v):
    v = round(v)
    return v if v % 2 else v + 1


def ref_to_video(fit):
    """src2 像素 → 原片像素"""
    a, dx, dy = fit
    def f(x, y):
        x2 = (x + 88 - 202) * 0.86 + 243
        y2 = (y + 32 - 42) * 0.86 + 207
        return x2 * a + dx, y2 * a + dy
    return f


def fit_first(frame0):
    """第一帧剪影 vs 参考图剪影：缩放 a、平移 (dx, dy) 网格搜，取 IoU 最大"""
    _, al = cutout(frame0)
    ref = np.array(Image.open(REF).convert('RGB')).astype(np.int16)
    _, ar = cutout(ref)
    m = al > 0.5
    best = None
    for a in np.arange(0.680, 0.712, 0.002):
        r = Image.fromarray((ar * 255).astype(np.uint8)).resize((round(1200 * a), round(1600 * a)), Image.BILINEAR)
        r = np.array(r) > 127
        h, w = m.shape
        for dy in range(-8, 9):
            for dx in range(-8, 9):
                c = np.zeros_like(m)
                ys0, xs0 = max(0, dy), max(0, dx)
                sub = r[ys0 - dy:ys0 - dy + h - ys0, xs0 - dx:xs0 - dx + w - xs0]
                c[ys0:ys0 + sub.shape[0], xs0:xs0 + sub.shape[1]] = sub
                iou = (m & c).sum() / (m | c).sum()
                if not best or iou > best[0]:
                    best = (iou, float(a), dx, dy)
    return best


def frame_job(args):
    i, path, fit, tmp = args
    a = np.array(Image.open(path).convert('RGB')).astype(np.int16)
    rgb, al = cutout(a)
    sp = np.clip(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1], 0, None) * (al < 0.99)   # 同 make2.py 去品红溢色
    rgb[..., 0] -= sp; rgb[..., 2] -= sp
    rgb = edge_extend(rgb, al)
    px = np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8)
    src = Image.fromarray(px, 'RGBA')
    # 输出（立绘 × UP）像素 → src2 → 原片，PIL AFFINE 要的就是输出 → 输入
    f = ref_to_video(fit)
    W, H = round(SIZE[0] * UP), round(SIZE[1] * UP)
    s2 = 1 / (UP * K)                     # 输出 1 像素 = 原图几像素
    ox, oy = CROP0[0] - PAD / K, CROP0[1] - PAD / K
    x0, y0 = f(ox, oy); x1, _ = f(ox + s2, oy); _, y1 = f(ox, oy + s2)
    body = src.transform((W, H), Image.AFFINE, (x1 - x0, 0, x0, 0, y1 - y0, y0), Image.BICUBIC)
    out = Image.new('RGBA', (W, H))
    sil = body.split()[3]
    for grow, blur, c in GLOW:
        L = Image.new('RGBA', (W, H), c + (0,))
        L.putalpha(sil.filter(ImageFilter.MaxFilter(odd(grow * UP))).filter(ImageFilter.GaussianBlur(blur * UP)))
        out.alpha_composite(L)
    out.alpha_composite(body)
    out.save(os.path.join(tmp, '%04d.png' % i))
    # 罐口：红盖子（右半边、偏下）的红色形心，换回立绘 1 倍像素
    red = (a[..., 0] > 170) & (a[..., 1] < 80) & (a[..., 2] < 80)
    red[:, :a.shape[1] // 2] = False; red[:a.shape[0] // 4] = False
    ys, xs = np.nonzero(red)
    cx, cy = xs.mean(), ys.mean()
    return i, ((cx - x0) / (x1 - x0) / UP, (cy - y0) / (y1 - y0) / UP)


def main(src):
    tmp = tempfile.mkdtemp(prefix='truthloop_')
    raw = os.path.join(tmp, 'raw'); os.makedirs(raw)
    subprocess.run([FF, '-v', 'error', '-y', '-i', src, '-vf', f'fps={FPS}', os.path.join(raw, '%04d.png')], check=True)
    frames = sorted(os.listdir(raw))
    iou, a, dx, dy = fit_first(np.array(Image.open(os.path.join(raw, frames[0])).convert('RGB')).astype(np.int16))
    print('fit first frame: IoU %.4f  scale %.3f  shift (%d, %d)' % (iou, a, dx, dy))
    fit = (a, dx, dy)
    with ProcessPoolExecutor() as ex:
        res = dict(ex.map(frame_job, [(i, os.path.join(raw, f), fit, tmp) for i, f in enumerate(frames)]))
    cap = np.array([res[i] for i in range(len(frames))])
    off = cap - cap[0]
    # 后坐：原片里罐口一帧往回（左上）跳 > 12 原片像素 ≈ 8 立绘像素
    jump = -(off[1:, 0] - off[:-1, 0])
    beats = []
    for i in np.nonzero(jump > 8)[0]:          # 一下后坐可能分两帧跳完（3.125 / 3.167），隔不到 0.3 秒的算同一下
        t = round(float(i + 1) / FPS, 3)
        if not beats or t - beats[-1] > 0.3:
            beats.append(t)
    print('frames', len(frames), 'cap0 (sprite px)', cap[0].round(1), 'vs spr.muzzle', MUZZLE_SPR, 'beats', beats)
    subprocess.run([FF, '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(tmp, '%04d.png'),
                    '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '26',
                    '-row-mt', '1', '-deadline', 'good', '-cpu-used', '2', '-auto-alt-ref', '0', OUT], check=True)
    json.dump({'fps': FPS, 'frames': len(frames), 'size': [round(SIZE[0] * UP), round(SIZE[1] * UP)], 'fit': [round(float(iou), 4), a, dx, dy],
               'beats': beats, 'cap': [[round(float(x), 1), round(float(y), 1)] for x, y in off]},
              open(OUT.replace('_alpha.webm', '.json'), 'w'), separators=(',', ':'))
    print('tmp', tmp, 'out', OUT, os.path.getsize(OUT))


if __name__ == '__main__':
    main(sys.argv[1])
