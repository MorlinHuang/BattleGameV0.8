# G17 正式页（绳在荡）漂移：绳子只在 HUD 下露 ~120 px，拟合角度误差 0.01 rad × 700 px = 7 px，改为直接量「绳子最下端」和「脚踝」的相对位置。
# 绳端：#8a6a44 附近颜色、y 150..250、x 40..300 里最低 12 行的质心（引擎把绳拴在 line [120,15] 那一点，绳端就是应在处）；
# 脚踝：图集那一帧的 85,0,150,90 块（alpha>0.9 做遮罩、平方差截 0.08）在绳端推算位置 ±14 px 内整像素平移匹配。
# 输出每格 (脚踝 − 绳端)；这一列在各格之间的变化 = 换帧漂移（绳子整体摆动两者一起动，抵消）。
import sys,json
import numpy as np
from PIL import Image
film=sys.argv[1]; R='/workspace/art/chashouji/web/assets/trio/'
m=json.load(open(R+'G17_mitsuri.json')); cw,ch=m['cell']; cols=m['cols']
AT=(150,240,1.06); ANC=(119.7,15.3); LINE=(120,15); s=AT[2]
at=np.array(Image.open(R+'G17_mitsuri.webp').convert('RGBA')).astype(np.float32)/255
F=np.array(Image.open(film+'.jpg').convert('RGB')).astype(np.float32)/255
fr=json.load(open(film+'.json')); box=(85,0,150,90); tgt=np.array([0x8a,0x6a,0x44])/255
out=[]
for c in range(12):
  f=[x.split(':')[1] for x in fr[c] if x.startswith('G17:')][0]; i=m['frames'].index(f)
  cell=Image.fromarray((at[(i//cols)*ch:(i//cols+1)*ch,(i%cols)*cw:(i%cols+1)*cw]*255).astype(np.uint8))
  cell=np.array(cell.resize((round(cw*s),round(ch*s)),Image.LANCZOS)).astype(np.float32)/255
  bx=[int(round(v*s)) for v in box]; T=cell[bx[1]:bx[3],bx[0]:bx[2]]; A=(T[...,3]>0.9).astype(np.float32)
  img=F[:, c*960:(c+1)*960]
  sub=img[150:250,40:300]; d=np.abs(sub-tgt).sum(-1)<0.16; ys,xs=np.nonzero(d)
  yb=ys.max(); k=ys>=yb-11; ex=40+xs[k].mean(); ey=150+yb
  X0=int(round(ex-(LINE[0]-bx[0])*s)); Y0=int(round(ey-(LINE[1]-bx[1])*s)); Rr=14
  best=None
  for dy in range(-Rr,Rr+1):
    for dx in range(-Rr,Rr+1):
      p=img[Y0+dy:Y0+dy+T.shape[0], X0+dx:X0+dx+T.shape[1]]
      if p.shape[:2]!=T.shape[:2]: continue
      e=(np.minimum(((p-T[...,:3])**2).sum(-1),0.08)*A).sum()/A.sum()
      if best is None or e<best[0]: best=(e,dx,dy)
  e,dx,dy=best; out.append((c+1,f,dx,dy,e))
  print(f'格{c+1:2d} {f:7s} 绳端 ({ex:6.1f},{ey:5.0f})  脚踝 − 绳端 dx {dx:+d} dy {dy:+d}  残差 {e:.4f}')
dxs=[o[2] for o in out]; dys=[o[3] for o in out]
print('dx 范围', min(dxs), max(dxs), ' dy 范围', min(dys), max(dys))
