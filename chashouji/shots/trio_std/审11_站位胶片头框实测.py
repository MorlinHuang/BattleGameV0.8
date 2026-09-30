"""胶片实测：后面那个人（后排 / 上方）每一格头框露出多少。
按 film json 的帧名取图集那一格，头框用 combo_scan 的 head_out/find_head（和矩阵同一个头框），按 at/anchor/s 放到屏幕上，
在 ±14 px 里做截断平方差匹配（吸收呼吸、前倾、拉锯），再逐像素比：头框内自己的像素（alpha>0.9、内缩 2px）里，
和胶片颜色差 > 0.25（RGB 均值，0~1）的算"被盖住"。用法：headvis.py <胶片.jpg> <gift> <编号> [<编号> ...]"""
import sys, json, importlib.util, numpy as np
from PIL import Image
from scipy import ndimage
sys_argv = sys.argv[:]; sys.argv = ['x']
spec = importlib.util.spec_from_file_location('cs', '/workspace/art/chashouji/v14/trio/tools/combo_scan.py')
cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)
film, side, who = sys_argv[1], sys_argv[2], sys_argv[3:]
D = cs.load_data()
im = np.array(Image.open(film).convert('RGB')).astype(np.float32) / 255
n = 12; W = im.shape[1] // n
log = json.load(open(film.rsplit('.', 1)[0] + '.json'))
for rid in who:
    c = D[side]['cast'][rid]; sh = c['sheet']; name = sh['src'].split('/')[-1].rsplit('.', 1)[0]
    A = np.array(Image.open('/workspace/art/chashouji/web/' + sh['src']).convert('RGBA'))
    cw, ch = sh['cell']; cols = sh['cols']
    cell = lambda fn: A[(sh['names'].index(fn) // cols) * ch:(sh['names'].index(fn) // cols + 1) * ch, (sh['names'].index(fn) % cols) * cw:(sh['names'].index(fn) % cols + 1) * cw]
    hr = cs.head_out(name); hb0, refc = hr[0], cell(hr[1])
    ax, ay = c['anchor']; X, Y, s = c['at']
    res = []
    for i in range(n):
        hit = [e.split(':')[1] for e in log[i] if e.split(':')[0] == rid]
        if not hit or hit[0] not in sh['names']: res.append(None); continue
        cc = cell(hit[0]); hb = cs.find_head(cc, refc, hb0)
        x0, y0, x1, y1 = [int(round(v)) for v in hb]
        x0, y0 = max(0, x0), max(0, y0)
        patch = Image.fromarray(cc[y0:y1, x0:x1]); pw, ph = round(patch.width * s), round(patch.height * s)
        p = np.array(patch.resize((pw, ph), Image.LANCZOS)).astype(np.float32) / 255
        m = ndimage.binary_erosion(p[..., 3] > 0.9, iterations=2)
        if m.sum() < 50: res.append(None); continue
        sx, sy = X + (x0 - ax) * s, Y + (y0 - ay) * s
        tile = im[:, i * W:(i + 1) * W]
        best = None
        for dy in range(-14, 15):
            for dx in range(-14, 15):
                yy, xx = int(round(sy)) + dy, int(round(sx)) + dx
                if yy < 0 or xx < 0 or yy + ph > tile.shape[0] or xx + pw > tile.shape[1]: continue
                d = np.abs(tile[yy:yy + ph, xx:xx + pw] - p[..., :3]).mean(-1)
                e = np.minimum(d, 0.25)[m].mean()
                if best is None or e < best[0]: best = (e, dx, dy, d)
        e, dx, dy, d = best
        occ = int(((d > 0.25) & m).sum()); res.append((hit[0], occ, int(m.sum()), dx, dy))
    vis = [r for r in res if r]
    worst = max(vis, key=lambda r: r[1] / r[2]) if vis else None
    print(f'{rid}（头框 {vis[0][2] if vis else 0} px 量级）: ' + ' '.join(f'{i+1}:{r[0]}={r[1]}' for i, r in enumerate(res) if r) +
          (f'  → 头框最差 {worst[1]}/{worst[2]} px（{worst[1]/worst[2]:.1%}，帧 {worst[0]}）' if worst else '  不在场'))
