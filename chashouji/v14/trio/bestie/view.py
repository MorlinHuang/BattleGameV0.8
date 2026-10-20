"""看候选：python3 view.py a.png b.png ... → /tmp/v.jpg（带 alpha 的铺灰底，并打印模式与幕布占比）"""
import sys
from PIL import Image
ims = []
for f in sys.argv[1:]:
    im = Image.open(f)
    print(f, im.size, im.mode)
    if im.mode == 'RGBA':
        g = Image.new('RGBA', im.size, (128, 128, 128, 255)); g.alpha_composite(im); im = g
    ims.append(im.convert('RGB').resize((im.width // 2, im.height // 2)))
c = Image.new('RGB', (sum(i.width for i in ims), max(i.height for i in ims)), 'white'); x = 0
for i in ims: c.paste(i, (x, 0)); x += i.width
c.save('/tmp/v.jpg', quality=85)
