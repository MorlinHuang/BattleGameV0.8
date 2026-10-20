"""ref/G*.png → ref/_sheet.jpg：每格一人，原图等比缩进格子（带 alpha 的铺中灰底，幕布色原样保留），格下写编号 + 名字。
名字表 NAMES 跟 docs/三人组30人名单.md（审查 1 后）同步。"""
import os, glob, re
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = {4: '春丽式格斗家', 5: '佟湘玉式老板娘', 6: '美伢式主妇', 7: '约尔式杀手', 8: '艾莎式冰雪女王', 9: '广场舞大妈',
         10: '小丑女式坏女孩', 13: '小龙女式仙子', 14: '希瑞式剑之公主', 15: 'Rose式船头少女', 16: '妲己式狐妖',
         17: '甘露寺式恋柱', 18: '穆桂英式挂帅女将', 19: '无人机网红主播', 20: '邓丽君式歌后', 23: '郭芙蓉式女侠',
         24: '华妃式贵妃', 25: '针筒护士', 26: '蝴蝶忍式剑士', 27: '杉菜式平民女孩', 28: '80年代健美操女',
         29: '黄蓉式女侠', 30: '蛇精式妖女'}
CW, CH, LH, COLS = 300, 400, 40, 6
font = ImageFont.truetype(glob.glob('/usr/share/fonts/**/*[Cc][Jj][Kk]*', recursive=True)[0], 22)
# 只取合成好的定妆图 G<n>.png；分层文件 G<n>_<层>.png 不上总览
files = sorted((f for f in glob.glob(os.path.join(HERE, 'ref', 'G*.png')) if re.fullmatch(r'G\d+\.png', os.path.basename(f))),
               key=lambda f: int(re.findall(r'G(\d+)', f)[0]))
rows = (len(files) + COLS - 1) // COLS
sheet = Image.new('RGB', (CW * COLS, (CH + LH) * rows), 'white'); d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    n = int(re.findall(r'G(\d+)', f)[0]); im = Image.open(f)
    if im.mode == 'RGBA':
        g = Image.new('RGBA', im.size, (128, 128, 128, 255)); g.alpha_composite(im); im = g
    im = im.convert('RGB'); k = min(CW / im.width, CH / im.height)
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    x, y = (i % COLS) * CW, (i // COLS) * (CH + LH)
    sheet.paste(im, (x + (CW - im.width) // 2, y + (CH - im.height) // 2))
    d.text((x + CW // 2, y + CH + LH // 2), f'G{n} {NAMES.get(n, "")}', fill='black', font=font, anchor='mm')
sheet.save(os.path.join(HERE, 'ref', '_sheet.jpg'), quality=88)
print(len(files), 'cells', sheet.size)
