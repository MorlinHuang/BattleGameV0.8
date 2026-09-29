"""v15 三间房：同一张几何模板生成 → 统一尺寸 → 拼长卷 → 程序画隔墙/门槛。
几何（世界像素，高 H=1707，与 main.js 一致）：
  PX_PER_M = 82*2/3；客厅正中 = 0 m；隔墙在 ±DOOR_M；判胜 ±30 m；世界两头 = 终点再往外 480（镜头 MID），
  所以拖到终点时镜头正好停在世界边上。"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
H = 1707
PX_PER_M = 82 * 2 / 3
DOOR_M, GOAL_M, MID = 9, 30, 480
LIV_W = round(2 * DOOR_M * PX_PER_M)                      # 984
SIDE_W = round((GOAL_M - DOOR_M) * PX_PER_M) + MID        # 1628
CENTER = SIDE_W + LIV_W // 2                              # 2120
CEIL_Y, FLOOR_Y = 67, 830    # 统一的顶角线下沿 / 墙地交界（踢脚线下沿）。三张生成图各自量出来的线按行分段线性拉到这两条上，
                              # 隔墙两边的墙地线、顶角线才对得上（生成图同一张模板也会偏 ±40）

def warp_rows(im, ceil, floor):
    """行映射：0→0、ceil→CEIL_Y、floor→FLOOR_Y、H→H，段内线性。"""
    a = np.asarray(im, np.float32)
    ys = np.arange(H, dtype=np.float32)
    src = np.interp(ys, [0, CEIL_Y, FLOOR_Y, H - 1], [0, ceil, floor, H - 1])
    y0 = np.floor(src).astype(int).clip(0, H - 2); t = (src - y0)[:, None, None]
    return Image.fromarray((a[y0] * (1 - t) + a[y0 + 1] * t).clip(0, 255).astype(np.uint8))

def fit(path, w, keep, ceil=CEIL_Y, floor=FLOOR_Y):
    """等比缩到高 H，把量出来的顶角线 / 墙地线拉到统一位置，再裁到宽 w；
    keep='left' 保留左边（裁右边），'right' 保留右边，'center' 居中。"""
    im = Image.open(path).convert('RGB')
    s = H / im.height; im = im.resize((round(im.width * s), H), Image.LANCZOS)
    im = warp_rows(im, ceil, floor)
    if im.width < w: im = im.resize((w, H), Image.LANCZOS)
    x0 = {'left': 0, 'right': im.width - w, 'center': (im.width - w) // 2}[keep]
    return im.crop((x0, 0, x0 + w, H))

# 房间分界（2026-09-29 用户：照 v14 长卷里那根墙柱——只要柱子这个框，不要门、不要半隔断）：
# post_src.png 是 v14 长卷里女生房 / 客厅接缝那一段（旧世界 x 1300~1700），柱子在其中 POST_X（含描边与底座），
# 底座下沿在 POST_BOT，地板上的木压条从 STRIP_TOP 往下（按木色抠出来）。贴到新接缝时：
#   · 柱子按行缩放，让底座下沿落在新墙地线下 12 px（旧图里底座比墙地线低 12）；压条按行拉到新地板上；
#   · 重打光：旧图是白天，柱子两侧分别乘"新墙 / 旧墙"的逐通道比值（左半用左墙、右半用右墙，中间渐变），
#     压条乘"新地板 / 旧地板"——在电竞房那侧自然被染成蓝紫、在女生房那侧偏暖粉。
# 两边地板在接缝处先各 FLOOR_BLEND 渐变（压条盖住中间），墙面直接由柱子隔开。
POST_X, POST_BOT, STRIP_TOP, OLD_FLOOR = (140, 229), 898, 887, 886
OLD_WALL = ((60, 120), (270, 330))      # post_src 里柱子左 / 右两块旧墙（量光用的列范围）
FLOOR_BLEND = 40

def seams(world):
    src = np.asarray(Image.open(os.path.join(HERE, 'post_src.png')).convert('RGB'), np.float32)
    a = np.array(world, np.float32)
    wall_rows, floor_rows = slice(300, 700), slice(1000, 1300)
    old_l = src[wall_rows, OLD_WALL[0][0]:OLD_WALL[0][1]].reshape(-1, 3).mean(0)
    old_r = src[wall_rows, OLD_WALL[1][0]:OLD_WALL[1][1]].reshape(-1, 3).mean(0)
    old_f = src[floor_rows, 20:380].reshape(-1, 3).mean(0)
    px0, px1 = POST_X; pw = px1 - px0; pc = (px0 + px1) / 2
    for x in (SIDE_W, SIDE_W + LIV_W):
        # 地板先渐变
        L = a[:, x - 2 * FLOOR_BLEND:x]; R = a[:, x:x + 2 * FLOOR_BLEND]
        t = np.clip((np.arange(4 * FLOOR_BLEND) - FLOOR_BLEND) / (2 * FLOOR_BLEND), 0, 1)[None, :, None]
        blend = np.concatenate([L, L[:, ::-1]], 1) * (1 - t) + np.concatenate([R[:, ::-1], R], 1) * t
        a[FLOOR_Y:, x - 2 * FLOOR_BLEND:x + 2 * FLOOR_BLEND] = blend[FLOOR_Y:]
        # 光照比值
        new_l = a[wall_rows, x - 90:x - 50].reshape(-1, 3).mean(0)
        new_r = a[wall_rows, x + 50:x + 90].reshape(-1, 3).mean(0)
        new_f = a[floor_rows, x - 200:x + 200].reshape(-1, 3).mean(0)
        # 柱子只按亮度换光，再带 35% 墙的色相（整个按逐通道比值乘会把奶白柱子染成墙色）
        lum = lambda c: c @ np.array([0.299, 0.587, 0.114])
        tint = lambda c: 0.65 + 0.35 * c / c.mean()
        gl = lum(new_l) / lum(old_l) * tint(new_l); gr = lum(new_r) / lum(old_r) * tint(new_r)
        gf = new_f / old_f
        # 柱子：行 0..POST_BOT → 0..FLOOR_Y+12
        bot = FLOOR_Y + (POST_BOT - OLD_FLOOR)
        ys = np.clip(np.arange(bot) * POST_BOT / bot, 0, POST_BOT - 1).astype(int)
        post = src[ys, px0:px1]
        k = np.linspace(0, 1, pw)[None, :, None]
        post = post * (gl * (1 - k) + gr * k)
        x0 = int(round(x - pw / 2))
        a[:bot, x0:x0 + pw] = post
        # 压条：旧 STRIP_TOP..H → 新 FLOOR_Y+1..H，按木色抠
        n = H - (FLOOR_Y + 1)
        ys = np.clip(STRIP_TOP + np.arange(n) * (H - STRIP_TOP) / n, 0, H - 1).astype(int)
        cols = slice(int(pc - 90), int(pc + 90))
        st = src[ys, cols]
        # 压条是一条往下略变宽的梯形（量的 post_src 坐标：y 890 处 224~244，y 1700 处 209~269）
        yy = ys[:, None].astype(np.float32); xx = np.arange(int(pc - 90), int(pc + 90))[None, :].astype(np.float32)
        le = 224 - (yy - 890) * 0.0185; ri = 244 + (yy - 890) * 0.031
        al = (np.clip(xx - le + 0.5, 0, 1) * np.clip(ri - xx + 0.5, 0, 1))[..., None]
        sx0 = int(round(x - 90))
        region = a[FLOOR_Y + 1:, sx0:sx0 + 180]
        a[FLOOR_Y + 1:, sx0:sx0 + 180] = region * (1 - al) + st * gf * al
    world.paste(Image.fromarray(a.clip(0, 255).astype(np.uint8)))

# 各房间生成图（缩到高 H 后）量到的顶角线下沿、墙地交界 y
LINES = {'girl_2.png': (67, 830), 'livfix_1.png': (66, 790), 'boy_3n.png': (52, 868)}

def build(girl, living, boy, out):
    rooms = [fit(girl, SIDE_W, 'right', *LINES[girl]), fit(living, LIV_W, 'center', *LINES[living]),
             fit(boy, SIDE_W, 'left', *LINES[boy])]
    world = Image.new('RGB', (2 * SIDE_W + LIV_W, H)); x = 0
    for r in rooms: world.paste(r, (x, 0)); x += r.width
    goals(world)
    seams(world)
    world.save(out)
    return world

# 终点地毯 / 地垫：沿用 v14 局部重绘出来的两张（bg/goal/goal{k}_gen.png，960 宽、以终点为中心），
# 只取梯形（墙根 → 画面下沿，带透视）混进新长卷。终点在世界 x = CENTER ∓ GOAL_M·PX_PER_M。
GOAL_W = 960
GOAL_TRAP = [(110, 860), (190, H)]     # 同 main.js GOAL.y0/y1/w0/w1
GOAL_FEATHER = 10
RELIGHT = (True, False)   # 地毯是反光物要重打光；RGB 地垫自己发光，旧电竞房光照本就相同，重打光反而把青色压成绿

def goals(world):
    from scipy import ndimage
    for k, d in enumerate((-1, +1)):
        gx = round(CENTER + d * GOAL_M * PX_PER_M); x0 = gx - GOAL_W // 2
        gen = Image.open(os.path.join(HERE, '..', 'goal', f'goal{k}_gen.png')).convert('RGB').resize((GOAL_W, H), Image.LANCZOS)
        (w0, y0), (w1, y1) = GOAL_TRAP
        m = Image.new('L', (GOAL_W, H)); c = GOAL_W / 2
        ImageDraw.Draw(m).polygon([(c - w0, y0), (c + w0, y0), (c + w1, y1), (c - w1, y1)], fill=255)
        w = ndimage.gaussian_filter(np.array(m, np.float32) / 255, GOAL_FEATHER / 2)[..., None]
        cv = world.crop((x0, 0, x0 + GOAL_W, H))
        # 重打光：地毯是从旧房间（白天 / 旧灯光）里画出来的，按梯形外一圈地板的平均色把它换到新房间的光下
        ring = (ndimage.binary_dilation(w[..., 0] > 0.02, iterations=60) & (w[..., 0] <= 0.02))
        ring[:y0 + 20] = False
        g = np.array(gen, np.float32); c0 = np.array(cv, np.float32)
        gain = c0[ring].mean(0) / g[ring].mean(0)
        if RELIGHT[k]: g = g * gain
        out = (c0 * (1 - w) + g * w).clip(0, 255).astype(np.uint8)
        world.paste(Image.fromarray(out), (x0, 0))


if __name__ == '__main__':
    build(*sys.argv[1:5])
    print('rooms', [SIDE_W, LIV_W, SIDE_W], 'center', CENTER)
