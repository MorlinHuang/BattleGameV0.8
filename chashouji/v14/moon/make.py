"""月亮查岗使立绘（女生档 4 第二人，2026-09-28，规格 shots/review/trio/trio_spec.md 第二节②）：绿幕原图 → 单层贴图 + 三层粉色外发光，打印量点。
用法：python3 v14/moon/make.py        → web/assets/world/moon1_up.webp

梗：「代表月亮，查你手机！」。保留金色丸子头 + 两条超长双马尾（剪影）、水手领短裙、及膝长靴、魔法少女短杖；
防版权改掉的：薄荷绿领 + 粉色大蝴蝶结（不是蓝领红结白衣）、额头是手机形小宝石（不是月牙）、胸口是爱心锁（不是变身胸针）、
杖头是放大镜套爱心（不是月亮杖）。提示词里没写原角色名。src1.png 挑中，src_alt.png 是同一轮另一张。
短杖本来就斜朝右下（spr.rest），瞄准时整个人只小幅前后倾（crew.js whole）。

**绿幕**：她一身粉（蝴蝶结、靴子），按品红抠会抠穿。薄荷绿领 / 裙子在绿键上 k ≈ 40~80，所以 KEY 的不透明上限放到 100
（幕布 k ≈ 245，中间只剩边缘过渡带）。量点按 src1.png 原图像素，换原图要重量。
K：原图人高 ~1490（丸子头 10 → 靴尖 1500），× 0.38 ≈ 566 = truth2 的人高。"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from crewart import make, rest

HERE = os.path.dirname(__file__)
PTS = dict(
    foot=(430, 1497),       # 靴尖最低点
    muzzle=(918, 822),      # 放大镜正中（爱心光流从这出）
    tail=(695, 640),        # 握杖的手：杖轴 = tail → muzzle，约朝右下 39°
    body=(470, 560),        # 整个人前后倾的转轴：腰胯
    head=(505, 20),         # 头顶（两个丸子中间）
    chest=(545, 390),       # 胸口（爱心锁）
    face=(555, 175),        # 脸心
)
q = make(os.path.join(HERE, 'src1.png'), os.path.join(HERE, '../../web/assets/world/moon1_up.webp'),
         'green', (100, 200), 0.38,
         [(21, 26, (230, 60, 150)),        # 外：玫粉
          (9, 10, (255, 140, 200)),        # 中：粉
          (3, 3, (255, 240, 250))], PTS)   # 贴轮廓：近白粉
print('rest', rest(PTS['tail'], PTS['muzzle'], +1))
