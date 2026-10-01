"""把 trio_bestie.js 里一个人的格内坐标整体平移 (dx, dy)（addframes.py 给格子左 / 上加边以后用：格子原点挪了，格内坐标都要跟着挪）。
屏幕坐标（cfg.at、enter.from / ends、ropes 的屏幕点）和挂件图自己的像素（parts[].pivot）不动。
平移的字段：anchor、和 anchor 同一行的 pivot、hold 各帧、atk.from、parts[].at（按帧写 / 一个点）、flex 框、rush ghost 的 box、punch 的 fist / fistC / wrist。
只改代码不改注释；改完用 node 把改前改后的 cfg 逐项比，打印所有变了的数值路径（应该只有上面这些、而且都是 +dx / +dy）。
用法（在 chashouji 下）：python3 v14/trio/bestie/tools/shiftcfg.py G5 dx dy"""
import json, re, subprocess, sys

P = 'web/trio_bestie.js'
g, dx, dy = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
fmt = lambda v: ('%d' % v) if float(v).is_integer() else ('%.1f' % v).rstrip('0').rstrip('.')
pt = lambda m: '[%s, %s' % (fmt(float(m.group(1)) + dx), fmt(float(m.group(2)) + dy))
NUM = r'(-?\d+(?:\.\d+)?)'
PAIR = re.compile(r'\[' + NUM + r', ' + NUM)
BOX = re.compile(r'\[' + NUM + r', ' + NUM + r', ' + NUM + r', ' + NUM)
box = lambda m: '[%s, %s, %s, %s' % (fmt(float(m.group(1)) + dx), fmt(float(m.group(2)) + dy), fmt(float(m.group(3)) + dx), fmt(float(m.group(4)) + dy))


def pre_pair(seg, prefix):
    """prefix 后面紧跟的 [x, y …] 平移"""
    return re.sub('(' + prefix + r')\[' + NUM + ', ' + NUM, lambda m: m.group(1) + '[%s, %s' % (fmt(float(m.group(2)) + dx), fmt(float(m.group(3)) + dy)), seg)


def code(seg):
    seg = pre_pair(seg, r'anchor: ')
    seg = pre_pair(seg, r'anchor: \[[^\]]*\], at: \[[^\]]*\], pivot: ')
    seg = re.sub(r'(hold: \{)([^}]*)(\})', lambda m: m.group(1) + PAIR.sub(pt, m.group(2)) + m.group(3), seg)
    seg = pre_pair(seg, r'(?:wrist|fistC|from): ')
    seg = re.sub(r'((?:fist|box): )' + BOX.pattern, lambda m: m.group(1) + '[%s, %s, %s, %s' % (fmt(float(m.group(2)) + dx), fmt(float(m.group(3)) + dy), fmt(float(m.group(4)) + dx), fmt(float(m.group(5)) + dy)), seg)
    seg = re.sub(BOX.pattern + r"(, '[tblr]')", lambda m: box(m) + m.group(5), seg)                 # flex 框
    # parts[].at：{ 帧: [x, y, 角], ... } 或 [x, y, 角]（只在 src 开头的挂件对象里）
    seg = re.sub(r"(src: '[^']*'[^{}]*?at: )(\{[^}]*\}|\[[^\]]*\])", lambda m: m.group(1) + PAIR.sub(pt, m.group(2)), seg)
    return seg


s = open(P).read()
m = re.search(r'^    %s: \{.*?^    \},\n' % g, s, re.S | re.M)
blk = m.group(0)
if 'enter: {' in blk and re.search(r"enter: \{[^}]*(ends|touch|line):", blk): raise SystemExit('enter 里有 ends / touch / line，先手工核对再平移')
parts = re.split(r'(/\*.*?\*/|//[^\n]*)', blk, flags=re.S)
new = ''.join(p if i % 2 else code(p) for i, p in enumerate(parts))
open('/tmp/_shift_old.js', 'w').write(s)
s2 = s[:m.start()] + new + s[m.end():]
open('/tmp/_shift_new.js', 'w').write(s2)
js = r'''
const vm=require('vm'),fs=require('fs');
const ld=f=>{const c={};vm.createContext(c);vm.runInContext('var ROPE={};'+fs.readFileSync(f,'utf8')+';this.T=TRIO_BESTIE;',c);return c.T.cast[process.argv[1]]};
const a=ld('/tmp/_shift_old.js'),b=ld('/tmp/_shift_new.js'),out=[];
const walk=(x,y,p)=>{if(typeof x==='number'){if(x!==y)out.push(p+' '+x+' -> '+y+' ('+(y-x>0?'+':'')+(Math.round((y-x)*100)/100)+')');return}
 if(x&&typeof x==='object')for(const k of new Set([...Object.keys(x),...Object.keys(y||{})]))walk(x[k],(y||{})[k],p+'.'+k)};
walk(a,b,'');console.log(out.join('\n'));
'''
r = subprocess.run(['node', '-e', js, g], capture_output=True, text=True)
if r.returncode: raise SystemExit(r.stderr)
print(r.stdout)
if '--write' in sys.argv: open(P, 'w').write(s2); print('已写入', P)
else: print('（预演：加 --write 才写回）')
