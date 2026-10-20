# P6 方向版对比图（B7 甩红纸条，所需 176°）：idle / wind / swing / release / thru / follow；swing 标握点 P，release 标 R、肩 S，P→R 箭头与 S→R 连线
import json, math
from PIL import Image, ImageDraw
J=json.load(open('/workspace/art/chashouji/web/assets/trio/B7_f4.json')); cw,ch=J['cell']
A=Image.open('/workspace/art/chashouji/web/assets/trio/B7_f4.webp').convert('RGBA')
P=(277,88); R=(20,85); S=(170,92); T=(38,160)        # 格内输出像素（手量，anchor [206.0, 453.1]）
NEED=176
ang=lambda a,b: math.degrees(math.atan2(-(b[1]-a[1]),b[0]-a[0]))%360
names=['idle','wind','swing','release','thru','follow']
W=Image.new('RGB',(cw*len(names),ch+48),(225,225,225)); d=ImageDraw.Draw(W)
for k,n in enumerate(names):
    i=J['frames'].index(n); c=A.crop((i%4*cw,i//4*ch,i%4*cw+cw,i//4*ch+ch))
    bg=Image.new('RGBA',c.size,(225,225,225,255)); bg.alpha_composite(c); W.paste(bg.convert('RGB'),(k*cw,48))
    d.text((k*cw+4,4),n,fill=(0,0,0))
    o=lambda p:(k*cw+p[0],48+p[1])
    def dot(p,col,t):
        x,y=o(p); d.ellipse([x-4,y-4,x+4,y+4],outline=col,width=2); d.text((x+6,y-14),t,fill=col)
    def arrow(a,b,col):
        d.line([o(a),o(b)],fill=col,width=2); th=math.atan2(b[1]-a[1],b[0]-a[0]); x,y=o(b)
        for s in (2.6,-2.6): d.line([(x,y),(x-12*math.cos(th+s),y-12*math.sin(th+s))],fill=col,width=2)
    if n=='swing':
        dot(P,(255,0,0),'P'); dot(R,(255,120,120),'R'); arrow(P,R,(255,0,0))
        d.text((k*cw+4,18),f'P{P} -> R{R}',fill=(200,0,0)); d.text((k*cw+4,32),f'P->R {ang(P,R):.1f} deg (need {NEED}+-10)',fill=(200,0,0))
    if n=='release':
        d.line([o(S),o(R)],fill=(0,90,255),width=2); dot(S,(0,90,255),'S'); dot(R,(255,0,0),'R'); dot(P,(255,120,120),'P'); arrow(P,R,(255,120,120))
        d.text((k*cw+4,18),f'S{S}->R{R} {ang(S,R):.1f} deg',fill=(0,60,200)); d.text((k*cw+4,32),f'need {NEED}+-10; P->R {ang(P,R):.1f}',fill=(0,60,200))
    if n=='thru':
        dot(T,(0,140,0),'T'); d.text((k*cw+4,18),f'hand T={T}',fill=(0,120,0))
W.save('/workspace/art/chashouji/v14/trio/preview/B7_f4_p6d.png')
print('P->R',ang(P,R),'S->R',ang(S,R),W.size)
