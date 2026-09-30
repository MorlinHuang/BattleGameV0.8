"""图集里个别帧整体横移（frames.py build、walkfix.py 之后跑；参数写在角色 frames.json 的 "cellshift": {"pad": 左边加宽几 px, "frames": {帧: 横移 px}}）。
为什么：walk 进场 seq 只在走路时长 TE 内生效（trio.js frameName），最后一步的落地帧（B10 一屁股坐下 plop）画在"离站位还差一步"的地方，
TE 一到换 idle、人横跳一步。把落地帧在格内往前（朝左 = 负）挪一步 = stride / 2 格内 px，坐下那一刻就已经落在站位上。
挪出格的话先给所有格左边加宽 pad（anchor x 跟着 + pad，脚本打印新的 cell / anchor），json 同步改。"""
import sys, os, json
import numpy as np
from PIL import Image
d = sys.argv[1].rstrip('/'); name = os.path.basename(d)
cfg = json.load(open(os.path.join(d, 'frames.json')))['cellshift']
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../web/assets/trio/')
j = json.load(open(W + name + '.json')); cw, ch = j['cell']; cols = j['cols']; names = j['frames']
A = np.array(Image.open(W + name + '.webp').convert('RGBA'))
P = cfg.get('pad', 0); nw = cw + P; rows = (len(names) + cols - 1) // cols
B = np.zeros((rows * ch, cols * nw, 4), np.uint8)
for i, f in enumerate(names):
    c = A[i // cols * ch:(i // cols + 1) * ch, i % cols * cw:(i % cols + 1) * cw]
    o = np.zeros((ch, nw, 4), np.uint8); o[:, P:] = c
    s = cfg['frames'].get(f, 0)
    if s:
        xs = np.nonzero((o[..., 3] > 0).any(0))[0]
        if xs.min() + s < 0 or xs.max() + s >= nw: sys.exit(f'{f} 横移 {s} 出格（内容 x {xs.min()}~{xs.max()}，格宽 {nw}），加大 pad')
        o = np.roll(o, s, axis=1)
    B[i // cols * ch:(i // cols + 1) * ch, i % cols * nw:(i % cols + 1) * nw] = o
Image.fromarray(B).save(W + name + '.webp', 'WEBP', quality=90, method=6)
j['cell'] = [nw, ch]; j['anchor'] = [round(j['anchor'][0] + P, 1), j['anchor'][1]]
if 'head' in j: j['head'] = [j['head'][0] + P, j['head'][1], j['head'][2] + P, j['head'][3]]
json.dump(j, open(W + name + '.json', 'w'), ensure_ascii=False)
print(name, 'cell', j['cell'], 'anchor', j['anchor'], '横移', cfg['frames'])
