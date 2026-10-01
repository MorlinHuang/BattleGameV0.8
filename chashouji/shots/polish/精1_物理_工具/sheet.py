import json,math,sys
from PIL import Image, ImageDraw
B=json.load(open('/tmp/phy/trio_buddy.json')); G=json.load(open('/tmp/phy/trio_bestie.json')); C={**B,**G}
R=json.load(open('/tmp/phy/geo.json'))
def cell(g,fr):
    sh=C[g]['sheet']; cw,ch=sh['cell']; i=sh['names'].index(fr)
    im=Image.open('/tmp/phy/assets/'+sh['src'].split('/')[-1]).convert('RGBA')
    return im.crop(((i%sh['cols'])*cw,(i//sh['cols'])*ch,(i%sh['cols']+1)*cw,(i//sh['cols']+1)*ch))
def frames(g):
    a=C[g]['atk']; seq=[x[0] if isinstance(x[0],str) else x[0][0] for x in a['seq']]
    FI=[i for i,x in enumerate(a['seq']) if len(x)>2 and x[2]=='fire']; FI=FI[0] if FI else 0
    pre=seq[FI-1] if FI>0 else None; post=seq[FI+1] if FI+1<len(seq) else None
    if a['kind']=='rush':
        f=a['seq'][FI][0]; f=[f] if isinstance(f,str) else list(f)
        return [seq[0]]+f+([post] if post else [])
    if a['kind']=='jet': return [seq[0],'aim3','aim0','aim8']
    return [f for f in (pre,seq[FI],post) if f]
def tile(g,fr,mark):
    t=cell(g,fr); cw,ch=t.size; S=2 if max(cw,ch)<300 else 1.4
    bg=Image.new('RGBA',t.size,(70,70,70,255)); bg.alpha_composite(t); t=bg.resize((int(cw*S),int(ch*S))); d=ImageDraw.Draw(t)
    for x in range(0,cw,20): d.line([(x*S,0),(x*S,ch*S)],fill=(255,0,0) if x%100==0 else (170,170,170),width=1)
    for y in range(0,ch,20): d.line([(0,y*S),(cw*S,y*S)],fill=(255,0,0) if y%100==0 else (170,170,170),width=1)
    for x in range(0,cw,100): d.text((x*S+2,2),str(x),fill=(255,255,0))
    for y in range(100,ch,100): d.text((2,y*S+2),str(y),fill=(255,255,0))
    r=R[g]; q=r.get('q')
    if mark and q:
        x,y=q[0]*S,q[1]*S; d.ellipse([x-7,y-7,x+7,y+7],outline=(0,255,0),width=3)
        for key,col in (('start',(255,40,40)),('straight',(255,230,0))):
            v=r.get(key)
            if isinstance(v,(int,float)):
                a=math.radians(v); d.line([(x,y),(x+math.cos(a)*160,y-math.sin(a)*160)],fill=col,width=3)
        if r.get('fistC'):
            f=r['fistC']; d.line([(x,y),(f[0]*S,f[1]*S)],fill=(0,200,255),width=3)
    d.text((4,ch*S-14),f'{g}:{fr}',fill=(0,255,255))
    return t
out=sys.argv[1]; gs=sys.argv[2:]; rows=[]
for g in gs:
    fs=frames(g); fire=R[g]['fire']
    ts=[tile(g,f,f==fire or (C[g]['atk']['kind']=='rush')) for f in fs]
    H=max(t.height for t in ts); W=sum(t.width for t in ts)
    row=Image.new('RGB',(W,H),(0,0,0)); x=0
    for t in ts: row.paste(t,(x,0)); x+=t.width
    rows.append(row)
W=max(r.width for r in rows); o=Image.new('RGB',(W,sum(r.height for r in rows)),(0,0,0)); y=0
for r in rows: o.paste(r,(0,y)); y+=r.height
sc=min(1,2400/W); o=o.resize((int(o.width*sc),int(o.height*sc))); o.save(out); print(out,o.size)
