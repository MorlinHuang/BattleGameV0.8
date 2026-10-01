# P6 方向版对比图：idle / wind / swing / release / thru / follow，swing、release 上标 P、R、P→R、肩→手与角度
import json, math
from PIL import Image, ImageDraw
J=json.load(open('/workspace/art/chashouji/web/assets/trio/B21_sakura.json')); cw,ch=J['cell']
A=Image.open('/workspace/art/chashouji/web/assets/trio/B21_sakura.webp').convert('RGBA')
P,R,S,T=(220,237),(135,24),(150,150),(32,14)       # 格内输出像素（手量，见回报）
ang=lambda a,b: math.degrees(math.atan2(-(b[1]-a[1]),b[0]-a[0]))
names=['idle','wind','swing','release','thru','follow']
W=Image.new('RGB',(cw*len(names),ch+40),(225,225,225)); d=ImageDraw.Draw(W)
for k,n in enumerate(names):
    i=J['frames'].index(n); c=A.crop((i%4*cw,i//4*ch,i%4*cw+cw,i//4*ch+ch))
    bg=Image.new('RGBA',c.size,(225,225,225,255)); bg.alpha_composite(c); W.paste(bg.convert('RGB'),(k*cw,40))
    d.text((k*cw+4,4),n,fill=(0,0,0))
    o=lambda p:(k*cw+p[0],40+p[1])
    dot=lambda p,col,t:(d.ellipse([o(p)[0]-5,o(p)[1]-5,o(p)[0]+5,o(p)[1]+5],outline=col,width=3),d.text((o(p)[0]+7,o(p)[1]-4),t,fill=col))
    if n=='swing':
        dot(P,(255,0,0),'P'); d.text((k*cw+4,18),f'P={P}',fill=(200,0,0))
    if n=='release':
        Pg=P                                   # 同一格坐标系（所有帧共用锚点）
        d.line([o(Pg),o(R)],fill=(255,0,0),width=3)
        a=math.atan2(R[1]-Pg[1],R[0]-Pg[0])
        for s in (0.45,-0.45): d.line([o(R),(o(R)[0]-18*math.cos(a+s),o(R)[1]-18*math.sin(a+s))],fill=(255,0,0),width=3)
        d.line([o(S),o(R)],fill=(0,90,255),width=3); dot(Pg,(255,0,0),'P'); dot(R,(255,0,0),'R'); dot(S,(0,90,255),'S')
        d.text((k*cw+4,18),f'P->R {ang(P,R):.1f} deg (need 105)   S->R {ang(S,R):.1f} deg',fill=(200,0,0))
    if n=='thru':
        dot(T,(0,140,0),'T'); d.text((k*cw+4,18),f'hand T={T}',fill=(0,120,0))
W.save('/workspace/art/chashouji/v14/trio/preview/B21_sakura_p6d.png')
print(ang(P,R),ang(S,R),W.size)
