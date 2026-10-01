"""精美1（P6 / P7）把重 build 过的图集接回 web/trio_buddy.js 里某个人的条目。

frames.py 重 build 时新帧可能把画布撑大，anchor 跟着变（Δ = 新 anchor − 旧 anchor）。cfg 里所有"格内像素"坐标都要平移同一个 Δ：
anchor、pivot、atk.hold 各帧、atk.from、flex 各框（x0, y0, x1, y1）、parts[].at 各帧的前两个数。at（屏幕坐标）不动。
sheet 的 cell / names 直接从新图集 json 抄。

用法（在 chashouji 下）：
  python3 v14/trio/buddy/p6int.py <编号> <图集名> [seq=<JS 数组>] [hold+=<帧>:<x>,<y>;<帧>:<x>,<y>] [part+=<帧>:<copy 帧>|<x>,<y>,<rot>;...]
  · 旧 anchor 从条目里读，新 anchor 从图集 json 读，自动算 Δ 并平移；
  · seq=…：替换 atk.seq（JS 字面量原样写进去）；
  · hold+=…：在 atk.hold 里加帧（新坐标系，不再平移）；
  · part+=…：给每个 parts[] 的 at 加帧——"<帧>:<已有帧>" 抄那一帧（平移后）的值，或直接给新坐标系的 x,y,rot。
打印 Δ 和改动前后的几行，供核对。"""
import json, re, sys

ROOT = '/workspace/art/chashouji/'
bid, name = sys.argv[1], sys.argv[2]
opt = dict(a.split('=', 1) for a in sys.argv[3:])
p = ROOT + 'web/trio_buddy.js'
s = open(p).read()
m = re.search(r"\n    %s: \{.*?\n    \},\n" % bid, s, re.S)
assert m, bid
E = m.group(0)
J = json.load(open(ROOT + 'web/assets/trio/%s.json' % name))
old = [float(v) for v in re.search(r"anchor: \[([\d.\-]+), ([\d.\-]+)\]", E).groups()]
dx, dy = round(J['anchor'][0] - old[0], 1), round(J['anchor'][1] - old[1], 1)
print(f'{bid} {name}: anchor {old} -> {J["anchor"]}  Δ = ({dx:+}, {dy:+})')

def num(v):
    v = round(v, 1)
    return str(int(v)) if v == int(v) else str(v)
def sh2(mt):                       # [x, y, ...] 前两个数平移
    xs = [x.strip() for x in mt.group(2).split(',')]
    xs[0] = num(float(xs[0]) + dx); xs[1] = num(float(xs[1]) + dy)
    return mt.group(1) + '[' + ', '.join(xs) + ']'
def sh4(box):                      # [x0, y0, x1, y1, ...] 前四个数平移
    xs = [x.strip() for x in box.split(',')]
    for k in range(4): xs[k] = num(float(xs[k]) + (dx if k % 2 == 0 else dy))
    return ', '.join(xs)

e = E
e = re.sub(r"(sheet: \{ src: '[^']+', )cell: \[\d+, \d+\], cols: \d+, names: \[[^\]]*\] \}",
           lambda mt: mt.group(1) + "cell: [%d, %d], cols: %d, names: [%s] }" % (J['cell'][0], J['cell'][1], J.get('cols', 4), ', '.join("'%s'" % f for f in J['frames'])), e)
e = re.sub(r"(anchor: )\[([^\]]*)\]", lambda mt: mt.group(1) + '[%s, %s]' % (num(J['anchor'][0]), num(J['anchor'][1])), e, count=1)
e = re.sub(r"(pivot: )\[([^\]]*)\]", sh2, e, count=1)
# atk.hold
def holdblock(mt):
    return mt.group(1) + re.sub(r"(\w+: )\[([^\]]*)\]", sh2, mt.group(2)) + mt.group(3)
e = re.sub(r"(hold: \{)([^}]*)(\})", holdblock, e)
e = re.sub(r"(\bfrom: )\[([^\]]*)\]", sh2, e)
# flex: { 帧: [[x0, y0, x1, y1, ...], ...], ... }
fm = re.search(r"flex: \{(.*?)\}(,|\s*\n)", e, re.S)
if fm:
    body = re.sub(r"\[\[?([\d.\-]+, [\d.\-]+, [\d.\-]+, [\d.\-]+)(?=,)", lambda mt: mt.group(0)[:mt.group(0).index(mt.group(1))] + sh4(mt.group(1)), fm.group(1))
    e = e[:fm.start(1)] + body + e[fm.end(1):]
# parts at
def partat(mt):
    return mt.group(1) + re.sub(r"(\w+: )\[([^\]]*)\]", sh2, mt.group(2)) + mt.group(3)
e = re.sub(r"(\bat: \{)([^}]*)(\})", partat, e)
if 'seq' in opt:
    am = re.search(r"atk: \{.*?(seq: )(\[\[.*?\]\]),", e, re.S)
    e = e[:am.start(2)] + opt['seq'] + e[am.end(2):]
if 'hold+' in opt:
    add = ', '.join('%s: [%s]' % (q.split(':')[0], ', '.join(q.split(':')[1].split(','))) for q in opt['hold+'].split(';'))
    e = re.sub(r"(hold: \{)([^}]*?)(\s*\})", lambda mt: mt.group(1) + mt.group(2).rstrip() + ', ' + add + ' }', e, count=1)
if 'part+' in opt:
    def addpart(mt):
        body = mt.group(2); out = []
        for q in opt['part+'].split(';'):
            f, v = q.split(':')
            if re.fullmatch(r'\w+', v):
                src = re.search(r"\b%s: (\[[^\]]*\])" % v, body).group(1); out.append('%s: %s' % (f, src))
            else: out.append('%s: [%s]' % (f, v))
        return mt.group(1) + body.rstrip() + ', ' + ', '.join(out) + ' ' + mt.group(3)
    e = re.sub(r"(\bat: \{)([^}]*?)\s*(\})", addpart, e)
s = s.replace(E, e)
open(p, 'w').write(s)
import difflib
for l in difflib.unified_diff(E.split('\n'), e.split('\n'), lineterm='', n=0):
    if l[:1] in '+-' and not l.startswith(('+++', '---')): print(l[:260])
