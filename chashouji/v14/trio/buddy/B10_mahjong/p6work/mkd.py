# P6 方向版：底图 = wind 格（canvas 位置同 p6_swing_base），清掉两条手臂、画粗略引导臂，蒙版只留腿+马扎+头
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
R='/workspace/art/chashouji/v14/trio/buddy/B10_mahjong/raw/'
MAG=(255,0,255)
yy,xx=np.mgrid[:1024,:1024]
ell=lambda cx,cy,rx,ry:((xx-cx)/rx)**2+((yy-cy)/ry)**2<=1
base=Image.open(R+'p6_swing_base.png').convert('RGB')
a=np.array(base); body=~((a[...,0]>180)&(a[...,2]>180)&(a[...,1]<110))
WAIST=583
SKIN=(244,196,150); INK=(40,30,30)
S=(525,445)          # 引导用肩点（画布坐标）
G={'swing':  dict(arm=[S,(605,548),(722,484)], hand=(728,480), hr=30),
   'release':dict(arm=[S,(418,410),(318,378)], hand=(300,372), hr=34),
   'thru':   dict(arm=[S,(415,465),(310,492)], hand=(292,498), hr=32)}
for n,g in G.items():
    im=base.copy(); d=ImageDraw.Draw(im)
    # 清掉举着的手臂 + 后侧拳头
    d.polygon([(395,160),(525,160),(548,330),(552,420),(540,480),(498,505),(452,440),(395,300)],fill=MAG)
    d.polygon([(712,470),(830,470),(830,585),(712,585)],fill=MAG)
    # 后侧手臂：撑在大腿上
    for w,c in ((50,INK),(42,SKIN)):
        d.line([(700,455),(742,535),(712,600)],fill=c,width=w,joint='curve')
    d.ellipse([686,580,742,628],fill=SKIN,outline=INK,width=4)
    # 出手臂引导
    for w,c in ((58,INK),(50,SKIN)):
        d.line(g['arm'],fill=c,width=w,joint='curve')
    hx,hy=g['hand']; r=g['hr']
    d.ellipse([hx-r,hy-r,hx+r,hy+r],fill=SKIN,outline=INK,width=4)
    im.save(R+f'p6d_{n}_base.png')
    keep=body.copy(); keep[:WAIST+8]=False
    keep=ndimage.binary_dilation(keep,iterations=6)
    keep|=ndimage.binary_erosion(ell(606,336,66,60)&body,iterations=5)&ell(606,336,60,54)
    m=np.zeros((1024,1024,4),np.uint8); m[...,3]=np.where(keep,255,0)
    Image.fromarray(m,'RGBA').save(R+f'p6d_{n}_mask.png')
    vis=np.array(im).astype(float); vis[~keep]=vis[~keep]*0.5+np.array([0,200,0])*0.5
    Image.fromarray(vis.astype(np.uint8)).save(f'/tmp/b10/d_{n}_mv.png')
