"""档 4 在场循环视频：即梦首尾帧原片（纯色幕布，首尾帧 = video/<名>_loop/ 里那张参考图）→ 游戏用的透明循环 webm + 每帧量点。
用法：python3 video/make_loop.py <名> 原片.mp4        名 = truth / baisu / change / sister（ROLES）
  → web/assets/video/<名>_loop_alpha.webm + <名>_loop.json（cap 手上那件东西每帧偏移、beats 后坐时刻；crew.js LoopVideo 运行时读）

**每一帧都摆在立绘贴图的坐标系里**（放大 up 倍），所以游戏拿它直接顶替立绘画（crew.js drawOne：塞进同一个框），
foot / muzzle / head 这些量点一个都不用改。抠像、去溢色、外发光照各自立绘的出图脚本逐帧做（v14/truth/make2.py、v14/crewart.py）。

原片 → 原图（立绘的 src）：参考图是原图按 ref 摆进画布的（名义值），即梦出片再缩放平移 —— 第一帧跟参考图按剪影拟合（fit）。
cap：手上那件东西（真相女神的红罐盖、白娘子的水球、嫦娥的小月牙）在每帧的形心相对第 0 帧挪了多少（立绘像素），喷口跟着它。
  只在立绘 muzzle 附近一个窗里找（track.win，原片像素），颜色按 track.hit 判。
beats（只有真相女神）：罐子往后猛震的时刻（罐盖一帧往回跳 > 8 立绘像素），游戏在这些时刻让喷口焰炸一下。
"""
import os, sys, json, subprocess, tempfile
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageFilter
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../v14'))
import build, crewart

FF = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 24                                  # 即梦原片 24.06 fps（容器标 60，按 60 解码每帧重复 2~3 次）
V14 = os.path.join(HERE, '../v14')


def cut_truth(path):
    """同 v14/truth/make2.py：build.cutout + 半透明带去品红溢色"""
    rgb, al = build.cutout(path)
    sp = np.clip(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1], 0, None) * (al < 0.99)
    rgb[..., 0] -= sp; rgb[..., 2] -= sp
    return build.edge_extend(rgb, al), al


def crop_of(src, screen, key, spill, margin=6):
    """crewart.make 的自动裁边框左上角（原图像素）"""
    _, al = crewart.cut(src, screen, key, (), spill)
    ys, xs = np.nonzero(al > 0.05)
    return max(0, xs.min() - margin), max(0, ys.min() - margin)


ROLES = {
    # 参考图 = src2 往右下挪 (88, 32) 补成 1200×1600，再裁 (202, 42) 起、缩 0.86、放到 (243, 207)
    'truth': dict(ref='truth_loop/真相女神_循环_首尾帧.png', screen='magenta',
                  ref_of=lambda x, y: ((x + 88 - 202) * 0.86 + 243, (y + 32 - 42) * 0.86 + 207),
                  crop=(130, 28), K=0.4, size=(426, 654), up=1.5, cut=cut_truth, muzzle=(370, 334),
                  glow=[(21, 26, (255, 170, 40)), (9, 10, (255, 225, 120)), (3, 3, (255, 252, 220))],
                  track=dict(win=130, hit=lambda a: (a[..., 0] > 170) & (a[..., 1] < 80) & (a[..., 2] < 80)), beats=True),
    # 参考图 = v14/baisu/src1.png 原大放到 1600 方图 (173, 173)；抠像 / 光同 v14/baisu/make.py
    'baisu': dict(ref='baisu_loop/白娘子_循环_首尾帧.png', screen='magenta', src='baisu/src1.png', key=(12, 150), spill='all',
                  ref_of=lambda x, y: (x + 173, y + 173), K=0.6, size=(825, 800), up=1.0, muzzle=(732, 447),
                  glow=[(25, 30, (40, 130, 255)), (11, 12, (140, 210, 255)), (3, 3, (240, 250, 255))],
                  track=dict(win=90, hit=lambda a: (a[..., 2] > 180) & (a[..., 0] < 140) & (a[..., 2] - a[..., 0] > 80)), beats=False),
    # 参考图 = v14/change/src1_rgba.png 按 getbbox (0, 33) 裁、缩 0.9、放到 1200×1600 绿底 (143, 123)；抠像 / 光同 v14/change/make.py
    'change': dict(ref='change_loop/嫦娥_循环_首尾帧.png', screen='green', src='change/src1.png', key=(20, 150), spill='decyan',
                   ref_of=lambda x, y: (x * 0.9 + 143, (y - 33) * 0.9 + 123), K=0.6, size=(654, 948), up=1.0, muzzle=(581, 355),
                   glow=[(25, 30, (150, 180, 255)), (11, 12, (215, 228, 255)), (3, 3, (255, 255, 255))],
                   track=dict(win=60, hit=lambda a: a.min(-1) > 225), beats=False),
    # 参考图 = v14/sister/pose/P3a.png 抠出剪影（左上 (306, 13)）缩 0.9 放到 1200×1600 纯绿 (372, 151)；抠像 / 光同 v14/sister/make.py
    'sister': dict(ref='sister_loop/绿茶妹妹_循环_首尾帧.png', screen='green', src='sister/pose/P3a.png', key=(40, 150), spill='edge',
                   ref_of=lambda x, y: ((x - 306) * 0.9 + 372, (y - 13) * 0.9 + 151), K=0.65, size=(425, 1032), up=1.0, muzzle=(73, 225),
                   glow=[(25, 30, (255, 150, 200)), (11, 12, (255, 215, 235)), (3, 3, (255, 255, 255))],
                   track=dict(win=70, hit=lambda a: (a[..., 0] > 200) & (a[..., 1] > 110) & (a[..., 1] < 185) & (a[..., 2] > 150) & (a[..., 2] - a[..., 1] > 15)), beats=False),
}


def setup(name):
    R = dict(ROLES[name])
    if 'crop' not in R:
        R['crop'] = crop_of(os.path.join(V14, R['src']), R['screen'], R['key'], R['spill'])
    if 'cut' not in R:
        def cut(path, R=R):
            rgb, al = crewart.cut(path, R['screen'], R['key'], (), R['spill'])
            return crewart.edge_extend(rgb, al), al
        R['cut'] = cut
    return R


def fit_first(R, path0):
    """第一帧剪影 vs 参考图剪影：缩放 a、平移 (dx, dy) 网格搜，取 IoU 最大"""
    _, al = R['cut'](path0)
    _, ar = R['cut'](os.path.join(HERE, R['ref']))
    m = al > 0.5
    h, w = m.shape
    a0 = w / ar.shape[1]                   # 名义：即梦按参考图等比出片
    best = None
    for a in a0 * np.arange(0.97, 1.031, 0.003):
        r = Image.fromarray((ar * 255).astype(np.uint8)).resize((round(ar.shape[1] * a), round(ar.shape[0] * a)), Image.BILINEAR)
        r = np.array(r) > 127
        for dy in range(-12, 13, 2):
            for dx in range(-12, 13, 2):
                c = np.zeros_like(m)
                ys0, xs0 = max(0, dy), max(0, dx)
                sub = r[ys0 - dy:ys0 - dy + h - ys0, xs0 - dx:xs0 - dx + w - xs0]
                c[ys0:ys0 + sub.shape[0], xs0:xs0 + sub.shape[1]] = sub
                iou = (m & c).sum() / (m | c).sum()
                if not best or iou > best[0]:
                    best = (float(iou), float(a), dx, dy)
    return best


def frame_job(args):
    name, i, path, fit, tmp = args
    R = setup(name)
    rgb, al = R['cut'](path)
    px = np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8)
    src = Image.fromarray(px, 'RGBA')
    a, dx, dy = fit
    K, up, PAD = R['K'], R['up'], crewart.PAD
    vid = lambda x, y: tuple(v * a + d for v, d in zip(R['ref_of'](x, y), (dx, dy)))   # 原图 → 原片
    # 输出（立绘 × up）像素 → 原图 → 原片，PIL AFFINE 要的就是输出 → 输入
    W, H = round(R['size'][0] * up), round(R['size'][1] * up)
    s2 = 1 / (up * K)
    ox, oy = R['crop'][0] - PAD / K, R['crop'][1] - PAD / K
    x0, y0 = vid(ox, oy); x1, _ = vid(ox + s2, oy); _, y1 = vid(ox, oy + s2)
    body = src.transform((W, H), Image.AFFINE, (x1 - x0, 0, x0, 0, y1 - y0, y0), Image.BICUBIC)
    out = Image.new('RGBA', (W, H))
    sil = body.split()[3]
    odd = lambda v: round(v) | 1
    for grow, blur, c in R['glow']:
        L = Image.new('RGBA', (W, H), c + (0,))
        L.putalpha(sil.filter(ImageFilter.MaxFilter(odd(grow * up))).filter(ImageFilter.GaussianBlur(blur * up)))
        out.alpha_composite(L)
    out.alpha_composite(body)
    out.save(os.path.join(tmp, '%04d.png' % i))
    # 手上那件东西：立绘 muzzle 换到原片，周围 win 像素里按颜色找形心，换回立绘 1 倍像素
    raw = np.array(Image.open(path).convert('RGB')).astype(np.int16)
    mx, my = R['muzzle']
    cx, cy = x0 + (mx * up) * (x1 - x0), y0 + (my * up) * (y1 - y0)
    win = R['track']['win']
    X0, Y0 = int(max(0, cx - win)), int(max(0, cy - win))
    hit = R['track']['hit'](raw[Y0:int(cy + win), X0:int(cx + win)])
    ys, xs = np.nonzero(hit)
    if len(xs) < 20:
        return i, None
    px_, py_ = xs.mean() + X0, ys.mean() + Y0
    return i, ((px_ - x0) / (x1 - x0) / up, (py_ - y0) / (y1 - y0) / up)


def main(name, src):
    R = setup(name)
    out = os.path.join(HERE, f'../web/assets/video/{name}_loop_alpha.webm')
    tmp = tempfile.mkdtemp(prefix=f'{name}loop_')
    raw = os.path.join(tmp, 'raw'); os.makedirs(raw)
    subprocess.run([FF, '-v', 'error', '-y', '-i', src, '-vf', f'fps={FPS}', os.path.join(raw, '%04d.png')], check=True)
    frames = sorted(os.listdir(raw))
    iou, a, dx, dy = fit_first(R, os.path.join(raw, frames[0]))
    print('fit first frame: IoU %.4f  scale %.4f  shift (%d, %d)' % (iou, a, dx, dy))
    with ProcessPoolExecutor() as ex:
        res = dict(ex.map(frame_job, [(name, i, os.path.join(raw, f), (a, dx, dy), tmp) for i, f in enumerate(frames)]))
    miss = [i for i in range(len(frames)) if res[i] is None]
    for i in range(len(frames)):           # 偶尔一帧没找到（被袖子挡住 / 光太淡）：沿用前一帧
        if res[i] is None:
            res[i] = res[i - 1] if i else next(v for v in res.values() if v)
    cap = np.array([res[i] for i in range(len(frames))])
    off = cap - cap[0]
    beats = []
    if R['beats']:
        jump = -(off[1:, 0] - off[:-1, 0])
        for i in np.nonzero(jump > 8)[0]:      # 一下后坐可能分两帧跳完（3.125 / 3.167），隔不到 0.3 秒的算同一下
            t = round(float(i + 1) / FPS, 3)
            if not beats or t - beats[-1] > 0.3:
                beats.append(t)
    print('frames', len(frames), 'track miss', len(miss), 'cap0 (sprite px)', cap[0].round(1), 'vs muzzle', R['muzzle'],
          'max off', np.abs(off).max(0).round(1), 'beats', beats)
    subprocess.run([FF, '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(tmp, '%04d.png'),
                    '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '26',
                    '-row-mt', '1', '-deadline', 'good', '-cpu-used', '2', '-auto-alt-ref', '0', out], check=True)
    W, H = round(R['size'][0] * R['up']), round(R['size'][1] * R['up'])
    json.dump({'fps': FPS, 'frames': len(frames), 'size': [W, H], 'fit': [round(iou, 4), a, dx, dy],
               'beats': beats, 'cap': [[round(float(x), 1), round(float(y), 1)] for x, y in off]},
              open(out.replace('_alpha.webm', '.json'), 'w'), separators=(',', ':'))
    print('tmp', tmp, 'out', out, os.path.getsize(out))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
