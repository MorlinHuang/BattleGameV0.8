const fs=require('fs');
const SIDE=process.argv[2]||'bestie',P=SIDE==='bestie'?'G':'B',VAR=SIDE==='bestie'?'TRIO_BESTIE':'TRIO_BUDDY';const src=fs.readFileSync('web/trio_'+SIDE+'.js','utf8');
global.ROPE={};
const vm=require('vm');const ctx={ROPE:{},console};vm.createContext(ctx);
vm.runInContext(src.replace(new RegExp('^const '+VAR,'m'),'this.TRIO_BESTIE'),ctx);
const T=ctx.TRIO_BESTIE;
// header comments
const head={},lines=src.split('\n');
lines.forEach(l=>{const m=l.match(/^\s{4}([GB]\d+): \{\s*\/\/\s*(.*)$/);if(m&&m[1][0]===P)head[m[1]]=m[2];});
// enter/atk comment: the /* */ block directly preceding 'enter:' and 'atk:' within char block
function blockOf(id){const i=src.search(new RegExp('^\\s{4}'+id+': \\{','m'));const j=src.slice(i+5).search(/^\s{4}[GB]\d+: \{|^\s{2}\},?\s*$/m);return src.slice(i,j<0?undefined:i+5+j);}
function cmtBefore(b,key){const k=b.search(new RegExp('^\\s+'+key+':','m'));if(k<0)return'';const pre=b.slice(0,k).trimEnd();if(!pre.endsWith('*/'))return'';const s=pre.lastIndexOf('/*');return pre.slice(s+2,-2).replace(/\s+/g,' ').trim();}
const roster={};
fs.readFileSync('docs/三人组30人名单.md','utf8').split('\n').forEach(l=>{const c=l.split('|').map(s=>s.trim());if(new RegExp('^'+P+'\\d+$').test(c[1]||'')&&!roster[c[1]])roster[c[1]]={slot:c[2],name:c[3],era:c[4],enter:c[5],atk:c[6]};});
const sign={};
fs.readFileSync('shots/审查_签字.md','utf8').split('\n').forEach(l=>{const c=l.split('|').map(s=>s.trim());if(new RegExp('^'+P+'\\d+$').test(c[1]||'')&&c[4]&&/签|打回|待审/.test(c[4]))sign[c[1]]={st:c[4],batch:c[5].replace(/\*/g,''),note:c[6]};});
const grp={};T.groups.forEach((g,i)=>{for(const k of['ground','top','floor'])grp[g[k]]=`${i+1}·${g.name}`;});
const slotOf={ground:'后排地面',top:'上方',floor:'前景地板'};
const out=[];
for(let n=1;n<=30;n++){const id=P+n,c=T.cast[id];if(!c){out.push({id,missing:1});continue;}
 const b=blockOf(id);const seq=s=>s?s.map(x=>x[0]).join('→'):'';
 const atk=c.atk||{};const props=[];
 if(atk.atlas)props.push(atk.atlas.src.replace('assets/trio/',''));if(atk.prop)props.push(atk.prop.replace(/^assets\//,''));
 const parts=(c.parts||[]).map(p=>p.src.replace('assets/trio/','')+(p.fixed?'(场景层)':'')+(p.ammo?'(随出手消失)':''));
 out.push({id,group:grp[id]||'',slot:roster[id]?.slot,name:roster[id]?.name,era:roster[id]?.era,
  head:head[id]||'',sheet:c.sheet.src.replace('assets/trio/',''),frames:c.sheet.names.join(' '),
  at:JSON.stringify(c.at),enterKind:(typeof c.enter==='string'?c.enter:c.enter?.kind),enterSeq:seq(c.enter?.seq),enterNote:cmtBefore(b,'enter'),
  idle:(c.idle?.frame||'')+(c.flex?' +局部摆动flex':'')+(c.swing?' +秋千摆':'')+(c.ropes?' +引擎画绳':''),
  atkKind:atk.kind,atkSeq:seq(atk.seq),atkNote:cmtBefore(b,'atk'),item:atk.item||'',props:props.join('，'),parts:parts.join('，'),recipe:c.recipe,onHit:atk.onHit||'',
  rEnter:roster[id]?.enter,rAtk:roster[id]?.atk,sign:sign[id]});
}
fs.writeFileSync('/tmp/'+SIDE+'.json',JSON.stringify(out,null,1));
console.log(out.filter(o=>o.missing).map(o=>o.id), out.length);
