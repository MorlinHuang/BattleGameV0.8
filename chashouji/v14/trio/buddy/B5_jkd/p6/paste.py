"""生成图 → 按蒙版外的腿（底图 y >= ycut 的剪影）模板匹配对齐（缩放 + 平移），只取蒙版透明区贴回底图（B28 做法）。
用法：python3 p6/paste.py <帧名 hitC|hitD|idle2> <gen.png> [ycut] [feather]
产物 raw/p6_<帧名>.png（RGBA 透明底，原底图像素 = 腿脚逐像素不变）。"""
import sys, os, json, numpy as np
sys.path.insert(0, '/workspace/art/chashouji/v14'); sys.path.insert(0, '/workspace/art/chashouji/v14/trio/tools')
from frames import gray, find, resize
from PIL import Image
from scipy import ndimage
name, gp = sys.argv[1], sys.argv[2]
ycut = int(sys.argv[3]) if len(sys.argv) > 3 else 660
fe = int(sys.argv[4]) if len(sys.argv) > 4 else 8
pre = os.environ.get('P6PRE', 'p6')   # p6d = 返修版文件名前缀
BASEP, MASKP, OUTP = f'raw/{pre}_{name}_base.png', f'raw/{pre}_{name}_mask.png', f'raw/{pre}_{name}.png'
src = {'hitC': 'hitA', 'hitD': 'hitB', 'idle2': 'idle'}[name]
ba = np.load(f'p6/{src}_alpha.npy')
brgb = np.array(Image.open(BASEP).convert('RGB')).astype(np.float32)
base = Image.fromarray(np.dstack([brgb, ba * 255]).astype(np.uint8), 'RGBA')
g = Image.open(gp).convert('RGBA')
if np.array(g)[..., 3].min() > 250:                     # 不透明幕布：抠
    from crewart import cut
    g.convert('RGB').save('/tmp/_g.png'); r, a = cut('/tmp/_g.png', 'magenta', (40, 150))
    g = Image.fromarray(np.dstack([r, a * 255]).clip(0, 255).astype(np.uint8), 'RGBA')
# 模板：底图腿（ycut 以下的剪影框）
ys, xs = np.nonzero(ba[ycut:] > 0.5); box = (xs.min() - 6, ycut, xs.max() + 7, ycut + ys.max() + 7)
tpl = gray(base.crop(box))
bh = np.ptp(np.nonzero(ba > 0.5)[0]); gy = np.nonzero(np.array(g)[..., 3] > 128)[0]
def search(ss):
    best = None
    for s in ss:
        r = find(gray(resize(g, s)), tpl)
        if r and (best is None or r[2] > best[0]): best = (r[2], s, r)
    return best
best = search(np.arange(0.6, 1.1, 0.03))                     # 粗找再细找（逐 0.005 全扫一张要 5 分钟）
best = search(np.arange(best[1] - 0.03, best[1] + 0.03, 0.005))
sc, s, r = best
gx, gy0 = box[0] - r[1], box[1] - r[0]
print(f'{name}: 缩放 {s:.3f}  腿匹配 {sc:.3f}  平移 {gx:.1f},{gy0:.1f}')
G = np.array(g.transform((1024, 1024), Image.AFFINE, (1 / s, 0, -gx / s, 0, 1 / s, -gy0 / s), Image.BICUBIC)).astype(np.float32)
mk = np.array(Image.open(MASKP))[..., 3] < 128            # True = 重画区
w = ndimage.distance_transform_edt(mk)                                          # 蒙版内到边的距离
w = np.clip(w / fe, 0, 1)
ga = G[..., 3] / 255
w = np.where((ga < 0.5) & (w < 1), 0, w)                                       # 渐变带里生成图是空的地方留原图
w = w[..., None]
al = ga[..., None] * w + ba[..., None] * (1 - w)
rgb = (G[..., :3] * ga[..., None] * w + brgb * ba[..., None] * (1 - w)) / np.maximum(al, 1e-3)
out = np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8)
# 去掉碎块
lab, k = ndimage.label(out[..., 3] > 20); sz = ndimage.sum(np.ones(lab.shape), lab, range(1, k + 1))
out[..., 3] *= ~np.isin(lab, np.nonzero(sz < 60)[0] + 1)
Image.fromarray(out, 'RGBA').save(OUTP)
json.dump({'gen': gp, 'scale': s, 'score': float(sc), 'offset': [float(gx), float(gy0)], 'ycut': ycut, 'feather': fe},
          open(f'p6/{pre}_{name}_paste.json' if pre != 'p6' else f'p6/{name}_paste.json', 'w'))
