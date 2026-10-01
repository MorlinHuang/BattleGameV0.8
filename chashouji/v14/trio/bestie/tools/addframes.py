"""给已经出好的图集补帧（2026-10-01，美术打磨自检·精1 P6 出手补帧 / P7 idle2）：同一张底图局部重绘，不重出整张动作条。

为什么不走 frames.py build 重建：重建会让格子大小、锚点、配准跟着变，而好几个人的图集出完以后还跑过后处理（G6 / G9 walkshift、
G15 bow、G20 moon、G22 legs、G27 fixleg），hold / parts / flex 坐标也都量在现有图集上。这里只在现有格子里补：
  底格（base，现有图集里的一帧）原样放大贴到 1024 见方的幕布上 → 蒙版框（格内像素）里透明、要重画 → generate_image 带蒙版重画 →
  只取框里那一块贴回底格（tools/inpaint_paste.py：框外一律是底格原像素，框边 feather 渐变）。
  框外（脚、腿、站的东西）一个像素都不动，所以新帧天然和底格配准，漂移 = 0；缩放锚点也不变。

<目录>/addframes.json：{"frames": [{"name": "release", "base": "throw", "box": [x0, y0, x1, y1] 或 [[...], [...]], "screen": "magenta", "fixed": [x0, y0, x1, y1]}, ...]}
  name 已经在图集里（比如不上场的 idle2 重画格）就替换那一格，否则追加在末尾；base 必须是图集原有的帧（不能是补出来的）。
  生图原图存 <目录>/raw/add_<name>.png（paste 时拷进来），底图 / 蒙版 raw/add_<name>_base.png、_mask.png。

用法（在 v14/trio 下）：
  python3 bestie/tools/addframes.py bestie/G5_tong prep release     # 出底图 + 蒙版，打印 K / ox / oy（写回 addframes.json）
  python3 bestie/tools/addframes.py bestie/G5_tong paste release /tmp/kf_generated_images/xxx.png
  python3 bestie/tools/addframes.py bestie/G5_tong build            # 按 addframes.json 把全部补帧贴进图集（可重复跑）
  python3 bestie/tools/addframes.py bestie/G5_tong cfg G5           # trio_bestie.js 里 sheet 的 cell / names 跟图集对齐
重新跑过 frames.py build（或任何改图集的后处理）以后要再跑一次 build。"""
import json, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TRIO = os.path.abspath(os.path.join(HERE, '../..'))
WEB = os.path.join(TRIO, '../../web/assets/trio')
sys.path.insert(0, os.path.join(TRIO, 'tools'))
import frames as F

SIDE, FIT = 1024, 900                                   # 幕布边长；底格长边放大到多少
SCREEN = {'magenta': (255, 0, 255), 'green': (0, 255, 0)}


def load(d):
    name = os.path.basename(d.rstrip('/'))
    meta = json.load(open(os.path.join(WEB, name + '.json')))
    a = Image.open(os.path.join(WEB, name + '.webp')).convert('RGBA')
    cw, ch = meta['cell']; C = meta['cols']
    cells = {n: a.crop((i % C * cw, i // C * ch, i % C * cw + cw, i // C * ch + ch)) for i, n in enumerate(meta['frames'])}
    spec = json.load(open(os.path.join(TRIO, d, 'addframes.json')))
    # pad [左, 上, 右, 下]：格子四周加边（往后拖的袖子、头发、举过头的手会伸出原来的格子）。图集上记着已经加了多少（meta.pad），
    # 只补差额 —— frames.py 重建以后 meta 没有 pad，这里会重新加上。左 / 上加边 = 格子原点挪了，cfg 的格内坐标要用 shiftcfg.py 平移同样的量
    want, cur = spec.get('pad', [0, 0, 0, 0]), meta.get('pad', [0, 0, 0, 0])
    dl, dt, dr, db = (w - c for w, c in zip(want, cur))
    assert min(dl, dt, dr, db) >= 0, '只能加边不能减边'
    if any((dl, dt, dr, db)):
        cw, ch = cw + dl + dr, ch + dt + db
        for n, c in cells.items():
            im = Image.new('RGBA', (cw, ch)); im.paste(c, (dl, dt)); cells[n] = im
        meta['cell'] = [cw, ch]; meta['anchor'] = [round(meta['anchor'][0] + dl, 1), round(meta['anchor'][1] + dt, 1)]
        if meta.get('head'): meta['head'] = [meta['head'][0] + dl, meta['head'][1] + dt, meta['head'][2] + dl, meta['head'][3] + dt]
        meta['pad'] = want
        print(f'  格子加边 左 {dl} 上 {dt} 右 {dr} 下 {db} → {cw}x{ch}，anchor {meta["anchor"]}（cfg 要 shiftcfg.py 平移 {dl} {dt}）')
    return name, meta, cells, spec


def sh(spec, b):
    """addframes.json 里的框写的是没加边的格内坐标 → 加边以后的格内坐标"""
    l, t = spec.get('pad', [0, 0])[:2]
    return [b[0] + l, b[1] + t, b[2] + l, b[3] + t]


def shb(spec, meta, b):
    """蒙版 / 贴回框：同 sh()，但框贴着原格子哪条边，就一直延伸到加边后的那条边 —— 加的边就是给伸出去的手臂、头发、竹棒留的，
    框不盖住它，伸进边里的那一截会被切掉（G21 / G27 头顶、G29 竹棒尖）"""
    l, t, r, bt = (spec.get('pad') or [0, 0, 0, 0]) + [0] * (4 - len(spec.get('pad') or []))
    cw, ch = meta['cell']; W, H = cw - l - r, ch - t - bt
    return [0 if b[0] <= 0 else b[0] + l, 0 if b[1] <= 0 else b[1] + t, cw if b[2] >= W else b[2] + l, ch if b[3] >= H else b[3] + t]


def boxes(e):
    """box 可以是一个框 [x0, y0, x1, y1]，也可以是几个框的列表（G4 踢腿：上半身 + 踢的那条腿，支撑腿那一块不动）"""
    return [e['box']] if isinstance(e['box'][0], (int, float)) else e['box']


def entry(spec, fn):
    return next(e for e in spec['frames'] if e['name'] == fn)


def prep(d, fn):
    name, meta, cells, spec = load(d)
    e = entry(spec, fn); c = cells[e['base']]; cw, ch = c.size
    K = FIT / max(cw, ch); ox, oy = round((SIDE - cw * K) / 2), round((SIDE - ch * K) / 2)
    bg = Image.new('RGBA', (SIDE, SIDE), SCREEN[e['screen']] + (255,))
    bg.alpha_composite(c.resize((round(cw * K), round(ch * K)), Image.LANCZOS), (ox, oy))
    m = Image.new('RGBA', (SIDE, SIDE), (0, 0, 0, 255))
    for x0, y0, x1, y1 in (shb(spec, meta, b) for b in boxes(e)):
        m.paste((0, 0, 0, 0), (ox + round(x0 * K), oy + round(y0 * K), ox + round(x1 * K), oy + round(y1 * K)))
    raw = os.path.join(TRIO, d, 'raw'); os.makedirs(raw, exist_ok=True)
    bg.convert('RGB').save(os.path.join(raw, f'add_{fn}_base.png')); m.save(os.path.join(raw, f'add_{fn}_mask.png'))
    e.update(K=round(K, 5), ox=ox, oy=oy)
    json.dump(spec, open(os.path.join(TRIO, d, 'addframes.json'), 'w'), ensure_ascii=False, indent=1)
    print(os.path.join(raw, f'add_{fn}_base.png'), os.path.join(raw, f'add_{fn}_mask.png'), 'K %.4f ox %d oy %d' % (K, ox, oy))


def cell(d, cells, e, meta, spec):
    """补出来的这一格：生图里整个人抠出来，照 frames.py build 的配准 —— 按参考帧的头找缩放（生图会把人画大一圈），
    按底格的不动部位（e["fixed"]，格内像素，一般是支撑脚）找平移，贴进同样大小的格子。
    不按像素原位贴（inpaint_paste）：模型不保尺寸，框边会留下硬切口"""
    if e.get('paste') == 'cell':
        # 不是生图：raw/add_<name>.png 已经是加边后整格大小的 RGBA（脚本合成，如 G8_elsa/armswing.py 绕肩转手臂）
        out = Image.open(os.path.join(TRIO, d, 'raw', f'add_{e["name"]}.png')).convert('RGBA')
        assert out.size == cells[e['base']].size, (out.size, cells[e['base']].size)
        print(f'  {e["name"]:8s} 整格贴入（脚本合成）')
        return out
    if e.get('paste') == 'inplace':
        # 小框局部改（换个表情、抬一只手）：模型在蒙版外基本原样画，按 prep 时的 K / ox / oy 原位贴回框里那一块（tools/inpaint_paste.py）。
        # prep 必须是在当前加过边的格子上做的（K、ox、oy 对应这个格子）
        import tempfile, shutil as _sh
        from inpaint_paste import paste as ipaste
        tmp = tempfile.mkdtemp(); b = os.path.join(tmp, 'b.png'); o = os.path.join(tmp, 'o.png')
        cells[e['base']].save(b)
        ipaste(b, os.path.join(TRIO, d, 'raw', f'add_{e["name"]}.png'), e['ox'], e['oy'], e['K'], e['screen'], [shb(spec, meta, x) for x in boxes(e)], o, e.get('feather', 6))
        out = Image.open(o).convert('RGBA'); _sh.rmtree(tmp)
        print(f'  {e["name"]:8s} 原位贴回 {len(boxes(e))} 个框')
        return out
    rgb, al = F.load_sheet(os.path.join(TRIO, d, 'raw', f'add_{e["name"]}.png'), 'auto', None)
    rgb = F.edge_extend(rgb, al)
    c = F.split(rgb, al, 1)[0]
    def head_t():
        """按头找缩放用的模板：帧上写 head = 底格自己的头框（踢腿帧头的朝向和参考帧不一样，按参考帧的头找缩放偏 20%）；
        否则参考帧的头框（老图集 json 没存头框的，addframes.json 顶层写 idle 的头框）。scale_by fixed / scale 写死的不需要"""
        if e.get('head'): return F.gray(cells[e['base']].crop(sh(spec, e['head'])))
        return F.gray(cells[meta.get('ref', 'idle')].crop(meta.get('head') or sh(spec, spec['head'])))
    base = cells[e['base']]; fx = sh(spec, e['fixed']); fix_t = F.gray(base.crop(fx))
    k0 = 1 / e['K'] * 1024 / 1254                          # 生图回来是 1254 见方，底格放大了 K 倍贴在 1024 上
    if 'scale' in e: s = e['scale']; mh = None
    elif e.get('scale_by') == 'fixed':                     # 缩放也按支撑脚（靴子长短不变；模型把踢腿帧的身子画壮一圈，按头找会大 20%）
        best = None
        for s in np.arange(k0 * 0.7, k0 * 1.2, 0.004):
            r = F.find(F.gray(F.resize(c, s)), fix_t)
            if r and (best is None or r[2] > best[1]): best = (s, r[2])
        s, mh = best
    else:
        best = None
        ht = head_t()
        for s in np.arange(k0 * 0.75, k0 * 1.15, 0.005):
            r = F.find(F.gray(F.resize(c, s)), ht)
            if r and (best is None or r[2] > best[1]): best = (s, r[2])
        s, mh = best
    def place(s):
        cs = F.resize(c, s); r = F.find(F.gray(cs), fix_t)
        return cs, fx[0] - r[1], fx[1] - r[0], r[2]

    def ckoff(cs, tx, ty):
        """另一个本该不动的部位（spec.check，另一只脚）在新帧里比底格偏多少（格内像素）"""
        ck = sh(spec, CK); t = F.gray(base.crop(ck)); g = F.gray(cs)
        ex, ey = ck[0] - tx, ck[1] - ty; wx, wy = max(0, int(ex) - 24), max(0, int(ey) - 24)
        q = F.find(g[wy:int(ey) + ck[3] - ck[1] + 24, wx:int(ex) + ck[2] - ck[0] + 24], t)
        return (q[1] + wx - ex, q[0] + wy - ey, q[2]) if q else (99, 99, 0)
    CK = e['check'] if 'check' in e else spec.get('check')   # 帧上写 "check": null = 这一帧没有第二个不动部位（G4 踢腿只有支撑脚）
    cs, tx, ty, rf = place(s)
    if CK and 'scale' not in e:
        # 头在出手 / 前倾里转着歪着，按头找的缩放会差几个百分点（G5 idle2 另一只脚偏 6.5 px）：两只脚都是照底格画的，
        # 在头找到的缩放 ±10% 里细调，让另一只脚也对上（支撑脚已经由平移对上）
        s0 = s
        s = min(np.arange(s0 * 0.9, s0 * 1.1, 0.0025), key=lambda v: np.hypot(*ckoff(*place(v)[:3])[:2]))
        cs, tx, ty, rf = place(s)
    cw, ch = base.size
    bb = cs.getbbox()
    over = [max(0, -(tx + bb[0])), max(0, -(ty + bb[1])), max(0, tx + bb[2] - cw), max(0, ty + bb[3] - ch)]
    if any(v > 0.5 for v in over): print(f'  {e["name"]:8s} 伸出格子 左 {over[0]:.0f} 上 {over[1]:.0f} 右 {over[2]:.0f} 下 {over[3]:.0f}（addframes.json 的 pad 至少要这么多）')
    out = Image.new('RGBA', (cw, ch))
    out.alpha_composite(cs.transform((cw, ch), Image.AFFINE, (1, 0, -tx, 0, 1, -ty), Image.BICUBIC))
    if e.get('paste') == 'box':
        # 只换框里那一块（踢腿帧：上身照底格原样，只重画踢的那条腿）——框外是底格原像素，框边往里 FE px 渐变到新图
        from scipy import ndimage
        M = np.zeros((ch, cw), bool)
        for x0, y0, x1, y1 in (shb(spec, meta, b) for b in boxes(e)): M[y0:y1, x0:x1] = True
        FE = e.get('feather', 8); w = np.clip(ndimage.distance_transform_edt(M) / FE, 0, 1)[..., None]
        A, B = np.array(base).astype(np.float32), np.array(out).astype(np.float32)
        al = A[..., 3:] * (1 - w) + B[..., 3:] * w
        rgb = (A[..., :3] * A[..., 3:] * (1 - w) + B[..., :3] * B[..., 3:] * w) / np.maximum(al, 1e-3)
        out = Image.fromarray(np.dstack([rgb, al]).clip(0, 255).astype(np.uint8), 'RGBA')
    # 和身体不相连的小碎块（蒙版边上生图留的细线、抠剩的点）：小于 40 px 的连通块清掉
    from scipy import ndimage
    o = np.array(out); lab, k = ndimage.label(o[..., 3] > 8)
    if k > 1:
        area = ndimage.sum(np.ones_like(lab), lab, range(1, k + 1))
        for i, a_ in enumerate(area):
            if a_ < 40: o[lab == i + 1, 3] = 0
        out = Image.fromarray(o, 'RGBA')
    if CK:
        q = ckoff(cs, tx, ty)
        print(f'  {e["name"]:8s} 另一只脚偏 {q[0]:+.1f},{q[1]:+.1f} px（匹配 {q[2]:.2f}）')
    r = (0, 0, rf)
    print(f'  {e["name"]:8s} 头缩放 {s / k0:.3f} × 底图（匹配 {mh if mh is None else round(mh, 2)}）  不动部位匹配 {r[2]:.2f}  平移 {tx:+.1f},{ty:+.1f}')
    return out


def build(d):
    name, meta, cells, spec = load(d)
    base_names = [n for n in meta['frames'] if n not in {e['name'] for e in spec['frames'] if e.get('added')}]
    order = list(base_names)
    for e in spec['frames']:
        assert e['base'] in base_names, f'{e["base"]} 不是图集原有的帧'
        if not os.path.exists(os.path.join(TRIO, d, 'raw', f'add_{e["name"]}.png')): print('  跳过（还没生图）', e['name']); continue
        cells[e['name']] = cell(d, cells, e, meta, spec)
        if e['name'] not in order: order.append(e['name']); e['added'] = True
        a = np.array(cells[e['name']])[..., 3] > 8
        edge = int(a[0].sum() + a[-1].sum() + a[:, 0].sum() + a[:, -1].sum())
        print(f'  {e["name"]:8s} ← {e["base"]}  框 {e.get("box", "整格")}  贴边不透明像素 {edge}（> 0 = 新姿势碰到格边被切）')
    cw, ch = meta['cell']; C = meta['cols']; rows = (len(order) + C - 1) // C
    atlas = Image.new('RGBA', (cw * C, ch * rows))
    for i, n in enumerate(order): atlas.paste(cells[n], (i % C * cw, i // C * ch))
    atlas.save(os.path.join(WEB, name + '.webp'), 'WEBP', quality=90, method=6)
    meta['frames'] = order
    if not meta.get('head') and spec.get('head'): meta['head'], meta['ref'] = sh(spec, spec['head']), 'idle'   # combo_scan 判头被挡用
    json.dump(meta, open(os.path.join(WEB, name + '.json'), 'w'), ensure_ascii=False)
    json.dump(spec, open(os.path.join(TRIO, d, 'addframes.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'→ {name}.webp {atlas.size}  names: {json.dumps(order)}')


def sync_cfg(d, g):
    """trio_bestie.js 里这个人 sheet 的 cell / cols / names 跟图集 json 对齐（补帧、加边以后）"""
    import re
    name = os.path.basename(d.rstrip('/')); meta = json.load(open(os.path.join(WEB, name + '.json')))
    P = os.path.join(TRIO, '../../web/trio_bestie.js'); s = open(P).read()
    m = re.search(r'^    %s: \{.*?^    \},\n' % g, s, re.S | re.M); blk = m.group(0)
    new = re.sub(r"(sheet: \{ src: 'assets/trio/%s\.webp', )cell: \[[^\]]*\], cols: \d+, names: \[[^\]]*\]" % name,
                 lambda q: q.group(1) + 'cell: [%d, %d], cols: %d, names: [%s]' % (*meta['cell'], meta['cols'], ', '.join("'%s'" % n for n in meta['frames'])), blk)
    assert new != blk or "names: [%s]" % ', '.join("'%s'" % n for n in meta['frames']) in blk, 'sheet 行没找到'
    open(P, 'w').write(s[:m.start()] + new + s[m.end():])
    print(g, 'sheet →', meta['cell'], meta['frames'])


if __name__ == '__main__':
    d, cmd = sys.argv[1], sys.argv[2]
    if cmd == 'prep': prep(d, sys.argv[3])
    elif cmd == 'paste': shutil.copy(sys.argv[4], os.path.join(TRIO, d, 'raw', f'add_{sys.argv[3]}.png')); print('ok')
    elif cmd == 'cfg': sync_cfg(d, sys.argv[3])
    else: build(d)
