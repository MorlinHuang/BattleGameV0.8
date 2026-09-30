"""闺蜜后排 walk 钉脚 / 换帧鞋跟读数（规范 8.4 walk 项；量法同 shots/trio_std/审4_B5鞋位.py：图集里那只鞋的模板到胶片里找，读鞋框左沿 = 鞋跟）。
用法：python3 walkheel.py <胶片(无后缀)...> -- <图集> <cellW>x<cellH> <帧名,...> <id> <s> <鞋框 json>
鞋框 json：{"walk1": {"front": [x0,y0,x1,y1], "rear": [...]}, ...}（格内像素，面朝右：左沿是鞋跟）
打印每格每只鞋的屏幕 x（鞋跟），同一帧名连续格的 Δ，以及换帧时同一只着地脚前后的差（配对写在 PAIRS）。"""
import sys, os, json, numpy as np
from PIL import Image
from scipy.signal import fftconvolve
i = sys.argv.index('--'); films = sys.argv[1:i]
atlas, cell, names, who, S, boxes = sys.argv[i + 1:i + 7]
cw, ch = map(int, cell.split('x')); names = names.split(','); S = float(S); SH = json.loads(boxes)
PAIRS = json.loads(sys.argv[i + 7]) if len(sys.argv) > i + 7 else []
at = Image.open(atlas).convert('RGBA')
def tpl(fn, box):
    k = names.index(fn); c = at.crop(((k % 4) * cw, (k // 4) * ch, (k % 4 + 1) * cw, (k // 4 + 1) * ch)).crop(box)
    c = c.resize((max(1, round(c.width * S)), max(1, round(c.height * S))), Image.LANCZOS); a = np.asarray(c).astype(float) / 255
    return a[..., :3], (a[..., 3] > 0.9).astype(float)
def find(I, fn, box, y0, y1):
    t, m = tpl(fn, box); J = I[y0:y1]; num = 0
    for c in range(3):
        T = t[..., c] * m
        num += fftconvolve(J[..., c] ** 2, m[::-1, ::-1], 'valid') - 2 * fftconvolve(J[..., c], T[::-1, ::-1], 'valid') + (T ** 2).sum()
    num /= m.sum() * 3; yy, xx = np.unravel_index(np.argmin(num), num.shape); dx = 0
    if 0 < xx < num.shape[1] - 1:
        a, b, c = num[yy, xx - 1], num[yy, xx], num[yy, xx + 1]; d = a - 2 * b + c; dx = 0.5 * (a - c) / d if d > 0 else 0
    return xx + dx, num[yy, xx]
Y = [int(v) for v in os.environ.get('WALK_Y', '900,1100').split(',')]   # 竖向搜索窗（屏幕 y）：只框脚那一带，别让模板拐到主角的衣服上
XW = [int(v) for v in os.environ.get('WALK_X', '0,960').split(',')]    # 横向搜索窗（屏幕 x）：G6 粉拖鞋和主角的粉短裤在同一高度，要把主角那一段切掉
rows = []
for f in films:
    I = np.asarray(Image.open(f + '.png').convert('RGB')).astype(float) / 255; fr = json.load(open(f + '.json'))
    print('==', f)
    for k, r in enumerate(fr):
        fn = [x.split(':')[1] for x in r if x.startswith(who + ':')]
        if not fn or fn[0] not in SH: continue
        fn = fn[0]; out = {}
        for foot, box in SH[fn].items():
            x, e = find(I[:, k * 960 + XW[0]:k * 960 + XW[1]], fn, box, *Y)
            x += XW[0]
            out[foot] = round(float(x), 1)
        rows.append((f, k + 1, fn, out)); print(k + 1, fn, out)
print('== 同一帧名连续格（着地鞋 Δ）')
for a, b in zip(rows, rows[1:]):
    if a[0] == b[0] and a[2] == b[2] and b[1] == a[1] + 1:
        print(a[0], f'格{a[1]}→{b[1]}', a[2], {ft: round(b[3][ft] - a[3][ft], 2) for ft in a[3]})
print('== 换帧：同一只着地脚鞋跟前后差（验收 ≤ 6）')
for a, b in zip(rows, rows[1:]):
    if a[0] != b[0] or b[1] != a[1] + 1 or a[2] == b[2]: continue
    for fa, fb, ta, tb in PAIRS:
        if a[2] == fa and b[2] == fb:
            print(a[0], f'格{a[1]}→{b[1]}', f'{fa}.{ta} {a[3][ta]} → {fb}.{tb} {b[3][tb]}', 'Δ', round(b[3][tb] - a[3][ta], 2))
