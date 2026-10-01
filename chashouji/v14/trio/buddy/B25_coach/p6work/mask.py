from PIL import Image, ImageDraw
polys={
 'swing':[(0,0),(1024,0),(1024,585),(560,585),(450,575),(0,575)],
 'thru':[(0,0),(1024,0),(1024,545),(500,545),(470,560),(455,600),(455,740),(0,740)],
 'idle2':[(445,160),(850,160),(850,440),(650,440),(600,420),(445,420)],
}
W=Image.new('RGB',(3072,1024))
for i,(k,p) in enumerate(polys.items()):
    m=Image.new('RGBA',(1024,1024),(0,0,0,255)); ImageDraw.Draw(m).polygon(p,fill=(0,0,0,0)); m.save(f'p6_{k}_mask.png')
    b=Image.open(f'p6_{k}_base.png').convert('RGB'); ImageDraw.Draw(b).polygon(p,outline=(0,255,0),width=3); W.paste(b,(i*1024,0))
W.save('/tmp/b25/masks.png')
