"""上方站 / 跪在支撑面上的人：脚底往上 H px 的"落脚区"（每帧剪影里 y ≥ 最低点 − H 的那一截：鞋、小腿、跪地的膝）
× 后排每个人的全部在场帧并集（含蓄力手持道具、挂件）：重叠像素。用引擎 combo_scan 的人物模型（CS_WEB 指定数据）。
用法：CS_WEB=<web 目录> footscan.py <H> <上方编号…>"""
import sys, os, importlib.util, numpy as np
H = int(sys.argv[1]); who = sys.argv[2:]; sys.argv = ['x']
spec = importlib.util.spec_from_file_location('cs', '/workspace/art/chashouji/v14/trio/tools/combo_scan.py')
cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)
cs.WEB = os.environ.get('CS_WEB', cs.WEB)
D = cs.load_data()
for side in ('buddy', 'bestie'):
    ids, ppl = cs.build(side, D)
    for t in [w for w in who if w in ppl]:
        T = ppl[t]; rows = []
        for f in T.frames:
            b = f.body; ys = np.nonzero(b.m.any(1))[0]; low = ys.max()
            m = b.m.copy(); m[:max(0, low - H + 1)] = False
            z = cs.Blob(m, b.x, b.y)
            for g in ids['ground']:
                B = ppl[g]
                for bf in B.frames:
                    o = cs.ov(z, (0, 0), bf.body, (0, 0))
                    if o: rows.append((o, g, bf.name, f.name, z.area()))
        best = {}
        for o, g, bn, fn, za in rows:
            if o > best.get(g, (0,))[0]: best[g] = (o, bn, fn, za)
        print(t, f'落脚区 {H}px', '；'.join(f'{g} {v[0]}px（{g}:{v[1]} × {t}:{v[2]}，区 {v[3]}px）' for g, v in sorted(best.items(), key=lambda kv: -kv[1][0])) or '0')
