"""用引擎 combo_scan.py（工作区版，含第 9 条）的函数，逐组算三人+主角读数，不写矩阵文件"""
import sys, importlib.util
sys.argv0 = sys.argv[1:]; sys.argv = ['x']
spec = importlib.util.spec_from_file_location('cs', '/workspace/art/chashouji/v14/trio/tools/combo_scan.py')
cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)
import os
cs.WEB = os.environ.get('CS_WEB', cs.WEB)
D = cs.load_data()
combos = {'bestie': [a for a in sys.argv0 if a.startswith('G')], 'buddy': [a for a in sys.argv0 if a.startswith('B')]}
          
for side, cl in combos.items():
    ids, ppl = cs.build(side, D)
    for c in cl:
        g, t, f = c.split('.')
        P = lambda r: ppl[r]
        out = [c]
        # 后排：对地板、对主角
        jf = cs.judge(P(g), (0,0), P(f), (0,0)); jcs = {c_: cs.judge(P(g), (0,0), ppl[c_], (0,0)) for c_ in cs.CP_IDS}
        tg = cs.total(P(g), (0,0), [(P(f),(0,0))] + [(ppl[c_],(0,0)) for c_ in cs.CP_IDS])
        out.append(f'  后排 {g}：×地板 {f} {jf[0]:.1%}({jf[1]}) 头{jf[2]} 认{jf[3]}' + ''.join(f'；×{k} 剪影{j[0]:.1%}({j[1]}) 头{j[2]} 认{j[3]} 最差项可见{j[4]:.1%}({j[5]})' for k, j in jcs.items()) + f'；合计 {tg[0]:.1%}({tg[1]}) 上限{P(g).lim:.0%}')
        jt = [(o, cs.judge(P(t), (0,0), P(o), (0,0))) for o in (g, f)] + [(c_, cs.judge(P(t), (0,0), ppl[c_], (0,0))) for c_ in cs.CP_IDS]
        tt = cs.total(P(t), (0,0), [(P(g),(0,0)), (P(f),(0,0))] + [(ppl[c_],(0,0)) for c_ in cs.CP_IDS])
        out.append(f'  上方 {t}：' + '；'.join(f'×{o} {j[0]:.1%}({j[1]}) 头{j[2]} 认{j[3]}' for o, j in jt) + f'；合计 {tt[0]:.1%}({tt[1]})')
        print('\n'.join(out), flush=True)
