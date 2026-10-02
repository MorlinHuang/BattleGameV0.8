"""B19 抬臂帧（swing，精1 P6：wind 两臂张开 → throw 十字手之间缺一拍）：wind 帧往前伸的那只小臂绕肘往上抬 45°（2026-10-02 总控）。
10-02 局部重绘 3 张都直接画成十字手（= throw），且红条纹被品红键吃成橙，未采用，改切件。
wind 帧肘以外（x < CUT、95~135 行）只有小臂和拳，抠出来绕肘点转、贴回 —— 身子和另一只胳膊逐像素同 wind。
后面那只胳膊没转：切口在红色袖段中间，往下转会在肩外露出一截断开的红布。
输入是 frames.py build 出来的图集（8 帧）；重新 build 之后再跑一次。在 chashouji 下：python3 v14/trio/buddy/B19_ultra/armswing.py"""
import json, os
import numpy as np
from PIL import Image
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio')
CUT, PIV, ROT = 50, (52, 116), -45     # 切口 x、肘点（格内）、转多少度（负 = 顺时针 = 往上抬）
m = json.load(open(os.path.join(WEB, 'B19_ultra.json'))); a = Image.open(os.path.join(WEB, 'B19_ultra.webp')).convert('RGBA')
cw, ch = m['cell']; C = m['cols']; assert 'swing' not in m['frames'], 'armswing.py 的输入是 frames.py 出的图集（还没有 swing）'
cells = [a.crop((i % C * cw, i // C * ch, i % C * cw + cw, i // C * ch + ch)) for i in range(len(m['frames']))]
A = np.array(cells[m['frames'].index('wind')]); yy, xx = np.mgrid[:ch, :cw]
sel = (xx < CUT) & (yy >= 95) & (yy < 135)
arm = A.copy(); arm[~sel] = 0; rest = A.copy(); rest[sel] = 0
sw = Image.fromarray(rest); sw.alpha_composite(Image.fromarray(arm).rotate(ROT, resample=Image.BICUBIC, center=PIV))
cells.append(sw); names = m['frames'] + ['swing']
rows = (len(cells) + C - 1) // C; out = Image.new('RGBA', (cw * C, ch * rows), (0, 0, 0, 0))
for i, c in enumerate(cells): out.alpha_composite(c, (i % C * cw, i // C * ch))
out.save(os.path.join(WEB, 'B19_ultra.webp'), 'WEBP', quality=90, method=6)
m.update(frames=names); json.dump(m, open(os.path.join(WEB, 'B19_ultra.json'), 'w'), ensure_ascii=False)
