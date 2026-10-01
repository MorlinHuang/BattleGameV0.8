"""精引2 出手方向读数（定稿口径，docs/三人组角色规范.md「出手方向」、docs/美术打磨自检.md「补帧：出手方向」）。
输入：改后胶片的 json（p2ab.py 存的 {'after': trioFaces}，每格 path = trio.js paths() 诊断）+ trio_tune.js 的 dir（node 导出）。
每人：
  首段差 = 引擎画出来的路线起始切线 a0 与参照方向（dir，复核 4.2 / 4.3「参照方向」换成仰角，加上出手那一刻人的倾角）之差 —— 判据 ≤ 10°
  拐角   = 起始切线到末段切线（光、拳影该是 0：直线）
  转肩   = 伸缩臂对准转了多少（B12 G29）
  压主角 = 这条路压在自己主角身上的长度 px（改后 / 同一落点直线）
用法：python3 readings2.py <dirs.json> <film json ...>"""
import json, math, sys
from collections import defaultdict

def ad(a, b): return (a - b + 180) % 360 - 180
def scr(el, face):   # 仰角 → 屏幕角（y 朝下）
    e = math.radians(el); return math.degrees(math.atan2(-math.sin(e), face * math.cos(e)))

DIRS = json.load(open(sys.argv[1]))
rows = defaultdict(list)
for f in sys.argv[2:]:
    J = json.load(open(f))
    for cell in J.get('after', J.get('faces', [])):
        for pid, q in cell.get('path') or []: rows[pid].append(q)
res = {}
for pid, R in rows.items():
    face = 1 if pid[0] == 'G' else -1
    k = R[0]['k']
    if k == 'punch':
        res[pid] = dict(k=k, diff=max(abs(ad(q['a0'], q['d'])) for q in R), turn=0.0, rot=[q.get('rot') for q in R], own=max(q['own'] or 0 for q in R), own0=max(q['own0'] or 0 for q in R), n=len(R)); continue
    ref = list(DIRS.get(pid, {}).values())
    if not ref: res[pid] = dict(k=k, diff=None, n=len(R)); continue
    refs = [scr(e, face) for e in ref]
    # 有 d 的样本：d 已经是屏幕角（含倾角）；没有的（弹道到不了、退回老弧）按参照仰角
    diffs = [min(abs(ad(q['a0'], q['d'] if q.get('d') is not None else r)) for r in refs) for q in R]
    turn = max(abs(ad(q['a1'], q['a0'])) for q in R)
    res[pid] = dict(k=k, diff=max(diffs), turn=turn, own=max(q['own'] or 0 for q in R), own0=max(q['own0'] or 0 for q in R), n=len(R),
                    way=any(q.get('d') is not None for q in R) and k not in ('beam', 'ghost'))
json.dump(res, open('/tmp/p2/readings2.json', 'w'), ensure_ascii=False, indent=0)
for pid in sorted(res, key=lambda s: (s[0], int(s[1:]))):
    r = res[pid]; d = '—' if r.get('diff') is None else f"{r['diff']:.1f}°"
    print(pid, r['k'], '首段差', d, '拐角', f"{r.get('turn', 0):.1f}°", '压主角', r.get('own'), '/', r.get('own0'), '转肩' if r.get('rot') else '', r.get('rot') or '', 'n', r['n'])
