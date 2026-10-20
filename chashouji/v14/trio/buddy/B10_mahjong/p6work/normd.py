# python3 normd.py <frame> <gen.png> <out.png>   生成图按腿+马扎配回底图 → 只取蒙版透明区贴回（腿/头 = 原像素）→ 透明底单格
import sys, numpy as np
sys.path.insert(0,'/workspace/art/chashouji/v14/trio/tools'); sys.path.insert(0,'/workspace/art/chashouji/v14')
from frames import gray, find, resize
from crewart import cut
from PIL import Image
from scipy import ndimage
R='/workspace/art/chashouji/v14/trio/buddy/B10_mahjong/raw/'
n,gp,op=sys.argv[1:4]
WAIST=583
b=np.array(Image.open(R+'p6_swing_base.png').convert('RGB'))          # wind 原格像素
body=~((b[...,0]>180)&(b[...,2]>180)&(b[...,1]<110))
balpha=np.array(Image.fromarray(np.dstack([b,np.zeros_like(b[...,0])])))  # placeholder
rgb0,al0=cut(R+'p6_swing_base.png','magenta',(40,150))
base=Image.fromarray(np.dstack([b,np.where(body,255,0)]).astype(np.uint8),'RGBA')
ys,xs=np.nonzero(body[WAIST+70:]); y0=WAIST+70
box=(xs.min()-4,y0,xs.max()+5,ys.max()+y0+5)
tpl=gray(base.crop(box))
g=Image.open(gp).convert('RGBA')
ga=np.array(g)
if ga[...,3].min()>=250:                         # 品红底 → 抠
    rgb,al=cut(gp,'magenta',(40,150)); g=Image.fromarray(np.dstack([rgb,al*255]).clip(0,255).astype(np.uint8),'RGBA')
best=None
for s in np.arange(0.76,0.88,0.004):
    r=find(gray(resize(g,s)),tpl)
    if r and (best is None or r[2]>best[0]): best=(r[2],s,r)
sc,s,r=best; gx,gy=box[0]-r[1],box[1]-r[0]
print(f'{n}: scale {s:.3f} score {sc:.3f} offset {gx:.1f},{gy:.1f}')
G=np.array(g.transform((1024,1024),Image.AFFINE,(1/s,0,-gx/s,0,1/s,-gy/s),Image.BICUBIC)).astype(float)
m=np.array(Image.open(R+f'p6d_{n}_mask.png'))[...,3]>128           # 不透明 = 保留原像素
w=ndimage.gaussian_filter(ndimage.binary_erosion(m,iterations=4).astype(float),3)   # 1 = 原图
O=np.dstack([rgb0,al0*255]).astype(float)
ga_=G[...,3:4]/255; oa=O[...,3:4]/255; wk=w[...,None]
# 渐变带里生成图透明的地方留原图
wk=np.where((ga_<0.5)&(oa>0.5),np.maximum(wk,1.0*(wk>0.02)),wk)
yy,xx=np.mgrid[:1024,:1024]
HD=((((xx-606)/92)**2+((yy-336)/84)**2)<=1)&(yy<372)&~((xx<545)&(yy>345))   # 头：只用原图（生成图的头偏了会出双发际线）
wk=np.where(HD[...,None],1.0,wk)
A=wk*oa+(1-wk)*ga_
C=(wk*oa*O[...,:3]+(1-wk)*ga_*G[...,:3])/np.maximum(A,1e-4)
out=np.dstack([C,A*255]).clip(0,255).astype(np.uint8)
Image.fromarray(out,'RGBA').save(op)
