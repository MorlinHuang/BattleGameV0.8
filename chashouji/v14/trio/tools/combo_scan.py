"""三人组自由组合遮挡矩阵（2026-10-01 起；同日按新判据重写）：线上每次送礼三个槽位各自从本边名单里独立随机抽一人，任意 后排 × 地板、
上方 × 后排都可能同框。这里把每个人**在场时会画的每一帧**（待机、出手 seq、进场最后落定那一帧；秋千按在场摆幅左右各转一次；
挂件层、手里拿着的道具一起）按引擎的摆法贴到屏幕上，逐帧看**画在后面的那个人**被挡了多少。

判据（2026-10-01 主控："礼物少时每个角色完整、特点清楚"，人缩小了反而认不出 —— 所以不追求外扩后完全不相交）：
  谁在后面：按 depth（上方 0.5 < 后排 0.8 < 地板 1.3，main.js 按它排远近，小的先画）。前面那个人不算被挡。
  对后面那个人的**每一帧**（前面那个人取他全部在场帧的并集 —— 两人各自出手、时机不定，哪一帧碰上哪一帧都可能）：
    · 被挡剪影占比 ≤ 8%（被挡像素 / 这一帧自己的剪影像素）；
    · 头框被挡 0 px：frames.json 的 head（参考帧上量的头框，映射到图集输出像素）在每一帧里按模板重新找一次位置；前面那人外扩 4px 再比；
    · 认人点被挡 0 px：挂件层（扇子、流苏、牛丸串……）、手里拿着的道具（hold 点、半径 = 引擎画的半径）、躯干
      （头框下沿到"头下沿 + 45% × 头下沿到脚底"那几行、头框中心左右各 1.2 个头宽以内 —— 招牌服装都在这一块），前面那人同样外扩 4px。
  前景地板在后排地面前面，挡住后排一点脚和小腿（躯干以下）本来就对，只要不超 8%。
  尺寸下限（suggest 只在这个范围里缩）：后排 s ≥ 0.8；别的槽位 ≥ 本人现值 × 0.9。先挪位置，挪不开才缩。

  帧序列（cfg.sheet）：屏幕点 = at + (格内点 − anchor) × s（trio.js place()，在场时没有位移）
  单张立绘（cfg.src）：整张图一帧；头框用剪影最上面 22% 估（没有 frames.json）
  后排的滑板哥们 / 平衡车闺蜜（原 crew.js，站位随机）2026-10-01 迁成了帧序列（crewframes.py），和别人一样按 at 摆
  还没做完的人（cast / ground 里都没有）：定妆图 ref/<编号>.png 估 —— 缩到本边同槽位已做完的人的中位高度、底边中点放到中位位置；标"估"
  fixed: true 的挂件（场景层，B18 墙头）是布景不是人，不算进剪影

每个槽位同时只站一人，只扫不同槽位之间。最后给一份建议站位（suggest），写在矩阵文件末尾。

用法（在 chashouji 下）：python3 v14/trio/tools/combo_scan.py [buddy|bestie|all] [--only=B1,B2,...]
  → shots/trio_std/组合遮挡矩阵_<边>.txt；头框映射缓存 /tmp/combo_heads.json"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.feature import match_template

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))   # chashouji/
WEB = os.path.join(ROOT, 'web')
TRIO_DIR = os.path.join(ROOT, 'v14/trio')
W, H = 960, 1334
DIL = 4                                        # 头框 / 认人点：前面那人外扩几 px 再比（留一道缝，轮廓线读得出）
RATIO = 0.08                                   # 被挡剪影占比上限
DEPTH = {'ground': 0.8, 'top': 0.5, 'floor': 1.3}
PAIRS = [('ground', 'floor', '后排 × 地板'), ('top', 'ground', '上方 × 后排'), ('top', 'floor', '上方 × 地板（附带）')]   # (后, 前)


def load_data():
    js = r"""
const fs=require('fs');const W=process.argv[1];
const src=fs.readFileSync(W+'/trio.js','utf8');
const rope=src.match(/const ROPE\s*=\s*\{[^}]*\};/)[0];
const d=new Function(rope+fs.readFileSync(W+'/trio_buddy.js','utf8')+fs.readFileSync(W+'/trio_bestie.js','utf8')+'\nreturn {buddy:TRIO_BUDDY,bestie:TRIO_BESTIE};')();
process.stdout.write(JSON.stringify(d));"""
    return json.loads(subprocess.run(['node', '-e', js, WEB], capture_output=True, text=True, check=True).stdout)


def alpha(path):
    return np.array(Image.open(path).convert('RGBA'))[..., 3] > 40


class Blob:
    """屏幕上的一块剪影：m（bool 裁到包围盒）+ 左上角屏幕坐标 (x, y)"""
    __slots__ = ('m', 'x', 'y')
    def __init__(self, m, x, y):
        ys, xs = np.nonzero(m)
        if not len(ys): self.m, self.x, self.y = np.zeros((1, 1), bool), 0, -99999; return
        self.m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; self.x = x + int(xs.min()); self.y = y + int(ys.min())
    def box(self): return self.x, self.y, self.x + self.m.shape[1], self.y + self.m.shape[0]
    def area(self): return int(self.m.sum())


def rect(x0, y0, x1, y1):
    x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
    return Blob(np.ones((max(1, y1 - y0), max(1, x1 - x0)), bool), x0, y0)


def ov(a, da, b, db):
    """两块剪影（各自平移 da / db）重叠像素"""
    ax, ay = a.x + da[0], a.y + da[1]; bx, by = b.x + db[0], b.y + db[1]
    x0, y0 = max(ax, bx), max(ay, by); x1, y1 = min(ax + a.m.shape[1], bx + b.m.shape[1]), min(ay + a.m.shape[0], by + b.m.shape[0])
    if x0 >= x1 or y0 >= y1: return 0
    return int((a.m[y0 - ay:y1 - ay, x0 - ax:x1 - ax] & b.m[y0 - by:y1 - by, x0 - bx:x1 - bx]).sum())


def union(bs):
    bs = [b for b in bs if b.y > -9999]
    x0 = min(b.x for b in bs); y0 = min(b.y for b in bs); x1 = max(b.box()[2] for b in bs); y1 = max(b.box()[3] for b in bs)
    m = np.zeros((y1 - y0, x1 - x0), bool)
    for b in bs: m[b.y - y0:b.y - y0 + b.m.shape[0], b.x - x0:b.x - x0 + b.m.shape[1]] |= b.m
    return Blob(m, x0, y0)


def grow(b, n=DIL):
    m = np.pad(b.m, n); return Blob(ndimage.binary_dilation(m, iterations=n), b.x - n, b.y - n)


def render(m, x0, y0, s, rot=0.0, pivot=None):
    """贴图 m（bool）左上角落在屏幕 (x0, y0)、缩放 s；rot 绕屏幕点 pivot 转（rad，canvas 顺时针为正）→ Blob"""
    im = Image.fromarray((m * 255).astype(np.uint8))
    w, h = max(1, round(im.width * s)), max(1, round(im.height * s))
    im = im.resize((w, h), Image.BILINEAR)
    if rot:
        px, py = pivot[0] - x0, pivot[1] - y0
        pad = int(np.hypot(px, py) + max(w, h)) + 4
        big = Image.new('L', (w + 2 * pad, h + 2 * pad)); big.paste(im, (pad, pad))
        big = big.rotate(-np.degrees(rot), center=(px + pad, py + pad), resample=Image.BILINEAR)
        im, x0, y0 = big, x0 - pad, y0 - pad
    return Blob(np.array(im) > 100, int(round(x0)), int(round(y0)))


# ---------- 头框：frames.json 的 head（参考帧格内像素）→ 图集输出像素 ----------
_HEADS = None
def head_out(name):
    """→ (头框, 参考帧名)。输出 = anchor_out + (点 − anchor_src) × K，K = size / 参考帧剪影宽或高（frames.py cmd_build 的 tr()，参考帧缩放 1、不平移）。
    新 build 的图集 json 里直接带 head（frames.py 2026-10-01 起写），老的按 frames.json 重算一次、缓存在 /tmp"""
    global _HEADS
    meta = json.load(open(os.path.join(WEB, 'assets/trio', name + '.json')))
    if meta.get('head'): return meta['head'], meta.get('ref', 'idle')
    d = next((os.path.join(TRIO_DIR, p, name) for p in ('buddy', 'bestie', 'tools/samples') if os.path.exists(os.path.join(TRIO_DIR, p, name, 'frames.json'))), None)
    if not d: return None
    cache = '/tmp/combo_heads.json'
    if _HEADS is None: _HEADS = json.load(open(cache)) if os.path.exists(cache) else {}
    key = f"{name}:{os.path.getmtime(os.path.join(d, 'frames.json'))}:{meta['anchor']}"
    if key not in _HEADS:
        sys.path.insert(0, os.path.join(TRIO_DIR, 'tools'))
        import frames as FR
        spec = json.load(open(os.path.join(d, 'frames.json')))
        with open(os.devnull, 'w') as dn:
            so = sys.stdout; sys.stdout = dn
            try: ref = FR.cells_of(d, spec)[spec['ref']]
            finally: sys.stdout = so
        ra = np.array(ref)[..., 3] > 8; ys, xs = np.nonzero(ra)
        K = spec['size'][1] / ((xs.max() - xs.min() + 1) if spec['size'][0] == 'w' else (ys.max() - ys.min() + 1))
        (sx, sy), (ox, oy), hb = spec['anchor'], meta['anchor'], spec['head']
        box = [ox + (hb[0] - sx) * K, oy + (hb[1] - sy) * K, ox + (hb[2] - sx) * K, oy + (hb[3] - sy) * K]
        # 校一遍：源参考帧的头缩 K 倍，在图集参考帧里找（原始动作条被重出过、或者 lift / graft 动过，算出来的框会偏）
        sh = json.load(open(os.path.join(WEB, 'assets/trio', name + '.json')))
        at = np.array(Image.open(os.path.join(WEB, 'assets/trio', name + '.webp')).convert('RGBA'))
        i = sh['frames'].index(spec['ref']); cw, ch = sh['cell']
        oc = at[(i // sh['cols']) * ch:(i // sh['cols'] + 1) * ch, (i % sh['cols']) * cw:(i % sh['cols'] + 1) * cw]
        t = np.array(ref.crop(tuple(hb)).resize((max(2, round((hb[2] - hb[0]) * K)), max(2, round((hb[3] - hb[1]) * K))), Image.LANCZOS).convert('RGBA'))
        g = gray(oc)
        if t.shape[0] < g.shape[0] and t.shape[1] < g.shape[1]:
            r = match_template(g, gray(t)); iy, ix = np.unravel_index(np.argmax(r), r.shape)
            if r[iy, ix] > 0.6: box = [ix, iy, ix + t.shape[1], iy + t.shape[0]]
        _HEADS[key] = [[round(float(v), 1) for v in box], spec['ref']]
        json.dump(_HEADS, open(cache, 'w'))
    return _HEADS[key]


def gray(rgba):
    a = rgba.astype(np.float32); al = a[..., 3:4] / 255
    return (a[..., :3].mean(2, keepdims=True) * al + 255 * (1 - al))[..., 0]


def find_head(cell, ref_cell, hb):
    """参考帧头框里那块，在这一帧里（缩放不变）找最像的位置 → 这一帧的头框；匹配 < 0.45 的（头整个转过去了）退回参考帧的框"""
    x0, y0, x1, y1 = (int(round(v)) for v in hb)
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(ref_cell.shape[1], x1), min(ref_cell.shape[0], y1)
    # 只在参考位置附近找（头在一个动作里挪不出一个头宽多少；全格找会被腿、衣服上相近的明暗拐走）
    w, h = x1 - x0, y1 - y0; mx, my = int(1.3 * w), int(1.3 * h)
    wx0, wy0 = max(0, x0 - mx), max(0, y0 - my); wx1, wy1 = min(cell.shape[1], x1 + mx), min(cell.shape[0], y1 + my)
    t = gray(ref_cell[y0:y1, x0:x1]); g = gray(cell[wy0:wy1, wx0:wx1])
    if t.shape[0] >= g.shape[0] or t.shape[1] >= g.shape[1]: return [x0, y0, x1, y1]
    r = match_template(g, t); iy, ix = np.unravel_index(np.argmax(r), r.shape)
    if r[iy, ix] < 0.4: return [x0, y0, x1, y1]
    return [wx0 + ix, wy0 + iy, wx0 + ix + w, wy0 + iy + h]


def est_head(m):
    """没有头框的（单张立绘 / 定妆图估）：剪影最上面 22% 高、那几行的横向范围"""
    ys, xs = np.nonzero(m)
    if not len(ys): return [0, 0, 1, 1]
    y1 = ys.min() + 0.22 * (ys.max() - ys.min()); sel = ys <= y1
    return [xs[sel].min(), ys.min(), xs[sel].max() + 1, y1]


def torso(m, hb):
    """躯干（招牌服装）：头框下沿到 头下沿 + 45% ×（头下沿 → 脚底），头框中心左右各 1.2 个头宽以内的剪影"""
    ys = np.nonzero(m.any(1))[0]
    if not len(ys): return np.zeros_like(m)
    y0 = int(hb[3]); y1 = int(round(hb[3] + 0.45 * max(0, ys.max() - hb[3])))
    cx, hw = (hb[0] + hb[2]) / 2, (hb[2] - hb[0])
    t = np.zeros_like(m)
    t[max(0, y0):max(0, y1), max(0, int(cx - 1.2 * hw)):max(0, int(cx + 1.2 * hw))] = True
    return t & m


class Frame:
    """一帧在屏幕上：body（剪影）、head（头框）、key（认人点：躯干 + 挂件 + 道具）"""
    __slots__ = ('name', 'body', 'head', 'key', 'area')
    def __init__(self, name, body, head, key):
        self.name, self.body, self.head, self.key = name, body, head, key; self.area = max(1, body.area())


def sheet_person(c, at):
    """帧序列 / 单张立绘 → [Frame]（at 可以不是 cfg.at：suggest 换站位时重贴）"""
    s = at[2]; ax, ay = c['anchor']
    X0, Y0 = at[0] - ax * s, at[1] - ay * s
    P = lambda q: (at[0] + (q[0] - ax) * s, at[1] + (q[1] - ay) * s)
    A = c.get('atk') or {}
    sw = c.get('swing'); rots = [-sw['a'], 0.0, sw['a']] if sw else [0.0]
    pv = P(c['pivot'])
    if c.get('sheet'):
        sh = c['sheet']; name = os.path.basename(sh['src']).rsplit('.', 1)[0]
        rgba = np.array(Image.open(os.path.join(WEB, sh['src'])).convert('RGBA'))
        cw, ch = sh['cell']; cols = sh['cols']
        cell = lambda fn: rgba[(sh['names'].index(fn) // cols) * ch:(sh['names'].index(fn) // cols + 1) * ch,
                               (sh['names'].index(fn) % cols) * cw:(sh['names'].index(fn) % cols + 1) * cw]
        want = [c['idle']['frame']]
        for q in A.get('seq', []): want += q[0] if isinstance(q[0], list) else [q[0]]
        E = c.get('enter')
        if isinstance(E, dict) and E.get('seq') and not isinstance(E['seq'][-1][0], list):   # 进场落定那一帧（走路循环是还在走，不算在场）
            want += [E['seq'][-1][0]]
        pump = (sw or {}).get('pump')
        if pump: want += [pump['fwd'], pump['back']]
        want = [f for f in dict.fromkeys(want) if f in sh['names']]
        hr = head_out(name); hb, refc = (hr[0], cell(hr[1])) if hr else (None, None)   # 头框量在参考帧上（不一定是 idle：G4 是 wind）
        cells = [(f, cell(f)) for f in want]
        heads = {f: (find_head(cc, refc, hb) if hb else est_head(cc[..., 3] > 40)) for f, cc in cells}
    else:
        im = np.array(Image.open(os.path.join(WEB, c['src'])).convert('RGBA'))
        cells = [('立绘', im)]; heads = {'立绘': est_head(im[..., 3] > 40)}
    # 挂件（场景层 fixed 不算人）、道具
    parts = []
    for q in c.get('parts', []) if c.get('sheet') else []:
        if q.get('fixed'): continue
        parts.append((q, alpha(os.path.join(WEB, q['src']))))
    R = 0
    if A.get('item'):
        if A.get('atlas'): R = A['r'] * A['atlas']['scale']
        elif A.get('prop'):
            pi = Image.open(os.path.join(WEB, A['prop'])); R = max(pi.size) * A.get('scale', 1) / 2
        else: R = A.get('r', 0)
    out = []
    for f, cc in cells:
        m = cc[..., 3] > 40
        hb = heads[f]; t = torso(m, hb)
        extra = []
        for q, pm in parts:
            a = q['at'].get(f)
            if not a: continue
            x, y = P(a[:2]); sway = (q.get('sway') or [0])[0]
            for ang in {a[2] - sway, a[2], a[2] + sway}:
                extra.append(render(pm, x - q['pivot'][0] * s, y - q['pivot'][1] * s, s, ang, (x, y)))
        if R and A.get('hold', {}).get(f) and not any(q[2:] == ['fire'] and q[0] == f for q in A.get('seq', [])):   # 出手帧东西已离手
            hx, hy = P(A['hold'][f]); rr = int(round(R))
            yy, xx = np.mgrid[-rr:rr + 1, -rr:rr + 1]
            extra.append(Blob(xx * xx + yy * yy <= rr * rr, int(round(hx)) - rr, int(round(hy)) - rr))
        for r in rots:
            body = render(m, X0, Y0, s, r, pv); head = render(_box(m.shape, hb), X0, Y0, s, r, pv)
            key = render(t, X0, Y0, s, r, pv)
            if r and extra: ex = [render(e.m, e.x, e.y, 1, r, pv) for e in extra]
            else: ex = extra
            if ex:
                body = union([body] + ex); key = union([key] + ex)
            out.append(Frame(f + (f' 摆{r:+.2f}' if r else ''), body, head, key))
    return out


def _box(shape, hb):
    m = np.zeros(shape, bool); x0, y0, x1, y1 = (int(round(v)) for v in hb)
    m[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
    return m


def ref_person(side, rid, done):
    """还没做完的人：定妆图剪影，高度 = 同槽位已做完的人的中位高度，底边中点 = 他们的中位底边中点"""
    p = os.path.join(TRIO_DIR, side, 'ref', rid + '.png')
    if not os.path.exists(p) or not done: return None
    m = alpha(p); ys, xs = np.nonzero(m); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    hs = [u.m.shape[0] for u in done]; bx = [u.x + u.m.shape[1] / 2 for u in done]; by = [u.y + u.m.shape[0] for u in done]
    s = np.median(hs) / m.shape[0]
    body = render(m, np.median(bx) - m.shape[1] * s / 2, np.median(by) - m.shape[0] * s, s)
    hb = est_head(body.m)
    return [Frame('估', body, rect(body.x + hb[0], body.y + hb[1], body.x + hb[2], body.y + hb[3]), Blob(torso(body.m, hb), body.x, body.y))]


class Person:
    def __init__(self, rid, slot, kind, frames):
        self.rid, self.slot, self.kind, self.frames = rid, slot, kind, frames
        self.all = union([f.body for f in frames]); self.all_g = grow(self.all)


def judge(back, db, front, dfr):
    """后面那人（平移 db）× 前面那人（平移 dfr）：返回 (最坏帧占比, 那一帧名, 头框被挡 px, 认人点被挡 px)，都取所有帧里最坏的"""
    if not ov(back.all_g, db, front.all_g, dfr): return (0.0, '', 0, 0)
    worst, wf, hd, ky = 0.0, '', 0, 0
    for f in back.frames:
        r = ov(f.body, db, front.all, dfr) / f.area
        if r > worst: worst, wf = r, f.name
        hd = max(hd, ov(f.head, db, front.all_g, dfr)); ky = max(ky, ov(f.key, db, front.all_g, dfr))
    return worst, wf, hd, ky


def ok_cell(j): return j[0] <= RATIO and j[2] == 0 and j[3] == 0


def fmt(j, n=1):
    if not j[0] and not j[2] and not j[3]: return '0'
    t = f'{j[0]:.1%}'
    if j[2]: t += f' 头{j[2]}'
    if j[3]: t += f' 认{j[3]}'
    return t + ('' if ok_cell(j) else ' ✗')


def build(side, D, at_over=None):
    data = D[side]; at_over = at_over or {}
    ids = {sl: [g[sl] for g in data['groups']] for sl in DEPTH}
    ppl = {}
    for sl in DEPTH:
        for rid in ids[sl]:
            if rid in data['cast']:
                c = data['cast'][rid]
                ppl[rid] = Person(rid, sl, 'sheet' if c.get('sheet') else '单张', sheet_person(c, at_over.get(rid, c['at'])))
    for sl in DEPTH:
        done = [ppl[r].frames[0].body for r in ids[sl] if r in ppl and ppl[r].kind in ('sheet', '单张')]
        for rid in ids[sl]:
            if rid not in ppl:
                fr = ref_person(side, rid, done)
                if fr: ppl[rid] = Person(rid, sl, '估', fr)
    return ids, ppl


def rescan(side, D, at):
    """按建议站位（at：{编号: [x, y, s]}）重贴一遍，逐对复核：返回 (对数, 不过的对, 后排最小 s)"""
    ids, ppl = build(side, D, at)
    n, bad = 0, []
    for bk, fr, _ in PAIRS:
        for r in ids[bk]:
            for c in ids[fr]:
                if r not in ppl or c not in ppl or '估' in (ppl[r].kind, ppl[c].kind): continue
                j = judge(ppl[r], (0, 0), ppl[c], (0, 0)); n += 1
                if not ok_cell(j): bad.append((r, c, j))
    ks = [at[r][2] for r in ids['ground'] if r in at]
    return n, bad, min(ks) if ks else None


def scan(side, D):
    ids, ppl = build(side, D)
    out = [f'# 组合遮挡矩阵 · {side}（combo_scan.py，2026-10-01 新判据）',
           f'判据：画在后面的人（上方 0.5 < 后排 0.8 < 地板 1.3）逐帧：被挡剪影占比 ≤ {RATIO:.0%}、头框被挡 0、认人点（躯干 + 挂件 + 手里道具）被挡 0；'
           f'头 / 认人点按前面那人外扩 {DIL}px 比。',
           '格子：最坏一帧的被挡占比；"头N" 头框被挡 N px；"认N" 认人点被挡 N px；✗ 不过。行 = 后面的人，列 = 前面的人。',
           '种类：sheet 帧序列 / 单张 旧单张立绘 / 估 定妆图估算（还没做出来的人，不在验收范围）']
    bad = []
    for bk, fr, title in PAIRS:
        rows, cols = ids[bk], ids[fr]
        out.append(f'\n== {title}（行在后 × 列在前）')
        out.append('        ' + ''.join(f'{c + "(" + ppl[c].kind + ")" if c in ppl else c:>16}' for c in cols))
        for r in rows:
            cells = []
            for c in cols:
                if r not in ppl or c not in ppl: cells.append(f'{"缺图":>16}'); continue
                j = judge(ppl[r], (0, 0), ppl[c], (0, 0))
                tag = '估' if '估' in (ppl[r].kind, ppl[c].kind) else ''
                cells.append(f'{fmt(j) + tag:>16}')
                if not ok_cell(j): bad.append((r, c, j, tag, ppl[r].kind, ppl[c].kind))
            out.append(f'{r + "(" + ppl[r].kind + ")" if r in ppl else r:>9}' + ''.join(cells))
    real = [x for x in bad if not x[3]]
    out.append(f'\n== 汇总：不过 {len(bad)} 对（已做完的人之间 {len(real)} 对；其余含估）')
    for r, c, j, tag, kr, kc in sorted(bad, key=lambda q: (bool(q[3]), -q[2][0])):
        out.append(f'  {r} 在 {c} 后面：最坏帧 {j[1]} 被挡 {j[0]:.1%}' + (f'，头框 {j[2]} px' if j[2] else '') + (f'，认人点 {j[3]} px' if j[3] else '') + (' 估' if tag else ''))
    return '\n'.join(out), ids, ppl


def suggest(side, D, ids, ppl, fixed_ids=()):
    """建议站位：轮流给不过的人找挪动最小的站位（|dx| + |dy|，10px 一档），让他和别的槽位已做完的人都满足判据。
    先挪，挪不开才缩：缩一档记 1000 分（比最大挪动 360 大），后排缩到 s ≥ 0.8，别的槽位缩到 ≥ 本人现值 × 0.9。
    约束：地板最低点 ≤ 1334；上方最高点 ≥ 200（拉力条下沿）；左右不比现在多出画（本来扒着墙出画的照旧）；横向 ±100、竖向 −100 ~ +40（后排 −160、上方 −260 起）。
    估的人不参与，也不当约束（还没有数据）。fixed_ids：不许挪的人（只当约束）"""
    data = D[side]
    movers = [r for r in ppl if ppl[r].kind in ('sheet', '单张')]
    slot = {r: ppl[r].slot for r in movers}
    def scales(r):
        s0 = data['cast'][r]['at'][2]
        lo = 0.8 if slot[r] == 'ground' else s0 * 0.9
        ks = [s0]; v = s0
        while v - 0.02 >= lo - 1e-9: v = round(v - 0.02, 3); ks.append(v)
        if ks[-1] > lo + 1e-9 and slot[r] == 'ground': ks.append(round(lo, 3))
        return ks
    var = {}                                   # r → {s: Person}
    def person(r, s):
        var.setdefault(r, {})
        if s not in var[r]:
            a = data['cast'][r]['at']
            var[r][s] = ppl[r] if s == a[2] else Person(r, slot[r], ppl[r].kind, sheet_person(data['cast'][r], [a[0], a[1], s]))
        return var[r][s]
    cur = {r: (data['cast'][r]['at'][2], [0, 0]) for r in movers}
    def pairs_of(r):
        for bk, fr, _ in PAIRS:
            if slot[r] == bk:
                for o in movers:
                    if slot[o] == fr: yield (r, o)
            if slot[r] == fr:
                for o in movers:
                    if slot[o] == bk: yield (o, r)
    def fails(r, s, d):
        n = 0
        for b, f in pairs_of(r):
            pb = person(b, s if b == r else cur[b][0]); pf = person(f, s if f == r else cur[f][0])
            db = d if b == r else cur[b][1]; df = d if f == r else cur[f][1]
            if not ok_cell(judge(pb, db, pf, df)): n += 1
        return n
    def inside(r, s, d):
        p = person(r, s); x0, y0, x1, y1 = p.all.box(); p0 = ppl[r].all.box()
        outx = lambda a, b: max(0, -a) + max(0, b - W)
        return ((slot[r] != 'floor' or y1 - 1 + d[1] <= 1334) and (slot[r] != 'top' or y0 + d[1] >= 200)
                and outx(x0 + d[0], x1 + d[0]) <= outx(p0[0], p0[2]) + 10)
    def search(r):
        best = None
        for i, s in enumerate(scales(r)):
            if best and i * 1000 >= best[0]: break
            for dy in range(-260 if slot[r] == 'top' else -160 if slot[r] == 'ground' else -100, 41, 10):
                for dx in range(-100, 101, 10):
                    cost = abs(dx) + abs(dy) + i * 1000
                    if best and cost >= best[0]: continue
                    if inside(r, s, [dx, dy]) and not fails(r, s, [dx, dy]): best = (cost, s, [dx, dy])
        return best
    # 每轮给所有不过的人各找一个最省的站位，只落实全场最省的那一个（挪的优先于缩的：缩一档 1000 分），直到都过或找不到
    tried = set()
    for _ in range(30):
        cand = [(search(r), r) for r in movers if r not in fixed_ids and fails(r, *cur[r])]
        cand = [(b, r) for b, r in cand if b and (r, b[1], tuple(b[2])) not in tried]
        if not cand: break
        (cost, s, d), r = min(cand, key=lambda q: q[0][0])
        tried.add((r, s, tuple(d))); cur[r] = (s, d)
    out = ['\n== 建议站位（suggest，新判据：只挪已做完的人；先挪后缩，后排 s ≥ 0.8、其他 ≥ 现值 × 0.9；估 的人不在内）']
    at = {}
    for r in movers:
        a0 = data['cast'][r]['at']; s, d = cur[r]
        at[r] = [a0[0] + d[0], a0[1] + d[1], s]
        f = fails(r, s, d)
        if at[r] != list(a0) or f:
            out.append(f'  {r}（{slot[r]}）at {a0} → {at[r]}' + (f'  仍有 {f} 对不过' if f else ''))
    if len(out) == 1: out.append('  不用挪：已做完的人两两都过')
    return '\n'.join(out), at


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--only=')]
    only = next((a[7:].split(',') for a in sys.argv[1:] if a.startswith('--only=')), None)   # --only=B1,B2：建议站位只挪这几个人（别人只当约束）
    which = args[0] if args else 'all'
    D = load_data()
    for side in (['buddy', 'bestie'] if which == 'all' else [which]):
        txt, ids, ppl = scan(side, D)
        print(txt, flush=True)
        sg, at = suggest(side, D, ids, ppl, fixed_ids=[r for r in ppl if only and r not in only])
        n, bad, kmin = rescan(side, D, at)
        sg += (f'\n\n== 按建议站位复扫（重贴每人全部在场帧，逐对复核）：已做完的人 {n} 对，不过 {len(bad)} 对；后排最小 s {kmin}' +
               ''.join(f'\n  ✗ {r} 在 {c} 后面：{fmt(j)}（最坏帧 {j[1]}）' for r, c, j in bad))
        p = os.path.join(ROOT, 'shots/trio_std', f'组合遮挡矩阵_{side}.txt')
        open(p, 'w').write(txt + '\n' + sg + '\n'); print(sg)
