"""G5 待机换姿势 idle2（精闺1 P7，2026-10-02 总控）：idle 帧的头绕脖子歪 9°（愣住的人歪头）。
原 idle2 是整张重生的人（头顶高 56 px、站姿也变），769478b 停用；按规范要以 idle 为底只改局部，但 G5 待机两只手都压在身上（按胸口、叉腰）、
胳膊切不下来，以 idle 为底的局部重绘又两次被上游审核拒，所以改动头：格内 y < Y 只有头、发髻和簪子（四周透明），抠出来绕颈点转、贴回 —— 身子逐像素同 idle。
直接替换图集里 idle2 那一格；重新 build 图集之后再跑一次。在 chashouji 下：python3 v14/trio/bestie/G5_tong/headidle2.py"""
import json, os
import numpy as np
from PIL import Image
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio')
Y, PIV, ROT = 134, (160, 136), 9     # 切口行（领口上沿）、颈点（格内）、转多少度（正 = 逆时针 = 头往后歪）
m = json.load(open(os.path.join(WEB, 'G5_tong.json'))); a = Image.open(os.path.join(WEB, 'G5_tong.webp')).convert('RGBA')
cw, ch = m['cell']; C = m['cols']; assert m['cell'] == [399, 464], '切口和颈点量在 cell 399×464 的图集上'
cell = lambda n: (m['frames'].index(n) % C * cw, m['frames'].index(n) // C * ch)
x, y = cell('idle'); A = np.array(a.crop((x, y, x + cw, y + ch))); sel = np.mgrid[:ch, :cw][0] < Y
head = A.copy(); head[~sel] = 0; rest = A.copy(); rest[sel] = 0
i2 = Image.fromarray(rest); i2.alpha_composite(Image.fromarray(head).rotate(ROT, resample=Image.BICUBIC, center=PIV))
x, y = cell('idle2'); a.paste(i2, (x, y))
a.save(os.path.join(WEB, 'G5_tong.webp'), 'WEBP', quality=90, method=6)
