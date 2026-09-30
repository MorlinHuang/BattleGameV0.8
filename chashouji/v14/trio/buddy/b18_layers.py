"""B18 唐伯虎定妆（审查 2）：人和扇子分两层。扇子单独生图（绿幕），斜插在后背，运行时出手那帧隐藏。
输出（都是 RGBA，同一张画布，叠起来就是 B18.png）：
  ref/B18_body.png  人
  ref/B18_fan.png   扇子层（画在人身后）
  ref/B18.png       合成的定妆图（总览用）
原图：人 src/B18_body_src.png（品红幕）、扇 src/B18_fan_src.png（绿幕），抠像走 crewart.cut。"""
import os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../..'))
from crewart import cut, edge_extend
REF = os.path.join(HERE, 'ref')
FAN_W = 440        # 扇面宽（像素）；人头约 150 宽，扇面露出远大于一个头
FAN_ROT = -40      # 顺时针转 40°，斜插
FAN_AT = (720, 520)  # 扇轴（扇子最下端）落在后背哪一点：人朝左，后背在右边

def rgba(path, screen):
    rgb, al = cut(path, screen, (40, 150))
    return Image.fromarray(np.dstack([edge_extend(rgb, al), al * 255]).clip(0, 255).astype(np.uint8), 'RGBA')

body = rgba(os.path.join(HERE, 'src', 'B18_body_src.png'), 'magenta')
fan = rgba(os.path.join(HERE, 'src', 'B18_fan_src.png'), 'green')
fan = fan.crop(fan.getbbox())
fan = fan.resize((FAN_W, round(fan.height * FAN_W / fan.width)), Image.LANCZOS)
pivot = (fan.width / 2, fan.height * 0.78)              # 扇轴约在包围盒 78% 高处（下面是流苏）
big = Image.new('RGBA', (fan.width * 2, fan.height * 2)); big.paste(fan, (fan.width // 2, fan.height // 2))
big = big.rotate(FAN_ROT, resample=Image.BICUBIC, center=(pivot[0] + fan.width // 2, pivot[1] + fan.height // 2))
layer = Image.new('RGBA', body.size)
layer.alpha_composite(big, (round(FAN_AT[0] - pivot[0] - fan.width // 2), round(FAN_AT[1] - pivot[1] - fan.height // 2)))
body.save(os.path.join(REF, 'B18_body.png'))
layer.save(os.path.join(REF, 'B18_fan.png'))
out = layer.copy(); out.alpha_composite(body)
out.save(os.path.join(REF, 'B18.png'))
print('fan layer bbox', layer.getbbox(), 'canvas', body.size)
