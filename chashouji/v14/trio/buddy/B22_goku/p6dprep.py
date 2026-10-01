# P6 方向版（B22）：底图 = throw 格（上一轮 p6_swing_base.png，去掉右下角邻格靴尖碎块）；蒙版 = 腰线以上 + 腰带结 + 带尾
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
R='/workspace/art/chashouji/v14/trio/buddy/B22_goku/raw/'
b=np.array(Image.open(R+'p6_swing_base.png').convert('RGB'))
d=np.abs(b.astype(int)-[255,0,255]).sum(2)>90
lab,k=ndimage.label(d); area=ndimage.sum(d,lab,range(1,k+1)); main=np.argmax(area)+1
b[(lab!=main)&d]=[255,0,255]                     # 碎块铺回幕布
for n in ['swing','release','thru']: Image.fromarray(b).save(R+f'p6d_{n}_base.png')
m=Image.new('L',(1024,1024),255); dr=ImageDraw.Draw(m)
dr.rectangle([0,0,1023,585],fill=0); dr.rectangle([470,585,1023,745],fill=0)   # 腰带结和垂下的带尾一起重画（只重画腰线以上会出两条腰带）
out=Image.new('RGBA',(1024,1024),(0,0,0,255)); out.putalpha(m)
for n in ['swing','release','thru']: out.save(R+f'p6d_{n}_mask.png')
