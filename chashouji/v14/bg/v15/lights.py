"""v15 长卷里用程序做的光效：离线从 world.png 量出位置、切出贴图，引擎（web/bgmotion.js）只负责按时间调亮度。
产出 <out>/fx.json + 几张小贴图（世界坐标都是 world.png 像素）：
  bulbs    串灯 / 镜灯 / 蜡烛的灯泡中心（自动检测：局部顶帽 + 亮度门槛；床幔立柱上那串跟着纱帘动，在视频里，不在这里）
  fans     机箱三个风扇环的遮罩贴图 fans.png（原像素 + 饱和度 × 亮度做 alpha），引擎按它换色相
  neon     霓虹手柄"灭了"的样子 neon_off.png：灯管 → 没通电的暗玻璃，光晕 → 墙色；引擎盖上它就是灭
  windows  三扇窗的闪电补光 flash_*.png：原图越亮的地方（云、天）加得越多，楼是暗的 → 闪一下楼成剪影；上强下弱
  phone    床上手机：screen_off.png 盖住亮屏（平时是黑屏）、body.png 整只手机（震动时错位 1px 画）
  chat     聊天屏：消息列表区域的屏幕遮罩 chat_mask.png（椅背挡住的地方不画）+ 版式
用法：python3 lights.py <输出目录>"""
import os, sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__))
W = np.asarray(Image.open(os.path.join(HERE, 'world.png')).convert('RGB')).astype(np.float32)
L = W @ np.array([.299, .587, .114], np.float32)

# 串灯分组：(名字, 检测框, 亮度门槛, 顶帽门槛, 最大面积, 灯色, 光晕半径, 呼吸方式)
BULBS = [
    ('床顶串灯',   (0, 190, 300, 300),     205, 25, 120, (255, 196, 130), 16, 'wave'),
    ('照片串灯',   (1000, 180, 1300, 300), 205, 25, 120, (255, 196, 130), 16, 'wave'),
    ('照片串灯右', (1370, 270, 1600, 330), 190, 20, 120, (255, 196, 130), 16, 'wave'),
    ('梳妆镜灯',   (1080, 420, 1300, 605), 215, 20, 500, (255, 214, 160), 24, 'mirror'),
    ('窗帘杆串灯', (3285, 190, 3690, 270), 150, 30, 120, (255, 184, 110), 15, 'wave'),
]
CANDLE = (1276, 609)                       # 梳妆台上的小蜡烛：火苗抖
FANS = ((3180, 535, 3246, 652), [(3212, 559), (3212, 594), (3212, 628)])
NEON = (3050, 352, 3192, 442)
WINDOWS = {'girl': (655, 240, 880, 660), 'living': (2400, 255, 2565, 810), 'boy': (3340, 230, 3655, 600)}
PHONE = (3448, 690, 3532, 722)
CHAT = {'box': (2886, 503, 2992, 592), 'x': 2914, 'rows': [515, 529, 543, 557, 571, 585], 'bg': [50, 77, 198]}

def detect(box, lmin, thmin, amax):
    x0, y0, x1, y1 = box; X0, Y0 = max(0, x0 - 12), y0 - 12
    ls = nd.gaussian_filter(L[Y0:y1 + 12, X0:x1 + 12], 0.7)
    th = ls - nd.grey_opening(ls, size=(15, 15))
    lab, n = nd.label((th > thmin) & (ls > lmin))
    pts = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if not 2 <= len(ys) <= amax: continue
        cx, cy = xs.mean() + X0, ys.mean() + Y0
        if x0 <= cx < x1 and y0 <= cy < y1: pts.append((float(cx), float(cy), len(ys)))
    keep = []                                   # 一颗灯泡被切成几块时只留最大那块
    for p in sorted(pts, key=lambda p: -p[2]):
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > 144 for q in keep): keep.append(p)
    return [(round(x, 1), round(y, 1)) for x, y, a in keep if a >= 8]

def save(a, path):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(path)

def feather(h, w, f):
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)).astype(np.float32)
    return np.clip(d / f, 0, 1)

def build(out):
    os.makedirs(out, exist_ok=True); fx = {}
    fx['bulbs'] = [{'name': n, 'color': c, 'r': r, 'mode': m, 'pts': detect(b, lm, th, am)} for n, b, lm, th, am, c, r, m in BULBS]
    fx['bulbs'].append({'name': '蜡烛', 'color': (255, 170, 90), 'r': 12, 'mode': 'candle', 'pts': [CANDLE]})

    # 风扇：alpha = 饱和度 × 亮度（环和它的蓝光晕），暗的机箱框架不动
    x0, y0, x1, y1 = FANS[0]; R = W[y0:y1, x0:x1]
    mx, mn = R.max(-1), R.min(-1); sat = (mx - mn) / (mx + 1)
    a = np.clip((sat - 0.35) / 0.4, 0, 1) * np.clip((mx - 90) / 120, 0, 1) * feather(y1 - y0, x1 - x0, 6)
    save(np.dstack([R, a * 255]), f'{out}/fans.png')
    fx['fans'] = {'x': x0, 'y': y0, 'src': 'fans.png', 'centers': FANS[1]}

    # 霓虹灭了：灯管芯 → 暗玻璃（带一点原色），光晕 → 墙色
    x0, y0, x1, y1 = NEON; R = W[y0:y1, x0:x1]; l = L[y0:y1, x0:x1]
    wall = np.median(np.concatenate([W[y0 - 8:y0, x0:x1].reshape(-1, 3), W[y1:y1 + 8, x0:x1].reshape(-1, 3)]), 0)
    lw = wall @ np.array([.299, .587, .114])
    g = np.clip((l - lw) / (l.max() - lw), 0, 1)                      # 离墙色多亮 = 光有多强
    core = np.clip((g - 0.55) / 0.25, 0, 1)[..., None]                 # 灯管本身
    glass = wall * 0.7 + R * 0.12 + 18                                  # 没通电的灯管：比墙略亮的暗玻璃
    off = wall * (1 - core) + glass * core
    a = np.clip(g * 6, 0, 1) * feather(y1 - y0, x1 - x0, 4)             # 只盖有光的地方，墙本身不动
    save(np.dstack([off, a * 255]), f'{out}/neon_off.png')
    fx['neon'] = {'x': x0, 'y': y0, 'src': 'neon_off.png'}

    # 闪电补光（叠加用）：越亮的像素加得越多 → 天亮、楼成剪影；上强下弱；冷白
    fx['windows'] = {}
    for k, (x0, y0, x1, y1) in WINDOWS.items():
        l = L[y0:y1, x0:x1] / 255.; h, w = l.shape
        grad = np.linspace(1, 0.35, h)[:, None]
        add = (0.15 + 0.85 * l ** 1.3) * grad * feather(h, w, 10)
        col = np.array([200, 215, 255], np.float32)
        save(np.dstack([np.broadcast_to(col, (h, w, 3)), add * 255]), f'{out}/flash_{k}.png')
        fx['windows'][k] = {'x': x0, 'y': y0, 'src': f'flash_{k}.png'}

    # 手机：亮屏像素（偏蓝、够亮）= 屏幕；机身 = 屏幕外扩一圈里的暗像素
    x0, y0, x1, y1 = PHONE; R = W[y0:y1, x0:x1]; l = L[y0:y1, x0:x1]
    scr = (R[..., 2] > 150) & (R[..., 2] > R[..., 0] + 80) & (l > 70)
    scr = nd.binary_closing(scr, iterations=2)
    body = nd.binary_dilation(scr, iterations=4) & ((l < 60) | scr)
    body = nd.binary_closing(body | scr, iterations=1)
    sa = nd.gaussian_filter(nd.binary_dilation(scr, iterations=1).astype(np.float32), 0.6)
    dark = np.array([12, 15, 34], np.float32) + (R - R.mean((0, 1))) * 0.06   # 黑屏：留一点反光起伏
    save(np.dstack([dark, np.clip(sa, 0, 1) * 255]), f'{out}/screen_off.png')
    ba = nd.gaussian_filter(body.astype(np.float32), 0.5)
    save(np.dstack([R, np.clip(ba, 0, 1) * 255]), f'{out}/phone_body.png')
    ys, xs = np.nonzero(scr)
    fx['phone'] = {'x': x0, 'y': y0, 'off': 'screen_off.png', 'body': 'phone_body.png',
                   'cx': round(float(xs.mean() + x0), 1), 'cy': round(float(ys.mean() + y0), 1)}

    # 聊天屏：蓝色屏幕像素（椅背是灰的，不算）
    x0, y0, x1, y1 = CHAT['box']; R = W[y0:y1, x0:x1]
    m = (R[..., 2] > 150) & (R[..., 2] > R[..., 0] + 90)
    m = nd.binary_fill_holes(nd.binary_opening(nd.binary_closing(m, iterations=3), iterations=1))   # 头像是粉的，补上
    save(np.dstack([np.full(m.shape + (3,), 255, np.float32), nd.gaussian_filter(m.astype(np.float32), 0.6) * 255]), f'{out}/chat_mask.png')
    fx['chat'] = {**CHAT, 'box': list(CHAT['box']), 'mask': 'chat_mask.png'}

    json.dump(fx, open(f'{out}/fx.json', 'w'), ensure_ascii=False, indent=1)
    for b in fx['bulbs']: print(b['name'], len(b['pts']))
    print('phone', fx['phone']['cx'], fx['phone']['cy'])

if __name__ == '__main__':
    build(sys.argv[1])
