"""精引2 出手方向读数（docs/三人组角色规范.md「出手方向」）。
输入：桌面 /tmp/p2read.py 按组跑出来的 json（每格 trioFaces[].path，trio.js paths() 诊断）。
每人取出手那几格的路线，算：
  · 出口差  = 路线起始切线 a0 与出手方向 d（atk.dir 换到屏幕）之差；|a60 − d| = 起点到沿路 60 px 那一点的弦与 d 之差（胶片上看得到的那一段）
  · 拐角    = 起始切线到末段切线一共拐了多少（直线 0）
  · 弦差    = 出口 → 落点的直线和 d 差多少 = 不加 dir 时（改前）出口处的折角
  · 反重力  = 丢出去的东西（throw / puff）路线的加速度朝上（p0 − 2c + p2 的 y < 0）：手平着、落点在上面，只能往上拐
  · 压主角  = 这条路 / 直线压在自己主角身上的长度 px（P9）
用法：python3 readings.py <json 目录> > 读数.md"""
import json, glob, math, os, sys
from collections import defaultdict

def ad(a, b):
    return (a - b + 180) % 360 - 180

rows = defaultdict(list)
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.json'))):
    J = json.load(open(f))
    for cell in J['faces']:
        for pid, q in cell.get('path') or []:
            rows[pid].append(q)

def el(a, face):   # 屏幕角（y 朝下）→ 朝对手那边的仰角
    return round(-a if face > 0 else -(180 - a) if a > 0 else -(-180 - a), 1)

print('| 人 | 写法 | 出手方向 d（仰角） | 起始切线差 | 前 60 px 差 | 拐角 | 弦差（改前折角） | 反重力 | 压主角 改后 / 直线 px | 样本 |')
print('|---|---|---|---|---|---|---|---|---|---|')
for pid in sorted(rows, key=lambda s: (s[0], int(s[1:]))):
    R = [q for q in rows[pid] if q.get('d') is not None]
    allq = rows[pid]
    if not allq: continue
    k = allq[0]['k']
    face = 1 if pid[0] == 'G' else -1
    if not R:
        print(f'| {pid} | {k} | — | | | | | | {max(q.get("own") or 0 for q in allq)} / {max(q.get("own0") or 0 for q in allq)} | {len(allq)} |'); continue
    d0 = max(abs(ad(q['a0'], q['d'])) for q in R)
    d60 = max(abs(ad(q['a60'], q['d'])) for q in R if q.get('a60') is not None) if any(q.get('a60') is not None for q in R) else None
    turn = max(abs(ad(q['a1'], q['a0'])) for q in R if 'a1' in q) if any('a1' in q for q in R) else None
    chord = max(abs(ad(q['ch'], q['d'])) for q in R if 'ch' in q) if any('ch' in q for q in R) else None
    anti = any(q['k'] not in ('beam', 'whip', 'ghost', 'punch') and (q['p0'][1] - 2 * q['c'][1] + q['p2'][1]) < -2 for q in R)
    own = max(q.get('own') or 0 for q in R); own0 = max(q.get('own0') or 0 for q in R)
    f = lambda v: '—' if v is None else f'{v:.1f}°'
    print(f'| {pid} | {k} | {el(R[0]["d"], face)}° | {f(d0)} | {f(d60)} | {f(turn)} | {f(chord)} | {"是" if anti else ""} | {own} / {own0} | {len(R)} |')

# ---- 补帧名单：按写法判"贝塞尔救不了 / 不合物理"（docs/美术打磨自检.md「补帧：出手方向」）----
#   光束（beam）、残影（ghost）、伸缩臂（punch）：光、打出去的拳影、伸长的手都该是直的 —— 拐角 > 10° 就要一张对准目标的出手帧，所需角度 = 弦的仰角
#   丢出去的东西（throw / puff）、绸鞭（whip）：受重力，往下拐合理；要往上拐（反重力）就要一张往上抛的帧，所需角度 ≥ 弦仰角 + 10°
STRAIGHT = ('beam', 'ghost', 'punch')
DIRS = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}   # web/trio_tune.js 的 dir（帧名），node 导出
print('\n### 补帧名单（自动判）\n')
print('| 人 | 写法 | 帧 | 现在手的仰角 | 所需仰角 | 落点（屏幕，样本中位） | 理由 |')
print('|---|---|---|---|---|---|---|')
for pid in sorted(rows, key=lambda s: (s[0], int(s[1:]))):
    R = [q for q in rows[pid] if q.get('d') is not None and 'a1' in q]
    if not R: continue
    face = 1 if pid[0] == 'G' else -1
    q = sorted(R, key=lambda q: q['ch'])[len(R) // 2]
    k = q['k']; ech = el(q['ch'], face); ed = el(q['d'], face); turn = abs(ad(q['a1'], q['a0']))
    acc_up = (q['p0'][1] - 2 * q['c'][1] + q['p2'][1]) < -2
    d60 = max(abs(ad(r['a60'], r['d'])) for r in R if r.get('a60') is not None) if any(r.get('a60') is not None for r in R) else 0
    whys = []
    if k in STRAIGHT and turn > 10: whys.append(f'{k} 应是直的，现在拐 {turn:.0f}°')
    if k not in STRAIGHT and acc_up: whys.append(f'要往上拐 {turn:.0f}°（反重力）')
    if d60 > 10: whys.append(f'出手后 60 px 内就偏离手 {d60:.0f}°（看得出拐）')
    if not whys: continue
    why = '；'.join(whys)
    need = f'{ech:.0f}°' if k in STRAIGHT else f'{ech + 10:.0f}°（比落点方向高 10°，抛物线往下落）'
    fr = '、'.join(DIRS.get(pid, {}).keys()) or '出手帧'
    print(f'| {pid} | {k} | {fr} | {ed:.0f}° | {need} | {q["p2"]} | {why} |')
