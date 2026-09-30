"""动作条里相邻两格粘连（手 / 道具碰到隔壁的鞋）时，frames.py 按连通块切不开。
按手写的判定把每个像素分给某一格，再把四格重新排到一张格距留足的画布上（背景色照原图），frames.py 读新图。
用法：python3 relayout.py <原图> <新图> <规则名>；规则在 RULES 里，(x, y) 是原图像素 → 格号 0~3（阅读顺序）。"""
import sys
import numpy as np
from PIL import Image

RULES = {
    # B6 act_a2：左下格抛出去的手（x < 112, y 685~768）碰到左上格的鞋
    'b6a2': lambda x, y: np.where(x < 560, np.where((y < 768) & ~(((x < 112) & (y > 690)) | ((x < 125) & (y > 745))), 0, 2), np.where(y < 760, 1, 3)),
    # B28 act_a1：左格背上的钉耙齿（x 505~560）碰到右格的鞋，上下两行各一处
    'b28a1': lambda x, y: np.where(y < 768,
                                   np.where((x < 505) | ((x < 560) & (y < 585)), 0, 1),
                                   np.where((x < 505) | ((x < 560) & (y < 1268)), 2, 3)),
}

src, dst, rule = sys.argv[1:4]
im = np.array(Image.open(src).convert('RGBA'))
H, W = im.shape[:2]
yy, xx = np.mgrid[:H, :W]
lab = RULES[rule](xx, yy)
bg = im[4, 4].copy()
G = 160                                     # 格与格之间多留的空
out = np.zeros((H + G, W + G, 4), np.uint8); out[:] = bg
for k in range(4):
    ox, oy = (k % 2) * G, (k // 2) * G
    m = lab == k
    tgt = out[oy:oy + H, ox:ox + W]
    tgt[m] = im[m]
Image.fromarray(out).save(dst)
print(dst, out.shape)
