"""白娘子的海面（2026-09-28 第三版）：三张手绘海浪生图 → 抠像 → 做成横向无缝循环的长条 → 远 / 中 / 近三层贴图。
用户："水波纹体积感还是做得太假，水波纹不适合做体积感，还是回到 2D 的感觉，但不要太 Q，需要写实些表现"。
第一版 canvas 现画的正弦色带（太 Q）、第二版 Blender 3 渲 2 的 Gerstner 海面（硬切明暗 + 描边，读成塑料）都被否。
这一版是动画电影背景那种手绘写实海浪（浪尖透光的青绿、笔刷画的白沫、深处藏青），动起来靠 sea.js：各层反向平移 + 按列起伏。

原图（生图，品红幕布；far_src 生图时直接出了透明底）：far_src.png / mid_src.png / near_src.png，1659×948 左右。
无缝循环：长条右端 OVER 列和左端 OVER 列叠在一起，沿一条竖向"差最小"的缝（动态规划找）拼接 —— 缝左取右端、缝右取左端，
再沿缝羽化 FEATHER 像素。直接首尾交叉淡化的话浪的剪影会在那一段重影（两道浪线叠在一起）。
跑法：python3 make.py → web/assets/world/sea2_<far|mid|near>.webp，并打印 sea.js SEA2 要填的尺寸。
"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from tidekit import load, solid, seam

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'web', 'assets', 'world')
# 层：原图、输出缩放（= 屏幕上的大小，引擎不再缩放）、往哪个颜色压多少（远处空气透视：发白发灰；近处压暗一点）
LAYERS = [
    ('far',  'far_src.png',  0.40, ((150, 196, 226), 0.30)),
    ('mid',  'mid_src.png',  0.52, ((60, 120, 180), 0.08)),
    ('near', 'near_src.png', 0.66, ((10, 30, 70), 0.12)),
]
KEY = (40, 150)          # 品红度 min(R,B) − G：水里最"品红"的是浪尖透光带边上的一点紫，实测 < 40
# load / solid / seam 在 v14/tidekit.py（2026-09-29 抽出去，四片新潮共用）


for name, src, K, (tint, tk) in LAYERS:
    print(name)
    rgb, al = load(os.path.join(HERE, src), 'magenta', KEY)
    al = solid(al)
    rgb = rgb * (1 - tk) + np.array(tint, np.float32) * tk
    A = seam(rgb, al)
    ys = np.nonzero(A[..., 3].max(1) > 8)[0]
    A = A[ys.min():]
    im = Image.fromarray(A.clip(0, 255).astype(np.uint8), 'RGBA')
    im = im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS)
    im.save(os.path.join(OUT, f'sea2_{name}.webp'), 'WEBP', quality=88, method=6)
    a = np.array(im)[..., 3]
    top = np.argmax(a > 128, axis=0)
    print(f'  sea2_{name}.webp {im.width}×{im.height}  浪上沿 y {top.min()}~{top.max()}  {os.path.getsize(os.path.join(OUT, f"sea2_{name}.webp")) // 1024}KB')
