"""暂存 web/trio_bestie.js，但把「别人正在改的角色」（引擎在改 G11）换回 HEAD 的版本 —— 只提交我负责的改动，不把别人的半成品带进提交。
用法（在 chashouji 目录下跑）：python3 v14/trio/bestie/tools/stage_bestie.py G11 [其他不归我的编号 ...]
做法：取工作区整个文件，把列出的那几个块替换成 HEAD 里的同名块（HEAD 里没有的就从暂存版里删掉），node --check 后写进 index。
（第一版反过来"从 HEAD 出发插我的块"，删旧块时吃掉了上一行的换行，旧 G22 粘到上一行没被删掉，留下了重复键 —— 所以改成从工作区出发。）"""
import subprocess, sys
others = sys.argv[1:]
head = subprocess.run(['git', 'show', 'HEAD:chashouji/web/trio_bestie.js'], capture_output=True, text=True, check=True).stdout
cur = open('web/trio_bestie.js').read()


def block(s, k):
    """cast 里编号 k 那一块：从 '    k: {' 的行首到 '    },' 那一行的换行为止"""
    a = s.find(f'\n    {k}: {{')
    if a < 0: return None
    b = s.index('\n    },\n', a) + len('\n    },\n')
    return a + 1, b


for k in others:
    cb, hb = block(cur, k), block(head, k)
    if not cb: continue
    cur = cur[:cb[0]] + (head[hb[0]:hb[1]] if hb else '') + cur[cb[1]:]
ids = [l.split(':')[0].strip() for l in cur.splitlines() if l.startswith('    G') and ': {' in l]
assert len(ids) == len(set(ids)), f'重复的编号：{ids}'
open('/tmp/trio_bestie_stage.js', 'w').write(cur)
subprocess.run(['node', '--check', '/tmp/trio_bestie_stage.js'], check=True)
h = subprocess.run(['git', 'hash-object', '-w', '/tmp/trio_bestie_stage.js'], capture_output=True, text=True, check=True).stdout.strip()
subprocess.run(['git', 'update-index', '--cacheinfo', f'100644,{h},chashouji/web/trio_bestie.js'], check=True)
print('staged；换回 HEAD 的：', others, '；cast 里现在有：', ids)
