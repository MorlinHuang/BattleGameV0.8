#!/usr/bin/env python3
"""三人组 3D 道具出图后的一次性验收：结构密度、识别色废帧、纯黑内腔、图集体积，外加一张 1:1 接触表。

    python3 prop_check.py <帧目录> <件名> <r> <识别色hex> [--atlas web/assets/trio/prop_<件名>.webp] [--sheet out.png]

- 结构密度：同 measure_volume.py（主尺，达标 ≥ 20%）。
- 识别色：这件东西最认人的那个颜色（西瓜的红瓤、锅的黑…不行，要选描边色以外的颜色），逐帧数
  色差 < 48 的实心像素；**少于 36 帧中位数 12% 的帧算废帧**，废帧 ≤ 12（三分之一）。
- 纯黑内腔：alpha>200 里亮度 < 12 的占比，skill 坑 7；> 1% 就查是不是有封闭夹缝。
- 屏幕描边宽：外轮廓那一圈描边缩到屏幕尺寸后有多厚（中位数）。同一套 common.py + screen_r=r 渲的，
  各件都该落在篮球那个数附近。
- 已经打成图集的件（美术出的、手上没有帧）：<帧目录> 换成图集 webp，加 --cell 和 --scale（引擎里填的那两个数）。
- 墨块帧：实心像素里不是描边色的不到 15% —— 整帧就是一块墨（零件间距 g < 2W 描边并满、或侧对时只剩一条边）。
  **结构密度会被墨块骗高**（哑铃 70%、磁带 72%，一半的帧是墨块），所以跟它一起看：墨块帧 ≤ 6/36。
- 接触表：36 帧按引擎里的屏幕尺寸（直径 2r × scale）缩好，贴在地板米色底上，每帧一格，眼睛逐帧看。
"""
import sys, os, glob, argparse
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure_volume import struct_density, frames_engine, cells, INK

BG = (233, 222, 200)        # 客厅米色地板，道具飞过时身后多半是它


def ink_width(ims, px):
    """外轮廓那一圈描边在屏幕上有多厚：每帧按并集裁好、缩到屏幕尺寸（整格 = 2r×scale 像素）再放大 4 倍量亚像素，
    剪影边上每一点往里走到第一个非描边的实心像素有多远，取中位数。只量外轮廓 —— 内部线常常两条并成一条，量它会偏大。"""
    from scipy.ndimage import distance_transform_edt, binary_erosion
    u = np.any([g[..., 3] > 8 for g in ims], axis=0)
    ys, xs = np.where(u)
    side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 1
    cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
    box = (cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side)
    d = max(8, int(round(px)))
    ws = []
    for g in ims:
        t = np.array(Image.fromarray(g).crop(box).resize((d * 4, d * 4), Image.LANCZOS)).astype(float)
        solid = t[..., 3] > 128
        ink = np.sqrt(((t[..., :3] - INK) ** 2).sum(-1)) < 60
        edge = solid & ~binary_erosion(solid)
        D = distance_transform_edt(~(solid & ~ink))          # 到最近的"实心且不是描边"像素的距离
        if edge.any():
            ws.append(np.median(D[edge]) / 4)
    return float(np.median(ws)) if ws else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('name'); ap.add_argument('r', type=float); ap.add_argument('idhex')
    ap.add_argument('--atlas'); ap.add_argument('--sheet')
    ap.add_argument('--cell', type=int, default=0); ap.add_argument('--scale', type=float, default=0)
    a = ap.parse_args()
    if a.src.endswith('.webp'):                      # 图集模式：切格子，scale 用引擎里填的
        ims = cells(a.src, a.cell)
        scale = a.scale
    else:
        ims = [np.array(Image.open(f).convert('RGBA')) for f in sorted(glob.glob(os.path.join(a.src, '*.png')))]
        _, scale, _, _, _ = frames_engine(a.src, a.r)
    px = 2 * a.r * scale
    dens = struct_density(a.src, a.cell, px)

    h = a.idhex.lstrip('#'); tgt = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)
    cnt, dark, blob = [], [], 0
    for g in ims:
        solid = g[..., 3] > 200
        rgb = g[..., :3].astype(float)
        cnt.append(int((solid & (np.sqrt(((rgb - tgt) ** 2).sum(-1)) < 48)).sum()))
        lum = rgb.mean(-1)
        ink = np.sqrt(((rgb - INK) ** 2).sum(-1)) < 60
        blob += (solid & ~ink).sum() < 0.15 * max(1, solid.sum())
        dark.append((solid & (lum < 12)).sum() / max(1, solid.sum()))
    med = float(np.median(cnt))
    ink_w = ink_width(ims, px)
    waste = sum(c < 0.12 * med for c in cnt)
    print('[%s] r=%g  屏幕直径 %.0fpx  结构密度 %.0f%%  识别色 #%s 中位 %d px（渲染图） 废帧 %d/%d  墨块帧 %d/%d  纯黑最高 %.2f%%  屏幕描边宽 %.1fpx'
          % (a.name, a.r, px, dens * 100, h, med, waste, len(ims), blob, len(ims), max(dark) * 100, ink_w))
    if a.atlas:
        print('[%s] 图集 %s  %dKB' % (a.name, a.atlas, os.path.getsize(a.atlas) // 1024))
    if a.sheet:
        # 并集裁切同 pack_atlas，缩到屏幕尺寸：cell 在屏幕上画成 2r×scale
        u = np.any([g[..., 3] > 8 for g in ims], axis=0)
        ys, xs = np.where(u)
        side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 1
        cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
        box = (cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side)
        d = max(8, int(round(px)))
        pad = 8
        cols = 12
        rows = (len(ims) + cols - 1) // cols
        out = Image.new('RGB', (cols * (d + pad) + pad, rows * (d + pad) + pad), BG)
        for k, g in enumerate(ims):
            t = Image.fromarray(g).crop(box).resize((d, d), Image.LANCZOS)
            out.paste(t, (pad + (k % cols) * (d + pad), pad + (k // cols) * (d + pad)), t)
        out.save(a.sheet)
        print('[%s] 接触表 %s（1:1 屏幕尺寸）' % (a.name, a.sheet))


if __name__ == '__main__':
    main()
