"""挂件层出图（docs/三人组角色规范.md 第六节）：扇子、靠旗、翎子这类从定妆 / 动作条里单独拆出来、运行时随动作甩的东西。
原图（透明底，或品红 / 绿幕）→ 抠像 → 裁到包围盒 → 缩到跟帧序列同一个比例 → web/assets/trio/<名>.webp，
另出 preview/<名>_grid.png（50 像素格线）量挂住的点 pivot。
比例怎么定：在 preview/<角色>_frames.png 上量这件东西在帧里该有多宽（或多高），填进来。
用法（在 v14/trio 下）：python3 tools/part.py <原图> <名> w|h <像素>
  例：python3 tools/part.py buddy/ref/B18_fan.png B18_fan w 120"""
import os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
TRIO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from frames import load_sheet, grid, OUT, PRE
from crewart import edge_extend

src, name, by, size = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
rgb, al = load_sheet(os.path.join(TRIO, src) if not os.path.isabs(src) else src, 'auto', None)
al = np.where(al < 0.05, 0, al)                     # 透明底四周常有 alpha 很低的噪点，不清掉包围盒会撑到画布边
rgb = edge_extend(rgb, al)
ys, xs = np.nonzero(al > 0.05)
im = Image.fromarray(np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8), 'RGBA').crop((xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3))
k = size / (im.width if by == 'w' else im.height)
im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
os.makedirs(OUT, exist_ok=True); os.makedirs(PRE, exist_ok=True)
im.save(os.path.join(OUT, f'{name}.webp'), 'WEBP', quality=90, method=6)
grid(im, label=f'{name} {im.width}x{im.height}').save(os.path.join(PRE, f'{name}_grid.png'))
print(f'→ web/assets/trio/{name}.webp {im.size}；在 preview/{name}_grid.png 上量 pivot（格线 50 像素、图放大 2 倍）')
