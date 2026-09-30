"""G15 船头做成同一张（审查第五批打回 / 规范第七轮修订第 1 条）。每次 frames.py build 之后跑一次（在 v14/trio 下：python3 bestie/G15_rose/bow.py）。

生图每一格都重画了一遍船头：立柱跳位、忽多忽少，船体下沿差到 5 屏幕 px。这里把 idle 的船头垫到在场各帧（wind / throw / follow / open / idle2）：
  · 船头 = 低饱和的白 / 浅灰、y ≥ 300、跟甲板连成一片的那一块（只留长条和大块，蕾丝小花进不来），再往外扩 2 px 收描边（浅灰 + 近黑）；
  · 画里的前后：蕾丝裙摆、小腿在栏杆后面，高跟鞋在栏杆前面（踩在甲板上、盖住中间那根横杆）。所以每帧拆成
    后层（人，去掉自己画的船头）→ idle 的船头 → 前层（鞋框 SHOE 里人的像素）三层叠；
  · 后层里原来被自己那份栏杆占着、现在 idle 栏杆又没盖到的缝（栏杆错开几 px），从四周的人像素往里扩散补上。
船尾往左接长：原来的格左边只到屏幕 x 31。顺着甲板斜度把栏杆、甲板、船体一列列往左接 EXT px（立柱按间距 PITCH 复制），下沿按格底平切。
接长的那截画进图集：每格往左加宽 EXT（cell 362 → 562），图集 json 的 cell / anchor / head 跟着改（x + EXT），cfg 里格内坐标同样 + EXT。
不做成挂件：挂件在遮挡扫描（combo_scan）里算认人点，船尾是布景，算进剪影才对。
frames.py build 出来的是 362 宽的格；已经加宽过的图集再跑会直接退出（先重新 build）。"""
import json
import os, numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, '../../../../web/assets/trio')
P = os.path.join(WEB, 'G15_rose.webp')
CW, CH, COLS = 362, 435, 4
NAMES = ['idle', 'wind', 'throw', 'follow', 'grip', 'step', 'open', 'idle2']
ON = ['wind', 'throw', 'follow', 'open', 'idle2']        # grip / step 不上场
SHOE = (180, 338, 266, 374)                              # 鞋框（格内 x0, y0, x1, y1）：脚踝带以下
LEFT, PITCH, EXT, ZONE = 30, 97, 200, 6                          # 船头最左那一列往里一点、立柱间距、往左接多长


def hsv(c):
    rgb = c[..., :3] / 255.0
    mx, mn = rgb.max(-1), rgb.min(-1)
    return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0), mx


def boat_mask(c):
    s, v = hsv(c)
    n = (c[..., 3] > 60) & (s < 0.13) & (v > 0.45)
    n[:300] = False
    # 栏杆是横着 / 竖着的长条、甲板船体是大块：只留装得下 11 px 横线、11 px 竖线或 7 × 7 方块的地方。
    # 蕾丝上的白色小花（圆的、8 px 上下、四周黑描边）装不下，就不会顺着贴在栏杆上的那几朵漫进来
    n = nd.binary_opening(n, np.ones((1, 11))) | nd.binary_opening(n, np.ones((11, 1))) | nd.binary_opening(n, np.ones((7, 7)))
    lab, k = nd.label(n)
    b = lab == np.argmax(nd.sum(n, lab, range(1, k + 1))) + 1
    edge = (c[..., 3] > 20) & ((s < 0.3) | (v < 0.15))   # 描边是近黑（v < 0.15 时饱和度没意义）
    for _ in range(2):
        b |= nd.binary_dilation(b) & edge
    return b


def fill(rgb, known, hole):
    """hole 里的像素从 known 往里一圈圈扩散（邻域平均）补上"""
    rgb, known = rgb.copy(), known.copy()
    todo = hole & ~known
    while todo.any():
        w = nd.uniform_filter(known.astype(float), 3)
        acc = np.stack([nd.uniform_filter(rgb[..., i] * known, 3) for i in range(3)], -1)
        ring = todo & (w > 0.05)                         # 至少一个已知邻居（1/9）；浮点噪声的 1e-17 不算
        if not ring.any():
            break
        rgb[ring] = acc[ring] / w[ring][:, None]
        known |= ring
        todo &= ~ring
    return rgb


def cell(a, n):
    i = NAMES.index(n)
    return (slice(i // COLS * CH, i // COLS * CH + CH), slice(i % COLS * CW, i % COLS * CW + CW))


META = os.path.join(WEB, 'G15_rose.json')
meta = json.load(open(META))
if meta['cell'][0] != CW:
    raise SystemExit('图集已经加宽过（cell %s）：先 python3 tools/frames.py bestie/G15_rose build 再跑' % meta['cell'])
a = np.array(Image.open(P).convert('RGBA')).astype(float)
idle = a[cell(a, 'idle')]
IBM = boat_mask(idle)
IB = np.where(IBM[..., None], idle, 0)       # idle 的船头层
cover = IB[..., 3] > 200
sx0, sy0, sx1, sy1 = SHOE
inbox = np.zeros((CH, CW), bool); inbox[sy0:sy1, sx0:sx1] = True

for n in ON:
    c = a[cell(a, n)]
    # 自己那份栏杆：连通的那一大块之外，idle / 自己船头附近 ZONE px 里所有「不确定是人」的像素（近白、近黑描边、抠像留下的半透明杂色）也算，
    # 不然错开几 px 的旧栏杆会留下黑描边和色点。确定是人 = 不透明且有颜色（蕾丝米色饱和度 0.17 起、裙子藏青、皮肤）。鞋框里不动（鞋的黑描边）
    s, v = hsv(c)
    sure = (c[..., 3] > 200) & (s >= 0.15) & (v >= 0.15)
    zone = nd.binary_dilation(IBM | boat_mask(c), iterations=ZONE) & ~inbox
    b = boat_mask(c) | (zone & (c[..., 3] > 0) & ~sure)
    person = (c[..., 3] > 0) & ~b
    back = np.where((person & ~inbox)[..., None], c, 0)
    front = np.where((person & inbox)[..., None], c, 0)
    # 缝：自己的栏杆拿掉了、idle 栏杆没盖到、两边都是人（后层闭运算以内）
    hole = b & ~cover & nd.binary_closing(person & ~inbox, np.ones((9, 9))) & ~inbox
    back[..., :3] = fill(back[..., :3], back[..., 3] > 200, hole)
    back[hole, 3] = 255
    out = back
    for lay in (IB, front):                                # alpha 叠：后层 < 船头 < 鞋
        al = lay[..., 3:4] / 255.0
        rgb = lay[..., :3] * al + out[..., :3] * (out[..., 3:4] / 255.0) * (1 - al)
        A = al + out[..., 3:4] / 255.0 * (1 - al)
        out = np.concatenate([np.where(A > 0, rgb / np.maximum(A, 1e-6), 0), A * 255], -1)
    a[cell(a, n)] = out
    print(n, 'boat px', int(b.sum()), 'hole filled', int(hole.sum()))


# 船尾接长：栏杆、甲板、船体都是顺着甲板斜度的直线，拿 LEFT 右边一列（没有立柱）往左一列列平移、每往左一格往下挪 SLOPE；
# 立柱按 PITCH 从 idle 最左那根（POST）往左复制。斜度 = 这一列和往右 GAP 列那一列按竖向错位做互相关（只在立柱之间量）。格底平切。
m = IB[..., 3] > 128
BASE, GAP, POST = LEFT + 2, 24, (57, 69)
c0, c1 = m[:, BASE].astype(float), m[:, BASE + GAP].astype(float)
d = max(range(0, 20), key=lambda d: (c0[d:] * c1[:CH - d]).sum())
SLOPE = d / GAP
ext = np.zeros((CH, EXT + LEFT, 4))
def put(t, col, sh):
    sh = int(round(sh))
    if sh < CH: ext[sh:, t + EXT] = col[:CH - sh]
for t in range(-EXT, LEFT):
    put(t, IB[:, BASE], SLOPE * (BASE - t))
    for k in range(1, 4):                                  # 立柱：idle 那根往左第 k 根
        x = t + k * PITCH
        if POST[0] <= x < POST[1]:
            put(t, IB[:, x], SLOPE * k * PITCH)
# 加宽：每格左边垫 EXT 列，船尾那截垫在人和船头下面（在场各帧 + idle；grip / step 不上场，只加宽）
NW = CW + EXT
wide = np.zeros((a.shape[0] // CH * CH, NW * COLS, 4))
for n in NAMES:
    i = NAMES.index(n); r, c = i // COLS, i % COLS
    cellimg = np.zeros((CH, NW, 4))
    if n in ON + ['idle']:
        cellimg[:, :EXT + LEFT] = ext
    src = a[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW]
    al = src[..., 3:4] / 255.0
    dst = cellimg[:, EXT:]
    da = dst[..., 3:4] / 255.0
    A = al + da * (1 - al)
    dst[..., :3] = np.where(A > 0, (src[..., :3] * al + dst[..., :3] * da * (1 - al)) / np.maximum(A, 1e-6), 0)
    dst[..., 3:4] = A * 255
    wide[r * CH:(r + 1) * CH, c * NW:(c + 1) * NW] = cellimg
Image.fromarray(np.clip(wide + 0.5, 0, 255).astype(np.uint8)).save(P, 'WEBP', quality=90, method=6)   # 同 frames.py
meta['cell'] = [NW, CH]
meta['anchor'] = [round(meta['anchor'][0] + EXT, 1), meta['anchor'][1]]
if meta.get('head'): meta['head'] = [meta['head'][0] + EXT, meta['head'][1], meta['head'][2] + EXT, meta['head'][3]]
meta['bow'] = 'bestie/G15_rose/bow.py：船头统一成 idle 那一份，每格左边加宽 %d 接船尾' % EXT
json.dump(meta, open(META, 'w'), ensure_ascii=False)
print('stern slope %.3f' % SLOPE, 'cell', meta['cell'], 'anchor', meta['anchor'], 'head', meta.get('head'))
