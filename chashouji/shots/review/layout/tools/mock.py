# 构图 mockup：用真实底图层 + 真实主角层 + 真实帮手贴图，按候选站位/缩放/转角合成，并量遮挡。
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw
WD = '/workspace/art/chashouji/web/assets/world/'
G = json.load(open('/tmp/rv/L_geo.json'))
PAD = 600
SPR = {
  'B': dict(foot=(113,483), muzzle=(290,18), body=(103,200), arm=(127,103), k=0.3, head=(40,0,125,95)),
  'T': dict(foot=(156,459), muzzle=(522,63), body=(136,184), whole=(161,71), head=(140,20,215,115)),
}
def layer(name): return Image.open(WD + name + '.webp').convert('RGBA')
def placed(im, s):
    im = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
    c = Image.new('RGBA', (im.width + 2*PAD, im.height + 2*PAD)); c.paste(im, (PAD, PAD)); return c
def rot(c, pivot_s, deg):  # pivot in scaled sprite coords
    return c.rotate(deg, resample=Image.BICUBIC, center=(pivot_s[0]+PAD, pivot_s[1]+PAD))
def tp(q, s, center, deg):  # transform sprite point (scaled) by rotation about center (scaled), CCW deg
    a = math.radians(deg); x, y = q[0]*s - center[0], q[1]*s - center[1]
    return (center[0] + x*math.cos(a) + y*math.sin(a), center[1] - x*math.sin(a) + y*math.cos(a))
def build(kind, skin, s, th, mode):
    """返回 (RGBA 画布, 脚底点在画布里的位置, 喷口点, 头框中心)。th=仰角(负=朝下)。"""
    S = SPR[kind]; deg = math.degrees(th)   # face +1: canvas CCW deg = th
    if kind == 'B':
        n = f'bestie{skin+1}'; lo, up, arm = placed(layer(n+'_lo'), s), placed(layer(n+'_up'), s), placed(layer(n+'_arm'), s)
        bt = S['k']*deg; bc = (S['body'][0]*s, S['body'][1]*s)
        arm = rot(rot(arm, (S['arm'][0]*s, S['arm'][1]*s), deg - bt), bc, bt); up = rot(up, bc, bt)
        out = Image.new('RGBA', lo.size); out.alpha_composite(arm); out.alpha_composite(up); out.alpha_composite(lo)
        sh = tp(S['arm'], s, bc, bt); m = tp(S['muzzle'], s, bc, bt)
        a = math.radians(deg - bt); dx, dy = m[0]-sh[0], m[1]-sh[1]
        m = (sh[0] + dx*math.cos(a) + dy*math.sin(a), sh[1] - dx*math.sin(a) + dy*math.cos(a))
        head = tp(((S['head'][0]+S['head'][2])/2, (S['head'][1]+S['head'][3])/2), s, bc, bt)
    else:
        lo0 = layer('truth1_lo')
        if mode.endswith('+board'):   # 示意：借平衡车的踏板拉长垫在她两只靴子下面（只为看构图，不是成品素材）
            bd = layer('bestie1_lo').crop((20, 432, 210, 486)).resize((340, 62), Image.LANCZOS)
            big = Image.new('RGBA', (lo0.width, lo0.height + 50)); big.alpha_composite(bd, (-12, 440)); big.alpha_composite(lo0)
            lo0 = big; mode = mode[:-6]
        lo, up = placed(lo0, s), placed(layer('truth1_up'), s)
        if mode == 'whole':
            c = (S['whole'][0]*s, S['whole'][1]*s); lo, up = rot(lo, c, deg), rot(up, c, deg)
        else:   # 'lean'：只有上身（含罐子）绕腰转，腿不动
            c = (S['body'][0]*s, S['body'][1]*s); up = rot(up, c, deg)
        out = Image.new('RGBA', lo.size); out.alpha_composite(up); out.alpha_composite(lo)
        m = tp(S['muzzle'], s, c, deg)
        head = tp(((S['head'][0]+S['head'][2])/2, (S['head'][1]+S['head'][3])/2), s, c, deg)
        if mode == 'whole': foot = tp(S['foot'], s, c, deg)
    foot = (S['foot'][0]*s, S['foot'][1]*s)
    off = lambda p: (p[0]+PAD, p[1]+PAD)
    return out, off(foot), off(m), off(head)
def scene(pose, actors, fn, title=''):
    """actors: dict(kind, skin, s, x, y(脚底屏幕点，whole 模式时=肩膀转之前脚底), th|'auto', mode, front)"""
    g = G[pose]; bg = Image.open(f'/tmp/rv/L_{pose}_bg.png').convert('RGBA'); ch = Image.open(f'/tmp/rv/L_{pose}_ch.png').convert('RGBA')
    W, H = bg.size; fb = g['fb']; tgt = (fb[0]-0.3*fb[2], fb[1]-0.25*fb[2])
    lays, stats = [], []
    for a in sorted(actors, key=lambda a: a['s']):
        th = a.get('th', 'auto')
        if th == 'auto':   # 两次迭代：按喷口反解仰角
            th = -0.3
            for _ in range(8):
                im, ft, m, hd = build(a['kind'], a.get('skin',0), a['s'], th, a.get('mode','lean'))
                ox, oy = a['x'] - ft[0], a['y'] - ft[1]
                mx, my = m[0]+ox, m[1]+oy
                # 喷口到目标所需仰角 vs 当前喷口朝向：朝向≈th，修正
                need = math.atan2(-(tgt[1]-my), tgt[0]-mx); th = max(-0.95, min(0.35, th + 0.8*(need - th)))
        im, ft, m, hd = build(a['kind'], a.get('skin',0), a['s'], th, a.get('mode','lean'))
        ox, oy = round(a['x'] - ft[0]), round(a['y'] - ft[1])
        full = Image.new('RGBA', (W + 2*2000, H + 2*2000)); full.paste(im, (ox+2000, oy+2000), im)
        big = np.array(full)[:, :, 3] > 40; total = int(big.sum())
        sc = full.crop((2000, 2000, 2000+W, 2000+H)); on = np.array(sc)[:, :, 3] > 40
        lays.append((a, sc, on, (m[0]+ox, m[1]+oy), (hd[0]+ox, hd[1]+oy), total, th))
    heroA = np.array(ch)[:, :, 3] > 40
    img = bg.copy()
    for L in lays:
        if not L[0].get('front'): img.alpha_composite(L[1])
    img.alpha_composite(ch)
    for L in lays:
        if L[0].get('front'): img.alpha_composite(L[1])
    d = ImageDraw.Draw(img)
    for i, (a, sc, on, m, hd, total, th) in enumerate(lays):
        # 被挡：主角 + 画在它之后的其他帮手
        occ = np.zeros_like(on)
        if not a.get('front'): occ |= heroA
        for j, L2 in enumerate(lays):
            later = (L2[0].get('front', False), j) > (a.get('front', False), i)
            if later: occ |= L2[2]
        vis = on & ~occ
        hx, hy = int(hd[0]), int(hd[1]); r = int(40*a['s'])
        hb = on[max(0,hy-r):hy+r, max(0,hx-r):hx+r]; hv = vis[max(0,hy-r):hy+r, max(0,hx-r):hx+r]
        st = dict(who=a['kind']+str(a.get('skin',0)), s=a['s'], th=round(th,2), onscreen=round(on.sum()/max(1,total),3),
                  visible=round(vis.sum()/max(1,on.sum()),3), face=round(hv.sum()/max(1,hb.sum()),3) if hb.sum() else 0.0,
                  height=int(np.ptp(np.nonzero(on.any(1))[0])) if on.any() else 0)
        stats.append(st)
        d.line([m, tgt], fill=(60,200,60,255), width=5)
    fa = g['fa']; fx, fy, fr = int(fa[0]), int(fa[1]), int(fa[2]*1.3)
    hero_face = heroA[fy-fr:fy+fr, fx-fr:fx+fr]; covered = np.zeros_like(hero_face)
    for L in lays:
        if L[0].get('front'): covered |= L[2][fy-fr:fy+fr, fx-fr:fx+fr]
    stats.append(dict(who='heroine_face', visible=round(1 - (hero_face & covered).sum()/max(1,hero_face.sum()),3)))
    ph = g['phone']; by = ph[1] - 44 - 200
    d.rectangle([ph[0]-150, by-140-2*76-32, ph[0]+150, by+32], outline=(255,120,200,255), width=3)
    d.rectangle([0, 1334, W, H], fill=(20,20,24,170)); d.text((12, 1345), 'y>1334 platform comment overlay', fill=(255,255,255))
    d.rectangle([0, 0, W, 40], fill=(0,0,0,160)); d.text((10, 12), f'{pose} {title}', fill=(255,255,0))
    img.convert('RGB').save(fn)
    return stats
