import json,glob,os
B=json.load(open('/tmp/phy/trio_buddy.json')); G=json.load(open('/tmp/phy/trio_bestie.json')); C={**B,**G}
CHANGED={'B6','B7','B8','B9','B10','B21','B22','B23','B24','B26','B27','B28','G5'}
def firefr(g):
    a=C[g]['atk']; seq=[x[0] if isinstance(x[0],str) else x[0][0] for x in a['seq']]
    FI=[i for i,x in enumerate(a['seq']) if len(x)>2 and x[2]=='fire']; FI=FI[0] if FI else 0
    fs={seq[FI]}
    if FI+1<len(seq): fs.add(seq[FI+1])
    if a['kind']=='rush':
        f=a['seq'][FI][0]; fs|=({f} if isinstance(f,str) else set(f))
    if a['kind']=='jet': fs={'aim%d'%i for i in range(11)}
    return fs
ev={}; OLD=set()
for g in C:
    fs=firefr(g); hits=[]
    dirs=['/tmp/phy/f'] if g in CHANGED else ['/tmp/phy/f','/tmp/p1/f']
    for d in dirs:
        for j in sorted(glob.glob(d+'/*.json')):
            if 'faces' in j: continue
            nm=os.path.basename(j)[:-5]
            if d=='/tmp/p1/f' and nm.startswith('p'): continue
            try: T=json.load(open(j))
            except Exception: continue
            idx=[i+1 for i,r in enumerate(T) for x in r if x.split(':')[0]==g and x.split(':')[1] in fs]
            if idx: hits.append((nm,idx))
    if g in CHANGED and not hits:
        for j in sorted(glob.glob('/tmp/p1/f/*.json')):
            if 'faces' in j: continue
            nm=os.path.basename(j)[:-5]; T=json.load(open(j))
            idx=[i+1 for i,r in enumerate(T) for x in r if x.split(':')[0]==g and x.split(':')[1] in ({'throw','follow','wind'})]
            if idx: hits.append((nm,idx)); OLD.add(g)
    ev[g]=hits
json.dump(ev,open('/tmp/phy/ev.json','w')); json.dump(sorted(OLD),open('/tmp/phy/old.json','w'))
print({g:[(n,i[0],i[-1]) for n,i in ev[g]][:2] for g in sorted(CHANGED)})
