"""G13 绳子复查：① 叠回去（body + rope 在前）和 G13.png 逐像素比；② 绳子中心线 ±7 px 带子里合成图的透明块（>4 px 算洞）；
③ 绳子层自己在带子里的透明块，只允许落在手肘 / 大腿 / 小腿三处遮挡；④ 小腿段（x ≥ 1300）下沿逐列：相邻列最大跳变、正下方有没有深棕描边。"""
import numpy as np
from PIL import Image
from scipy import ndimage
CO = (-7.10200401e-05, 1.59854088e-01, 3.98340456e+02)
body = Image.open('ref/G13_body.png'); rope = Image.open('ref/G13_rope.png'); comp = Image.open('ref/G13.png')
st = body.copy(); st.alpha_composite(rope)
d = np.abs(np.array(st).astype(int) - np.array(comp).astype(int)).max()
print('① 叠回 vs 合成图 最大像素差', d)
W, H = comp.size; yy, xx = np.mgrid[0:H, 0:W]; yc = np.polyval(CO, xx); band = np.abs(yy - yc) <= 7
ca = np.array(comp)[..., 3]; lab, n = ndimage.label(band & (ca < 128))
sz = ndimage.sum(np.ones_like(ca), lab, range(1, n + 1)) if n else []
print('② 合成图带子里透明块', n, '个，最大', int(max(sz)) if n else 0, 'px')
ra = np.array(rope)[..., 3]; ba = np.array(body)[..., 3]
lab, n = ndimage.label(band & (ra < 128))
print('③ 绳子层带子里的空缺：')
for i, o in enumerate(ndimage.find_objects(lab)):
    m = lab[o] == i + 1
    if m.sum() > 4: print('   x', o[1].start, '~', o[1].stop, ' y', o[0].start, '~', o[0].stop, m.sum(), 'px，人层不透明占', f'{(ba[o][m] > 128).mean():.0%}')
rgb = np.array(comp)[..., :3].astype(int)
bot, dark = [], 0
for x in range(1300, W):
    col = np.nonzero((ba[:, x] > 128) & (np.abs(np.arange(H) - yc[0, x]) <= 12))[0]
    if not len(col): continue
    y = col.max(); bot.append(y)
    below = rgb[y + 1:y + 3, x]
    dark += int((below.sum(1) < 200).any())
bot = np.array(bot)
print(f'④ 小腿下沿 {len(bot)} 列：相邻列最大跳变 {np.abs(np.diff(bot)).max()} px；正下方 2 px 内有深棕描边的列 {dark}/{len(bot)}')
