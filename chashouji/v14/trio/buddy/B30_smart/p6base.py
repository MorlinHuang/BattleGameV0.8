import numpy as np
from PIL import Image, ImageDraw, ImageFilter
R='/workspace/art/chashouji/v14/trio/buddy/B30_smart/raw/'
sh=Image.open(R+'act_a1.png').convert('RGB')
BG=(255,0,255)
a=np.array(sh).astype(int)
def person(box):
    c=np.array(sh.crop(box)).astype(int)
    mg=(c[...,0]>170)&(c[...,2]>170)&(c[...,1]<90)
    out=c.copy(); out[mg]=BG          # 幕布统一成纯品红
    return Image.fromarray(out.astype(np.uint8))
# name: crop box, paste pos, waist y (canvas)
cfg={'swing':((540,0,1024,762),(470,240)),
     'thru':((0,768,556,1536),(400,230)),
     'idle2':((0,0,540,768),(260,230))}
for n,(box,pos) in cfg.items():
    cv=Image.new('RGB',(1024,1024),BG); cv.paste(person(box),pos); cv.save(R+f'p6_{n}_base.png')
