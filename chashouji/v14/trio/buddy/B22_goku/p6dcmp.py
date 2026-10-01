# P6 方向版对比图（B22 气功波）：idle / wind / swing / release / thru / follow；release 标肩 S、掌心中点 R（出口点）与 S→R 角，swing 标两掌中心 P，thru 标肩→掌角
import json, math
from PIL import Image, ImageDraw
J=json.load(open('/workspace/art/chashouji/web/assets/trio/B22_goku.json')); cw,ch=J['cell']
A=Image.open('/workspace/art/chashouji/web/assets/trio/B22_goku.webp').convert('RGBA')
P=(94,169); S=(150,115); R=(26,66); TS=(187.5,120); TR=(70,75)      # 格内输出像素（手量，anchor [143.7, 314]）
ang=lambda a,b: math.degrees(math.atan2(-(b[1]-a[1]),b[0]-a[0]))
names=['idle','wind','swing','release','thru','follow']
W=Image.new('RGB',(cw*len(names),ch+44),(225,225,225)); d=ImageDraw.Draw(W)
for k,n in enumerate(names):
    i=J['frames'].index(n); c=A.crop((i%4*cw,i//4*ch,i%4*cw+cw,i//4*ch+ch))
    bg=Image.new('RGBA',c.size,(225,225,225,255)); bg.alpha_composite(c); W.paste(bg.convert('RGB'),(k*cw,44))
    d.text((k*cw+4,4),n,fill=(0,0,0))
    o=lambda p:(k*cw+p[0],44+p[1])
    def dot(p,col,t):
        x,y=o(p); d.ellipse([x-4,y-4,x+4,y+4],outline=col,width=2); d.text((x+6,y-12),t,fill=col)
    def ray(a,b,col,ext=60):        # 肩→掌连线，并沿方向往前延长（光束走向）
        d.line([o(a),o(b)],fill=col,width=2)
        th=math.atan2(b[1]-a[1],b[0]-a[0]); e=(b[0]+ext*math.cos(th),b[1]+ext*math.sin(th))
        for t in range(0,ext,8): d.line([(o(b)[0]+t*math.cos(th),o(b)[1]+t*math.sin(th)),(o(b)[0]+(t+4)*math.cos(th),o(b)[1]+(t+4)*math.sin(th))],fill=col,width=1)
    if n=='swing':
        dot(P,(255,0,0),'P'); d.text((k*cw+4,18),f'palms P={P}',fill=(200,0,0))
    if n=='release':
        ray(S,R,(0,90,255)); dot(S,(0,90,255),'S'); dot(R,(255,0,0),'R')
        d.text((k*cw+4,18),f'S->R {ang(S,R):.1f} deg (need 160+-10)',fill=(0,60,200))
        d.text((k*cw+4,30),f'exit R={R}',fill=(200,0,0))
    if n=='thru':
        ray(TS,TR,(0,140,0)); dot(TS,(0,140,0),'S'); dot(TR,(0,140,0),'T')
        d.text((k*cw+4,18),f'S->T {ang(TS,TR):.1f} deg',fill=(0,120,0))
W.save('/workspace/art/chashouji/v14/trio/preview/B22_goku_p6d.png')
print('release',ang(S,R),'thru',ang(TS,TR),'P->R',ang(P,R),W.size)
