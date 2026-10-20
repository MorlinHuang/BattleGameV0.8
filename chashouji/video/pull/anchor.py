"""拉扯视频的锚点姿势图：游戏里实际看到的样子（手机放大 1.3 倍 + 亮屏聊天界面），铺回品红幕布，给生图改图 / 即梦首尾帧用。
2026-10-05 用户：「抢的手机应该是屏幕亮着的……让人一看就知道抢的是手机」—— pose/ 原图里手机还是黑块，
放大、点亮是 build.py 出贴图时才做的（enlarge_phone），所以锚点不能直接拿 pose/ 原图。
不写游戏目录：只调 build 的 cutout / find_phone / enlarge_phone；要锚点时 build_pose 的输出目录临时改到 /tmp。

七张锚点必须画在**同一块画布、同一个比例**上（stage）：相邻两张是同一段视频的首尾帧，人在两张里大小、
站位、地面线不一样，视频就得在中间"变焦 / 平移"，接到下一段又跳回去。游戏里每档是这样摆的（build.main + main.js）：
  原图按 SCALE / BODY[档] 缩（扑倒、趴那几张人被画小了，按身体补回来），锚点（a/b 档 = 外框底边中点，
  n0 = 脚底质心）对到地面上同一个点。这里照搬，只是把 SCALE 换成画布比例 K。

用法：
  python3 video/pull/anchor.py <pose 原图> <输出.png>       单张点亮（原图分辨率）
  python3 video/pull/anchor.py stage <输出目录>             七张锚点，统一画布（另出 *_dark.png：手机未点亮，给生图改）
  python3 video/pull/anchor.py crop <档> <画布图> <输出>     裁成 1536×1024 给生图改
  python3 video/pull/anchor.py uncrop <档> <改好的图> <输出> <crop_box.json> [新 n0_raw.png]   放回画布、对齐赢方脚、点亮手机
"""
import os, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '../../v14'))
import build

MAGENTA = np.array([255, 0, 255], np.float32)

# 七档：名字 → (原图, 锚点按脚底质心还是外框中点)，与 build.main 的列表一致
POSES = {'n0': ('loop/n0.png', True),
         'aK': ('pose/21_女优_男跪.png', False), 'aF': ('pose/22_女优_男扑倒.png', False), 'aL': ('pose/23_女优_男趴.png', False),
         'bK': ('pose/24_男优_女跪.png', False), 'bF': ('pose/25_男优_女扑倒.png', False), 'bL': ('pose/26_男优_女趴.png', False)}

# 画布：16:9 1920×1080（即梦首尾帧比例）。K = 原图像素 → 画布像素（n0 的比例；其余档再除以 BODY）。
# 最宽的 aF 在游戏里 887 宽 = 原图 2016，按赢方脚对齐后再左右挪（见 CX），K=0.66 时最宽处两边各留约 120 给视频里甩头发、伸腿；
# n0 只占画面一半多一点。地面线离底边 GROUND_PAD，留给拖鞋蹭地时往下沉一点。
W, H, K = 1920, 1080, 0.66
CX = W / 2 + 67     # 各档锚点（外框中点）落在这一列：按赢方脚对齐后 b 档整体往左挪 260~330（输的女生趴得远），a 档往右挪 100~160，
                    # 中线右移 67 让最左（bL 女生头发）、最右（aF/aL 男生拖鞋）两边各留约 120
GROUND_PAD = 110


# 微信聊天界面（用户 2026-10-05：「应该是微信的消息界面，让人一看就知道抢的是手机」）。
# 游戏里的 build.screen_tex 是"像聊天软件"的抽象图案（绿顶栏、不写字），这里换成微信自己的配色和版式：
# 浅灰底、浅灰顶栏 + 居中标题、左边方头像 + 白气泡、右边方头像 + 微信绿气泡（都带小尖角）、底部语音钮 + 输入框 + 表情 / 加号。
# 只给视频锚点用，不改游戏贴图。不写字：视频模型会把字画乱，出片后按手机四角贴回的也是这张图。
WX = {'bg': (237, 237, 237), 'bar': (247, 247, 247), 'bar_h': 0.11, 'title': (60, 60, 60),
      'them': (255, 255, 255), 'me': (149, 236, 105), 'av_them': (250, 170, 120), 'av_me': (90, 150, 230),
      'input': (247, 247, 247), 'input_h': 0.1, 'icon': (90, 90, 90),
      'rows': [('them', 0.62), ('me', 0.5), ('them', 0.7), ('me', 0.42)],
      'line': (120, 120, 120), 'edge': (200, 200, 200)}
# 2026-10-05 第一版 5 行窄气泡、不画字行：锚点里屏幕只有 90×45 像素，转成横拿后白气泡在浅灰底上看不见、
# 绿气泡成了几根竖条，读成柱状图。改成 4 个宽气泡、白气泡加一圈灰边、气泡里画灰色"字行"（不是字，读出"一条消息"）


def wechat_tex(w, h):
    """w×h 竖屏（宽 < 高）微信聊天页，接口与 build.screen_tex 相同（light_phone 会把它转成横拿、贴上玻璃反光以外的部分）"""
    S = WX
    im = Image.new('RGB', (w, h), S['bg'])
    g = ImageDraw.Draw(im)
    bh = round(h * S['bar_h'])
    g.rectangle((0, 0, w, bh), fill=S['bar'])
    g.line((0, bh, w, bh), fill=(215, 215, 215), width=max(1, w // 120))
    lw = max(2, w // 40)
    g.line((w * 0.1, bh * 0.5, w * 0.16, bh * 0.3), fill=S['title'], width=lw)          # 返回箭头 <
    g.line((w * 0.1, bh * 0.5, w * 0.16, bh * 0.7), fill=S['title'], width=lw)
    g.rounded_rectangle((w * 0.36, bh * 0.4, w * 0.64, bh * 0.6), bh * 0.1, fill=S['title'])   # 居中标题（一条深灰）
    for k in range(3):                                                                    # 右上 ··· 
        r = w * 0.012; cx = w * (0.82 + k * 0.04)
        g.ellipse((cx - r, bh / 2 - r, cx + r, bh / 2 + r), fill=S['title'])
    ih = round(h * S['input_h'])
    g.rectangle((0, h - ih, w, h), fill=S['input'])
    g.line((0, h - ih, w, h - ih), fill=(215, 215, 215), width=max(1, w // 120))
    cy, r = h - ih / 2, ih * 0.26
    for cx in (w * 0.09, w * 0.78, w * 0.91):                                            # 语音钮、表情、加号三个圆圈
        g.ellipse((cx - r, cy - r, cx + r, cy + r), outline=S['icon'], width=lw)
    g.rounded_rectangle((w * 0.18, cy - r * 1.05, w * 0.69, cy + r * 1.05), r * 0.3, fill=(255, 255, 255))
    rows = S['rows']
    lh = (h - bh - ih) / len(rows)
    av = min(w * 0.13, lh * 0.55)
    for k, (side, ln) in enumerate(rows):
        y = bh + lh * (k + 0.22)
        if side == 'them':
            ax = w * 0.04; bx = ax + av + w * 0.04; ex = bx + w * ln
        else:
            ax = w * 0.96 - av; ex = ax - w * 0.04; bx = ex - w * ln
        g.rounded_rectangle((ax, y, ax + av, y + av), av * 0.15, fill=S['av_' + side])     # 方头像
        bh_ = lh * 0.7                                                                    # 气泡比头像高：两行字
        g.rounded_rectangle((bx, y, ex, y + bh_), av * 0.18, fill=S[side], outline=S['edge'] if side == 'them' else None, width=max(1, w // 150))
        for j, f in enumerate((0.85, 0.55)):                                              # 两道灰色字行，第二行短
            ly = y + bh_ * (0.33 + j * 0.36)
            g.line((bx + w * 0.04, ly, bx + (ex - bx - w * 0.08) * f + w * 0.04, ly), fill=S['line'], width=max(2, round(bh_ * 0.13)))
        t = av * 0.18; ty = y + av * 0.45                                                 # 小尖角指向头像
        tip = [(bx, ty - t), (bx - t, ty), (bx, ty + t)] if side == 'them' else [(ex, ty - t), (ex + t, ty), (ex, ty + t)]
        g.polygon(tip, fill=S[side])
    im = im.convert('RGBA')
    m = Image.new('L', (w, h)); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), w * build.SCREEN['round'], fill=255)
    im.putalpha(m)
    return im


build.screen_tex = wechat_tex        # light_phone 按名字取 screen_tex，换掉即可


def lit(path):
    """pose 原图（或已抠好的数组来源）→ (rgb, alpha)，手机已放大、点亮成微信界面"""
    rgb, al = build.cutout(path)
    ph = build.find_phone(rgb, al)
    assert ph, f'{path} 里没找到手机'
    return build.enlarge_phone(rgb, al, ph)


def on_magenta(rgb, al):
    a = al[..., None]
    return (rgb * a + MAGENTA * (1 - a)).clip(0, 255).astype(np.uint8)


def feet_x(al, phone_x, side):
    """赢方两只拖鞋的横向质心：贴地那一条（最底下 4%）里、手机那一侧以外的像素。side='a' 女生在左，'b' 男生在右"""
    ys = np.nonzero(al.max(1) > 0.5)[0]
    band = al[ys[-1] - round(0.04 * al.shape[0]):ys[-1] + 1] > 0.5
    xs = np.nonzero(band)[1]
    xs = xs[xs < phone_x] if side == 'a' else xs[xs > phone_x]
    return xs.mean()


def place(name, lit_=True):
    """一档 → 画布上的 (rgb, alpha, 手机 x)：跟游戏里同一套缩放和锚点，只是比例是 K 不是 SCALE"""
    f, feet = POSES[name]
    path = os.path.join(build.HERE, f)
    s = build.SCALE / build.BODY.get(name, 1)          # 游戏里这一档的缩放
    out, build.OUT = build.OUT, tempfile.mkdtemp()      # build_pose 会写一张 webp，别写进游戏目录
    try:
        _, _, (ax, ay) = build.build_pose(name, path, feet, scale=s)
    finally:
        build.OUT = out
    rgb, al = build.cutout(path)
    ph = build.find_phone(rgb, al)
    if lit_:
        rgb, al = build.enlarge_phone(rgb, al, ph)
    k = K * s / build.SCALE
    im = Image.fromarray(np.concatenate([rgb, al[..., None] * 255], -1).clip(0, 255).astype(np.uint8), 'RGBA')
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    ox, oy = round(CX - ax * k), round(H - GROUND_PAD - ay * k)
    cv = Image.new('RGBA', (W, H))
    cv.alpha_composite(im, (ox, oy))
    a = np.array(cv).astype(np.float32) / 255
    return a[..., :3] * 255, a[..., 3], ox + ph[0] * k


def stage(name, lit_=True):
    """place 之后再横移，让**赢方的脚**落在 n0 里同一个人的脚的位置。
    游戏按外框中点摆（扑倒、趴的外框被输方拉宽，赢方会横跳 100~150 像素），换档时有过渡帧和镜头卷动盖住；
    视频的首尾帧要是这样，模型就得在 2 秒里把赢方平移一截 —— 读成赢方脚底打滑。视频锚点改成赢方脚不动、
    只有输方倒下去；抽帧进游戏时再按手机点换算回游戏坐标，不影响游戏里的摆法。"""
    rgb, al, px = place(name, lit_)
    if name != 'n0':
        side = name[0]
        _, al0, px0 = place('n0', False)
        dx = round(feet_x(al0, px0, side) - feet_x(al, px, side))
        edge = al[:, W - dx:] if dx > 0 else al[:, :-dx]          # roll 前：会被绕到另一边的那几列必须是空的
        assert edge.max() < 0.03, f'{name} 横移 {dx} 出画'
        rgb, al = np.roll(rgb, dx, 1), np.roll(al, dx, 1)
    return rgb, al


def crop(name, src, out):
    """统一画布上的锚点 → 裁成 3:2（人物外框四周留白）放大到 1536×1024 给生图改：整张 16:9 送进去人只占一半，
    改出来细节糊。框记在 crop_box.json，改完用 uncrop 原样放回同一块画布。"""
    import json
    im = Image.open(src).convert('RGB'); a = np.array(im).astype(int)
    m = ~((abs(a[..., 0] - 255) < 20) & (a[..., 1] < 30) & (abs(a[..., 2] - 255) < 20))
    ys, xs = np.nonzero(m); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    h = max((y1 - y0) * 1.3, (x1 - x0) * 1.15 / 1.5); w = h * 1.5
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - (y1 - y0) * 0.05
    b = [round(cx - w / 2), round(cy - h / 2), round(cx + w / 2), round(cy + h / 2)]
    f = os.path.join(os.path.dirname(out), 'crop_box.json')
    box = json.load(open(f)) if os.path.exists(f) else {}
    box[name] = b; json.dump(box, open(f, 'w'), indent=1)
    c = Image.new('RGB', (b[2] - b[0], b[3] - b[1]), (255, 0, 255)); c.paste(im, (-b[0], -b[1]))
    c.resize((1536, 1024), Image.LANCZOS).save(out)


# 改图之后整套锚点统一再缩 ZOOM（以 (CX, 地面线) 为中心）：生图把倒地的输方画得更长（aF 男生从手到脚尖拉满一整屏），
# 赢方脚对齐再一挪就出画。七张必须同一个缩放，所以在这里统一做、不按张调。人物 n0 高约 470 像素，游戏里也只有 400 左右，够用。
ZOOM = 0.8
PAD = 600           # 横移、缩放在左右各加宽 PAD 的画布上做，避免先出画再缩回来时丢一截


def uncrop(name, gen, out, box_file, ref=None):
    """生图改好的 1536×1024 → 缩回裁切框大小 → 先在这个尺寸上点亮手机（find_phone 的面积门槛按整张图算，
    缩完 ZOOM 再找手机太小、找不到）→ 放回加宽的品红画布、以 (CX, 地面线) 为中心缩 ZOOM → 横移让赢方的脚对上 ref
    （新 n0 的 _raw.png；生图改胳膊时会把人整体挪一点）→ 裁回 1920×1080。
    点亮版存 <out>，未点亮版存 <out>_raw.png（给下一张当 ref、给生图再改）；两版同一套变换。<out 去掉 .png>.json 记手机中心。"""
    import json
    b = json.load(open(box_file))[name]
    g = Image.open(gen).convert('RGBA')
    bg = Image.new('RGBA', g.size, (255, 0, 255, 255)); bg.alpha_composite(g)      # 生图偶尔直接出透明底
    g = np.array(bg.convert('RGB').resize((b[2] - b[0], b[3] - b[1]), Image.LANCZOS))
    rgb, al = build.cutout(g.astype(np.int16))
    ph = build.find_phone(rgb, al)
    assert ph, f'{gen} 里没找到手机'
    lit_ = on_magenta(*build.enlarge_phone(rgb, al, ph))
    gy = H - GROUND_PAD

    def place(im):
        cv = Image.new('RGB', (W + 2 * PAD, H), (255, 0, 255)); cv.paste(Image.fromarray(im), (b[0] + PAD, b[1]))
        cv = cv.resize((round(cv.width * ZOOM), round(H * ZOOM)), Image.LANCZOS)
        big = Image.new('RGB', (W + 2 * PAD, H), (255, 0, 255))                     # 缩完把 (CX, 地面线) 放回原处
        big.paste(cv, (round((CX + PAD) * (1 - ZOOM)), round(gy * (1 - ZOOM))))
        return np.array(big)

    raw, lit_ = place(g), place(lit_)
    px = (b[0] + ph[0] + PAD) * ZOOM + (CX + PAD) * (1 - ZOOM)             # 手机 x 跟着同一套变换走（加宽画布坐标）
    py = (b[1] + ph[1]) * ZOOM + gy * (1 - ZOOM)
    if ref and name != 'n0':
        _, al = build.cutout(raw.astype(np.int16))
        _, a0 = build.cutout(ref)
        p0 = json.load(open(ref[:-8] + '.json'))['phone'][0]                       # 缩完的图里手机太小 find_phone 找不到，用记下的
        dx = round(feet_x(a0, p0, name[0]) - feet_x(al[:, PAD:PAD + W], px - PAD, name[0]))
        raw, lit_ = np.roll(raw, dx, 1), np.roll(lit_, dx, 1)
        px += dx
        print(name, '赢方脚横移', dx)
    m = ~((raw[..., 0] > 230) & (raw[..., 1] < 30) & (raw[..., 2] > 230))
    xs = np.nonzero(m.any(0))[0] - PAD
    assert xs[0] > 0 and xs[-1] < W - 1, f'{name} 出画：{xs[0]}~{xs[-1]}'
    print(name, '左留', xs[0], '右留', W - 1 - xs[-1])
    Image.fromarray(raw[:, PAD:PAD + W]).save(out[:-4] + '_raw.png')
    Image.fromarray(lit_[:, PAD:PAD + W]).save(out)
    json.dump({'phone': [round(px - PAD, 1), round(py, 1)]}, open(out[:-4] + '.json', 'w'))   # 画布坐标：抽帧后按手机稳住、换算回游戏


if __name__ == '__main__':
    if sys.argv[1] == 'crop':
        crop(*sys.argv[2:5])
    elif sys.argv[1] == 'uncrop':
        uncrop(*sys.argv[2:7])
    elif sys.argv[1] == 'stage':
        d = sys.argv[2]; os.makedirs(d, exist_ok=True)
        for n in POSES:
            Image.fromarray(on_magenta(*stage(n))).save(os.path.join(d, f'{n}.png'))
            print(n)
    else:
        src, out = sys.argv[1:3]
        Image.fromarray(on_magenta(*lit(src))).save(out)
        print(out)
