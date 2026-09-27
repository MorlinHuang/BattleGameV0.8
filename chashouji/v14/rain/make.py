"""【已停用 2026-09-27：榴莲、高跟鞋改走 3D 转盘图集 tools/3d/durian.py、heel.py，这里的平面贴图只留作备选，输出已删】
榴莲 + 高跟鞋雨（女生档 2，替换抱枕）的两张掉落物贴图：品红底原图 → 抠像、裁边、缩放。
原图用 Q 版（durian_q.png / heel_q.png：圆滚滚、圆钝的刺、矮胖的鞋 + 蝴蝶结、粗描边贴纸风，用户要"再 Q 版一点"）；
高跟鞋用 heel_mid.png（写实比例的尖头细跟 + 赛璐璐描边高光）：Q 版鞋用户嫌"太 Q"，要写实一点；榴莲保持 Q 版。
备选：写实 durian_src.png / heel_src.png、Q 版 heel_q.png（透明底，load_cut 直接用它的 alpha）。
用法：python3 v14/rain/make.py

输出 web/assets/items/：
  rain_durian.webp               榴莲（DURIAN_PX 宽，画面上按 GIFT.durian.r 缩）
  rain_heel_{red,pink,black}.webp 高跟鞋三色：原图红色，粉 / 黑是把**鞋面红**那部分调色（饱和的红，鞋垫的米色不动）
贴图按画面尺寸的 2 倍出（画面上缩小绘制，转起来边缘不糊）。"""
import os, sys, colorsys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from build import load_cut, edge_extend

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, '../../web/assets/items/rain_%s.webp')
DURIAN_PX, HEEL_PX = 220, 220           # 输出贴图宽


def cut(name, width):
    rgb, al = load_cut(os.path.join(HERE, name))
    rgb = edge_extend(rgb, al)
    ys, xs = np.nonzero(al > 0.5)
    x0, x1, y0, y1 = xs.min() - 3, xs.max() + 4, ys.min() - 3, ys.max() + 4
    im = Image.fromarray(np.dstack([rgb, al * 255]).astype(np.uint8)[y0:y1, x0:x1], 'RGBA')
    return im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)


def recolor(im, fn):
    """鞋面红（R 高、G/B 低：饱和的红和它的暗部、高光边）按 fn(r,g,b) 换色，其余不动"""
    a = np.array(im).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 90) & (r > g * 1.8) & (r > b * 1.8)
    a[..., :3] = np.where(red[..., None], fn(r, g, b), a[..., :3])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


cut('durian_q.png', DURIAN_PX).save(OUT % 'durian', 'WEBP', quality=90, method=6)
heel = cut('heel_mid.png', HEEL_PX)
heel.save(OUT % 'heel_red', 'WEBP', quality=90, method=6)
# 粉：红 → 亮玫粉（红通道保留明暗，蓝拉起来、绿稍抬）
recolor(heel, lambda r, g, b: np.stack([r, g * 0.6 + r * 0.35, r * 0.75], -1)).save(OUT % 'heel_pink', 'WEBP', quality=90, method=6)
# 黑：漆皮黑（按红通道的明暗压到深灰，高光留一点）
recolor(heel, lambda r, g, b: np.stack([r * 0.22 + g * 0.5] * 3, -1)).save(OUT % 'heel_black', 'WEBP', quality=90, method=6)
for n in ('durian', 'heel_red', 'heel_pink', 'heel_black'):
    print(n, Image.open(OUT % n).size)
