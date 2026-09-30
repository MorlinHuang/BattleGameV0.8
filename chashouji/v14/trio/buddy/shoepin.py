"""胶片上直接量走路换帧时"继续着地那只脚"的鞋跟 / 鞋尖屏幕 x（审查第四轮 3：同一只着地脚量鞋跟，差 ≤ 6 px）。
鞋 = 地面线附近的深色块（黑布鞋；横向只看黄衣服那几列 ± 70），不做模板匹配（换帧时鞋的画法会变，模板对不上）。
每格：at.y 往上 h 像素、x 在 [xa, xb] 里 max(RGB) < 70 的连通块，宽 ≥ w 的算一只鞋；左端 = 鞋尖（朝左走），右端 = 鞋跟。
换帧：前一格最左那只（接地帧前脚）/ 唯一那只（过渡帧支撑脚）/ 最右那只（接地帧后脚）按 walkfix pivot 的链：
  walk1→walk2、walk3→walk4 钉鞋跟：前一格前脚鞋跟 vs 后一格支撑脚鞋跟；walk2→walk3、walk4→walk1 钉鞋尖：支撑脚鞋尖 vs 后脚鞋尖。
用法：python3 shoepin.py <at_y> <xa> <xb> <胶片.png> ... [shoe=blue] [body=none]（胶片旁边同名 .json = 帧名表；格宽 960）"""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage
opt = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a); sys.argv = [a for a in sys.argv if '=' not in a]
ay = int(sys.argv[1]); xa, xb = int(sys.argv[2]), int(sys.argv[3]); H, WMIN, CW = 80, 30, 960
BLUE = opt.get('shoe') == 'blue'          # shoe=blue：蓝人字拖（B10）；body=none：不按黄衣服限横向范围（胶片里只召了这一个人时用）
def shoes(I, k):
    xa, xb = 0, CW
    if opt.get('body') != 'none':
        y = I[ay - 260:ay - 20, k * CW:(k + 1) * CW].astype(int)      # 这个人的横向范围 = 黄衣服（B5 连体衣）那几列 ± 70
        cols = np.nonzero(((y[..., 0] > 200) & (y[..., 1] > 160) & (y[..., 2] < 90)).sum(0) > 8)[0]
        if not len(cols): return []
        xa, xb = max(0, cols.min() - 70), min(CW, cols.max() + 70)
    c = I[ay - H:ay + 4, k * CW + xa:k * CW + xb].astype(int)
    shoe = ((c[..., 2] > 120) & (c[..., 0] < 90) & (c[..., 2] > c[..., 1] + 30)) if BLUE else (c.max(2) < 70)
    d = ndimage.binary_opening(shoe); lab, n = ndimage.label(d); out = []
    for q in range(1, n + 1):
        ys, xs = np.nonzero(lab == q)
        if xs.max() - xs.min() >= WMIN and ys.max() >= H - 20 - 0: out.append((xs.min() + xa, xs.max() + xa, ys.max()))
    return sorted(out)
rule = {('walk1', 'walk2'): ('front', 'only', 1), ('walk3', 'walk4'): ('front', 'only', 1),
        ('walk2', 'walk3'): ('only', 'back', 0), ('walk4', 'walk1'): ('only', 'back', 0)}
pick = {'front': lambda s: s[0], 'back': lambda s: s[-1], 'only': lambda s: max(s, key=lambda c: (c[2], c[1] - c[0])) if s else None}   # 过渡帧：贴地最低那只（提起的脚高）
worst = 0
for f in sys.argv[4:]:
    I = np.asarray(Image.open(f).convert('RGB')); names = [x[0].split(':')[1] for x in json.load(open(f[:-4] + '.json'))]   # 第一个人（只召一个人拍）
    S = [shoes(I, k) for k in range(len(names))]
    for k in range(len(names) - 1):
        a, b = names[k], names[k + 1]
        if (a, b) in rule:
            ga, gb, e = rule[(a, b)]; pa, pb = pick[ga](S[k]), pick[gb](S[k + 1])
            if pa is None or pb is None or len(S[k]) > 2 or len(S[k + 1]) > 2 or len(S[k]) + len(S[k + 1]) < 3: print(f'  {f.split("/")[-1]} 格{k+1}→{k+2} {a}→{b} 鞋没认全 {S[k]} {S[k+1]}'); continue
            dx = pb[e] - pa[e]; worst = max(worst, abs(dx))
            print(f'  {f.split("/")[-1]} 格{k+1}→{k+2} {a}→{b} {"鞋跟" if e else "鞋尖"} {pa[e]} → {pb[e]}  Δx {dx:+d}   （鞋 {[c[:2] for c in S[k]]} → {[c[:2] for c in S[k+1]]}）')
print('换帧最大 |Δx|', worst)
