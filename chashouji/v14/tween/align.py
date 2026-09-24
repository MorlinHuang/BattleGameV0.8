"""补帧对齐：把生图出来的补帧按"缩放 + 平移"对到 s000（僵持帧）的坐标里。

生图每次会把整组人左右挪几十像素，不对齐的话连播起来整组人在横跳。身高定缩放、脚底定地面线、上半身重心定水平，都只看赢的那一方。拿全身去配准会把输的那方的姿态变化也当误差对掉；
只拿上半身做像素配准实测缩放偏大一成（头发的面积在变），脚踩进了地面线以下。
每张都直接对 s000（不是对上一张），误差不会一张张累积。

用法：python3 v14/tween/align.py a   → 读 tween/a/sNNN.png，写 tween/a/aligned/sNNN.png
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CX, CY = 768, 512                # 生图原图 1536×1024 的中心
PAD = 320                        # 输出画布四周各留这么多（build.py 读 aligned/ 时要把锚点加上它）


def measure(path, side):
    """(头顶 y, 脚底 y, 上半身重心 x)，只取赢的那一方（全段站着；手机竖线左边是
    女生、右边是男生）。重心只取上半身 —— 她在迈步，腿的质心跟着脚走。"""
    sys.path.insert(0, os.path.join(HERE, '..'))
    from build import cutout, find_phone
    rgb, al = cutout(path)
    px = find_phone(rgb, al)[0]
    xs = np.arange(al.shape[1])[None, :]
    m = (al > 0.5) & ((xs < px) if side == 'a' else (xs > px))
    ys, xx = np.nonzero(m)
    top, bot = ys.min(), ys.max()
    return top, bot, xx[ys < top + (bot - top) * 0.5].mean()


def solve(ref, mov):
    """缩放 = 赢的那一方的身高比；脚底对地面线；上半身重心对水平位置。
    生图会把人画小一成左右（头顶不动、脚底往上缩 60~86px），这是真缩放。
    试过但被姿势带偏的尺子：粉睡衣面积（迈步时两腿互相遮挡，漂到 1.24）、
    手机长度（握得越深露出越短，漂到 1.20）、上半身像素配准（头发面积在变）。
    身高在这一段里可用，是因为赢的一方全程同一个后仰角度；到了后仰更狠的段落要复核。"""
    rt, rb, rx = ref
    mt, mb, mx = mov
    s = (rb - rt) / (mb - mt)
    return s, rx - (mx - CX) * s - CX, rb - (mb - CY) * s - CY


def apply(im, s, dx, dy):
    """按 (s, dx, dy) 变换原图，放进四周各加 PAD 的品红画布。
    放大一成再平移之后，画在原图边缘的脚会被推出 1536×1024 —— 画布不够大就是在裁肢体。"""
    cx, cy = CX, CY
    # PIL 的 affine 是"输出像素 → 输入像素"的反向映射；输出坐标先减 PAD 回到原图系
    c = cx - (cx + dx) / s - PAD / s
    f = cy - (cy + dy) / s - PAD / s
    size = (im.width + 2 * PAD, im.height + 2 * PAD)
    return im.convert('RGB').transform(size, Image.AFFINE, (1 / s, 0, c, 0, 1 / s, f), Image.BICUBIC,
                                       fillcolor=(255, 0, 255))


def main(side):
    d = os.path.join(HERE, side)
    out = os.path.join(d, 'aligned')
    os.makedirs(out, exist_ok=True)
    ref = measure(os.path.join(d, 's000.png'), side)
    for f in sorted(os.listdir(d)):
        if not (f.startswith('s') and f.endswith('.png')) or '_' in f:
            continue
        im = Image.open(os.path.join(d, f))
        s, dx, dy = solve(ref, measure(os.path.join(d, f), side))
        apply(im, s, dx, dy).save(os.path.join(out, f))
        print(f'{f}  缩放 {s:.3f}  平移 ({dx:+.0f}, {dy:+.0f})px')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'a')
