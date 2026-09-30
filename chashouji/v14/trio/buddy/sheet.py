"""定妆总览：ref/B*.png → ref/_sheet.jpg。原图按幕布抠像（自带 alpha 的直接用），贴到浅灰底上——顺带检查抠得干不干净。
名字从 docs/三人组30人名单.md 的哥们表里取，名单改了重跑即可。"""
import os, sys, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../..'))
from crewart import cut
REF = os.path.join(HERE, 'ref')
LIST = open(os.path.join(HERE, '../../../docs/三人组30人名单.md'), encoding='utf-8').read()
NAMES = dict(re.findall(r'^\| (B\d+) \| [^|]+ \| ([^|（]+)', LIST, re.M))
FONT = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', 26)
CW, CH, COLS = 300, 450, 6

def load(p):
    im = Image.open(p)
    if im.mode == 'RGBA' and np.array(im)[..., 3].min() < 250:
        return im
    r, g, b = np.array(im.convert('RGB'))[5, 5].astype(int)
    rgb, al = cut(p, 'green' if g > r else 'magenta', (40, 150))
    return Image.fromarray(np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8), 'RGBA')

files = sorted((f for f in os.listdir(REF) if re.fullmatch(r'B\d+\.png', f)), key=lambda f: int(f[1:-4]))
rows = -(-len(files) // COLS)
S = Image.new('RGB', (CW * COLS, (CH + 40) * rows), (225, 225, 225))
d = ImageDraw.Draw(S)
for i, f in enumerate(files):
    im = load(os.path.join(REF, f))
    im = im.crop(im.getbbox())
    k = min((CW - 16) / im.width, (CH - 16) / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    x, y = i % COLS * CW, i // COLS * (CH + 40)
    S.paste(im, (x + (CW - im.width) // 2, y + CH - 8 - im.height), im)
    d.text((x + 8, y + CH + 2), f'{f[:-4]} {NAMES.get(f[:-4], "").strip()}', font=FONT, fill=(0, 0, 0))
S.save(os.path.join(REF, '_sheet.jpg'), quality=88)
print(len(files), 'cells', S.size)
