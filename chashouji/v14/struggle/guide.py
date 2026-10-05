"""挣扎帧重画的引导图 → struggle/<档>/g<k>.png：**原图 base** 里输方的腿和拖鞋抹成品红，再把旧 s<k> 里的两只拖鞋原样贴到它们在 s<k> 的位置。
直接拿 s<k> 当第一张图，模型会把旧腿的毛病（小腿鼓包、一粗一细）原样照搬（10-05 aL s1 试过 4 张全照搬）；
只抹掉 s<k> 的腿也不行：s<k> 的短裤也被旧重绘改过（aK 旧帧短裤长到盖住膝盖，原图是短的），新图照着画、
build 按腰线取用时短裤一截取新图一截取原图，又是一道错位。所以底子用原图，s<k> 只贡献拖鞋落点（= 这一格的姿势）。
拖鞋上旧重绘画出来的黄眼睛（原图是白点/叉）顺手改回白色。
用法 guide.py <档> <k>"""
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(HERE, '..')
sys.path.insert(0, V)
name, k = sys.argv[1], int(sys.argv[2])
# 腿区同 build.py STRUGGLE_HIP：(这一行以下, 这一列起, 到这一列)
HIP = {'aK': (745, 0, 1536), 'aF': (640, 0, 1536), 'aL': (0, 1190, 1536),
       'bK': (700, 0, 1536), 'bF': (700, 0, 1536), 'bL': (0, 0, 390)}
lose = np.array(Image.open(f'{V}/tween/{name}/mask.png').getchannel('A')) < 128
y0, x0, x1 = HIP[name]
box = np.zeros_like(lose); box[y0:, x0:x1] = True
base = np.array(Image.open(f'{HERE}/{name}/base.png').convert('RGB')).astype(int)
a = np.array(Image.open(f'{HERE}/{name}/s{k}.png').convert('RGB')).astype(int)
fg = lambda q: (np.minimum(q[..., 0], q[..., 2]) - q[..., 1]) < 60
# 放开区同 build.py struggle_load（不含赢方那条）：腿区 + 腿区外原图没人的空地（踢高的小腿、拖鞋会伸到腰线以上）
R = lose & (box | ~ndimage.binary_dilation(fg(base) & ~box, iterations=6))
def skin(q):
    r, g, b = q[..., 0], q[..., 1], q[..., 2]
    return (r - b > 28) & (r > g) & (g > b) & (r > 150)
def slipper(q):
    """男生被拖：黑猫拖鞋（暗）；女生被拖：白兔拖鞋（亮、不偏色）"""
    return q.max(2) < 70 if name[0] == 'a' else (q.min(2) > 200) & (q.max(2) - q.min(2) < 40)
def clothes(q):
    """要原样留着的：输方短裤（男生藏青、女生粉色；女生上衣也是粉的，所以够大的块都算）外扩 3 带上描边 —— 短裤下沿就是接缝所在；
    女生被拖时盖在腿上的长发也留着，按皮肤外扩一抹会把搭在大腿上的几缕头发切出一道边（10-05 bL 引导图）"""
    r, g, b = q[..., 0], q[..., 1], q[..., 2]
    c = (b - r > 25) & (b > 60) if name[0] == 'a' else (r > 200) & (r - g > 25) & (b > g)
    # 品红幕布也满足「粉」，先扣掉；开运算 9：女生腿的描边也偏粉，细线不能算衣服
    c = ndimage.binary_opening(c & fg(q) & lose, np.ones((9, 9)))
    lab, n = ndimage.label(c)
    big = [i for i in range(1, n + 1) if (lab == i).sum() > 2000]
    out = ndimage.binary_dilation(np.isin(lab, big), iterations=3)
    if name[0] == 'b':
        # 头发：暗像素里和腿区外那一大片头发连着的（发丝细，按块大小筛会把搭在腿上的几缕筛掉）
        dark = (q.max(2) < 90) & fg(q) & lose
        lab, n = ndimage.label(dark, np.ones((3, 3)))
        ids = np.unique(lab[dark & ~box])
        out |= ndimage.binary_dilation(np.isin(lab, ids[ids > 0]), iterations=1)
    return out
# 原图：腿（皮肤外扩 9 带上描边）和拖鞋（任意大小的块都算，叠着的两只、鞋底碎块一起抹）抹成品红，短裤不动
keep = clothes(base)
erase = (ndimage.binary_dilation(skin(base) & box & lose, iterations=9) | ndimage.binary_dilation(slipper(base) & box & lose, iterations=3)) & R & ~keep
# 抹完剩下的细线（拖鞋、小腿下沿的白色反光边，离皮肤超过 9 像素）：腿区里还在的前景，开运算 7 去不掉的才是成块的东西
rest = fg(np.where(erase[..., None], 255 * np.array([1, 0, 1]), base)) & box & R & ~keep
erase |= ndimage.binary_dilation(rest & ~ndimage.binary_opening(rest, np.ones((7, 7))), iterations=2) & R & ~keep
# 旧 s<k>：只取两只拖鞋（够大的两块）
sl = ndimage.binary_closing(slipper(a) & R & ~clothes(a), np.ones((7, 7)))     # 黑猫拖鞋和藏青短裤的暗部都暗，扣掉衣服
lab, n = ndimage.label(sl)
big = [i for i in range(1, n + 1) if (lab == i).sum() > 1500]
assert len(big) == 2, (name, k, len(big))
ss = ndimage.binary_dilation(ndimage.binary_fill_holes(np.isin(lab, big)), iterations=3) & R
out = base.copy()
out[erase] = (255, 0, 255)
px = a[ss]
yellow = (px[:, 0] > 150) & (px[:, 1] > 130) & (px[:, 2] < 110)
px[yellow] = 255
out[ss] = px
Image.fromarray(out.astype(np.uint8)).save(f'{HERE}/{name}/g{k}.png')
print(name, k, '抹掉', erase.sum(), '贴拖鞋', ss.sum(), '黄改白', yellow.sum())
