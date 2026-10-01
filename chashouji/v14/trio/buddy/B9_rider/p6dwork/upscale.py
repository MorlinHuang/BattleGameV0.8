# 上半身以胯为心缩 f（连续形变场：胯线以下、车把/后视镜/扶把手附近权重 0）—— 照 p6work/final.py 的形变，输入输出都是铺绿幕的不透明图
# python3 upscale.py <in> <out> f hx hy bx0 by0 bx1 by1
import sys, numpy as np
from PIL import Image
from scipy import ndimage
i,o=sys.argv[1:3]; f,xh,yh=[float(v) for v in sys.argv[3:6]]; B=[int(v) for v in sys.argv[6:10]]
A=np.array(Image.open(i).convert('RGB')).astype(float); H,W=A.shape[:2]
Y,X=np.mgrid[0:H,0:W].astype(float)
t=np.clip((yh+10-Y)/40,0,1); wv=t*t*(3-2*t)
bx=np.ones((H,W),bool); bx[B[1]:B[3],B[0]:B[2]]=False
dd=ndimage.distance_transform_edt(bx); t=np.clip(dd/60,0,1); wb=t*t*(3-2*t)
w=wv*wb
sx=X+w*((xh+(X-xh)/f)-X); sy=Y+w*((yh+(Y-yh)/f)-Y)
out=np.dstack([ndimage.map_coordinates(A[...,k],[sy,sx],order=3,mode='nearest') for k in range(3)])
Image.fromarray(out.clip(0,255).astype(np.uint8)).save(o); print('→',o)
