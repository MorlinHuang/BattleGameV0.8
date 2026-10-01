from PIL import Image, ImageDraw
R='/workspace/art/chashouji/v14/trio/buddy/B26_gamer/raw/'
polys={
 'swing':[(0,0),(700,0),(700,420),(640,450),(580,470),(560,500),(470,520),(400,525),(300,530),(0,540)],
 'thru':[(0,0),(720,0),(720,380),(650,420),(600,470),(585,570),(270,570),(250,660),(0,670)],
 'idle2':[(318,325),(405,322),(415,415),(385,445),(345,485),(300,508),(235,508),(235,335)],
}
for k,p in polys.items():
    m=Image.new('RGBA',(1024,1024),(0,0,0,255)); ImageDraw.Draw(m).polygon(p,fill=(0,0,0,0)); m.save(R+f'p6_{k}_mask.png')
    b=Image.open(R+f'p6_{k}_base.png').convert('RGB'); o=b.copy(); ImageDraw.Draw(o).polygon(p,outline=(255,0,0)); o.save(f'/tmp/b26/mk_{k}.png')
