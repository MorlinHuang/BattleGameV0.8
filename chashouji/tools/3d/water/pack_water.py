"""把 jet.py 渲出来的帧打成 WebP 图集（2026-09-28），打印引擎要填的数。
用法：python3 pack_water.py <渲染根目录（含 jet_out）> <web/assets/fx 目录>
（海面原先也是 3 渲 2（sea.py），同日被用户否掉、换回手绘 2D（v14/sea2/make.py），sea.py 已删，见 git 8cc1ebd；
命中水花 splash.py（3D 水冠）也被否 —— "直接爆水泡沫就行"，换成 sea.js Foam，已删，见 git af0660c。）

每一套按**所有帧的并集外框**裁（逐帧裁的话帧与帧对不齐、播起来抖），再按 SCALE 缩，排成 COLS 列：
  jet.webp：水柱 16 帧，原尺寸。打印的 x0 = 掌心（渲染图 x 12 像素处，jet.py X0）在裁剪框里的 x，cy = 中轴在裁剪框里的 y。
"""
import os, sys, glob
from PIL import Image

SRC, DST = sys.argv[1], sys.argv[2]


def union(files):
    box = None
    for f in files:
        b = Image.open(f).getbbox()
        if b is None: continue
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    return box


def pack(files, out, scale, cols):
    box = union(files)
    w, h = box[2] - box[0], box[3] - box[1]
    cw, ch = round(w * scale), round(h * scale)
    rows = (len(files) + cols - 1) // cols
    at = Image.new('RGBA', (cw * cols, ch * rows))
    for i, f in enumerate(files):
        im = Image.open(f).crop(box)
        if scale != 1: im = im.resize((cw, ch), Image.LANCZOS)
        at.paste(im, ((i % cols) * cw, (i // cols) * ch))
    at.save(out, 'WEBP', quality=86, method=6)
    print(f'{os.path.basename(out)}: {len(files)} 帧 cell {cw}x{ch} cols {cols} 裁剪框 {box} 文件 {os.path.getsize(out) // 1024}KB')
    return box


fs = sorted(glob.glob(os.path.join(SRC, 'jet_out', 'jet_*.png')))
b = pack(fs, os.path.join(DST, 'jet.webp'), 1, 4)
print(f'  jet 掌心 x0 {12 - b[0]} 中轴 cy {120 - b[1]}（jet.py：X0 = −2.9 → 渲染 x = (−2.9 + 3) × 120 = 12，出口封口描边往左 ~3 像素）')
