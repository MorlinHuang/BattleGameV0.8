import sys; sys.path.insert(0,'/tmp/rv')
from mock import scene
exec(open('/tmp/rv/mk1.py').read().split("R={}")[0].split("from PIL")[1].join(["from PIL",""]) if False else "")
from PIL import Image, ImageDraw
def sheet(fns, out, labels, crop=(0,150,960,1350), w=400):
    ims=[Image.open(f).crop(crop) for f in fns]; h=int(ims[0].height*w/ims[0].width)
    o=Image.new('RGB',(w*len(ims),h)); d=ImageDraw.Draw(o)
    for i,im in enumerate(ims): o.paste(im.resize((w,h)),(i*w,0)); d.text((i*w+6,26),labels[i],fill=(255,255,0))
    o.save(out)
poses=['p50','p70','p95','pos20','p5']
V={
 'S4_T_board': [dict(kind='T',s=0.9,x=160,y=945,mode='lean+board',front=False)],
 'X7': [dict(kind='B',skin=0,s=0.86,x=75,y=945,front=False),
        dict(kind='B',skin=1,s=0.74,x=95,y=735,front=False),
        dict(kind='T',s=0.86,x=250,y=880,mode='lean+board',front=False)],
}
for name,spec in V.items():
    fns=[]
    for p in poses:
        fn=f'/tmp/rv/m_{name}_{p}.png'; st=scene(p,spec,fn,name); fns.append(fn)
        print(name,p,[(x['who'],float(x.get('visible',0)),float(x.get('face',-1)),float(x.get('onscreen',-1)),x.get('th')) for x in st], flush=True)
    sheet(fns,f'/tmp/rv/ms_{name}.png',poses)
