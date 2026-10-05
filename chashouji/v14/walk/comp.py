"""选定的候选 → 合成帧（候选名写 = 表示这一格沿用现有 w<i>）：腿区（蒙版放开区）取候选，其余取 base。
接缝按 ../seam.py 对齐：分界附近把候选拽到 base 的轮廓上再渐变（10-05 用户截图：大腿根像被切过错位 —— 旧做法只往里羽化 3 像素）。写 <档>/w<i>.png，再拼一条腿部胶片 + gif"""
import sys, os, numpy as np
W = os.path.dirname(os.path.abspath(__file__))       # v14/walk
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(W, '..'))
import seam
name, picks = sys.argv[1], sys.argv[2:]
G = os.path.join(W, '..', 'gait')
base = np.array(Image.open(f'{G}/{name}/base.png').convert('RGB')).astype(np.float32)
M = np.array(Image.open(f'{G}/{name}/mask.png'))[..., 3] == 0
frames = [base]
for i, pk in enumerate(picks, 1):
    if pk == '=':      # 这一格不换，沿用现有 w<i>
        frames.append(np.array(Image.open(f'{W}/{name}/w{i:02d}.png').convert('RGB')).astype(np.float32)); continue
    c = np.array(Image.open(f'{W}/{name}/cand/{pk}.png').convert('RGB').resize((1536, 1024))).astype(np.float32)
    out = seam.paste(base, c, M)       # 放开区外一律 base
    Image.fromarray(np.round(out).astype(np.uint8)).save(f'{W}/{name}/w{i:02d}.png')
    frames.append(out)
ys, xs = np.nonzero(M)
box = (max(0, xs.min() - 30), ys.min() - 200, min(1536, xs.max() + 30), 1024)
tiles = [Image.fromarray(np.round(f).astype(np.uint8)).crop(box) for f in frames]
tw, th = tiles[0].size; s = 260 / th
tiles = [t.resize((int(tw * s), 260)) for t in tiles]
sh = Image.new('RGB', (tiles[0].width * 8, 520), 'white')
for i, t in enumerate(tiles):
    ImageDraw.Draw(t).text((4, 4), str(i), fill=(0, 0, 0)); sh.paste(t, ((i % 8) * t.width, (i // 8) * 260))
sh.save(f'{W}/{name}/sheet.jpg')
tiles[0].save(f'{W}/{name}/sheet.gif', save_all=True, append_images=tiles[1:], duration=90, loop=0)
