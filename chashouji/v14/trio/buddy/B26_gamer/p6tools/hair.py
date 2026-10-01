import sys, numpy as np
from PIL import Image
ref,src,dst,box=sys.argv[1],sys.argv[2],sys.argv[3],list(map(int,sys.argv[4].split(',')))
def hairmask(a):
    x=a[...,:3]/255; mx=x.max(-1); mn=x.min(-1); s=(mx-mn)/np.maximum(mx,1e-6)
    r,g,b=x[...,0],x[...,1],x[...,2]
    return (a[...,3]>200)&(r>g)&(g>b)&(s>0.35)&(s<0.8)&(mx>0.15)&(mx<0.7)
o=np.array(Image.open(ref).convert('RGBA')).astype(float); a=np.array(Image.open(src).convert('RGBA')).astype(float)
x0,y0,x1,y1=box
mo=hairmask(o); ma=hairmask(a); win=np.zeros(mo.shape,bool); win[y0:y1,x0:x1]=True
co=o[mo&(np.arange(1024)[:,None]<y1)][:,:3].mean(0) if False else o[mo&win][:,:3].mean(0)
ca=a[ma&win][:,:3].mean(0); gain=co/ca; print('ref',co.round(1),'gen',ca.round(1),'gain',gain.round(3))
m=ma&win
a[m,:3]=(a[m,:3]*gain).clip(0,255)
Image.fromarray(a.round().astype(np.uint8),'RGBA').save(dst)
