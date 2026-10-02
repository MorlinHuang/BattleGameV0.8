# 生成图配回底图（按保留区灰度模板找缩放 + 平移），只取蒙版区（6px 渐变）贴回原 cell：python3 reg.py <帧> <gen.png> <out.png>
import sys, numpy as np
sys.path.insert(0, '/workspace/art/chashouji/v14/trio/tools')
from frames import gray, find, resize
from PIL import Image
from scipy import ndimage
f, gp, out = sys.argv[1:4]
S, OX, OY = 2, 68, 125
cell = Image.open(f'/tmp/g29/{f}_cell.png').convert('RGBA'); cw, ch = cell.size
base = Image.open(f'/tmp/g29/{f}_base.png').convert('RGB')
keep = np.array(Image.open(f'/tmp/g29/{f}_mask.png'))[..., 3] > 128
key = lambda X: np.clip(((X[..., 0] + X[..., 2]) / 2 - X[..., 1] - 40) / 110, 0, 1)   # 品红幕
lm = ndimage.binary_erosion(keep, iterations=16) & (key(np.array(base).astype(float)) < 0.5)
ys, xs = np.nonzero(lm); box = (xs.min(), ys.min(), xs.max(), ys.max())
tpl = gray(base.crop(box)); g4 = Image.open(gp).convert('RGBA')
g = Image.new('RGBA', g4.size, (255, 0, 255, 255)); g.alpha_composite(g4); g = g.convert('RGB')   # 生成图常是透明底：铺回品红幕再按幕布键
q = 0.25; tq = gray(resize(base.crop(box), q)); best = None
for s in np.arange(0.70, 0.95, 0.01):          # 粗：1/4 分辨率
    r = find(gray(resize(g, s * q)), tq)
    if r and (best is None or r[2] > best[0]): best = (r[2], s, r)
s0 = best[1]; best = None
for s in np.arange(s0 - 0.012, s0 + 0.013, 0.003):   # 细：原分辨率
    r = find(gray(resize(g, s)), tpl)
    if r and (best is None or r[2] > best[0]): best = (r[2], s, r)
sc, s, r = best; gx, gy = box[0] - r[1], box[1] - r[0]
print(f'{f}: scale {s:.3f} score {sc:.3f} offset {gx},{gy}')
C = Image.new('RGB', (1024, 1024), (255, 0, 255)); C.paste(resize(g, s), (int(gx), int(gy)))
G = np.array(C).astype(np.float32); a = 1 - key(G)
rgb = np.where(a[..., None] > 0.02, (G - (1 - a[..., None]) * np.array([255, 0, 255])) / np.maximum(a[..., None], 0.02), 0).clip(0, 255)
new = Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8)).crop((OX, OY, OX + cw * S, OY + ch * S)).resize((cw, ch), Image.LANCZOS)
w = np.clip(ndimage.distance_transform_edt(~keep) / 6, 0, 1)[OY:OY + ch * S:S, OX:OX + cw * S:S][..., None]
N, O = np.array(new).astype(np.float32), np.array(cell).astype(np.float32)
pm = lambda X: np.dstack([X[..., :3] * X[..., 3:] / 255, X[..., 3:]])
o = pm(N) * w + pm(O) * (1 - w)
res = np.dstack([o[..., :3] * 255 / np.maximum(o[..., 3:], 1e-3), o[..., 3:]]).clip(0, 255).astype(np.uint8)
Image.fromarray(res).save(out)
