"""从 world.png 切给即梦的取景图：每张 = 游戏里镜头停在某处时的一整屏（960×1707，9:16），放大到 1080×1920。
MOVE 里是每张允许动的区域（世界坐标），回来的视频只取这些区域（羽化）叠回底图，其余一律用底图。"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
TW, TH, OUT_W, OUT_H = 960, 1707, 1080, 1920
TILES = {   # 名字: (世界 x0, [(动区名, x0, y0, x1, y1), ...])
    'T1_客厅':        (1640, [('鱼缸', 1675, 570, 1845, 700), ('阳台门外雨', 2400, 255, 2565, 810)]),
    'T2_女生_写真窗': (560,  [('雨窗', 655, 240, 880, 660), ('写真相框', 1300, 210, 1485, 485)]),
    'T3_男生_猫':     (2640, [('黑猫', 3030, 500, 3195, 675)]),
    'T4_男生_雨窗':   (3280, [('雨窗', 3340, 230, 3655, 600)]),
    'T5_女生_床幔':   (0,    [('床幔纱帘', 0, 200, 490, 820)]),
}
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    w = Image.open(os.path.join(HERE, 'world.png')).convert('RGB')
    F = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', 34)
    for name, (x0, moves) in TILES.items():
        t = w.crop((x0, 0, x0 + TW, TH))
        t.resize((OUT_W, OUT_H), Image.LANCZOS).save(os.path.join(out, f'{name}.png'))
        a = t.copy(); d = ImageDraw.Draw(a, 'RGBA')
        for lab, mx0, my0, mx1, my1 in moves:
            b = (mx0 - x0, my0, mx1 - x0, my1)
            d.rectangle(b, outline=(80, 255, 120), width=5)
            tw = d.textlength(lab, font=F); tx = min(max(b[0], 4), TW - tw - 4); ty = b[3] + 6
            d.rectangle((tx - 4, ty, tx + tw + 4, ty + 44), fill=(0, 0, 0, 180)); d.text((tx, ty + 2), lab, font=F, fill=(80, 255, 120))
        a.resize((540, 960)).save(os.path.join(out, f'{name}_动区示意.jpg'), quality=88)
