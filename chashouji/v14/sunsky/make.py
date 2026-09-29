"""后羿脚下的「烈日火空」（2026-09-29，替掉太阳火云海 tide_sun_{far,mid,near}）：两张贴图，引擎里拼（sea.js SunSky，跟嫦娥的明月银河同一套 Sky）。
用法：python3 v14/sunsky/make.py → web/assets/world/sunsky_{fire,sun}.webp，打印 sea.js 要填的尺寸。

用户："后羿的元素是对比嫦娥的。屏幕下方的特效，可以做一轮烈日 + 火花飞溅，里面有小陨石和三足金乌飞行"（选的方案 A：暗红到橙金的火空，
右下角半轮巨大的烈日从下沿升起、日冕翻腾、火花往上溅；小陨石从右上往左下坠；三足金乌往左飞）。
  · fire_src.png：黑底上一条横贯的火焰云带（fire_alt 另一张）→ 裁出带子那几行、横向无缝、缩小；黑底变透明（alpha = 最亮通道，颜色除回去），
    同 v14/moonsky 的银河。
  · sun_src.png：黑底上一轮烈日（sun_alt 另一张）。边上一圈火舌是虚的，不能按圆盘硬抠：alpha = 最亮通道 / SUN_A（亮过它的全不透明），
    颜色除回去 —— 日面全不透明，火舌半透、叠在火空上还是亮的。
三足金乌沿用 tide_sun_crow1~4（v14/tides/make.py 出）；火花、陨石、日冕是引擎里现画的。
"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from tidekit import seam

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'web', 'assets', 'world')


def unblack(rgb, full=255):
    """黑底 → 透明：alpha = 最亮通道 / full，颜色除回去（source-over 叠在深色上 ≈ 把光加上去）"""
    a = np.clip(rgb.max(-1, keepdims=True) / full, 0, 1)
    return np.dstack([np.clip(rgb / np.maximum(a, 1 / 255), 0, 255), a * 255]).clip(0, 255).astype(np.uint8)


def save(im, name):
    p = os.path.join(OUT, name)
    im.save(p, 'WEBP', quality=88, method=6)
    print(f'  {name} {im.width}×{im.height} {os.path.getsize(p) // 1024}KB')


# 火焰云带：原图 1536×1024，带子在 y ≈ 280~730（每行最亮通道均值 > 20）；裁 ROWS，拼缝后宽 1216，缩 K
ROWS, K = (230, 780), 0.62
g = np.array(Image.open(os.path.join(HERE, 'fire_src.png')).convert('RGB')).astype(np.float32)[ROWS[0]:ROWS[1]]
A = seam(g, np.ones(g.shape[:2], np.float32))
im = Image.fromarray(unblack(A[..., :3]), 'RGBA')
save(im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS), 'sunsky_fire.webp')

# 烈日：原图里日面 + 火舌在 (99~1166, 96~1141)，取正方形外框、缩到 SD
SD, SUN_A = 360, 150
s = np.array(Image.open(os.path.join(HERE, 'sun_src.png')).convert('RGB')).astype(np.float32)
ys, xs = np.nonzero(s.max(-1) > 40)
cx, cy, r = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2, max(xs.max() - xs.min(), ys.max() - ys.min()) / 2 + 4
box = tuple(int(v) for v in (cx - r, cy - r, cx + r, cy + r))
im = Image.fromarray(unblack(s, SUN_A), 'RGBA').crop(box)
save(im.resize((SD, SD), Image.LANCZOS), 'sunsky_sun.webp')
