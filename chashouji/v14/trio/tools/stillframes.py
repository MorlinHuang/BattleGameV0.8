"""原单张立绘的老角色（B12 草帽、G12 紫衣仙子）打成帧序列图集（2026-10-01）。

这两个人的姿势帧都是在**同一张原立绘的画布上**局部重绘出来的（inpaint_paste.py：框外是原图像素），所以天然对齐 ——
锚点、转轴、手的位置都和原来的单张立绘同一个像素，不用配准。这里只把几帧按格排进一张图集，写 json（带头框，combo_scan 用）。

用法（在 chashouji 下）：python3 v14/trio/tools/stillframes.py B12|G12
       python3 v14/trio/tools/stillframes.py compare B12|G12 → shots/trio_std/老_<编号>_原图对比.png（原立绘 / 图集 idle / 补的姿势帧，idle 与原图逐像素差值）"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
SETS = {
    # 名：(图集名, [(帧名, 图), ...], 锚点, 头框（原图像素，帽子 / 发髻算头）)
    'B12': ('B12_straw', [('idle', 'web/assets/world/trio_straw.webp'), ('wind', 'v14/trio/buddy/B12_straw/inp/wind.png')], [300, 180], [108, 0, 196, 84]),
    'G12': ('G12_fairy', [('idle', 'web/assets/world/trio_fairy.webp'), ('kiss', 'v14/trio/bestie/G12_fairy/inp/kiss.png')], [145, 0], [124, 52, 192, 128]),
}


def build(code):
    name, frames, anchor, head = SETS[code]
    ims = [(fn, Image.open(os.path.join(ROOT, p)).convert('RGBA')) for fn, p in frames]
    cw, ch = ims[0][1].size
    assert all(im.size == (cw, ch) for _, im in ims), '帧必须是同一张画布'
    cols = len(ims)
    at = Image.new('RGBA', (cw * cols, ch))
    for i, (fn, im) in enumerate(ims): at.paste(im, (i * cw, 0))
    out = os.path.join(ROOT, 'web/assets/trio', name)
    at.save(out + '.webp', 'WEBP', quality=92, method=6)
    json.dump({'cell': [cw, ch], 'cols': cols, 'frames': [fn for fn, _ in ims], 'anchor': anchor, 'residual': 0, 'head': head, 'ref': 'idle',
               'src': 'stillframes.py'}, open(out + '.json', 'w'), ensure_ascii=False)
    print(f"{code}: sheet: {{ src: 'assets/trio/{name}.webp', cell: [{cw}, {ch}], cols: {cols}, names: {[fn for fn, _ in ims]} }}，{os.path.getsize(out + '.webp') // 1024}KB")


def compare(code):
    name, frames, anchor, head = SETS[code]
    orig = Image.open(os.path.join(ROOT, frames[0][1])).convert('RGBA')
    meta = json.load(open(os.path.join(ROOT, 'web/assets/trio', name + '.json'))); cw, ch = meta['cell']
    at = Image.open(os.path.join(ROOT, 'web/assets/trio', name + '.webp')).convert('RGBA')
    cells = [(fn, at.crop((i * cw, 0, (i + 1) * cw, ch))) for i, fn in enumerate(meta['frames'])]
    diff = np.abs(np.array(orig).astype(int) - np.array(cells[0][1]).astype(int)).max(2)
    cv = Image.new('RGBA', ((cw + 20) * (1 + len(cells)) + 20, ch + 60), (236, 232, 224, 255))
    d = ImageDraw.Draw(cv); fo = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 15)
    for k, (lab, im) in enumerate([('原单张立绘', orig)] + [(f'图集 {fn} 帧', im) for fn, im in cells]):
        cv.alpha_composite(im, (20 + k * (cw + 20), 50)); d.text((20 + k * (cw + 20), 6), lab, fill=(0, 0, 0), font=fo)
    d.text((20 + cw + 20, 26), f'与原图最大差 {diff.max()}（WebP 压缩），差 > 24 的像素 {(diff > 24).sum()}', fill=(60, 60, 60), font=fo)
    cv.convert('RGB').save(os.path.join(ROOT, 'shots/trio_std', f'老_{code}_原图对比.png'))
    print(code, 'idle vs 原图 最大差', diff.max(), '差>24 像素', (diff > 24).sum())


if __name__ == '__main__':
    if sys.argv[1:2] == ['compare']:
        for c in sys.argv[2:] or SETS: compare(c)
        sys.exit()
    for c in sys.argv[1:] or SETS: build(c)
