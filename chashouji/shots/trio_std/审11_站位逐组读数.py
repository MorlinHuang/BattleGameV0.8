"""用引擎 combo_scan.py（工作区版，含第 9 条）的函数，逐组算三人+主角读数，不写矩阵文件"""
import sys, importlib.util
sys.argv = ['x']
spec = importlib.util.spec_from_file_location('cs', '/workspace/art/chashouji/v14/trio/tools/combo_scan.py')
cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)
import os
cs.WEB = os.environ.get('CS_WEB', cs.WEB)
D = cs.load_data()
combos = {'bestie': ['G4.G16.G28','G5.G18.G28','G6.G14.G25','G8.G18.G28','G10.G16.G25','G9.G20.G28','G1.G19.G28','G3.G16.G27','G2.G15.G25'],
          'buddy':  ['B5.B19.B21','B8.B15.B30','B7.B16.B25','B6.B14.B21','B9.B19.B25','B1.B15.B22','B4.B19.B30','B10.B18.B29','B2.B20.B28']}
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
