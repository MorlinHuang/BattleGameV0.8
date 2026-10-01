# 上半身（腰线以上）绕腰点缩 f，腰下原样，腰线上下 band 像素内渐变
import sys, numpy as np
from PIL import Image
src,dst,f=sys.argv[1],sys.argv[2],float(sys.argv[3])
im=Image.open(src).convert('RGBA'); a=np.array(im).astype(float)
r,g,b,al=a[...,0],a[...,1],a[...,2],a[...,3]
blue=(b>150)&(r<90)&(al>128)
rows=np.nonzero(blue.sum(1)>15)[0]; yh=rows.min()+15     # 牛仔裤顶往下 15
xs=np.nonzero(blue[yh])[0]; xh=(xs.min()+xs.max())/2
print('hip',xh,yh)
sc=im.transform(im.size,Image.AFFINE,(1/f,0,xh-xh/f,0,1/f,yh-yh/f),Image.BICUBIC)
s=np.array(sc).astype(float)
band=24
Y=np.arange(a.shape[0])[:,None,None]
w=np.clip((yh+band/2-Y)/band,0,1)            # 1 = 用缩过的（上），0 = 原图（下）
pm=lambda x:np.dstack([x[...,:3]*x[...,3:]/255,x[...,3:]])
o=pm(s)*w+pm(a)*(1-w)
out=np.dstack([o[...,:3]*255/np.maximum(o[...,3:],1e-3),o[...,3:]]).clip(0,255).astype(np.uint8)
Image.fromarray(out,'RGBA').save(dst)
