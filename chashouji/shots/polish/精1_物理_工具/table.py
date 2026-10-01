import json,math
rows={r['id']:r for r in json.load(open('/tmp/phy/judge.json'))}
exec(open('/tmp/phy/judge.py').read().split('rows=[]')[0])  # 取 clear_par / dif / 常量
NAME={}
for f in ('/tmp/buddy.json','/tmp/bestie.json'):
    try:
        for x in json.load(open(f)): NAME[x['id']]=x['name']
    except Exception: pass
ENERGY={'B15'}            # 发射的能量物：应走直线，不受重力
ACC_REF=1800
def req_throw(r,T,shield):
    p0=tuple(r['hand']); s=r['straight']; left=abs(s)>90
    # 从直线方向往上找：能到达且（后排）越过护脸框的最小初速方向，再加 8° 余量
    for k in range(1,90):
        th=nd(s+(-k if left else k)) if True else s
        th=nd(180-(abs(180-abs(s))*(1 if s<0 else -1))) if False else th
        reach,cl=clear_par(p0,th,T,shield)
        if reach and (cl or not r['rear']):
            el=k+8; return nd(s+(-el if left else el)), el
    return None,None
def eleva(th):  # 仰角（相对朝目标那侧的水平）
    return round(nd(180-th),1) if abs(th)>90 else round(th,1)
out=[]
for g,r in rows.items():
    k=r['kind']; side=g[0]; T=TG[side]; shield=BOY if side=='B' else GIRL
    d=r['diff']; cls=''; req=''; grade=''; note=''
    if k=='jet': grade='过'; cls='合格'; note='11 档 aim 帧按仰角选帧，喷嘴角 ≤ 2.5°（大动作 ≤ 6.3°）；水 / 雾按 G 受重力'
    elif k=='camera': grade='过'; cls='合格'; note='镜头处瞬时闪光，无飞行路径；照片按 700 px/s² 下落'
    elif g=='B5': grade='A'; cls='引擎 / 配置可解'; note='方向 0°~5° 合格，但残影起点 from (270, 28) 是蓄力帧举过头顶的手，出拳两帧里棍在 (≈10, 100) / (≈80, 215)，起点偏约 150 px'; req='atk.from 按帧写（hitA → 棍梢 ≈ (10, 100)，hitB → ≈ (80, 215)）'
    elif k=='slash':
        grade='A'; cls='引擎 / 配置可解'
        note=('剑往右下劈约 43°，斩痕弦线往右上约 58°，划向相反；斩痕在落点凭空出现，跟剑之间没有连接' if g=='G14' else '双刀从水平扫到左上约 60°（刀尖往上走），斩痕弦线右上约 34°、差约 26°；斩痕在落点凭空出现，与刀之间没有剑气连接')
        req=('slash.ang 改成顺劈向（弦线往右下约 45°，从右上往左下划）；剑尖（正指着他）甩出剑气飞过去再展开' if g=='G14' else 'slash.ang 顺刀尖走向（左上 ≈ 60°）；剑气从刀尖沿挥向飞出再展开')
    elif k in('beam','punch') or (k=='rush' and g in('B16','G4')) or g in ENERGY:
        if d is not None and d<=10: grade='过'; cls='合格'
        else:
            grade='A'; cls='需美术补帧'; tgt=r['start_used'] if r['film'] else r['straight']
            req=f'出手帧{"手臂 / 掌" if k!="rush" else "出拳 / 出腿"}指向 {round(tgt,0):g}°（仰角 {eleva(tgt)}°）'
            note={'beam':'光是直线，不能拐弯：只能让手臂指向目标','punch':'伸长的肢体必须沿前臂：只能让前臂指向目标','rush':'肢体残影应沿出拳 / 出腿方向飞：肢体要指向目标；残影还要沿路径转'}.get(k,'能量发射物走直线：指向必须对准目标')
            if g=='G4': note='hitA 竖直靴、hitB 水平靴，残影路径往右下 34°（轴向差 56° / 34°），残影不转；'+note
    elif k=='rush':   # B13 飞剑
        grade='A'; cls='引擎可解'; note='御剑：剑是独立飞行物，可以走路径；问题是剑身按图水平画、不转（剑身与路径差 63°）'; req='残影沿路径切线旋转（剑尖朝飞行方向）'
    elif k=='whip':
        if d<=10: grade='过'; cls='合格'
        else: grade='A'; cls='引擎可解'; note='绸带是软的：可以先沿手臂甩出去再落到目标（物理成立）'; req='带子第一节方向 = 手臂方向，弹簧链 / 三次贝塞尔弯向目标'
    elif k=='spray':
        grade='A'; cls='引擎可解'; note='酒雾是液体：沿嘴的朝向喷出、受重力下坠就能落到目标（目标在喷射线下方）'; req='雾团首段沿嘴的朝向（水平）喷出，按重力抛物线下坠'
    elif k=='throw':
        reach,cl=r['par']
        if d<=10 and r['id']!='B6': grade='过'; cls='合格'
        else:
            grade='A'
            if reach and cl: cls='引擎可解'; req=f'首段沿手的出手方向 {r["ref"]:g}°，按重力抛物线落到目标（射线在目标上方，物理可达{"、越过主角头顶" if r["rear"] else ""}）'
            else:
                th,el=req_throw(r,T,shield); cls='需美术补帧'
                why=f'沿手的出手方向（{r["ref"]:g}°）抛，目标（直线 {r["straight"]:g}°）在这条射线上方；重力只会让东西往下弯，到不了' if not reach else '沿手的方向抛会砸到主角脸上（越不过头顶）'
                note=why; req=f'出手帧（或补一张出手瞬间帧）手的运动方向 ≈ {round(th):g}°（仰角约 {eleva(th)}°，至少比直线高 {el}°）' if th is not None else '需重画出手'
    EXTRA={'G18':'另：长枪不走 aim，枪身与飞行方向差约 83°（精1 a_q5 格3~8），cfg 加 aim 让枪尖朝飞行方向',
           'G19':'另：火箭 spin 翻滚、有一段尾巴朝前倒着飞（精1 a_q6 格5~8），应走 aim',
           'G25':'另：针筒 spin 翻转、针头不朝前，应走 aim',
           'B13':'剑指出手帧本身水平，路径往左下 63°：剑转过来以后剑指和剑之间仍有 63° 差，若要零折角需补一张剑指斜下的帧（可选）'}
    if g in EXTRA: note=(note+'；' if note else '')+EXTRA[g]
    out.append(dict(r,grade=grade,cls=cls,req=req,note=note))
json.dump(out,open('/tmp/phy/final.json','w'),ensure_ascii=False)
from collections import Counter
print(Counter(o['cls'] for o in out))
for o in out: print(o['id'],o['grade'],o['cls'],o['diff'],o['req'][:60])
