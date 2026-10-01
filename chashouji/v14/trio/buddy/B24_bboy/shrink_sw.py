import sys,numpy as np
from PIL import Image
src,dst,f=sys.argv[1],sys.argv[2],float(sys.argv[3]); px,py=560,555; y0,y1=510,550
im=Image.open(src).convert('RGBA'); a=np.array(im).astype(float)
s=np.array(im.transform(im.size,Image.AFFINE,(1/f,0,px-px/f,0,1/f,py-py/f),Image.BICUBIC)).astype(float)
Y=np.arange(1024)[:,None,None]; w=np.clip((y1-Y)/(y1-y0),0,1)
pm=lambda x:np.dstack([x[...,:3]*x[...,3:]/255,x[...,3:]])
o=pm(s)*w+pm(a)*(1-w)
out=np.dstack([o[...,:3]*255/np.maximum(o[...,3:],1e-3),o[...,3:]]).clip(0,255).astype(np.uint8)
Image.fromarray(out,'RGBA').save(dst)
