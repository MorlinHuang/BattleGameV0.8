"""走路钉脚在胶片上量（规范 8.4 walk 项）：ammoms=40 胶片，着地鞋在屏幕上的位置。
  · 同一帧名的连续格：着地鞋位移 ≤ 2 px；
  · 换帧前后：继续着地的那只脚位移 ≤ 6 px（哪只脚、量哪一点和 walkfix.py 一样：鞋贴地那一段的左端；换帧链读 frames.json 的 walkfix.chain）。
鞋模板 = 图集那一格里鞋贴地那一段（带 alpha，按 at.s 缩放），在胶片那一格里做遮罩平方差匹配，抛物线亚像素。
鞋整个在画内、匹配残差低（< 0.01）的才计；后一格只在前一格位置 ±40 px 里找（两只鞋长得一样，全宽搜会锁到另一只）。
用法：python3 walkpin.py <角色目录> <at_x,at_y,s> <胶片.png> [...]"""
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.signal import fftconvolve

d = sys.argv[1].rstrip('/'); n = os.path.basename(d); who = n.split('_')[0]
wf = json.load(open(os.path.join(d, 'frames.json'))).get('walkfix', {})
ax, ay, S = map(float, sys.argv[2].split(','))
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../web/assets/trio/')
j = json.load(open(W + n + '.json')); cw, ch = j['cell']; names = j['frames']; anc = j['anchor']
atlas = Image.open(W + n + '.webp').convert('RGBA')
cell = lambda f: atlas.crop((names.index(f) % 4 * cw, names.index(f) // 4 * ch, names.index(f) % 4 * cw + cw, names.index(f) // 4 * ch + ch))
BAND = wf.get('band', 16)

def feet(f):
    a = np.array(cell(f))[..., 3] > 128
    yb = np.nonzero(a.any(1))[0].max(); band = a[yb - BAND:yb + 1]
    lab, k = ndimage.label(band); out = []
    for q in range(1, k + 1):
        ys, xs = np.nonzero(lab == q)
        if xs.max() - xs.min() >= wf.get('min_w', 15): out.append((int(xs.min()), yb - BAND, int(xs.max()) + 1, yb + 1, int(ys.max())))
    return sorted(out)
pick = {'front': lambda F: F[0], 'back': lambda F: F[-1], 'support': lambda F: max(F, key=lambda c: (c[4], c[2] - c[0]))}
chain = wf.get('chain', [['front', 'support'], ['support', 'back'], ['front', 'support'], ['support', 'back']])
KEEP = dict(zip([('walk1', 'walk2'), ('walk2', 'walk3'), ('walk3', 'walk4'), ('walk4', 'walk1')], chain))
HOLD = {'walk1': chain[0][0], 'walk2': chain[1][0], 'walk3': chain[2][0], 'walk4': chain[3][0]}   # 这一帧停着时着地的那只

def find(img, f, box, near=None):
    c = cell(f).crop(box[:4]); c = c.resize((max(1, round(c.width * S)), max(1, round(c.height * S))), Image.LANCZOS)
    t = np.asarray(c).astype(float) / 255; m = (t[..., 3] > 0.9).astype(float); t = t[..., :3]
    ey = ay + (box[1] - anc[1]) * S; y0, y1 = int(ey - 30), int(ey + 30)
    x0, x1 = 0, img.shape[1] - t.shape[1]
    if near is not None: x0, x1 = max(0, int(near - 40)), min(x1, int(near + 40))   # 两只鞋长得一样：只在上一格位置附近找，别锁到另一只上
    I = img[y0:y1 + t.shape[0], x0:x1 + t.shape[1]]; num = 0
    for k in range(3):
        T = t[..., k] * m
        num = num + fftconvolve(I[..., k] ** 2, m[::-1, ::-1], 'valid') - 2 * fftconvolve(I[..., k], T[::-1, ::-1], 'valid') + (T ** 2).sum()
    num /= m.sum() * 3
    yy, xx = np.unravel_index(np.argmin(num), num.shape); e = num[yy, xx]; dx = 0
    if 0 < xx < num.shape[1] - 1:
        a, b, cc = num[yy, xx - 1], num[yy, xx], num[yy, xx + 1]; dd = a - 2 * b + cc; dx = 0.5 * (a - cc) / dd if dd > 0 else 0
    ok = 2 < xx < num.shape[1] - 3 and e < 0.01
    return x0 + xx + dx, e, ok

same, chg = [], []
for fp in sys.argv[3:]:
    im = np.asarray(Image.open(fp).convert('RGB')).astype(float) / 255
    fr = json.load(open(fp[:-4] + '.json'))
    seq = [next((t.split(':')[1] for t in r if t.startswith(who + ':')), None) for r in fr]
    print('==', os.path.basename(fp), seq)
    for i in range(1, 12):
        a, b = seq[i - 1], seq[i]
        if a not in HOLD or b is None: continue
        cA, cB = im[:, (i - 1) * 960:i * 960], im[:, i * 960:(i + 1) * 960]
        if a == b:
            bx = pick[HOLD[a]](feet(a)); pa, ea, oka = find(cA, a, bx); pb, eb, okb = find(cB, b, bx, pa)
            tag = "" if oka and okb else f"（鞋不全在画内 / 被挡，不计；残差 {ea:.4f} {eb:.4f}）"
            if not tag: same.append(pb - pa)
            print(f'  格{i}→{i + 1} {a} 停着  着地鞋 Δx {pb - pa:+.2f}{tag}')
        elif (a, b) in KEEP:
            wa, wb = KEEP[(a, b)]
            pa, ea, oka = find(cA, a, pick[wa](feet(a))); pb, eb, okb = find(cB, b, pick[wb](feet(b)), pa)
            tag = "" if oka and okb else f"（鞋不全在画内 / 被挡，不计；残差 {ea:.4f} {eb:.4f}）"
            if not tag: chg.append(pb - pa)
            print(f'  格{i}→{i + 1} {a}→{b} 换帧  继续着地的脚 Δx {pb - pa:+.2f}{tag}')
f = lambda L: f'{max(map(abs, L)):.2f}' if L else '—'
print(f'{n}：同一帧名连续格 最大 |Δx| {f(same)}（{len(same)} 对）；换帧 最大 |Δx| {f(chg)}（{len(chg)} 次）')
