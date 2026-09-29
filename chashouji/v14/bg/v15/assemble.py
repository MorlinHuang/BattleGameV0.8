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

# 房间分界（2026-09-29 用户：不要门、不要半隔断，照最早那张长卷——两间房直接挨着）：
# 墙面在接缝处硬切（换墙色），只压一道很淡的墙角阴影；地板两边各 FLOOR_BLEND 渐变过去，不留竖条。
# 渐变要用到对方房间越过接缝的像素，房间图里没有，就用各自边缘往外镜像补。
FLOOR_BLEND, CORNER_SHADE = 40, 0.18

def seams(world):
    a = np.array(world, np.float32)
    for x in (SIDE_W, SIDE_W + LIV_W):
        L = a[:, x - 2 * FLOOR_BLEND:x]; R = a[:, x:x + 2 * FLOOR_BLEND]
        left_ext = np.concatenate([L, L[:, ::-1]], 1)            # 左房间越过接缝的部分用镜像补
        right_ext = np.concatenate([R[:, ::-1], R], 1)
        t = np.clip((np.arange(4 * FLOOR_BLEND) - FLOOR_BLEND) / (2 * FLOOR_BLEND), 0, 1)[None, :, None]
        blend = left_ext * (1 - t) + right_ext * t
        a[FLOOR_Y:, x - 2 * FLOOR_BLEND:x + 2 * FLOOR_BLEND] = blend[FLOOR_Y:]
        # 墙角：接缝两侧各 6 px 由深到浅，只在墙面上
        d = np.abs(np.arange(-6, 6) + 0.5)
        k = 1 - CORNER_SHADE * (1 - d / 6)
        a[:FLOOR_Y, x - 6:x + 6] *= k[None, :, None]
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
