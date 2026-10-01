# 把生成图按靴子（fixed 部位）配回底图的大小/位置：python3 norm.py <name> <gen.png> <out.png>
import sys, numpy as np
sys.path.insert(0,'/workspace/art/chashouji/v14/trio/tools')
from frames import gray, find, resize
from PIL import Image
R='/workspace/art/chashouji/v14/trio/buddy/B8_logger/raw/'
cfg={'swing':((555,0),(17,36,451,712),(479,307)),'thru':((0,768),(20,56,537,619),(300,401)),'idle2':((0,0),(130,66,416,710),(369,320))}
name,gp,op=sys.argv[1:4]
(qx,qy),bb,pos=cfg[name]
sh=Image.open(R+'act_a1.png').convert('RGBA')
c=sh.crop((qx+bb[0],qy+bb[1],qx+bb[2]+1,qy+bb[3]+1))
base=Image.new('RGBA',(1024,1024),(0,0,0,0)); base.alpha_composite(c,pos)
a=np.array(base)[...,3]; ys,xs=np.nonzero(a>128); yb=ys.max()
# 靴子：最低 95 像素
by0=yb-95; bx=np.nonzero((a[by0:yb+1]>128).any(0))[0]
box=(bx.min()-4,by0,bx.max()+5,yb+5)
tpl=gray(base.crop(box))
g=Image.open(gp).convert('RGBA')
ga=np.array(g)
if ga[...,3].min()>250:   # 不透明幕布：按品红抠出 alpha
    from crewart import cut
g=g
best=None
for s in np.arange(float(sys.argv[4]),float(sys.argv[5]),0.005):
    r=find(gray(resize(g,s)),tpl)
    if r and (best is None or r[2]>best[0]): best=(r[2],s,r)
sc,s,r=best
gx,gy=box[0]-r[1],box[1]-r[0]
print(f'{name}: scale {s:.3f} score {sc:.3f} offset {gx:.1f},{gy:.1f}')
out=g.transform((1024,1024),Image.AFFINE,(1/s,0,-gx/s,0,1/s,-gy/s),Image.BICUBIC)
out.save(op)
