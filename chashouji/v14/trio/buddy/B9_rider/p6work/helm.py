import sys, numpy as np
from PIL import Image
from scipy import ndimage
def helm(p, x0=0, x1=1024, y0=0):
    a=np.array(Image.open(p).convert('RGBA')).astype(int)
    r,g,b,al=a[...,0],a[...,1],a[...,2],a[...,3]
    blue=(b>170)&(r<90)&(g>80)&(g<200)&(al>128)
    if p.endswith('base.png'): blue&=~((g>200)&(r<80)&(b<80))
    blue[:, :x0]=0; blue[:, x1:]=0; blue[:y0]=0
    lab,k=ndimage.label(ndimage.binary_closing(blue,iterations=2))
    # 头盔：最高的那块（尺寸 > 3000 像素）
    best=None
    for i,s in enumerate(ndimage.find_objects(lab)):
        n=(lab[s]==i+1).sum()
        if n>3000 and (best is None or s[0].start<best[1][0].start): best=(i+1,s,n)
    i,s,n=best
    return s[1].stop-s[1].start, s[0].stop-s[0].start, n, (s[1].start,s[0].start)
for arg in sys.argv[1:]:
    p,*lim=arg.split(':'); lim=[int(v) for v in lim]
    print(p, helm(p,*lim))
