#!/usr/bin/env python3
"""把 Blender 渲出来的转盘帧打包成引擎用的图集。

    python3 pack_atlas.py <帧目录> <输出.webp> [--cell 268] [--cols 6] [--q 88]

做三件事：

1. **按所有角度的并集裁一个正方形。** 逐帧各裁各的会让物体在格子里跳来跳去 ——
   转盘播起来就是原地乱窜。并集裁切保证每一帧里物体的相对位置都是对的。
2. 下采样到 cell 并拼成图集。
3. 算出 ammo.js 里 `SPRITE` 那一行要填的 `scale`，直接打印出来。

## 为什么用 WebP 而不是 PNG

玫瑰花束一件 2.3MB，八件 18MB —— 这是铺开前的卡点。根因不是尺寸也不是帧数，
是 **PNG 的无损编码**：这些图是 Toon 平涂 + 硬描边，PNG 压不动大片渐变边缘。
换 WebP(q=88) 后同样 36 帧 268px 从 2433KB 掉到 408KB，**alpha 通道逐像素无损**
（WebP 的 alpha 始终单独无损压），RGB 平均差 4.3/255，2 倍放大肉眼看不出。
降单格边长或砍帧数都是牺牲画质去换体积，换编码不牺牲任何东西。

## scale 是怎么算出来的

约定：物品建模时主体直径做成 `NOMINAL`=2.0 个 Blender 单位，相机 `ORTHO`=3.3。
于是物体在渲染图里的标称直径 = 渲染边长 × 2.0/3.3。
引擎按 `drawImage(..., 2r*scale)` 画，要让物体本身正好显示成直径 2r，
就得 `scale = 并集边长 / 标称直径像素` —— 并集比物体大多少，就放大多少倍回去。
"""
import sys, os, glob, argparse
import numpy as np
from PIL import Image

ORTHO, NOMINAL = 3.3, 2.0          # 必须与 common.py 保持一致


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('out')
    ap.add_argument('--cell', type=int, default=0, help='最终单格边长，0=不缩放')
    ap.add_argument('--cols', type=int, default=6)
    ap.add_argument('--q', type=int, default=88)
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(a.src, '*.png')))
    if not files:
        sys.exit('没有找到帧：' + a.src)
    ims = [Image.open(f).convert('RGBA') for f in files]
    full = ims[0].size[0]

    # 并集包围盒：alpha>8 才算有东西，低于这个是 Freestyle 描边的抗锯齿尾巴
    x0, y0, x1, y1 = full, full, 0, 0
    for im in ims:
        al = np.array(im)[..., 3] > 8
        if not al.any():
            continue
        ys, xs = np.where(al)
        x0, x1 = min(x0, xs.min()), max(x1, xs.max())
        y0, y1 = min(y0, ys.min()), max(y1, ys.max())
    # 正方形化并居中：引擎按正方形格子采样，长方形会被拉伸
    side = max(x1 - x0 + 1, y1 - y0 + 1)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    box = (cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side)

    cell = a.cell or side
    n = len(ims)
    rows = (n + a.cols - 1) // a.cols
    atlas = Image.new('RGBA', (cell * a.cols, cell * rows), (0, 0, 0, 0))
    for k, im in enumerate(ims):
        g = im.crop(box)
        if cell != side:
            g = g.resize((cell, cell), Image.LANCZOS)
        atlas.paste(g, ((k % a.cols) * cell, (k // a.cols) * cell))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    atlas.save(a.out, 'WEBP', quality=a.q, method=6)
    scale = side / (full * NOMINAL / ORTHO)
    kb = os.path.getsize(a.out) // 1024
    print('帧数 %d  渲染边长 %d  并集 %d  单格 %d  体积 %dKB' % (n, full, side, cell, kb))
    print('ammo.js 里填：{ src: \'assets/items/%s\', n: %d, cols: %d, cell: %d, scale: %.2f }'
          % (os.path.basename(a.out), n, a.cols, cell, scale))


if __name__ == '__main__':
    main()
