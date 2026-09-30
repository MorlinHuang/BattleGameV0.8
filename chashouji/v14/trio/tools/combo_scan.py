"""三人组自由组合遮挡矩阵（2026-10-01）：线上每次送礼三个槽位各自从本边 10 人里独立随机抽一人，任意 后排 × 地板、上方 × 后排
都可能同框。这里把每个人**在场时会画的全部帧**（待机、出手 seq、进场最后落定那一帧；秋千按在场摆幅左右各转一次）的剪影
按引擎的摆法贴到屏幕上，外扩 4px，两两求交，数重叠像素。0 = 不挡。

  帧序列（cfg.sheet）：屏幕点 = at + (格内点 − anchor) × s（trio.js place()，在场时没有位移）
  单张立绘（cfg.src）：同上，整张图一个剪影
  crew.js 的滑板哥们 / 平衡车闺蜜（data.ground）：站位是随机的 —— 横向 r ∈ 0~1、远近 d 在 rows 里抽（crew.js summon / pose），
      这里按 crew.js pose() 的公式取 r 0 / 0.25 / 0.5 / 0.75 / 1 × 两排上下限，手机在正中（开局）；上身按瞄准角上下限各转一次。
      报"最坏重叠像素 / 相交的站位占几成"
  还没做完的人（cast / ground 里都没有）：用定妆图 ref/<编号>.png 估 —— 剪影缩到本边同槽位已做完的人的中位高度，
      底边中点放到他们的中位位置。结果标"估"

每个槽位同时只站一人（没有备用位），所以只扫不同槽位之间；最后给一份建议站位（suggest）。

用法（在 chashouji 下）：python3 v14/trio/tools/combo_scan.py [buddy|bestie|all]
  → shots/trio_std/组合遮挡矩阵_<边>.txt；另存 /tmp/combo_masks_<边>.npz（剪影缓存）"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))   # chashouji/
WEB = os.path.join(ROOT, 'web')
W, H = 960, 1334
PAD = 500                                      # 画布四周多留的边（画外的部分也算，出画那截不会挡人，但算上无妨）
GROUND, HORIZON_UP, MID = 1195, 350, 480
DIL = 4


def load_data():
    js = r"""
const fs=require('fs');const W=process.argv[1];
const src=fs.readFileSync(W+'/trio.js','utf8');
const trio=new Function(src.match(/const TRIO = \{[\s\S]*?\n\};/)[0]+'\nreturn TRIO;')();
const rope=src.match(/const ROPE\s*=\s*\{[^}]*\};/)[0];
const d=new Function(rope+fs.readFileSync(W+'/trio_buddy.js','utf8')+fs.readFileSync(W+'/trio_bestie.js','utf8')+'\nreturn {buddy:TRIO_BUDDY,bestie:TRIO_BESTIE};')();
const crew=fs.readFileSync(W+'/crew.js','utf8');
const grab=(name)=>{const i=crew.indexOf(name);return crew.slice(i,i+4000);};
process.stdout.write(JSON.stringify({data:d}));"""
    out = subprocess.run(['node', '-e', js, WEB], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


# crew.js 两个滑板 / 平衡车 Crew 的参数（crew.js Buddy / MIST；只取摆放用到的几项，改了 crew.js 这里要跟着改）
CREW = {
    'buddy': dict(face=-1, src='assets/world/buddy%n_%k.webp', layers=['up', 'lo'], rot='up', pivot=[266, 200], k=0.85,
                  foot=[260, 446], muzzle=[2, 88], rows=[[0.87, 0.94], [0.78, 0.84]], skins=[1, 4, 5, 7], aim=[-0.52, 0.21],
                  zone=lambda: [min(MID + 100, W - 420), W + 90]),
    'bestie': dict(face=+1, src='assets/world/bestie%n_%k.webp', layers=['arm', 'up', 'lo'], rot='arm', pivot=[198, 105], k=0.85,
                   foot=[184, 485], muzzle=[361, 20], rows=[[0.68, 0.74], [0.60, 0.64]], skins=[2, 6, 7], aim=[-0.7, 0.35],
                   zone=lambda: [max(MID - 60, 420), -40]),
}


def alpha(path):
    return np.array(Image.open(path).convert('RGBA'))[..., 3] > 40


def canvas():
    return np.zeros((H + 2 * PAD, W + 2 * PAD), bool)


def paste(cv, m, x0, y0, s, rot=0.0, pivot=None):
    """贴图 m（bool）左上角落在屏幕 (x0, y0)、缩放 s；rot 绕屏幕点 pivot 转（rad，canvas 顺时针为正）"""
    im = Image.fromarray((m * 255).astype(np.uint8))
    w, h = max(1, round(im.width * s)), max(1, round(im.height * s))
    im = im.resize((w, h), Image.BILINEAR)
    if rot:
        px, py = pivot[0] - x0, pivot[1] - y0
        big = Image.new('L', (w + 2 * 600, h + 2 * 600)); big.paste(im, (600, 600))
        big = big.rotate(-np.degrees(rot), center=(px + 600, py + 600), resample=Image.BILINEAR)
        im, x0, y0 = big, x0 - 600, y0 - 600
    a = np.array(im) > 100
    X, Y = int(round(x0)) + PAD, int(round(y0)) + PAD
    ys, xs = np.nonzero(a)
    if not len(ys): return
    ys, xs = ys + Y, xs + X
    ok = (ys >= 0) & (ys < cv.shape[0]) & (xs >= 0) & (xs < cv.shape[1])
    cv[ys[ok], xs[ok]] = True


def sheet_frames(c):
    sh = c['sheet']; im = alpha(os.path.join(WEB, sh['src']))
    cw, ch = sh['cell']; cols = sh['cols']
    def cell(fn):
        i = sh['names'].index(fn); return im[(i // cols) * ch:(i // cols + 1) * ch, (i % cols) * cw:(i % cols + 1) * cw]
    want = [c['idle']['frame']]
    A = c.get('atk') or {}
    for q in A.get('seq', []): want += q[0] if isinstance(q[0], list) else [q[0]]
    E = c.get('enter')
    if isinstance(E, dict) and E.get('seq'):
        q = E['seq'][-1][0]; want += q if isinstance(q, list) else [q]
    P = (c.get('swing') or {}).get('pump')
    if P: want += [P['fwd'], P['back']]
    return [cell(f) for f in dict.fromkeys(want) if f in sh['names']]


def act_mask(c, at=None):
    """帧序列 / 单张立绘：全部在场帧的剪影并集（屏幕）"""
    at = at or c['at']; s = at[2]; ax, ay = c['anchor']
    ms = sheet_frames(c) if c.get('sheet') else [alpha(os.path.join(WEB, c['src']))]
    sw = c.get('swing'); rots = [0.0]
    if sw:                                                   # 在场摆幅 a（秋千绕绳顶 pivot 转）
        rots = [-sw['a'], 0.0, sw['a']]
    cv = canvas()
    pv = [at[0] + (c['pivot'][0] - ax) * s, at[1] + (c['pivot'][1] - ay) * s]
    for m in ms:
        for r in rots: paste(cv, m, at[0] - ax * s, at[1] - ay * s, s, r, pv)
    return cv


def crew_masks(side, sk):
    """crew.js 站位随机：返回 [(说明, 剪影)]，每个 (r, d) 一张（上身按瞄准角上下限、0 三个角度并起来）"""
    C = CREW[side]; n = C['skins'][sk]
    lay = {k: alpha(os.path.join(WEB, C['src'].replace('%n', str(n)).replace('%k', k))) for k in C['layers']}
    wid = lay['lo'].shape[1]
    near, edge = C['zone'](); face = C['face']
    out = []
    for d in sorted({v for R in C['rows'] for v in R}):
        s = d * C['k']
        far = edge - (wid - C['muzzle'][0]) * s if face < 0 else edge + C['muzzle'][0] * s
        far = max(near, far) if face < 0 else min(near, far)
        for r in (0, 0.25, 0.5, 0.75, 1):
            x1 = near + (far - near) * r + (C['foot'][0] - C['muzzle'][0]) * s
            y = GROUND - HORIZON_UP * (1 - d)
            x0, y0 = x1 - C['foot'][0] * s, y - C['foot'][1] * s
            pv = [x1 + (C['pivot'][0] - C['foot'][0]) * s, y + (C['pivot'][1] - C['foot'][1]) * s]
            cv = canvas()
            for k, m in lay.items():
                if k == C['rot']:
                    for th in (C['aim'][0], 0, C['aim'][1]): paste(cv, m, x0, y0, s, -face * th, pv)
                else: paste(cv, m, x0, y0, s)
            out.append((f'd{d:.2f} r{r:.2f}', cv))
    return out


def ref_mask(side, rid, slot, done):
    """还没做完的人：定妆图剪影，高度 = 同槽位已做完的人的中位高度，底边中点 = 他们的中位底边中点"""
    p = os.path.join(ROOT, 'v14/trio', side, 'ref', rid + '.png')
    if not os.path.exists(p): return None
    m = alpha(p); ys, xs = np.nonzero(m); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    hs, bx, by = [], [], []
    for cv in done:
        yy, xx = np.nonzero(cv); hs.append(yy.max() - yy.min()); bx.append((xx.min() + xx.max()) / 2 - PAD); by.append(yy.max() - PAD)
    s = np.median(hs) / m.shape[0]
    cv = canvas(); paste(cv, m, np.median(bx) - m.shape[1] * s / 2, np.median(by) - m.shape[0] * s, s)
    return cv


def dil(cv):
    return ndimage.binary_dilation(cv, iterations=DIL)


def scan(side, D):
    data = D[side]; out = []
    ids = {sl: [g[sl] for g in data['groups']] for sl in ('ground', 'top', 'floor')}
    masks, kind = {}, {}
    for sl in ('ground', 'top', 'floor'):
        for rid in ids[sl]:
            if rid in data['ground']:
                masks[rid] = [(t, dil(m)) for t, m in crew_masks(side, data['ground'][rid])]; kind[rid] = 'crew'
            elif rid in data['cast']:
                masks[rid] = [('', dil(act_mask(data['cast'][rid])))]; kind[rid] = 'sheet' if data['cast'][rid].get('sheet') else '单张'
    for sl in ('ground', 'top', 'floor'):
        done = [masks[r][0][1] for r in ids[sl] if kind.get(r) in ('sheet', '单张')]
        for rid in ids[sl]:
            if rid not in masks:
                m = ref_mask(side, rid, sl, done)
                if m is not None: masks[rid] = [('估', dil(m))]; kind[rid] = '估'
    def inter(a, b):
        """a、b 各自若干站位：返回 (最坏重叠像素, 相交的站位对占比)"""
        v = [int((ma & mb).sum()) for _, ma in masks[a] for _, mb in masks[b]]
        return max(v), sum(x > 0 for x in v) / len(v)
    def mat(rows, cols, title):
        out.append(f'\n== {title}（行 × 列，外扩 {DIL}px 后重叠像素；crew 行 = 最坏站位/相交站位占比；估 = 定妆图估的剪影）')
        out.append('        ' + ''.join(f'{c:>12}' for c in cols))
        bad = []
        for r in rows:
            cells = []
            for c in cols:
                if r not in masks or c not in masks: cells.append(f'{"缺图":>12}'); continue
                v, fr = inter(r, c)
                tag = '估' if '估' in (kind[r], kind[c]) else ''
                txt = (f'{v}' if v == 0 else f'{v}') + (f'/{fr:.0%}' if len(masks[r]) * len(masks[c]) > 1 else '') + tag
                cells.append(f'{txt:>12}')
                if v: bad.append((r, c, v, fr, tag))
            out.append(f'{r + "(" + kind.get(r, "?") + ")":>8}' + ''.join(cells))
        return bad
    out.append(f'# 组合遮挡矩阵 · {side}（combo_scan.py；每人在场全部帧的剪影并集，外扩 {DIL}px）')
    out.append('种类：sheet 帧序列 / 单张 旧单张立绘 / crew crew.js 滑板·平衡车（站位随机，扫 10 个站位 × 3 个瞄准角）/ 估 定妆图估算')
    bad = mat(ids['ground'], ids['floor'], '后排 × 地板')
    bad += mat(ids['top'], ids['ground'], '上方 × 后排')
    bad += mat(ids['top'], ids['floor'], '上方 × 地板（附带）')
    out.append('\n== 备用位：已撤（2026-10-01 自由组合起每个槽位同时只站一人）。撤之前搜过 SLOT2（后排 dx 110~250 / dy −45~−140 / 缩放 0.75~0.85，'
               '上方 dx 0~120 / dy −210~−360）：后排最好的一档 90 对里仍有 9 对相交、最坏 3560 px；上方要 dy −360 才只剩 1 对，但人顶进 HUD 207 px')
    out.append(f'\n== 汇总：主矩阵相交 {len(bad)} 对（其中估 {sum(1 for x in bad if x[4])} 对）')
    for r, c, v, fr, tag in sorted(bad, key=lambda q: -q[2]):
        out.append(f'  {r} × {c}: {v} px' + (f'（{fr:.0%} 站位相交）' if fr and fr < 1 else '') + (' 估' if tag else ''))
    return '\n'.join(out), bad


def suggest(side, D):
    """建议站位（只挪已做完的人，缩放不变）：轮流给有冲突的人找最小挪动（|dx| + |dy|，10px 一档），让他和别的槽位已做完的人外扩 4px 后都不相交。
    后排 × 地板、上方 × 后排两组关系；地板最低点 ≤ 1334，上方最高点 ≥ 200（拉力条下沿），不比现在多出画；横向最多挪 100、竖向 −100 ~ +40（后排 −160、上方 −260 起）。
    crew.js 的滑板 / 平衡车（站位随机）和定妆图估的人不参与（前者要迁成帧序列才有 at 可调，后者还没有数据）。
    缩放不变时挪 at 就是整块剪影平移，所以每人只贴一次、裁到包围盒，候选位置按偏移量求交（快）"""
    data = D[side]; ids = {sl: [g[sl] for g in data['groups']] for sl in ('ground', 'top', 'floor')}
    slot = {r: sl for sl in ids for r in ids[sl] if r in data['cast']}
    def crop(r, k):
        c = data['cast'][r]; a = [c['at'][0], c['at'][1], c['at'][2] * k]
        m = dil(act_mask(c, a)); ys, xs = np.nonzero(m)
        return (m[ys.min():ys.max() + 1, xs.min():xs.max() + 1], xs.min() - PAD, ys.min() - PAD)   # 剪影、左上角屏幕坐标
    KS = (1.0, 0.95, 0.9, 0.85, 0.8)                     # 后排可以往后站：更小（透视），每缩 5% 记 20 分（≈ 挪 20px）
    boxes = {r: {k: crop(r, k) for k in (KS if slot[r] == 'ground' else (1.0,))} for r in slot}
    box = {r: boxes[r][1.0] for r in slot}
    off = {r: [0, 0] for r in slot}; kk = {r: 1.0 for r in slot}
    def inter(a, da, b, db):
        ma, xa, ya = box[a]; mb, xb, yb = box[b]
        xa += da[0]; ya += da[1]; xb += db[0]; yb += db[1]
        x0, y0 = max(xa, xb), max(ya, yb); x1, y1 = min(xa + ma.shape[1], xb + mb.shape[1]), min(ya + ma.shape[0], yb + mb.shape[0])
        if x0 >= x1 or y0 >= y1: return 0
        return int((ma[y0 - ya:y1 - ya, x0 - xa:x1 - xa] & mb[y0 - yb:y1 - yb, x0 - xb:x1 - xb]).sum())
    vs = {'ground': ('floor', 'top'), 'floor': ('ground',), 'top': ('ground',)}
    def hits(r, d):
        h = {o: inter(r, d, o, off[o]) for o in slot if slot[o] in vs[slot[r]]}
        return {o: v for o, v in h.items() if v}
    def ok(r, d):
        m, x, y = box[r]
        outside = lambda dx: max(0, -(x + dx + DIL)) + max(0, x + dx + m.shape[1] - 1 - DIL - (W - 1))   # 出画多少（左右）
        return ((slot[r] != 'floor' or y + d[1] + m.shape[0] - 1 - DIL <= 1334) and (slot[r] != 'top' or y + d[1] + DIL >= 200)
                and outside(d[0]) <= outside(0) + 10)                                                    # 不许比现在多出画（上方扒右墙那种本来就出画的照旧）
    for _ in range(4):
        moved = False
        for r in sorted(slot, key=lambda q: -sum(hits(q, off[q]).values())):
            if not hits(r, off[r]): continue
            best = None
            for k in boxes[r]:
                box[r] = boxes[r][k]
                for dy in range(-260 if slot[r] == 'top' else -160 if slot[r] == 'ground' else -100, 41, 10):
                    for dx in range(-100, 101, 10):
                        cost = abs(dx) + abs(dy) + round((1 - k) * 400)
                        if best and cost >= best[0]: continue
                        if ok(r, [dx, dy]) and not hits(r, [dx, dy]): best = (cost, [dx, dy], k)
            if best and (best[1] != off[r] or best[2] != kk[r]): off[r], kk[r] = best[1], best[2]; moved = True
            box[r] = boxes[r][kk[r]]
        if not moved: break
    out = ['\n== 建议站位（suggest：只挪已做完的人，后排可缩到 0.8 倍往后站，挪完彼此外扩 4px 不相交；crew / 估 的人不在内）']
    at = {}
    for r in slot:
        a0 = data['cast'][r]['at']; at[r] = [a0[0] + off[r][0], a0[1] + off[r][1], round(a0[2] * kk[r], 3)]
        h = hits(r, off[r])
        if off[r] != [0, 0] or kk[r] != 1 or h:
            out.append(f'  {r}（{slot[r]}）at {a0} → {at[r]}' + (f'  仍相交 {h}' if h else ''))
    if len(out) == 1: out.append('  不用挪')
    crew = [r for r in ids['ground'] if r in data['ground']]
    if crew:
        out.append(f'  crew.js 老角色 {"、".join(crew)}：站位是 crew.js rows（远近 d）+ main.js zone 随机出来的，脚底 y ≈ {GROUND - HORIZON_UP * (1 - CREW[side]["rows"][1][0]):.0f}~{GROUND - HORIZON_UP * (1 - CREW[side]["rows"][0][1]):.0f}，'
                   '整条落在地板那一带；要不压地板的人只能把 d 压到 0.45 以下（缩成一半）。按规范 4.3 迁成帧序列（ride + spray）后按 at 摆，和上面后排的人同一套站位')
    return '\n'.join(out), at

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    D = load_data()
    for side in (['buddy', 'bestie'] if which == 'all' else [which]):
        txt, bad = scan(side, D['data'])
        sg, _ = suggest(side, D['data'])
        p = os.path.join(ROOT, 'shots/trio_std', f'组合遮挡矩阵_{side}.txt')
        open(p, 'w').write(txt + '\n' + sg + '\n'); print(txt); print(sg)
