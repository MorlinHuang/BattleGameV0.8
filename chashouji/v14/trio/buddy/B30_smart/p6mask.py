import numpy as np
from PIL import Image, ImageDraw
R='/workspace/art/chashouji/v14/trio/buddy/B30_smart/raw/'
def save(n,draw):
    m=Image.new('L',(1024,1024),255); d=ImageDraw.Draw(m); draw(d)
    out=Image.new('RGBA',(1024,1024),(0,0,0,255)); out.putalpha(m); out.save(R+f'p6_{n}_mask.png')
save('swing',lambda d:d.rectangle([0,0,1023,732],fill=0))
def thru(d):
    d.rectangle([0,0,1023,652],fill=0); d.rectangle([0,0,505,880],fill=0)
save('thru',thru)
def idle2(d):
    d.rounded_rectangle([520,300,770,630],radius=60,fill=0)
save('idle2',idle2)
