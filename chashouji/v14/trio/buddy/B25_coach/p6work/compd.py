# python3 comp.py <name> <gen.png> [out] [f px py] ; 按蒙版外的腿把生成图配回底图，只取蒙版透明区
import sys, json, numpy as np
sys.path.insert(0,'/workspace/art/chashouji/v14/trio/tools'); sys.path.insert(0,'/workspace/art/chashouji/v14')
from frames import gray, find, resize
from crewart import cut
from PIL import Image
from scipy import ndimage
R='/workspace/art/chashouji/v14/trio/buddy/B25_coach/raw/'
name,gp=sys.argv[1:3]
out_p=sys.argv[3] if len(sys.argv)>3 and sys.argv[3]!='-' else R+f'p6d_{name}.png'
orig=Image.open(f'/tmp/b25/{name}_orig.png').convert('RGBA')
g=Image.open(gp).convert('RGBA'); ga=np.array(g)
if ga[...,3].min()>250:
    rgb,al=cut(gp,'magenta',(40,150)); g=Image.fromarray(np.dstack([rgb,al*255]).clip(0,255).astype(np.uint8),'RGBA')
import os
mp=f'/tmp/b25/{name}_compmask.png'
mk=np.array(Image.open(mp if os.path.exists(mp) else R+f'p6d_{name}_mask.png'))[...,3]<128   # True = 重画
info=json.load(open('/tmp/b25/info.json'))[name]
px,py=info['pos']; w,h=info['size']
oa=np.array(orig)[...,3]
# 模板 = 蒙版外、有人的部分的外接框（再往上收 10px 离开蒙版边）
ys,xs=np.nonzero((oa>128)&~ndimage.binary_dilation(mk,iterations=12))
box=(xs.min(),ys.min(),xs.max()+1,ys.max()+1)
tpl=gray(orig.crop(box))
P=200
def srch(ss):
    best=None
    for s in ss:
        gs=resize(g,s); r=find(gray(gs.crop((box[0]-P,box[1]-P,box[2]+P,box[3]+P))),tpl)
        if r and (best is None or r[2]>best[0]): best=(r[2],s,r)
    return best
b0=srch(np.arange(0.55,0.96,0.01)); best=srch(np.arange(b0[1]-0.009,b0[1]+0.0091,0.002))
sc,s,r=best; gx,gy=box[0]-P+r[1]-box[0]*0, 0
gx,gy=(box[0]-P+r[1])-box[0]*1, (box[1]-P+r[0])-box[1]
# 生成图（缩放后）里模板落在 (box0-P+r1, box1-P+r0)，要搬到 box0,box1：平移 = -(上面的差)
gx,gy=-gx,-gy
print(f'{name}: tplbox {box} scale {s:.3f} score {sc:.3f} offset {gx:.1f},{gy:.1f}')
gt=np.array(g.transform((1024,1024),Image.AFFINE,(1/s,0,-gx/s,0,1/s,-gy/s),Image.BICUBIC)).astype(np.float32)
if len(sys.argv)>4:
    f,qx,qy=map(float,sys.argv[4:7])
    gi=Image.fromarray(gt.round().clip(0,255).astype(np.uint8),'RGBA')
    gt=np.array(gi.transform((1024,1024),Image.AFFINE,(1/f,0,qx-qx/f,0,1/f,qy-qy/f),Image.BICUBIC)).astype(np.float32)
    print(' shrink',f,qx,qy)
o=np.array(orig).astype(np.float32)
import os
if os.environ.get('WARP'):
    Image.fromarray(gt.round().clip(0,255).astype(np.uint8),'RGBA').save(f'/tmp/b25/_pre_{name}.png')
    os.system(f'python3 /tmp/b25/warp.py /tmp/b25/_pre_{name}.png /tmp/b25/_post_{name}.png '+os.environ['WARP'])
    gt=np.array(Image.open(f'/tmp/b25/_post_{name}.png')).astype(np.float32); print(' warp',os.environ['WARP'])
F=8
m=np.clip(ndimage.distance_transform_edt(mk)/F,0,1)
band=(m>0)&(m<1)&(gt[...,3]<128); m[band]=0
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
Image.fromarray(out,'RGBA').save(out_p)
d=np.abs(out.astype(int)-np.array(orig).astype(int))[~mk].max(); print(' outside-mask maxdiff',d, '->',out_p)
# also save aligned gen for inspection
Image.fromarray(gt.round().clip(0,255).astype(np.uint8),'RGBA').save(f'/tmp/b25/{name}_genaligned.png')
