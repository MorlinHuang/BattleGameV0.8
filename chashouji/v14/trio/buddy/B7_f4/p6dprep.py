# P6 方向版（B7）：底图 = idle 格（上一轮 p6_idle2_base.png，躯干就在 idle 位置）；蒙版 = 腰线（y<790）以上整宽重画
import numpy as np
from PIL import Image
R='/workspace/art/chashouji/v14/trio/buddy/B7_f4/raw/'
b=Image.open(R+'p6_idle2_base.png').convert('RGB')
m=np.full((1536,1024),255,np.uint8); m[:790]=0
out=Image.new('RGBA',(1024,1536),(0,0,0,255)); out.putalpha(Image.fromarray(m))
for n in ['swing','release','thru']:
    b.save(R+f'p6d_{n}_base.png'); out.save(R+f'p6d_{n}_mask.png')
