"""G7 跟随帧（through）：throw 帧伸直的右臂绕肩往下转 ROT 度，接着出手的劲往下收（2026-10-02 总控）。
原 through 是整张重生的人、头顶比 throw 高 30 px，已停用（769478b）；这张底图做局部重绘会被上游审核拒，所以照 G8_elsa/armswing.py：
throw 帧里肩口以外的整段手臂都落在透明背景上，抠出来绕肩点转、原位清掉、贴回 —— 身子、头发、腿逐像素同 throw，人不会忽大忽小。
手臂区 = 切口 x ≥ CUT 的 116~146 行（肩到护手）+ x ≥ 300 的 88~146 行（翘起来的手指）；x 300 以左、116 行以上是头发，不碰。
输出 raw/add_through.png（整格 RGBA，换进图集 through 格）。在 v14/trio 下：python3 bestie/G7_yor/armswing.py <G7_yor.webp> <G7_yor.json>"""
import json, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
PIV, CUT, ROT = (256, 129), 264, -40           # 肩点（格内）、切口 x、转多少度（负 = 顺时针 = 往下）
m = json.load(open(sys.argv[2])); a = Image.open(sys.argv[1]).convert('RGBA')
cw, ch = m['cell']; C = m['cols']; i = m['frames'].index('throw')
A = np.array(a.crop((i % C * cw, i // C * ch, i % C * cw + cw, i // C * ch + ch)))
yy, xx = np.mgrid[:ch, :cw]
sel = ((xx >= CUT) & (yy >= 116) & (yy < 146)) | ((xx >= 300) & (yy >= 88) & (yy < 146))
arm = A.copy(); arm[~sel] = 0; rest = A.copy(); rest[sel] = 0
out = Image.fromarray(rest); out.alpha_composite(Image.fromarray(arm).rotate(ROT, resample=Image.BICUBIC, center=PIV))
out.save(os.path.join(HERE, 'raw', 'add_through.png'))
