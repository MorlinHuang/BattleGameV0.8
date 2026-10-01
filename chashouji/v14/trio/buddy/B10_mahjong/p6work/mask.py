import numpy as np
from PIL import Image
from scipy import ndimage
R='/workspace/art/chashouji/v14/trio/buddy/B10_mahjong/raw/'
for n in ['swing','thru','idle2']:
    a=np.array(Image.open(R+f'p6_{n}_base.png').convert('RGB')).astype(int)
    body=np.load(f'/tmp/b10/{n}_body.npy')
    r,g,b=a[...,0],a[...,1],a[...,2]
    olive=(abs(r-g)<25)&(r>90)&(r<170)&(b<r-15)&(b>50)
    rows=np.nonzero(olive.sum(1)>60)[0]; waist=rows.min()
    print(n,'shorts top',waist)
    keep=body.copy(); keep[:waist+8]=False          # 腰带往下 8px 以下的人保留
    if n=='idle2':
        # 只重画：头 + 挠头那只手臂（肚子上那只）+ 上身；搭膝那只手保留
        keep=body.copy()
        T=np.zeros_like(body); T[:waist+8, 520:]=True   # 右半上身+头
        T[:waist+8, :]=True
        lab=np.zeros_like(body); lab[waist-110:waist+70, 300:445]=True  # 搭膝的手/前臂
        T&=~lab
        keep&=~T
    keep=ndimage.binary_dilation(keep,iterations=6)
    m=np.zeros((1024,1024,4),np.uint8); m[...,3]=np.where(keep,255,0)
    Image.fromarray(m,'RGBA').save(R+f'p6_{n}_mask.png')
    vis=a.copy(); vis[~keep]=(vis[~keep]*0.4+np.array([0,200,0])*0.6).astype(int)
    Image.fromarray(vis.astype(np.uint8)).save(f'/tmp/b10/{n}_maskvis.png')
