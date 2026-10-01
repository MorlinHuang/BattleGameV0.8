# python3 norm.py <name> <gen.png> <out.png> [lo hi]
import sys, numpy as np
sys.path.insert(0,'/workspace/art/chashouji/v14/trio/tools')
from frames import gray, find, resize
from PIL import Image
R='/workspace/art/chashouji/v14/trio/buddy/B10_mahjong/raw/'
name,gp,op=sys.argv[1:4]; lo,hi=(float(sys.argv[4]),float(sys.argv[5])) if len(sys.argv)>5 else (0.75,0.9)
waist={'swing':583,'thru':595,'idle2':519}[name]
body=np.load(f'/tmp/b10/{name}_body.npy')
bimg=np.array(Image.open(R+f'p6_{name}_base.png').convert('RGB'))
base=Image.fromarray(np.dstack([bimg,np.where(body,255,0).astype(np.uint8)]),'RGBA')
ys,xs=np.nonzero(body[waist+70:]); y0=waist+70; yb=ys.max()+y0
box=(xs.min()-4,y0,xs.max()+5,yb+5)
tpl=gray(base.crop(box))
g=Image.open(gp).convert('RGBA')
best=None
for s in np.arange(lo,hi,0.005):
    r=find(gray(resize(g,s)),tpl)
    if r and (best is None or r[2]>best[0]): best=(r[2],s,r)
sc,s,r=best
gx,gy=box[0]-r[1],box[1]-r[0]
print(f'{name}: scale {s:.3f} score {sc:.3f} offset {gx:.1f},{gy:.1f} box {box}')
out=g.transform((1024,1024),Image.AFFINE,(1/s,0,-gx/s,0,1/s,-gy/s),Image.BICUBIC)
out.save(op)
