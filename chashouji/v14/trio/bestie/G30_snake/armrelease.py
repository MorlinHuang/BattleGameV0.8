"""G30 放光帧 release（2026-10-02 总控，用户："图片缺失，动作畸形"）：throw 帧平伸的手臂连如意绕肩往上转 50°，举起来朝右上放光。
原 release 是 addframes 局部重绘、只把生图上半身贴回 throw（inplace 框 [225, 0, 497, 185]）：生图的人胸胯腿都画大一圈、头却差不多大，
按腿配准上半身就小一截，框边还缺一条；整张用又是身子大一圈 —— 生图比例和底图对不上，所以不用生图（addframes.json 里的 release 条目已删）。
throw 帧肩口以外（下巴右侧 x ≥ 364 起）的手臂、手和如意都悬在透明底上，抠出来绕肩点转、贴回 —— 身子逐像素同 throw。
切口分三段：肩口 236~262 行；x ≥ 378 多切到 266 行（胳膊下沿那道轮廓线，不切会在腋下留一道线）；x ≥ 392 整段（手和如意）。
直接替换图集里 release 那一格；重新 build 图集之后再跑一次。在 chashouji 下：python3 v14/trio/bestie/G30_snake/armrelease.py"""
import json, math, os
import numpy as np
from PIL import Image
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio')
PIV, ROT = (370, 258), 50     # 肩点（格内）、转多少度（正 = 逆时针 = 往上举）
m = json.load(open(os.path.join(WEB, 'G30_snake.json'))); a = Image.open(os.path.join(WEB, 'G30_snake.webp')).convert('RGBA')
cw, ch = m['cell']; C = m['cols']; assert m['cell'] == [577, 385], '切口和肩点量在 cell 577×385 的图集上'
cell = lambda n: (m['frames'].index(n) % C * cw, m['frames'].index(n) // C * ch)
x, y = cell('throw'); A = np.array(a.crop((x, y, x + cw, y + ch))); yy, xx = np.mgrid[:ch, :cw]
sel = ((xx >= 364) & (yy >= 236) & (yy < 262)) | ((xx >= 378) & (yy >= 236) & (yy < 267)) | ((xx >= 392) & (yy >= 222) & (yy < 300))
arm = A.copy(); arm[~sel] = 0; rest = A.copy(); rest[sel] = 0
rel = Image.fromarray(rest); rel.alpha_composite(Image.fromarray(arm).rotate(ROT, resample=Image.BICUBIC, center=PIV))
x, y = cell('release'); a.paste(rel, (x, y))
a.save(os.path.join(WEB, 'G30_snake.webp'), 'WEBP', quality=90, method=6)
t = math.radians(ROT); dx, dy = 522 - PIV[0], 234 - PIV[1]        # throw 的如意头 hold [522, 234] 跟着转
print('release 如意头', [round(PIV[0] + dx * math.cos(t) + dy * math.sin(t), 1), round(PIV[1] - dx * math.sin(t) + dy * math.cos(t), 1)])
