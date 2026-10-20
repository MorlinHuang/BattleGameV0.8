# P6 方向版：同 p6paste.py，读写 raw/p6d_*：python3 p6dpaste.py <name> <gen.png> [f] [s0 s1]
import sys, numpy as np
sys.path.insert(0,'/workspace/art/chashouji/v14/trio/tools'); sys.path.insert(0,'/workspace/art/chashouji/v14')
from frames import gray, find, resize
from crewart import cut
from PIL import Image
from scipy import ndimage
R='/workspace/art/chashouji/v14/trio/buddy/B7_f4/raw/'
name,gp=sys.argv[1:3]; f=float(sys.argv[3]) if len(sys.argv)>3 else 1.0; s0,s1=(float(sys.argv[4]),float(sys.argv[5])) if len(sys.argv)>5 else (0.5,1.0)
rgb,al=cut(R+f'p6d_{name}_base.png','green',(40,150))
base=Image.fromarray(np.dstack([rgb,al*255]).clip(0,255).astype(np.uint8),'RGBA')
keep=np.array(Image.open(R+f'p6d_{name}_mask.png'))[...,3]>128          # 不透明 = 保留
import os; PADR=int(os.environ.get('PADR','0'))      # 生成图的手伸出 1024 画布右边：画布往右加宽 PADR（加宽区按要重画处理）
CW=1024+PADR
if PADR:
    rgb=np.pad(rgb,((0,0),(0,PADR),(0,0))); al=np.pad(al,((0,0),(0,PADR))); keep=np.pad(keep,((0,0),(0,PADR)))
    base=Image.fromarray(np.dstack([rgb,al*255]).clip(0,255).astype(np.uint8),'RGBA')
# 模板：蒙版外（腿）的身体包围盒，往里收 20 远离蒙版边
lm=keep&(al>0.5); lm=ndimage.binary_erosion(keep,iterations=20)&(al>0.5)
ys,xs=np.nonzero(lm); box=(xs.min()-4,ys.min(),xs.max()+5,ys.max()+5)
tpl=gray(base.crop(box))
g=Image.open(gp).convert('RGBA')
if np.array(g)[...,3].min()>250:
    gr,ga=cut(gp,'green',(40,150)); g=Image.fromarray(np.dstack([gr,ga*255]).clip(0,255).astype(np.uint8),'RGBA')
q=0.25; tq=gray(resize(base.crop(box),q))
best=None
for s in np.arange(s0,s1,0.01):
    r=find(gray(resize(g,s*q)),tq)
    if r and (best is None or r[2]>best[0]): best=(r[2],s,r)
sc0=best[1]; best=None
for s in np.arange(sc0-0.012,sc0+0.013,0.003):
    gi=resize(g,s); cy,cx=best_r=( None,None)
    r=find(gray(gi),tpl)
    if r and (best is None or r[2]>best[0]): best=(r[2],s,r)
sc,s,r=best
gx,gy=box[0]-r[1],box[1]-r[0]
print(f'{name}: scale {s:.3f} score {sc:.3f} offset {gx:.1f},{gy:.1f}')
G=np.array(g.transform((CW,1536),Image.AFFINE,(1/s,0,-gx/s,0,1/s,-gy/s),Image.BICUBIC)).astype(np.float32)
if f!=1.0:   # 上半身绕胯点缩 f（腰线以下不影响：蒙版外本来就用原图）
    ky=int(os.environ.get('KY','575'))               # 蒙版透明区最低一行 = 腰线
    row=np.nonzero(al[ky+10]>0.5)[0]; xh=float(os.environ.get('XH',(row.min()+row.max())/2)); yh=ky+10
    Gi=Image.fromarray(G.clip(0,255).astype(np.uint8),'RGBA')
    Gs=np.array(Gi.transform((CW,1536),Image.AFFINE,(1/f,0,xh-xh/f,0,1/f,yh-yh/f),Image.BICUBIC)).astype(np.float32)
    # 上半身缩放
    BAND=int(os.environ.get('BAND','40')); Y=np.arange(1536)[:,None,None]; wy=np.clip((yh+BAND/2-Y)/BAND,0,1)
    pmx=lambda X:np.dstack([X[...,:3]*X[...,3:]/255,X[...,3:]])
    o2=pmx(Gs)*wy+pmx(G)*(1-wy)
    G=np.dstack([o2[...,:3]*255/np.maximum(o2[...,3:],1e-3),o2[...,3:]]).clip(0,255)
    print('shrink',f,'pivot',xh,yh)
B=np.array(base).astype(np.float32)
# B7：原 idle 外套下摆尖在蒙版线（790）下面还露几像素 —— 腰线附近原图里的酒红色像素清掉（新外套由生成图给）
Yb=np.arange(B.shape[0])[:,None]
red=(B[...,0]>B[...,1]+50)&(B[...,0]>B[...,2]+20)&(Yb>=760)&(Yb<=815)
red=ndimage.binary_dilation(red,iterations=2)&(Yb>=760)&(Yb<=815)
B[red,3]=0
# 再把腰线带里和腿不相连的原图碎块（下摆尖的黑描边）清掉：只留与 830 行（腿）连通的
band=B[760:831,:,3]>25; lab,_=ndimage.label(band); keepl=set(np.unique(lab[-1]))-{0}
B[760:831,:,3]*=np.isin(lab,list(keepl))|(~band)
# 腿两侧的外轮廓按 805 / 830 两行线性外推到腰线带，外推轮廓以外的原图像素清掉（下摆底下压着的暗衬里）
def edges(y):
    r=np.nonzero(B[y,:,3]>128)[0]; return r.min(),r.max()
(l1,r1),(l2,r2)=edges(805),edges(830)
for y in range(765,805):
    t=(y-805)/25; L=l1+(l1-l2)*-t*-1 if False else l1+(l1-l2)*(805-y)/25; Rr=r1+(r1-r2)*(805-y)/25
    B[y,:int(L)-1,3]=0; B[y,int(Rr)+2:,3]=0
# 蒙版透明区权重，边上 8px 渐变（只往透明区里渐变，蒙版外全是原像素）
d=ndimage.distance_transform_edt(~keep)
w=np.clip(d/8,0,1)
ga,ba=G[...,3]/255,B[...,3]/255
w=w*np.maximum(ga,1-ba)            # 渐变带里生成图是空的地方留原图
w=np.where(d>8,1,w)                # 渐变带外完全用生成图
pm=lambda X:np.dstack([X[...,:3]*X[...,3:]/255,X[...,3:]])
o=pm(G)*w[...,None]+pm(B)*(1-w[...,None])
out=np.dstack([o[...,:3]*255/np.maximum(o[...,3:],1e-3),o[...,3:]]).clip(0,255).astype(np.uint8)
# 上半身绕腰点缩小后，腰线带里生成图的裤腿也跟着收窄，和原图裤腿之间漏出缝：按 805/830 行外推的裤腿轮廓，把缝里透明处用 806 行同一列的裤子像素垫在下面
o=out.astype(np.float32)
for y in range(760,806):
    L=int(l1+(l1-l2)*(805-y)/25); Rr=int(r1+(r1-r2)*(805-y)/25)
    under=o[806,L:Rr+1].copy(); a=o[y,L:Rr+1,3:]/255
    o[y,L:Rr+1,:3]=o[y,L:Rr+1,:3]*a+under[:,:3]*(1-a); o[y,L:Rr+1,3]=np.maximum(o[y,L:Rr+1,3],under[:,3])
    if y>=775: o[y,Rr+3:,3]*=(o[y,Rr+3:,3]>=160)     # 插兜手腕下面的半透明渐变残渣
out=o.clip(0,255).astype(np.uint8)
Image.fromarray(out,'RGBA').save(R+f'p6d_{name}.png')
# 预览
pv=Image.new('RGBA',(CW,1536),(200,200,200,255)); pv.alpha_composite(Image.fromarray(out,'RGBA'))
pv.convert('RGB').resize((CW//2,768)).save(f'/tmp/b7d/out_{name}.png')
