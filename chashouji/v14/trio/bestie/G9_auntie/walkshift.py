"""G9 走路条换帧钉脚：frames.py 的 loose 帧横向按头对齐，但秧歌步四帧里人的前后位置画得不均（着地鞋跟每次换帧前进 65 / 76 / 59 / 73 格内 px），
填一个 stride 时换帧那一下同一只脚最多差 9 格内 px（×0.88 ≈ 8 屏幕 px，超 6）。这里把 walk2 / walk3 / walk4 整格横移 −3 / +4 / −5 px，
四次换帧都变成 68 / 69 / 68 / 68（stride 136.5）。每次 frames.py build 之后都要重跑。"""
import os, numpy as np
from PIL import Image
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/trio/G9_auntie.webp')
CW, CH, COLS = 277, 415, 4
NAMES = ['idle', 'wind', 'throw', 'follow', 'walk1', 'walk2', 'walk3', 'walk4']
SHIFT = {'walk2': -3, 'walk3': 4, 'walk4': -5}
a = np.array(Image.open(P).convert('RGBA'))
for n, d in SHIFT.items():
    i = NAMES.index(n); y, x = i // COLS * CH, i % COLS * CW
    c = a[y:y + CH, x:x + CW].copy()
    gone = c[:, -d:] if d > 0 else c[:, :-d]
    assert not gone[..., 3].any(), n   # 卷出去（绕到另一边）的那几列必须是空的
    a[y:y + CH, x:x + CW] = np.roll(c, d, axis=1)
Image.fromarray(a).save(P, 'WEBP', quality=90, method=6)   # 同 frames.py
print('shifted', SHIFT)
