"""二郎·打码神立绘 + 哮天犬贴图（男生档 4 第三人，2026-09-28，规格 trio_spec.md 第二节⑥）：绿幕原图 → 单层贴图 + 三层金色外发光，打印量点。
用法：python3 v14/erlang/make.py        → web/assets/world/erlang1_up.webp、dog1_up.webp

梗：天眼本来"看穿一切"，这里反过来 —— 天眼一开把证据全部打上马赛克；旁边一只胖哮天犬把飞出来的聊天气泡叼走吃掉。
保留额头竖眼、银甲、长披风、三尖两刃刀（只当造型，不攻击）；神话人物本身是公版。
不照 2022《新神榜：杨戬》/ 1996 电视剧 / 1999《宝莲灯》任何一版：银甲配墨蓝披风、长发高束，自己组合的。脚下一团祥云画进贴图
（悬停的理由，跟女神的尾焰同一个作用）。src1.png 挑中。原图里的竖眼很小，**天眼睁开的金光由运行时画在 eye 点上**（crew.js drawErlangAura）。
哮天犬 dog_src1.png：圆滚滚的柴犬 / 田园犬表情包风，单独一张贴图，运行时让它在祥云边上绕、扑咬气泡。

**绿幕**：银甲、墨蓝、白云都不含绿。K：原图人高 ~1485（发冠 5 → 云底 1490），× 0.38 ≈ 564。"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from crewart import make

HERE = os.path.dirname(__file__)
PTS = dict(
    foot=(500, 1488),       # 祥云最低点
    eye=(400, 177),         # 额头天眼（金光从这射出）
    muzzle=(400, 177),
    body=(460, 560),        # 前后倾的转轴：腰胯
    head=(440, 30),
    chest=(450, 400),
)
q = make(os.path.join(HERE, 'src1.png'), os.path.join(HERE, '../../web/assets/world/erlang1_up.webp'),
         'green', (60, 150), 0.38,
         [(21, 26, (200, 130, 20)),        # 外：暗金
          (9, 10, (255, 200, 60)),         # 中：暖金
          (3, 3, (255, 248, 210))], PTS)   # 贴轮廓：白金
# 哮天犬：朝左跑，嘴（mouth）是叼气泡的点；K 0.16 → 身宽 ~170 贴图像素，站在他脚边的祥云上跟他腿差不多高
d = make(os.path.join(HERE, 'dog_src1.png'), os.path.join(HERE, '../../web/assets/world/dog1_up.webp'),
         'green', (60, 150), 0.16,
         [(3, 2, (255, 250, 235))], dict(mouth=(150, 560), foot=(560, 1060)))
