import json,math
B=json.load(open('/tmp/phy/trio_buddy.json')); G=json.load(open('/tmp/phy/trio_bestie.json'))
GIRL=(281,858,24.8); BOY=(626,845,32)
TGT={'B':(320,900),'G':(616.4,837)}
def bez(p0,c,p2,e): return ((1-e)**2*p0[0]+2*e*(1-e)*c[0]+e*e*p2[0],(1-e)**2*p0[1]+2*e*(1-e)*c[1]+e*e*p2[1])
def over(p0,p2,cy,pad,rear,shield):
    dx=p2[0]-p0[0]
    if not rear or abs(dx)<1: return [(p0[0]+p2[0])/2,cy]
    f=shield; Y=f[1]-f[2]-40-pad; cols=[f[0]-f[2]-pad,f[0],f[0]+f[2]+pad]
    steep=any(0.9<=(x-p0[0])/dx<1 for x in cols)
    c=[p2[0] if steep else (p0[0]+p2[0])/2,cy]
    for x in cols:
        u=(x-p0[0])/dx
        if u<=0 or u>=1: continue
        e=1-math.sqrt(1-u) if steep else u
        if 0.02<e<0.98: c[1]=min(c[1],(Y-(1-e)**2*p0[1]-e*e*p2[1])/(2*e*(1-e)))
    return c
def ang(v): return -math.degrees(math.atan2(v[1],v[0]))
def out():
  R={}
  for side,C in (('B',B),('G',G)):
    shield=BOY if side=='B' else GIRL; T=TGT[side]
    for g,v in C.items():
        a=v['atk']; k=a['kind']; at=v['at']; an=v['anchor']; rear=v.get('depth',1)<1; s=at[2]
        seq=a['seq']; FI=[i for i,x in enumerate(seq) if len(x)>2 and x[2]=='fire']
        FI=FI[0] if FI else 0; ff=seq[FI][0]; ff=ff if isinstance(ff,str) else ff[0]
        q=a.get('from') or (a.get('hold') or {}).get(ff) or v.get('hand')
        r={'id':g,'kind':k,'fire':ff,'rear':rear,'q':q,'depth':v.get('depth',1)}
        if k=='punch': q=a['wrist']; r['q']=q; r['fistC']=a['fistC']
        if q is None: R[g]=r; continue
        to=lambda q:(at[0]+(q[0]-an[0])*s, at[1]+(q[1]-an[1])*s)
        p0=to(q); r['hand']=[round(p0[0]),round(p0[1])]
        d=math.dist(p0,T); r['straight']=round(ang((T[0]-p0[0],T[1]-p0[1])),1)
        if k=='throw':
            if a.get('atlas'): R0=a.get('r',20)*a['atlas']['scale']
            elif a.get('r'): R0=a['r']
            else: R0=30
            c=over(p0,T,min(p0[1],T[1])-a.get('arc',0.2)*d,R0,rear,shield)
            Tt=a.get('T',0.5); acc=(2*(p0[0]-2*c[0]+T[0])/Tt**2, 2*(p0[1]-2*c[1]+T[1])/Tt**2)
            r['start']=round(ang((c[0]-p0[0],c[1]-p0[1])),1); r['acc']=[round(acc[0]),round(acc[1])]
            r['accTilt']=round(math.degrees(math.atan2(acc[0],acc[1])),1) if acc[1]!=0 else None
            r['aimTip']=a.get('aim'); r['spin']=a.get('spin')
        elif k=='rush':
            gh=a['rush']['ghost']; gh=gh if isinstance(gh,list) else [gh]
            box=gh[0]['box']; w=(box[2]-box[0])*s*1.1; h=(box[3]-box[1])*s*1.1
            c=over(p0,T,(p0[1]+T[1])/2,max(w,h)/2,rear,shield); r['start']=round(ang((c[0]-p0[0],c[1]-p0[1])),1)
            r['ghostBoxes']=[x['box'] for x in gh]
        elif k=='whip':
            Q=a['whip']; c=over(p0,T,(p0[1]+T[1])/2,Q.get('amp',24)*1.2+Q.get('w',8)*s,rear,shield)
            arch=c[1]<(p0[1]+T[1])/2-1
            if arch: r['start']=round(ang((c[0]-p0[0],c[1]-p0[1])),1)
            else:
                dx,dy=T[0]-p0[0],T[1]-p0[1]; L=math.hypot(dx,dy); f=0.02
                pt=(p0[0]+dx*f, p0[1]+dy*f+math.sin(math.pi*f)*L*0.08*0.4); r['start']=round(ang((pt[0]-p0[0],pt[1]-p0[1])),1)
        elif k=='spray':
            c=over(p0,T,(p0[1]+T[1])/2,a['spray'].get('r',14)*2.8,rear,shield); r['start']=round(ang((c[0]-p0[0],c[1]-p0[1])),1)
        elif k=='punch':
            fr=to(a['fistC']); r['fist']=[round(fr[0]),round(fr[1])]
            r['forearm']=round(ang((fr[0]-p0[0],fr[1]-p0[1])),1)
            fz=(a['fist'][3]-a['fist'][1])*s*a.get('fistZ',1)/2
            cc=over(fr,T,(fr[1]+T[1])/2,fz,rear,shield); fx,fy=bez(fr,cc,T,1.0)
            L=math.hypot(fx-p0[0],fy-p0[1]); nx,ny=-(fy-p0[1])/L,(fx-p0[0])/L; sag=L*0.16*(-1 if ny<0 else 1)
            for wob in (0.08,):
                sag=L*wob*(-1 if ny<0 else 1); cx,cy=(p0[0]+fx)/2+nx*sag,(p0[1]+fy)/2+ny*sag
                up=over(p0,(fx,fy),cy,a['armW']*s,rear,shield)
                if up[1]<cy: cx,cy=up
                r['start']=round(ang((cx-p0[0],cy-p0[1])),1); r['tubeEnd']=round(ang((fx-cx,fy-cy)),1)
        elif k in('beam',):
            r['start']=r['straight']
        elif k=='slash':
            r['slashAng']=a['slash']['ang']
        elif k=='jet':
            r['start']='aim帧'
        R[g]=r
  return R
R=out(); json.dump(R,open('/tmp/phy/geo.json','w'),ensure_ascii=False)
for g,r in R.items(): print(g,{k:v for k,v in r.items() if k!='id'})
