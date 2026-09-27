import json, math, sys
L=json.load(open(sys.argv[1]))
FOOT=(156,459); MUZ=(522,63); BP=(136,184); WP=(161,71); TAIL=(71,57)
enter,exit_=0.55,0.45; H=(180,1195-198)
def ease(u): return 1-(1-u)**3
def pose(b):
    s=b['s']; t=b['t']; se=enter+b['spray']; top=-(FOOT[1]-MUZ[1]+120)*s
    sx=math.sin(t*0.9+b['ph'])*8*s; sy=math.sin(t*1.8+b['ph'])*4*s; bob=math.sin(t*2.2+b['ph'])*5*s
    if t<enter: return (H[0], top+(H[1]-top)*ease(t/enter), s)
    k=min(1,(t-enter)/0.3); bk=b['back']*(1-ease(min(1,(t-b['backT'])/enter))) if b['back'] else 0; x=H[0]+sx*k; y=H[1]+(sy+bob)*k+bk
    if t>se: u=min(1,(t-se)/exit_); return (x, y+(top-y)*u*u, s)
    return (x,y,s)
def at(p,q): return (p[0]+(q[0]-FOOT[0])*p[2], p[1]+(q[1]-FOOT[1])*p[2])
def turn(q,c,th):
    ph=-th; co,si=math.cos(ph),math.sin(ph); dx,dy=q[0]-c[0],q[1]-c[1]
    return (c[0]+dx*co-dy*si, c[1]+dx*si+dy*co)
def carried(p,q,th,b):
    bt=0.06*b['kick']-0.03*b['lean']
    return turn(turn(at(p,q),at(p,BP),bt),at(p,WP),th)
def pts(b):
    p=pose(b); th=b['aim']
    # foot belongs to lo layer: only whole rotation (no bt)
    foot=turn(at(p,FOOT),at(p,WP),th)
    return dict(foot=foot, muz=carried(p,MUZ,th,b), tail=carried(p,TAIL,th,b), head=carried(p,(250,40),th,b), pos=p)
