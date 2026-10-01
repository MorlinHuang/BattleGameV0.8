# python3 paste.py <name> <gen.png> [s0 s1]  → raw/p6_<name>.png（RGBA；蒙版外 = 底图原像素）
import sys, os, numpy as np
sys.path.insert(0,'/workspace/art/chashouji/v14/trio/tools'); sys.path.insert(0,'/workspace/art/chashouji/v14')
from frames import gray, find, resize
from crewart import cut
from scipy import ndimage
from PIL import Image
R='/workspace/art/chashouji/v14/trio/buddy/B24_bboy/raw/'
n,gp=sys.argv[1],sys.argv[2]
s0,s1=(float(sys.argv[3]),float(sys.argv[4])) if len(sys.argv)>4 else (0.78,0.86)
rgb,al=cut(os.environ.get('BASE',R+f'p6d_{n}_base.png'),'green',(40,150))
base=Image.fromarray(np.dstack([rgb,al*255]).clip(0,255).astype(np.uint8),'RGBA')
keep=np.array(Image.open(os.environ.get('MASK',R+f'p6d_{n}_mask.png')))[...,3]>128
# 模板：蒙版外（腿脚）的人
legs=(al>0.5)&ndimage.binary_erosion(keep,iterations=12)
ys,xs=np.nonzero(legs); box=(xs.min()-4,ys.min()-4,xs.max()+5,ys.max()+5)
tb=np.array(base).copy(); tb[...,3]=np.where(ndimage.binary_erosion(keep,iterations=12),tb[...,3],0)
tpl=gray(Image.fromarray(tb).crop(box))
g=Image.open(gp).convert('RGBA')
best=None
for s in np.arange(s0,s1,0.003):
    r=find(gray(resize(g,s)),tpl)
    if r and (best is None or r[2]>best[0]): best=(r[2],s,r)
sc,s,r=best; gx,gy=box[0]-r[1],box[1]-r[0]
print(f'{n}: scale {s:.3f} score {sc:.3f} offset {gx:.1f},{gy:.1f}')
ga=np.array(g.transform((1024,1024),Image.AFFINE,(1/s,0,-gx/s,0,1/s,-gy/s),Image.BICUBIC)).astype(np.float32)
F=8
import os
if os.environ.get('SHRINK'):
    f=float(os.environ['SHRINK']); px,py=map(float,os.environ['PIVOT'].split(','))
    gi=Image.fromarray(ga.clip(0,255).astype(np.uint8),'RGBA').transform((1024,1024),Image.AFFINE,(1/f,0,px-px/f,0,1/f,py-py/f),Image.BICUBIC)
    ga=np.array(gi).astype(np.float32); print('shrink',f,'pivot',px,py)
w=np.clip(ndimage.distance_transform_edt(~keep)/F,0,1)
band=(w>0)&(w<1)
w=np.where(band&(ga[...,3]<128),0,w)
ba=np.array(base).astype(np.float32)
pb=np.dstack([ba[...,:3]*ba[...,3:]/255,ba[...,3:]]); pg=np.dstack([ga[...,:3]*ga[...,3:]/255,ga[...,3:]])
o=pg*w[...,None]+pb*(1-w[...,None])
out=np.dstack([o[...,:3]*255/np.maximum(o[...,3:],1e-3),o[...,3:]]).clip(0,255).astype(np.uint8)
# 小碎块清掉
lab,k=ndimage.label(out[...,3]>10); sz=ndimage.sum(np.ones(lab.shape),lab,range(1,k+1))
out[np.isin(lab,np.nonzero(sz<60)[0]+1)]=0
op=sys.argv[5] if len(sys.argv)>5 else R+f'p6d_{n}.png'
Image.fromarray(out,'RGBA').save(op)
v=Image.new('RGBA',(1024,1024),(200,200,200,255)); v.alpha_composite(Image.fromarray(out,'RGBA')); v.convert('RGB').crop((150,250,900,900)).save(f'/tmp/b24/d_{n}_pasted.png')
