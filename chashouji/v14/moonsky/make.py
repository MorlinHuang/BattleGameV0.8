"""嫦娥脚下的「明月银河」（2026-09-29，替掉月夜银云海 tide_moon_*）：三样贴图，引擎里拼（sea.js MoonSky）。
用法：python3 v14/moonsky/make.py → web/assets/world/moonsky_{galaxy,moon,rabbit1..4}.webp，打印 sea.js 要填的尺寸。

用户："嫦娥的特效太像水面了，跟白娘子的重复而且与嫦娥设定不搭。屏幕下方的特效，可以做一轮明月 + 银河星带，里面再漂些兔子和薄纱就行"
（选的方案 A：左下角半轮大明月从下沿升起，银河星带从明月往右铺开、星尘流动，玉兔失重般翻着漂，几条淡紫薄纱在里面飘）。
  · galaxy_src.png：黑底上一条横贯的银河（galaxy_alt 同一轮另一张）→ 裁出星带那几行、横向无缝（tidekit.seam）、缩小。
    黑底换成透明：alpha = 最亮通道、颜色除回去（source-over 叠在深色夜空上 ≈ 把光加上去，黑 = 全透）。
    不用黑底图 + 'lighter'：离屏画布上夜空顶上是渐隐的透明，黑底图的"黑"是不透明的，叠上去是一块黑。
  · moon_src.png：黑底上一轮满月（moon_alt 另一张）→ 按亮度找出圆盘、边缘羽化一点，存成透明底。月晕引擎里画。
  · rabbits_src.png：品红幕 2×2 四只失重漂着的玉兔（抱药杵 / 提灯笼 / 蜷着睡 / 张开手脚），都朝右（rabbits_alt 另一组）→ 按连通块切四张，
    烘一圈银蓝外发光（同 tides/make.py 小兵）。
薄纱、星星、星尘是引擎里现画的（sea.js MoonSky）。
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from tidekit import seam
from crewart import cut, edge_extend

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'web', 'assets', 'world')
save = lambda im, name, q=88: (im.save(os.path.join(OUT, name), 'WEBP', quality=q, method=6),
                               print(f'  {name} {im.width}×{im.height} {os.path.getsize(os.path.join(OUT, name)) // 1024}KB'))

# 银河：原图 1536×1024，星带在 y ≈ 260~740（每行最亮通道均值 > 10）；裁 ROWS，拼缝后宽 1216，缩 K
ROWS, GK = (220, 780), 0.62
g = np.array(Image.open(os.path.join(HERE, 'galaxy_src.png')).convert('RGB')).astype(np.float32)[ROWS[0]:ROWS[1]]
A = seam(g, np.ones(g.shape[:2], np.float32))
ga = A[..., :3].max(-1, keepdims=True) / 255
im = Image.fromarray(np.dstack([A[..., :3] / np.maximum(ga, 1 / 255), ga * 255]).clip(0, 255).astype(np.uint8), 'RGBA')
save(im.resize((round(im.width * GK), round(im.height * GK)), Image.LANCZOS), 'moonsky_galaxy.webp')

# 明月：圆盘 = 最亮通道 > 120 的最大连通块补洞；边缘往里羽化 MF 像素（原图外圈一层柔光，硬切会有一圈白边）。缩到直径 MD
MD, MF = 320, 6
m = Image.open(os.path.join(HERE, 'moon_src.png')).convert('RGB')
c = np.array(m).astype(np.float32)
disc = ndimage.binary_fill_holes(c.max(2) > 120)
lab, n = ndimage.label(disc)
disc = lab == (np.argmax(ndimage.sum(disc, lab, range(1, n + 1))) + 1)
ys, xs = np.nonzero(disc)
x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
al = ndimage.gaussian_filter(ndimage.binary_erosion(disc, iterations=MF).astype(np.float32), MF / 2)
px = np.dstack([c, al[..., None] * 255])[y0:y1, x0:x1].clip(0, 255).astype(np.uint8)
save(Image.fromarray(px, 'RGBA').resize((MD, MD), Image.LANCZOS), 'moonsky_moon.webp')

# 玉兔：同 tides/make.py mobs —— 连通块最大的四块，按所在格子命名，高 HGT，外发光留边 PAD（18 时外发光在贴图边上被切成方框）
HGT, PAD, GLOW = 130, 32, (205, 218, 255)
NAMES = {(0, 0): 'rabbit1', (1, 0): 'rabbit2', (0, 1): 'rabbit3', (1, 1): 'rabbit4'}   # 抱药杵 / 提灯笼 / 蜷着睡 / 张开手脚
rgb, al = cut(os.path.join(HERE, 'rabbits_src.png'), 'magenta', (40, 150))
rgb = edge_extend(rgb, al)
lab, n = ndimage.label(al > 0.5)
sz = ndimage.sum(np.ones_like(al), lab, range(1, n + 1))
H, W = al.shape
for i in np.argsort(sz)[::-1][:4]:
    ys, xs = np.nonzero(lab == i + 1)
    cell = (int(xs.mean() > W / 2), int(ys.mean() > H / 2))
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    keep = ndimage.binary_dilation(lab == i + 1, iterations=4)[y0:y1, x0:x1]
    sp = Image.fromarray(np.dstack([rgb[y0:y1, x0:x1], al[y0:y1, x0:x1] * keep * 255]).clip(0, 255).astype(np.uint8), 'RGBA')
    sp = sp.resize((round(sp.width * HGT / sp.height), HGT), Image.LANCZOS)
    res = Image.new('RGBA', (sp.width + 2 * PAD, sp.height + 2 * PAD))
    body = Image.new('RGBA', res.size); body.alpha_composite(sp, (PAD, PAD))
    sil = body.split()[3]
    for grow, blur, col, k in [(15, 12, GLOW, 0.8), (5, 4, (245, 248, 255), 0.9)]:
        L = Image.new('RGBA', res.size, col + (0,))
        L.putalpha(sil.filter(ImageFilter.MaxFilter(grow)).filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * k)))
        res.alpha_composite(L)
    res.alpha_composite(body)
    save(res, f'moonsky_{NAMES[cell]}.webp', 90)
