"""档 4 在场循环视频：即梦首尾帧原片（纯色幕布，首尾帧 = video/<名>_loop/ 里那张参考图）→ 游戏用的透明循环 webm + 每帧量点。
用法：python3 video/make_loop.py <名> 原片.mp4        名 = truth / baisu / change / sister（ROLES）
  → web/assets/video/<名>_loop_alpha.webm + <名>_loop.json（cap 手上那件东西每帧偏移、beats 后坐时刻；crew.js LoopVideo 运行时读）

**每一帧都摆在立绘贴图的坐标系里**（放大 up 倍），所以游戏拿它直接顶替立绘画（crew.js drawOne：塞进同一个框），
foot / muzzle / head 这些量点一个都不用改。抠像、去溢色、外发光照各自立绘的出图脚本逐帧做（v14/truth/make2.py、v14/crewart.py）。

原片 → 原图（立绘的 src）：参考图是原图按 ref 摆进画布的（名义值），即梦出片再缩放平移 —— 第一帧跟参考图按剪影拟合（fit）。
head（有 face 的）：脸心那一块每帧相对第 0 帧挪了多少（立绘像素，模板匹配 ±30），头顶的天使环、头后的光轮跟着它。
cap：手上那件东西（真相女神的红罐盖、白娘子的水球、嫦娥的小月牙、绿茶妹妹的手机）在每帧相对第 0 帧挪了多少（立绘像素），喷口跟着它。
  hit：只在立绘 muzzle 附近一个窗里找（track.win，原片像素），颜色按 track.hit 判，取形心；
  tmpl：颜色跟周围分不开的（绿茶妹妹淡粉手机 vs 手），取第 0 帧 muzzle 周围 ±tmpl 像素做模板，每帧在 ±win 里按差的平方和找最像的位置。
beats（只有真相女神）：罐子往后猛震的时刻（罐盖一帧往回跳 > 8 立绘像素），游戏在这些时刻让喷口焰炸一下。
抠像之后、去毛边之前先 unmix（贴边 12 像素里"人和幕布混着"的按混合模型解开，飘发 / 动态模糊发梢的偏粉、偏橄榄）。
首尾接缝：最后 SEAM 帧往第 0 帧融（smoothstep），cap / head 一起收到 0。
deflame（只有真相女神）：即梦在每下后坐都自己画了 3~4 帧卡通火（提示词没要），游戏同一刻也炸喷口焰 → 两层火。
  出火的帧把罐口往外那半边（过罐盖中心、垂直罐轴的半平面）整块换成第 0 帧的，按罐身模板匹配的位移对齐：火、火星没了，罐盖还在。
"""
import os, sys, json, subprocess, tempfile
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageFilter
import imageio_ffmpeg
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../v14'))
import build, crewart

FF = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 24                                  # 即梦原片 24.06 fps（容器标 60，按 60 解码每帧重复 2~3 次）
V14 = os.path.join(HERE, '../v14')
SEAM = 6                                  # 首尾接缝融几帧（见 main）


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
    # face：脸心（立绘像素）—— 光环跟着它挪（视频里会转头、歪头）；只给头上顶着 / 头后挂着光环的人
    'truth': dict(ref='truth_loop/真相女神_循环_首尾帧.png', screen='magenta', face=(207, 122),
                  ref_of=lambda x, y: ((x + 88 - 202) * 0.86 + 243, (y + 32 - 42) * 0.86 + 207),
                  crop=(130, 28), K=0.4, size=(426, 654), up=1.5, cut=cut_truth, muzzle=(370, 334),
                  glow=[(21, 26, (255, 170, 40)), (9, 10, (255, 225, 120)), (3, 3, (255, 252, 220))],
                  track=dict(win=130, hit=lambda a: (a[..., 0] > 170) & (a[..., 1] < 80) & (a[..., 2] < 80)), beats=True,
                  deflame=dict(axis=(0.81, 0.58), back=24, body=(316, 292), xmin=300)),   # 罐轴朝右下 ~35°；罐身模板取罐盖后面的指示灯 / 银圈；她的腿在 x < 300（立绘）
    # 参考图 = v14/baisu/src1.png 原大放到 1600 方图 (173, 173)；抠像 / 光同 v14/baisu/make.py
    'baisu': dict(ref='baisu_loop/白娘子_循环_首尾帧.png', screen='magenta', src='baisu/src1.png', key=(12, 150), spill='all',
                  ref_of=lambda x, y: (x + 173, y + 173), K=0.6, size=(825, 800), up=1.0, muzzle=(732, 447),
                  glow=[(25, 30, (40, 130, 255)), (11, 12, (140, 210, 255)), (3, 3, (240, 250, 255))],
                  track=dict(win=90, hit=lambda a: (a[..., 2] > 180) & (a[..., 0] < 140) & (a[..., 2] - a[..., 0] > 80)), beats=False),
    # 参考图 = v14/change/src1_rgba.png 按 getbbox (0, 33) 裁、缩 0.9、放到 1200×1600 绿底 (143, 123)；抠像 / 光同 v14/change/make.py
    'change': dict(ref='change_loop/嫦娥_循环_首尾帧.png', screen='green', face=(451, 216), src='change/src1.png', key=(20, 150), spill='decyan',
                   ref_of=lambda x, y: (x * 0.9 + 143, (y - 33) * 0.9 + 123), K=0.6, size=(654, 948), up=1.0, muzzle=(581, 355),
                   glow=[(25, 30, (150, 180, 255)), (11, 12, (215, 228, 255)), (3, 3, (255, 255, 255))],
                   track=dict(win=60, hit=lambda a: a.min(-1) > 225), beats=False),
    # 参考图 = v14/sister/pose/P3a.png 抠出剪影（左上 (306, 13)）缩 0.9 放到 1200×1600 纯绿 (372, 151)；抠像 / 光同 v14/sister/make.py
    # spill 'all'（立绘是 'edge'）：原片压缩后发丝边上一圈不透明的暗绿点，只去半透明带去不掉；她身上没有绿，整张压 G ≤ max(R, B) 不伤颜色
    'sister': dict(ref='sister_loop/绿茶妹妹_循环_首尾帧.png', screen='green', src='sister/pose/P3a.png', key=(40, 150), spill='all',
                   ref_of=lambda x, y: ((x - 306) * 0.9 + 372, (y - 13) * 0.9 + 151), K=0.65, size=(425, 1032), up=1.0, muzzle=(73, 225),
                   glow=[(25, 30, (255, 150, 200)), (11, 12, (255, 215, 235)), (3, 3, (255, 255, 255))],
                   track=dict(tmpl=36, win=30), beats=False),   # 淡粉手机跟手的肤色分不开 → 按第 0 帧手机那块做模板匹配
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


def geom(R, fit):
    """输出（立绘 × up）像素 (u, v) ↔ 原片像素：原片 = (x0 + u·sx, y0 + v·sy)"""
    a, dx, dy = fit
    K, up, PAD = R['K'], R['up'], crewart.PAD
    vid = lambda x, y: tuple(v * a + d for v, d in zip(R['ref_of'](x, y), (dx, dy)))   # 原图 → 原片
    s2 = 1 / (up * K)
    ox, oy = R['crop'][0] - PAD / K, R['crop'][1] - PAD / K
    x0, y0 = vid(ox, oy); x1, _ = vid(ox + s2, oy); _, y1 = vid(ox, oy + s2)
    return x0, y0, x1 - x0, y1 - y0


def track_tmpl(R, fit, paths, pt=None, T=None, W=None):
    """模板匹配跟踪：返回每帧 pt（默认 muzzle，立绘像素）那一块的位置（立绘 1 倍像素）"""
    x0, y0, sx, sy = geom(R, fit)
    up = R['up']
    T, W = T or R['track']['tmpl'], W or R['track']['win']
    mx, my = pt or R['muzzle']
    cx, cy = int(round(x0 + mx * up * sx)), int(round(y0 + my * up * sy))
    load = lambda p: np.array(Image.open(p).convert('L')).astype(np.float32)
    t = load(paths[0])[cy - T:cy + T + 1, cx - T:cx + T + 1]
    out = []
    for p in paths:
        g = load(p)
        best = None
        for dy in range(-W, W + 1):
            for dx in range(-W, W + 1):
                c = g[cy + dy - T:cy + dy + T + 1, cx + dx - T:cx + dx + T + 1]
                e = ((c - t) ** 2).sum()
                if best is None or e < best[0]:
                    best = (e, dx, dy)
        out.append(((cx + best[1] - x0) / sx / up, (cy + best[2] - y0) / sy / up))
    return out


def unmix(rgb, al, path, band=12, res_max=0.2):
    """贴边 band 像素里"人和幕布混着"的像素按混合模型解开（2026-10-04：真相女神后坐时被吹散的发梢整片偏粉、绿茶妹妹飘发偏橄榄）。
    即梦把飘动的发丝画成动态模糊的半透明，又经 4:2:0 压缩，细发整根混进了幕布色；键按色差抠，这些像素几乎不透明，
    去溢色只削掉"比幕布更偏"的那份（品红幕 min(R, B) − G > 0），奶金发混进两成品红只是 G 低了十几，判不出来。
    观测色 C = α·F + (1 − α)·M（M 幕布色取原片透明区中位数，F 从里面 band 像素外的干净颜色扩出来）：
    α = (C − M)·(F − M) / |F − M|²；只解落在 M—F 连线附近的（离线距离 / |F − M| < res_max）——头发的深色描边、手机和头发交界这类
    "本来就是另一种颜色"的不在线上，不动（放到 0.3 手机边、肩膀会过冲出品红描边）。解开的颜色 = M + (C − M) / α，α 太小（< 0.25）直接用 F。"""
    a = np.array(Image.open(path).convert('RGB')).astype(np.float32)
    body = al > 0.05
    Mc = np.median(a[al < 0.01], 0)
    inner = ndimage.binary_erosion(body, iterations=band)
    F = crewart.edge_extend(rgb.copy(), inner.astype(np.float32), it=band + 30)
    d, c = F - Mc, a - Mc
    dd = np.maximum((d * d).sum(-1), 1)
    au = (c * d).sum(-1) / dd
    res = np.sqrt(((c - au[..., None] * d) ** 2).sum(-1) / dd)
    m = body & ~inner & (au < 0.98) & (res < res_max)
    est = np.where((au > 0.25)[..., None], np.clip(Mc + c / np.maximum(au, 0.25)[..., None], 0, 255), F)
    rgb[m] = est[m]
    return rgb, np.where(m, np.minimum(al, np.clip(au, 0, 1)), al)


def defringe(rgb, al, path, screen):
    """轮廓外沿去毛边（2026-10-04 用户："绿茶妹妹特效周围一圈好像有明显的毛边"，四条都有）。
    原片是 h264 4:2:0，压缩把幕布色往人里面晕进三四像素；按键抠出来这些混色像素几乎不透明，去溢色只削掉多出来的那份绿 / 品红，
    剩下缺蓝（绿幕 → 发黄）或缺绿（品红幕 → 发灰紫）—— 一圈 1~2 像素的暗黄 / 灰紫点线。
    染没染按**原片**颜色判：离透明区 5 像素以内、原片里有一丁点偏幕布色（绿幕 G − max(R, B) > 0，品红幕 min(R, B) − G > 0；奶白被绿晕进去 4 个色阶就已经发黄）的算染了，
    再加贴着透明区的最外 2 像素；它们（连同外面全透明的那片）颜色换成从里面干净像素扩出来的颜色，最外一像素 alpha 再软一半。
    不按"半透明"挑：白娘子 / 嫦娥的薄纱整片都半透明，那是真颜色。"""
    a = np.array(Image.open(path).convert('RGB')).astype(np.int16)
    k = a[..., 1] - np.maximum(a[..., 0], a[..., 2]) if screen == 'green' else np.minimum(a[..., 0], a[..., 2]) - a[..., 1]
    body = al > 0.05
    near = body & ~ndimage.binary_erosion(body, iterations=5)
    bad = (near & (k > 0)) | (body & ~ndimage.binary_erosion(body, iterations=2))
    clean = body & ~bad
    rgb2 = crewart.edge_extend(rgb.copy(), clean.astype(np.float32), it=30)   # 30：飘出去的细发丝整根都是混色，要从头发里一路扩过去
    rgb[~clean] = rgb2[~clean]          # 外面全透明的那片也换：摆进立绘坐标时双三次插值会把它们的颜色混回边上
    outer = body & ~ndimage.binary_erosion(body, iterations=1)
    return rgb, np.where(outer, al * 0.5, al)


def deflame(R, fit, paths):
    """把原片里出火的帧就地改掉（见文件头 deflame）。返回改了哪些帧"""
    D = R['deflame']
    x0, y0, sx, sy = geom(R, fit)
    up = R['up']
    raw = lambda x, y: (x0 + x * up * sx, y0 + y * up * sy)
    ux, uy = D['axis']
    px, py = raw(R['muzzle'][0] - ux * D['back'], R['muzzle'][1] - uy * D['back'])
    xmin = raw(D['xmin'], 0)[0]
    pos = track_tmpl(R, fit, paths, D['body'], 30, 24)       # 罐身每帧在哪（立绘像素）
    f0 = np.array(Image.open(paths[0]).convert('RGB'))
    h, w = f0.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    done = []
    for i, p in enumerate(paths):
        dx, dy = (pos[i][0] - pos[0][0]) * up * sx, (pos[i][1] - pos[0][1]) * up * sy
        Z = ((xx - px - dx) * ux + (yy - py - dy) * uy > 0) & (xx > xmin)
        a = np.array(Image.open(p).convert('RGB'))
        r, g, b = (a[..., c].astype(int) for c in range(3))
        sh = np.array(Image.fromarray(f0).transform((w, h), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), Image.BICUBIC, fillcolor=tuple(int(v) for v in f0[0, -1])))   # 移出来的边补幕布色
        s0 = sh.astype(int)
        empty = ~ndimage.binary_dilation(s0[..., 1] >= 90, iterations=6)   # 第 0 帧这里是幕布、离罐盖 6 像素外（罐盖边上的亮红高光不算火）
        fire = Z & empty & (r > 180) & (g > 90) & (b < 200) & (r - b > 60) & (g - b > 25)   # 橙、黄、奶白的火芯（罐盖的粉红高光 g ≈ b 不算）
        if fire.sum() < 40:
            continue
        a[Z] = sh[Z]
        Image.fromarray(a).save(p)
        done.append(i)
    return done


def frame_job(args):
    name, i, path, fit, tmp = args
    R = setup(name)
    rgb, al = defringe(*unmix(*R['cut'](path), path), path, R['screen'])
    px = np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8)
    src = Image.fromarray(px, 'RGBA')
    up = R['up']
    # 输出（立绘 × up）像素 → 原图 → 原片，PIL AFFINE 要的就是输出 → 输入
    W, H = round(R['size'][0] * up), round(R['size'][1] * up)
    x0, y0, sx, sy = geom(R, fit)
    x1, y1 = x0 + sx, y0 + sy
    body = src.transform((W, H), Image.AFFINE, (sx, 0, x0, 0, sy, y0), Image.BICUBIC)
    out = Image.new('RGBA', (W, H))
    sil = body.split()[3]
    odd = lambda v: round(v) | 1
    for grow, blur, c in R['glow']:
        L = Image.new('RGBA', (W, H), c + (0,))
        L.putalpha(sil.filter(ImageFilter.MaxFilter(odd(grow * up))).filter(ImageFilter.GaussianBlur(blur * up)))
        out.alpha_composite(L)
    out.alpha_composite(body)
    out.save(os.path.join(tmp, '%04d.png' % i))
    if 'hit' not in R['track']:
        return i, None
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
    if 'deflame' in R:
        print('deflame frames', deflame(R, (a, dx, dy), [os.path.join(raw, f) for f in frames]))
    with ProcessPoolExecutor() as ex:
        res = dict(ex.map(frame_job, [(name, i, os.path.join(raw, f), (a, dx, dy), tmp) for i, f in enumerate(frames)]))
    if 'tmpl' in R['track']:
        res = dict(enumerate(track_tmpl(R, (a, dx, dy), [os.path.join(raw, f) for f in frames])))
    miss = [i for i in range(len(frames)) if res[i] is None]
    for i in range(len(frames)):           # 偶尔一帧没找到（被袖子挡住 / 光太淡）：沿用前一帧
        if res[i] is None:
            res[i] = res[i - 1] if i else next(v for v in res.values() if v)
    cap = np.array([res[i] for i in range(len(frames))])
    off = cap - cap[0]
    head = None
    if 'face' in R:
        h = np.array(track_tmpl(R, (a, dx, dy), [os.path.join(raw, f) for f in frames], R['face'], 40, 30))
        # 模板匹配按原片整像素跳（立绘里一步 ~1 像素），逐帧直接用光环会抖：5 帧滑动平均，首尾按循环接（视频本来就首尾相接）
        n = len(h); ker = np.ones(5) / 5
        h = np.stack([np.convolve(np.concatenate([h[-2:, c], h[:, c], h[:2, c]]), ker, 'valid') for c in range(2)], -1)[:n]
        head = h - h[0]
        print('head max off', np.abs(head).max(0).round(1))
    beats = []
    if R['beats']:
        jump = -(off[1:, 0] - off[:-1, 0])
        for i in np.nonzero(jump > 8)[0]:      # 一下后坐可能分两帧跳完（3.125 / 3.167），隔不到 0.3 秒的算同一下
            t = round(float(i + 1) / FPS, 3)
            if not beats or t - beats[-1] > 0.3:
                beats.append(t)
    print('frames', len(frames), 'track miss', len(miss), 'cap0 (sprite px)', cap[0].round(1), 'vs muzzle', R['muzzle'],
          'max off', np.abs(off).max(0).round(1), 'beats', beats)
    # 首尾接缝：即梦的尾帧只是"接近"首帧（白娘子 / 嫦娥尾→首一跳是平常每帧的两倍，循环时一顿）。
    # 最后 SEAM 帧按 smoothstep 往第 0 帧融（预乘 alpha 混，免得半透明边发黑），cap / head 同样往 0 收
    n = len(frames)
    f0 = np.array(Image.open(os.path.join(tmp, '0000.png'))).astype(np.float32) / 255
    pm = lambda f: np.dstack([f[..., :3] * f[..., 3:], f[..., 3:]])
    for j in range(SEAM):
        i = n - SEAM + j
        w = (j + 1) / (SEAM + 1); w = w * w * (3 - 2 * w)
        p = os.path.join(tmp, '%04d.png' % i)
        f = pm(np.array(Image.open(p)).astype(np.float32) / 255) * (1 - w) + pm(f0) * w
        al = f[..., 3:]
        Image.fromarray(np.dstack([f[..., :3] / np.maximum(al, 1e-4), al]).clip(0, 1).__mul__(255).round().astype(np.uint8), 'RGBA').save(p)
        off[i] *= 1 - w
        if head is not None:
            head[i] *= 1 - w
    subprocess.run([FF, '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(tmp, '%04d.png'),
                    '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '26',
                    '-row-mt', '1', '-deadline', 'good', '-cpu-used', '2', '-auto-alt-ref', '0', out], check=True)
    W, H = round(R['size'][0] * R['up']), round(R['size'][1] * R['up'])
    json.dump({'fps': FPS, 'frames': len(frames), 'size': [W, H], 'fit': [round(iou, 4), a, dx, dy],
               'beats': beats, 'cap': [[round(float(x), 1), round(float(y), 1)] for x, y in off],
               **({'head': [[round(float(x), 1), round(float(y), 1)] for x, y in head]} if head is not None else {})},
              open(out.replace('_alpha.webm', '.json'), 'w'), separators=(',', ':'))
    print('tmp', tmp, 'out', out, os.path.getsize(out))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
