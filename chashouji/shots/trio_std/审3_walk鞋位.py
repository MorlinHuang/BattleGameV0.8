import sys, json, numpy as np
from PIL import Image
from scipy.signal import fftconvolve
at=Image.open('/workspace/art/chashouji/web/assets/trio/B5_jkd.webp').convert('RGBA'); cw,ch=423,482
names=['idle','wind','hitA','hitB','walk1','walk2','walk3','taunt']
BOX={'walk1':(120,430,220,480),'walk3':(110,430,215,480),'walk2':(205,440,295,480)}  # 前脚（着地）鞋
S=0.83
def tpl(fn):
    i=names.index(fn); c=at.crop(((i%4)*cw,(i//4)*ch,(i%4+1)*cw,(i//4+1)*ch)).crop(BOX[fn])
    c=c.resize((round(c.width*S),round(c.height*S)),Image.LANCZOS); a=np.asarray(c).astype(float)/255
    return a[:,:,:3], (a[:,:,3]>0.9).astype(float)
def find(cell, fn):
    t,m=tpl(fn); y0,y1,x0,x1=990,1110,250,960
    I=cell[y0:y1,x0:x1]; th,tw=m.shape
    num=0
    for c in range(3):
        T=t[:,:,c]*m; num+= fftconvolve(I[:,:,c]**2, m[::-1,::-1],'valid') - 2*fftconvolve(I[:,:,c], T[::-1,::-1],'valid') + (T**2).sum()
    num/=m.sum()*3
    k=np.unravel_index(np.argmin(num),num.shape); e=num[k]
    # 亚像素
    yy,xx=k; dx=0
    if 0<xx<num.shape[1]-1:
        a,b,c=num[yy,xx-1],num[yy,xx],num[yy,xx+1]; d=a-2*b+c; dx=0.5*(a-c)/d if d>0 else 0
    return x0+xx+dx, y0+yy, e
for f in sys.argv[1:]:
    im=np.asarray(Image.open(f).convert('RGB')).astype(float)/255; fr=json.load(open(f[:-4]+'.json'))
    print('==',f)
    prev=None
    for i,r in enumerate(fr):
        fn=r[0].split(':')[1] if r else ''
        if fn not in BOX: print(i+1,fn); prev=None; continue
        x,y,e=find(im[:, i*960:(i+1)*960], fn)
        d = f'{x-prev[1]:+.2f}' if prev and prev[0]==fn else ''
        print(i+1,fn,f'x={x:.2f} y={y} err={e:.4f}',d); prev=(fn,x)
