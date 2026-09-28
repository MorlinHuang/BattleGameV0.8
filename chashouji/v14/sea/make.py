"""白娘子海水里的虾兵蟹将（2026-09-28）：绿幕原图 → 抠像、裁边、缩到屏幕大小的单层贴图（不烘外发光：它们是海里的小兵，不是主角）。
用法：python3 v14/sea/make.py      → web/assets/world/sea_shrimp1.webp … sea_crab2.webp

两只虾、两只蟹各一张，同一轮生图挑的（都朝右 —— 冲着男生那边去；sea.js 里朝左游的就水平翻过来画）。
**绿幕**：一身红橙 + 金盔，品红幕在红上会抠穿。高度按屏幕像素定（sea.js 直接按原大画）：
虾 150（主角身高的三分之一出头，远看认得出是只拿枪的虾）、蟹 120（横着宽，面积跟虾差不多）。"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from crewart import cut, edge_extend

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, '../../web/assets/world')
for name, h in [('shrimp1', 150), ('shrimp2', 150), ('crab1', 120), ('crab2', 120)]:
    rgb, al = cut(os.path.join(HERE, name + '_src.png'), 'green', (60, 150))
    rgb = edge_extend(rgb, al)
    ys, xs = np.nonzero(al > 0.05)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    im = Image.fromarray(np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8)[y0:y1, x0:x1], 'RGBA')
    K = h / im.height
    im = im.resize((round(im.width * K), h), Image.LANCZOS)
    im.save(os.path.join(OUT, f'sea_{name}.webp'), 'WEBP', quality=90, method=6)
    print(name, im.size)
