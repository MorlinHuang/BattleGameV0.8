import json,math
R=json.load(open('/tmp/phy/geo.json')); FO=json.load(open('/tmp/phy/follow.json'))
B=json.load(open('/tmp/phy/trio_buddy.json')); G=json.load(open('/tmp/phy/trio_bestie.json')); C={**B,**G}
GIRL=(281,858,24.8); BOY=(626,845,32); TG={'B':(320,900),'G':(616.4,837)}
def nd(a): return (a+180)%360-180
def dif(a,b): return abs(nd(a-b))
def elev(th,left): return nd(180-th) if left else th   # 仰角：朝目标那一侧水平为 0，往上为正
# 参照方向 (deg, +上, 180=左) 与来源
REF={
'B5':(180,'双节棍轴（hitA 水平）'),'B6':(132.3,'手位移 swing→throw'),'B7':(-135,'手位移 wind→swing'),'B8':(141.6,'手位移 wind→swing'),
'B9':(-167.7,'手位移 wind→swing'),'B10':(-109.5,'手位移 wind→swing'),'B11':(164,'手位移 wind→throw'),'B12':(180,'前臂（wrist→fistC）'),
'B13':(180,'剑身（残影图块水平）'),'B14':(-113,'手位移 wind→throw'),'B15':(180,'指向（手臂轴，发射类）'),'B16':(180,'出拳手臂轴'),
'B17':(180,'手臂轴（无前一帧手位）'),'B18':(-165,'手位移 wind→throw'),'B19':(180,'十字手横臂'),'B20':(180,'嘴的朝向'),
'B21':(-127.7,'手位移 swing→throw'),'B22':(175,'双掌前推轴'),'B23':(None,'斩痕'),'B24':(-175.6,'手位移 swing→throw'),
'B25':(-160.4,'手位移 raise→throw'),'B26':(-121.3,'手位移 swing→throw'),'B27':(178,'手位移 swing→throw'),'B28':(-114.9,'手位移 swing→throw'),
'B29':(180,'手臂轴（无前一帧手位）'),'B30':(-140,'手位移 wind→throw'),
'G4':(90,'腿影图块（hitA 竖直靴）'),'G5':(-2.5,'手位移 wind→release（出手帧 throw 时手已回收）'),'G6':(-20.6,'手位移 wind→throw'),'G7':(-16.8,'手位移 wind→throw'),
'G8':(-42,'手位移 wind→throw（在 wind 帧出手）'),'G9':(52,'举起的手臂轴'),'G10':(-7.3,'手位移 wind→throw（在 wind 帧出手）'),'G11':(22.3,'手位移 wind→throw'),
'G12':(0,'飞吻朝向（嘴 / 手）'),'G13':(18,'手臂轴'),'G14':(None,'斩痕'),'G15':(-20.4,'手位移 wind→throw'),'G16':(-53,'手位移 wind→throw'),
'G17':(-45,'倒挂手臂轴'),'G18':(-16.8,'手位移 wind→throw'),'G19':(-20.4,'手位移 wind→throw'),'G20':(-41.7,'手位移 wind→throw'),
'G21':(10.5,'手位移 wind→throw'),'G23':(1.5,'双掌前推轴'),'G24':(-4.9,'手位移 wind→throw'),'G25':(-10.6,'手位移 wind→throw'),
'G26':(3.6,'手位移 wind2→throw'),'G27':(27.3,'手位移 wind→throw'),'G28':(17,'手位移 wind→throw'),'G29':(6.1,'前臂 / 棒（wrist→fistC）'),'G30':(20,'握如意的手臂轴'),
}
# 实测（胶片）首段读数覆盖理论：(实测首段方向, 证据)
FILM={'B12':(-131.2,'pa_g1 格2（线上）'),'B22':(159.6,'pa_g1 格12（线上）'),'B19':(-118.7,'精1 b_g10 格8'),'B16':(-125,'精1 a_g3 格7、9（55~67° 下）'),'G9':(-31,'精1 a_q6 格10'),
'G13':(-46,'精1 b_q8 格2'),'G23':(39,'精1 a_q2 格11'),'G30':(69,'精1 b_q3 格3'),'G29':(33,'精1 a_q8 格11'),'G21':(56,'精1 a_q1 格8→10（50°、63°）'),
'G18':(62,'理论；精1 a_q5 格3~8 实测枪身横飞 83°'),'G17':(-43,'精1 c_q1 格6')}
def clear_par(p0,th,T,shield,pad=30):
    # 初速方向 th（屏幕角，+上）、过目标的抛物线（重力竖直），返回 [能到, 越过护脸框]
    vx,vy=math.cos(math.radians(th)),-math.sin(math.radians(th)); dx,dy=T[0]-p0[0],T[1]-p0[1]
    if vx*dx<=0: return False,False
    t1=dx/vx                      # 以 v=1 计的"时间"
    a=(dy-vy*t1)/(t1*t1)          # 需要的竖直加速度（屏幕 y 向下为正）
    if a<=0: return False,False   # 目标在射线上方：重力往下拉，到不了
    f=shield; Y=f[1]-f[2]-40-pad; ok=True
    for x in (f[0]-f[2]-pad,f[0],f[0]+f[2]+pad):
        t=(x-p0[0])/vx
        if 0<t<t1:
            y=p0[1]+vy*t+a*t*t
            if y>Y: ok=False
    return True,ok
rows=[]
for g in sorted(C,key=lambda k:(k[0],int(k[1:]))):
    r=R[g]; k=r['kind']; side=g[0]; T=TG[side]; shield=BOY if side=='B' else GIRL
    ref,src=REF.get(g,(None,''))
    st=r.get('start'); film=FILM.get(g)
    if film: st_used=film[0]
    else: st_used=st if isinstance(st,(int,float)) else None
    d=dif(st_used,ref) if (ref is not None and st_used is not None) else None
    rows.append(dict(id=g,kind=k,ref=ref,src=src,start=st,film=film,start_used=st_used,diff=None if d is None else round(d,1),straight=r.get('straight'),hand=r.get('hand'),rear=r['rear'],acc=r.get('acc'),follow=FO[g]))
    if k=='throw' and ref is not None:
        reach,cl=clear_par(tuple(r['hand']),ref,T,shield) ; rows[-1]['par']=(reach,cl if r['rear'] else True)
json.dump(rows,open('/tmp/phy/judge.json','w'),ensure_ascii=False)
for x in rows: print(x['id'],x['kind'],'ref',x['ref'],'start',x['start'],'used',x['start_used'],'diff',x['diff'],'straight',x['straight'],'par',x.get('par'))
