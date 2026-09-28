# 三人同屏站位示意：用现有女神/恶魔立绘当占位，摆出 1 人 / 3 人两种站位。只看站位与遮挡，不代表新形象。
from PIL import Image, ImageDraw, ImageFont
W = '/workspace/art/chashouji/web/assets/world/'
base = Image.open('/tmp/g3/base.png').convert('RGBA')
T = Image.open(W + 'truth2_up.webp').convert('RGBA'); TF = (160, 608); TM = (370, 334); TH = (211, 78)
D = Image.open(W + 'demon1_up.webp').convert('RGBA'); DF = (244, 555); DM = (53, 305); DH = (204, 59)
font = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc', 30) if __import__('os').path.exists('/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc') else ImageFont.load_default()
FA, FB = (273, 862), (667, 850)          # 女生 / 男生脸（截图量）
def put(im, spr, foot, at, s, alpha=255):
    w, h = spr.size; sp = spr.resize((int(w * s), int(h * s)), Image.LANCZOS)
    x, y = int(at[0] - foot[0] * s), int(at[1] - foot[1] * s)
    im.alpha_composite(sp, (x, y)); return lambda p: (x + p[0] * s, y + p[1] * s)
def panel(slotsL, slotsR, title):
    im = base.copy(); d = ImageDraw.Draw(im)
    for at, s in slotsL: m = put(im, T, TF, at, s)
    for at, s in slotsR: m = put(im, D, DF, at, s)
    d = ImageDraw.Draw(im)
    for k, (at, s) in enumerate(slotsL):
        f = lambda p: (at[0] + (p[0] - TF[0]) * s, at[1] + (p[1] - TF[1]) * s)
        d.line([f(TM), FB], fill=(120, 220, 60, 255), width=4)
        hx, hy = f(TH); d.ellipse([hx - 14, hy - 14, hx + 14, hy + 14], outline=(255, 0, 0, 255), width=4)
        d.text((hx - 8, hy - 60), str(len(slotsL) - k), font=font, fill=(200, 0, 0, 255), stroke_width=3, stroke_fill='white')
    for k, (at, s) in enumerate(slotsR):
        f = lambda p: (at[0] + (p[0] - DF[0]) * s, at[1] + (p[1] - DF[1]) * s)
        d.line([f(DM), FA], fill=(180, 80, 230, 255), width=4)
        hx, hy = f(DH); d.ellipse([hx - 14, hy - 14, hx + 14, hy + 14], outline=(255, 0, 0, 255), width=4)
        d.text((hx - 8, hy - 60), str(len(slotsR) - k), font=font, fill=(200, 0, 0, 255), stroke_width=3, stroke_fill='white')
    for y, c, t in [(190, (0, 0, 0), 'y190 拉力行'), (780, (220, 0, 0), 'y780 女生头顶'), (750, (140, 0, 180), 'y750 男生头顶')]:
        for x in range(0, 960, 24): d.line([(x, y), (x + 12, y)], fill=c + (255,), width=3)
        d.text((8 if y != 750 else 700, y - 36), t, font=font, fill=c + (255,), stroke_width=3, stroke_fill='white')
    d.line([(480, 180), (480, 800)], fill=(0, 0, 0, 160), width=2)
    d.rectangle([0, 1250, 960, 1340], fill=(255, 255, 255, 230)); d.text((20, 1268), title, font=font, fill=(0, 0, 0, 255))
    return im.crop((0, 0, 960, 1340))
mir = lambda sl: [((960 - x, y - 25), s) for (x, y), s in sl]   # 恶魔侧：镜像，靴底上移 25（男生头顶更高）
one = [((170, 740), 0.95)]
trio = [((330, 517), 0.55), ((215, 626), 0.60), ((100, 740), 0.66)]   # 远→近：右上 → 左下，沿喷射方向的垂线排
a = panel(one, [((790, 715), 0.95)], '现在：每边 1 人，s 0.95')
b = panel(trio, mir(trio), '三人时：沿斜线排三个槽，远小近大（s 0.55 / 0.60 / 0.66）')
out = Image.new('RGB', (1920 + 20, 1340), 'white'); out.paste(a, (0, 0)); out.paste(b, (980, 0))
out.save('/workspace/art/chashouji/shots/review/trio/trio_layout.png')
out.resize((970, 670)).save('/tmp/g3/trio_small.png')
