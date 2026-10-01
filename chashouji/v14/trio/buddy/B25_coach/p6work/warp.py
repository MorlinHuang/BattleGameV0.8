# python3 warp.py in.png out.png fh xc yw L  : 上半身随高度渐变缩放（腰线 yw 处 1，往上 L 像素到 fh），绕 (xc, yw)
import sys, numpy as np
from PIL import Image
from scipy import ndimage
src,dst=sys.argv[1:3]; fh,xc,yw,L=map(float,sys.argv[3:7])
a=np.array(Image.open(src).convert('RGBA')).astype(np.float32)
H,W=a.shape[:2]
Y,X=np.mgrid[0:H,0:W].astype(np.float32)
# 输出 y 处缩放 f(y)；源坐标 = 积分形式保证单调：src_d = ∫0^d 1/f
d=np.clip(yw-np.arange(H),0,None).astype(np.float32)
f=1-(1-fh)*np.clip(d/L,0,1)
srcd=np.concatenate([[0],np.cumsum((1/f)[::-1][:-1])])[::-1]  # 累计（从下往上）
srcd=np.where(d>0, srcd - srcd[int(min(yw,H-1))], 0)
sy=np.where(np.arange(H)<yw, yw-srcd, np.arange(H)).astype(np.float32)
SY=np.repeat(sy[:,None],W,1); SX=xc+(X-xc)/f[:,None]
pm=np.dstack([a[...,:3]*a[...,3:]/255,a[...,3:]])
o=np.dstack([ndimage.map_coordinates(pm[...,c],[SY,SX],order=1,mode='constant') for c in range(4)])
out=np.dstack([o[...,:3]*255/np.maximum(o[...,3:],1e-3),o[...,3:]]).clip(0,255).astype(np.uint8)
Image.fromarray(out,'RGBA').save(dst)
