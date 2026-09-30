# B17 正式页（绳在荡）漂移：从画面量绳子角度 → 绳端（锚点）应在处；脚踝那块做平移匹配 → 实际处；差 = 漂移
import sys,json
import numpy as np
from PIL import Image
from scipy.signal import fftconvolve
film=sys.argv[1]; R='/workspace/art/chashouji/web/assets/trio/'
m=json.load(open(R+'B17_wolf.json')); cw,ch=m['cell']; cols=m['cols']
names=['idle','wind','throw','follow','plunge','bounce','settle','idle2']
AT=(830,370,1.05); ANC=(116.3,6.5); PIV=(116,-660)
s=AT[2]; px=AT[0]+(PIV[0]-ANC[0])*s; py=AT[1]+(PIV[1]-ANC[1])*s; L=np.hypot((ANC[0]-PIV[0]),(ANC[1]-PIV[1]))*s
at=np.array(Image.open(R+'B17_wolf.webp').convert('RGBA')).astype(np.float32)/255
F=np.array(Image.open(film+'.png').convert('RGB')).astype(np.float32)/255
fr=json.load(open(film+'.json'))
box=(85,0,150,90)
out=[]
for c in range(12):
  f=[x.split(':')[1] for x in fr[c] if x.startswith('B17:')][0]; i=m['frames'].index(f)
  cell=Image.fromarray((at[(i//cols)*ch:(i//cols+1)*ch,(i%cols)*cw:(i%cols+1)*cw]*255).astype(np.uint8))
  cell=np.array(cell.resize((round(cw*s),round(ch*s)),Image.LANCZOS)).astype(np.float32)/255
  bx=[int(v*s) for v in box]; T=cell[bx[1]:bx[3],bx[0]:bx[2]]; A=(T[...,3]>0.9).astype(np.float32)
  img=F[:, c*960:(c+1)*960]
  # 绳：#8a6a44 附近颜色，在 y 150..(锚点−20) 里每行取质心
  tgt=np.array([0x8a,0x6a,0x44])/255; ys=[];xs=[]
  for y in range(150,int(AT[1]-15),4):
    row=img[y,700:960]; d=np.abs(row-tgt).sum(-1); k=np.nonzero(d<0.18)[0]
    if len(k) and np.ptp(k)<8: ys.append(y); xs.append(700+k.mean())
  b,a=np.polyfit(ys,xs,1); th=np.arctan(b)            # x = a + b y
  # 绳端应在：从绳顶沿这条线走 L
  ex=px+L*np.sin(th); ey=py+L*np.cos(th)
  # 这一帧锚点在格内 ANC → 模板左上角应在 (ex-ANC.x*s+bx0, ey-ANC.y*s+by0)（忽略小角度对模板本身的转动）
  X0=int(round(ex-ANC[0]*s+bx[0])); Y0=int(round(ey-ANC[1]*s+bx[1])); Rr=12
  sub=img[max(0,Y0-Rr):Y0+T.shape[0]+Rr, X0-Rr:X0+T.shape[1]+Rr]
  best=None
  for dy in range(-Rr,Rr+1):
    for dx in range(-Rr,Rr+1):
      yy=Y0-Rr if Y0-Rr>=0 else 0
      p=sub[dy+Rr:dy+Rr+T.shape[0], dx+Rr:dx+Rr+T.shape[1]]
      if p.shape[:2]!=T.shape[:2]: continue
      e=(np.minimum(((p-T[...,:3])**2).sum(-1),0.08)*A).sum()/A.sum()
      if best is None or e<best[0]: best=(e,dx,dy)
  e,dx,dy=best; out.append((c+1,f,round(float(th),4),dx,dy,round(float(e),4)))
  print(f'格{c+1:2d} {f:7s} 绳角 {th:+.4f} rad  脚踝相对绳端 dx {dx:+d} dy {dy:+d}  残差 {e:.4f}')
print('最大', max(max(abs(o[3]),abs(o[4])) for o in out))
