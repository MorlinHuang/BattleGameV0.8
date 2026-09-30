"""G24 华妃扔出去的金护甲（指套）—— 程序画，赛璐璐风（金色锥身 + 暗金明暗带 + 高光 + 几道花丝箍 + 根部一颗红宝石 + 黑描边）。
为什么不从定妆 / 动作条里抠：她的护甲都套在手指上，跟手指、流苏坠子叠在一起，抠不出一件干净的；生图服务当时又在熔断。
4 倍超采样画、LANCZOS 缩回，描边在游戏尺寸（× 0.45）上约 1.5 px，跟人物描边粗细一致。
用法：python3 prop_nailguard.py → web/assets/world/trio_g24_nailguard.webp（尖朝右，根在左；引擎 drawShot 绕中心转）"""
import os
import numpy as np
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../web/assets/world/trio_g24_nailguard.webp')
S = 4                                     # 超采样
L, W0 = 150, 15                           # 成品长、根部半宽（像素）
BEND = 0.0016                             # 往上弯：y = -BEND·x²（护甲是弯的，不是直锥）
N = 80


def spine(u):
    x = u * L
    return np.array([x, -BEND * x * x]), np.array([1.0, -2 * BEND * x])


def outline(off, half):
    """沿中线的一条带：off 法向偏移（−1..1 × 半宽）、half 带的半宽（× 半宽）→ 多边形点（成品像素）"""
    top, bot = [], []
    for i in range(N + 1):
        u = i / N
        p, t = spine(u); t /= np.linalg.norm(t); n = np.array([t[1], -t[0]])      # n 朝上（屏幕 y 向下）
        w = W0 * (1 - u) ** 0.85 + 0.6
        c = p + n * off * w
        top.append(c + n * half * w); bot.append(c - n * half * w)
    return top + bot[::-1]


pad = 12
H = int(BEND * L * L + 2 * W0 + 2 * pad)
img = Image.new('RGBA', ((L + 2 * pad) * S, H * S))
d = ImageDraw.Draw(img)
org = np.array([pad, pad + BEND * L * L + W0])
P = lambda pts: [tuple((org + q) * S) for q in pts]
d.polygon(P(outline(0, 1.0)), fill=(30, 18, 8, 255))                  # 描边（整块黑，下面几层往里收）
d.polygon(P(outline(0, 0.78)), fill=(232, 178, 52, 255))              # 金
d.polygon(P(outline(-0.42, 0.36)), fill=(176, 118, 30, 255))          # 下侧暗金
d.polygon(P(outline(0.44, 0.14)), fill=(255, 236, 150, 255))          # 上侧高光
for u in (0.12, 0.3, 0.5, 0.68):                                      # 花丝箍：横着一道暗线 + 一排小点
    p, t = spine(u); t /= np.linalg.norm(t); n = np.array([t[1], -t[0]]); w = W0 * (1 - u) ** 0.85 * 0.78
    a, b = org + p + n * w, org + p - n * w
    d.line([tuple(a * S), tuple(b * S)], fill=(110, 66, 14, 255), width=int(1.4 * S))
    for k in (-0.5, 0, 0.5):
        c = org + p + t * 4 + n * w * k
        d.ellipse([(c[0] - 1.1) * S, (c[1] - 1.1) * S, (c[0] + 1.1) * S, (c[1] + 1.1) * S], fill=(120, 72, 16, 255))
c0 = org + spine(0)[0]                                                 # 根部开口：椭圆口沿（不画的话根部是一刀齐的平切口，没有描边）
for rx, ry, col in ((W0 * 0.42, W0 + 0.6, (30, 18, 8, 255)), (W0 * 0.3, W0 * 0.8, (120, 76, 18, 255)), (W0 * 0.16, W0 * 0.55, (60, 34, 10, 255))):
    d.ellipse([(c0[0] - rx) * S, (c0[1] - ry) * S, (c0[0] + rx) * S, (c0[1] + ry) * S], fill=col)
g = org + spine(0.2)[0] + np.array([2, 0])                             # 根部红宝石
r = W0 * 0.42
d.ellipse([(g[0] - r - 1.4) * S, (g[1] - r - 1.4) * S, (g[0] + r + 1.4) * S, (g[1] + r + 1.4) * S], fill=(30, 18, 8, 255))
d.ellipse([(g[0] - r) * S, (g[1] - r) * S, (g[0] + r) * S, (g[1] + r) * S], fill=(200, 20, 40, 255))
d.ellipse([(g[0] - r * 0.55) * S, (g[1] - r * 0.7) * S, (g[0] - r * 0.05) * S, (g[1] - r * 0.25) * S], fill=(255, 150, 160, 255))
img = img.resize((img.width // S, img.height // S), Image.LANCZOS)
a = np.array(img); ys, xs = np.nonzero(a[..., 3] > 8)
img = img.crop((xs.min() - 1, ys.min() - 1, xs.max() + 2, ys.max() + 2))
img.save(OUT, 'WEBP', quality=92, method=6)
print('→', os.path.relpath(OUT), img.size)
