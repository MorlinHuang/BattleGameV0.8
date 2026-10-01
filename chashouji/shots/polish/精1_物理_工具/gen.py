import json
F=json.load(open('/tmp/phy/final.json')); EV=json.load(open('/tmp/phy/ev.json'))
NM={x['id']:(x['name'].split('（')[0],x['era']) for f in ('/tmp/buddy.json','/tmp/bestie.json') for x in json.load(open(f))}
KIND={'throw':'抛物','jet':'喷射','rush':'连打残影','beam':'光束','punch':'伸长肢体','whip':'绸带 / 鞭','spray':'喷雾','slash':'斩痕','camera':'拍照'}
OLDFILM=set(json.load(open('/tmp/phy/old.json')))
TINY={'B6':'硬币太小，目测未见','B10':'麻将牌太小，目测未见'}
def evs(g):
    h=EV.get(g,[])
    if not h: return '线上胶片未取到（见 4.0 末条）；图集叠影 / 网格图见 4.1'
    t='；'.join(f'{("线上 " if n.startswith("p") else "精1 ")}{n} 格{i[0]}~{i[-1]}' for n,i in h[:2])
    if g in OLDFILM and not any(n.startswith('p') for n,_ in h): t='线上胶片未取到；'+t+'（改帧前的旧配置胶片：引擎路径公式未变，问题同类）'
    return t
def row(o):
    g=o['id']; n,era=NM.get(g,('',''))
    k=o['kind']; d=o['diff']
    origin={'jet':'喷嘴（aim.nozzle）','slash':'无（落点凭空出现）','camera':'镜头'}.get(k,'在手 / 道具出口')
    if g=='B5': origin='**偏约 150 px**（蓄力帧的手）'
    if g=='G5': origin='在手，但出手帧选晚了一帧（手已回收）'
    ref='—' if o['ref'] is None else f"{o['ref']:g}°（{o['src']}）"
    if o['start_used'] is None: st='—'
    else: st=f"{o['start_used']:g}°（{'实测 '+o['film'][1] if o['film'] else '理论'}）"
    dd='—' if d is None else f'**{d:g}°**' if d>10 else f'{d:g}°'
    if g=='G4': dd='**56° / 34°**（轴向，hitA / hitB）'
    if g=='B23': dd='**约 26°**'
    if g=='G14': dd='**约 100°，划向反**'
    kink={'throw':dd,'beam':dd,'whip':dd,'spray':dd,'jet':'0°','camera':'—'}.get(k,'')
    if k=='punch': kink=f"腕部 {dd} + 管身再弯约 18°（理论）"
    if k=='rush': kink='残影朝向 '+(dd if g!='B5' else '0°~5°（方向对，起点错）')
    if k=='slash': kink='— （与挥砍无连接）'
    arm='**否**（前臂水平 / 近水平，管子斜出）' if k=='punch' else '—'
    if g=='B15': grav='现在走抛物线（指尖发射的能量球应走直线，不该下坠）'
    elif k=='throw':
        a=o['acc']; grav=f"是（竖直，{a[1]} px/s² ≈ {a[1]/1800:.1f}× 引擎下落 g）"
    elif k=='jet': grav='是（水滴 / 雾按 G 下坠）'
    elif k=='spray': grav='轨迹是抛物线，但首段斜着往下出、不沿嘴'
    else: grav='—（直线 / 软带 / 冲刺，不适用）'
    after=('未见残留' + (f'（{TINY[g]}）' if g in TINY else '')) if k=='throw' else '—'
    f0,f1,xr=o['follow'][0],o['follow'][1],o['follow'][2]
    fol=f'{f0}→{f1}，剪影差 {xr:.2f}'
    if xr==0: fol=f'**无跟随帧**（{f0} 出手后直接停在 {f1}）'
    elif xr<0.15: fol=f'{f0}→{f1}，剪影差 {xr:.2f}（**跟随几乎不动**）'
    if g=='B25': fol='throw→idle（**没有 follow**，扔完直接回待机）'
    fix='；'.join(x for x in (o['req'],o['note']) if x)
    return f"| {g} {n}（{era}） | {KIND.get(k,k)} | {origin} | {ref} | {st} | {dd} | {kink} | {arm} | {grav} | {after} | {fol} | {'**A**' if o['grade']=='A' else '过'} | {o['cls']} | {fix or '—'} | {evs(g)} |"
H='| 角色 | 类型 | 出手起点 | 参照方向（来源） | 首段方向 | 首段差 | 最大折角 | 伸长肢体沿前臂 | 抛物受重力 | 出手后手上 | 后坐 / 跟随 | 判 | 结论 | 改法（所需角度） | 胶片证据 |\n|'+'---|'*15
out=[]
for side,t in (('B','### 4.2 哥们 30 人'),('G','### 4.3 闺蜜 30 人')):
    out.append(t+'\n\n'+H)
    for o in sorted([o for o in F if o['id'][0]==side],key=lambda o:int(o['id'][1:])): out.append(row(o))
    out.append('')
open('/tmp/phy/rows.md','w').write('\n'.join(out))
# 汇总
def lst(c): return [o for o in F if o['cls']==c]
S=[]
S.append('### 4.4 汇总\n')
S.append(f"- 合格 {len(lst('合格'))} 人：" + '、'.join(o['id'] for o in lst('合格')))
eng=lst('引擎可解')+lst('引擎 / 配置可解')
S.append(f"- **引擎可解 {len(eng)} 人**（改路径 / 朝向 / 配置即可，不用重画）：\n\n| 角色 | 首段差 | 引擎要做的事 |\n|---|---|---|")
for o in sorted(eng,key=lambda o:(o['id'][0],int(o['id'][1:]))):
    S.append(f"| {o['id']} {NM[o['id']][0]} | {'—' if o['diff'] is None else str(o['diff'])+'°'} | {o['req']} |")
art=lst('需美术补帧')
S.append(f"\n- **需美术补帧 {len(art)} 人**（引擎改路径在物理上做不到：光不能拐弯、伸长的手臂必须沿前臂、物体受重力只能往下弯）：\n\n| 角色 | 首段差 | 所需出手角度（屏幕角，0° = 水平向右、180° = 水平向左、正 = 往上） | 为什么引擎解不了 |\n|---|---|---|---|")
for o in sorted(art,key=lambda o:(o['id'][0],int(o['id'][1:]))):
    dd='56° / 34°（轴向）' if o['id']=='G4' else f"{o['diff']}°"
    S.append(f"| {o['id']} {NM[o['id']][0]} | {dd} | {o['req']} | {o['note']} |")
open('/tmp/phy/sum.md','w').write('\n'.join(S)+'\n')
print(len(F))
