# P6d：生成图按蒙版外部位（腿/靴 或 车）模板匹配对齐底图，只取蒙版透明区贴回（边上 band px 渐变），输出铺幕布色的不透明图
# python3 paste.py <base.png> <mask.png> <gen.png> <out.png> <tplbox x0,y0,x1,y1> <smin> <smax> [band]
import sys, numpy as np
sys.path.insert(0,'/workspace/art/chashouji/v14/trio/tools')
from frames import gray, find, resize
from PIL import Image
from scipy import ndimage
bp,mp,gp,op=sys.argv[1:5]; box=tuple(int(v) for v in sys.argv[5].split(',')); s0,s1=float(sys.argv[6]),float(sys.argv[7])
band=int(sys.argv[8]) if len(sys.argv)>8 else 8
base=Image.open(bp).convert('RGB'); B=np.array(base).astype(float); key=B[0,0].copy()
isbg=(np.abs(B-key).sum(-1)<60)
ba=Image.fromarray(np.dstack([B,np.where(isbg,0,255)]).astype(np.uint8),'RGBA')
tpl=gray(ba.crop(box))
g=Image.open(gp).convert('RGBA'); ga=np.array(g)
if ga[...,3].min()>250:   # 不透明幕布 → 按色键抠
    G=ga[...,:3].astype(float); k=G[0,0]; d=np.abs(G-k).sum(-1); ga[...,3]=np.clip((d-60)*255/120,0,255).astype(np.uint8); g=Image.fromarray(ga)
best=None
for s in np.arange(s0,s1,0.004):
    r=find(gray(resize(g,s)),tpl)
    if r and (best is None or r[2]>best[0]): best=(r[2],s,r)
sc,s,r=best; gx,gy=box[0]-r[1],box[1]-r[0]
print(f'scale {s:.3f} score {sc:.3f} offset {gx:.1f},{gy:.1f}')
gt=np.array(g.transform(base.size,Image.AFFINE,(1/s,0,-gx/s,0,1/s,-gy/s),Image.BICUBIC)).astype(float)
gal=gt[...,3:]/255; gon=gt[...,:3]*gal+key*(1-gal)          # 生成图铺到幕布上
m=np.array(Image.open(mp).convert('RGBA'))[...,3]<128          # True = 重画区
d_in=ndimage.distance_transform_edt(m); d_out=ndimage.distance_transform_edt(~m)
w=np.clip(0.5+(d_in-d_out)/band,0,1)                         # 1 = 用生成图
# 渐变带里：生成图是幕布的地方留原图
inband=(w>0)&(w<1); w=np.where(inband&(gal[...,0]<0.5),0,w)
o=gon*w[...,None]+B*(1-w[...,None])
Image.fromarray(o.clip(0,255).astype(np.uint8)).save(op); print('→',op)
