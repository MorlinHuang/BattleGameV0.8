"""拖步挑帧：量 <档>/cand/ 每张候选两只拖鞋的位置和腿宽，挑一组让两只脚的实测位置都单调走的组合。
用法 pick.py <档> [强制: 格=候选 …]   结果打印每格最优候选 + 各格位移；cand/meta.json 缓存量值。
单调：前半步（1~8 格）后脚往前、前脚往后（两脚往中间收），后半步（8~16 格）反过来；第 0/16 格 = base。
站地脚每格位移就是这一格在循环里的播放位置差（build.py walk_load 按实测算 at），倒退一格 = 播放倒序，必须避开；
摆动脚倒退一格 = 脚往回抽一下，也避开。"""
import sys, os, json, glob, numpy as np
W = os.path.dirname(os.path.abspath(__file__))
from PIL import Image
from scipy import ndimage
exec(open(f'{W}/score.py').read().split('for f in sys.argv[3:]')[0].replace('name, i = sys.argv[1], int(sys.argv[2])', 'name, i = sys.argv[1], 1'))
from skimage.morphology import skeletonize
name = sys.argv[1]
force = dict(a.split('=') for a in sys.argv[2:])
N = p['N']; h = N // 2
fwd = 1 if A else -1                        # 身子朝向（脚往对方那边挪 = 往前）
def legw(a):
    r, g, b = [a[..., k].astype(int) for k in range(3)]
    skin = (r - b > 28) & (r > g) & (g > b) & (r > 150) & M
    skin = ndimage.binary_opening(skin, np.ones((3, 3)))
    dt = ndimage.distance_transform_edt(skin); sk = skeletonize(skin) & (dt > 6)
    return float(np.median(dt[sk] * 2)) if sk.any() else 0.0
def feet(a):
    got = slippers(a)
    if len(got) != 2: return None
    got.sort(key=lambda q: q[0] * fwd)            # [后脚, 前脚]
    return [got[0][0], got[1][0]]
mp = f'{W}/{name}/cand/meta.json'
meta = json.load(open(mp)) if os.path.exists(mp) else {}
base = np.array(Image.open(f'{G}/{name}/base.png').convert('RGB'))
bw = legw(base); b0 = feet(base)
for f in sorted(glob.glob(f'{W}/{name}/cand/*.png')):
    k = os.path.basename(f)[:-4]
    if k in meta: continue
    a = np.array(Image.open(f).convert('RGB').resize((1536, 1024)))
    black = not (a[3, 3, 0] > 200 and a[3, 3, 1] < 60)
    meta[k] = dict(black=black, feet=None if black else feet(a), w=0 if black else round(legw(a) / bw, 3))
json.dump(meta, open(mp, 'w'), indent=0)
cands = {i: [] for i in range(1, N)}
for k, m in meta.items():
    i = int(k[:2])
    if m['black'] or not m['feet'] or m['w'] < 0.86: continue
    if k in ('%02d_bad' % i,): continue
    cands[i].append((k, m['feet'], m['w']))
for i, k in force.items(): cands[int(i)] = [(k, meta[k]['feet'], meta[k]['w'])]
# 动态规划：状态 = 第 i 格选的候选；转移要求两脚都按本半步的方向单调（容差 tol 像素）
tol = 3
def ok(i, fa, fb):
    """第 i-1 格 fa → 第 i 格 fb：两脚位移方向对不对。返回站地脚这一步挪了多少（不对返回 None）"""
    db, df = (fb[0] - fa[0]) * fwd, (fb[1] - fa[1]) * fwd     # 往前为正
    if i <= h:   # 前半步：后脚往前（站地），前脚往后
        if db < -tol or df > tol: return None
        return db
    if db > tol or df < -tol: return None
    return df
seq = [[('base', b0, 1.0)]] + [cands[i] for i in range(1, N)] + [[('base', b0, 1.0)]]
best = [{0: (0.0, None)}]
for i in range(1, N + 1):
    cur = {}
    for j, (k, fb, w) in enumerate(seq[i]):
        for jj, (sc, _) in best[-1].items():
            st = ok(i, seq[i - 1][jj][1], fb)
            if st is None: continue
            # 打分：站地脚步子越匀越好（惩罚过小的一步），腿宽贴 1
            s = sc + min(st, 12) - 20 * abs(1 - w)
            if j not in cur or s > cur[j][0]: cur[j] = (s, jj)
    best.append(cur)
    if not cur:
        print(f'第 {i} 格接不上：前一格候选', [c[0] for c in seq[i - 1]], '本格', [(c[0], [round(v) for v in c[1]]) for c in seq[i]]); sys.exit(1)
j = max(best[-1], key=lambda q: best[-1][q][0]); path = []
for i in range(N, 0, -1):
    path.append(j); j = best[i][j][1]
path = path[::-1]
picks = [seq[i][path[i - 1]] for i in range(1, N)]
print('base', [round(v) for v in b0])
for i, (k, f, w) in enumerate(picks, 1):
    print('%2d %-7s 后 %4d 前 %4d 宽 %.2f' % (i, k, f[0], f[1], w))
print('PICKS', ' '.join(k for k, _, _ in picks))
