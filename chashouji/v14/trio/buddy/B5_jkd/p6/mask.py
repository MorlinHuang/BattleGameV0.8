"""P6 蒙版（透明 = 重画）。hitC：腰以上全放开（y < 615）；hitD：y < 650（hitB 的棍横在大腿上，要一起去掉）；
idle2：前手臂 + 脸 + 两者之间（拇指擦鼻子），头发外缘、持棍手、腿全保留。"""
import numpy as np
from PIL import Image, ImageDraw
def save(name, keep):
    m = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0)); m.putalpha(keep); m.save(f'raw/p6_{name}_mask.png')
k = Image.new('L', (1024, 1024), 255); ImageDraw.Draw(k).rectangle((0, 0, 1023, 614), fill=0); save('hitC', k)
k = Image.new('L', (1024, 1024), 255); ImageDraw.Draw(k).rectangle((0, 0, 1023, 649), fill=0); save('hitD', k)
k = Image.new('L', (1024, 1024), 255); d = ImageDraw.Draw(k)
d.rectangle((250, 420, 470, 580), fill=0)          # 前手臂（张开的掌）
d.ellipse((425, 360, 540, 465), fill=0)            # 脸（鼻子嘴眼），头发外缘留原图
d.polygon([(400, 420), (470, 400), (540, 430), (520, 520), (420, 540)], fill=0)   # 手从前面收到鼻子的路径
save('idle2', k)
