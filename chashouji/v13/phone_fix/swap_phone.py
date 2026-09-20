"""把 raw 里的手机统一成同一个朝向 —— 手不动，只换道具。

朝向分两段（用 orient 参数，命令行在档位后加 h 表示横）：**对拉的中段一律竖握**，
手机垂直于拉扯方向，和两条手臂形成十字，一眼看得出争的是它；**一方得手的两端
一律横握**，那是抱在怀里看的姿势。中段成功而两端失败的原因是握法不同：中段是
两个拳头对顶夹住手机，换窄了拳头照样贴着；两端是双手捧着手机、手指沿长边分布，
换窄之后手指就悬空了。

为什么不重新生图：模型每次都会把整张重画一遍（实测保留区改动 3%，手臂位置、
睡衣褶皱全变），而这一步要的恰恰是"姿态一个像素都别动，只把道具转 90 度"。
为什么不从别的档位贴手+手机：只有姿态几乎相同的相邻档对得上（f045←f040 差
2~10px 可以，f025←f032 差 120px 完全不行），做不成通用手段。

做法分四步，关键在第四步：
  1. 用冷色判据找出手机本体（机身是深灰蓝，B 高于 R；头发是暖黑，R≥B）
  2. 把这些像素擦成品红 —— 此时压在手机正面的手指仍然留在画面上
  3. 在原手机中心画一部竖手机（圆角矩形 + 粗描边 + 左上角双摄，颜色取自原图）
  4. 把第 2 步之后还留在手机区域里的非品红像素（就是那些手指）重新盖回去
     —— 这样手指自然压在新手机正面，和原来的遮挡关系完全一致。
     盖回时取的是**原图**而不是擦过的图：擦手机时连描边一起膨胀掉了两像素，
     那两像素里有手指自己的描边，从擦过的图里取就再也取不回来，手机与拳头之间
     会留一条品红细缝。

尺寸只信原手机的**长边**：横手机的长边不会被手指整条遮住，量得准；短边则经常
把手指的暗部一起算进来（f022 量出 64x59、f035 量出 81x55，都比真实的扁手机厚），
照它对调会得到一块近乎正方形的砖。所以转 90 度后 **高度 = 原长边，宽度 = 高度 /
1.6**（1.6 是卡通简化后的手机比例，实测 f045 这样算出来的 51 与它量到的短边一致）。
副作用是新手机比两个拳头的间距窄几个像素，实测每侧空隙 3~5px，成品帧上约 3px，
看不出来；反过来若按间距取宽度，手机会压住拳头内缘，那个更显眼。
"""
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

MAG = (255, 0, 255)


def find_phone(a):
    """返回手机像素掩码。a 是 RGB int 数组。

    机身和屏幕要一起找：正面朝观众的那几档（f050）机身只露出一圈边框，光靠冷色
    深色判据量出来的框比真实手机小三成，照它画的新手机盖不住原来的屏幕，底下会
    留一条兔子图案。两个判据并起来再取最大连通块就对了。"""
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    h = a.shape[0]
    body = (a.sum(2) < 430) & (B > R + 6) & (B > 40)      # 深灰蓝机身
    screen = (B > R + 20) & (B > 110) & (a.sum(2) > 260)  # 亮着的屏幕（正面朝观众那几档）
    m = body | screen
    find_phone.body_only = body
    m[:int(h * 0.35)] = False          # 只在手部那条横带里找，避开头发与裤子
    m[int(h * 0.62):] = False
    lab, n = ndimage.label(m)
    if n == 0:
        return None
    sz = ndimage.sum(m, lab, range(1, n + 1))
    k = int(np.argmax(sz)) + 1
    if sz[k - 1] < 150:
        return None
    return lab == k


def tight_box(m, frac=0.10):
    """掩码的行列投影里，低于峰值 frac 的行列当成碎屑丢掉。

    手机被手指压住时掩码会碎成好几块，直接取 bbox 会把远处的零星像素也框进来。
    矩形物体的投影是个平台，碎屑是毛刺，按峰值比例切一刀就能把毛刺去掉。
    frac 只能取小值：0.25 时 f035 的长边从 81 被切到 54，把手机本身削掉了三成。"""
    cols, rows = m.sum(0), m.sum(1)
    cx = np.where(cols >= cols.max() * frac)[0]
    ry = np.where(rows >= rows.max() * frac)[0]
    return int(cx.min()), int(cx.max()), int(ry.min()), int(ry.max())


def draw_phone(w, h, body, edge, ss=4):
    """竖手机：圆角矩形 + 粗黑描边 + 左上角方形双摄。ss 是超采样倍数。"""
    W, H = w * ss, h * ss
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = int(w * 0.17 * ss)
    lw = max(2, int(2.2 * ss))
    d.rounded_rectangle([lw // 2, lw // 2, W - lw // 2 - 1, H - lw // 2 - 1],
                        radius=r, fill=body + (255,), outline=edge + (255,), width=lw)
    cw = int(W * 0.30)
    cx0, cy0 = int(W * 0.12), int(H * 0.04)
    d.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + cw], radius=int(cw * 0.3),
                        fill=tuple(int(v * 0.78) for v in body) + (255,),
                        outline=edge + (255,), width=max(1, lw // 2))
    rr = int(cw * 0.2)
    for ox, oy in ((0.3, 0.3), (0.68, 0.66)):
        px, py = cx0 + cw * ox, cy0 + cw * oy
        d.ellipse([px - rr, py - rr, px + rr, py + rr],
                  fill=tuple(int(v * 0.45) for v in body) + (255,),
                  outline=tuple(min(255, int(v * 1.5)) for v in body) + (255,), width=max(1, lw // 3))
    return im.resize((w, h), Image.LANCZOS)


def swap(path, out, size=None, orient='v'):
    im = Image.open(path).convert('RGB')
    a = np.array(im).astype(int)
    m = find_phone(a)
    if m is None:
        return None
    x0, x1, y0, y1 = tight_box(m)
    long_side = max(x1 - x0 + 1, y1 - y0 + 1)
    short_side = min(x1 - x0 + 1, y1 - y0 + 1)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2

    # 取色只认机身那部分：正面朝观众的档位里屏幕像素占多数，连屏幕一起取中位数
    # 会把新手机染成浅蓝。
    bm = find_phone.body_only & m
    px = a[bm if bm.sum() > 120 else m]
    s = px.sum(1)
    body = tuple(int(v) for v in np.median(px[(s > np.percentile(s, 30)) & (s < np.percentile(s, 85))], 0))
    edge = tuple(int(v * 0.58) for v in body)      # 描边照机身压暗，比取原图最暗像素稳

    if size is not None:
        h, w = size
    elif orient == 'v':
        h, w = int(long_side), max(10, int(round(long_side / 1.6)))
    else:
        w, h = int(long_side), max(10, int(round(long_side / 1.6)))

    # 2) 擦掉旧手机（先填内部的洞——屏幕高光线和摄像头不在冷色判据里，不填就会在
    #    第 4 步被当成手指盖回来，在新手机上留下一条横贯的亮线），手指留在原处
    m = ndimage.binary_fill_holes(m)
    grown = ndimage.binary_dilation(m, iterations=2)
    erased = a.copy()
    erased[grown] = MAG

    # 3) 画竖手机
    cv = Image.fromarray(erased.astype(np.uint8))
    ph = draw_phone(w, h, body, edge) if orient == 'v' else \
         draw_phone(h, w, body, edge).rotate(90, expand=True)
    bx, by = cx - w // 2, cy - h // 2
    cv.paste(ph, (bx, by), ph)

    # 4) 把仍留在新手机范围内的手指盖回手机正面（取自原图，不是擦过的图）
    res = np.array(cv).astype(int)
    sub = a[by:by + h, bx:bx + w]
    subm = m[by:by + h, bx:bx + w]
    R, G, B = sub[..., 0], sub[..., 1], sub[..., 2]
    # 非品红、不是旧手机、且是暖色（R≥B）= 手指与袖口。加 R≥B 这一条是因为旧手机
    # 边缘的浅色高光既不在冷色判据里、也不是内部的洞，不排掉就会盖成手机顶上一块白斑。
    # R > B + 15 而不是 R >= B：正面朝观众那几档的屏幕图案（白兔）R≈B，只用 R>=B
    # 会把它当手指盖回去，新手机背面上就印着一只兔子。肤色的红蓝差远大于 15。
    fingers = ((np.minimum(R, B) - G) < 90) & ~subm & (R > B + 15)
    # 只认从新手机矩形**边界伸进来**的那几块：手指必然连着画外的手臂，而屏幕上的
    # 图案（白兔的高光也是暖色）是孤岛。不这么筛，新手机背面会印着半只兔子。
    flab, fn = ndimage.label(fingers)
    edge_ids = set(flab[0]) | set(flab[-1]) | set(flab[:, 0]) | set(flab[:, -1])
    edge_ids.discard(0)
    fingers = np.isin(flab, list(edge_ids)) if edge_ids else np.zeros_like(fingers)
    reg = res[by:by + h, bx:bx + w]
    reg[fingers] = sub[fingers]

    Image.fromarray(res.clip(0, 255).astype(np.uint8)).save(out)
    return dict(old=(int(x1 - x0 + 1), int(y1 - y0 + 1)), new=(w, h),
                center=(int(cx), int(cy)), body=body, edge=edge)


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        # 档位，或 "档位:宽x高" 手工指定新手机尺寸（检测不可靠的那几张用）
        orient = 'v'
        if arg.endswith('h'):
            arg, orient = arg[:-1], 'h'      # 末尾加 h = 转成横握（得手段用）
        if ':' in arg:
            a1, a2 = arg.split(':')
            p, size = int(a1), tuple(int(v) for v in a2.split('x'))
        else:
            p, size = int(arg), None
        r = swap(f'raw/f{p:03d}.png', f'phone_fix/f{p:03d}.png', size, orient)
        print(f'f{p:03d}', r)
