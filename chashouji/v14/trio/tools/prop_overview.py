#!/usr/bin/env python3
"""三人组 3D 道具总览：每件取转盘第 0 / 9 / 18 / 27 格（0° / 90° / 180° / 270°），按引擎里的屏幕尺寸（直径 2r × scale）×2 画在地板米色上。

    python3 v14/trio/tools/prop_overview.py [输出.png]      # 默认 shots/trio_std/3d道具总览.png（在 chashouji/ 下跑）

PROPS 与 docs/三人组角色规范.md 第七节的道具表一致：件名 → (谁的、cell、scale、r)。新出一件就在这里和表里各加一行。
"""
import sys
from PIL import Image, ImageDraw, ImageFont

PROPS = {   # 件名: (角色 · 道具, cell, scale, r)
    'basketball': ('B21 樱木 · 篮球', 104, 1.07, 34),
    'meatball':   ('B27 食神 · 牛丸（美术）', 68, 1.27, 18),
    'dumbbell':   ('B25 教练 · 哑铃（美术）', 75, 1.08, 24),
    'cassette':   ('B24 霹雳舞 · 磁带（美术）', 84, 1.31, 22),
    'coin':       ('B6 上海滩 · 银元', 63, 1.13, 20),
    'mahjong':    ('B10 麻将大叔 · 红中', 77, 1.37, 20),
    'pinecone':   ('B8 光头强 · 松果', 76, 1.04, 26),
    'takeout':    ('B9 外卖小哥 · 外卖盒', 96, 1.32, 26),
    'dirtblock':  ('B14 方块矿工 · 泥土方块', 125, 1.49, 30),
    'fan':        ('B18 唐伯虎 · 折扇', 92, 1.10, 30),
    'mouse':      ('B26 电竞宅男 · 有线鼠标', 88, 1.37, 22),
    'watermelon': ('B28 八戒 · 西瓜', 98, 1.17, 30),
    'crutch':     ('B29 卖拐 · 拐杖', 118, 1.24, 34),
    'abacus':     ('G5 佟湘玉 · 算盘', 115, 1.35, 34),
    'pan':        ('G6 主妇 · 平底锅', 91, 1.08, 30),
    'bat':        ('G10 小丑女 · 棒球棍', 98, 1.09, 32),
    'necklace':   ('G15 Rose · 海洋之心', 79, 1.09, 26),
    'spear':      ('G18 穆桂英 · 红缨枪', 120, 1.07, 40),
    'rocket':     ('G19 主播 · 小火箭', 106, 1.35, 28),
    'nailguard':  ('G24 华妃 · 护甲', 68, 1.22, 20),
    'schoolbag':  ('G27 杉菜 · 书包', 115, 1.37, 30),
    'hoop':       ('G28 健美操 · 呼啦圈', 108, 1.07, 36),
    'syringe':    ('G25 护士 · 针筒（美术，scale 估 1.2）', 128, 1.2, 40),
    'butterfly':  ('G26 蝴蝶忍 · 蝴蝶（美术，scale 估 1.2）', 76, 1.2, 22),
}
Z, COLS, TW, TH = 2, 2, 200, 250
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'


def main(out):
    f = ImageFont.truetype(FONT, 18)
    rows = (len(PROPS) + COLS - 1) // COLS
    im = Image.new('RGB', (COLS * (4 * TW + 20), rows * TH + 60), (233, 222, 200))
    d = ImageDraw.Draw(im)
    d.text((16, 14), '三人组 3D 道具总览（%d 件）：转盘 0° / 90° / 180° / 270°，引擎屏幕尺寸 ×2，地板米色底' % len(PROPS), fill=(40, 30, 20), font=f)
    for k, (n, (who, cell, sc, r)) in enumerate(PROPS.items()):
        a = Image.open(f'web/assets/trio/prop_{n}.webp').convert('RGBA')
        px = int(round(2 * r * sc * Z))
        x0, y0 = (k % COLS) * (4 * TW + 20) + 10, (k // COLS) * TH + 60
        d.text((x0 + 6, y0 + 4), f'{who}   prop_{n}.webp  r {r}', fill=(40, 30, 20), font=f)
        for j, i in enumerate((0, 9, 18, 27)):
            g = a.crop(((i % 6) * cell, (i // 6) * cell, (i % 6 + 1) * cell, (i // 6 + 1) * cell)).resize((px, px), Image.LANCZOS)
            im.paste(g, (x0 + j * TW + TW // 2 - px // 2, y0 + 135 - px // 2), g)
    im.save(out)
    print(out, im.size)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'shots/trio_std/3d道具总览.png')
