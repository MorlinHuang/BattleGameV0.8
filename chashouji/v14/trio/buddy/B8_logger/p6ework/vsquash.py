# 躯干竖向压缩：y<ys 的部分整体下移 d（头、举起的手臂刚性平移），ys~yb 之间线性压缩，y>yb 不动；可选 dx 同样按权重横移
# python3 vsquash.py <in> <out> ys yb d [dx]
import sys, numpy as np
from PIL import Image
from scipy import ndimage
i,o=sys.argv[1:3]; ys,yb,d=[float(v) for v in sys.argv[3:6]]; dx=float(sys.argv[6]) if len(sys.argv)>6 else 0
A=np.array(Image.open(i).convert('RGB')).astype(float); H,W=A.shape[:2]
y=np.arange(H,dtype=float); w=np.clip((yb-y)/(yb-ys),0,1)      # 1 above ys, 0 below yb
fy=y+d*w                                                        # forward map (monotonic if d<yb-ys)
src_y=np.interp(y,fy,y)                                         # inverse
wsrc=np.clip((yb-src_y)/(yb-ys),0,1)
Y=np.repeat(src_y[:,None],W,1); X=np.arange(W)[None,:]-dx*wsrc[:,None]
X=np.broadcast_to(X,(H,W))
key=A[0,0]
out=np.dstack([ndimage.map_coordinates(A[...,c],[Y,X],order=1,mode='constant',cval=key[c]) for c in range(3)])
Image.fromarray(out.clip(0,255).astype(np.uint8)).save(o); print('→',o)
