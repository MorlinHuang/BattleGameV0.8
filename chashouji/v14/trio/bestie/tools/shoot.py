"""拍闺蜜三人组胶片直到帧号表里出现要的几段（进场 / 出手时机随 STAGGER 和 cd 随机，一次不一定拍全）。
用法：python3 shoot.py <名> "<URL 参数>" <id> <必须出现的帧,逗号> [最少几格 idle] ；胶片 + json 拉到 shots/trio_bestie/"""
import json, subprocess, sys, os
name, q, who, need = sys.argv[1:5]
min_idle = int(sys.argv[5]) if len(sys.argv) > 5 else 0
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../shots/trio_bestie')
for k in range(8):
    r = subprocess.run(['timeout', '150', 'ssh', '-o', 'ConnectTimeout=20', 'kf-deployment', f'python3 /tmp/film.py "v=s{k}{name}&{q}" /tmp/{name}.png'], capture_output=True, text=True)
    if r.returncode: continue
    subprocess.run(['timeout', '90', 'scp', '-o', 'ConnectTimeout=20', '-q', f'kf-deployment:/tmp/{name}.*', OUT])
    fr = [[e.split(':')[1] for e in c if e.split(':')[0] == who] for c in json.load(open(f'{OUT}/{name}.json'))]
    seq = [f[0] if f else '-' for f in fr]
    ok = all(n in seq for n in need.split(',')) and seq.count('idle') >= min_idle
    print(name, 'try', k, ' '.join(seq), r.stdout.splitlines()[0])
    if ok: break
