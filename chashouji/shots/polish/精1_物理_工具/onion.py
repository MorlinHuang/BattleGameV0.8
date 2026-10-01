import json,math,sys
from PIL import Image, ImageDraw, ImageChops
B=json.load(open('/tmp/phy/trio_buddy.json')); G=json.load(open('/tmp/phy/trio_bestie.json')); C={**B,**G}
R=json.load(open('/tmp/phy/geo.json'))
def cell(g,fr):
    sh=C[g]['sheet']; cw,ch=sh['cell']; i=sh['names'].index(fr)
    im=Image.open('/tmp/phy/assets/'+sh['src'].split('/')[-1]).convert('RGBA')
    return im.crop(((i%sh['cols'])*cw,(i//sh['cols'])*ch,(i%sh['cols']+1)*cw,(i//sh['cols']+1)*ch))
def nxt(g):
    a=C[g]['atk']; seq=[x[0] if isinstance(x[0],str) else x[0][0] for x in a['seq']]
    FI=[i for i,x in enumerate(a['seq']) if len(x)>2 and x[2]=='fire'][0]
    return seq[FI], (seq[FI+1] if FI+1<len(seq) else C[g]['idle']['frame'])
def panel(g,S=1.5):
    f0,f1=nxt(g); a=cell(g,f0); b=cell(g,f1); cw,ch=a.size
    bg=Image.new('RGBA',a.size,(60,60,60,255))
    ga=a.copy(); r,gg,bb,al=ga.split(); al=al.point(lambda v:v*0.45); ga=Image.merge('RGBA',(r.point(lambda v:255),gg.point(lambda v:v//3),bb.point(lambda v:v//3),al))
    bg.alpha_composite(b); bg.alpha_composite(ga)
    t=bg.resize((int(cw*S),int(ch*S))); d=ImageDraw.Draw(t)
    for x in range(0,cw,25): d.line([(x*S,0),(x*S,ch*S)],fill=(255,255,0) if x%100==0 else ((0,200,255) if x%50==0 else (130,130,130)),width=1)
    for y in range(0,ch,25): d.line([(0,y*S),(cw*S,y*S)],fill=(255,255,0) if y%100==0 else ((0,200,255) if y%50==0 else (130,130,130)),width=1)
    for x in range(0,cw,50): d.text((x*S+2,2),str(x),fill=(255,255,255))
    for y in range(50,ch,50): d.text((2,y*S+2),str(y),fill=(255,255,255))
    q=R[g].get('q')
    if q: d.ellipse([q[0]*S-8,q[1]*S-8,q[0]*S+8,q[1]*S+8],outline=(0,255,0),width=3)
    d.rectangle([0,ch*S-18,260,ch*S],fill=(0,0,0)); d.text((4,ch*S-15),f'{g} red={f0}(fire) solid={f1}',fill=(0,255,255))
    return t
gs=sys.argv[2:]; ps=[panel(g) for g in gs]
cols=3; rows=(len(ps)+cols-1)//cols
W=max(p.width for p in ps); H=max(p.height for p in ps)
o=Image.new('RGB',(W*min(cols,len(ps)),H*rows),(0,0,0))
for k,p in enumerate(ps): o.paste(p,((k%cols)*W,(k//cols)*H))
o.save(sys.argv[1]); print(o.size)
