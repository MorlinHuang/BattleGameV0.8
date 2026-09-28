"""法海的神兽小佛（2026-09-28）：一张 2×2 生图 → 四张单独的贴图（金色外发光烘进去），对应白娘子海里的虾兵蟹将。
用法：python3 v14/scroll/beasts.py → web/assets/world/scroll_{monk,qilin,lion,elephant}.webp
用户："虾兵蟹将可以对应神兽小佛"。四只：踩祥云合十的小沙弥、麒麟崽、护法小石狮（踩绣球）、驮莲花的小白象，全朝左（冲女生那边）。
beasts_src.png 生图时直接出了透明底，但 alpha 不干净：身子里是 250~254，四周一圈 1~31 的黄色虚边 → alpha 按 (32, 240) 拉满 / 清零。
按连通块切（四只互不相连），每只缩到 HGT 高。beasts_alt.png 是同一轮另一张。
"""
import os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'web', 'assets', 'world')
HGT = 150                        # 输出剪影高度（同虾兵 150；引擎里再按远近乘 0.75 / 1.0）
PAD = 18
GLOW = [(15, 12, (255, 190, 50), 0.9), (5, 4, (255, 240, 170), 1.0)]   # 外扩、模糊、颜色、强度：先金橙、再贴边浅金
NAMES = {(0, 0): 'monk', (1, 0): 'qilin', (0, 1): 'lion', (1, 1): 'elephant'}   # 按在原图里的格子（列, 行）

im = np.array(Image.open(os.path.join(HERE, 'beasts_src.png')).convert('RGBA')).astype(np.float32)
al = np.clip((im[..., 3] - 32) / (240 - 32), 0, 1)
lab, n = ndimage.label(al > 0.5)
sz = ndimage.sum(np.ones_like(al), lab, range(1, n + 1))
H, W = al.shape
for i in np.argsort(sz)[::-1][:4]:
    ys, xs = np.nonzero(lab == i + 1)
    cell = (int(xs.mean() > W / 2), int(ys.mean() > H / 2))
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    keep = ndimage.binary_dilation(lab == i + 1, iterations=4)[y0:y1, x0:x1]   # 只要这一块（带 4 像素的边），邻居的虚边不要
    a = al[y0:y1, x0:x1] * keep
    px = np.dstack([im[y0:y1, x0:x1, :3], a * 255]).clip(0, 255).astype(np.uint8)
    sp = Image.fromarray(px, 'RGBA')
    K = HGT / sp.height
    sp = sp.resize((round(sp.width * K), HGT), Image.LANCZOS)
    res = Image.new('RGBA', (sp.width + 2 * PAD, sp.height + 2 * PAD))
    body = Image.new('RGBA', res.size); body.alpha_composite(sp, (PAD, PAD))
    sil = body.split()[3]
    for grow, blur, c, k in GLOW:
        L = Image.new('RGBA', res.size, c + (0,))
        L.putalpha(sil.filter(ImageFilter.MaxFilter(grow)).filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * k)))
        res.alpha_composite(L)
    res.alpha_composite(body)
    name = NAMES[cell]
    res.save(os.path.join(OUT, f'scroll_{name}.webp'), 'WEBP', quality=90, method=6)
    print(name, res.size)
