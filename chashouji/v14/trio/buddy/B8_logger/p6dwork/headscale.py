# 只放大头：以下巴/颈点 C 为心放大 f，头部椭圆内权重 1、外沿 fall px 渐变到 0（连续形变场）
# python3 headscale.py <in> <out> f cx cy hx hy rx ry fall
import sys, numpy as np
from PIL import Image
from scipy import ndimage
i,o=sys.argv[1:3]; f,cx,cy,hx,hy,rx,ry,fall=[float(v) for v in sys.argv[3:11]]
A=np.array(Image.open(i).convert('RGBA')).astype(float)
H,W=A.shape[:2]; Y,X=np.mgrid[0:H,0:W].astype(float)
d=np.sqrt(((X-hx)/rx)**2+((Y-hy)/ry)**2)            # 1 = 椭圆边
t=np.clip(1-(d-1)*min(rx,ry)/fall,0,1); w=t*t*(3-2*t)
k=1+(f-1)*w
sx=cx+(X-cx)/k; sy=cy+(Y-cy)/k
out=np.dstack([ndimage.map_coordinates(A[...,c],[sy,sx],order=3,mode='nearest') for c in range(4)]).clip(0,255).astype(np.uint8)
Image.fromarray(out).save(o); print('→',o)
