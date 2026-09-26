"""手臂缩短（2026-09-26，用户："拉扯时手臂会莫名其妙拉很长，看着非常不自然"）。

## 为什么不重新生图

关键姿势每张都挂着 8 格步态（f1~f7 是拿 base 局部重绘腿得来的），重画一张 base 就得把它那 7 格
全部重做。这里走纯几何：**手和手机不动，人整体朝手机平移 d，手臂那一段沿横向压短 d**。
同一套参数对 base 和它的 7 格步态逐像素做同样的事，步态格的腿跟着人一起平移，上半身仍然和 base 一模一样。

## 怎么切

每个人一条"手臂带"：肩点 S 到拳头 F 的连线，上下各 HALF 像素。
- 带内、横坐标在 S.x 与 F.x 之间 → 按列压缩：S 端跟身体一起走 d，F 端不动，中间线性插值；
- 带内、比 F.x 更靠手机 → 拳头，不动；
- 其余前景按连通块归属：质心在手机左边的是女生（+d），右边的是男生（-d），被带子切下的手机/拳头块不动。
压缩只在横向做，竖直方向一行不动，所以肩膀和拳头的高度都不变。

## 目标长度

量的是肩关节到拳心（原图 1536×1024 像素）。女生 aF/bF/bL 约 290~300、男生 bF/bL/aK 约 255~290，
这几张看着自然，就按女生 300、男生 280 定。长出来的才缩，本来就短的（女生 nL2 245）不拉长。
"""
import os, sys, json
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HALF = 58          # 手臂带半宽：两条胳膊一上一下，都要包进去
FIST = 30          # 拳头往回留多少不压（拳头本身压扁了读成鸡爪）

# 每张：a = 女生、b = 男生，(压缩起点 x, 该处手臂 y, 拳 x, 拳 y, d)。d = 缩短量（原图像素），0 = 不动。
# 压缩起点不是肩膀，是**脸的前方**：手臂带在肩膀那头会扫到下巴，从肩膀就开始压，下巴被撕开、嘴歪
# （n0 女生第一版就是这样）。肩到脸前那一段跟身体一起平移，只压脸前方到拳头这一截。
CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cfg.json')))

SRC = {'n0': 'loop/n0.png', 'nL1': 'loop/nL1.png', 'nL2': 'loop/nL2.png', 'nR1': 'loop/nR1.png', 'nR2': 'loop/nR2.png',
       'aK': 'pose/21_女优_男跪.png', 'aF': 'pose/22_女优_男扑倒.png', 'aL': 'pose/23_女优_男趴.png',
       'bK': 'pose/24_男优_女跪.png', 'bF': 'pose/25_男优_女扑倒.png', 'bL': 'pose/26_男优_女趴.png'}
MAGENTA = np.array([252, 3, 250], np.float32)


def keyed(a):
    return np.minimum(a[..., 0], a[..., 2]) - a[..., 1]


def band(shape, sx, sy, fx, fy):
    """肩→拳连线上下 HALF 的带子（按竖直距离量，胳膊是斜的也照样包住）"""
    H, W = shape
    yy, xx = np.mgrid[0:H, 0:W]
    t = (xx - sx) / (fx - sx)
    ly = sy + t * (fy - sy)
    return (np.abs(yy - ly) <= HALF) & (t >= 0) & (t <= 1.0 + 60 / abs(fx - sx))


def fix(rgb, cfg):
    """rgb: HxWx3 int16，品红底。返回同尺寸 uint8。"""
    H, W = rgb.shape[:2]
    fg = keyed(rgb) < 60
    fgd = ndimage.binary_dilation(fg, iterations=3)          # 边缘的半透明过渡像素跟着前景走
    xx = np.tile(np.arange(W, dtype=np.float32), (H, 1))

    arm = {}
    for s, sgn in (('a', 1), ('b', -1)):
        sx, sy, fx, fy, d = cfg[s]
        B = band((H, W), sx, sy, fx, fy)
        xh = fx - sgn * FIST
        arm[s] = (B & ((xx - sx) * sgn >= 0) & ((xh - xx) * sgn > 0), sx, xh, d, sgn)
    # 两只拳头之间（含手机）整块不动
    yy = np.tile(np.arange(H)[:, None], (1, W))
    ya, yb = cfg['a'][3], cfg['b'][3]
    fixed = (xx >= arm['a'][2]) & (xx <= arm['b'][2]) & (yy >= min(ya, yb) - HALF - 20) & (yy <= max(ya, yb) + HALF + 20)

    # 身体：前景去掉两条手臂带和拳头之后的连通块，按质心归左右
    body = fgd & ~arm['a'][0] & ~arm['b'][0] & ~fixed
    lab, n = ndimage.label(body)
    cx = ndimage.center_of_mass(body, lab, range(1, n + 1))
    mid = (cfg['a'][2] + cfg['b'][2]) / 2
    shift = np.zeros((H, W), np.float32)
    for i, c in enumerate(cx):
        m = lab == i + 1
        # 太小的碎块（手机边、指缝）贴着拳头的也不动
        if m.sum() < 400 and (fixed | arm['a'][0] | arm['b'][0])[ndimage.binary_dilation(m, iterations=2)].any() \
                and abs(c[1] - mid) < 200:
            continue
        shift[m] = cfg['a'][4] if c[1] < mid else -cfg['b'][4]
    for s in 'ab':
        inner, sx, xh, d, sgn = arm[s]
        k = (abs(xh - sx) - d) / abs(xh - sx)
        # 带内：x' = xh - (xh - x)·k   →  位移 = x' - x
        shift[inner & fgd] = (xh - (xh - xx) * k - xx)[inner & fgd]

    # 反向贴：位移只沿横向，逐行做。一行里按"源像素连续、位移连续"切段，每段单调，
    # 用一维插值求每个输出像素取源的哪个位置；段与段按身体 → 手臂 → 拳头的顺序覆盖
    out = np.tile(MAGENTA, (H, W, 1))
    moved = fgd | fixed
    for y in range(H):
        xs = np.nonzero(moved[y])[0]
        if not len(xs):
            continue
        srcrow = rgb[y].astype(np.float32)
        parts = []
        for seg in np.split(xs, np.nonzero(np.diff(xs) != 1)[0] + 1):
            cut = np.nonzero(np.abs(np.diff(shift[y, seg])) > 0.75)[0] + 1
            parts += [p for p in np.split(seg, cut) if len(p)]
        # 位移为 0 的（拳头/手机）最后画，压着手臂的接缝
        parts.sort(key=lambda p: (shift[y, p[0]] == 0, abs(shift[y, p[0]])))
        for part in parts:
            d0 = part + shift[y, part]
            a, b = int(np.ceil(d0.min())), int(np.floor(d0.max()))
            ox = np.arange(max(a, 0), min(b, W - 1) + 1)
            if not len(ox):
                continue
            sxp = np.interp(ox, d0, part.astype(np.float32))
            i0 = np.clip(np.floor(sxp).astype(int), 0, W - 2); t = (sxp - i0)[:, None]
            out[y, ox] = srcrow[i0] * (1 - t) + srcrow[i0 + 1] * t
    return np.clip(out.round(), 0, 255).astype(np.uint8), shift


def shift_mask(path, dx):
    """步态蒙版（透明 = 重画的腿）跟着赢方平移 dx"""
    m = np.array(Image.open(path).convert('RGBA'))
    out = np.zeros_like(m); out[..., 3] = 255
    if dx >= 0:
        out[:, dx:] = m[:, :m.shape[1] - dx]
    else:
        out[:, :dx] = m[:, -dx:]
    return Image.fromarray(out)


def run(name, path, cfg):
    rgb = np.array(Image.open(path).convert('RGB')).astype(np.int16)
    Image.fromarray(fix(rgb, cfg)[0]).save(path)


if __name__ == '__main__':
    """python3 arms/arms.py            → 全部原地改写（原图先备份到各自目录下的 old_arms1/）
       python3 arms/arms.py --dry n0   → 只出 /tmp/arms_<名>.png 看效果"""
    import shutil
    if sys.argv[1:2] == ['--dry']:
        for n in sys.argv[2:]:
            rgb = np.array(Image.open(os.path.join(HERE, SRC[n])).convert('RGB')).astype(np.int16)
            Image.fromarray(fix(rgb, CFG[n])[0]).save(f'/tmp/arms_{n}.png')
        sys.exit()

    def backup(path):
        d = os.path.join(os.path.dirname(path), 'old_arms1')
        os.makedirs(d, exist_ok=True)
        if not os.path.exists(os.path.join(d, os.path.basename(path))):
            shutil.copy2(path, d)

    for n, rel in SRC.items():
        path = os.path.join(HERE, rel); backup(path); run(n, path, CFG[n]); print(n, flush=True)
        g = os.path.join(HERE, 'gait', n)
        if not os.path.isdir(g):
            continue
        # 步态：base 与 f1~f7 同一套参数；蒙版跟着赢方（a 档 = 女生 +d、b 档 = 男生 -d）平移
        for f in ['base'] + [f'f{i}' for i in range(1, 8)]:
            p = os.path.join(g, f + '.png'); backup(p); run(n, p, CFG[n])
        p = os.path.join(g, 'mask.png'); backup(p)
        w = n[0]
        shift_mask(p, CFG[n][w][4] if w == 'a' else -CFG[n][w][4]).save(p)
        print(n, 'gait', flush=True)
