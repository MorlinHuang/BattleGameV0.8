"""两张条分开生图时人画得大小不一（B6 走路条的人只有出手条的 0.76）：frames.py 的 scale 是全部帧共用一个搜索范围，
放宽到能容下两张条，同一张条里转了头 / 被手挡了脸的格就会被头匹配带偏（B6 throw 放大 1.5 倍）。
所以先把整张条按一个倍数缩放到和参考条一样大，frames.py 的 scale 收窄到 ±5%。
用法：python3 prescale.py <原图> <新图> <倍数>"""
import sys
from PIL import Image
src, dst, k = sys.argv[1], sys.argv[2], float(sys.argv[3])
im = Image.open(src).convert('RGBA')
im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS).save(dst)
print(dst, im.size, '→', (round(im.width * k), round(im.height * k)))
