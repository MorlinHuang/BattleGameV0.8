import numpy as np
from PIL import Image
from scipy import ndimage
R='/workspace/art/chashouji/v14/trio/buddy/B10_mahjong/raw/'
MAG=np.array([255,0,255],np.uint8)
yy,xx=np.mgrid[:1024,:1024]
ell=lambda cx,cy,rx,ry:((xx-cx)/rx)**2+((yy-cy)/ry)**2<=1
cfg={'swing':dict(waist=583,head=(606,336,66,60),shift=(-55,18)),
     'thru': dict(waist=595,head=(555,392,62,66),shift=(-22,38)),
     'idle2':dict(waist=519,head=(528,295,62,66),shift=(0,0))}
for n,c in cfg.items():
    a=np.array(Image.open(R+f'p6_{n}_base.png').convert('RGB'))
    body=np.load(f'/tmp/b10/{n}_body.npy')
    hx,hy,rx,ry=c['head']; dx,dy=c['shift']
    H=ell(hx,hy,rx,ry)&body
    out=a.copy(); nb=body.copy()
    keep=body.copy(); keep[:c['waist']+8]=False
    if n!='idle2':
        out[:c['waist']+8][body[:c['waist']+8]]=MAG; nb[:c['waist']+8]=False   # 上身清掉
        Hs=np.roll(np.roll(H,dy,0),dx,1)
        out[Hs]=np.roll(np.roll(a,dy,0),dx,1)[Hs]; nb|=Hs
        hk=ndimage.binary_erosion(Hs,iterations=5)&ell(hx+dx,hy+dy,rx-6,ry-6)
    else:
        # 打哈欠：脸前半（眼、嘴）重画；后脑勺留给挠头的手
        hk=H&~ell(503,305,34,48)&~((xx>562)&(yy>245)&(yy<330))
        hk=ndimage.binary_erosion(hk,iterations=3)
        lab=np.zeros_like(body); lab[c['waist']-110:c['waist']+70,300:445]=True
        keep|=body&lab
    keep=ndimage.binary_dilation(keep,iterations=6)|hk
    Image.fromarray(out).save(R+f'p6_{n}_base2.png')
    m=np.zeros((1024,1024,4),np.uint8); m[...,3]=np.where(keep,255,0)
    Image.fromarray(m,'RGBA').save(R+f'p6_{n}_mask2.png')
    np.save(f'/tmp/b10/{n}_body2.npy',nb)
    vis=out.astype(float); vis[~keep]=vis[~keep]*0.4+np.array([0,200,0])*0.6
    Image.fromarray(vis.astype(np.uint8)).save(f'/tmp/b10/{n}_mv2.png')
