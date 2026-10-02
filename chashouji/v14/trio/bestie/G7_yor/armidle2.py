"""G7 待机换姿势 idle2（精闺1 P7，2026-10-02 总控）：idle 帧前面那只小臂绕肘往上收 100°，手立到胸前（活动手指 / 整理手套）。
原 idle2 是整张重生的人（头顶高 25 px、站姿也变），769478b 停用；按规范要以 idle 为底只改局部，这里用切件：
idle 帧肘以外（x 262~345、150~215 行）只有前臂和手套，抠出来绕肘点转、贴回 —— 身子逐像素同 idle，待机轮换不忽大忽小。
直接替换图集里 idle2 那一格；addframes.json 里没有 idle2 条目，build 时 idle2 按原图集保留，不用重跑。在 chashouji 下：python3 v14/trio/bestie/G7_yor/armidle2.py"""
import json, os
import numpy as np
from PIL import Image
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio')
X0, X1, Y0, Y1, PIV, ROT = 262, 345, 150, 215, (266, 183), 100     # 前臂框、肘点（格内）、转多少度（正 = 逆时针 = 往上收）
m = json.load(open(os.path.join(WEB, 'G7_yor.json'))); a = Image.open(os.path.join(WEB, 'G7_yor.webp')).convert('RGBA')
cw, ch = m['cell']; C = m['cols']; assert m['cell'] == [410, 435], '框和肘点量在 cell 410×435 的图集上'
cell = lambda n: (m['frames'].index(n) % C * cw, m['frames'].index(n) // C * ch)
x, y = cell('idle'); A = np.array(a.crop((x, y, x + cw, y + ch))); yy, xx = np.mgrid[:ch, :cw]
sel = (xx >= X0) & (xx < X1) & (yy >= Y0) & (yy < Y1)
arm = A.copy(); arm[~sel] = 0; rest = A.copy(); rest[sel] = 0
i2 = Image.fromarray(rest); i2.alpha_composite(Image.fromarray(arm).rotate(ROT, resample=Image.BICUBIC, center=PIV))
x, y = cell('idle2'); a.paste(i2, (x, y))
a.save(os.path.join(WEB, 'G7_yor.webp'), 'WEBP', quality=90, method=6)
