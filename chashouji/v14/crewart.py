"""档 4 三人组立绘的共用管线（2026-09-28）：绿幕 / 品红幕原图 → 抠像、去溢色、边缘颜色扩散、裁边、缩放、烘三层外发光 → 单层贴图，
打印量点（输出贴图像素）。每个角色一个 v14/<名>/make.py，只填原图、键、倍率、光色和量点，调这里的 make()。
写法照 v14/truth/make2.py、v14/demon/make.py（那两个是先写的、各自内联，没改）。

为什么共用：四个人 + 一只狗，每个都要抠像 → 去溢色 → edge_extend → 缩放 → 烘光，差的只是参数；各抄一份的话改一处要改五处。

抠像两种幕布（见 chashouji-art 第二节、记忆 genimage-magenta-cutout）：
  green：k = G − max(R,B)。紫色、暗红、粉色的角色用它 —— 品红度在粉 / 紫上能到 70~100+，按品红抠会被抠穿。
  magenta：k = min(R,B) − G。
  都先转 int16 再减（uint8 相减会下溢，暗部整块变透明）。
  key = (k0, k1)：k ≤ k0 全不透明、k ≥ k1 全透明、中间线性。幕布上 k ≈ 240，角色身上的薄荷绿（月亮查岗使的领子、裙子）k 可到 60，
  所以 k0 要高过角色身上最绿的那块；cut() 打印"轮廓内部被键吃掉的像素"来确认。
外发光烘进贴图：运行时 ctx.filter 在 Safari 上不可用。明亮底图上发光靠色相，三层由外到内：外扩 grow（MaxFilter 核，奇数）、模糊 blur、颜色。
"""
import math
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

PAD = 44                                   # 输出贴图四周给外发光留的边（输出像素），同 truth2 / demon1


def cut(src, screen, key, erase=()):
    """原图 → (rgb float32, alpha 0~1)。去溢色只动半透明过渡带（不透明的像素本来的颜色不动）。
    erase：[(x0, y0, x1, y1), ...] 原图像素，这些框里一律抠掉（画进原图、但运行时另外画的东西，如黑蛛女特工手上往上的丝）。"""
    a = np.array(Image.open(src).convert('RGB')).astype(np.int16)
    if screen == 'green':
        k = a[..., 1] - np.maximum(a[..., 0], a[..., 2])
    else:
        k = np.minimum(a[..., 0], a[..., 2]) - a[..., 1]
    al = np.clip(1 - (k - key[0]) / (key[1] - key[0]), 0, 1).astype(np.float32)
    for x0, y0, x1, y1 in erase:
        al[y0:y1, x0:x1] = 0
    # 小于 60 像素的孤立碎块（幕布上的噪点、抠剩的溢色斑）清掉
    lab, n = ndimage.label(al > 0.05)
    if n:
        sz = ndimage.sum(np.ones_like(al), lab, range(1, n + 1))
        al[np.isin(lab, np.nonzero(sz < 60)[0] + 1)] = 0
    rgb = a.astype(np.float32)
    edge = al < 0.99
    if screen == 'green':
        rgb[..., 1] = np.where(edge, np.minimum(rgb[..., 1], np.maximum(rgb[..., 0], rgb[..., 2])), rgb[..., 1])
    else:
        sp = np.clip(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1], 0, None) * edge
        rgb[..., 0] -= sp; rgb[..., 2] -= sp
    # 自检：半透明像素应该只在轮廓那一圈。离轮廓 6 像素以内都不算；再往里还半透明 = 角色自己的颜色被键吃掉了（要调高 key[0]）
    inner = ndimage.binary_erosion(al > 0.02, iterations=6)
    print('轮廓内部被键吃掉的像素', int((inner & (al < 0.98)).sum()), '（应接近 0）')
    return rgb, al


def edge_extend(rgb, al, it=12):
    """透明区的 RGB 仍是整片幕布色，LANCZOS 缩放会把它混进边缘出色边：把边缘颜色往外扩几圈。"""
    mask = al > 0.03
    ker = np.ones((3, 3), np.float32)
    for _ in range(it):
        m = mask.astype(np.float32)
        cnt = ndimage.convolve(m, ker, mode='constant')
        acc = np.stack([ndimage.convolve(rgb[..., c] * m, ker, mode='constant') for c in range(3)], -1)
        fill = (cnt > 0) & ~mask
        if not fill.any():
            break
        rgb[fill] = (acc / np.maximum(cnt, 1)[..., None])[fill]
        mask |= cnt > 0
    return rgb


def make(src, out, screen, key, K, glow, pts, margin=6, erase=()):
    """pts：{名: (x, y)} 原图像素；返回输出贴图像素的量点。裁边框按剪影外框 + margin 自动取（量点按原图像素，不受影响）。"""
    rgb, al = cut(src, screen, key, erase)
    rgb = edge_extend(rgb, al)
    ys, xs = np.nonzero(al > 0.05)
    x0, y0 = max(0, xs.min() - margin), max(0, ys.min() - margin)
    x1, y1 = min(al.shape[1], xs.max() + 1 + margin), min(al.shape[0], ys.max() + 1 + margin)
    px = np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(px[y0:y1, x0:x1], 'RGBA')
    im = im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS)
    res = Image.new('RGBA', (im.width + 2 * PAD, im.height + 2 * PAD))
    body = Image.new('RGBA', res.size); body.alpha_composite(im, (PAD, PAD))
    sil = body.split()[3]
    for grow, blur, c in glow:
        L = Image.new('RGBA', res.size, tuple(c) + (0,))
        L.putalpha(sil.filter(ImageFilter.MaxFilter(grow)).filter(ImageFilter.GaussianBlur(blur)))
        res.alpha_composite(L)
    res.alpha_composite(body)
    res.save(out, 'WEBP', quality=90, method=6)
    tr = lambda p: [round((p[0] - x0) * K + PAD), round((p[1] - y0) * K + PAD)]
    q = {n: tr(p) for n, p in pts.items()}
    print('size', res.size, '剪影', im.size, ' '.join(f'{n} {v}' for n, v in q.items()))
    return q


def rest(tail, muzzle, face):
    """贴图里喷口本来的指向（仰角，朝下为负）。face +1 朝右、-1 朝左。"""
    return round(-math.atan2(muzzle[1] - tail[1], (muzzle[0] - tail[0]) * face), 3)
