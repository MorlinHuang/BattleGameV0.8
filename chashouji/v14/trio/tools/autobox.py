"""站在滑板 / 平衡车上的人（后排地面、ride 进场）：在参考帧上自动量 head / fixed / anchor，写回 frames.json，并出一张带框的检查图。
fixed = 脚下的板（最下面 band 行，板在出手几帧里不动）；anchor = 板最低一行的横向中点；head = 剪影最上面 hh 行里最宽那团的外框。
用法：python3 tools/autobox.py <目录> [band 70] [hh 0.17]   → preview/<名>_box.png"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frames import cells_of, PRE

d = sys.argv[1]; band = int(sys.argv[2]) if len(sys.argv) > 2 else 70; hh = float(sys.argv[3]) if len(sys.argv) > 3 else 0.17
spec = json.load(open(os.path.join(d, 'frames.json')))
c = cells_of(d, spec)[spec['ref']]
a = np.array(c)[..., 3] > 128
ys, xs = np.nonzero(a); y0, y1 = ys.min(), ys.max()
b = a[y1 - band:y1 + 1]; bx = np.nonzero(b.any(0))[0]
fixed = [int(bx.min()) - 4, int(y1 - band), int(bx.max()) + 4, int(y1) + 2]
last = np.nonzero(a[y1 - 3:y1 + 1].any(0))[0]
anchor = [round(float(bx.min() + bx.max()) / 2, 1), int(y1)]
H = int((y1 - y0) * hh); t = a[y0:y0 + H]; tx = np.nonzero(t.any(0))[0]
head = [int(tx.min()) - 4, int(y0) - 4, int(tx.max()) + 4, int(y0 + H)]
spec.update(head=head, fixed=fixed, anchor=anchor)
json.dump(spec, open(os.path.join(d, 'frames.json'), 'w'), ensure_ascii=False, indent=1)
im = Image.new('RGBA', c.size, (60, 60, 60, 255)); im.alpha_composite(c); dr = ImageDraw.Draw(im)
dr.rectangle(head, outline=(255, 60, 60), width=3); dr.rectangle(fixed, outline=(60, 160, 255), width=3)
dr.ellipse([anchor[0] - 6, anchor[1] - 6, anchor[0] + 6, anchor[1] + 6], outline=(255, 255, 0), width=3)
name = os.path.basename(os.path.normpath(d)); im.convert('RGB').save(os.path.join(PRE, f'{name}_box.png'))
print(name, 'head', head, 'fixed', fixed, 'anchor', anchor, 'cell', c.size)
