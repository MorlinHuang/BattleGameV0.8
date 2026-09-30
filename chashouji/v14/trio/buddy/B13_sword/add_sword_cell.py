"""B13 图集末尾加一格 'sword'（飞剑 + 蓝光拖尾），给 atk.rush.ghost 取：rush 的残影按图原样水平画、不旋转，剑尖一直朝左、拖尾在后。
（throw 飞出去的平面道具朝向是随机的 b.hang，只有玫瑰顺着速度转；带拖尾的剑用 throw 会横着 / 倒着飞。）
frames.py build 之后跑：python3 buddy/B13_sword/add_sword_cell.py（在 v14/trio 下），打印 ghost 的 box。"""
import json, os
import numpy as np
from PIL import Image
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio/')
j = json.load(open(W + 'B13_sword.json')); cw, ch = j['cell']; cols = j['cols']; names = j['frames']
if 'sword' in names: raise SystemExit('已经有 sword 格了（重新 build 之后再跑）')
A = Image.open(W + 'B13_sword.webp').convert('RGBA')
sw = Image.open(W + 'B13_sword_fly.webp').convert('RGBA')
k = (cw - 6) / sw.width; sw = sw.resize((round(sw.width * k), round(sw.height * k)), Image.LANCZOS)
n = len(names); rows = n // cols + 1
B = Image.new('RGBA', (cols * cw, rows * ch), (0, 0, 0, 0)); B.paste(A, (0, 0))
x0 = n % cols * cw + 3; y0 = n // cols * ch + ch // 2 - sw.height // 2
B.alpha_composite(sw, (x0, y0))
B.save(W + 'B13_sword.webp', 'WEBP', quality=90, method=6)
j['frames'] = names + ['sword']; json.dump(j, open(W + 'B13_sword.json', 'w'), ensure_ascii=False)
bx = [3, ch // 2 - sw.height // 2, 3 + sw.width, ch // 2 - sw.height // 2 + sw.height]
print('sword 格', n, 'box', bx, '剑宽', sw.width)
