"""B15 出手帧（throw）手臂往下转 ROT 度，指尖对准左下方的她（2026-10-02 总控；精1 P12 / trio_tune 补帧名单：手没对准落点）。
出手点在屏幕 (723, 441)，她的脸在左下约 40°，原 throw 指尖水平向左。throw 帧肩口以左（x < CUT）的整段手臂落在透明背景上，
抠出来绕肩点转、原位清掉、贴回 —— 身子、头、腿逐像素不变（同 bestie/G8_elsa、G7_yor 的 armswing.py）。
直接改图集里的 throw 格：frames.py 从 raw 重新 build 之后要再跑一次本脚本。在 chashouji 下：python3 v14/trio/buddy/B15_gojo/armswing.py"""
import json, os
import numpy as np
from PIL import Image
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio')
CUT, PIV, ROT = 96, (112, 118), 38             # 切口 x、肩点（格内）、往下转多少度（PIL 正 = 逆时针 = 指向左的手往下）
m = json.load(open(os.path.join(WEB, 'B15_gojo.json'))); a = Image.open(os.path.join(WEB, 'B15_gojo.webp')).convert('RGBA')
cw, ch = m['cell']; C = m['cols']; i = m['frames'].index('throw'); x0, y0 = i % C * cw, i // C * ch
A = np.array(a.crop((x0, y0, x0 + cw, y0 + ch)))
yy, xx = np.mgrid[:ch, :cw]
sel = (xx < CUT) & (yy > 40) & (yy < 142)      # 手臂 + 翘起的拇指；142 以下是盘着的腿
arm = A.copy(); arm[~sel] = 0; rest = A.copy(); rest[sel] = 0
out = Image.fromarray(rest); out.alpha_composite(Image.fromarray(arm).rotate(ROT, resample=Image.BICUBIC, center=PIV))
a.paste(out, (x0, y0)); a.save(os.path.join(WEB, 'B15_gojo.webp'), 'WEBP', quality=90, method=6)
print('throw 指尖 (0, 90) → (6.5, 164.9)')
