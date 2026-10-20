"""拉扯视频 → 游戏姿势帧（2026-10-06，女赢 10 段先行）。

输入：src/女赢_01~10.mp4（即梦首尾帧模式出的 1280×720、24fps 品红底视频，首尾帧钉在 anchor/v2 的七张锚点上）。
输出：web/assets/world/vid/v<段>_<格>.webp + vid.json —— main.js 在 ?vid=1 时把它们并进 WORLD.poses，
     用视频段替掉 n 僵持 和 a 三档（K 跪 / F 扑倒 / L 趴）的循环与过渡帧。

几条约定（都是对着片子量出来的，见 女赢10段_视频提示词.md 与 summary）：
- 十段视频是同一个机位：七张锚点在同一张 1920×1080 画布上赢方脚对齐，所以**所有帧共用一个锚点**
  （舞台上一个固定点 X0、脚底线 GROUND_720），不按每帧外框算 —— 按外框算，人一伸腿锚点就跳。
- 循环段（第 3/5/7 段）尾帧是锚点整体左移 360@1080 = 240@720，视频里两个人真的往左走了 240。
  进游戏时第 f 格按 (f-a)/(b-a)×240 往右挪回去（写进 ax），地板按同样的量往右卷：脚踩在地上不打滑。
  一圈对应地板卷过 cycle = 240×SC 像素，main.js 按位移推相位（同步态）。
- 即梦首帧照搬上传图、第 2 帧跳成它自己画的版本（整体左跳 20~42）：这一跳在 JUMP_R 格里分摊回去。
- 过渡段掐掉首尾不动的部分（首尾帧本来就等于两头的循环），只留动作。
- 帧率减半到 12 格/秒（每两帧取一帧）：一套十段 500 来张，首屏不等它们。
"""
import os, sys, json, glob, subprocess, hashlib
import numpy as np
from PIL import Image
from scipy import ndimage
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'v14'))
from build import cutout, keyed, two_people, edge_extend, edges, ground_segs, hip_find   # noqa: E402

FF = '/home/worker/.local/lib/python3.12/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
WEB = os.path.join(HERE, '..', '..', 'web', 'assets', 'world')
# 出到哪个目录、主角放大多少。主角大小跟着 world.json 的 n0 走（10-06 画面布局方案定 ×1.10，在 v14/build.py 的 HERO 里放，
# world.json 已是 1.1 倍）—— 这里的 HERO 只是在它上面再乘的试验倍数，默认 1。
# 第一版这里也默认 1.1：world.json 换成 1.1 倍之后再跑就成了 1.21 倍（SC 1.3906 → 1.5255，10-06 出 vidarm 时发现）。
# 试别的倍数：VID_DIR=vid105 HERO=1.05 python3 build_vid.py，网页用 ?vid=vid105 加载
VID_DIR = os.environ.get('VID_DIR', 'vid')
HERO = float(os.environ.get('HERO', '1'))
OUT = os.path.join(WEB, VID_DIR)
TMP = '/tmp/vidframes'

# 段：(编号, 名字, 循环/过渡, 过渡段位移)。名字：循环段 = 档名（n / aK / aF / aL / bK / bF / bL），过渡段 = '从>到'
# 循环段的 (a, b, dx)：第 a 帧 ≈ 第 b 帧右移 dx（源视频像素；正 = 片子里人往左走了 dx）——接缝搜索（seam()，半分辨率）量的，
# 循环取 [a, b)。残差：01 4.0 / 03 3.07 / 05 3.69 / 07 3.06（视频压缩噪声约 1~2；换起帧就到 26，见 summary）。
# 写成 ('auto', dx 估计值) 的：交片后第一次跑时自动搜（起帧 1~8 × 止帧最后 30 帧 × dx 估计值 ±SEAM_DX），结果打印出来，
# 确认后抄回这里写死（搜一次要一分钟）。
# 过渡段位移：尾帧锚点比首帧挪了多少（源视频像素，正 = 往左），按帧号线性分摊进 ax —— 只有第 11 段带一步
# （尾帧 bK_右移156），不补的话人在过渡段里往前冲一步、进循环又跳回去。
# 两套：女赢 01~10（anchor/v2），男赢 11~19（anchor/v3d，人放大 1.3 倍）。僵持循环两套共用 01。
# 两套都是 720P（即梦首尾帧模式只出 720P，10-06 用户确认）：男赢的位移按锚点 1080 画布 ×2/3 写成源像素（一步 156 → 104）。
# 男赢循环段 10-06 v4 回到女赢写法：5 秒走 3 步（尾帧右移 468@1080 = 312@720）；过渡段只有已出的 11 带一步（尾帧右移 156），
# 13 起和女赢一样原地完成（11 段写了挪步，男生一下子退出去、两人拉开，见 男赢9段_视频提示词.md 踩坑表）。
SEGS = [
    ('01', 'n', (1, 119, 0), 0),
    ('02', 'n>aK', None, 0),
    ('03', 'aK', (1, 95, 240), 0),
    ('04', 'aK>aF', None, 0),
    ('05', 'aF', (1, 120, 240), 0),
    ('06', 'aF>aL', None, 0),
    ('07', 'aL', (1, 121, 240), 0),
    ('08', 'aL>aF', None, 0),
    ('09', 'aF>aK', None, 0),
    ('10', 'aK>n', None, 0),
    ('11', 'n>bK', None, -104),
    ('12', 'bK', (5, 97, -312), 0),          # 10-06 试3（即梦 6794），接缝残差 4.74
    ('13', 'bK>bF', None, 0),
    ('14', 'bF', (1, 121, -312), 0),         # 10-06 即梦 1237，接缝残差 4.35
    ('15', 'bF>bL', None, 0),
    ('16', 'bL', (1, 121, -312), 0),         # 10-06 即梦 2616，接缝残差 4.84
    ('17', 'bL>bF', None, 0),
    ('18', 'bF>bK', None, 0),
    ('19', 'bK>n', None, 0),
]
# 每套：哪些段、源文件名前缀、用哪一段的第 1 帧（= n0 锚点）定缩放和锚点
SETS = {'女赢': ('01', [f'{i:02d}' for i in range(1, 11)]), '男赢': ('11', [f'{i:02d}' for i in range(11, 20)])}
SEAM_DX = 40
# 过渡段手动起帧（覆盖 trim() 量出来的起点）。男赢第 11 段按旧提示词"0~1 秒较劲"出的：前 1 秒两人原地晃（帧间差 2~23，
# 超过 STILL、trim 当成在动），第 26 帧起才真的开拽 —— 留着的话送礼后先原地晃 1 秒才跪，等于僵持循环又播一遍。
# 从第 22 帧起（留 4 帧起势）。新提示词改成 0~0.3 秒起势，之后的段不该再需要
# 过渡段从第几帧起播（默认 trim() 量的起动帧）。10-06 曾为跳过第 11 段开头 1 秒原地晃写过 {'11': 22}，
# 结果过渡段第一格不是锚点姿势、从僵持切进来跳 55 像素（整条流程连拍量的），撤掉：开头那一秒较劲照播。
TRIM_START = {}
# 循环段里两人整体往回挪（拉锯）的段：按两人着地点的平均位置做「只进不退」修正，往回挪的那几帧让人在地面上原地不动、动作照播。
# 只用在两人一起挪的段（女生脚尖和男生后脚的回退量差不多）——只有女生往回滑的段这么修，会变成男生被她拽着往前走（12 试过）。
# 14：第 45~65 帧女生脚尖 −120、男生后脚 −118、手机 −97，修后两人各自最大回退 138/132 → 53/56。
GROUND_PIN = {'14'}
FPS = 24.15         # 按源片帧率出格：即梦一张画停 2 帧或 3 帧、两种混着来（12 / 8 张每秒），停着的格复用同一张图（cadence()）。
                    # 10-06 以前每 2 帧取 1 格（12 格/秒），停 3 帧的段取出来是 2、1、2、1 格交替 —— 动作一顿一顿（第 10、16、17 段 1/4 的格突跳）
DUP = 4.5           # 半分辨率前景平均差低于它 = 同一张画（重编码噪声 2~3.6；真的在动最小 8 上下）
RIFE_MODEL = os.path.join(HERE, 'sr', 'rife49.onnx')
RIFE_URL = 'https://huggingface.co/yuvraj108c/rife-onnx/resolve/main/rife49_ensemble_True_scale_1_sim.onnx'
# 哪几段、相邻两张画差多少以上，用 RIFE 在停着的那几帧里补中间画（保持原片节奏，只把一下跳过去的拆成 2~3 步）。
# 01 僵持循环：一圈 5 次换方向猛拽，那一张和前一张差 56~92（平时 10~30），12 格/秒播是一下闪过去（10-06 审查第 1 条）
# 过渡段（倒下、撑起、站起）：倒下那一下常是一张画停 4 帧再整个人砸下去（15 段 8→12→16，差 59~65；13 段 16→20→22 差 56~62），6 张/秒
# 10-07 撤掉：补出来的中间画在腿交叉、倒下处是重影、粉色幽灵腿、两腿粘连（08 段 i019/i021、17 段 i023/i024），
# 越该补的地方补得越差。宁要原片一拍三的顿挫。旧值 {'01': 35, 过渡段: 45}
RIFE_D = {}
SETTLE = 0.05       # 过渡段收尾：剪影和尾帧的距离（1 − 交并比）一直小于它就算到位，后面的收势剪掉（10-06 审查第 2 条：
                    # 02 段末尾 2.2 秒、15 段 2.0 秒几乎不动，局势变了画面还在等）
GROUND_720 = 646    # 女赢 720 片的脚底线（七张锚点外框下沿 645~647）；趴档男生放大 / 贴地那几个函数只用于女赢，按它算。
                    # 出帧用的脚底线每套各自量（SETP[套]['G']）
JUMP_R = 8          # 第 2 帧那一跳在几帧（源帧）里分摊回去
STILL = 4.0         # 过渡段：和首/尾帧的差（前景平均绝对差）超过它才算开始动 / 还在动
PHONE_DX = -4.6     # 微信绿气泡外框中心比手机中心偏右（四张锚点 json 对比量的，720 像素；1080 片按 R 换算）

# 趴档男生画小了（10-06 用户：「趴下去以后人物变小一圈……特别明显」）。aL 锚点里男生比 aF 小：剪影面积 25600 对 32900
# （√ = 1.13），视频第 6 段中间按 aF 的个头画他趴下、最后 0.8 秒（源帧 57~77）为了贴合尾帧缩回去；第 7 段整段是小的；
# 第 8 段撑起来时（21~61）又长回 aF 的个头。头的大小各锚点一样（宽 60~63），差在身子和腿。
# 做法：趴着的这些帧把男生放大 MAN_K —— 以地面为基准（贴地的身子还贴地），手机、手、头和女生前脚这一截原样不动，
# 从 x0（手机右边 MAN_KEEP 与女生前脚右沿取靠右的那个）往右 MAN_RAMP 像素内放大倍数从 1 平滑升到 MAN_K。
# 每段按源帧号给倍数：(从第几帧, 到第几帧, 起倍数, 止倍数)，中间 smoothstep，之外取两头。
MAN_K = 1.16      # 1.13 时趴档身长 694、第 6 段中段趴着 708，差的是手和头那一截没放大，补到 1.16
# 窗口按原片男生身长（手机 → 脚尖，720）量的：第 6 段 57→77 从 562 缩到 501；第 8 段 21→35 从 502 长回 561。
# 第 8 段原来写 21→61，原片 35 就长回去了、我这边还放大着，中间男生大一圈（10-06 用户「趴下到起来跪着……明显变大一圈然后再变小」）
MAN_SCALE = {'06': (57, 77, 1.0, MAN_K), '07': (1, 1, MAN_K, MAN_K), '08': (14, 28, MAN_K, 1.0)}
MAN_KEEP = 90       # 手机中心往右多少（720 像素）以内不动：手、头
MAN_RAMP = 120


def man_k(seg, f, table=MAN_SCALE):
    if seg not in table:
        return 1.0 if table is MAN_SCALE else 0.0
    f0, f1, k0, k1 = table[seg]
    t = min(1.0, max(0.0, (f - f0) / max(1, f1 - f0)))
    t = t * t * (3 - 2 * t)
    return k0 + (k1 - k0) * t


def man_grow(a, ph, k):
    """把手机右边的男生放大 k（见 MAN_K）。a：720 原帧（品红底），ph：手机中心。逆向映射：输出 (x, y) 取原图
    (x0 + (x−x0)/s, G − (G−y)/s)，s 在 [x0, x0+MAN_RAMP] 从 1 升到 k。"""
    if k == 1.0:
        return a
    h, w, _ = a.shape
    x0 = man_x0(a, ph)
    G = GROUND_720
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.clip((xx - x0) / MAN_RAMP, 0, 1)
    s = 1 + (k - 1) * t * t * (3 - 2 * t)
    sx = np.where(xx > x0, x0 + (xx - x0) / s, xx)
    sy = np.where(xx > x0, G - (G - yy) / s, yy)
    out = np.stack([ndimage.map_coordinates(a[..., c].astype(np.float32), [sy, sx], order=1, mode='constant', cval=(255, 0, 255)[c])
                    for c in range(3)], -1)
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


# 趴档男生悬空（10-06 用户：「完全趴下的时候……感觉像是悬空并没有落地」）。aL 锚点里男生是一块斜板：脚尖点地，
# 胯离地约 30、胸口约 37（720 像素）；第 6 段中间他本来平趴在地上，最后 0.8 秒为了贴合尾帧被抬成这块板 —— 读成"变了个体型"。
# 做法：在锚点帧（第 7 段第 1 帧，已放大）量男生每一列身子底边离地多高（lay_profile），趴着的帧每列往下挪这么多，
# 身子贴回地面；挪的量从 x0（手、头那一截不动）往右 LAY_RAMP 内从 0 升满，手臂顺势往下弯一点。
# 用锚点量一次、各帧共用同一条：循环里蹬腿、拱身这些相对锚点的动作原样保留。
# 挪多少按 LAY_SCALE 的时间表（格式同 MAN_SCALE）：第 6 段跟放大同步；第 8 段他一开始撑起（源帧 ~16 起）就得收掉，
# 跟放大一起拖到 61 的话膝盖落地那几帧（源 ~25）还往下挪着，会陷进地板 23 像素。
LAY_RAMP = 150
LAY_SCALE = {'06': (57, 77, 0.0, 1.0), '07': (1, 1, 1.0, 1.0), '08': (14, 24, 1.0, 0.0)}


def man_x0(a, ph):
    """手机右边不动的那一截到哪：手机右 MAN_KEEP 与女生前脚拖鞋右沿 +8，取靠右的"""
    h = a.shape[0]
    # 女生前脚的拖鞋（地面一带的白块）右沿：在手机右边 150 以内找
    band = a[h * 4 // 5:, :int(ph[0] + 150)].astype(int)
    white = (band.min(-1) > 225)
    lab, n = ndimage.label(white)
    right = 0
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        if (lab[sl] == i).sum() > 60:
            right = max(right, sl[1].stop)
    return max(ph[0] + MAN_KEEP, right + 8)


def lay_profile(a, ph):
    """锚点帧里男生每列身子底边离地多高，下标 = 列 − 手机 x + 返回的 px。没有身子的列取最近的有身子的列，再取局部最低、高斯抹平"""
    x0 = int(man_x0(a, ph))
    m = fg(a)
    w = a.shape[1]
    lift = np.full(w, np.nan)
    for x in range(x0, w):
        ys = np.nonzero(m[:, x])[0]
        if len(ys):
            lift[x] = max(0, GROUND_720 - 1 - ys.max())
    ok = np.nonzero(~np.isnan(lift))[0]
    lift[:ok[0]] = lift[ok[0]]
    lift[ok[-1]:] = lift[ok[-1]]
    # 取左右 40 列内最低的：拖鞋尖往上翘、脚背这些"局部离地"的列不算，只认整段身子离地多高
    lift = ndimage.gaussian_filter1d(ndimage.minimum_filter1d(lift, 81), 10)
    return lift, int(ph[0])


def man_lay(a, ph, t):
    """趴着的帧把男生每列往下挪锚点量的离地高 × t（见 LAY_RAMP 上面的注释）"""
    if t == 0:
        return a
    lift, px = CTX['LAY']
    h, w, _ = a.shape
    x0 = man_x0(a, ph)
    u = np.clip(np.arange(w) - int(ph[0]) + px, 0, len(lift) - 1)
    r = np.clip((np.arange(w) - x0) / LAY_RAMP, 0, 1)
    dy = lift[u] * r * r * (3 - 2 * r) * t                     # 每列往下挪多少
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    sy = yy - dy[None, :]
    out = np.stack([ndimage.map_coordinates(a[..., c].astype(np.float32), [sy, xx], order=1, mode='constant', cval=(255, 0, 255)[c])
                    for c in range(3)], -1)
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def boy_mask(a, ph):
    """女赢片里男生的像素（arm_who 线稿分水岭，种子要男生的头：动漫头部检测，取手机右边那颗）。
    不用 split()：平趴在女生脚边时两人连成一块，split 把女生的腿也算给男生"""
    white = a.copy(); white[~fg(a)] = 255
    hs = [b for b in heads(Image.fromarray(white))[:2] if (b[0] + b[2]) / 2 > ph[0]]
    hc = ((hs[0][0] + hs[0][2]) / 2, (hs[0][1] + hs[0][3]) / 2) if hs else (ph[0] + 120, ph[1])
    return arm_who(a, ph, hc, body=True)


def man_sim(a, ph, k, g=0.0):
    """男生整个人绕手机中心等比放大 k（头、胳膊、身子、腿一起，形状不变，手还攥着手机），再在胯上折一下贴地：
    上身（手机 → 胯）绕手机转 α、腿（胯以后）绕胯转 γ，短裤那 ±HINGE_B 内两个转角平滑过渡 —— 上身、腿各自是整块转的，
    只有短裤跟着弯。g = 贴地权重（0~1）：
      g = 0：α = γ = 同一个角，让整个人最低的地方落回原来的高度（只放大不改姿势）；
      g = 1：α 让上身（胯往前半截）最低点落到地面、γ 让腿最低点落到地面。原片趴档是一块斜板（脚尖点地、胯和胸口离地
      30~37），用户：「还有点悬空的感觉」。
    10-07 以前的 man_grow / man_lay 只放大手机右边一截、按列下压贴地：非均匀拉伸把翘起的小腿压弯、T 恤扯歪"""
    if (k == 1.0 and g == 0) or not ph:
        return a
    boy = boy_mask(a, ph)
    P = np.array(ph, np.float32)
    by, bx = np.nonzero(boy)
    navy = boy & (a[..., 2].astype(int) > a[..., 0].astype(int) + 25) & (a.max(-1) < 140)     # 藏青短裤
    ny, nx = np.nonzero(navy & (np.arange(a.shape[1])[None, :] > P[0] + 120))
    H = np.array([nx.mean(), ny.mean()], np.float32) if len(nx) > 200 else None
    def rot(t, dx, dy):
        c, s_ = np.cos(t), np.sin(t)
        return c * dx + s_ * dy, -s_ * dx + c * dy
    def low_after(t, xs, ys, ox, oy, cx, cy):       # 绕 (cx, cy) 放大 k、转 t，再平移到 (ox, oy)，最低点 y
        return (oy + k * rot(t, xs - cx, ys - cy)[1]).max()
    ts = np.radians(np.arange(-10, 10.001, 0.05))
    far = bx > P[0] + 150
    t0 = ts[np.argmin([abs(low_after(t, bx[far], by[far], P[0], P[1], P[0], P[1]) - by[far].max()) for t in ts])]
    al = ga = t0
    if g > 0 and H is not None:
        u = (H - P) / np.linalg.norm(H - P); sH = float(np.linalg.norm(H - P))
        sb = (bx - P[0]) * u[0] + (by - P[1]) * u[1]
        G0 = GROUND_720 - 1
        tor = (sb > 0.5 * sH) & (sb < sH)
        aa = ts[np.argmin([abs(low_after(t, bx[tor], by[tor], P[0], P[1], P[0], P[1]) - G0) for t in ts])]
        al = t0 + g * (aa - t0)
        hx, hy = rot(al, H[0] - P[0], H[1] - P[1]); H1 = (P[0] + k * hx, P[1] + k * hy)
        leg = sb > sH + HINGE_B
        gg = ts[np.argmin([abs(low_after(t, bx[leg], by[leg], H1[0], H1[1], H[0], H[1]) - G0) for t in ts])]
        ga = t0 + g * (gg - t0)
    else:
        H = P; u = np.array([1, 0], np.float32); sH = 0.0
    hx, hy = rot(al, H[0] - P[0], H[1] - P[1]); H1 = (P[0] + k * hx, P[1] + k * hy)
    def fwd(qx, qy):        # 源点 → 出点
        x1, y1 = rot(al, qx - P[0], qy - P[1])
        x2, y2 = rot(ga, qx - H[0], qy - H[1])
        sq = (qx - P[0]) * u[0] + (qy - P[1]) * u[1]
        w = np.clip((sq - sH + HINGE_B) / (2 * HINGE_B), 0, 1); w = w * w * (3 - 2 * w)
        return (1 - w) * (P[0] + k * x1) + w * (H1[0] + k * x2), (1 - w) * (P[1] + k * y1) + w * (H1[1] + k * y2)
    h, w_, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w_].astype(np.float32)
    sx, sy = P[0] + (xx - P[0]) / k, P[1] + (yy - P[1]) / k        # 逆映射：不动点迭代（雅可比 ≈ k·R，按 1/k 步长收敛）
    for _ in range(20):
        fx, fy = fwd(sx, sy)
        sx, sy = sx + (xx - fx) / k, sy + (yy - fy) / k
    mag = np.array([255, 0, 255], np.float32)
    lay = np.where(boy[..., None], a.astype(np.float32), mag)
    mk = ndimage.map_coordinates(boy.astype(np.float32), [sy, sx], order=1)[..., None]
    ob = np.stack([ndimage.map_coordinates(lay[..., q], [sy, sx], order=1, cval=float(mag[q])) for q in range(3)], -1)
    # 擦掉原位置的男生：往外多擦 2 像素（不碰女生）—— 描边外那圈和品红混色的半透明像素 fg() 不算前景、boy 里没有，
    # 留在原处抠出来是一圈淡白边（男生挪开以后露出来）
    gone = ndimage.binary_dilation(boy, iterations=2) & ~(fg(a) & ~boy)
    base = np.where(gone[..., None], mag, a.astype(np.float32))
    return np.clip(base * (1 - mk) + ob * mk + 0.5, 0, 255).astype(np.uint8)


HINGE_B = 25        # 胯上折的过渡带半宽（720 像素，沿手机 → 胯的方向）


# 清晰度与抠像（10-06 用户两次：「抠图粗糙、一圈毛边」「分辨率非常低、很廉价，比纯图片差很多；头发发红；手机下缘黑边宽」）。
# 根子在片源：即梦交的是 720P 的 4:2:0 压缩视频，人只占画面 45% 高，进游戏还要放大 SC≈1.26。
# 压缩把线条糊成一格格的块、颜色边比亮度边糊两三个像素，深色边（头发、手机黑边）混上品红是一圈暗紫 ——
# 品红度 min(R,B)−G 跟亮度成正比，暗紫的品红度低、被判成不透明，于是一圈紫边又宽又硬。
# 做法：先用 Real-ESRGAN 动漫视频模型（realesr-animevideov3，4 倍）超分 —— 它是拿压缩过的动漫片训的，
# 能把块和糊边还原成干净的线条；4 倍降到 2 倍再抠（边缘有两倍的像素做过渡），抠完按 SC/2 缩回游戏大小（缩小 = 自带抗锯齿）。
# 10-06 第一版的 cutout_vid（混色反解）在 720 原帧上做，块状的锯齿和发梢紫边都还在，超分之后就不需要了。
SR_MODEL = os.path.join(HERE, 'sr', 'realesr-animevideov3.onnx')
SR_URL = 'https://huggingface.co/skillsafe-ai/realesr-animevideov3/resolve/main/model.onnx'
SR_CACHE = '/tmp/vidsr'     # 超分一帧 2~3 秒：按输入图内容缓存 2 倍图，只调抠像参数时不用重跑
DESPILL_BAND = 4            # 去溢色只动边缘往里这么多像素（2 倍图）：不透明的粉睡衣本身就偏红
DESPILL_K = 4               # 品红度超过它的才扣：粉睡衣品红度 10~20，边上扣掉一点无妨
_SESS = []


def sr_session():
    if not _SESS:
        import onnxruntime as ort
        if not os.path.exists(SR_MODEL):
            os.makedirs(os.path.dirname(SR_MODEL), exist_ok=True)
            subprocess.run(['curl', '-sL', '-o', SR_MODEL, SR_URL], check=True)
        o = ort.SessionOptions()
        o.intra_op_num_threads = 1      # 外面 Pool(8) 已经占满 8 核
        _SESS.append(ort.InferenceSession(SR_MODEL, o, providers=['CPUExecutionProvider']))
    return _SESS[0]


def sr2(a, R=1.0):
    """小图 → 超分 4 倍 → LANCZOS 降到 720 片的 2 倍那么大（1080 片 = 4/3 倍）。
    缓存键是输入图本身的摘要：原来按（段, 帧号, 放大, 贴地）当键，换了片子（男赢 11 段先用锚点合成的假片跑过）
    同帧号直接取到旧片的超分图，出来一半是假片的叠影（10-06）"""
    a = np.ascontiguousarray(a)
    key = hashlib.md5(a.tobytes() + repr((a.shape, R)).encode()).hexdigest()
    path = f'{SR_CACHE}/{key}.png'
    if os.path.exists(path):
        return np.asarray(Image.open(path).convert('RGB'))
    x = (np.ascontiguousarray(a).astype(np.float32) / 255).transpose(2, 0, 1)[None]
    y = sr_session().run(None, {'input': x})[0][0]
    y = Image.fromarray(np.clip(y.transpose(1, 2, 0) * 255 + 0.5, 0, 255).astype(np.uint8))
    y = y.resize((round(a.shape[1] * 2 / R), round(a.shape[0] * 2 / R)), Image.LANCZOS)
    os.makedirs(SR_CACHE, exist_ok=True)
    y.save(path)
    return np.asarray(y)


# 脸（头）在哪：礼物瞄脸（口红、闺蜜喷雾、档 4 真相女神 / 灭迹恶魔……）、三人组护脸都按它（main.js faceOf）。
# 第一版沿用 v14 的模板匹配（face_find，拿僵持帧里的脸当模板）：男生一跪一趴、脸转过去，三成多的帧找到了膝盖、拖鞋、短裤上，
# 打脸的礼物全偏（10-06 用户「有些礼物的特效没有对准男女主」）。改用动漫头部检测（deepghs/anime_head_detection v2.0_s，YOLO）：
# 每帧两颗头、置信度 0.84~0.91；左边那颗是女生、右边是男生。结果仍是 [中心 x, 中心 y, 半径]（整颗头含头发，同 v14），半径 = 宽高均值的一半。
HEAD_MODEL = os.path.join(HERE, 'sr', 'head_model.onnx')
HEAD_URL = 'https://huggingface.co/deepghs/anime_head_detection/resolve/main/head_detect_v2.0_s/model.onnx'
HEAD_THR = 0.3
_HEAD = []


def heads(im, size=640):
    """im（RGBA 贴图）里的头：[(x0, y0, x1, y1, 置信度)]，按置信度从高到低，重叠的去掉"""
    if not _HEAD:
        import onnxruntime as ort
        if not os.path.exists(HEAD_MODEL):
            subprocess.run(['curl', '-sL', '-o', HEAD_MODEL, HEAD_URL], check=True)
        o = ort.SessionOptions(); o.intra_op_num_threads = 1
        _HEAD.append(ort.InferenceSession(HEAD_MODEL, o, providers=['CPUExecutionProvider']))
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im.convert('RGBA'))
    w, h = im.size; k = size / max(w, h)
    c = Image.new('RGB', (size, size), (114, 114, 114)); c.paste(bg.convert('RGB').resize((round(w * k), round(h * k)), Image.BILINEAR), (0, 0))
    x = (np.asarray(c).astype(np.float32) / 255).transpose(2, 0, 1)[None]
    o = _HEAD[0].run(None, {'images': x})[0][0].T          # N × (cx, cy, w, h, 置信度)，640 画布坐标
    o = o[o[:, 4] > HEAD_THR]
    out = []
    for cx, cy, bw, bh, sc in o[np.argsort(-o[:, 4])]:
        b = ((cx - bw / 2) / k, (cy - bh / 2) / k, (cx + bw / 2) / k, (cy + bh / 2) / k)
        if all(max(0, min(b[2], q[2]) - max(b[0], q[0])) * max(0, min(b[3], q[3]) - max(b[1], q[1])) < 0.3 * (b[2] - b[0]) * (b[3] - b[1]) for q in out):
            out.append((*b, float(sc)))
    return out


def faces(im, px):
    """{'a': 女生, 'b': 男生}，各 [x, y, r]；两颗头左右分。只找到一颗（被手臂、头发挡住）时按它在手机 px 哪边定是谁，
    缺的那个 main() 里按同段前后帧补"""
    hs = sorted(heads(im)[:2], key=lambda b: b[0] + b[2])
    f = {s: [round(float(b[0] + b[2]) / 2, 1), round(float(b[1] + b[3]) / 2, 1), round(float(b[2] - b[0] + b[3] - b[1]) / 4, 1)] for s, b in zip('ab', hs)}
    if len(hs) == 1:      # 一颗：离谁上一帧近不知道，按它在手机哪边定
        f = {('a' if f['a'][0] < px else 'b'): f['a']}
    return f


# 女生头发校色（10-06 用户「头发边缘和缝隙还是带有红色、看起来脏脏的，不够飘逸」）。不只是边：视频压缩 + 超分后
# 她整片头发里都有一块块发紫、发红、发绿的色斑，发梢偏蓝紫 —— 色度噪声，抠像管不到。头发是暗、低饱和的一大片，
# 只把这些像素的色相换回锚点图里量的棕发（亮度原样保留，明暗、发丝走向不动）。
# HAIR_RGB = anchor/v2/n0.png 手机以左、亮度 15~100、非品红的像素（1.5 万个）每通道除以亮度的中位数。
# 只动手机以左（女生那一侧）：男生的黑发、藏青短裤是冷色，不能被染棕。红发花（亮的正红）、粉睡衣（亮）不在里面；
# 发梢的蓝紫饱和度高，也要换（第一版按饱和度 < 0.6 筛，发梢全漏了）。
# 只换连成大片（≥ HAIR_AREA 像素，2 倍图）的暗区：眼睛（暗紫的瞳孔）、眉毛是脸上的小块，换成棕色就改了人物设定
HAIR_RGB = np.array([1.093, 0.995, 0.776], np.float32)
HAIR_Y = (95, 125)          # 亮度低于前一个数全换、到后一个数渐变到不换
HAIR_AREA = 3000
HAIR_GAP = 25


def hair_tone(rgb, al, x_max):
    """rgb（float，2 倍图）里 x < x_max 的头发像素换成棕发色相、保留亮度"""
    Y = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    # 发花是亮的正红（R 比 G、B 都高出 1.6 倍以上、亮度 > 70）；头发里的色斑是紫红、暗红，R 跟 B 差不多或者很暗
    red = (rgb[..., 0] > rgb[..., 1] * 1.6) & (rgb[..., 0] > rgb[..., 2] * 1.6) & (Y > 70)
    w = np.clip((HAIR_Y[1] - Y) / (HAIR_Y[1] - HAIR_Y[0]), 0, 1) * ~red * (al > 0.01)
    w[:, max(0, int(x_max)):] = 0
    lab, n = ndimage.label(w > 0.5)
    if n:
        big = np.zeros(n + 1, bool); big[1:] = ndimage.sum(np.ones_like(w), lab, range(1, n + 1)) >= HAIR_AREA
        w *= ndimage.binary_dilation(big[lab], iterations=2)      # 外扩 2：大片边上渐变的那圈也算
    return rgb * (1 - w[..., None]) + np.clip(Y[..., None] * HAIR_RGB, 0, 255) * w[..., None]


def cutout_sr(a, lo=60, hi=150):
    """超分后的 2 倍图抠像：透明度同 v14 cutout（品红度 lo~hi 线性），去溢色改成边缘往里 DESPILL_BAND 像素内
    把 R、B 各扣掉品红度（min(R,B)−G）超出 DESPILL_K 的部分 —— 品红混进来只抬 R、B 不抬 G，扣掉正好还原；
    v14 按 (R+B)/2−G 只扣六成、只扣半透明那一圈，暗紫的发梢和手机黑边（不透明）扣不到"""
    a = a.astype(np.int16)
    al = np.clip((hi - keyed(a)) / (hi - lo), 0, 1)
    near = ndimage.binary_dilation(al < 0.99, iterations=DESPILL_BAND) & (al > 0.01)
    rgb = a.astype(np.float32)
    spill = np.clip(np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1] - DESPILL_K, 0, None)
    for c in (0, 2):
        rgb[..., c] = np.where(near, rgb[..., c] - spill, rgb[..., c])
    return np.clip(rgb, 0, 255), al.astype(np.float32)


def set_of(seg):
    return next(k for k, (_, ss) in SETS.items() if seg in ss)


def src_of(seg):
    return os.path.join(HERE, 'src', f'{set_of(seg)}_{seg}.mp4')


# 张嘴喊的段把嘴换成闭着的（游戏无声，10-06 用户要求人物不说话；已出的片不重出，在帧上补）：
# 段 → (参照, 模板框, 补丁框, 脸中心 x, 跟踪误差上限, 只贴口腔发深红的帧)，框都是参照里的 (x0, x1, y0, y1)，720 源像素。
# 模板 = 刘海 + 眼睛（各帧表情不同但头的轮廓稳定）；补丁 = 鼻子以下的嘴和下巴，
# 只盖到参照脸的侧面轮廓外 6 像素为止，参照是背景、这帧是手臂的地方也不盖（盖上去会糊出残影）。
# 找头：先按手机（屏幕绿气泡）比参照挪了多少定个大概 —— 两手抓着手机，头跟着手机走；再在它左右 ±30、上下 ±8 里对模板。
# 每帧单独找，不靠上一帧（14 拖一下头挪 70 多像素，一帧接一帧跟会跟丢）。
# 参照写帧号 = 用这一帧的脸；写锚点名 = 用锚点图（缩到 720）的脸。跟踪误差超上限的帧不贴：宁可留着张嘴，也别贴歪到手臂上。
# 过渡段只贴从锚点那头（首帧、尾帧里跟锚点像的那头）连着跟准的一段：再往下是换姿势的动作，头不在那儿；循环段全程一个姿势，跟准的都贴。
# 12：试3 第 5 帧咬紧牙关闭着嘴；张嘴帧和闭嘴帧交替，张嘴时口腔深红、认得出，只贴这些（闭嘴帧贴上去会在下巴边的手臂上留白条）。
#     误差 26：第 45~53、81~89 帧低头、嘴藏在手臂后（脸红被认成口腔），误差 26.9~33.7；张嘴的帧都 ≤24.4。
# 13：扑倒以后整段张嘴 —— 是尾帧锚点 bF 本身画的张嘴（10-06 已在 anchor_b3.py MOUTH 改成闭嘴），参照改好的 bF，全贴；
#     误差 34：扑倒半路的第 22、23 帧误差 36 左右、位置是错的，第 24 帧起 31~33、位置对。
# 14、15、17、18：都是用改嘴之前的 bF 出的（第 1 帧嘴部对旧 bF 11.4、对新 bF 19.1），同 13 参照新 bF。16、19 全程咬牙闭嘴，不用贴。
MOUTH = {'12': (5, (620, 700, 322, 362), (618, 700, 352, 400), 650, 26, True),
         '13': ('bF', (535, 580, 385, 412), (546, 586, 410, 436), 560, 34, False),
         '14': ('bF', (535, 580, 385, 412), (546, 586, 410, 436), 560, 34, False),
         '15': ('bF', (535, 580, 385, 412), (546, 586, 410, 436), 560, 34, False),
         '17': ('bF', (535, 580, 385, 412), (546, 586, 410, 436), 560, 34, False),
         '18': ('bF', (535, 580, 385, 412), (546, 586, 410, 436), 560, 34, False)}


def close_mouth(d, n, cfg, loop):
    ref, (tx0, tx1, ty0, ty1), (px0, px1, py0, py1), cx, emax, red_only = cfg
    if isinstance(ref, str):
        src = np.asarray(Image.open(os.path.join(HERE, 'anchor', 'v3d', ref + '.png')).convert('RGB').resize((1280, 720), Image.LANCZOS)).astype(np.float32)
    else:
        src = load(d, ref).astype(np.float32)
    tpl = src[ty0:ty1, tx0:tx1].mean(2)
    bg = ~fg(src[py0:py1, px0:px1])
    m = np.zeros(bg.shape, np.float32)
    for r in range(bg.shape[0]):                       # 每行从脸中心往右找到第一个背景像素 = 侧脸轮廓
        e = np.argmax(bg[r, cx - px0:]) + cx - px0 if bg[r, cx - px0:].any() else bg.shape[1]
        m[r, :min(bg.shape[1], e + 6)] = 1
    m[:4] = 0; m[:, :3] = 0; m[-3:] = 0
    m = ndimage.gaussian_filter(m, 2)[..., None]
    p0 = phone_green(src)[0]
    at = {}                                            # 帧 → (头挪了 dx, dy) 或 None（没跟准）
    for i in range(1, n + 1):
        a = load(d, i).astype(np.float32)
        c = int(round(phone_green(a)[0] - p0))
        win = a[ty0 - 8:ty1 + 8, tx0 + c - 30:tx1 + c + 30].mean(2)
        e = np.abs(np.lib.stride_tricks.sliding_window_view(win, tpl.shape) - tpl).mean((2, 3))
        j, k = np.unravel_index(np.argmin(e), e.shape)
        at[i] = (c + k - 30, j - 8) if e[j, k] < emax else None
    if not loop:
        order = range(1, n + 1) if isinstance(ref, int) or diff(load(d, 1), src) < diff(load(d, n), src) else range(n, 0, -1)
        run = []
        for i in order:
            if at[i] is None:
                break
            run.append(i)
        at = {i: (at[i] if i in run else None) for i in at}
    done = []
    for i, pos in at.items():
        if pos is None:
            continue
        a = load(d, i).astype(np.float32)
        sl = (slice(py0 + pos[1], py1 + pos[1]), slice(px0 + pos[0], px1 + pos[0]))
        t = a[sl]; r, g, b = t[..., 0], t[..., 1], t[..., 2]
        red = (r > 90) & (r < 230) & (g < 80) & (b < 110) & (r - g > 60)               # 口腔的深红
        if red_only and red.sum() < 20:
            continue
        keep = fg(t) & bg & ~ndimage.binary_dilation(red, iterations=3)
        mm = m * ~keep[..., None]
        a[sl] = src[py0:py1, px0:px1] * mm + t * (1 - mm)
        Image.fromarray(a.round().astype(np.uint8)).save(f'{d}/f{i:03d}.png')
        done.append(i)
    print(f'  闭嘴 {os.path.basename(d)}: 贴了 {len(done)} 帧（{min(done)}~{max(done)}）；没跟准、没贴的 {[i for i, p in at.items() if p is None]}')


# 手机屏幕（10-06 审查第 4 条）：即梦画的屏幕是几块糊开的绿色，每张画形状都不一样，播起来闪；男赢多了红蓝小圆点，两套界面对不上。
# 换成一张固定的微信聊天界面：逐帧找屏幕（亮的屏幕 + 上下两条深色边框，按每套固定的大小搜中心和角度），按手机的角度贴上去。
# 手指、拳头、边框（肤色、暗的像素）照原样留在上面。手机横着拿，界面竖屏、顶端朝左（原片的绿块也是竖条）。
SCREEN = {'女赢': (22, 11), '男赢': (25, 12)}   # 屏幕半长、半宽（720 像素，对着片子量的）
SCREEN_K = 8                                    # 界面超采样倍数
SCREEN_CACHE = '/tmp/vidscreen'


def screen_like(a):
    a = a.astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(2), a.min(2)
    white = (mn > 150) & (mx - mn < 45)
    green = (g > r + 20) & (g > b + 20) & (g > 120)
    return (white | green) & ((r * 3 + g * 6 + b) / 10 > 120)


def skin(a):
    """肤色（拳头、手指）：偏红黄、不太艳 —— 男赢原片界面上的橙色小图标艳度 150 以上，不算"""
    r, g, b = (a[..., i].astype(int) for i in range(3))
    return (r > b + 35) & (g > b) & (g > 0.62 * r) & (r - b < 110)


def screen_find(a, ph, L, H):
    """屏幕中心 xy、角度（弧度，图像坐标里长轴往右下斜为正）：在手机点 ±70×45 里，把屏幕转平（−40°~40°，1° 一档），
    找「L×H 里亮的屏幕像素最多 + 上下两条边框最暗」的位置"""
    px, py = ph
    W, Hh = 70, 45
    x0, y0 = int(px) - W, int(py) - Hh
    sub = np.empty((2 * Hh, 2 * W, 3), np.uint8); sub[:] = (255, 0, 255)
    ys0, xs0 = max(0, y0), max(0, x0)
    blk = a[ys0:y0 + 2 * Hh, xs0:x0 + 2 * W]
    sub[ys0 - y0:ys0 - y0 + blk.shape[0], xs0 - x0:xs0 - x0 + blk.shape[1]] = blk
    scr = screen_like(sub).astype(np.float32)
    dk = (sub.max(2) < 130).astype(np.float32)
    best = None
    for deg in range(-40, 41):
        rs = ndimage.rotate(scr, deg, reshape=False, order=1)      # 转 +deg：图里斜 deg 的屏幕转平
        rd = ndimage.rotate(dk, deg, reshape=False, order=1)
        strip = ndimage.uniform_filter(rd, (3, 2 * L - 10))
        sc = ndimage.uniform_filter(rs, (2 * H - 2, 2 * L - 4)) + 0.5 * (np.roll(strip, H + 1, 0) + np.roll(strip, -(H + 1), 0))
        sc[:15] = sc[-15:] = 0; sc[:, :15] = sc[:, -15:] = 0
        iy, ix = np.unravel_index(np.argmax(sc), sc.shape)
        if best is None or sc[iy, ix] > best[0]:
            best = (sc[iy, ix], ix, iy, np.radians(deg))
    _, ix, iy, th = best
    cx, cy = (2 * W - 1) / 2, (2 * Hh - 1) / 2
    dx, dy = ix - cx, iy - cy
    return [float(x0 + cx + dx * np.cos(th) - dy * np.sin(th)), float(y0 + cy + dx * np.sin(th) + dy * np.cos(th)), float(th)]


_TEX = {}


def chat_tex(L, H):
    """竖屏微信聊天界面（宽 2H、高 2L，720 像素 × SCREEN_K）：顶栏、四个气泡（白 = 收到、绿 = 发出）、输入栏。
    屏幕只有 44~50 × 22~24 像素，细节画多了读成噪点：气泡要粗，不画头像"""
    if (L, H) in _TEX:
        return _TEX[L, H]
    from PIL import ImageDraw
    w, h = 2 * H * SCREEN_K, 2 * L * SCREEN_K
    im = Image.new('RGB', (w, h), (237, 237, 237))
    d = ImageDraw.Draw(im)
    u = w / 22.0
    d.rectangle([0, 0, w, 5.5 * u], fill=(247, 247, 247))
    d.rectangle([7 * u, 2.4 * u, 15 * u, 3.6 * u], fill=(60, 60, 60))
    y = 7.5 * u
    for side, bw in (('l', 11), ('r', 15), ('r', 9), ('l', 14)):
        if y + 6 * u > h - 5 * u:
            break
        if side == 'l':
            d.rounded_rectangle([2 * u, y, (2 + bw) * u, y + 6 * u], 1.2 * u, fill=(255, 255, 255))
            d.rectangle([3.5 * u, y + 2.4 * u, (bw + 0.5) * u, y + 3.6 * u], fill=(165, 165, 165))
        else:
            d.rounded_rectangle([w - (2 + bw) * u, y, w - 2 * u, y + 6 * u], 1.2 * u, fill=(149, 236, 105))
            d.rectangle([w - (bw + 0.5) * u, y + 2.4 * u, w - 3.5 * u, y + 3.6 * u], fill=(80, 130, 60))
        y += 8.2 * u
    d.rectangle([0, h - 4 * u, w, h], fill=(247, 247, 247))
    d.rounded_rectangle([2 * u, h - 3.1 * u, w - 6 * u, h - 0.9 * u], 0.6 * u, fill=(255, 255, 255))
    _TEX[L, H] = np.asarray(im).astype(np.float32)
    return _TEX[L, H]


def screen_paste(a, prm, L, H):
    """按 (中心 x, y, 角度) 把聊天界面贴进屏幕；肤色、暗的（拳头、描边、边框）、品红底不贴。
    屏幕外 3 像素一圈里的彩色像素（男赢原片界面边上的红蓝小圆点）抹成边框色"""
    if prm is None:
        return a
    cx, cy, th = prm
    tex, K = chat_tex(L, H), SCREEN_K
    r = L + H + 6
    x0, y0 = max(0, int(cx - r)), max(0, int(cy - r))
    x1, y1 = min(a.shape[1], int(cx + r)), min(a.shape[0], int(cy + r))
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    du, dv = xx - cx, yy - cy
    u = du * np.cos(th) + dv * np.sin(th); v = -du * np.sin(th) + dv * np.cos(th)
    out = np.stack([ndimage.map_coordinates(tex[..., c], [(u + L) * K - 0.5, (H - v) * K - 0.5], order=1, mode='nearest')
                    for c in range(3)], -1)
    sub = a[y0:y1, x0:x1].astype(np.float32)
    sat = sub.max(2) - sub.min(2)
    dark = (sub @ np.array([0.3, 0.6, 0.1], np.float32) < 95) & (sat < 70)        # 描边、边框是灰黑的；暗红暗蓝的是界面图标
    edge = np.minimum(L - np.abs(u), H - np.abs(v))
    # 屏幕里的肤色只有连着屏幕外（拳头从两头盖进来）的才是手指；屏幕中间孤立的一小块是界面上的浅橙图标
    sk = skin(a[y0:y1, x0:x1])
    lab, nl = ndimage.label(sk)
    sk = np.isin(lab, np.unique(lab[sk & (edge < -1)]))
    keep = sk | dark | ~fg(a[y0:y1, x0:x1])
    al = np.clip(edge + 0.5, 0, 1) * ~keep
    ring = (edge < 0) & (edge > -3) & (sat > 60) & ~keep
    res = sub * (1 - al[..., None]) + out * al[..., None]
    res[ring] = (55, 55, 60)
    b = a.copy()
    b[y0:y1, x0:x1] = np.clip(res + 0.5, 0, 255).astype(np.uint8)
    return b


def screen_measure(job):
    d, f, L, H = job
    a = load(d, f); ph = phone_green(a)
    return f, screen_find(a, ph, L, H) if ph else None


def screen_plan(seg):
    """一段每个源帧的屏幕 (中心 x, y, 角度)：逐帧量（缓存），没找到手机的帧按前后插值；角度时间中值 5 帧再轻抹（1° 一档的量化抖动）"""
    d, n = extract(seg)
    L, H = SCREEN[set_of(seg)]
    path = f'{SCREEN_CACHE}/{seg}.json'
    tag = [open(os.path.join(d, 'source.txt')).read(), L, H]
    c = json.load(open(path)) if os.path.exists(path) else None
    if not c or c['tag'] != tag:
        with Pool(8) as p:
            got = dict(p.imap_unordered(screen_measure, [(d, f, L, H) for f in range(1, n + 1)], chunksize=4))
        c = {'tag': tag, 'v': [got[f] for f in range(1, n + 1)]}
        os.makedirs(SCREEN_CACHE, exist_ok=True)
        json.dump(c, open(path, 'w'))
    v = np.array([r if r else [np.nan] * 3 for r in c['v']], float)
    ok = ~np.isnan(v[:, 0]); idx = np.arange(n)
    v = np.stack([np.interp(idx, idx[ok], v[ok, q]) for q in range(3)], -1)
    v[:, 2] = ndimage.gaussian_filter1d(ndimage.median_filter(v[:, 2], size=5, mode='nearest'), 1.0, mode='nearest')
    return {f: v[f - 1] for f in range(1, n + 1)}


def screen_prm(seg, i):
    """图 i 的屏幕参数；RIFE 中间画按两头的参数线性插"""
    pl = CTX.get('SCR', {}).get(seg)
    if pl is None:
        return None
    if isinstance(i, str):
        f, u, nx = (int(q) for q in i[1:].split('_'))
        t = (f - u) / (nx - u)
        return pl[u] * (1 - t) + pl[nx] * t
    return pl[i]


def ground_x(a):
    """男赢两人着地点的平均 x：女生（左）最左的脚尖、男生（右）黑拖鞋最右"""
    m = fg(a); xs = np.nonzero(m.any(0))[0]
    blk = np.nonzero((a[600:].max(2) < 60).any(0))[0]
    return (xs.min() + blk.max()) / 2


def extract(seg):
    """抽帧到 TMP/<段>/。目录里记着抽的是哪个源文件（大小 + 修改时间）和闭嘴参数，变了就重抽 —— 不然换片后还拿旧片的帧"""
    d, src = os.path.join(TMP, seg), src_of(seg)
    st = os.stat(src)
    tag = f'{src} {st.st_size} {st.st_mtime_ns} {MOUTH.get(seg)}'
    mark = os.path.join(d, 'source.txt')
    if not (os.path.exists(mark) and open(mark).read() == tag and glob.glob(d + '/f*.png')):
        os.makedirs(d, exist_ok=True)
        for f in glob.glob(d + '/f*.png') + glob.glob(d + '/i*.png'):
            os.remove(f)
        subprocess.run([FF, '-loglevel', 'error', '-y', '-i', src, '-vsync', '0', d + '/f%03d.png'], check=True)
        if seg in MOUTH:
            close_mouth(d, len(glob.glob(d + '/f*.png')), MOUTH[seg], any(q[0] == seg and q[2] for q in SEGS))
        open(mark, 'w').write(tag)
    return d, len(glob.glob(d + '/f*.png'))


def load(d, i):
    """第 i 帧；i 是字符串的是 RIFE 补的中间画（见 cadence()）"""
    return np.asarray(Image.open(f'{d}/{i}.png' if isinstance(i, str) else f'{d}/f{i:03d}.png').convert('RGB'))


_RIFE = []


def rife(a, b, t):
    """a、b 两张画之间 t 处的中间画（RIFE 4.9，品红底照样补，边上补成品红再抠）"""
    import onnxruntime as ort
    if not _RIFE:
        if not os.path.exists(RIFE_MODEL):
            subprocess.run(['curl', '-sL', '-o', RIFE_MODEL, RIFE_URL], check=True)
        so = ort.SessionOptions(); so.intra_op_num_threads = 8
        _RIFE.append(ort.InferenceSession(RIFE_MODEL, so, providers=['CPUExecutionProvider']))
    h, w = a.shape[:2]; H, W = -(-h // 64) * 64, -(-w // 64) * 64
    def pad(x):
        p = np.empty((H, W, 3), np.float32); p[:] = (255, 0, 255); p[:h, :w] = x
        return (p / 255).transpose(2, 0, 1)[None]
    r = _RIFE[0].run(None, {'img0': pad(a), 'img1': pad(b), 'timestep': np.array([t], np.float32)})[0][0]
    return (r[:3].transpose(1, 2, 0)[:h, :w] * 255 + 0.5).clip(0, 255).astype(np.uint8)


def cadence(d, seg, s, e):
    """源帧 s..e 每一帧（24 格/秒）播哪张图：[(源帧, 图)]。图 = 这张画第一次出现的源帧号；同一张画停着的帧复用它。
    跟这张画的第一帧比（不跟上一帧比）：慢慢挪的画面每帧都差不到 DUP，跟上一帧比会一直认成同一张、整段冻住。
    RIFE_D 里的段：相邻两张画差超过阈值的，停着的那几帧换成 RIFE 补的中间画（图 = 'i<源帧>_<前一张>_<后一张>'，存 d/ 下）"""
    L = lambda f: load(d, f)[::2, ::2]
    starts, cur = [s], L(s)
    for f in range(s + 1, e + 1):
        a = L(f)
        if diff(a, cur) > DUP:
            starts.append(f); cur = a
    img = {}
    for k, u in enumerate(starts):
        nx = starts[k + 1] if k + 1 < len(starts) else None
        for f in range(u, nx if nx else e + 1):
            img[f] = u
        if nx and seg in RIFE_D and nx - u > 1 and diff(L(u), L(nx)) > RIFE_D[seg]:
            A, B = load(d, u), load(d, nx)
            for f in range(u + 1, nx):
                img[f] = f'i{f:03d}_{u}_{nx}'          # 文件名带上两头：DUP 改了、分画变了不会拿到旧的
                if not os.path.exists(f'{d}/{img[f]}.png'):
                    Image.fromarray(rife(A, B, (f - u) / (nx - u))).save(f'{d}/{img[f]}.png')
    return [(f, img[f]) for f in range(s, e + 1)]


def fnum(i):
    """图的源帧号（RIFE 中间画 'i020_19_21' → 20）"""
    return int(i[1:4]) if isinstance(i, str) else i


def settle(d, s, e, n):
    """过渡段从哪一帧起算到位：之后到 e 的每一帧剪影都和尾帧（第 n 帧）差不到 SETTLE（±8 像素内取最好的平移）"""
    fn = fg(load(d, n)[::2, ::2])
    def far(f):
        m = fg(load(d, f)[::2, ::2])
        return min(1 - float((fn & np.roll(m, k, 1)).sum()) / float((fn | np.roll(m, k, 1)).sum()) for k in range(-4, 5))
    f = e
    while f > s + 1 and far(f - 1) < SETTLE:
        f -= 1
    return f


def fg(a):
    return ~((a[..., 0] > 200) & (a[..., 1] < 80) & (a[..., 2] > 200))


def diff(a, b, dx=0):
    a = a.astype(np.float32); b = np.roll(b.astype(np.float32), dx, axis=1)
    m = fg(a) | fg(b)
    return float(np.abs(a - b)[m].mean())


def jump(d, R=1.0):
    """第 2 帧要右移多少才对得上第 1 帧（源像素；正 = 第 2 帧整体往左跳了这么多）。女赢量出来 20~42（720），男赢往哪跳没见过，两边都搜"""
    a, b = load(d, 1)[::2, ::2], load(d, 2)[::2, ::2]
    r = int(36 * R)
    return min(range(-r, r + 1), key=lambda s: diff(a, b, s)) * 2


def shift_to(d, i, k, R=1.0):
    """第 i 帧要右移多少才对得上第 k 帧（源像素，半分辨率搜 ±36·R）"""
    a, b = load(d, k)[::2, ::2], load(d, i)[::2, ::2]
    r = int(36 * R)
    return min(range(-r, r + 1), key=lambda s: diff(a, b, s)) * 2


def seam(d, n, dx0, R=1.0):
    """循环接缝（同 /tmp/seam.py）：起帧 a ∈ 1~8、止帧 b ∈ 最后 30 帧、平移 dx ∈ dx0 ± SEAM_DX·R，
    取「b 帧右移 dx 后和 a 帧」前景平均差最小的一组。先 1/4 分辨率、dx 步长 4 粗搜，再在 1/2 分辨率 dx ±4 细搜
    （1080 片直接半分辨率全搜要一万五千次比较、九分多钟）"""
    cache = {}
    def L(i, k):
        return cache.setdefault((i, k), load(d, i)[::k, ::k].astype(np.float32))
    best = None
    for a in range(1, 9):
        for b in range(max(a + 30, n - 29), n + 1):
            for s_ in range(int((dx0 - SEAM_DX * R) / 4), int((dx0 + SEAM_DX * R) / 4) + 1):
                r = diff(L(a, 4), L(b, 4), s_)
                if best is None or r < best[0]:
                    best = (r, a, b, s_ * 4)
    _, a, b, dx = best
    r, s_ = min((diff(L(a, 2), L(b, 2), s_), s_) for s_ in range(dx // 2 - 2, dx // 2 + 3))
    print(f'  接缝 {os.path.basename(d)}: 残差 {r:.2f} → ({a}, {b}, {s_ * 2})  确认后抄进 SEGS')
    return a, b, s_ * 2


def trim(d, n):
    """过渡段：从第一帧开始动的前一帧，到最后一帧还在动的后一帧。
    起点参照取第 3 帧不取第 1 帧：第 1 帧是照搬的锚点图，第 2 帧起是模型重画的（线条、光照都变了，差 19），跟谁比都「在动」"""
    f1, fn = load(d, 3)[::2, ::2], load(d, n)[::2, ::2]
    moving_from = [diff(load(d, i)[::2, ::2], f1) > STILL for i in range(1, n + 1)]
    moving_to = [diff(load(d, i)[::2, ::2], fn) > STILL for i in range(1, n + 1)]
    s = max(1, moving_from.index(True, 3))                  # 第 4 帧起第一帧动了的那帧的前一帧（1 起数，index 正好是前一帧）
    e = min(n, n - moving_to[::-1].index(True) + 1)         # 最后一帧还没回到尾帧的后一帧
    return s, e


def phone_green(a, R=1.0):
    """手机中心：屏幕上的微信绿气泡（找手机黑块的 find_phone 在视频里找不到 —— 视频手机是亮屏、黑边很细）"""
    a = a.astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (g > r + 25) & (g > b + 35) & (g > 140)
    m[a.shape[0] * 9 // 10:] = False
    lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=6))
    if n == 0:
        return None
    sz = ndimage.sum(m, lab, range(1, n + 1)); k = np.argmax(sz) + 1
    ys, xs = np.nonzero(m & (lab == k))
    return (xs.min() + xs.max()) / 2 + PHONE_DX * R, (ys.min() + ys.max()) / 2


def split(solid, phone):
    """贴图里每个像素是谁（1 女 / 2 男）：同 build.py edges() 的分法（挖掉手机一块，最大两块连通块各是一个人）"""
    px, py = phone
    cut = solid.copy()
    cut[max(0, int(py - 42)):int(py + 42), max(0, int(px - 54)):int(px + 54)] = False
    lab, n = two_people(cut, px)
    sizes = ndimage.sum(cut, lab, range(1, n + 1))
    big = np.argsort(sizes)[::-1][:2] + 1
    cxs = ndimage.center_of_mass(cut, lab, big)
    girl, boy = (big[0], big[1]) if cxs[0][1] < cxs[1][1] else (big[1], big[0])
    cg, cb = ndimage.center_of_mass(cut, lab, [girl, boy])
    side = np.zeros(n + 1, np.int8)
    for k, c in enumerate(ndimage.center_of_mass(cut, lab, range(1, n + 1)), 1):
        side[k] = 1 if abs(c[1] - cg[1]) < abs(c[1] - cb[1]) else 2
    who = side[lab]
    xs = np.arange(solid.shape[1])[None, :]
    box = solid & ~cut
    who[box & (xs < px)] = 1
    who[box & (xs >= px)] = 2
    return who


# 胳膊过长（10-06 用户：「男生倒地女生拉……胳膊过长导致非常诡异的表现」，要求不重出片子、肉眼看不出）。
# 毛病在女赢锚点构图：女生把手机拽在胸口高，男生扑倒 / 趴下后肩膀贴近地面，中间这段只能靠胳膊补。
# 手机 → 男生头的距离各档一样（720 像素 162），差在肩膀：跪档肩膀在头前下方（胳膊从袖口出来），扑倒、趴下时
# 肩膀在头后面、被仰起的脸挡住 —— 胳膊从手机一直伸到下巴底下，比跪档长三四成（DWPose 腕→肩 跪 126 / 扑倒 148 / 趴 170）。
# 修法：手和手机不动，男生的头、肩、上身朝手机送 D。沿「手机中心 → 男生头」这条线一维变形（s = 离手机中心多远）：
# 拳头 0 → 下巴 1（胳膊均匀缩短）→ 肩 1（头、肩整块平移、不变形）→ 胯 0（胯、腿、贴地的部分原样；竖直分量见 ARM_LIFT）。
# 只沿这条线挪，胳膊角度不变 —— 上一版整个人水平挪，胳膊立起来，像吊在女生手底下。
# 收多少按档位定（ARM_D 时间表，同 MAN_SCALE 的写法）：逐帧按关节点算过，DWPose 在趴着的帧把肩认到脖子上，
# 算出来的 D 一会儿 58 一会儿 0，人跟着抽。时间表的转折帧对着片子看的（倒下 / 撑起 / 跪起那几帧）。
# 只动男生：两人一碰（趴平时男生头挨着女生拖鞋）连通块分人就错，改按线稿分水岭分（arm_who）。
ARM_DF = 30         # 扑倒档收多少（720 像素）：腕→肩 148 → 118~128
ARM_DL = 40         # 趴档（已放大 MAN_K）170 → 130
ARM_DM = 34         # 第 6 段中间平趴（头挨着女生拖鞋）：收多了头顶进女生小腿
ARM_D = {           # 段: [(源帧, D), ...]，之间 smoothstep，两头外取端点
    '04': [(22, 0), (34, ARM_DF)],
    '05': [(1, ARM_DF)],
    '06': [(19, ARM_DF), (25, ARM_DM), (57, ARM_DM), (77, ARM_DL)],
    '07': [(1, ARM_DL)],
    '08': [(17, ARM_DL), (23, 12), (26, 12), (31, ARM_DF)],
    '09': [(8, ARM_DF), (18, 0)],
}
ARM_FIST = 50       # 手机中心往外这么远不动：手机半长 + 拳头（腕在 30~46）
ARM_TORSO = 130     # 肩 → 胯（沿线）多长：水平那一份摊在这一段（躯干拉长一点）
ARM_LIFT = 70       # 竖直那一份过了肩多远收完：胸口以下只水平挪、贴地的还贴地（10-06 第一版整段躯干跟着抬，
                    # 趴档胸口离地二三十像素，又成了用户说过的「悬空」），头和肩抬起来 = 上背弓一下
# 身子过长（10-06 用户：「男生被拉倒，身体明显会变得非常长」）。扑倒档原片男生头心 → 脚尖 636（出帧像素）= 头半径 43 的 14.8 倍，
# 跪着站着头心 → 脚底 9~10 倍、趴平脚尖绷直该 12 倍出头 —— 生视频把他的躯干和腿拉长了两成；趴档锚点原图 541 是对的，
# 放大 MAN_K（为了不比扑倒档小一圈）后也到了 628。两档都乘同一个 BODY_K，长度回到 ≈525，档间不会一大一小。
# 只压横向（贴地的还贴地、身子厚度不变），从头后沿（头心 + 半径）往后 BODY_RAMP 内从不压过渡到压满，头、肩、胳膊不动。
# 时间表 BODY_W（0~1，乘到 1 − BODY_K 上）：倒下、跪起跟 ARM_D 同几帧，中间一直压着。
BODY_K = 0.82
BODY_RAMP = 60
BODY_W = {
    '04': [(22, 0), (34, 1)], '05': [(1, 1)], '06': [(1, 1)], '07': [(1, 1)], '08': [(1, 1)],
    '09': [(8, 1), (18, 0)],
}
# 10-07 全部关掉（WARP=1 恢复）：趴档放大、贴地下压、胳膊缩短、身子横压这四道非刚性变形，
# 把男生的头和衣服扯歪（往手机送时竖直分量把 T 恤拉成一片垂下来）、上身抬成斜板、翘起的小腿被逐列下压压弯 ——
# 用户逐帧对原片：「原视频就是这样吗？……为什么会加这种进去」。出帧和原片逐帧一致，修正它们的毛病另想不变形的办法。
# 用 clear() 不重新赋值：man_k 的默认参数绑的是这几个 dict 本身
WARP = os.environ.get('WARP') == '1'
if not WARP:
    for _t in (LAY_SCALE, ARM_D, BODY_W):
        _t.clear()
    # 趴档男生画小了还得修（10-07 用户：「从半跪到完全趴下的过程中，男主整个体型有一次明显的缩小」），改用 man_sim 整人等比放大。
    # 第一版（10-07）按身长（手机 → 脚尖）对齐：身长对上了、块头没对上 —— 原片第 6 段中间平趴在女生脚边时男生画得比扑倒档还大
    # （剪影 √面积 游戏像素 288 对 246，头一样大），57→77 再缩到 214，按身长只补回 236，用户第二次报「前后还是有明显的缩小」。
    # 改按剪影大小逐帧对齐到扑倒循环的平均：06 / 08 逐帧（σ=1 帧轻抹）、07 整段一个倍数。头的大小跟着差 ±10%（原片头不随身子变）
    MAN_SCALE.clear()
MAN_SIM_SEGS = ('06', '07', '08')
MAN_SIM_LO, MAN_SIM_HI = 0.8, 1.3
# 贴地权重（man_sim 的 g，格式同 MAN_SCALE）：第 6 段倒平以后（源帧 ~20 起）、第 7 段整段、第 8 段撑起来（~16）以前
GROUND_W = {'06': (18, 28, 0.0, 1.0), '07': (1, 1, 1.0, 1.0), '08': (12, 20, 1.0, 0.0)}
_SIM = {}


def boy_size(seg):
    """原片这一段每帧男生多大：√(男生剪影像素数)（720 像素，男生按 boy_mask）。没找到手机的帧按前后插值"""
    d, n = extract(seg)
    v = []
    for i in range(1, n + 1):
        a = load(d, i); ph = phone_green(a)
        v.append(np.sqrt(boy_mask(a, ph).sum()) if ph else np.nan)
    v = np.array(v, float); ok = ~np.isnan(v); idx = np.arange(n)
    return np.interp(idx, idx[ok], v[ok])


def man_k_sim(seg, f):
    """WARP 关掉时第 seg 段第 f 帧的整人放大倍数：把男生剪影大小对齐到扑倒循环（第 5 段）的平均（见 MAN_SIM_SEGS 上面的注释）"""
    if WARP or seg not in MAN_SIM_SEGS:
        return man_k(seg, f)
    if not _SIM:
        _SIM['T'] = float(boy_size('05').mean())
    if seg not in _SIM:
        z = boy_size(seg)
        if seg == '07':
            k = np.full(len(z), _SIM['T'] / np.median(z))     # 循环里踢腿、拱身剪影大小会变：整段一个倍数，不跟着抽
        else:
            k = _SIM['T'] / ndimage.gaussian_filter1d(z, 1.0, mode='nearest')
        _SIM[seg] = np.clip(k, MAN_SIM_LO, MAN_SIM_HI)
    return float(_SIM[seg][f - 1])
ARM_MED = 7         # 手机点、头的时间中值窗（源帧）
ARM_CACHE = '/tmp/vidpose'


def arm_d(seg, f, table=ARM_D):
    ks = table.get(seg)
    if not ks:
        return 0.0
    if f <= ks[0][0]:
        return float(ks[0][1])
    for (f0, d0), (f1, d1) in zip(ks, ks[1:]):
        if f <= f1:
            t = (f - f0) / (f1 - f0)
            return d0 + (d1 - d0) * t * t * (3 - 2 * t)
    return float(ks[-1][1])


def arm_src(d, f, k, lay):
    """跟 frame_() 一样先放大、贴地，再量"""
    a = load(d, f)
    ph = phone_green(a)
    return (man_lay(man_grow(a, ph, k), ph, lay) if ph else a), ph


def arm_measure(job):
    """一帧的手机中心和男生的头（中心 xy、半径）；没手机、没找到手机右边那颗头的帧返回 None"""
    d, f, k, lay = job
    a, ph = arm_src(d, f, k, lay)
    if not ph:
        return f, None
    white = a.copy(); white[~fg(a)] = 255
    hs = [b for b in heads(Image.fromarray(white))[:2] if (b[0] + b[2]) / 2 > ph[0]]
    if not hs:
        return f, None
    b = hs[0]
    return f, [float(q) for q in (ph[0], ph[1], (b[0] + b[2]) / 2, (b[1] + b[3]) / 2, (b[2] - b[0] + b[3] - b[1]) / 4)]


def arm_plan(seg):
    """一段每个源帧的变形参数 {f: (手机中心, 方向 u, (拳, 下巴, 肩, 胯) 四个 s, D, 头中心)}。手机点、头逐帧量（缓存），
    时间中值滤掉认错的再轻抹；D 按 ARM_D"""
    d, n = extract(seg)
    jobs = [(d, f, man_k(seg, f), man_k(seg, f, LAY_SCALE)) for f in range(1, n + 1)]
    path = f'{ARM_CACHE}/{seg}.json'
    tag = [[round(j[2], 4), round(j[3], 4)] for j in jobs]
    c = json.load(open(path)) if os.path.exists(path) else None
    if not c or c['tag'] != tag:
        with Pool(8) as p:
            got = dict(p.imap_unordered(arm_measure, jobs, chunksize=2))
        c = {'tag': tag, 'v': [got[f] for f in range(1, n + 1)]}
        os.makedirs(ARM_CACHE, exist_ok=True)
        json.dump(c, open(path, 'w'))
    v = np.array([r if r else [np.nan] * 5 for r in c['v']], float)
    ok = ~np.isnan(v[:, 0]); idx = np.arange(n)
    v = np.stack([np.interp(idx, idx[ok], v[ok, q]) for q in range(5)], -1)
    v = ndimage.gaussian_filter1d(ndimage.median_filter(v, size=(ARM_MED, 1), mode='nearest'), 1.0, axis=0, mode='nearest')
    out = {}
    for f in range(1, n + 1):
        P, hc, hr = v[f - 1, :2], v[f - 1, 2:4], v[f - 1, 4]
        L = float(np.linalg.norm(hc - P))
        s_c = max(ARM_FIST + 30, L - hr * 0.9)
        s_t = L + hr
        D = min(arm_d(seg, f), 0.5 * (s_c - ARM_FIST))
        out[f] = (P, (hc - P) / L, (ARM_FIST, s_c, s_t, s_t + ARM_TORSO), D, hc, hc[0] + hr, (1 - BODY_K) * arm_d(seg, f, BODY_W))
    return out


def arm_who(a, ph, hc, body=False):
    """男生的像素：线稿分水岭。种子：女生 = 手机左边 40 以外的前景，男生 = 头中心一块 + 手机右边 260 以外的前景
    （女生前脚最远到手机右边一百出头）。分水岭在描边上分界，两人挨着也分得开。手机框里按 x 分（拳头、手机反正不动）"""
    from skimage.segmentation import watershed
    m = fg(a)
    Y = a.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    grad = np.hypot(ndimage.sobel(Y, 0), ndimage.sobel(Y, 1))
    mk = np.zeros(m.shape, np.int32)
    xs = np.arange(m.shape[1])[None, :]
    mk[m & (xs < ph[0] - 40)] = 1
    mk[m & (xs > ph[0] + 260)] = 2
    yy, xx = np.ogrid[:m.shape[0], :m.shape[1]]
    mk[m & ((yy - hc[1]) ** 2 + (xx - hc[0]) ** 2 < 15 ** 2)] = 2
    if body:    # 整个人（boy_mask）：头往右、离地 40 以上也是男生 —— 只靠头一小块种子，平趴在女生拖鞋上时 T 恤被分给女生
        mk[m & (xx > hc[0] + 40) & (yy < GROUND_720 - 40)] = 2
        # 女生的兔子拖鞋（贴地的白块，男生穿黑拖鞋）：他的头压在拖鞋上时不让头的种子漫过去
        mk[m & (a.min(-1) > 225) & (yy > GROUND_720 - 60) & (xx < hc[0] + 20)] = 1
    lab = watershed(grad, mk, mask=m)
    box = (abs(yy - ph[1]) < 42) & (abs(xx - ph[0]) < 54) & m
    lab[box] = np.where(xs >= ph[0], 2, 1)[0][np.nonzero(box)[1]]
    return lab == 2


def arm_fix(a, ph, prm):
    """按 arm_plan 的参数把男生朝手机挪（见 ARM_DF、ARM_LIFT 上面的注释）"""
    if prm is None or (prm[3] < 0.5 and prm[6] < 1e-3) or not ph:
        return a
    P, u, knots, D, hc, xb, kb = prm
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    f0, c, t, e = knots
    def disp(x, y):         # 源点 → 位移：水平分量过了肩沿躯干收到胯，竖直分量过了肩 ARM_LIFT 内就收掉；再加身子横向压
        s = (x - P[0]) * u[0] + (y - P[1]) * u[1]
        wh = np.interp(s, [-1e4, f0, c, t, e, 1e4], [0, 0, 1, 1, 0, 0])
        wv = np.interp(s, [-1e4, f0, c, t, t + ARM_LIFT, 1e4], [0, 0, 1, 1, 0, 0])
        q = np.clip(x - xb, 0, None)                     # 身子横向压 kb（见 BODY_K）：头后沿往后 BODY_RAMP 内斜率从 0 升到 kb
        body = kb * np.where(q < BODY_RAMP, q * q / (2 * BODY_RAMP), q - BODY_RAMP / 2)
        return -D * u[0] * wh - body, -D * u[1] * wv
    sx, sy = xx, yy         # 逆映射：出点 p = 源点 q + disp(q)，不动点迭代（位移的斜率 ≤ 0.5 + 0.16，收敛）
    for _ in range(10):
        dx, dy = disp(sx, sy)
        sx, sy = xx - dx, yy - dy
    boy = arm_who(a, ph, hc)
    mag = np.array([255, 0, 255], np.float32)
    lay = np.where(boy[..., None], a.astype(np.float32), mag)
    mk = ndimage.map_coordinates(boy.astype(np.float32), [sy, sx], order=1)[..., None]
    ob = np.stack([ndimage.map_coordinates(lay[..., c], [sy, sx], order=1, cval=float(mag[c])) for c in range(3)], -1)
    base = np.where(boy[..., None], mag, a.astype(np.float32))
    return np.clip(base * (1 - mk) + ob * mk + 0.5, 0, 255).astype(np.uint8)


def arm_plans(have, only):
    """女赢 ARM_D 里各段的 arm_plan 放进 CTX['ARM'][段]"""
    CTX['ARM'] = {seg: arm_plan(seg) for seg in ARM_D if seg in have and (not only or seg in only)}


# 对抗线（10-07 用户「对抗线是站着的人的最前方脚尖的位置：比如相持动作，两人脚尖相触，刚好到屏幕水平中点。
# 而有任一方倒下，则另一方一定是站立状态。站立姿势下，最前方的脚尖处，就是对抗线位置」）：
# 僵持（n）= 女生最前（最右）的脚尖和男生最前（最左）的脚尖正中；女赢各档（a*）= 女生最前的脚尖；男赢（b*）= 男生最前的脚尖。
# 脚尖 = 锚点往上 LINE_BAND 内属于这个人的最靠前一列（谁是谁按 split()）。只量循环段：游戏镜头在过渡段里从上一档的线过到这一档的。
# 每段取所有格的平均（相对锚点）存 segs[段]['line']（main.js derive 的镜头对着它）：倒退走两只脚轮流在前，单格来回 ±60，不能逐格跟。
# 以前（10-07 上午）是两人贴地一条最左到最右的正中、再加"谁都不出画"的外框约束，用户否了，box 不再存
LINE_BAND = 40


def seg_lines(segs, poses, out):
    for key, sk in segs.items():
        if not sk.get('loop'):
            sk.pop('line', None); sk.pop('box', None)
            continue
        v = []
        for n in sk['frames']:
            m = poses[n]
            who = split(np.array(Image.open(os.path.join(out, n + '.webp')))[..., 3] > 128, m['phone'])
            ay = int(round(m['ay']))
            band = who[max(0, ay - LINE_BAND):ay + 2]
            toe = lambda k: np.nonzero((band == k).sum(0) >= 2)[0]
            g = lambda: toe(1).max()                                # 女生朝右，最前 = 最右
            b = lambda: toe(2).min()                                # 男生朝左，最前 = 最左（倒下的那个不量：趴平时连通块分人会分错）
            v.append(((g() + b()) / 2 if key == 'n' else g() if key[0] == 'a' else b()) - m['ax'])
        sk['line'] = round(float(np.mean(v)), 1)
        sk.pop('box', None)


CTX = {}
SETP = {}       # 每套 {'SC', 'X0', 'G', 'R'}，main() 开头量（见那里的注释）


def frame(job):
    try:
        return frame_(job)
    except Exception as e:
        raise RuntimeError(f'{job[2]}（{job[0]} 第 {job[1]} 帧）: {e!r}') from e


def frame_(job):
    """一帧：抠像 → 缩到游戏大小 → 裁外框 → 量锚点、手机、轮廓、脸、短裤、贴地段"""
    d, i, name, off, lose, k, lay, st = job
    SC, X0, G, R = (SETP[st][q] for q in ('SC', 'X0', 'G', 'R'))
    a = load(d, i)
    ph = phone_green(a, R)
    a = man_lay(man_grow(a, ph, k), ph, lay) if WARP else man_sim(a, ph, k, lay)
    a = arm_fix(a, ph, CTX.get('ARM', {}).get(os.path.basename(d), {}).get(fnum(i)))
    a = screen_paste(a, screen_prm(os.path.basename(d), i), *SCREEN[st])
    m = fg(a); ys, xs = np.nonzero(m)
    bx0, by0 = max(0, xs.min() - 12), max(0, ys.min() - 12)
    sub = a[by0:ys.max() + 13, bx0:xs.max() + 13]
    rgb, al = cutout_sr(sr2(sub, R))
    if ph:      # 女生在手机以左；手机中心往左让开 HAIR_GAP（720 像素）：两只手、男生伸过来的手指不碰
        rgb = hair_tone(rgb, al, (ph[0] - HAIR_GAP * R - bx0) * 2 / R)
    rgb = edge_extend(rgb, al)
    im = Image.fromarray(np.concatenate([rgb, al[..., None] * 255], -1).astype(np.uint8), 'RGBA')
    im = im.resize((round(sub.shape[1] * SC), round(sub.shape[0] * SC)), Image.LANCZOS)
    al2 = np.array(im)[..., 3].astype(np.float32) / 255
    yy, xx = np.where(al2 > 0.06)
    x0, x1, y0, y1 = xx.min(), xx.max() + 1, yy.min(), yy.max() + 1
    im = im.crop((x0, y0, x1, y1))
    im.save(os.path.join(OUT, name + '.webp'), quality=86, method=4)
    ox, oy = bx0 * SC + x0, by0 * SC + y0                       # 贴图左上角在「720 画面 × SC」里的位置
    meta = {'w': int(x1 - x0), 'h': int(y1 - y0), 'src': f'{VID_DIR}/{name}.webp',
            'ax': round(float((X0 - off) * SC - ox), 1), 'ay': round(float(G * SC - oy), 1)}
    if ph:
        meta['phone'] = [round(float(ph[0] * SC - ox), 1), round(float(ph[1] * SC - oy), 1)]
        solid = np.array(im)[..., 3] > 127
        meta['edge'] = edges(solid, meta['phone'])
        if lose:     # 被拖的那个人（a 档男生 = 2，b 档女生 = 1）的贴地段（拖痕）
            who = split(solid, meta['phone'])
            meta['drag'], meta['float'] = ground_segs(solid & (who == lose), meta['ay'], meta['ax'])
    meta['face'] = faces(im, meta['phone'][0] if ph else im.width / 2)
    try:
        meta['hip'] = hip_find(im)
    except ValueError:
        pass
    return name, meta


def motion(frames, poses):
    """循环段每格 → 下一张**不同的**图（最后接回开头）剪影变了多少（1 − 交并比，按各自锚点对齐）。
    同一张画停着的几格（cadence()）算它们之后那一下：不然停着的格全是 0，走走停停时哪一格都当成脚踩实了"""
    ms = {}
    for n in dict.fromkeys(frames):
        p = poses[n]
        a = np.array(Image.open(os.path.join(OUT, n + '.webp')))[..., 3] > 127
        m = np.zeros((900, 2600), bool)
        x0, y0 = int(round(1200 - p['ax'])), int(round(880 - p['ay']))
        m[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] = a
        ms[n] = m
    N = len(frames)
    def mv(i):
        a = frames[i]
        b = next((frames[(i + k) % N] for k in range(1, N) if frames[(i + k) % N] != a), a)
        return round(1 - float((ms[a] & ms[b]).sum()) / float((ms[a] | ms[b]).sum()), 3)
    return [mv(i) for i in range(N)]


def main():
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]                 # 只重做某几段：python3 build_vid.py 03 05
    for f in glob.glob(OUT + '/*.webp'):
        if not only or os.path.basename(f)[1:3] in only:
            os.remove(f)
    # 每套的缩放与锚点：这一套的起始段第 1 帧（= n0 锚点）外框高对到游戏现行 pose_n0 的高（两套 n0 一样大、站在同一处）；
    # 脚底线 G = 外框下沿；锚点 x 按外框左沿 + 游戏 n0 的 ax 换算。R = 片高 / 720（720 像素写的常数按它换算）
    g = json.load(open(os.path.join(WEB, 'world.json')))['poses']['n0']
    have = [sg for sg in (q[0] for q in SEGS) if os.path.exists(src_of(sg))]
    for st, (s0, _) in SETS.items():
        if s0 not in have:
            print(f'{st}：没有 {os.path.basename(src_of(s0))}，这一套跳过')
            continue
        d1, _ = extract(s0)
        a1 = load(d1, 1)
        rgb, al = cutout(a1.astype(np.int16))
        yy, xx = np.where(al > 0.06)
        G = float(yy.max() + 1)
        SC = g['h'] * HERO / (G - yy.min())
        SETP[st] = dict(SC=SC, X0=xx.min() + g['ax'] / SC, G=G, R=a1.shape[0] / 720)
        print(st, {k: round(v, 4) for k, v in SETP[st].items()})
    if '07' in have:
        d7, _ = extract('07')
        a7 = load(d7, 1); ph7 = phone_green(a7)
        CTX['LAY'] = lay_profile(man_grow(a7, ph7, MAN_K), ph7)

    poses, segs = {}, {}
    old = os.path.join(OUT, 'vid.json')
    if only and os.path.exists(old):
        prev = json.load(open(old)); poses, segs = prev['poses'], prev['segs']
    jobs_all = []
    for seg, key, loop, tdx in SEGS:
        if (only and seg not in only) or seg not in have:
            continue
        st = set_of(seg); SC, R = SETP[st]['SC'], SETP[st]['R']
        for k in [k for k in poses if k.startswith(f'v{seg}_')]:
            del poses[k]
        d, n = extract(seg)
        frames = []
        if loop:
            a, b, dx = seam(d, n, loop[1], R) if loop[0] == 'auto' else loop
            j = jump(d, R) if dx else 0        # 第 2 帧左跳 j：从第 2 帧起先右挪 j，JUMP_R 帧里放回 0
            cad = cadence(d, seg, a, b - 1)
            off_of = lambda f: (f - a) / (b - a) * dx + (j * max(0.0, 1 - (f - 2) / JUMP_R) if f >= 2 else 0)
            if seg in GROUND_PIN:
                g = np.array([ground_x(load(d, f)) for f in range(a, b + 1)]) * np.sign(-dx)    # 正 = 往前（拖的方向）
                pin = np.maximum.accumulate(g) - g                                            # 比走过的最远处退回了多少
                print(f'  着地点修正 {seg}: 最大 {pin.max():.0f}，止帧处 {pin[-1]:.0f}（应为 0，否则接缝会跳）')
                off0 = off_of
                off_of = lambda f: off0(f) + pin[f - a] * np.sign(-dx)
            # cycle 取绝对值：一圈地板卷过多少像素；往哪边走由档名（a / b）定（main.js vidWalk 的 toward）
            info = {'loop': True, 'cycle': round(float(abs(dx) * SC), 1), 'jump': j, 'src': [a, b, dx]}
        else:
            s, e0 = trim(d, n)
            s = TRIM_START.get(seg, s)
            e = settle(d, s, e0, n)
            # 头尾对齐锚点：即梦第 1 帧、最后一帧是照搬的锚点图，中间是它自己重画的、整体偏 20~40 像素（同循环段的 jump）。
            # 过渡段从第 s 帧播到第 e 帧，两头都是重画的：不补的话从循环的锚点格切进来就错开这么多
            # （10-06 整条流程连拍 + 换档淡出看出来的：女赢扑倒 → 跪起两个人整体错开 30 像素）。
            # 第 s 帧对到第 1 帧、第 e 帧对到第 n 帧，各在 JUMP_R 帧里放回 0
            js, je = shift_to(d, s, 1, R), shift_to(d, e, n, R)
            off_of = lambda f: tdx * (f - s) / max(1, e - s) + js * max(0.0, 1 - (f - s) / JUMP_R) + je * max(0.0, 1 - (e - f) / JUMP_R)
            cad = cadence(d, seg, s, e)
            info = {'loop': False, 'src': [s, e], 'dx': tdx, 'align': [js, je], 'cut': round((e0 - e) / FPS, 2)}
        name_of = {}
        lose = 2 if 'a' in key else 1 if 'b' in key else 0       # 被拖的是谁：a 档男生、b 档女生、僵持没有
        for f, im in cad:
            if im not in name_of:
                fi = fnum(im)
                name_of[im] = f'v{seg}_{fi:03d}'
                jobs_all.append((d, im, name_of[im], off_of(fi), lose, man_k_sim(seg, fi), man_k(seg, fi, LAY_SCALE if WARP else GROUND_W), st))
            frames.append(name_of[im])
        info['draw'] = len(name_of)
        if loop:
            # 每格离锚点姿势多远（挪回 off 之后跟起帧比）：游戏里要离开循环时等到离得近的那几格再切进过渡段，
            # 过渡段第一帧就是锚点，硬切在拽到一半的那格上会跳一下
            a0 = fg(load(d, cad[0][1])[::2, ::2])
            def far(im):     # 1 − 剪影交并比（颜色差在压缩噪声和光照重画面前不可靠，剪影够判姿势）
                b = np.roll(fg(load(d, im)[::2, ::2]), int(round(off_of(fnum(im)) / 2)), axis=1)
                return round(1 - float((a0 & b).sum()) / float((a0 | b).sum()), 3)
            fa = {im: far(im) for im in name_of}
            info['d0'] = [fa[im] for _, im in cad]
        segs[key] = dict(info, frames=frames, fps=round(FPS, 2), seg=seg)
        print(seg, key, {k: v for k, v in info.items() if k != 'd0'}, len(frames), '格')
    arm_plans(have, only)
    CTX['SCR'] = {seg: screen_plan(seg) for seg in have if not only or seg in only}
    with Pool(8) as p:
        for name, meta in p.imap_unordered(frame, jobs_all, chunksize=2):
            poses[name] = meta
    # 个别帧手挡住了微信绿框、找不到手机（女赢第 10 段 1 帧）：按同段前后两格的手机点（相对锚点）插值补上，
    # 不然游戏里那一格手机位置停在上一帧、弹幕瞄偏
    for sk in segs.values():
        fr = sk['frames']
        for i, n in enumerate(fr):
            if 'phone' in poses[n]:
                continue
            a = next((poses[m] for m in reversed(fr[:i]) if 'phone' in poses[m]), None)
            b = next((poses[m] for m in fr[i + 1:] if 'phone' in poses[m]), None)
            if a and b:
                me = poses[n]
                me['phone'] = [round((a['phone'][k] - a[ak] + b['phone'][k] - b[ak]) / 2 + me[ak], 1) for k, ak in ((0, 'ax'), (1, 'ay'))]
                # 轮廓（礼物碰哪、女生倒没倒）按手机点分人，frame() 里没手机点就没量：补完手机点再量
                solid = np.array(Image.open(os.path.join(OUT, n + '.webp')))[..., 3] > 127
                me['edge'] = edges(solid, me['phone'])
    # 头被挡住只找到一颗（或一颗都没有）的帧：缺的那颗按同段前后两格（相对锚点）插值
    for sk in segs.values():
        fr = sk['frames']
        for i, n in enumerate(fr):
            me = poses[n]
            for s_ in 'ab':
                if s_ in me['face']:
                    continue
                a = next((poses[m] for m in reversed(fr[:i]) if s_ in poses[m]['face']), None)
                b = next((poses[m] for m in fr[i + 1:] if s_ in poses[m]['face']), None)
                src = [q for q in (a, b) if q]
                if src:
                    me['face'][s_] = [round(sum(q['face'][s_][0] - q['ax'] for q in src) / len(src) + me['ax'], 1),
                                      round(sum(q['face'][s_][1] - q['ay'] for q in src) / len(src) + me['ay'], 1),
                                      round(sum(q['face'][s_][2] for q in src) / len(src), 1)]
    # 循环段每格到下一格动了多少（对齐锚点后剪影 1 − 交并比）：游戏里走走停停时停在动得少的格上（脚踩实的那一下），
    # 不必等到离锚点近的格 —— 女赢跪档一圈 47 格只有第 0 格前后像锚点，等它要多走一整圈 5.5 米（10-06 桌面实测）
    for sk in segs.values():
        if sk['loop']:
            sk['mv'] = motion(sk['frames'], poses)
    seg_lines(segs, poses, OUT)
    json.dump({'sets': {k: {q: round(v, 4) for q, v in sp.items()} for k, sp in SETP.items()}, 'segs': segs, 'poses': dict(sorted(poses.items()))},
              open(old, 'w'), ensure_ascii=False)
    tot = sum(os.path.getsize(f) for f in glob.glob(OUT + '/*.webp'))
    print('poses', len(poses), 'size %.1f MB' % (tot / 1e6))


if __name__ == '__main__':
    main()
