from PIL import Image, ImageDraw
import sys
def sheet(items,box,fn,scale=1.0):
    ims=[Image.open(f'/tmp/rv/{a}_{n:05d}.png').crop(box) for a,n in items]
    w,h=ims[0].size; w2,h2=int(w*scale),int(h*scale)
    o=Image.new('RGB',(w2*len(ims),h2)); d=ImageDraw.Draw(o)
    for i,im in enumerate(ims): o.paste(im.resize((w2,h2)),(i*w2,0)); d.text((i*w2+4,4),f'{items[i][0]} {items[i][1]}',fill=(255,0,0))
    o.save(fn); print(fn,o.size)
