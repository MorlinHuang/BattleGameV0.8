# 生成图 → 按蒙版外的腿配回底图 → 只取蒙版透明区贴回：python3 paste.py <name> <gen.png> [s0 s1]
import sys, numpy as np
sys.path.insert(0,'/workspace/art/chashouji/v14/trio/tools'); sys.path.insert(0,'/workspace/art/chashouji/v14')
from frames import gray, find, resize
from crewart import cut
from PIL import Image
from scipy import ndimage
R='/workspace/art/chashouji/v14/trio/buddy/B30_smart/raw/'
name,gp=sys.argv[1:3]; f=float(sys.argv[3]) if len(sys.argv)>3 else 1.0; s0,s1=(float(sys.argv[4]),float(sys.argv[5])) if len(sys.argv)>5 else (0.5,1.0)
rgb,al=cut(R+f'p6_{name}_base.png','magenta',(40,150))
base=Image.fromarray(np.dstack([rgb,al*255]).clip(0,255).astype(np.uint8),'RGBA')
keep=np.array(Image.open(R+f'p6_{name}_mask.png'))[...,3]>128          # 不透明 = 保留
# 模板：蒙版外（腿）的身体包围盒，往里收 20 远离蒙版边
lm=keep&(al>0.5); lm=ndimage.binary_erosion(keep,iterations=20)&(al>0.5)
ys,xs=np.nonzero(lm); box=(xs.min()-4,ys.min(),xs.max()+5,ys.max()+5)
tpl=gray(base.crop(box))
g=Image.open(gp).convert('RGBA')
if np.array(g)[...,3].min()>250:
    gr,ga=cut(gp,'magenta',(40,150)); g=Image.fromarray(np.dstack([gr,ga*255]).clip(0,255).astype(np.uint8),'RGBA')
q=0.25; tq=gray(resize(base.crop(box),q))
best=None
for s in np.arange(s0,s1,0.01):
    r=find(gray(resize(g,s*q)),tq)
    if r and (best is None or r[2]>best[0]): best=(r[2],s,r)
sc0=best[1]; best=None
for s in np.arange(sc0-0.012,sc0+0.013,0.003):
    gi=resize(g,s); cy,cx=best_r=( None,None)
    r=find(gray(gi),tpl)
    if r and (best is None or r[2]>best[0]): best=(r[2],s,r)
sc,s,r=best
gx,gy=box[0]-r[1],box[1]-r[0]
print(f'{name}: scale {s:.3f} score {sc:.3f} offset {gx:.1f},{gy:.1f}')
G=np.array(g.transform((1024,1024),Image.AFFINE,(1/s,0,-gx/s,0,1/s,-gy/s),Image.BICUBIC)).astype(np.float32)
if f!=1.0:   # 上半身绕胯点缩 f（腰线以下不影响：蒙版外本来就用原图）
    ky=np.nonzero((~keep).all(1))[0].max()               # 蒙版透明区最低一行 = 腰线
    row=np.nonzero(al[ky+10]>0.5)[0]; xh=(row.min()+row.max())/2; yh=ky+10
    Gi=Image.fromarray(G.clip(0,255).astype(np.uint8),'RGBA')
    G=np.array(Gi.transform((1024,1024),Image.AFFINE,(1/f,0,xh-xh/f,0,1/f,yh-yh/f),Image.BICUBIC)).astype(np.float32)
    print('shrink',f,'pivot',xh,yh)
B=np.array(base).astype(np.float32)
# 蒙版透明区权重，边上 8px 渐变（只往透明区里渐变，蒙版外全是原像素）
d=ndimage.distance_transform_edt(~keep)
w=np.clip(d/8,0,1)
ga,ba=G[...,3]/255,B[...,3]/255
w=w*np.maximum(ga,1-ba)            # 渐变带里生成图是空的地方留原图
w=np.where(d>8,1,w)                # 渐变带外完全用生成图
pm=lambda X:np.dstack([X[...,:3]*X[...,3:]/255,X[...,3:]])
o=pm(G)*w[...,None]+pm(B)*(1-w[...,None])
out=np.dstack([o[...,:3]*255/np.maximum(o[...,3:],1e-3),o[...,3:]]).clip(0,255).astype(np.uint8)
Image.fromarray(out,'RGBA').save(R+f'p6_{name}.png')
# 预览
pv=Image.new('RGBA',(1024,1024),(200,200,200,255)); pv.alpha_composite(Image.fromarray(out,'RGBA'))
pv.convert('RGB').resize((512,512)).save(f'/tmp/b30/out_{name}.png')
