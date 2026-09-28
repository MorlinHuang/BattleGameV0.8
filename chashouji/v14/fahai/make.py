"""法海立绘（男生档 4，2026-09-28）：品红幕原图 → 单层贴图 + 三层金色外发光，打印量点。
用法：python3 v14/fahai/make.py        → web/assets/world/fahai1_up.webp

用户："给男生那边做个法海，与白娘子对立，在男生那边。法海可以向女神发送各种金光咒语，周身也是金光自发光。"
原创脸（提示词写明不像任何演员）：光头戒疤、浓眉、面相严厉；黄僧袍 + 红金格纹袈裟、大串念珠，右手托金钵。
src1.png 挑中（伸出的左掌心有一团金光，咒语从这出），src_alt1 / src_alt2 是同一轮另两张。
姿势：整个人朝左飞、身子略前倾，左臂伸向左边掌心朝外（施咒），袈裟和袖子往右上飘；**最低点是右脚草鞋**（在身子右下，同白娘子的裙角）。
K：原图人高 1265（头顶 118 → 右脚草鞋底 1383）× 0.5 ≈ 633 = 男生侧身高 488 × 1.3（跟白娘子一样比同侧的人大三成）。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from crewart import make, rest

HERE = os.path.dirname(__file__)
PTS = dict(
    foot=(885, 1383),       # 右脚草鞋底（最低点）
    muzzle=(66, 290),       # 左掌心金光正中（咒语从这出）
    tail=(145, 318),        # 手腕（只用来打印 rest）
    body=(495, 570),        # 身子轻轻前后倾的转轴：腰带
    head=(435, 118),        # 头顶
    chest=(450, 450),       # 胸口（金钵，身后的佛光从这发出）
    face=(442, 240),        # 脸心
)
q = make(os.path.join(HERE, 'src1.png'), os.path.join(HERE, '../../web/assets/world/fahai1_up.webp'),
         'magenta', (40, 150), 0.5,
         [(25, 30, (255, 170, 20)),        # 外：金橙
          (11, 12, (255, 220, 110)),       # 中：浅金
          (3, 3, (255, 250, 220))], PTS)   # 贴轮廓：近白
print('rest', rest(PTS['tail'], PTS['muzzle'], -1))
