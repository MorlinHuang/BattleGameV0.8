"""嫦娥立绘（女生档 4 第三人，2026-09-29）：绿幕原图 → 单层贴图 + 三层月白外发光，打印量点。
用法：python3 v14/change/make.py        → web/assets/world/change1_up.webp

用户："新增一对人物，嫦娥 vs 后羿，主题为月和日。制作规格和白娘子法海一致"；嫦娥打"月光 + 玉兔"（月牙光刃，底下月夜银云海、玉兔在云上跑）。
原创动漫脸；月白 + 冰蓝浅紫广袖汉服、飞天髻月牙发饰、长披帛；朝右飞，右掌心上方悬一弯银白小月牙（光刃从这出）。
src1.png 挑中；src_alt1 同一轮另一张；src_alt2 是生图直接给的透明底版本（alpha 干净但外圈烘了一层黑底白光，没用）。
**绿幕**：她一身淡紫薄纱，第一轮品红幕上纱透着品红、跟幕布同色相，抠不开（品红度在淡紫上 20+）。绿幕上纱透出来是绿的，
按绿度抠成半透明，整张去溢色再压青（spill='decyan'：纱被生图画成了偏青）。
没有脚：最低点是裙摆最下沿（foot）。
K 0.6：原图人高 1355（发髻顶 125 → 裙摆最低 1480）→ 813；整个人铺开的面积跟白娘子（屏幕上 737×711）相当（用户对白娘子 / 法海大小的要求是"看面积"）。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from crewart import make, rest

HERE = os.path.dirname(__file__)
PTS = dict(
    foot=(420, 1478),       # 裙摆最低点
    muzzle=(922, 570),      # 掌心上方的月牙正中（光刃从这出）
    tail=(840, 645),        # 手腕（只用来打印 rest）
    body=(570, 660),        # 身子轻轻前后倾的转轴：腰
    head=(615, 125),        # 发髻顶
    chest=(705, 495),       # 胸口（身后的月光从这发出）
    face=(705, 338),        # 脸心
)
q = make(os.path.join(HERE, 'src1.png'), os.path.join(HERE, '../../web/assets/world/change1_up.webp'),
         'green', (20, 150), 0.6,
         [(25, 30, (150, 180, 255)),       # 外：月蓝
          (11, 12, (215, 228, 255)),       # 中：银白
          (3, 3, (255, 255, 255))], PTS, spill='decyan')
print('rest', rest(PTS['tail'], PTS['muzzle'], +1))
