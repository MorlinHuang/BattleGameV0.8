"""B14 抡臂帧（swing，精1 P6：wind 举过头顶 → throw 往左下砸之间缺一拍）：throw 帧往左下伸的胳膊绕肩往上转 35° 抡到水平（2026-10-02 总控）。
throw 帧肩以左（x < CUT、110~172 行）只有胳膊，抠出来绕肩点转、贴回 —— 身子逐像素同 throw。
抡平后拳头伸出格子左边约 9 px，所以整张图集每格左边加宽 PAD（cell 240 → 252），cfg 里 B14 所有格内 x 坐标 +PAD。
输入是 frames.py build 出来的图集（cell 240）；重新 build 之后再跑一次。在 chashouji 下：python3 v14/trio/buddy/B14_miner/armswing.py"""
import json, math, os
import numpy as np
from PIL import Image
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio')
PAD, CUT, PIV, ROT = 12, 64, (70, 126), -35     # 左边加宽、切口 x、肩点（加宽前的格内）、转多少度（负 = 顺时针 = 往上抡）
m = json.load(open(os.path.join(WEB, 'B14_miner.json'))); a = Image.open(os.path.join(WEB, 'B14_miner.webp')).convert('RGBA')
cw, ch = m['cell']; C = m['cols']; assert cw == 240, 'armswing.py 的输入是 frames.py 出的 cell 240 图集'
cells = [a.crop((i % C * cw, i // C * ch, i % C * cw + cw, i // C * ch + ch)) for i in range(len(m['frames']))]
A = np.array(cells[m['frames'].index('throw')]); yy, xx = np.mgrid[:ch, :cw]
sel = (xx < CUT) & (yy >= 110) & (yy < 172)
arm = A.copy(); arm[~sel] = 0; rest = A.copy(); rest[sel] = 0
W = cw + PAD
pad = lambda c: (lambda o: (o.alpha_composite(c, (PAD, 0)), o)[1])(Image.new('RGBA', (W, ch), (0, 0, 0, 0)))
sw = pad(Image.fromarray(rest)); sw.alpha_composite(pad(Image.fromarray(arm)).rotate(ROT, resample=Image.BICUBIC, center=(PIV[0] + PAD, PIV[1])))
cells = [pad(c) for c in cells] + [sw]; names = m['frames'] + ['swing']
rows = (len(cells) + C - 1) // C; out = Image.new('RGBA', (W * C, ch * rows), (0, 0, 0, 0))
for i, c in enumerate(cells): out.alpha_composite(c, (i % C * W, i // C * ch))
out.save(os.path.join(WEB, 'B14_miner.webp'), 'WEBP', quality=90, method=6)
m.update(cell=[W, ch], frames=names, anchor=[m['anchor'][0] + PAD, m['anchor'][1]], head=[m['head'][0] + PAD, m['head'][1], m['head'][2] + PAD, m['head'][3]])
json.dump(m, open(os.path.join(WEB, 'B14_miner.json'), 'w'), ensure_ascii=False)
th = math.radians(-ROT); dx, dy = 10 - PIV[0], 150 - PIV[1]        # throw 的握点 [10, 150] 跟着转
print('swing 握点', [round(PIV[0] + dx * math.cos(th) - dy * math.sin(th) + PAD, 1), round(PIV[1] + dx * math.sin(th) + dy * math.cos(th), 1)])
