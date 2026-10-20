"""补帧原尺寸自检（2026-10-01，精闺1 第 4 批：用户"最近出的图有很多瑕疵"）。
每人一张拼图：每一行 = 一张补出来的帧 | 它的底格（原帧）| 新帧 | 差异（新旧不同的像素标红、蒙版框画青线），全部原尺寸、灰底；
同时打印四项机检读数（只在新帧和底格不一样的那一块里量，底格本来就有的不算）：
  · 幕布色残留：不透明像素里色相接近幕布（品红 / 绿 / 蓝）的个数 —— 毛边、抠剩的斑
  · 破洞：剪影内部被透明包住的小洞（< 400 px 的透明连通块，不连到格边）
  · 碎块：和主体不相连的不透明小块（< 300 px）—— 框边留下的残片、飘在外面的线头
  · 框边接缝：蒙版框边两侧 3 px 的颜色跳变（平均 |ΔRGB|）比框内同样距离的平均跳变大多少倍（> 2 = 看得出的拼缝 / 色差）
用法（在 chashouji 下）：python3 v14/trio/bestie/tools/selfcheck.py G16_daji [帧 ...]   → shots/trio_bestie/精闺1_自检_<目录>.png"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__)); TRIO = os.path.abspath(os.path.join(HERE, '../..')); ROOT = os.path.abspath(os.path.join(TRIO, '../..'))
WEB = os.path.join(ROOT, 'web/assets/trio'); OUT = os.path.join(ROOT, 'shots/trio_bestie')
BG = (200, 200, 204)
FONT = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', 13)
HUE = {'magenta': lambda r, g, b: (np.minimum(r, b) - g > 60), 'green': lambda r, g, b: (g - np.maximum(r, b) > 60),
       'blue': lambda r, g, b: (b - np.maximum(r, g) > 90)}


def cells(name):
    m = json.load(open(os.path.join(WEB, name + '.json'))); a = Image.open(os.path.join(WEB, name + '.webp')).convert('RGBA')
    cw, ch = m['cell']; C = m['cols']
    return m, {n: a.crop((i % C * cw, i // C * ch, i % C * cw + cw, i // C * ch + ch)) for i, n in enumerate(m['frames'])}


def boxes_of(e, spec, meta):
    if 'box' not in e: return []
    bs = [e['box']] if isinstance(e['box'][0], (int, float)) else e['box']
    l, t, r, bt = (spec.get('pad') or [0, 0, 0, 0]) + [0] * (4 - len(spec.get('pad') or []))
    cw, ch = meta['cell']; W, H = cw - l - r, ch - t - bt
    return [[0 if b[0] <= 0 else b[0] + l, 0 if b[1] <= 0 else b[1] + t, cw if b[2] >= W else b[2] + l, ch if b[3] >= H else b[3] + t] for b in bs]


def check(new, base, bxs, screen):
    N = np.array(new).astype(np.int16); B = np.array(base).astype(np.int16)
    an, ab = N[..., 3] > 128, B[..., 3] > 128
    vis = (N[..., 3] > 8) | (B[..., 3] > 8)                     # 两边都透明的像素 RGB 是幕布残值，不算
    diff = vis & ((np.abs(N[..., :3] * (N[..., 3:] / 255) - B[..., :3] * (B[..., 3:] / 255)).max(-1) > 24) | (an != ab))
    zone = ndimage.binary_dilation(diff, iterations=4)
    r, g, b = N[..., 0], N[..., 1], N[..., 2]
    keys = [screen] if screen in HUE else list(HUE)
    tint = np.zeros_like(an)
    for k in keys: tint |= HUE[k](r, g, b)
    tint &= (N[..., 3] > 40) & zone
    # 破洞：透明连通块不碰格边、面积小
    lab, n = ndimage.label(~an); holes = 0
    if n:
        sz = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)); edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
        for i, s in enumerate(sz):
            if s < 400 and (i + 1) not in edge and zone[lab == i + 1].any(): holes += int(s)
    lab, n = ndimage.label(an); frag = 0; fragn = 0
    if n > 1:
        sz = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1)); big = sz.argmax()
        for i, s in enumerate(sz):
            if i != big and s < 300 and zone[lab == i + 1].any(): frag += int(s); fragn += 1
    # 框边接缝：框边内外各 3 px 的颜色跳变 vs 框内深处同样宽度的跳变
    seam = []
    for x0, y0, x1, y1 in bxs:
        for (p, q, inner) in [((slice(y0, y1), x0 - 3), (slice(y0, y1), x0 + 3), (slice(y0, y1), x0 + 12)),
                              ((slice(y0, y1), x1 - 4), (slice(y0, y1), x1 + 2), (slice(y0, y1), x1 - 14)),
                              ((y0 - 3, slice(x0, x1)), (y0 + 3, slice(x0, x1)), (y0 + 12, slice(x0, x1))),
                              ((y1 - 4, slice(x0, x1)), (y1 + 2, slice(x0, x1)), (y1 - 14, slice(x0, x1)))]:
            try:
                P, Q = N[p], N[q]; I = N[inner]
                ok = (P[..., 3] > 200) & (Q[..., 3] > 200) & (I[..., 3] > 200)
                if ok.sum() < 8: continue
                j = np.abs(P[..., :3] - Q[..., :3]).mean(-1)[ok].mean(); k = np.abs(Q[..., :3] - I[..., :3]).mean(-1)[ok].mean()
                seam.append(round(float(j / max(k, 4)), 2))
            except IndexError:
                continue
    return dict(tint=int(tint.sum()), holes=holes, frag=frag, fragn=fragn, seam=max(seam) if seam else 0), diff


def main(d, only=None):
    name = os.path.basename(d.rstrip('/')); meta, C = cells(name)
    spec = json.load(open(os.path.join(TRIO, 'bestie', name, 'addframes.json')))
    es = [e for e in spec['frames'] if e['name'] in C and (not only or e['name'] in only)]
    cw, ch = meta['cell']; rows = []
    for e in es:
        new, base = C[e['name']], C[e['base']]; bxs = boxes_of(e, spec, meta)
        r, diff = check(new, base, bxs, e.get('screen'))
        tiles = []
        for im in (base, new):
            g = Image.new('RGBA', im.size, BG + (255,)); g.alpha_composite(im); tiles.append(g.convert('RGB'))
        dv = Image.new('RGBA', new.size, BG + (255,)); dv.alpha_composite(new); dv = dv.convert('RGB')
        dv = Image.blend(dv, Image.new('RGB', dv.size, BG), 0.55); D = np.array(dv); D[diff] = (230, 40, 40); dv = Image.fromarray(D); dd = ImageDraw.Draw(dv)
        for b in bxs: dd.rectangle([b[0], b[1], b[2] - 1, b[3] - 1], outline=(0, 170, 200), width=1)
        tiles.append(dv); rows.append((e, r, tiles))
        print(f'{name:16s} {e["name"]:8s} ← {e["base"]:6s} 幕布色 {r["tint"]:4d}  破洞 {r["holes"]:4d}  碎块 {r["fragn"]} 块 {r["frag"]:4d} px  接缝倍数 {r["seam"]}')
    H = 18 + len(rows) * (ch + 22); o = Image.new('RGB', (cw * 3 + 12, H), 'white'); d_ = ImageDraw.Draw(o)
    d_.text((4, 3), f'{name}  原帧（底格） | 新帧 | 差异（红 = 改过的像素，青框 = 蒙版框）  原尺寸', fill=(0, 0, 0), font=FONT)
    for j, (e, r, tiles) in enumerate(rows):
        y = 18 + j * (ch + 22)
        d_.text((4, y + 3), f'{e["name"]} ← {e["base"]}   幕布色 {r["tint"]}  破洞 {r["holes"]}  碎块 {r["fragn"]}/{r["frag"]}px  接缝 ×{r["seam"]}', fill=(0, 0, 0), font=FONT)
        for k, t in enumerate(tiles): o.paste(t, (k * (cw + 6), y + 20))
    os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, f'精闺1_自检_{name}.png'); o.save(p); print('→', p)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
