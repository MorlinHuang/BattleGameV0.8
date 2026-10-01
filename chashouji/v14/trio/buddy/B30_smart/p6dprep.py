# P6 方向版：底图 + 蒙版（swing 底 = wind 格，release / thru 底 = throw 格；同 p6base.py 的画布）
import shutil
from PIL import Image, ImageDraw
R='/workspace/art/chashouji/v14/trio/buddy/B30_smart/raw/'
shutil.copy(R+'p6_swing_base.png',R+'p6d_swing_base.png')
shutil.copy(R+'p6_thru_base.png',R+'p6d_release_base.png')
shutil.copy(R+'p6_thru_base.png',R+'p6d_thru_base.png')
def save(n,draw):
    m=Image.new('L',(1024,1024),255); d=ImageDraw.Draw(m); draw(d)
    out=Image.new('RGBA',(1024,1024),(0,0,0,255)); out.putalpha(m); out.save(R+f'p6d_{n}_mask.png')
def swing(d):   # 腰以上全透明 + 身后胯旁（手收到那里）
    d.rectangle([0,0,1023,732],fill=0); d.rectangle([815,0,1023,850],fill=0)
def up(d):      # 腰以上全透明 + 左前方空白
    d.rectangle([0,0,1023,652],fill=0); d.rectangle([0,0,505,880],fill=0)
save('swing',swing); save('release',up); save('thru',up)
