"""G24 出手帧 release（2026-10-02 总控，复查 G30 同类问题时发现）：throw 帧袖口以外的小臂和戴护甲的手绕袖口往上扬 40°（出手瞬间手甩到最前上方）。
原 release 是 addframes 局部重绘、生图上半身两框贴回 throw：生图的头和发饰画小了一圈、脸也不是同一张，框边把袖子切断渐隐，throw 伸出去的那只手还剩一截飘在框外。
生图比例对不上，所以不用（addframes.json 里的 release 条目已删）。袖子压在身上切不下来，只切袖口以外：x ≥ 383 的 150~192 行（小臂）+ x ≥ 396 的 150~215 行（手和垂下的护甲坠子），
都悬在透明底上，抠出来绕袖口点转、贴回 —— 袖子和身子逐像素同 throw。
直接替换图集里 release 那一格；重新 build 图集之后再跑一次。在 chashouji 下：python3 v14/trio/bestie/G24_huafei/armrelease.py"""
import json, math, os
import numpy as np
from PIL import Image
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio')
PIV, ROT = (382, 178), 40     # 袖口点（格内）、转多少度（正 = 逆时针 = 往上扬）
m = json.load(open(os.path.join(WEB, 'G24_huafei.json'))); a = Image.open(os.path.join(WEB, 'G24_huafei.webp')).convert('RGBA')
cw, ch = m['cell']; C = m['cols']; assert m['cell'] == [570, 303], '切口和袖口点量在 cell 570×303 的图集上'
cell = lambda n: (m['frames'].index(n) % C * cw, m['frames'].index(n) // C * ch)
x, y = cell('throw'); A = np.array(a.crop((x, y, x + cw, y + ch))); yy, xx = np.mgrid[:ch, :cw]
sel = ((xx >= 383) & (yy >= 150) & (yy < 192)) | ((xx >= 396) & (yy >= 150) & (yy < 215))
arm = A.copy(); arm[~sel] = 0; rest = A.copy(); rest[sel] = 0
rel = Image.fromarray(rest); rel.alpha_composite(Image.fromarray(arm).rotate(ROT, resample=Image.BICUBIC, center=PIV))
x, y = cell('release'); a.paste(rel, (x, y))
a.save(os.path.join(WEB, 'G24_huafei.webp'), 'WEBP', quality=90, method=6)
t = math.radians(ROT); dx, dy = 461 - PIV[0], 169 - PIV[1]        # throw 的出手点 hold [461, 169] 跟着转
print('release 出手点', [round(PIV[0] + dx * math.cos(t) + dy * math.sin(t), 1), round(PIV[1] - dx * math.sin(t) + dy * math.cos(t), 1)])
