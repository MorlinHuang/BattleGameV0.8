"""走路帧按"着地脚不滑"横向对齐（frames.py build 之后跑；参数写在角色 frames.json 的 "walkfix" 里，重 build 以后要再跑一遍）。

为什么：frames.py 把走路帧（loose）横向按头对齐，但引擎 walk 每换一帧整个人固定前进 stride/2（规范 6.2），
只有"这一帧着地的那只脚、到下一帧还着地"的鞋位在格内正好差 stride/2，换帧时脚才钉得住。按头对齐时这个差四次各不一样
（B6：64 / 124 / 70 / 119 格内 px），换帧那一下脚会往前 / 往后滑二三十像素。
怎么对：一个循环四次换帧里继续着地的那只脚：接地帧前脚 → 过渡帧支撑脚 → 下一个接地帧后脚 → 过渡帧支撑脚 → 回到接地帧前脚…
四次的格内位移加起来 = 2 × stride（跟各帧怎么平移无关），所以 stride = 总和 / 2；再给每帧一个横向平移，让四次都正好 = stride/2。
量哪一点：鞋贴地那一段（剪影最低 band px）的前沿（朝左走 = 左端；倒退跑的人脚尖朝右，也是往左走，同样取左端）。
"edge": "pivot"（B5 起用）：量整只鞋（深色；"shoe": "blue" 改认蓝人字拖），前脚落地那一下钉鞋跟、后脚踮起那一下钉鞋尖（审查第四轮 3：接地时脚尖会转）。
过渡帧两只脚常并在一起，取贴地的那一块整个的左端。
用法：python3 walkfix.py <角色目录>   （读 frames.json 的 walkfix: {"ref": 平移为 0 的那一帧（= 进场最后一步那一帧，走完换待机时人不跳）, "band": 16, "min_w": 鞋至少多宽（滤掉拐杖尖）, "chain": 可选}，改 web/assets/trio/<名>.webp，打印 stride）"""
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage

d = sys.argv[1].rstrip('/'); name = os.path.basename(d)
cfg = json.load(open(os.path.join(d, 'frames.json')))['walkfix']
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../web/assets/trio/')
j = json.load(open(W + name + '.json')); cw, ch = j['cell']; names = j['frames']
atlas = Image.open(W + name + '.webp').convert('RGBA'); A = np.array(atlas)
F = ['walk1', 'walk2', 'walk3', 'walk4']
box = lambda f: (names.index(f) % 4 * cw, names.index(f) // 4 * ch)

def feet(f):
    x0, y0 = box(f); a = A[y0:y0 + ch, x0:x0 + cw, 3] > 128
    yb = np.nonzero(a.any(1))[0].max(); band = a[yb - cfg.get('band', 16):yb + 1]
    lab, k = ndimage.label(band); out = []
    for q in range(1, k + 1):
        ys, xs = np.nonzero(lab == q)
        if xs.max() - xs.min() >= cfg.get('min_w', 15): out.append((int(xs.min()), int(xs.min()), int(xs.max()), int(ys.max())))
    return sorted(out)

if cfg.get('edge') == 'pivot':
    # 整只鞋（深色、够宽的块，贴近地面线）：接地帧前脚 → 过渡帧支撑脚 这一下是鞋跟着地再放平，钉鞋跟（右端）；
    # 过渡帧支撑脚 → 接地帧后脚 这一下是鞋跟抬起、前掌不动，钉鞋尖（左端）。只看贴地 band 那一段量不到踮起来的后脚（B5 实测差 25~37 px）
    def feet(f):
        x0, y0 = box(f); c = A[y0:y0 + ch, x0:x0 + cw].astype(int); a = c[..., 3] > 128
        yb = np.nonzero(a.any(1))[0].max()
        if cfg.get('shoe') == 'blue':      # 蓝人字拖（B10）
            dark = a & (c[..., 2] > 120) & (c[..., 0] < 90) & (c[..., 2] > c[..., 1] + 30)
        else:
            dark = a & (c[..., :3].max(2) < 70)
        dark[:yb - cfg.get('shoe_h', 90)] = False
        lab, k = ndimage.label(ndimage.binary_opening(dark)); out = []
        for q in range(1, k + 1):
            ys, xs = np.nonzero(lab == q)
            if xs.max() - xs.min() >= cfg.get('min_w', 40): out.append((int(xs.min()), int(xs.min()), int(xs.max()), int(ys.max())))
        return sorted(out)
    heel = lambda g: (lambda f: g(f)[2]); toe = lambda g: (lambda f: g(f)[1])
    fr = lambda f: ft[f][0]; bk = lambda f: ft[f][-1]; sp = lambda f: max(ft[f], key=lambda c: (c[3], c[2] - c[1]))
    T = [('walk1', 'walk2', heel(fr), heel(sp)), ('walk2', 'walk3', toe(sp), toe(bk)),
         ('walk3', 'walk4', heel(fr), heel(sp)), ('walk4', 'walk1', toe(sp), toe(bk))]
ft = {f: feet(f) for f in F}
front = lambda f: ft[f][0][0]
back = lambda f: ft[f][-1][0]
support = lambda f: max(ft[f], key=lambda c: (c[3], c[2] - c[1]))[0]
# 四次换帧：(从, 到, 从那帧的哪只脚, 到那帧的哪只脚)
if cfg.get('edge') != 'pivot':
    T = [('walk1', 'walk2', front, support), ('walk2', 'walk3', support, back),
         ('walk3', 'walk4', front, support), ('walk4', 'walk1', support, back)]
if 'chain' in cfg and cfg.get('edge') != 'pivot':      # 步态特殊的人手写每次换帧继续着地的是哪只脚（B29 拄拐：过渡帧也是一前一后两脚着地，后脚是支撑）
    G = {'front': front, 'back': back, 'support': support}
    T = [(a, b, G[ga], G[gb]) for (a, b), (ga, gb) in zip([('walk1', 'walk2'), ('walk2', 'walk3'), ('walk3', 'walk4'), ('walk4', 'walk1')], cfg['chain'])]
D = [gb(b) - ga(a) for a, b, ga, gb in T]
stride = sum(D) / 2; half = stride / 2
sh = {'walk1': 0.0}
for (a, b, _, _), dd in zip(T[:3], D[:3]): sh[b] = sh[a] + half - dd      # 让 (到 − 从) + 平移差 = stride/2
ref = cfg.get('ref', 'walk1'); base = sh[ref]
sh = {f: round(v - base + cfg.get('offset', 0)) for f, v in sh.items()}   # offset：格子一边不够宽时整体再挪（走完换待机那一下人会跳 offset × s）
print(name, '鞋', ft)
print('四次换帧格内位移（平移前）', D, '→ stride', round(stride, 1))
print('每帧横向平移（格内 px，+ = 往右）', sh)
for f, s in sh.items():
    if not s: continue
    x0, y0 = box(f); c = A[y0:y0 + ch, x0:x0 + cw].copy()
    xs = np.nonzero((c[..., 3] > 0).any(0))[0]
    if xs.min() + s < 0 or xs.max() + s >= cw: sys.exit(f'{f} 平移 {s} 会出格（内容 x {xs.min()}~{xs.max()}，格宽 {cw}），换一个 ref')
    A[y0:y0 + ch, x0:x0 + cw] = np.roll(c, s, axis=1)
Image.fromarray(A).save(W + name + '.webp', 'WEBP', quality=90, method=6)
# 复核
ft = {f: feet(f) for f in F}; D2 = [gb(b) - ga(a) for a, b, ga, gb in T]
print('平移后四次换帧格内位移', D2, '（都应 ≈ stride/2 =', round(half, 1), '）')
