"""把工作区 trio_bestie.js 里我这几个人的块，插进 HEAD 版本同位置（只暂存自己的改动）。用法：python3 stage_mine.py G8 [G9 ...]"""
import subprocess, sys, re
P='chashouji/web/trio_bestie.js'
head=subprocess.run(['git','show','HEAD:'+P],capture_output=True,text=True,cwd='/workspace/art').stdout
work=open('/workspace/art/'+P).read()
def block(src,id):
    m=re.search(r'^    %s: \{.*?^    \},\n'%id, src, re.S|re.M); return m
for id in sys.argv[1:]:
    b=block(work,id).group(0)
    h=block(head,id)
    if h: head=head[:h.start()]+b+head[h.end():]; continue
    # 新人：放在工作区里它前一个块之后（前一个块在 HEAD 里也要有）
    w=block(work,id); prev=list(re.finditer(r'^    (G\d+): \{', work[:w.start()], re.M))[-1].group(1)
    hp=block(head,prev); assert hp, prev
    head=head[:hp.end()]+b+head[hp.end():]
open('/tmp/_stage.js','w').write(head)
sha=subprocess.run(['git','hash-object','-w','/tmp/_stage.js'],capture_output=True,text=True,cwd='/workspace/art').stdout.strip()
subprocess.run(['git','update-index','--cacheinfo','100644,%s,%s'%(sha,P)],check=True,cwd='/workspace/art')
print('staged',sys.argv[1:],sha)
