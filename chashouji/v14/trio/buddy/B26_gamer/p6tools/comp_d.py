# python3 comp_d.py <swing|release|thru> <gen.png> [out] ：精美1 方向版，底图都是 wind 格（swing_orig）
import sys, numpy as np
sys.path.insert(0,'/workspace/art/chashouji/v14/trio/tools'); sys.path.insert(0,'/workspace/art/chashouji/v14')
from frames import gray, find, resize
from crewart import cut
from PIL import Image
from scipy import ndimage
R='/workspace/art/chashouji/v14/trio/buddy/B26_gamer/raw/'
name,gp=sys.argv[1:3]
orig=Image.open(f'/tmp/b26/swing_orig.png').convert('RGBA')
g=Image.open(gp).convert('RGBA'); ga=np.array(g)
if ga[...,3].min()>250:
    rgb,al=cut(gp,'green',(40,150)); rgb[...,1]=np.minimum(rgb[...,1],np.maximum(rgb[...,0],rgb[...,2])); g=Image.fromarray(np.dstack([rgb,al*255]).clip(0,255).astype(np.uint8),'RGBA')
mk=np.array(Image.open(R+f'p6d_{name}_mask.png'))[...,3]<128   # True = 重画
box=(250,600,790,830)       # 沙发下半 + 拖鞋（三张蒙版外）
tpl=gray(orig.crop(box))
best=None
P=30
for s in np.arange(1024/1254-0.012,1024/1254+0.0121,0.004):
    gs=resize(g,s); r=find(gray(gs.crop((box[0]-P,box[1]-P,box[2]+P,box[3]+P))),tpl)
    if r and (best is None or r[2]>best[0]): best=(r[2],s,r)
sc,s,r=best; gx,gy=P-r[1],P-r[0]
print(f'{name}: scale {s:.3f} score {sc:.3f} offset {gx:.1f},{gy:.1f}')
gt=np.array(g.transform((1024,1024),Image.AFFINE,(1/s,0,-gx/s,0,1/s,-gy/s),Image.BICUBIC)).astype(np.float32)
o=np.array(orig).astype(np.float32)
if len(sys.argv)>4:      # 上半身（蒙版内的生成内容）绕 pivot 缩 f：生成图头 / 耳机被画大
    f,px,py=map(float,sys.argv[4:7])
    gi=Image.fromarray(gt.round().clip(0,255).astype(np.uint8),'RGBA')
    gt=np.array(gi.transform((1024,1024),Image.AFFINE,(1/f,0,px-px/f,0,1/f,py-py/f),Image.BICUBIC)).astype(np.float32)
    print(' shrink',f,px,py)
F=8
m=np.clip(ndimage.distance_transform_edt(mk)/F,0,1)          # 蒙版内 0→1 渐变 F 像素
band=(m>0)&(m<1)&(gt[...,3]<128)
m[band]=0
# 沙发保护：蒙版内 = 生成图 盖在 原图沙发层 上；生成图里的沙发橙（高饱和橙）在原沙发处丢掉
import colorsys
def hsv(a):
    x=a[...,:3]/255; mx=x.max(-1); mn=x.min(-1); sat=np.where(mx>0,(mx-mn)/np.maximum(mx,1e-6),0)
    r,g_,b=x[...,0],x[...,1],x[...,2]
    return sat,mx,(r>g_)&(g_>b)&(r-b>0.45)
os_,ov,oor=hsv(o); orng=oor&(os_>0.6)&(o[...,3]>128)
near=ndimage.binary_dilation(orng,iterations=5)
dark=(ov<0.4)&(o[...,3]>64)
other=(o[...,3]>128)&~orng&~dark
near_other=ndimage.binary_dilation(other,iterations=4)
near_bg=ndimage.binary_dilation(o[...,3]<20,iterations=4)
sofa=orng|(near&dark&(~near_other|near_bg))
sofa=ndimage.binary_fill_holes(sofa)&(o[...,3]>0) if False else sofa
gs_,gv,gor=hsv(gt); gor=gor&(gs_>0.6)
ga=gt[...,3:]/255*(~(gor&sofa))[...,None]
sa=o[...,3:]/255*sofa[...,None]
gt=gt.copy()
a2=ga+sa*(1-ga)
c2=(gt[...,:3]*ga+o[...,:3]*sa*(1-ga))/np.maximum(a2,1e-3)
gt=np.dstack([c2,a2*255])
m=m[...,None]
pa=o[...,3:]/255*(1-m)+gt[...,3:]/255*m
prem=o[...,:3]*o[...,3:]/255*(1-m)+gt[...,:3]*gt[...,3:]/255*m
rgb=np.where(pa>1e-3,prem/np.maximum(pa,1e-3),0)
out=np.dstack([rgb,pa*255]).round().clip(0,255).astype(np.uint8)
keep=(m[...,0]==0); out[keep]=np.array(orig)[keep]
lab,k=ndimage.label(ndimage.binary_dilation(out[...,3]>25,iterations=2))
if k>1:
    sz=ndimage.sum(np.ones_like(lab),lab,range(1,k+1)); big=np.argmax(sz)+1
    for j in range(1,k+1):
        if j!=big and sz[j-1]<400: out[lab==j]=0; print(' drop speck',int(sz[j-1]))
Image.fromarray(out,'RGBA').save(sys.argv[3] if len(sys.argv)>3 else R+f'p6d_{name}.png')
# 体检：蒙版外差异
d=np.abs(out.astype(int)-np.array(orig).astype(int))[~mk].max(); print(' outside-mask maxdiff',d)
