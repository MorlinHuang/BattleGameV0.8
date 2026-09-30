"""crew.js 老角色（后排滑板哥们 B1~B4 / 平衡车闺蜜 G1~G3）迁成 trio.js 帧序列（2026-10-01）。

用户："之前做好的很多角色，已经细致调优过的角色尽量保留……立绘、配色、脸都不换……用原立绘做底"。
所以这里**不生图**：直接拿 crew.js 在用的分层原图（web/assets/world/buddy%n_%k.webp、bestie%n_%k.webp，v14/buddy|bestie/make.py 切的），
照 crew.js drawOne 的转法（上身绕腰 body.pivot、闺蜜手臂再绕肩 arm.pivot、下身 + 滑板 / 平衡车不动）合成每一个姿势帧：
  idle 待机（枪 / 罐端着）、wind 蓄力（举起来）、aim0..aimN 喷的时候按瞄准角挑的那一帧（crew.js 的 aim.lo~hi 等分）、
  闺蜜另有 kick0..kickN（每按一下后坐：手臂往上甩 kick[0]、上身往后仰 kick[1]，crew.js MIST.anim）、follow 收势、ride 滑进来、brake 刹住。
每一帧都是原图的像素，只是转了角度 —— 外形、配色、脸跟 crew.js 画出来的一模一样（对比图 shots/trio_std/老_<编号>_原图对比.png）。

尺寸：按 crew.js 三人组那一排远近的中间值（哥们 rows[0] 0.87~0.94 → d 0.905 × k 0.85 = 0.769；闺蜜 0.68~0.74 → 0.71 × 0.85 = 0.604）
烤进图集，再除以 AT_S（后排统一的 at.s 0.83 / 0.88）—— cfg 里 at.s 写 AT_S 时屏幕上和 crew.js 原来一样大。
锚点 = 脚底（crew.js spr.foot：滑板 / 平衡车着地的那一点）。喷口（crew.js spr.muzzle）每个 aim / kick 帧各算一个，打印成 cfg 的 atk.aim.nozzle。

用法（在 chashouji 下）：python3 v14/trio/tools/crewframes.py B1|B2|B3|B4|G1|G2|G3|all
  → web/assets/trio/<名>.webp + .json，v14/trio/preview/<名>_frames.png；打印 cfg 片段
  python3 v14/trio/tools/crewframes.py compare B1|...|all → shots/trio_std/老_<编号>_原图对比.png
      左：crew.js 原来画的样子（分层原图、瞄准角 0、三人组那一排的中间缩放）；右：新图集的 idle 帧 × at.s。同一屏幕像素比例，标剪影面积"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
WEB = os.path.join(ROOT, 'web'); OUT = os.path.join(WEB, 'assets/trio'); PRE = os.path.join(ROOT, 'v14/trio/preview')

# crew.js Buddy / MIST（只抄合成要用的几项，crew.js 改了这里跟着改）
RIG = {
    'buddy': dict(face=-1, src='assets/world/buddy%n_%k.webp', layers=['up', 'lo'], body=[266, 200], bk=1.0, arm=None,
                  foot=[260, 446], muzzle=[2, 88], lo=-0.52, hi=0.21, kick=None, lean=0, s=0.905 * 0.85, AT_S=0.83),
    'bestie': dict(face=+1, src='assets/world/bestie%n_%k.webp', layers=['arm', 'up', 'lo'], body=[174, 202], bk=0.3, arm=[198, 105],
                   foot=[184, 485], muzzle=[361, 20], lo=-0.7, hi=0.35, kick=[0.12, 0.05], lean=0.08, s=0.71 * 0.85, AT_S=0.88),
}
WHO = {'B1': ('buddy', 1, 'B1_surfer'), 'B2': ('buddy', 4, 'B2_zhizunbao'), 'B3': ('buddy', 5, 'B3_beile'), 'B4': ('buddy', 7, 'B4_yagami'),
       'G1': ('bestie', 2, 'G1_shades'), 'G2': ('bestie', 6, 'G2_bulma'), 'G3': ('bestie', 7, 'G3_sailor')}
SS = 2                                         # 合成时先放大 SS 倍转、再缩（转角边缘不糊）
PAD = 160


def angles(R, th, kick=0.0, lean=0.0):
    """crew.js angles()：[上身转角, 手臂绝对转角]（仰角，抬高为正）"""
    if not R['arm']: return th - R['lean'] * lean, th
    k0, k1 = R['kick'] or [0, 0]
    return R['bk'] * th - R['lean'] * lean + k1 * kick, th + k0 * kick


def turn(q, c, phi):
    co, si = math.cos(phi), math.sin(phi); dx, dy = q[0] - c[0], q[1] - c[1]
    return [c[0] + dx * co - dy * si, c[1] + dx * si + dy * co]


def rot_layer(im, c, phi):
    """整张层绕贴图点 c 转 phi（canvas 顺时针为正）"""
    return im.rotate(-math.degrees(phi), resample=Image.BICUBIC, center=(c[0] * SS, c[1] * SS))


def compose(R, lay, th, kick=0.0, lean=0.0):
    """crew.js drawOne：arm（绕肩，跟着上身）→ up（绕腰）→ lo（不动，盖在最上）。返回 (RGBA 图 SS 倍, 喷口贴图点, 喷口仰角)"""
    F = R['face']; bt, at_ = angles(R, th, kick, lean)
    W, H = lay['lo'].size
    cv = Image.new('RGBA', (W, H))
    if R['arm']:
        a = rot_layer(lay['arm'], R['arm'], -F * (at_ - bt))          # 先绕肩转"手臂比上身多转的那部分"，再和上身一起绕腰转
        cv.alpha_composite(rot_layer(a, R['body'], -F * bt))
    cv.alpha_composite(rot_layer(lay['up'], R['body'], -F * bt))
    cv.alpha_composite(lay['lo'])
    if R['arm']:
        sh1 = turn(R['arm'], R['body'], -F * bt); m1 = turn(R['muzzle'], R['arm'], -F * at_)
        m = [m1[0] + sh1[0] - R['arm'][0], m1[1] + sh1[1] - R['arm'][1]]
        return cv, m, at_
    return cv, turn(R['muzzle'], R['body'], -F * bt), bt


def build(code):
    side, n, name = WHO[code]; R = RIG[side]
    lay = {}
    for k in R['layers']:                                                  # 四周先垫 PAD（转起来枪口 / 罐子会伸出原图的边）
        im = Image.open(os.path.join(WEB, R['src'].replace('%n', str(n)).replace('%k', k))).convert('RGBA')
        big = Image.new('RGBA', (im.width + 2 * PAD, im.height + 2 * PAD)); big.paste(im, (PAD, PAD))
        lay[k] = big.resize((big.width * SS, big.height * SS), Image.LANCZOS)
    sh = lambda q: [q[0] + PAD, q[1] + PAD] if q else q
    R = dict(R, body=sh(R['body']), arm=sh(R['arm']), foot=sh(R['foot']), muzzle=sh(R['muzzle']))
    lo, hi = R['lo'], R['hi']
    n_aim = 11
    aims = [round(lo + (hi - lo) * i / (n_aim - 1), 4) for i in range(n_aim)]
    poses = [('idle', lo + (hi - lo) * 0.45, 0, 0), ('wind', hi + 0.12, 0, 0), ('follow', lo - 0.05, 0, 0),
             ('ride', (lo + hi) / 2 + 0.1, 0, 0), ('brake', hi + 0.05, 0, 0)]
    poses += [(f'aim{i}', th, 0, 1) for i, th in enumerate(aims)]          # 喷着：上身往前探（lean 1）
    if R['kick']: poses += [(f'kick{i}', th, 1, 1) for i, th in enumerate(aims)]
    K = R['s'] / R['AT_S']                                                  # 贴图像素 → 格内像素
    ims, noz = {}, {}
    for fn, th, kk, ln in poses:
        im, m, a = compose(R, lay, th, kk, ln)
        ims[fn] = im.resize((round(im.width / SS * K), round(im.height / SS * K)), Image.LANCZOS)
        noz[fn] = [round(m[0] / SS * K * SS, 1), round(m[1] / SS * K * SS, 1), round(a, 4)]   # muzzle 是贴图像素（未放大）
    # 统一格：全部帧 alpha 并集的外框 + 4
    un = None
    for im in ims.values():
        a = np.array(im)[..., 3] > 8; un = a if un is None else un | a
    ys, xs = np.nonzero(un); x0, y0 = max(0, xs.min() - 4), max(0, ys.min() - 4); x1, y1 = xs.max() + 5, ys.max() + 5
    cw, ch = int(x1 - x0), int(y1 - y0)
    names = list(ims); cols = 4; rows = (len(names) + cols - 1) // cols
    atlas = Image.new('RGBA', (cw * cols, ch * rows))
    for i, fn in enumerate(names): atlas.paste(ims[fn].crop((x0, y0, x0 + cw, y0 + ch)), ((i % cols) * cw, (i // cols) * ch))
    anchor = [round(float(R['foot'][0] * K - x0), 1), round(float(R['foot'][1] * K - y0), 1)]
    hb = head_box(ims['idle'].crop((x0, y0, x0 + cw, y0 + ch)), R['body'][0] * K - x0, K)
    atlas.save(os.path.join(OUT, name + '.webp'), 'WEBP', quality=90, method=6)
    json.dump({'cell': [cw, ch], 'cols': cols, 'frames': names, 'anchor': anchor, 'residual': 0, 'head': hb, 'ref': 'idle',
               'src': 'crewframes.py'}, open(os.path.join(OUT, name + '.json'), 'w'), ensure_ascii=False)
    nz = {fn: [round(float(v[0] - x0), 1), round(float(v[1] - y0), 1), v[2]] for fn, v in noz.items() if fn.startswith(('aim', 'kick'))}
    # 预览：每帧一格，锚点红圈、喷口蓝点、头框绿
    os.makedirs(PRE, exist_ok=True)
    pv = Image.new('RGBA', atlas.size, (255, 255, 255, 255)); pv.alpha_composite(atlas); d = ImageDraw.Draw(pv)
    for i, fn in enumerate(names):
        ox, oy = (i % cols) * cw, (i // cols) * ch
        d.rectangle([ox, oy, ox + cw - 1, oy + ch - 1], outline=(200, 200, 200)); d.text((ox + 3, oy + 3), fn, fill=(0, 0, 0))
        d.ellipse([ox + anchor[0] - 4, oy + anchor[1] - 4, ox + anchor[0] + 4, oy + anchor[1] + 4], outline=(255, 0, 0), width=2)
        if fn in nz: q = nz[fn]; d.ellipse([ox + q[0] - 3, oy + q[1] - 3, ox + q[0] + 3, oy + q[1] + 3], fill=(0, 80, 255))
    pv.save(os.path.join(PRE, name + '_frames.png'))
    kb = os.path.getsize(os.path.join(OUT, name + '.webp')) // 1024
    print(f'{code} {name}: 格 {cw}x{ch}，{len(names)} 帧，{kb}KB，锚点 {anchor}，头框 {hb}')
    return dict(name=name, cell=[cw, ch], cols=cols, names=names, anchor=anchor, nozzle=nz, aims=aims, K=K)


def head_box(im, px, K):
    """头框（combo_scan 判"头被挡"用）：剪影最上面 20% 高那几行的横向范围 —— crew 立绘都是站直的人，头在最上面
    枪 / 罐子举起来也会进这几行，所以只看腰转轴正上方 −140 ~ +70 贴图像素那几列（七个人的头都在这一带，同一姿势改图换人）"""
    a = np.array(im)[..., 3] > 40; ys, xs = np.nonzero(a)
    top = ys[(xs >= px - 140 * K) & (xs <= px + 70 * K)].min(); y1 = top + 0.2 * (ys.max() - top)
    sel = (ys <= y1) & (xs >= px - 140 * K) & (xs <= px + 70 * K); xs_, ys_ = xs[sel], ys[sel]   # 腰转轴上方那一带（枪 / 罐子伸在外面）
    # 头：最上面那一团（按列连通取最宽的一段）
    cols = np.unique(xs_); runs = np.split(cols, np.nonzero(np.diff(cols) > 3)[0] + 1)
    run = max(runs, key=len)
    return [int(run.min()), int(top), int(run.max()) + 1, int(round(y1))]


def compare(code):
    side, n, name = WHO[code]; R = RIG[side]
    lay = {k: Image.open(os.path.join(WEB, R['src'].replace('%n', str(n)).replace('%k', k))).convert('RGBA') for k in R['layers']}
    W0, H0 = lay['lo'].size
    old = Image.new('RGBA', (W0, H0))
    for k in R['layers']: old.alpha_composite(lay[k])                    # 瞄准角 0：各层都不转，就是切层之前的原立绘
    old = old.resize((round(W0 * R['s']), round(H0 * R['s'])), Image.LANCZOS)
    meta = json.load(open(os.path.join(OUT, name + '.json'))); cw, ch = meta['cell']
    at = Image.open(os.path.join(OUT, name + '.webp')).convert('RGBA'); i = meta['frames'].index('idle')
    new = at.crop(((i % meta['cols']) * cw, (i // meta['cols']) * ch, (i % meta['cols'] + 1) * cw, (i // meta['cols'] + 1) * ch))
    new = new.resize((round(cw * R['AT_S']), round(ch * R['AT_S'])), Image.LANCZOS)
    hh = max(old.height, new.height) + 56
    cv = Image.new('RGBA', (old.width + new.width + 60, hh), (236, 232, 224, 255))
    cv.alpha_composite(old, (20, hh - old.height - 10)); cv.alpha_composite(new, (40 + old.width, hh - new.height - 10))
    d = ImageDraw.Draw(cv); fo = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 15)
    d.text((20, 6), f'{code} crew.js 原图（s {R["s"]:.3f}）', fill=(0, 0, 0), font=fo); d.text((40 + old.width, 6), f'{name} idle 帧 × at.s {R["AT_S"]}', fill=(0, 0, 0), font=fo)
    ba = lambda im: (np.array(im)[..., 3] > 40).sum()
    d.text((20, 24), f'剪影 {ba(old)} px', fill=(60, 60, 60), font=fo); d.text((40 + old.width, 24), f'剪影 {ba(new)} px（{ba(new) / ba(old):.3f} 倍）', fill=(60, 60, 60), font=fo)
    os.makedirs(os.path.join(ROOT, 'shots/trio_std'), exist_ok=True)
    cv.convert('RGB').save(os.path.join(ROOT, 'shots/trio_std', f'老_{code}_原图对比.png'))
    print(code, '原图剪影', ba(old), '新 idle', ba(new), f'{ba(new) / ba(old):.3f}')


if __name__ == '__main__':
    if sys.argv[1:2] == ['compare']:
        which = sys.argv[2] if len(sys.argv) > 2 else 'all'
        for c in (WHO if which == 'all' else [which]): compare(c)
        sys.exit()
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    res = {c: build(c) for c in (WHO if which == 'all' else [which])}
    json.dump(res, open('/tmp/crewframes.json', 'w'), ensure_ascii=False)
