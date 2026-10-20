import sys, json, numpy as np
from PIL import Image
from scipy.signal import fftconvolve
at=Image.open('/workspace/art/chashouji/web/assets/trio/B5_jkd.webp').convert('RGBA'); cw,ch=494,482
names=["idle","wind","hitA","hitB","walk1","walk2","walk3","walk4","taunt","idle2"]
S=0.83
def tpl(fn,box):
    i=names.index(fn); c=at.crop(((i%4)*cw,(i//4)*ch,(i%4+1)*cw,(i//4+1)*ch)).crop(box)
    c=c.resize((round(c.width*S),round(c.height*S)),Image.LANCZOS); a=np.asarray(c).astype(float)/255
    return a[:,:,:3],(a[:,:,3]>0.9).astype(float)
def find(I,fn,box):
    t,m=tpl(fn,box); y0,y1,x0,x1=950,1100,0,960; J=I[y0:y1,x0:x1]; num=0
    for c in range(3):
        T=t[:,:,c]*m; num+=fftconvolve(J[:,:,c]**2,m[::-1,::-1],'valid')-2*fftconvolve(J[:,:,c],T[::-1,::-1],'valid')+(T**2).sum()
    num/=m.sum()*3; k=np.unravel_index(np.argmin(num),num.shape); yy,xx=k; dx=0
    if 0<xx<num.shape[1]-1:
        a,b,c=num[yy,xx-1],num[yy,xx],num[yy,xx+1]; d=a-2*b+c; dx=0.5*(a-c)/d if d>0 else 0
    return x0+xx+dx, num[k]
# 每帧两只鞋的框（格内），以及鞋尖 / 鞋跟格内 x（面朝左：鞋尖在左）
SH={'walk1':{'near':(118,445,202,478),'far':(314,420,380,478)},
    'walk2':{'near':(225,452,310,478)},
    'walk3':{'near':(330,430,410,478),'far':(98,436,182,478)},
    'walk4':{'far':(188,452,256,478)},}
for f in sys.argv[1:]:
    I=np.asarray(Image.open(f).convert('RGB')).astype(float)/255; fr=json.load(open(f[:-4]+'.json'))
    print('==',f)
    for i,r in enumerate(fr):
        fn=[x.split(':')[1] for x in r if x.startswith('B5:')][0]
        if fn not in SH: continue
        out=[]
        for foot,box in SH[fn].items():
            x,e=find(I[:,i*960:(i+1)*960],fn,box)
            # 框左沿屏幕 x → 鞋框左沿（格内 box[0]）对应的"世界"格内坐标换算：屏幕 x - box0*S 即锚点相关的格原点
            out.append(f'{foot} 框左 {x:.1f} 格原点 {x-box[0]*S:.1f} err {e:.4f}')
        print(i+1,fn,' | '.join(out))
