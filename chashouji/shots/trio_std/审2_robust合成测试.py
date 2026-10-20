import numpy as np, json, sys
from PIL import Image
S='shots/trio_std/'
enter=np.array(Image.open(S+'改_B5_enter.jpg').convert('RGB')).astype(np.float32)
idle=np.array(Image.open(S+'改_B5_idle.jpg').convert('RGB')).astype(np.float32)
W=960
bg=enter[:,0:W].copy()                    # 格1：B5 还在画外
real=idle[:,8*W:9*W]                      # 格9：B5 idle 在场
A=Image.open('web/assets/trio/B5_jkd.webp').convert('RGBA').crop((0,0,423,482))
s=0.85; ax,ay=800,1158; kx,ky=260.7,478.1
def paste(img,dx,dy):
    # 亚像素：先放大 4 倍再缩，偏移按 1/4 像素
    big=A.resize((round(423*s*4),round(482*s*4)),Image.LANCZOS)
    ox,oy=ax-kx*s+dx, ay-ky*s+dy
    ix,iy=int(np.floor(ox)),int(np.floor(oy)); fx,fy=ox-ix,oy-iy
    can=Image.new('RGBA',(big.width+8,big.height+8)); can.paste(big,(round(fx*4),round(fy*4)))
    sm=np.array(can.resize((can.width//4,can.height//4),Image.LANCZOS)).astype(np.float32)
    h,w=sm.shape[:2]; a=sm[...,3:]/255
    out=img.copy(); out[iy:iy+h,ix:ix+w]=out[iy:iy+h,ix:ix+w]*(1-a)+sm[...,:3]*a
    return out, (iy,ix,h,w,a[...,0])
# 男主挡在前面的像素：真格里 B5 轮廓内、和 B5 贴在原位差得多的
ref,(iy,ix,h,w,a)=paste(bg,0,0)
d=np.abs(real-ref).max(-1)/255
occ=np.zeros(real.shape[:2],bool); occ[iy:iy+h,ix:ix+w]=(a>0.5)
occ&=d>0.25
# 前脚框（格内 130,440,215,480）里被挡的比例
fx0,fy0=ax+(130-kx)*s, ay+(440-ky)*s; fx1,fy1=ax+(215-kx)*s, ay+(480-ky)*s
fb=(slice(int(fy0),int(fy1)),slice(int(fx0),int(fx1)))
print('前脚框被挡比例 %.2f'%(occ[fb].sum()/max(1,(ref[fb].sum(-1)>0).sum())), '框内 B5 像素', int((a>0.9)[int(fy0)-iy:int(fy1)-iy, int(fx0)-ix:int(fx1)-ix].sum()))
shifts=[(0,0),(0.5,0),(1,0),(1.5,0),(2,0),(3,0),(4,0),(6,0),(0,2),(0,4),(-3,0),(2,-2)]
tiles=[]
for dx,dy in shifts:
    t,_=paste(bg,dx,dy); t[occ]=real[occ]; tiles.append(t)
Image.fromarray(np.concatenate(tiles,1).clip(0,255).astype(np.uint8)).save('/tmp/rb/syn.png')
json.dump([["B5:idle"]]*12,open('/tmp/rb/syn.json','w'))
print('注入',shifts)
