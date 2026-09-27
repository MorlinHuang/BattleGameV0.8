"""高跟鞋图集调色：heel_atlas.webp（红，heel.py 渲的）→ heel_pink_atlas.webp / heel_black_atlas.webp。
只动鞋面红（R 高、G/B 低：饱和的红和它的暗面），米色鞋垫、深色鞋底、黑鞋钉、描边都不动。
用法：python3 tools/3d/recolor_heel.py   （在 chashouji/ 下跑，heel 重渲打包后重跑一次）"""
import numpy as np
from PIL import Image

SRC = 'web/assets/items/heel_atlas.webp'


def recolor(im, fn):
    a = np.array(im).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 90) & (r > g * 1.8) & (r > b * 1.8)
    a[..., :3] = np.where(red[..., None], fn(r, g, b), a[..., :3])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


im = Image.open(SRC).convert('RGBA')
# 粉：红 → 亮玫粉（红通道保留明暗，蓝拉起来、绿稍抬）
recolor(im, lambda r, g, b: np.stack([r, g * 0.6 + r * 0.35, r * 0.75], -1)).save(
    'web/assets/items/heel_pink_atlas.webp', 'WEBP', quality=88, method=6)
# 黑：漆皮黑（按红通道的明暗压到深灰，高光留一点）
recolor(im, lambda r, g, b: np.stack([r * 0.22 + g * 0.5] * 3, -1)).save(
    'web/assets/items/heel_black_atlas.webp', 'WEBP', quality=88, method=6)
