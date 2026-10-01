# 头盔模板（idle 底图的头盔壳）多尺度找 → 头相对 idle 的大小
import sys, numpy as np
sys.path.insert(0,'/workspace/art/chashouji/v14/trio/tools'); sys.path.insert(0,'/workspace/art/chashouji/v14')
from frames import gray, find, resize
from PIL import Image
def ld(p):
    a=np.array(Image.open(p).convert('RGBA'))
    if p.endswith('base.png'):
        g=(a[...,1]>200)&(a[...,0]<80)&(a[...,2]<80); a[...,3]=np.where(g,0,255)
    return Image.fromarray(a)
tpl=gray(ld('raw/p6_idle2_base.png').crop((500,228,605,300)))
for p in sys.argv[1:]:
    im=ld(p).crop((150,100,850,600))
    best=max(((s,find(gray(resize(im,s)),tpl)) for s in np.arange(0.75,1.25,0.01)),key=lambda q:q[1][2] if q[1] else -1)
    print(p, 'head %.3f'%(1/best[0]), 'score %.2f'%best[1][2], 'at', round(best[1][1]/best[0]+150), round(best[1][0]/best[0]+100))
