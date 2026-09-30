"""把 web/trio_bestie.js 里「我负责的那几个人」的块暂存进 git（别的角色 —— 引擎正在改的 G11 —— 保持 HEAD 版本，不跟着提交）。
用法：python3 stage_bestie.py G21 G22 ...（在 chashouji 目录下跑）"""
import subprocess, sys, re
ids = sys.argv[1:]
head = subprocess.run(['git', 'show', 'HEAD:chashouji/web/trio_bestie.js'], capture_output=True, text=True, check=True).stdout
cur = open('web/trio_bestie.js').read()
def block(s, k):
    a = s.find(f'\n    {k}: {{'); 
    if a < 0: return None
    b = s.index('\n    },\n', a) + len('\n    },\n')
    return a, b
MARK = '\n    /* ---- 单张立绘'
for k in ids:
    nb = block(cur, k); new = cur[nb[0]:nb[1]]
    ob = block(head, k)
    if ob: head = head[:ob[0]] + head[ob[1]:]
    i = head.index(MARK); head = head[:i] + new + head[i:]
open('/tmp/trio_bestie_stage.js', 'w').write(head)
subprocess.run(['node', '--check', '/tmp/trio_bestie_stage.js'], check=True)
h = subprocess.run(['git', 'hash-object', '-w', '/tmp/trio_bestie_stage.js'], capture_output=True, text=True, check=True).stdout.strip()
subprocess.run(['git', 'update-index', '--cacheinfo', f'100644,{h},chashouji/web/trio_bestie.js'], check=True)
print('staged', ids)
