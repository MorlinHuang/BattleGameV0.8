"""精美1 改前 / 改后胶片对比：同一个人单召、出手 1.4 秒起 60 ms 一格（ammosc=1）。
上一行改前、下一行改后，每格截这个人所在的那一块（按 cfg at 和图集剪影包围盒算），格上标帧名。
用法：python3 p6cmp.py <编号> <改前胶片.png> <改后胶片.png> <输出.jpg>"""
import json, re, sys
from PIL import Image, ImageDraw

ROOT = '/workspace/art/chashouji/'
bid, fb, fa, out = sys.argv[1:5]
s = open(ROOT + 'web/trio_buddy.js').read()
E = re.search(r"\n    %s: \{.*?\n    \},\n" % bid, s, re.S).group(0)
src = re.search(r"sheet: \{ src: '([^']+)'", E).group(1)
ax, ay, sc = [float(v) for v in re.search(r"\bat: \[([\d.]+), ([\d.]+), ([\d.]+)\]", E).groups()]
J = json.load(open(ROOT + 'web/' + src[:-5] + '.json'))
cw, ch = J['cell']; anx, any_ = J['anchor']
# 这个人在屏幕上的框：格子整块（锚点对齐）再往外放 40 px
x0, y0 = ax - anx * sc - 40, ay - any_ * sc - 40
x1, y1 = x0 + cw * sc + 80, y0 + ch * sc + 80
x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(960, int(x1)), min(1707, int(y1))
w, h = x1 - x0, y1 - y0
k = min(1.0, 200 / w)
tw, th = int(w * k), int(h * k)
rows = []
for f in (fb, fa):
    im = Image.open(f).convert('RGB')
    try: names = [next((t.split(':')[1] for t in r if t.startswith(bid + ':')), '-') for r in json.load(open(f[:-4] + '.json'))]
    except Exception: names = ['?'] * 12
    row = Image.new('RGB', (tw * 12, th + 18), (255, 255, 255))
    for i in range(12):
        c = im.crop((i * 960 + x0, y0, i * 960 + x1, y1)).resize((tw, th))
        row.paste(c, (i * tw, 18))
        ImageDraw.Draw(row).text((i * tw + 4, 3), names[i], fill=(0, 0, 0))
    rows.append(row)
W = Image.new('RGB', (tw * 12, (th + 18) * 2 + 24), (255, 255, 255))
d = ImageDraw.Draw(W)
d.text((4, 4), f'{bid}  top: before   bottom: after (jingmei1 P6/P7)', fill=(0, 0, 0))
W.paste(rows[0], (0, 24)); W.paste(rows[1], (0, 24 + th + 18))
W.save(out, quality=88)
print(out, W.size)
