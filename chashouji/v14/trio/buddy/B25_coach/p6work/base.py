import sys, json; sys.path.insert(0,'tools'); sys.path.insert(0,'..')
from frames import load_sheet
import numpy as np
from PIL import Image
from scipy import ndimage
R='buddy/B25_coach/raw/'
info={}
for sheet,new,src,li,pos in [('act_a1','swing','raise',1,(330,190)),('act_a1','thru','throw',3,(330,250)),('act_b1','idle2','pop',3,(256,240))]:
    rgb,al=load_sheet(R+sheet+'.png','auto',None)
    lab=ndimage.label(ndimage.binary_dilation(al>0.1,iterations=3))[0]
    sy,sx=ndimage.find_objects((lab==li).astype(int))[0]
    y0,y1,x0,x1=max(0,sy.start-4),sy.stop+4,max(0,sx.start-4),sx.stop+4
    a=al[y0:y1,x0:x1]*(lab[y0:y1,x0:x1]==li); c=rgb[y0:y1,x0:x1]
    h,w=a.shape; px,py=pos
    rgba=np.zeros((1024,1024,4),np.float32); rgba[py:py+h,px:px+w,:3]=c; rgba[py:py+h,px:px+w,3]=a*255
    Image.fromarray(rgba.round().clip(0,255).astype(np.uint8),'RGBA').save(f'/tmp/b25/{new}_orig.png')
    A=rgba[...,3:]/255; base=rgba[...,:3]*A+np.array([255,0,255])*(1-A)
    Image.fromarray(base.round().clip(0,255).astype(np.uint8)).save(R+f'p6_{new}_base.png')
    info[new]=dict(src=src,cellbox=[x0,y0,x1,y1],pos=pos,size=[w,h])
print(info); json.dump(info,open('/tmp/b25/info.json','w'))
