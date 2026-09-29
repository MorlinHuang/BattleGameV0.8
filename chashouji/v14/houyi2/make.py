"""后羿第二版立绘：持弓拉弦（2026-09-29）。品红幕原图 → 两层贴图（身子 up + 拉弦的右前臂 arm），同一个裁边框、同一个倍率，打印量点。
用法：python3 v14/houyi2/make.py → web/assets/world/houyi2_up.webp、houyi2_arm.webp

用户："后羿进攻女生的特效，是可以连续射出箭矢飞向女生。从后羿手中的弓箭射出，所以后羿的立绘也需要相应的动作"；
射箭选"匀速连射"，立绘选"立绘 + 引擎画弦和箭"：立绘只画人和弓，弦和搭在弦上的箭引擎现画（crew.js drawBow），
拉弦的右前臂单独一层，跟着弦前后挪（HOUYI.spr.arm.axis）。
  · src1.png：拿第一版立绘（v14/houyi/src1.png，掌心托小太阳）图生图改姿势 —— 朝左下 45° 俯射：左臂斜伸向左下握金弓，
    右手拉到右脸颊（满弓的靠位），手肘高抬；提示词写死"没有弓弦、没有箭"（生图照做了，弓两梢之间是空的幕布）。
    第一轮（src_try_level*.png 没留）手臂是水平朝左的：女生在他左下方很陡的地方，箭斜着射出去跟弓对不上。
    src_alt1 / src_alt2 是同一轮另两张。
  · inpaint1.png：src1 上把右手和前臂蒙掉（armmask_L.png 白 = 蒙掉）重绘成后面的东西（下巴、脖子、领口、红披风）——
    身子那层要它：手臂层前后挪时，原来手臂的位置露出来的是这些，不是一个洞。生图把整张都重画了一遍（背景都变了），
    所以只取蒙版里那块、羽化 3 像素贴回 src1（body_src.png）。
  · 手臂层：从 src1 按同一个蒙版（往里收 2 像素、羽化）抠出来；外发光只烘在身子那层（按整个人 —— 连手臂 —— 的剪影），
    手臂层不烘（它压在脸和肩膀上，烘了脸上一圈火光）。
K 0.6：原图人高 ≈ 1230（发尾最高 ≈ 60 → 弓下梢 ≈ 1290）；屏幕上的缩放在 main.js G4STAND.houyi 按实心面积对齐嫦娥。
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from crewart import cut, edge_extend, rest, PAD

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'web', 'assets', 'world')
K, MARGIN = 0.6, 6
GLOW = [(25, 30, (255, 110, 20)), (11, 12, (255, 196, 80)), (3, 3, (255, 244, 210))]   # 同第一版：外火橙、中金、贴轮廓近白
PTS = dict(
    foot=(826, 1124),       # 右脚战靴尖（悬停位的"脚底"）
    muzzle=(152, 860),      # 握弓的拳头上沿：箭从这出（箭台）
    nock=(424, 551),        # 右手捏弦的指尖：满弓时弦被拉到这
    top=(40, 424),          # 弓上梢挂弦处
    bot=(472, 1276),        # 弓下梢挂弦处
    body=(500, 760),        # 身子倾的转轴：腰
    head=(360, 393),        # 发冠顶
    chest=(488, 675),       # 胸口护心镜（身后的日光从这发出）
    halo=(345, 480),        # 头后日轮
    face=(330, 520),        # 脸心
)

m = np.array(Image.open(os.path.join(HERE, 'armmask_L.png')).convert('L')).astype(np.float32) / 255
src = Image.open(os.path.join(HERE, 'src1.png')).convert('RGB')
soft = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
Image.composite(Image.open(os.path.join(HERE, 'inpaint1.png')).convert('RGB'), src, soft).save(os.path.join(HERE, 'body_src.png'))

rgb0, al0 = cut(os.path.join(HERE, 'src1.png'), 'magenta', (40, 150))          # 整个人（含手臂）：裁边框、外发光按它
rgb1, al1 = cut(os.path.join(HERE, 'body_src.png'), 'magenta', (40, 150))      # 身子（手臂处补成了后面的东西）
arm_m = ndimage.gaussian_filter(ndimage.binary_erosion(m > 0.5, iterations=2).astype(np.float32), 1.5)
ys, xs = np.nonzero(np.maximum(al0, al1) > 0.05)
x0, y0 = max(0, xs.min() - MARGIN), max(0, ys.min() - MARGIN)
x1, y1 = min(al0.shape[1], xs.max() + 1 + MARGIN), min(al0.shape[0], ys.max() + 1 + MARGIN)


def layer(rgb, al):
    rgb = edge_extend(rgb.copy(), al)
    px = np.dstack([rgb, al * 255]).clip(0, 255).astype(np.uint8)[y0:y1, x0:x1]
    im = Image.fromarray(px, 'RGBA')
    im = im.resize((round(im.width * K), round(im.height * K)), Image.LANCZOS)
    res = Image.new('RGBA', (im.width + 2 * PAD, im.height + 2 * PAD))
    res.alpha_composite(im, (PAD, PAD))
    return res


body = layer(rgb1, al1)
sil = layer(rgb0, np.maximum(al0, al1)).split()[3]
lit = Image.new('RGBA', body.size)
for grow, blur, c in GLOW:
    L = Image.new('RGBA', body.size, tuple(c) + (0,))
    L.putalpha(sil.filter(ImageFilter.MaxFilter(grow)).filter(ImageFilter.GaussianBlur(blur)))
    lit.alpha_composite(L)
lit.alpha_composite(body)
lit.save(os.path.join(OUT, 'houyi2_up.webp'), 'WEBP', quality=90, method=6)
arm = layer(rgb0, al0 * arm_m)
arm.save(os.path.join(OUT, 'houyi2_arm.webp'), 'WEBP', quality=90, method=6)

tr = lambda p: [round((p[0] - x0) * K + PAD), round((p[1] - y0) * K + PAD)]
q = {n: tr(p) for n, p in PTS.items()}
print('size', lit.size, ' '.join(f'{n} {v}' for n, v in q.items()))
ax = np.subtract(PTS['nock'], PTS['muzzle']); ax = ax / np.hypot(*ax)
print('axis（箭台 → 弦，往后拉的方向）', ax.round(3).tolist(), ' rest', rest(PTS['nock'], PTS['muzzle'], -1))
