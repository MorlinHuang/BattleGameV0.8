"""出手方向自检（美术打磨自检第 4 节「物理一致性复核」的口径，公式抄 shots/polish/精1_物理_工具/judge.py 的 clear_par）。
在 chashouji 下跑：python3 v14/trio/bestie/tools/dircheck.py G8 [G21 ...]
每人读 trio_bestie.js 的 cfg（node 导出），找 atk.seq 里标 'fire' 的帧 F 和它前一帧 P：
  · 出手点 = hold[F]（没有就 atk.from / wrist），换到屏幕：at + (点 − anchor) × s
  · 手的运动方向 = hold[P] → hold[F] 的位移（投掷实物的参照方向）；cfg 写了 atk.dir[F] 就用它（光束 / 伸长肢体 = 手臂指向）
  · 直线角 = 出手点 → 目标（闺蜜打男主 (616.4, 837)）
  · 抛物：初速沿手的方向、重力竖直，能不能落到目标（目标在射线上方 = 到不了），后排还要越过女主头顶那三列
  · 所需最小仰角 = 能到且越过头顶的最小角（+8° 余量就是审查表里的"所需角度"）
屏幕角：0° = 水平向右，正 = 往上。"""
import json, math, subprocess, sys

T = (616.4, 837); GIRL = (281, 858, 24.8)
js = r'''const vm=require('vm'),fs=require('fs');const c={};vm.createContext(c);
vm.runInContext('var ROPE={};'+fs.readFileSync('web/trio_bestie.js','utf8')+';this.T=TRIO_BESTIE;',c);console.log(JSON.stringify(c.T.cast))'''
C = json.loads(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout)
ang = lambda v: -math.degrees(math.atan2(v[1], v[0]))


def clear_par(p0, th, rear, pad=30):
    vx, vy = math.cos(math.radians(th)), -math.sin(math.radians(th)); dx, dy = T[0] - p0[0], T[1] - p0[1]
    if vx * dx <= 0: return False, False
    t1 = dx / vx; a = (dy - vy * t1) / (t1 * t1)
    if a <= 0: return False, False
    f = GIRL; Y = f[1] - f[2] - 40 - pad; ok = True
    for x in (f[0] - f[2] - pad, f[0], f[0] + f[2] + pad):
        t = (x - p0[0]) / vx
        if 0 < t < t1 and p0[1] + vy * t + a * t * t > Y: ok = False
    return True, (ok if rear else True)


for g in sys.argv[1:]:
    v = C[g]; a = v['atk']; seq = a['seq']; at, an = v['at'], v['anchor']; s = at[2]; rear = v.get('depth', 1) < 1
    FI = next(i for i, q in enumerate(seq) if len(q) > 2 and q[2] == 'fire')
    F = seq[FI][0] if isinstance(seq[FI][0], str) else seq[FI][0][0]; P = seq[FI - 1][0] if FI else None
    H = a.get('hold') or {}
    q = H.get(F) or a.get('from') or a.get('wrist')
    scr = lambda p: (at[0] + (p[0] - an[0]) * s, at[1] + (p[1] - an[1]) * s)
    p0 = scr(q); st = ang((T[0] - p0[0], T[1] - p0[1]))
    D = (a.get('dir') or {}).get(F)
    if D is None and P in H and F in H: D = ang((H[F][0] - H[P][0], H[F][1] - H[P][1])); src = f'手位移 {P}→{F}'
    else: src = 'cfg atk.dir'
    line = f'{g} {a["kind"]:6s} 出手帧 {F}（前一帧 {P}）出手点 格内 {q} → 屏幕 ({p0[0]:.0f}, {p0[1]:.0f})  直线角 {st:+.1f}°'
    if D is not None:
        line += f'  出手方向 {D:+.1f}°（{src}）'
        if a['kind'] == 'throw':
            r, c = clear_par(p0, D, rear)
            mn = next((th for th in [x / 2 for x in range(-170, 171)] if all(clear_par(p0, th, rear))), None)
            line += f'  能到 {r} 越过头顶 {c}  最小可行仰角 {mn}°（+8° = {None if mn is None else mn + 8}°）'
    print(line)
