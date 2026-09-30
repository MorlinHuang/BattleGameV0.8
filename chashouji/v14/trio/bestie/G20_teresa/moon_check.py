"""G20 月亮挂件验收读数（在 chashouji 下跑）。

① 图集：python3 v14/trio/bestie/G20_teresa/moon_check.py atlas <旧图集.webp>
   各帧（挂件月亮 + 人那一层，按 cfg 摆好）的月亮区扣掉人盖住的部分，和 idle 逐像素比（审查第八批给的验收法）。
   旧图集（moon.py 之前，月亮画在帧里）同样比：月亮区 = moon.py 的 moon_mask，扣掉两帧里人盖住的部分。
   打印：月亮区像素数、差 > 8 / > 40 的像素数、最大差；上月尖（月亮最高那一行往下 12 行里最右一列）x。
② 胶片：python3 v14/trio/bestie/G20_teresa/moon_check.py film <at_y> <胶片.png> [...]
   只看月亮左半边的背弧（格内 x 0~60、y 30~240 × at.s 摆到屏幕）：手和月牙镖都到不了这里。相邻两格（隔一个 ammoms）比：
   金 = 月亮色（色相 44~74、饱和 > 0.12、亮 > 0.55）；轮廓变 = 一格是金、另一格不是金的像素；同金变色 = 两格都是金、颜色差 > 40。
   呼吸（breathe 0.014）让人和月亮一起绕锚点胀缩，相邻两格之间是连续的小变化；换帧的跳变叠在上面"""
import json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import moon as M

WEB = os.path.join(HERE, '../../../../web/assets/trio')
AT_X, S, ANCHOR = 150, 0.9, (105.5, 181.5)


def cells(path, meta):
    a = np.array(Image.open(path).convert('RGBA')).astype(float)
    CW, CH = meta['cell']; C = meta['cols']
    return {n: a[i // C * CH:(i // C + 1) * CH, i % C * CW:(i % C + 1) * CW] for i, n in enumerate(meta['frames'])}


def over(top, bot):
    ta, ba = top[..., 3:] / 255, bot[..., 3:] / 255
    A = ta + ba * (1 - ta)
    rgb = (top[..., :3] * ta + bot[..., :3] * ba * (1 - ta)) / np.maximum(A, 1e-6)
    return np.concatenate([rgb, A * 255], -1)


def tip(moonmask):
    ys = np.nonzero(moonmask.any(1))[0]
    return int(np.nonzero(moonmask[ys[0]:ys[0] + 12].any(0))[0].max())


def atlas(old):
    meta = json.load(open(os.path.join(WEB, 'G20_teresa.json')))
    new = cells(os.path.join(WEB, 'G20_teresa.webp'), meta)
    part = np.array(Image.open(os.path.join(WEB, 'G20_moon.webp')).convert('RGBA')).astype(float)
    CW, CH = meta['cell']
    lay = np.zeros((CH, CW, 4))
    ox, oy = round(ANCHOR[0] - 104.5), round(ANCHOR[1] - 177.5)            # cfg：pivot [104.5, 177.5]、at = 锚点（整数偏移 1, 4）
    lay[oy:oy + part.shape[0], ox:ox + part.shape[1]] = part[:CH - oy, :CW - ox]
    moon = lay[..., 3] > 0
    print('== 改后（挂件月亮 + 人那一层；八帧 parts.at 都是 [105.5, 181.5]）')
    ref = over(new['idle'], lay)
    for n, c in new.items():
        comp = over(c, lay)
        m = moon & (c[..., 3] == 0) & (new['idle'][..., 3] == 0)       # 月亮区扣掉两帧里人盖住的部分
        d = np.abs(comp - ref)[m].max(-1) if m.any() else np.zeros(1)
        print('%-6s 月亮区 %5d px  差 > 8：%d  差 > 40：%d  最大差 %.0f  上月尖 x %d' % (n, m.sum(), (d > 8).sum(), (d > 40).sum(), d.max(), tip(moon)))
    print('== 改前（%s：月亮画在每一帧里）' % os.path.basename(old))
    oc = cells(old, json.load(open(old.rsplit('.', 1)[0] + '.json')))
    mm = {n: M.moon_mask(c, M.KEEP.get(n))[0] for n, c in oc.items()}
    for n, c in oc.items():
        pi_, pn = (oc['idle'][..., 3] > 0) & ~mm['idle'], (c[..., 3] > 0) & ~mm[n]
        m = (mm['idle'] | mm[n]) & ~pi_ & ~pn                           # 两帧里谁的月亮都算，扣掉人
        d = np.abs(c - oc['idle'])[m].max(-1)
        print('%-6s 月亮区 %5d px  差 > 8：%d  差 > 40：%d  最大差 %.0f  上月尖 x %d' % (n, m.sum(), (d > 8).sum(), (d > 40).sum(), d.max(), tip(mm[n])))


def film(at_y, paths):
    x0, y0 = AT_X - ANCHOR[0] * S, at_y - ANCHOR[1] * S
    X0, Y0, X1, Y1 = int(x0), int(y0 + 30 * S), int(x0 + 60 * S), int(y0 + 240 * S)
    for f in paths:
        im = Image.open(f); fr = [c[0].split(':')[1] if c else '-' for c in json.load(open(f.rsplit('.', 1)[0] + '.json'))]
        C = [np.array(im.crop((k * 960 + X0, Y0, k * 960 + X1, Y1)).convert('RGBA')).astype(float) for k in range(12)]
        G = []
        for c in C:
            h, s, v = M.hsv(c); G.append((h >= 44) & (h < 74) & (s > 0.12) & (v > 0.55))
        print('== %s（背弧框屏幕 x %d~%d y %d~%d）%s' % (os.path.basename(f), X0, X1, Y0, Y1, ' '.join(fr)))
        for k in range(11):
            a, b = k, k + 1
            both = G[a] & G[b]
            chg = both & (np.abs(C[a] - C[b])[..., :3].max(-1) > 40)
            print('格%2d→%2d %-6s→%-6s %s  金 %4d px  轮廓变 %3d px  同金变色 %3d px' % (a + 1, b + 1, fr[a], fr[b], '换帧' if fr[a] != fr[b] else '    ', G[b].sum(), (G[a] ^ G[b]).sum(), chg.sum()))


if __name__ == '__main__':
    if sys.argv[1] == 'atlas': atlas(sys.argv[2])
    else: film(float(sys.argv[2]), sys.argv[3:])
