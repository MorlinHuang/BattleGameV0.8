import numpy as np
from PIL import Image
from scipy import ndimage
R='/workspace/art/chashouji/v14/trio/buddy/B10_mahjong/raw/'
sh=np.array(Image.open(R+'act_a1.png').convert('RGB'))
MAG=np.array([255,0,255],np.uint8)
# name: (crop box in sheet, paste pos, waist y in crop-local coords)
cfg={'swing':((552,10,1000,742),(380,160),None),
     'thru':((10,850,526,1440),(330,300),None),
     'idle2':((45,110,500,730),(300,200),None)}
for n,(bb,pos,_) in cfg.items():
    c=sh[bb[1]:bb[3],bb[0]:bb[2]]
    body=~((c[...,0]>180)&(c[...,2]>180)&(c[...,1]<110))
    can=np.tile(MAG,(1024,1024,1)); cb=np.zeros((1024,1024),bool)
    x,y=pos; h,w=body.shape
    can[y:y+h,x:x+w]=c; cb[y:y+h,x:x+w]=body
    Image.fromarray(can).save(R+f'p6_{n}_base.png')
    np.save(f'/tmp/b10/{n}_body.npy',cb)
    print(n,'crop',bb,'pos',pos)
