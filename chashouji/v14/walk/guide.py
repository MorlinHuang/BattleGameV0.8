"""后退步态引导图：把赢方两只拖鞋按算好的位置贴在 base 上（腿区抹成品红），生成局部重绘蒙版（只放开腿、不放开拖鞋）。
用法: guide.py <档> <N> <lift>   → walk/<档>/g<i>.png + m<i>.png（i = 1..N-1）+ plan.json
一个循环 N 格（两步）：前半步 后脚站地从身后挪到身前、前脚抬起从身前摆到身后；第 N/2 格两脚换位；后半步换另一只脚。
每只脚一直在自己那条地面线上（近脚低、远脚高），交替才看得出来。"""
import sys, json, os, numpy as np
W = os.path.dirname(os.path.abspath(__file__))       # v14/walk
from PIL import Image
from scipy import ndimage
G = os.path.join(W, '..', 'gait')
name, N, LIFT = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
out = f'{W}/{name}'; os.makedirs(out, exist_ok=True)
base = np.array(Image.open(f'{G}/{name}/base.png').convert('RGB')).astype(np.int16)
M = np.array(Image.open(f'{G}/{name}/mask.png'))[..., 3] == 0
r, g, b = base[..., 0], base[..., 1], base[..., 2]
fg = (np.minimum(r, b) - g) < 60
skin = (r - b > 28) & (r > g) & (g > b)
floor = np.nonzero((fg & M).sum(1) > 2)[0].max()
band = np.zeros_like(fg); band[floor - 130:floor + 1] = (fg & M)[floor - 130:floor + 1]
lab, n = ndimage.label(ndimage.binary_opening(band, np.ones((3, 3))))
feet = []
for i in range(1, n + 1):
    ys, xs = np.nonzero(lab == i)
    if len(xs) < 400: continue
    lo = ys.max()
    # 拖鞋 = 这只脚最低 95 行里不是皮肤的前景，闭运算补洞，外扩 2 带上描边
    y0 = lo - 95
    box = np.zeros_like(fg); box[y0:lo + 1] = (lab == i)[y0:lo + 1] | ndimage.binary_dilation(lab == i, iterations=3)[y0:lo + 1]
    s = box & fg & ~skin
    s = ndimage.binary_closing(s, np.ones((5, 5)))
    s = ndimage.binary_fill_holes(s)
    s = ndimage.binary_opening(s, np.ones((3, 3)))
    sl, k = ndimage.label(s); 
    if k == 0: continue
    big = np.argmax(ndimage.sum(s, sl, range(1, k + 1))) + 1
    s = ndimage.binary_dilation(sl == big, iterations=2) & fg
    ys2, xs2 = np.nonzero(s)
    feet.append(dict(cx=float(xs2.mean()), lo=int(ys2.max()), mask=s, x0=int(xs2.min()), x1=int(xs2.max()), y0=int(ys2.min())))
assert len(feet) == 2, len(feet)
back_dir = -1 if name[0] == 'a' else 1          # a 档女生往左退：身后 = 左
feet.sort(key=lambda f: f['cx'] * back_dir, reverse=True)    # [0] = 后脚（更靠身后）
Bk, Fr = feet
S = abs(Fr['cx'] - Bk['cx'])
def sprite(f):
    y0, y1, x0, x1 = f['y0'], f['lo'] + 1, f['x0'], f['x1'] + 1
    rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    rgba[..., :3] = base[y0:y1, x0:x1]; rgba[..., 3] = f['mask'][y0:y1, x0:x1] * 255
    return Image.fromarray(rgba), f['cx'] - x0, y1 - y0     # 锚点：横向中心、鞋底
spr = [sprite(Bk), sprite(Fr)]   # 0 号脚 = 开局的后脚，1 号 = 开局的前脚；各自一直用自己的样子和自己的地面线
lines = [Bk['lo'], Fr['lo']]
near = int(np.argmax(lines))     # 鞋底更低的那只离镜头近，最后贴（盖住远脚）
plan = dict(name=name, N=N, S=S, back=Bk['cx'], front=Fr['cx'], lines=lines, near=near, lift=LIFT, frames=[])
def pos(foot, i):
    """第 i 格这只脚：(x, 鞋底 y, 抬起, 脚尖往下转的角度)"""
    h, u = N // 2, (i % (N // 2)) / (N // 2)
    stance = foot if i >= h else 1 - foot      # 前半步 0 号脚（后脚）站地；后半步 1 号站地
    stance = 1 - stance
    # 前半步：0 号站地，从身后 → 身前；1 号摆动，从身前 → 身后。后半步对调
    first = i < h
    is_stance = (foot == 0) == first
    if is_stance:
        x = Bk['cx'] - back_dir * S * u
        return x, lines[foot], 0.0, 0.0
    x = Fr['cx'] + back_dir * S * u
    # 拖着后退是贴地蹭：第一格就抬到 LIFT，之后一直这么低地往后滑，落地前一格再放下。
    # 抬成正弦（中点最高）时摆动拖鞋正好悬在站地脚上方小腿高处，模型只能画出交叉、反折、拖鞋脱脚的腿。
    lift = LIFT * min(1.0, np.sin(np.pi * u) / np.sin(np.pi * 2 / N))
    ang = min(14.0, 22 * np.sin(np.pi * u) + 6 * (1 - u) * (u > 0))        # 抬脚时脚跟先起、脚尖往下垂
    return x, lines[foot], lift, ang
for i in range(1, N):
    can = base.copy(); can[M] = (255, 0, 255)
    im = Image.fromarray(can.astype(np.uint8)).convert('RGBA')
    keep = np.zeros(M.shape, bool)
    order = [1 - near, near]
    info = {}
    for foot in order:
        x, ly, lift, ang = pos(foot, i)
        sp, ax, ay = spr[foot]
        a = -ang * back_dir * -1      # 脚尖朝对方：a 档脚尖朝右，脚尖往下 = 顺时针 = PIL 负角
        rot = sp.rotate(-ang if back_dir < 0 else ang, resample=Image.BICUBIC, expand=True)
        # 旋转后锚点：用鞋底中心近似 —— 旋转后外框中心对齐原外框中心，再按抬起量上移
        ox = int(round(x - rot.width / 2 + (sp.width / 2 - ax)))
        oy = int(round(ly - lift - rot.height + (rot.height - sp.height) / 2))
        im.alpha_composite(rot, (ox, oy))
        al = np.zeros(M.shape, bool)
        ra = np.array(rot)[..., 3] > 128
        yy, xx = np.nonzero(ra); yy, xx = yy + oy, xx + ox; ok = (xx >= 0) & (xx < M.shape[1]) & (yy >= 0) & (yy < M.shape[0]); keep[yy[ok], xx[ok]] = True
        info[foot] = dict(x=round(x, 1), line=ly, lift=round(lift, 1), ang=round(ang, 1))
    plan['frames'].append(dict(i=i, feet=info))
    im.convert('RGB').save(f'{out}/g{i:02d}.png')
    ed = M & ~ndimage.binary_erosion(keep, iterations=2)     # 拖鞋往里收 2 像素放开：边缘让模型接上脚踝
    mk = np.zeros(M.shape + (4,), np.uint8); mk[..., 3] = np.where(ed, 0, 255)
    Image.fromarray(mk).save(f'{out}/m{i:02d}.png')
json.dump(plan, open(f'{out}/plan.json', 'w'), indent=1, ensure_ascii=False, default=float)
print(name, 'S', round(S), 'back', round(Bk['cx']), 'front', round(Fr['cx']), 'lines', lines, 'near', near)
