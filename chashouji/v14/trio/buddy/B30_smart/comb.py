"""B30 杀马特的飞梳子（平面道具）→ web/assets/trio/prop_comb.webp。
生图服务 2026-09-30 下午整体 503，梳子这种小件直接程序画：赛璐璐两色 + 暖黑描边（跟 3D 道具同一个描边色 3a2c26）。
4 倍尺寸画完再缩，描边缩下来约 2.5px。尖尾梳：左边一段带齿的梳身，右边一根细长尾柄。"""
import os
from PIL import Image, ImageDraw
Z = 4
W, H = 64, 20                            # 屏幕像素（scale 1）
INK, BLUE, DARK, HI = (58, 44, 38, 255), (40, 96, 230, 255), (24, 58, 160, 255), (190, 215, 255, 255)
im = Image.new('RGBA', (W * Z, H * Z)); d = ImageDraw.Draw(im)
s = lambda *p: [v * Z for v in p]
# 梳齿（先画，梳背压在上面）
for x in range(4, 36, 3):
    d.rectangle(s(x, 8, x + 1.6, 17), fill=INK)
    d.rectangle(s(x + 0.4, 8, x + 1.2, 16.2), fill=DARK)
# 梳背 + 尾柄：一个多边形
body = [(2, 3), (38, 3), (62, 8.5), (62, 10), (38, 9.5), (2, 9.5)]
d.polygon([(x * Z, y * Z) for x, y in body], fill=BLUE, outline=INK)
d.line([(x * Z, y * Z) for x, y in body + [body[0]]], fill=INK, width=int(2.4 * Z), joint='curve')
d.polygon([(x * Z, y * Z) for x, y in [(4, 4.4), (36, 4.4), (52, 7.6), (36, 5.9), (4, 5.9)]], fill=HI)   # 高光
out = im.resize((W, H), Image.LANCZOS)
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio/prop_comb.webp')
out.save(p, 'WEBP', quality=92, method=6)
out.resize((W * 6, H * 6), Image.NEAREST).save('/tmp/comb_x6.png')
print('→', os.path.normpath(p), out.size)
