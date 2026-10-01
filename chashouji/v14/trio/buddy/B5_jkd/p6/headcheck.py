"""新帧头大小 vs 底图头大小：底图头框作模板，在新帧（缩放 0.85~1.15）里找，打印最佳缩放（>1 = 新帧头大）。另手量黑发宽。"""
import sys, numpy as np
sys.path.insert(0, '/workspace/art/chashouji/v14/trio/tools')
from frames import gray, find, resize
from PIL import Image
name, box = sys.argv[1], [int(v) for v in sys.argv[2].split(',')]
src = {'hitC': 'hitA', 'hitD': 'hitB', 'idle2': 'idle'}[name]
ba = np.load(f'p6/{src}_alpha.npy'); br = np.array(Image.open(f'raw/p6_hitC_base.png' if name=='hitC' else f'raw/p6_{name}_base.png').convert('RGB'))
base = Image.fromarray(np.dstack([br, ba * 255]).astype(np.uint8), 'RGBA')
new = Image.open(__import__('os').environ.get('NEWP', f'raw/p6_{name}.png'))
t = gray(base.crop(box))
res = [(find(gray(resize(new, s)), t), s) for s in np.arange(0.85, 1.16, 0.01)]
r, s = max(res, key=lambda q: q[0][2])
print(f'{name} 头：新帧需缩 {s:.2f} 才对上底图头（匹配 {r[2]:.2f}）→ 新帧头是底图的 {1/s:.3f} 倍；新帧头在 ({r[1]/s:.0f},{r[0]/s:.0f})')
def hair(im, y0, y1):
    a = np.array(im.convert('RGBA')).astype(int); d = (a[..., :3].max(2) < 60) & (a[..., 3] > 128)
    rows = [np.ptp(np.nonzero(d[y])[0]) for y in range(y0, y1) if d[y].sum() > 5]
    return max(rows) if rows else 0
