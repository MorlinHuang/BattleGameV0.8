"""G9 抠像验收（复审）：丝巾、粉花、衬衫三块区域的 alpha 最小值，要求 ≥ 0.95。
区域 = 框 ∩ 人物内部（alpha>0.5 填洞后向里收 3 px，去掉轮廓抗锯齿那一圈）；衬衫另按颜色（红底 / 黄花 / 绿叶）取像素。
用法：python3 g9_check.py <图> <幕布 blue|magenta>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
import layers as L
sys.path.insert(0, '../..')
from crewart import cut
path, screen = sys.argv[1], sys.argv[2]
rgb, al = L.cut_blue(path) if screen == 'blue' else cut(path, screen, (40, 150))
src = np.array(Image.open(path).convert('RGB')).astype(int); r, g, b = src[..., 0], src[..., 1], src[..., 2]
inner = ndimage.binary_erosion(ndimage.binary_fill_holes(al > 0.5), iterations=3)
def box(x0, x1, y0, y1):
    m = np.zeros_like(inner); m[y0:y1, x0:x1] = True; return m & inner
scarf, flower = box(425, 616, 247, 386), box(520, 585, 378, 435)
shirt_col = ((r > 150) & (g < 110) & (b < 110)) | ((r > 200) & (g > 150) & (b < 120)) | ((g > r) & (g > b) & (g > 80))
shirt = box(240, 720, 230, 560) & shirt_col
for name, m in [('丝巾', scarf), ('粉花', flower), ('衬衫', shirt)]:
    print(f'{name}: 像素 {m.sum()}, alpha 最小 {al[m].min():.3f}, <0.95 的 {(al[m] < 0.95).sum()}')
