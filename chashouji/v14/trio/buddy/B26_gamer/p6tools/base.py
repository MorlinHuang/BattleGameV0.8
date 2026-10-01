import numpy as np, json
from PIL import Image
from scipy import ndimage
R='/workspace/art/chashouji/v14/trio/buddy/B26_gamer/raw/'
im=np.array(Image.open(R+'act_a1.png').convert('RGBA'))
a=im[...,3]
lab,k=ndimage.label(ndimage.binary_dilation(a>25,iterations=3))
cells={'idle':4,'wind':2,'throw':3}  # will verify below
objs=ndimage.find_objects(lab)
info={}
for name,(fr,li) in {'idle2':('idle',None),'swing':('wind',None),'thru':('throw',None)}.items(): pass
# reading order: top row (y<700): x small first
comps=[i+1 for i,s in enumerate(objs) if (lab[s]==i+1).sum()>5000]
comps.sort(key=lambda i:(objs[i-1][0].start>700, objs[i-1][1].start))
order=dict(zip(['idle','wind','throw','follow'],comps))
for new,src in [('idle2','idle'),('swing','wind'),('thru','throw')]:
    li=order[src]; sy,sx=objs[li-1]
    y0,y1,x0,x1=sy.start,sy.stop,sx.start,sx.stop
    c=im[y0:y1,x0:x1].copy(); c[...,3]=c[...,3]*(lab[y0:y1,x0:x1]==li)
    h,w=c.shape[:2]; px=(1024-w)//2; py=(1024-h)//2
    rgba=np.zeros((1024,1024,4),np.uint8); rgba[py:py+h,px:px+w]=c
    Image.fromarray(rgba).save(f'/tmp/b26/{new}_orig.png')
    al=rgba[...,3:]/255.0
    rgb=rgba[...,:3]*al+np.array([0,255,0])*(1-al)
    Image.fromarray(rgb.round().clip(0,255).astype(np.uint8)).save(R+f'p6_{new}_base.png')
    info[new]=dict(src=src,box=[x0,y0,x1,y1],pos=[px,py])
print(info); json.dump(info,open('/tmp/b26/info.json','w'))
