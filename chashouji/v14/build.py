"""v14 素材构建：长卷背景 + 姿势贴图 + 元数据。在 chashouji/ 下运行：python3 v14/build.py

产物全部写进 web/assets/world/，外加一份 world.json 给 main.js 读：
  room0/1/2.webp   三段房间（女生卧室｜客厅｜电竞房），高 1334
  pose_*.webp      抠好的角色贴图，已裁到外框
  world.json       房间宽度、客厅中点、每张贴图的锚点与手机位置

────────── 背景怎么拼 ──────────
三张房间图是分开生成的，每张在接缝那一侧都画了一扇被画面边缘切开的门：
女生卧室右边缘有门（左门框 + 透出客厅的门洞），客厅左边缘也有门（门洞 + 右门框）。
拼的时候**一扇门取两张图各一半**：卧室那张留到右边缘（左门框+门洞），客厅那张从它
自己的右门框开始 —— 于是接缝落在门洞里，读出来是"一扇门"，不是两张图硬拼。
电竞房那边同理。切点的像素位置是对着原图量出来的（CUT_*），换图必须重量。

────────── 角色贴图怎么对齐 ──────────
所有姿势用**同一个缩放**（SCALE）：生图时都写死了"站立身高约占画面 78%、脚底在 92%"，
而且都以僵持帧为参考图生成，实测人物尺寸一致。逐张按面积归一化反而有害 ——
坐在地上被拖的那个人面积本来就小，按面积放大就把他放成巨人。
锚点 = (外框中点 x, 脚底线 y)：引擎把锚点对到屏幕中线与地面线上。按外框而不是质心：
拖地姿势宽约 1000px，比屏幕还宽，按质心对齐会让一侧整整多出画 100 多像素。
僵持循环那几帧例外：脚是钉在地上不动的，所以水平按**脚那一截**的质心对齐，
否则上身前后倾会把整个人带着左右滑，读成"脚在冰上打滑"。

────────── 手机位置 ──────────
弹幕往手机那条竖线上打、聊天气泡从手机里冒出来，所以每张贴图都要知道手机在哪。
自动找：近黑像素的连通块里，挑"沿自身方向量的填充率高 + 长条"的那一块（手机可以斜着）。头发也是黑的，
但它是散的（填充率低）；裤子是黑的，但它是竖的、面积大。每次重跑都会把找到的
位置画到 v14/preview/phone_check.jpg 上，**必须看一眼**再部署。
"""
import json
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'web', 'assets', 'world')
H = 1334
SCALE = 0.66          # 1536×1024 的生图 → 引擎像素。站立的人约 600 高
K = np.ones((3, 3), np.float32)

# 门的切点（原图 1659×948 坐标）：卧室留到右边缘；客厅从它左门的右门框起、
# 留到右边缘（含右门的左门框+门洞）；电竞房从它左门的右门框起
CUT_LIVING_L = 75
CUT_BOY_L = 140


def cutout(path, lo=60, hi=150):
    a = np.array(Image.open(path).convert('RGB')).astype(np.int16)   # int16：uint8 相减会下溢
    m = np.minimum(a[..., 0], a[..., 2]) - a[..., 1]
    alpha = np.clip((hi - m) / (hi - lo), 0, 1)
    edge = ndimage.binary_dilation(alpha < 0.99, np.ones((3, 3))) & (alpha > 0.01)
    rgb = a.astype(np.float32)
    spill = np.clip((rgb[..., 0] + rgb[..., 2]) / 2 - rgb[..., 1], 0, None)
    for c in (0, 2):   # 去溢色只动半透明边缘，不透明的粉睡衣本身就偏红
        rgb[..., c] = np.where(edge, rgb[..., c] - spill * 0.6, rgb[..., c])
    return np.clip(rgb, 0, 255), alpha


def edge_extend(rgb, al, iters=10):
    rgb = rgb.copy()
    mask = al > 0.03
    for _ in range(iters):
        m = mask.astype(np.float32)
        cnt = ndimage.convolve(m, K, mode='constant')
        acc = np.stack([ndimage.convolve(rgb[..., c] * m, K, mode='constant') for c in range(3)], -1)
        grown = cnt > 0
        fill = grown & ~mask
        if not fill.any():
            break
        rgb[fill] = (acc / np.maximum(cnt, 1)[..., None])[fill]
        mask |= grown
    return rgb


def find_phone(rgb, al):
    dark = (rgb.max(-1) < 70) & (al > 0.9)
    lab, n = ndimage.label(dark)
    best, score = None, 0
    h, w = al.shape
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        ys, xs = sl
        py, px = np.nonzero(lab[sl] == i)
        area = len(px)
        if not 0.0012 * h * w < area < 0.03 * h * w:
            continue
        if ys.start > h * 0.75:           # 拖鞋在最底下，手机不会在那
            continue
        # 长宽沿块自己的主方向量，不用水平外框：趴地那两张手机是斜着拿的，
        # 水平外框只填得满一半，会被当成散开的头发筛掉
        pts = np.stack([px, py], 1).astype(np.float32)
        pts -= pts.mean(0)
        _, vec = np.linalg.eigh(np.cov(pts.T))
        proj = pts @ vec
        ext = proj.max(0) - proj.min(0) + 1
        long_, short = ext.max(), ext.min()
        fill = area / (long_ * short)
        if not (1.3 < long_ / max(short, 1) < 3.6 and fill > 0.62):
            continue
        s = fill * area
        if s > score:
            score, best = s, (xs.start + px.mean(), ys.start + py.mean(), long_, short)
    return best


def build_pose(name, path, feet_align=False):
    rgb, al = cutout(path)
    ph = find_phone(rgb, al)
    rgb = edge_extend(rgb, al)
    im = Image.fromarray(np.concatenate([rgb, al[..., None] * 255], -1).astype(np.uint8), 'RGBA')
    im = im.resize((round(im.width * SCALE), round(im.height * SCALE)), Image.LANCZOS)
    a = np.array(im)[..., 3].astype(np.float32) / 255
    ys, xs = np.where(a > 0.06)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    foot = y1
    if feet_align:
        band = a[foot - int((foot - y0) * 0.08):foot]
        cx = (band.sum(0) * np.arange(a.shape[1])).sum() / band.sum()
    else:
        cx = (x0 + x1) / 2     # 拖地这类宽姿势比屏幕还宽，按质心对齐会让一侧整截出画
    im = im.crop((x0, y0, x1, y1))
    im.save(os.path.join(OUT, f'pose_{name}.webp'), quality=90, method=6)
    meta = {'w': int(x1 - x0), 'h': int(y1 - y0),
            'ax': round(float(cx - x0), 1), 'ay': int(foot - y0)}
    if ph:
        meta['phone'] = [round(ph[0] * SCALE - x0, 1), round(ph[1] * SCALE - y0, 1)]
    return meta, im


def main():
    os.makedirs(OUT, exist_ok=True)
    bg = os.path.join(HERE, 'bg')
    G = Image.open(f'{bg}/girlroom_raw.png').convert('RGB')
    L = Image.open(f'{bg}/living_raw.png').convert('RGB')
    B = Image.open(f'{bg}/boyroom_raw.png').convert('RGB')
    s = H / G.height
    parts = [G, L.crop((CUT_LIVING_L, 0, L.width, L.height)), B.crop((CUT_BOY_L, 0, B.width, B.height))]
    rooms = []
    for i, p in enumerate(parts):
        r = p.resize((round(p.width * s), H), Image.LANCZOS)
        r.save(os.path.join(OUT, f'room{i}.webp'), quality=86, method=6)
        rooms.append(r.width)
    # 客厅中点 = 沙发正中 = 0 米。按原图客厅中线换算到拼接后的世界坐标
    center = rooms[0] + round((L.width / 2 - CUT_LIVING_L) * s)

    poses = {}
    sheet = []
    for name, f, feet in [
        ('n0', 'loop/n0.png', True), ('nL1', 'loop/nL1.png', True), ('nL2', 'loop/nL2.png', True),
        ('nR1', 'loop/nR1.png', True), ('nR2', 'loop/nR2.png', True),
        # 被拉倒三档：K 跪着 / F 往前扑倒 / L 趴在地上。a = 查岗党(女)占优、男方倒；b 反之。
        # 两人朝向永远不变：头朝对方、腿在身后（见 chashouji-art skill 的朝向铁律）
        ('aK', 'pose/21_女优_男跪.png', False), ('aF', 'pose/22_女优_男扑倒.png', False),
        ('aL', 'pose/23_女优_男趴.png', False),
        ('bK', 'pose/24_男优_女跪.png', False), ('bF', 'pose/25_男优_女扑倒.png', False),
        ('bL', 'pose/26_男优_女趴.png', False),
    ]:
        meta, im = build_pose(name, os.path.join(HERE, f), feet)
        poses[name] = meta
        sheet.append((name, meta, im))
        print(name, meta)

    json.dump({'rooms': rooms, 'center': center, 'height': H, 'poses': poses},
              open(os.path.join(OUT, 'world.json'), 'w'), ensure_ascii=False, indent=1)
    print('rooms', rooms, 'total', sum(rooms), 'center', center)

    # 手机位置自检图：每张贴图上画出锚点（绿）与手机（红圈）
    cw = 560
    out = Image.new('RGB', (cw * 3, 380 * ((len(sheet) + 2) // 3)), (40, 40, 40))
    for k, (name, meta, im) in enumerate(sheet):
        c = Image.new('RGBA', im.size, (250, 240, 150, 255)); c.alpha_composite(im)
        d = ImageDraw.Draw(c)
        d.line((meta['ax'], 0, meta['ax'], meta['h']), fill=(0, 160, 0), width=3)
        if 'phone' in meta:
            px, py = meta['phone']; d.ellipse((px - 26, py - 26, px + 26, py + 26), outline=(255, 0, 0), width=5)
        d.text((8, 8), name, fill=(0, 0, 0))
        c.thumbnail((cw, 380))
        out.paste(c.convert('RGB'), ((k % 3) * cw, (k // 3) * 380))
    out.save(os.path.join(HERE, 'preview', 'phone_check.jpg'), quality=88)


if __name__ == '__main__':
    main()
