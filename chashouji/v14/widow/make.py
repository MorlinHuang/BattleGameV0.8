"""黑蛛女特工立绘（女生档 4 第三人，2026-09-28，规格 trio_spec.md 第二节③）：绿幕原图 → 单层贴图 + 三层暗红外发光，打印量点。
用法：python3 v14/widow/make.py        → web/assets/world/widow1_up.webp

梗：特工吊着一根丝从天花板降下来（吊威亚潜入）。保留暗红齐肩短发、黑色紧身作战服、腰带、腕部装置、冷脸；
防版权改掉的：腰带扣是红色手机定位图钉（不是沙漏）、臂章无任何组织标志、脸不照任何演员、头发是利落短 bob（不是电影大波浪）。
提示词里没写原角色名。src1.png 挑中，src_alt.png 同轮另一张。
**身体竖直**（不倒挂：倒挂时头是最低点，要保证 ≤ y780 就得整个人往上抬）。左手举过头顶抓着丝 —— 丝由运行时从 hand 画到画面顶。
右臂伸直斜朝右下，腕上是腕表式钩索装置（不是蜘蛛侠那种手心朝前两指按下），蛛网从 muzzle 射出。

**绿幕**：暗红头发、黑衣服，品红度在暗红上偏高。K：原图人高 ~1470（发顶 195 不算，手 30 → 靴底 1505），
人本身（发顶 → 靴底）1310 × 0.375 ≈ 490，加上举过头的手总高 ~553。"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from crewart import make, rest

HERE = os.path.dirname(__file__)
PTS = dict(
    foot=(478, 1505),       # 靴底最低点
    muzzle=(858, 600),      # 腕部装置出口
    tail=(750, 545),        # 装置后端（前臂上）：装置轴 = tail → muzzle，约朝右下 27°
    body=(490, 650),        # 前后倾 / 吊着摆的转轴：腰胯
    hand=(428, 30),         # 举过头顶抓丝的手（丝从这连到画面顶）
    head=(500, 200),        # 发顶
    chest=(510, 450),
    face=(515, 290),
)
q = make(os.path.join(HERE, 'src1.png'), os.path.join(HERE, '../../web/assets/world/widow1_up.webp'),
         'green', (60, 150), 0.375,
         [(21, 26, (140, 10, 30)),         # 外：暗红
          (9, 10, (220, 40, 60)),          # 中：红
          (3, 3, (255, 190, 190))], PTS)   # 贴轮廓：浅红
print('rest', rest(PTS['tail'], PTS['muzzle'], +1))
