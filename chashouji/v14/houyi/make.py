"""后羿立绘（男生档 4 第三人，2026-09-29）：品红幕原图 → 单层贴图 + 三层火橙外发光，打印量点。
用法：python3 v14/houyi/make.py        → web/assets/world/houyi1_up.webp

用户："嫦娥 vs 后羿，主题为月和日。制作规格和白娘子法海一致"；后羿打"太阳火球 + 金乌"（掌心打出小太阳火球，底下金红火焰云海、三足金乌在火上飞）。
原创脸；红金上古战甲、金兽面护肩、红披风，背金色长弓和箭囊；朝左飞，左掌心前悬一颗燃烧的小太阳（火球从这出）。
src1.png 挑中（朝左、火球在掌心、身子紧凑）；src_alt1 / src_alt2 同一轮另两张。
最低点是右脚战靴尖（在身子右下，同法海的草鞋）。弓梢比头顶高（量 head 取发冠顶，不算弓）。
K 0.6：原图人高 1140（发冠顶 240 → 靴尖 1380）→ 684；连弓、披风铺开的面积跟法海相当。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from crewart import make, rest

HERE = os.path.dirname(__file__)
PTS = dict(
    foot=(922, 1380),       # 右脚靴尖（最低点）
    muzzle=(83, 705),       # 掌心前的小太阳正中（火球从这出）
    tail=(172, 683),        # 手腕（只用来打印 rest）
    body=(518, 630),        # 身子轻轻前后倾的转轴：腰带兽面
    head=(428, 240),        # 发冠顶
    chest=(510, 510),       # 胸口护心镜（身后的日光从这发出）
    face=(405, 368),        # 脸心
)
q = make(os.path.join(HERE, 'src1.png'), os.path.join(HERE, '../../web/assets/world/houyi1_up.webp'),
         'magenta', (40, 150), 0.6,
         [(25, 30, (255, 110, 20)),        # 外：火橙
          (11, 12, (255, 196, 80)),        # 中：金
          (3, 3, (255, 244, 210))], PTS)   # 贴轮廓：近白
print('rest', rest(PTS['tail'], PTS['muzzle'], -1))
