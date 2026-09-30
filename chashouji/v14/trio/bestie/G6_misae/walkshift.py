"""G6 跑步条换帧钉脚（2026-10-01 验收收紧到 ≤ 2 屏幕 px）：frames.py 的 loose 帧横向按头对齐，四帧里人的前后位置画得不均，
着地拖鞋鞋跟每次换帧退 82 / 92 / 86 / 90 格内 px，引擎每帧前进 stride / 2 = 87.5，同一只脚换帧差 −5.5 / +4.5 / −1.5 / +2.5（× 0.88 最大 4.8 屏幕 px）。
这里在图集上量鞋跟（y ≥ 360 的不透明连通块，左沿 = 鞋跟），按"每次换帧正好退 87.5"解出四帧的整格横移（walk3 后脚贴着格左沿，挪不动的帧由整条一起加的常数让开），取整以后每次换帧差 ≤ 0.5 格内 px。
横移量是按当前图集量出来算的：已经对齐的图集再跑，算出来是 0，不会重复挪。每次 frames.py build 之后跑一次（在 chashouji 下：python3 v14/trio/bestie/G6_misae/walkshift.py）。"""
import os, math, numpy as np
from PIL import Image
from scipy import ndimage

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio/G6_misae.webp')
CW, CH, COLS = 316, 403, 4
NAMES = ['idle', 'wind', 'throw', 'follow', 'walk1', 'walk2', 'walk3', 'walk4']
STEP, Y0 = 175 / 2, 360


def cell(a, n):
    i = NAMES.index(n); return i // COLS * CH, i % COLS * CW


def shoes(a, n):
    y, x = cell(a, n)
    m = a[y + Y0:y + CH, x:x + CW, 3] > 128
    lab, k = ndimage.label(m)
    return sorted(int(np.nonzero(lab == j)[1].min()) for j in range(1, k + 1) if (lab == j).sum() >= 60)


a = np.array(Image.open(P).convert('RGBA'))
s1, s2, s3, s4 = (shoes(a, n) for n in ('walk1', 'walk2', 'walk3', 'walk4'))
assert len(s1) == 2 and len(s2) == 1 and len(s3) == 2 and len(s4) == 1, (s1, s2, s3, s4)
# 换帧：walk1 前脚 → walk2 着地脚 → walk3 后脚；walk3 前脚 → walk4 着地脚 → walk1 后脚。每次应退 STEP
err = [(s2[0] - s1[1]) + STEP, (s3[0] - s2[0]) + STEP, (s4[0] - s3[1]) + STEP, (s1[0] - s4[0]) + STEP]
# 连续解：walk1 记 0，walk2~4 各自相对它挪多少；四帧再一起加一个整数 c（整条一起挪不改换帧差），挑 |c| 最小、四帧都不把内容挪出格子的那个。
# 各自取整（.5 向 0 取，已经对齐的图集再跑算出来全是 0），余差不累积
def free(n):
    y, x = cell(a, n); xs = np.nonzero(a[y:y + CH, x:x + CW, 3].any(0))[0]
    return xs.min(), CW - 1 - xs.max()
rnd = lambda v: int(math.copysign(math.floor(abs(v) + 0.5 - 1e-6), v))
X = {'walk1': 0.0, 'walk2': -err[0]}; X['walk3'] = X['walk2'] - err[1]; X['walk4'] = X['walk3'] - err[2]
for c in sorted(range(-20, 21), key=abs):
    SHIFT = {n: rnd(v + c) for n, v in X.items()}
    if all(-free(n)[0] <= d <= free(n)[1] for n, d in SHIFT.items()): break
d1, d2, d3, d4 = (SHIFT[n] for n in ('walk1', 'walk2', 'walk3', 'walk4'))
left = [err[0] + d2 - d1, err[1] + d3 - d2, err[2] + d4 - d3, err[3] + d1 - d4]
print('鞋跟', s1, s2, s3, s4, '换帧差（格内）', err, '→ 横移', SHIFT, '→ 余差', left)
for n, d in SHIFT.items():
    if not d: continue
    y, x = cell(a, n)
    c = a[y:y + CH, x:x + CW].copy()
    gone = c[:, -d:] if d > 0 else c[:, :-d]
    assert not gone[..., 3].any(), n   # 卷出去（绕到另一边）的那几列必须是空的（上面挑 c 时已经保证）
    a[y:y + CH, x:x + CW] = np.roll(c, d, axis=1)
if any(SHIFT.values()):
    Image.fromarray(a).save(P, 'WEBP', quality=90, method=6)   # 同 frames.py
