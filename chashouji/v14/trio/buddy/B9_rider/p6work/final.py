# B9 P6 收尾：生成图（已按电驴配准）→ 上半身以胯为心缩 f（连续形变场：胯线以下、车把/后视镜/扶把的左手附近权重 0，不撕不重影）
#   → y ≥ 545 的电驴 / 腿从原条原像素贴回（20px 渐变）→ raw/p6_<帧>.png
# python3 final.py <帧> <norm.png> <f>
import sys, numpy as np
from PIL import Image
from scipy import ndimage
R='/workspace/art/chashouji/v14/trio/buddy/B9_rider/raw/'
name,src,f=sys.argv[1],sys.argv[2],float(sys.argv[3])
CELL={'swing':(511,56,997,720),'thru':(11,850,507,1425),'idle2':(20,147,505,720)}   # 底图格（原条像素）
HIP={'swing':(565,505),'thru':(600,485),'idle2':(560,500)}
BAR={'swing':(370,440,452,548),'thru':(395,395,480,500),'idle2':(365,400,450,505)}   # 后视镜+车把+左手
x0,y0,x1,y1=CELL[name]
c=Image.open(R+'act_a1.png').convert('RGBA').crop((x0-4,y0-4,x1+4,y1+4))
base=Image.new('RGBA',(1024,1024),(0,0,0,0)); base.alpha_composite(c,((1024-c.width)//2,(1024-c.height)//2))
pm=lambda x:np.dstack([x[...,:3]*x[...,3:]/255,x[...,3:]])
un=lambda o:np.dstack([o[...,:3]*255/np.maximum(o[...,3:],1e-3),o[...,3:]]).clip(0,255).astype(np.uint8)
Y,X=np.mgrid[0:1024,0:1024].astype(float)
ga=pm(np.array(Image.open(src).convert('RGBA')).astype(float))
if f!=1:
    xh,yh=HIP[name]
    t=np.clip((yh+10-Y)/40,0,1); wv=t*t*(3-2*t)                       # 胯线以上 1、以下 0（smoothstep 40px）
    bx=np.ones((1024,1024),bool); b=BAR[name]; bx[b[1]:b[3],b[0]:b[2]]=False
    dd=ndimage.distance_transform_edt(bx); t=np.clip(dd/60,0,1); wb=t*t*(3-2*t)
    w=wv*wb
    sx=X+w*((xh+(X-xh)/f)-X); sy=Y+w*((yh+(Y-yh)/f)-Y)
    ga=np.dstack([ndimage.map_coordinates(ga[...,k],[sy,sx],order=3,mode='constant') for k in range(4)])
    ga[...,3]=ga[...,3].clip(0,255); ga[...,:3]=np.minimum(ga[...,:3].clip(0,None),ga[...,3:])
ba=pm(np.array(base).astype(float))
# 渐变带里只在原条有像素的地方让原条盖上来（原条空、生成图有 = 甩下来的手 / 衣摆，保留全不透明）；560 以下只要原条
r=np.clip((Y-535)/20,0,1)[...,None]; r2=np.clip((Y-560)/10,0,1)[...,None]
o=ba*r+ga*(1-r*ba[...,3:]/255)
o=o*(1-r2)+ba*r2
Image.fromarray(un(o),'RGBA').save(R+f'p6_{name}.png')
print('→',R+f'p6_{name}.png')
