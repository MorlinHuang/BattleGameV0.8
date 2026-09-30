"""B14 方块墙、B16 神殿石檐：parts fixed 场景层（审查第七批打回：名单写"从墙里挖出来""落在墙沿"，要把墙画出来）。
程序画：上沿要精确落在帧里的脚底那一行（接触线 ≤ 2 px），生图做不到逐像素对齐。先按 3 倍画、描黑边，再缩到格内像素（和帧同一个单位），
上沿 = 图的第 0 行（pivot [0, 0]），cfg 里 at 写 [墙左端的格内 x, 脚底那一行]。下半截 40 px 渐隐，不然一块墙浮在半空（同 B18 墙头）。
用法（在 chashouji 下）：python3 v14/trio/buddy/make_ledges.py"""
import os
import numpy as np
from PIL import Image, ImageDraw
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../web/assets/trio')
K = 3
INK = (38, 30, 28, 255)


def fade(im, solid):
    a = np.array(im); h = a.shape[0]
    for y in range(solid * K, h):
        a[y, :, 3] = (a[y, :, 3] * max(0.0, 1 - (y - solid * K) / (h - solid * K))).astype(np.uint8)
    return Image.fromarray(a)


def save(im, name):
    im = im.resize((im.width // K, im.height // K), Image.LANCZOS)
    im.save(os.path.join(OUT, name + '.webp'), 'WEBP', quality=92)
    a = np.array(im)[..., 3]; print(name, im.size, '第 0 行不透明像素', int((a[0] > 128).sum()), '/', im.width)


def b14():
    """方块墙：顶排草方块（绿顶 + 土侧）、第二排土、第三排石头，块边 44 格内像素；右边有一块被挖空的（黑洞 + 碎口），人就是从那儿钻出来的"""
    B, W, rows = 44, 300, 4
    im = Image.new('RGBA', (W * K, B * rows * K), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(14)
    pal = {'dirt': [(134, 96, 67), (115, 80, 55), (150, 108, 76), (96, 68, 48)],
           'grass': [(106, 170, 64), (90, 150, 52), (121, 188, 74)],
           'stone': [(128, 128, 128), (112, 112, 112), (143, 143, 143), (98, 98, 98)]}
    px = B * K // 8                                                  # 一块 8×8 个像素点
    for r in range(rows):
        for c in range(-1, W // B + 2):
            x0, y0 = c * B * K + (B * K // 2 if r % 2 else 0) * 0, r * B * K
            hole = r == 0 and c == 5
            for i in range(8):
                for j in range(8):
                    kind = 'stone' if r >= 2 else ('grass' if r == 0 and j < 2 + (i % 3 == 0) else 'dirt')
                    col = (22, 16, 14) if hole else pal[kind][rng.integers(len(pal[kind]))]
                    if hole and (j < 2 and rng.random() < 0.5): col = pal['dirt'][rng.integers(4)]   # 碎口：洞的上沿留几粒土
                    d.rectangle([x0 + i * px, y0 + j * px, x0 + (i + 1) * px - 1, y0 + (j + 1) * px - 1], fill=col + (255,))
            d.rectangle([x0, y0, x0 + B * K - 1, y0 + B * K - 1], outline=INK, width=2 * K // 2 + 1)
    d.line([(0, 0), (W * K, 0)], fill=INK, width=2 * K)                # 上沿描粗一点：人站的那条线
    d.line([(0, 0), (0, B * rows * K)], fill=INK, width=2 * K)        # 左端
    im = fade(im, B * 2)
    save(im, 'B14_wall')


def b16():
    """神殿石檐：白大理石檐板（上沿亮面 + 下沿阴影）→ 一排齿饰 → 檐下横楣，下面渐隐；左端收成一个斜切头"""
    W, H = 320, 120
    im = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    M0, M1, M2 = (242, 236, 222, 255), (214, 205, 188, 255), (176, 164, 146, 255)
    GOLD = (226, 178, 70, 255)
    s = lambda v: int(v * K)
    d.rectangle([0, 0, s(W), s(22)], fill=M0, outline=INK, width=s(1.5))                    # 檐板
    d.rectangle([0, s(3), s(W), s(6)], fill=(255, 252, 244, 255))                              # 顶面高光
    d.rectangle([0, s(16), s(W), s(22)], fill=M1)
    d.line([(0, 0), (s(W), 0)], fill=INK, width=s(2))
    d.rectangle([s(6), s(22), s(W), s(30)], fill=GOLD, outline=INK, width=s(1.2))            # 金色线脚
    for x in range(10, W, 18):                                                                  # 齿饰
        d.rectangle([s(x), s(30), s(x + 11), s(44)], fill=M1, outline=INK, width=s(1.2))
    d.rectangle([s(8), s(30), s(W), s(33)], fill=M2)
    d.rectangle([s(8), s(44), s(W), s(H)], fill=M0, outline=INK, width=s(1.5))              # 横楣
    for x in range(40, W, 64):                                                                  # 横楣上的回纹分格
        d.line([(s(x), s(52)), (s(x), s(H))], fill=M2, width=s(2))
    d.rectangle([s(8), s(44), s(W), s(50)], fill=M2)
    im = fade(im, 60)
    save(im, 'B16_ledge')


b14(); b16()
