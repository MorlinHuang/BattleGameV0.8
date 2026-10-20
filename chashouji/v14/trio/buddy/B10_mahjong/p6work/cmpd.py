# 对比图 preview/B10_mahjong_p6d.png：idle / wind / swing / release / thru / follow（输出像素、浅灰底），标 P、R、P→R 箭头、肩→手
import json, math, sys
from PIL import Image, ImageDraw, ImageFont
W='/workspace/art/chashouji/web/assets/trio/'; name='B10_mahjong'
P=tuple(map(float,sys.argv[1].split(','))); R=tuple(map(float,sys.argv[2].split(','))); S=tuple(map(float,sys.argv[3].split(','))); T=tuple(map(float,sys.argv[4].split(',')))
j=json.load(open(W+name+'.json')); cw,ch=j['cell']; A=Image.open(W+name+'.webp').convert('RGBA')
ang=lambda a,b: math.degrees(math.atan2(-(b[1]-a[1]),b[0]-a[0]))
th1,th2=ang(P,R),ang(S,R)
names=['idle','wind','swing','release','thru','follow']; Z=2
try: F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
except Exception: F=ImageFont.load_default()
out=Image.new('RGB',(cw*Z*len(names),ch*Z+40),(228,228,228)); d=ImageDraw.Draw(out)
def arrow(d,a,b,col):
    d.line([a,b],fill=col,width=4); t=math.atan2(b[1]-a[1],b[0]-a[0])
    for s in (2.6,-2.6): d.line([b,(b[0]+18*math.cos(t+s),b[1]+18*math.sin(t+s))],fill=col,width=4)
for k,f in enumerate(names):
    i=j['frames'].index(f); c=A.crop((i%4*cw,i//4*ch,i%4*cw+cw,i//4*ch+ch)).resize((cw*Z,ch*Z),Image.LANCZOS)
    ox=k*cw*Z; out.paste(c,(ox,40),c)
    g=lambda p:(ox+p[0]*Z,40+p[1]*Z)
    d.text((ox+8,8),f,fill=(0,0,0),font=F)
    if f=='swing':
        x,y=g(P); d.ellipse([x-7,y-7,x+7,y+7],outline=(220,0,0),width=4); d.text((x+10,y+8),'P (%.0f,%.0f)'%P,fill=(220,0,0),font=F)
        x2,y2=g(R); arrow(d,(x,y),(x2,y2),(220,0,0)); d.text((ox+8,36+ch*Z-60),'P→R %.1f° (所需 162°)'%th1 if False else 'P->R %.1f deg (need 162)'%th1,fill=(220,0,0),font=F)
    if f=='release':
        x,y=g(R); d.ellipse([x-7,y-7,x+7,y+7],outline=(220,0,0),width=4); d.text((x-20,y+14),'R (%.0f,%.0f)'%R,fill=(220,0,0),font=F)
        xp,yp=g(P); arrow(d,(xp,yp),(x,y),(220,0,0))
        xs,ys=g(S); d.line([(xs,ys),(x,y)],fill=(0,90,230),width=4); d.ellipse([xs-7,ys-7,xs+7,ys+7],outline=(0,90,230),width=4)
        d.text((xs+10,ys+10),'S (%.0f,%.0f)'%S,fill=(0,90,230),font=F)
        d.text((ox+8,36+ch*Z-90),'P->R %.1f deg'%th1,fill=(220,0,0),font=F)
        d.text((ox+8,36+ch*Z-60),'S->R %.1f deg (need 162)'%th2,fill=(0,90,230),font=F)
    if f=='thru':
        x,y=g(T); d.ellipse([x-7,y-7,x+7,y+7],outline=(0,140,0),width=4); d.text((x+10,y+10),'hand (%.0f,%.0f)'%T,fill=(0,140,0),font=F)
out.save('/workspace/art/chashouji/v14/trio/preview/B10_mahjong_p6d.png')
print('P->R %.1f (diff %.1f)  S->R %.1f (diff %.1f)'%(th1,th1-162,th2,th2-162))
