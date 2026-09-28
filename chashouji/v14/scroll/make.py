"""法海的金光经卷（2026-09-28）：对应白娘子的海面 —— 屏幕底部几条金色佛经卷轴像海浪一样起伏，远 / 中 / 近三层。
用户："同样也需要跟白娘子海面的动效，可能是在金光虚化的佛经卷轴，也会和海平面一样波动"。
用法：python3 v14/scroll/make.py [字体] → web/assets/world/scroll_{far,mid,near}.webp，打印 sea.js SCROLL 要填的尺寸。
字体默认 /tmp/NotoSerifCJK-Bold.ttc（桌面容器 /usr/share/fonts/opentype/noto/ 里有，scp 过来；27MB 不进仓库）。

程序画、不生图：生图写出来的汉字是乱码，直播间观众一眼就看得出来。经文用《般若波罗蜜多心经》（玄奘译本，公版）。
一条卷轴 = 金色绢面（上下中间亮、两边暗的竖向渐变 + 横向细纹）+ 上下两道绛红锦边（金线、卍字纹）+ 竖排经文（绛褐字、一列列）；
四周烘一圈金光（"金光虚化"）；整条半透明（ALPHA），下面的地板和海 / 人隐约透出来。
横向无缝：宽 = 列距 × 列数，卍字纹的周期也整除宽 —— 首尾一列接一列，不用拼缝。
三层是同一种卷轴按不同大小画（远的小），经文从不同的字起（三层不会一模一样）。
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'web', 'assets', 'world')
FONT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/NotoSerifCJK-Bold.ttc'
SUTRA = ('观自在菩萨行深般若波罗蜜多时照见五蕴皆空度一切苦厄舍利子色不异空空不异色色即是空空即是色受想行识亦复如是'
         '舍利子是诸法空相不生不灭不垢不净不增不减是故空中无色无受想行识无眼耳鼻舌身意无色声香味触法无眼界乃至无意识界'
         '无无明亦无无明尽乃至无老死亦无老死尽无苦集灭道无智亦无得以无所得故菩提萨埵依般若波罗蜜多故心无挂碍无挂碍故'
         '无有恐怖远离颠倒梦想究竟涅槃三世诸佛依般若波罗蜜多故得阿耨多罗三藐三菩提故知般若波罗蜜多是大神咒是大明咒'
         '是无上咒是无等等咒能除一切苦真实不虚故说般若波罗蜜多咒即说咒曰揭谛揭谛波罗揭谛波罗僧揭谛菩提萨婆诃')
# 层：名、缩放、列数（宽 = 列距 × 列数）、经文从第几个字起
LAYERS = [('far', 0.55, 40, 0), ('mid', 0.78, 34, 97), ('near', 1.0, 30, 191)]
# 以 1.0 倍量（像素）：绢面高、锦边高、列距、字号、每列几个字、四周金光留边
PAPER_H, BORDER, COL, FS, ROWS, GLOW = 118, 13, 36, 23, 3, 26
GOLD = [(255, 236, 170), (246, 196, 88), (214, 146, 40)]   # 绢面：中间亮 → 上下边暗
RED, REDK, INK = (150, 36, 24), (96, 20, 14), (110, 40, 14)   # 锦边、锦边深、经文墨色（绛褐，金底上看得清又不发黑）
ALPHA = 0.86                     # 整条卷轴的不透明度


def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def scroll(K, cols, start):
    col, fs, bd, ph, gl = round(COL * K), round(FS * K), max(4, round(BORDER * K)), round(PAPER_H * K), round(GLOW * K)
    W, H = col * cols, ph + 2 * gl
    font = ImageFont.truetype(FONT, fs, index=2)          # index 2 = 简体
    paper = Image.new('RGBA', (W, ph))
    px = paper.load()
    rng = np.random.default_rng(3)
    fiber = rng.normal(0, 1, ph)                          # 横向细纹：每一行一点明暗（绢的织纹），沿 x 不变 → 天然无缝
    for y in range(ph):
        v = abs(y / (ph - 1) - 0.5) * 2                   # 0 中间 → 1 上下边
        c = lerp(GOLD[0], GOLD[1], v / 0.7) if v < 0.7 else lerp(GOLD[1], GOLD[2], (v - 0.7) / 0.3)
        c = tuple(max(0, min(255, int(ch + fiber[y] * 5))) for ch in c)
        for x in range(W): px[x, y] = c + (255,)
    d = ImageDraw.Draw(paper)
    # 上下锦边：绛红底、两道金线、中间一排卍字（周期 = 两列，整除宽）
    for y0 in (0, ph - bd):
        d.rectangle([0, y0, W, y0 + bd - 1], fill=RED + (255,))
        d.line([0, y0 + max(1, bd // 6), W, y0 + max(1, bd // 6)], fill=GOLD[1] + (255,), width=max(1, bd // 8))
        d.line([0, y0 + bd - 1 - max(1, bd // 6), W, y0 + bd - 1 - max(1, bd // 6)], fill=GOLD[1] + (255,), width=max(1, bd // 8))
        sf = ImageFont.truetype(FONT, max(6, int(bd * 0.8)), index=2)
        for x in range(0, W, col * 2):
            d.text((x + col, y0 + bd / 2), '卍', font=sf, fill=(255, 214, 110, 255), anchor='mm')
    # 经文：竖排，每列 ROWS 个字，列与列之间一道极淡的界栏
    top, bot = bd + 2, ph - bd - 2
    step = (bot - top) / ROWS
    k = start
    for c in range(cols):
        x = W - col * c - col / 2                          # 竖排从右往左读
        d.line([x - col / 2, top, x - col / 2, bot], fill=GOLD[2] + (90,), width=1)
        for r in range(ROWS):
            d.text((x, top + step * (r + 0.5)), SUTRA[k % len(SUTRA)], font=font, fill=INK + (255,), anchor='mm')
            k += 1
    # 金光：绢面剪影外扩 + 模糊，金橙 → 浅金两层；再把整条压成半透明
    out = Image.new('RGBA', (W, H))
    sil = Image.new('L', (W, H)); sil.paste(255, (0, gl, W, gl + ph))
    # 第一版外扩 2·gl、0.75 不透明：金光厚得跟绢面一样高，整条读成三道实心黄杠。现在外扩半个 gl、淡一半，贴边一道细亮线
    for grow, blur, c, a in [(gl // 2 * 2 + 1, gl * 0.45, (255, 176, 30), 0.5), (3, 2, (255, 240, 170), 0.85)]:
        L = Image.new('RGBA', (W, H), c + (0,))
        m = sil.filter(ImageFilter.MaxFilter(min(grow, 51))).filter(ImageFilter.GaussianBlur(blur))
        # 横向无缝：模糊按行只看上下（绢面整条横贯，左右本来就满），边缘列不会被模糊吃掉
        L.putalpha(m.point(lambda v: int(v * a)))
        out.alpha_composite(L)
    out.alpha_composite(paper, (0, gl))
    a = np.array(out)
    body = np.zeros(a.shape[:2], bool); body[gl:gl + ph] = True
    a[..., 3] = np.where(body, a[..., 3] * ALPHA, a[..., 3]).astype(np.uint8)
    return Image.fromarray(a), gl, ph


for name, K, cols, start in LAYERS:
    im, gl, ph = scroll(K, cols, start)
    p = os.path.join(OUT, f'scroll_{name}.webp')
    im.save(p, 'WEBP', quality=90, method=6)
    print(f'scroll_{name}.webp {im.width}×{im.height}  绢面 y {gl}~{gl + ph}  {os.path.getsize(p) // 1024}KB')
