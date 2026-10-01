# B9：把生成图按电驴（fixed：后半车身+后轮）配回底图：python3 norm.py <frame> <gen.png> <out.png>
import sys, numpy as np
sys.path.insert(0,'/workspace/art/chashouji/v14/trio/tools')
sys.path.insert(0,'/workspace/art/chashouji/v14')
from frames import gray, find, resize
from PIL import Image
R='/workspace/art/chashouji/v14/trio/buddy/B9_rider/raw/'
name,gp,op=sys.argv[1:4]
base=Image.open(R+f'p6_{name}_base.png').convert('RGBA')
b=np.array(base); g0=(b[...,1]>200)&(b[...,0]<80)&(b[...,2]<80); b[...,3]=np.where(g0,0,255); base=Image.fromarray(b)
a=b[...,3]; ys,xs=np.nonzero(a>128); yb=ys.max(); xr=xs.max()
box=(xr-260,yb-250,xr+5,yb+5)          # 后半车身 + 后轮
tpl=gray(base.crop(box))
g=Image.open(gp).convert('RGBA')
if np.array(g)[...,3].min()>250:
    from crewart import cut
    rgb,al=cut(gp,'green',(40,150)); g=Image.fromarray(np.dstack([rgb,al*255]).clip(0,255).astype(np.uint8),'RGBA')
best=None
for s in np.arange(0.78,0.86,0.004):
    r=find(gray(resize(g,s)),tpl)
    if r and (best is None or r[2]>best[0]): best=(r[2],s,r)
sc,s,r=best
gx,gy=box[0]-r[1],box[1]-r[0]
print(f'{name}: scale {s:.3f} score {sc:.3f} offset {gx:.1f},{gy:.1f}')
out=g.transform((1024,1024),Image.AFFINE,(1/s,0,-gx/s,0,1/s,-gy/s),Image.BICUBIC)
out.save(op)
