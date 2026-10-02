"""三人组自由组合遮挡矩阵（2026-10-01 起；同日按新判据重写）：线上每次送礼三个槽位各自从本边名单里独立随机抽一人，任意 后排 × 地板、
上方 × 后排都可能同框。这里把每个人**在场时会画的每一帧**（待机、出手 seq、进场最后落定那一帧；秋千按在场摆幅左右各转一次；
挂件层、手里拿着的道具一起）按引擎的摆法贴到屏幕上，逐帧看**画在后面的那个人**被挡了多少。

判据（2026-10-01 主控："礼物少时每个角色完整、特点清楚"，人缩小了反而认不出 —— 所以不追求外扩后完全不相交）：
  谁在后面：按 depth（上方 0.5 < 后排 0.8 < 地板 1.3，main.js 按它排远近，小的先画）。前面那个人不算被挡。
  对后面那个人的**每一帧**（前面那个人取他全部在场帧的并集 —— 两人各自出手、时机不定，哪一帧碰上哪一帧都可能）：
    · 被挡剪影占比 ≤ 8%（被挡像素 / 这一帧自己的剪影像素）；
    · 头框被挡 0 px：图集 json 写了 heads[帧]（逐帧量的框）就用它；没写的帧拿 frames.json 的 head（参考帧上量的头框，映射到图集输出像素）在这一帧里按模板重新找一次位置；前面那人外扩 4px 再比；
    · 认人点被挡 0 px：落脚区（FOOTED 的人，见第二版第 8 条）、挂件层（扇子、流苏、牛丸串……）、手里拿着的道具（hold 点；形状按 drawHeld 的画法，见 held_shape）、躯干
      （头框下沿到"头下沿 + 45% × 头下沿到脚底"那几行、头框中心左右各 1.2 个头宽以内 —— 招牌服装都在这一块），前面那人同样外扩 4px。
  前景地板在后排地面前面，挡住后排一点脚和小腿（躯干以下）本来就对，只要不超 8%。
  尺寸下限（suggest 只在这个范围里缩）：后排 s ≥ 0.8；别的槽位 ≥ 本人现值 × 0.9。先挪位置，挪不开才缩。

第二版（2026-10-01，审查第八轮「自由组合遮挡抽查」4 个漏洞）：
  1. 主角也是遮挡物：两个主角画在上方 / 后排之后、地板之前（main.js renderActors）。遮挡范围 = couple_a.png / couple_b.png ——
     正式页 ?coupleprobe=1 拍 4 段 4.8 秒胶片（哥们礼物 / 闺蜜礼物 × 开头 / 往后 4.8 秒），每个模拟步把两人单独画出来叠的并集
     （拉锯前后晃、甩开的长发都在里面）。主角对每个人判头框 0、认人点 0；剪影占比不单独卡（主角是站在画面中间不动的一大块，
     后排按设计站在自己主角身后、脚在地板上 —— 腿脚压在主角身后是这个布局本来的样子），剪影算进第 3 条合计。
  2. 认人点加上画在帧里的招牌道具：图集 json 的 ident（每帧各自的框，crewframes.py ident 按合成转角算的水枪 / 喷罐 / 滑板 / 平衡车），
     或 cfg.ident [[x0, y0, x1, y1], ...]（参考帧格内像素，每帧跟头框一样按模板重找）。框 ∩ 自己的剪影才算。
  3. 合计：一组三个人 + 两个主角同时在场，后面那个人这一帧被所有画在他前面的东西挡住的并集 ≤ 25%（TOTAL）。
     一对一的 8% 管"哪一个人挡得太多"，合计管"几样东西各挡一点加起来"。25% 的来历：主角并集占 x 145~785、y 793~1194，
     后排脚底被站位约束在视平线 845 以下（GROUND_Y，再抬就站到沙发上了），闺蜜后排挪到最好的位置光主角就挡 0~21%（全是腿脚）；
     头、躯干、招牌道具由头框 0 / 认人点 0 保住，合计管的是剩下的腿脚，25% = 主角那一份 + 同组一点余量。
  4. 不出画：在场各帧剪影横向在 0~960 以内（EXEMPT 里的人按设计出画，见第 7 条；秋千摆到两头那一下不算）；
     地板最低点 ≤ 1334、上方最高点 ≥ 200。suggest 的站位也按这条约束，所以不会再建议出一个出画的站位。
  5. 哥们后排（buddy 的 depth 0.8，B1~B10）对主角（2026-10-01 主控拍板）：男主占 x 426~785，右边只剩 175px，后排脚在地板上、又不能站到
     两人拉手机的中间，水枪 / 滑板 / 躯干必有一截压在男主身后（第二版全量扫：最好的位置也挡 4~35%）。所以只对这一种"后 × 前"改成：
       · 头框被挡 0（头框含脸和发型，照旧外扩 4px 比）；
       · 认人点**每一项**（躯干、每件帧里招牌道具、每个挂件、手里的道具，各算各的）可见面积 ≥ 70%（KEEP），按帧取最差的一格，主角不外扩（算的是真被盖住的像素）；
       · 合计 ≤ 35%（TOTAL_BACK，他当后面那人的所有组合）。
     他们对地板同伴、上方对他们，以及闺蜜全体，仍是第 1~4 条（认人点 0、合计 25%）。按项算不按并集算：水枪被挡一半而躯干全露，并集照样过 70%，但水枪已经认不出来了。
  6. 闺蜜后排（bestie 的 depth 0.8，G1~G10）对女主（2026-10-01 主控拍板，规范第 9 条，第 5 条的对称版）：头框 0、认人点逐项可见 ≥ 70% 同第 5 条；
     合计仍 ≤ 25%（女主比男主窄）。
     第 5、6 条只作用于"后排 × 自家主角"：两个主角分成两个遮挡物（女主 couple_a、男主 couple_b），后排对另一个主角仍是头框 0、认人点 0。
  7. 出画豁免（EXEMPT）：B11 / B12 扒着右屏边、G15 船尾接长到出画，都是设计本身；不查横向出画，出画像素照量、在矩阵"出画豁免"一行另列理由。
  8. 落脚区（2026-10-01 主控拍板，规范第十二轮第 1 条）：站 / 跪 / 坐在支撑面上的上方的人（FOOTED：G14 G16 G18 B14 B16 B18），
     每一帧剪影最低一行往上 40 屏幕 px 的剪影算一项认人点，前面的人外扩 4px 比，被挡 0（后排蓄力举过头顶的冰锥 / 算盘 / 外卖盒正好在支撑面那一行，
     一只靴子只占剪影 2~3%，8% 和躯干框都量不到；脚被盖住读成踩空、被戳穿）。只看人自己的剪影，不含 fixed 场景层（墙沿 / 石檐是布景）。
  9. 场景层（fixed 挂件：墙沿、石檐、墙头）格内坐标跟 at 走。cfg.at 那一版里按设计出画的那一边（scene_of），挪了 at 以后仍要出画，缩进画里的像素算出画 ——
     suggest 不会再建议出一截悬空的墙头。
  10. 跨边同屏（2026-10-01 主控，修12 方案 A：G18 挪到 at x 496、锚点越过中线）：两边同时送礼，闺蜜、哥们两组同屏。锚点越过中线的人
     （CROSS：闺蜜 at x > W/2、哥们 at x < W/2）对另一边全员逐对判（第 1 条口径，不放宽：跨边没有"自家主角"）+ 合计（两组六人 + 两个主角，
     画在他前面的每个槽位各取一人，只在跟他有交叠的人里组合）。画的先后：depth 小的先画；depth 一样时哥们先画（main.js CREWS = 哥们、闺蜜，
     sort 稳定），闺蜜在前。场景层（墙沿、石檐）跟人同一个 depth 画（drawBody → drawScene），挡别人时算进这个人的遮挡范围。
     读数写在 bestie / buddy 矩阵文件末尾（cross_section）。
  另外：人名单直接取 cast（按 depth 分槽，不再取 groups：组表只剩诊断用），ride 在场前后溜（enter.roll）的人按 ±幅度 三个位置都判。

  帧序列（cfg.sheet）：屏幕点 = at + (格内点 − anchor) × s（trio.js place()，在场时没有位移）
  单张立绘（cfg.src）：整张图一帧；头框用剪影最上面 22% 估（没有 frames.json）
  后排的滑板哥们 / 平衡车闺蜜（原 crew.js，站位随机）2026-10-01 迁成了帧序列（crewframes.py），和别人一样按 at 摆
  还没做完的人（cast / ground 里都没有）：定妆图 ref/<编号>.png 估 —— 缩到本边同槽位已做完的人的中位高度、底边中点放到中位位置；标"估"
  fixed: true 的挂件（场景层，B18 墙头）是布景不是人，不算进剪影

每个槽位同时只站一人，只扫不同槽位之间。最后给一份建议站位（suggest），写在矩阵文件末尾。

用法（在 chashouji 下）：python3 v14/trio/tools/combo_scan.py [buddy|bestie|all] [--only=B1,B2,...] [--nosuggest]
  → shots/trio_std/组合遮挡矩阵_<边>.txt；头框映射缓存 /tmp/combo_heads.json"""
import itertools, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.feature import match_template

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))   # chashouji/
WEB = os.path.join(ROOT, 'web')
TRIO_DIR = os.path.join(ROOT, 'v14/trio')
W, H = 960, 1334
DIL = 4                                        # 头框 / 认人点：前面那人外扩几 px 再比（留一道缝，轮廓线读得出）
RATIO = 0.08                                   # 被挡剪影占比上限（一个遮挡物）
TOTAL = 0.25                                   # 三人 + 主角同时在场，被挡的并集占比上限（取值理由见文件头第二版第 3 条）
GROUND_Y = (880, 1080)                         # 后排脚底 y 的绝对范围（视平线 845 + 35；再抬车轮 / 鞋底就压到沙发前的地毯边）。suggest 的"相对现值 −60~+40"会随每轮挪动往上漂，要和它取交集
KEEP, TOTAL_BACK = 0.70, 0.35                  # 后排对自家主角：认人点每一项可见 ≥ 70%；哥们后排合计 ≤ 35%（文件头第二版第 5、6 条）
CP_IDS = ('女主', '男主')                       # 两个主角各是一个遮挡物（couple_a / couple_b）
OWN = {'buddy': '男主', 'bestie': '女主'}         # 后排站在谁身后：只对这一个主角按第 5 / 6 条放宽，对另一个仍是认人点 0
DEPTH = {'ground': 0.8, 'top': 0.5, 'floor': 1.3}
SLOT = {v: k for k, v in DEPTH.items()}
S_FLOOR = {'G14': 0.693, 'G18': 0.792}          # 缩过的人：缩放下限按缩之前的值 × 0.9 定死（G14 0.77、G18 0.88，落脚区那一轮缩的）—— 按"现值 × 0.9"算，每缩一轮下限就跟着往下漂
FOOT_H = 40                                    # 落脚区高（屏幕 px）：规范第十二轮第 1 条
FOOTED = ('G14', 'G16', 'G18', 'B14', 'B16', 'B18')   # 站 / 跪 / 坐在支撑面上的上方的人（规范第十一轮第 1 条要画支撑面的那几个）：脚下被挡读成踩空 / 被戳穿
EXEMPT = {                                    # 按设计横向出画的人（不查横向出画，出画像素照样量、在矩阵里另列）：编号 → 理由
    'B11': '扒着右屏边爬进来，手和身子贴边是构图本身',
    'B12': '从右屏边弹进来扒着边，贴边是构图本身',
    'G15': '船尾按设计出画（审查第七轮打回 G15 的要求，审查_签字.md 第五批：船尾往左接长到屏幕 x ≤ 0，读成"船从画外伸进来"；停在画内是一刀平切，读成悬在客厅里的一截船头）',
}
PAIRS = [('ground', 'floor', '后排 × 地板'), ('top', 'ground', '上方 × 后排'), ('top', 'floor', '上方 × 地板（附带）')]   # (后, 前)


def load_data():
    js = r"""
const fs=require('fs');const W=process.argv[1];
const src=fs.readFileSync(W+'/trio.js','utf8');
const rope=src.match(/const ROPE\s*=\s*\{[^}]*\};/)[0];
const tune=fs.existsSync(W+'/trio_tune.js')?fs.readFileSync(W+'/trio_tune.js','utf8'):'const TRIO_TUNE={};';
const d=new Function(rope+fs.readFileSync(W+'/trio_buddy.js','utf8')+fs.readFileSync(W+'/trio_bestie.js','utf8')+tune+'\nreturn {buddy:TRIO_BUDDY,bestie:TRIO_BESTIE,tune:TRIO_TUNE};')();
process.stdout.write(JSON.stringify(d));"""
    d = json.loads(subprocess.run(['node', '-e', js, WEB], capture_output=True, text=True, check=True).stdout)
    tune = d.pop('tune')
    for side in d.values():
        side['cast'] = {k: tuned(tune.get(k), c) for k, c in side['cast'].items()}
    return d


def tuned(t, c):
    """web/trio_tune.js 合并进角色数据，和 trio.js tuned() 同一条规矩（角色数据里写了的为准；at 里的点只在同一版图集 cell 上有效，
    不一致整块作废、连同 alt）。扫描要看运行时真画的帧：idle.alt（idle2）、hold.idle2、parts.at.idle2 都从这里来（精引2）"""
    if not t: return c
    c = dict(c); atk = dict(c.get('atk') or {}); idle = dict(c.get('idle') or {})
    if t.get('dir') and not atk.get('dir'): atk['dir'] = t['dir']
    if t.get('atlasAim') and atk.get('atlas') and not atk['atlas'].get('aim'): atk['atlas'] = {**atk['atlas'], 'aim': t['atlasAim']}
    at = t.get('at'); same = bool(at and c.get('sheet') and list(at['cell']) == list(c['sheet']['cell']))
    if same and at.get('hold'): atk['hold'] = {**at['hold'], **(atk.get('hold') or {})}
    if same and at.get('arm') and not atk.get('arm'): atk['arm'] = at['arm']
    if same and at.get('parts') and c.get('parts'):
        c['parts'] = [({**q, 'at': {**at['parts'][os.path.basename(q['src']).rsplit('.', 1)[0]], **q['at']}}
                       if os.path.basename(q['src']).rsplit('.', 1)[0] in at['parts'] else q) for q in c['parts']]
    if t.get('alt') and not idle.get('alt') and (not at or same): idle['alt'] = t['alt']
    c['atk'] = atk; c['idle'] = idle
    return c


def alpha(path):
    return np.array(Image.open(path).convert('RGBA'))[..., 3] > 40


class Blob:
    """屏幕上的一块剪影：m（bool 裁到包围盒）+ 左上角屏幕坐标 (x, y)"""
    __slots__ = ('m', 'x', 'y')
    def __init__(self, m, x, y):
        ys, xs = np.nonzero(m)
        if not len(ys): self.m, self.x, self.y = np.zeros((1, 1), bool), 0, -99999; return
        self.m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; self.x = x + int(xs.min()); self.y = y + int(ys.min())
    def box(self): return self.x, self.y, self.x + self.m.shape[1], self.y + self.m.shape[0]
    def area(self): return int(self.m.sum())


def rect(x0, y0, x1, y1):
    x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
    return Blob(np.ones((max(1, y1 - y0), max(1, x1 - x0)), bool), x0, y0)


def ov(a, da, b, db):
    """两块剪影（各自平移 da / db）重叠像素"""
    ax, ay = a.x + da[0], a.y + da[1]; bx, by = b.x + db[0], b.y + db[1]
    x0, y0 = max(ax, bx), max(ay, by); x1, y1 = min(ax + a.m.shape[1], bx + b.m.shape[1]), min(ay + a.m.shape[0], by + b.m.shape[0])
    if x0 >= x1 or y0 >= y1: return 0
    return int((a.m[y0 - ay:y1 - ay, x0 - ax:x1 - ax] & b.m[y0 - by:y1 - by, x0 - bx:x1 - bx]).sum())


def ovmask(a, da, b, db):
    """a（平移 da）上被 b（平移 db）盖住的像素：返回 a.m 形状的 bool（合计遮挡要按像素并）"""
    out = np.zeros_like(a.m)
    ax, ay = a.x + da[0], a.y + da[1]; bx, by = b.x + db[0], b.y + db[1]
    x0, y0 = max(ax, bx), max(ay, by); x1, y1 = min(ax + a.m.shape[1], bx + b.m.shape[1]), min(ay + a.m.shape[0], by + b.m.shape[0])
    if x0 < x1 and y0 < y1:
        out[y0 - ay:y1 - ay, x0 - ax:x1 - ax] = a.m[y0 - ay:y1 - ay, x0 - ax:x1 - ax] & b.m[y0 - by:y1 - by, x0 - bx:x1 - bx]
    return out


def union(bs):
    bs = [b for b in bs if b.y > -9999]
    x0 = min(b.x for b in bs); y0 = min(b.y for b in bs); x1 = max(b.box()[2] for b in bs); y1 = max(b.box()[3] for b in bs)
    m = np.zeros((y1 - y0, x1 - x0), bool)
    for b in bs: m[b.y - y0:b.y - y0 + b.m.shape[0], b.x - x0:b.x - x0 + b.m.shape[1]] |= b.m
    return Blob(m, x0, y0)


def grow(b, n=DIL):
    m = np.pad(b.m, n); return Blob(ndimage.binary_dilation(m, iterations=n), b.x - n, b.y - n)


def render(m, x0, y0, s, rot=0.0, pivot=None):
    """贴图 m（bool）左上角落在屏幕 (x0, y0)、缩放 s；rot 绕屏幕点 pivot 转（rad，canvas 顺时针为正）→ Blob"""
    im = Image.fromarray((m * 255).astype(np.uint8))
    w, h = max(1, round(im.width * s)), max(1, round(im.height * s))
    im = im.resize((w, h), Image.BILINEAR)
    if rot:
        px, py = pivot[0] - x0, pivot[1] - y0
        pad = int(np.hypot(px, py) + max(w, h)) + 4
        big = Image.new('L', (w + 2 * pad, h + 2 * pad)); big.paste(im, (pad, pad))
        big = big.rotate(-np.degrees(rot), center=(px + pad, py + pad), resample=Image.BILINEAR)
        im, x0, y0 = big, x0 - pad, y0 - pad
    return Blob(np.array(im) > 100, int(round(x0)), int(round(y0)))


# ---------- 头框：frames.json 的 head（参考帧格内像素）→ 图集输出像素 ----------
_HEADS = None
def head_out(name):
    """→ (头框, 参考帧名)。输出 = anchor_out + (点 − anchor_src) × K，K = size / 参考帧剪影宽或高（frames.py cmd_build 的 tr()，参考帧缩放 1、不平移）。
    新 build 的图集 json 里直接带 head（frames.py 2026-10-01 起写），老的按 frames.json 重算一次、缓存在 /tmp"""
    global _HEADS
    meta = json.load(open(os.path.join(WEB, 'assets/trio', name + '.json')))
    if meta.get('head'): return meta['head'], meta.get('ref', 'idle')
    d = next((os.path.join(TRIO_DIR, p, name) for p in ('buddy', 'bestie', 'tools/samples') if os.path.exists(os.path.join(TRIO_DIR, p, name, 'frames.json'))), None)
    if not d: return None
    cache = '/tmp/combo_heads.json'
    if _HEADS is None: _HEADS = json.load(open(cache)) if os.path.exists(cache) else {}
    key = f"{name}:{os.path.getmtime(os.path.join(d, 'frames.json'))}:{meta['anchor']}"
    if key not in _HEADS:
        sys.path.insert(0, os.path.join(TRIO_DIR, 'tools'))
        import frames as FR
        spec = json.load(open(os.path.join(d, 'frames.json')))
        with open(os.devnull, 'w') as dn:
            so = sys.stdout; sys.stdout = dn
            try: ref = FR.cells_of(d, spec)[spec['ref']]
            finally: sys.stdout = so
        ra = np.array(ref)[..., 3] > 8; ys, xs = np.nonzero(ra)
        K = spec['size'][1] / ((xs.max() - xs.min() + 1) if spec['size'][0] == 'w' else (ys.max() - ys.min() + 1))
        (sx, sy), (ox, oy), hb = spec['anchor'], meta['anchor'], spec['head']
        box = [ox + (hb[0] - sx) * K, oy + (hb[1] - sy) * K, ox + (hb[2] - sx) * K, oy + (hb[3] - sy) * K]
        # 校一遍：源参考帧的头缩 K 倍，在图集参考帧里找（原始动作条被重出过、或者 lift / graft 动过，算出来的框会偏）
        sh = json.load(open(os.path.join(WEB, 'assets/trio', name + '.json')))
        at = np.array(Image.open(os.path.join(WEB, 'assets/trio', name + '.webp')).convert('RGBA'))
        i = sh['frames'].index(spec['ref']); cw, ch = sh['cell']
        oc = at[(i // sh['cols']) * ch:(i // sh['cols'] + 1) * ch, (i % sh['cols']) * cw:(i % sh['cols'] + 1) * cw]
        t = np.array(ref.crop(tuple(hb)).resize((max(2, round((hb[2] - hb[0]) * K)), max(2, round((hb[3] - hb[1]) * K))), Image.LANCZOS).convert('RGBA'))
        g = gray(oc)
        if t.shape[0] < g.shape[0] and t.shape[1] < g.shape[1]:
            r = match_template(g, gray(t)); iy, ix = np.unravel_index(np.argmax(r), r.shape)
            if r[iy, ix] > 0.6: box = [ix, iy, ix + t.shape[1], iy + t.shape[0]]
        _HEADS[key] = [[round(float(v), 1) for v in box], spec['ref']]
        json.dump(_HEADS, open(cache, 'w'))
    return _HEADS[key]


def gray(rgba):
    a = rgba.astype(np.float32); al = a[..., 3:4] / 255
    return (a[..., :3].mean(2, keepdims=True) * al + 255 * (1 - al))[..., 0]


def find_head(cell, ref_cell, hb):
    """参考帧头框里那块，在这一帧里（缩放不变）找最像的位置 → 这一帧的头框；匹配 < 0.45 的（头整个转过去了）退回参考帧的框"""
    x0, y0, x1, y1 = (int(round(v)) for v in hb)
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(ref_cell.shape[1], x1), min(ref_cell.shape[0], y1)
    # 只在参考位置附近找（头在一个动作里挪不出一个头宽多少；全格找会被腿、衣服上相近的明暗拐走）
    w, h = x1 - x0, y1 - y0; mx, my = int(1.3 * w), int(1.3 * h)
    wx0, wy0 = max(0, x0 - mx), max(0, y0 - my); wx1, wy1 = min(cell.shape[1], x1 + mx), min(cell.shape[0], y1 + my)
    t = gray(ref_cell[y0:y1, x0:x1]); g = gray(cell[wy0:wy1, wx0:wx1])
    if t.shape[0] >= g.shape[0] or t.shape[1] >= g.shape[1]: return [x0, y0, x1, y1]
    r = match_template(g, t); iy, ix = np.unravel_index(np.argmax(r), r.shape)
    if r[iy, ix] < 0.4: return [x0, y0, x1, y1]
    return [wx0 + ix, wy0 + iy, wx0 + ix + w, wy0 + iy + h]


def est_head(m):
    """没有头框的（单张立绘 / 定妆图估）：剪影最上面 22% 高、那几行的横向范围"""
    ys, xs = np.nonzero(m)
    if not len(ys): return [0, 0, 1, 1]
    y1 = ys.min() + 0.22 * (ys.max() - ys.min()); sel = ys <= y1
    return [xs[sel].min(), ys.min(), xs[sel].max() + 1, y1]


def torso(m, hb):
    """躯干（招牌服装）：头框下沿到 头下沿 + 45% ×（头下沿 → 脚底），头框中心左右各 1.2 个头宽以内的剪影"""
    ys = np.nonzero(m.any(1))[0]
    if not len(ys): return np.zeros_like(m)
    y0 = int(hb[3]); y1 = int(round(hb[3] + 0.45 * max(0, ys.max() - hb[3])))
    cx, hw = (hb[0] + hb[2]) / 2, (hb[2] - hb[0])
    t = np.zeros_like(m)
    t[max(0, y0):max(0, y1), max(0, int(cx - 1.2 * hw)):max(0, int(cx + 1.2 * hw))] = True
    return t & m


class Frame:
    """一帧在屏幕上：body（剪影）、head（头框）、key（认人点：躯干 + 画在帧里的招牌道具 + 挂件 + 手里拿的道具）"""
    __slots__ = ('name', 'body', 'head', 'key', 'area', 'items')
    def __init__(self, name, body, head, key, items=()):
        """items：认人点逐项 [(名, Blob)]（第二版第 5 条按项算可见率）"""
        self.name, self.body, self.head, self.key = name, body, head, key; self.area = max(1, body.area())
        self.items = [(n, b) for n, b in items if b.area() >= 30]


def foot_zone(m, s):
    """落脚区：这一帧剪影最低一行往上 FOOT_H 屏幕 px（格内 FOOT_H / s 行）以内的剪影 —— 鞋、小腿、跪地的膝、垂下来的裙摆"""
    ys = np.nonzero(m.any(1))[0]
    z = np.zeros_like(m)
    if len(ys): z[max(0, int(np.floor(ys.max() + 1 - FOOT_H / s))):] = True
    return z & m


def disc(r, x, y):
    rr = int(round(r)); yy, xx = np.mgrid[-rr:rr + 1, -rr:rr + 1]
    return Blob(xx * xx + yy * yy <= rr * rr, int(round(x)) - rr, int(round(y)) - rr)


_AIMBOX = {}
def aim_box(side):
    """拿在手里就指着对方的道具（atk.aim）瞄的点 = 对方主角的脸（main.js boyAim / girlAim），脸跟着拉锯姿势走，但总在对方剪影里：
    取对方主角在场扫过的剪影外框（闺蜜打男生 couple_b、哥们打女生 couple_a）"""
    if side not in _AIMBOX:
        m = np.array(Image.open(os.path.join(TRIO_DIR, 'tools', f"couple_{'b' if side == 'bestie' else 'a'}.png"))) > 100
        ys, xs = np.nonzero(m); _AIMBOX[side] = (xs.min(), ys.min(), xs.max(), ys.max())
    return _AIMBOX[side]


def held_shape(A, side):
    """拿在手里的道具在屏幕上可能占的地方（trio.js drawHeld）→ 函数 (握点 x, y) → Blob：
      · 3D 图集 / 程序画的球：按随机初始角挑格 → 任意朝向，半径 r × scale 的圆；
      · 平面图（prop，宽 × 高 × scale，居中画）：aim 的尖头指着对方的脸 → 按握点到对方主角剪影外框四角的角度范围扫一遍（每 2°）；
        不 aim 的转 hang × 0.2（hang = 随机 0~6 + idleSpin × t）：有 idleSpin 任意角 → 外接圆，没有就在 0~1.2 rad 里扫"""
    if A.get('atlas'): return lambda x, y: disc(A['r'] * A['atlas']['scale'], x, y)
    if not A.get('prop'): return (lambda x, y: disc(A['r'], x, y)) if A.get('r') else None
    pi = Image.open(os.path.join(WEB, A['prop'])); w, h = pi.width * A.get('scale', 1), pi.height * A.get('scale', 1)
    if not A.get('aim') and A.get('idleSpin'): return lambda x, y: disc(np.hypot(w, h) / 2, x, y)
    tip = 0 if A.get('aim') is True else A.get('aim', 0)
    def shape(x, y):
        if A.get('aim'):
            bx = aim_box(side); an = [np.arctan2(cy - y, cx - x) - tip for cx in bx[0::2] for cy in bx[1::2]]
            a0, a1 = min(an), max(an)
        else: a0, a1 = 0.0, 1.2
        rr = int(np.ceil(np.hypot(w, h) / 2)) + 1
        im = Image.new('L', (2 * rr + 1, 2 * rr + 1)); dr = ImageDraw.Draw(im)
        for a in np.arange(a0, a1 + 1e-9, np.radians(2)).tolist() + [a1]:
            ca, sa = np.cos(a), np.sin(a)
            dr.polygon([(rr + px * ca - py * sa, rr + px * sa + py * ca) for px, py in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))], fill=255)
        return Blob(np.array(im) > 0, int(round(x)) - rr, int(round(y)) - rr)
    return shape


def sheet_person(c, at, foot, side):
    """帧序列 / 单张立绘 → [Frame]（at 可以不是 cfg.at：suggest 换站位时重贴）；foot：加落脚区认人点（FOOTED 的人）；side：拿在手里 aim 的道具瞄谁（held_shape）"""
    s = at[2]; ax, ay = c['anchor']
    X0, Y0 = at[0] - ax * s, at[1] - ay * s
    P = lambda q: (at[0] + (q[0] - ax) * s, at[1] + (q[1] - ay) * s)
    A = c.get('atk') or {}
    sw = c.get('swing'); rots = [-sw['a'], 0.0, sw['a']] if sw else [0.0]
    pv = P(c['pivot'])
    if c.get('sheet'):
        sh = c['sheet']; name = os.path.basename(sh['src']).rsplit('.', 1)[0]
        rgba = np.array(Image.open(os.path.join(WEB, sh['src'])).convert('RGBA'))
        cw, ch = sh['cell']; cols = sh['cols']
        cell = lambda fn: rgba[(sh['names'].index(fn) // cols) * ch:(sh['names'].index(fn) // cols + 1) * ch,
                               (sh['names'].index(fn) % cols) * cw:(sh['names'].index(fn) % cols + 1) * cw]
        want = [c['idle']['frame']] + ([c['idle']['alt']['frame']] if c['idle'].get('alt') else [])   # 待机轮换的 idle2 也在场上画（精引2）
        for q in A.get('seq', []): want += q[0] if isinstance(q[0], list) else [q[0]]
        E = c.get('enter')
        if isinstance(E, dict) and E.get('seq') and not isinstance(E['seq'][-1][0], list):   # 进场落定那一帧（走路循环是还在走，不算在场）
            want += [E['seq'][-1][0]]
        pump = (sw or {}).get('pump')
        if pump: want += [pump['fwd'], pump['back']]
        # 出手 / 进场 / 待机引用的帧必须在 sheet.names 里：引擎按名字找格，找不到 indexOf = -1，这一段整个人不画（G30 release 漏写，放光 0.5 秒人消失、光像从半空射出）
        miss = [f for f in dict.fromkeys(want) if f not in sh['names'] and f != 'aim']
        if miss: raise SystemExit(f'{name}: seq / enter / idle 用到的帧 {miss} 不在 sheet.names {sh["names"]} 里')
        want = [f for f in dict.fromkeys(want) if f in sh['names']]
        hr = head_out(name); hb, refc = (hr[0], cell(hr[1])) if hr else (None, None)   # 头框量在参考帧上（不一定是 idle：G4 是 wind）
        cells = [(f, cell(f)) for f in want]
        # 头框：图集 json 的 heads（美术逐帧量的框，图集格内像素 {帧: [x0, y0, x1, y1]}）优先；没写的帧拿参考帧的头按模板找。
        # 模板找不可靠的情形：头侧仰 / 张嘴喊的新帧最高分只有 0.46~0.48，过了 0.4 的阈值却落在胸口（B8 新 release，报"头被挡 485 px"，实际头高过男主头顶）
        meta = json.load(open(os.path.join(WEB, 'assets/trio', name + '.json')))
        hd = meta.get('heads') or {}
        heads = {f: (list(hd[f]) if f in hd else find_head(cc, refc, hb) if hb else est_head(cc[..., 3] > 40)) for f, cc in cells}
        # 画在帧里的招牌道具：图集 json 的 ident（每帧各自的框）优先；cfg.ident 是参考帧上的框，每帧按模板重找
        # {帧: {名: 框}}（crewframes.py ident）；美术重出的图集写成 {帧: [框, ...]}（没名字），按 道具1、道具2 编号
        idf = lambda v: list(v.items()) if isinstance(v, dict) else [(f'道具{k + 1}', bx) for k, bx in enumerate(v or [])]
        idents = {f: idf(meta.get('ident', {}).get(f)) for f, _ in cells}
        if c.get('ident') and refc is not None:
            for f, cc in cells: idents[f] = idents[f] + [(f'道具{len(idents[f]) + k + 1}', find_head(cc, refc, bx)) for k, bx in enumerate(c['ident'])]
    else:
        im = np.array(Image.open(os.path.join(WEB, c['src'])).convert('RGBA'))
        cells = [('立绘', im)]; heads = {'立绘': est_head(im[..., 3] > 40)}; idents = {'立绘': []}
    # 手里可能有这件东西的帧（= 运行时 b.ammo 可能为 true）：出手帧 fire() 那一格起手里就空了，要等动作收完、扔出去的那件回来才有（trio.js reload）。
    # 只出现在出手帧及之后的帧（follow、throw……）手里一定是空的；出手前的蓄力帧、待机 / 进场 / 离场帧都可能拿着。
    # 标了 ammo 的挂件（手里那一件本身）和手持道具（hold）都只在这些帧里算
    seq = A.get('seq', []); fi = next((i for i, q in enumerate(seq) if q[2:] == ['fire']), None)
    nm = lambda qs: {f for q in qs for f in (q[0] if isinstance(q[0], list) else [q[0]])}
    E_ = c.get('enter'); X_ = (c.get('exit') or {}).get('frame')
    free = {c['idle']['frame']} | ({c['idle']['alt']['frame']} if c['idle'].get('alt') else set()) | (nm(E_['seq']) if isinstance(E_, dict) and E_.get('seq') else set()) | set(X_ if isinstance(X_, list) else [X_] if X_ else []) \
           | ({(sw or {}).get('pump', {}).get(k) for k in ('fwd', 'back')} if (sw or {}).get('pump') else set())
    empty = (nm(seq[fi:]) - nm(seq[:fi]) - free) if fi is not None else set()
    # 挂件（场景层 fixed 不算人）、道具
    parts = []
    for q in c.get('parts', []) if c.get('sheet') else []:
        if q.get('fixed'): continue
        parts.append((q, alpha(os.path.join(WEB, q['src']))))
    held = held_shape(A, side) if A.get('item') else None
    out = []
    for f, cc in cells:
        m = cc[..., 3] > 40
        hb = heads[f]; t0 = torso(m, hb); t = t0.copy(); its = [('躯干', t0)]
        if foot: fz = foot_zone(m, s); t = t | fz; its.append(('落脚区', fz))
        for tag, bx in idents[f]:
            u = _box(m.shape, bx) & m; t = t | u; its.append((tag, u))
        extra = []
        for q, pm in parts:
            a = q['at'].get(f)
            if not a or (q.get('ammo') and f in empty): continue
            x, y = P(a[:2]); sway = (q.get('sway') or [0])[0]
            pb = [render(pm, x - q['pivot'][0] * s, y - q['pivot'][1] * s, s, ang, (x, y)) for ang in {a[2] - sway, a[2], a[2] + sway}]
            extra += [('挂件 ' + os.path.basename(q['src']).rsplit('.', 1)[0], b) for b in pb]
        if held and A.get('hold', {}).get(f) and f not in empty:   # 出手帧起东西已离手
            extra.append(('手持道具', held(*P(A['hold'][f]))))
        for r in rots:
            body = render(m, X0, Y0, s, r, pv); head = render(_box(m.shape, hb), X0, Y0, s, r, pv)
            key = render(t, X0, Y0, s, r, pv)
            ex = [(n, render(e.m, e.x, e.y, 1, r, pv) if r else e) for n, e in extra]
            if ex:
                body = union([body] + [e for _, e in ex]); key = union([key] + [e for _, e in ex])
            items = [(n, render(u, X0, Y0, s, r, pv)) for n, u in its] + ex
            out.append(Frame(f + (f' 摆{r:+.2f}' if r else ''), body, head, key, items))
    return out


def couple():
    """两个主角各自在场扫过的范围（main.js ?coupleprobe=1 拍的，见文件头）→ {'女主': Person, '男主': Person}（不动、不当"后面的人"）"""
    out = {}
    for rid, w in zip(CP_IDS, 'ab'):
        b = Blob(np.array(Image.open(os.path.join(TRIO_DIR, 'tools', f'couple_{w}.png'))) > 100, 0, 0)
        out[rid] = Person(rid, 'couple', '主角', [Frame('拉锯', b, rect(0, 0, 1, 1), b)])
    return out


def _box(shape, hb):
    m = np.zeros(shape, bool); x0, y0, x1, y1 = (int(round(v)) for v in hb)
    m[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
    return m


def ref_person(side, rid, done):
    """还没做完的人：定妆图剪影，高度 = 同槽位已做完的人的中位高度，底边中点 = 他们的中位底边中点"""
    p = os.path.join(TRIO_DIR, side, 'ref', rid + '.png')
    if not os.path.exists(p) or not done: return None
    m = alpha(p); ys, xs = np.nonzero(m); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    hs = [u.m.shape[0] for u in done]; bx = [u.x + u.m.shape[1] / 2 for u in done]; by = [u.y + u.m.shape[0] for u in done]
    s = np.median(hs) / m.shape[0]
    body = render(m, np.median(bx) - m.shape[1] * s / 2, np.median(by) - m.shape[0] * s, s)
    hb = est_head(body.m)
    return [Frame('估', body, rect(body.x + hb[0], body.y + hb[1], body.x + hb[2], body.y + hb[3]), Blob(torso(body.m, hb), body.x, body.y))]


class Person:
    def __init__(self, rid, slot, kind, frames, roll=0, loose=None, lim=TOTAL, scene=()):
        """roll：ride 在场前后溜的幅度（enter.roll[0] + 细抖）—— 后面的人按 −roll / 0 / +roll 三个位置判，前面的人按溜过的范围并；
        scene：场景层（scene_of）"""
        self.rid, self.slot, self.kind, self.frames, self.scene = rid, slot, kind, frames, scene
        self.loose = loose                           # 后排：自家主角的编号（'男主' / '女主'），对他按第二版第 5 / 6 条判；别人 None
        self.lim = lim                               # 他当后面那人时的合计上限
        self.shifts = [(-roll, 0), (0, 0), (roll, 0)] if roll else [(0, 0)]
        one = union([f.body for f in frames])
        self.all = union([Blob(one.m, one.x + dx, one.y) for dx, _ in self.shifts]) if roll else one
        self.all_g = grow(self.all)


def scene_of(c, at):
    """fixed 场景层（墙沿、石檐、墙头……，trio.js drawScene：格内坐标跟 at 走）在屏幕上的横向范围，和"哪一边按设计出画" →
    [(x0, x1, 左边要出画, 右边要出画)]。哪一边要出画按 cfg.at 那一版定（G14 / G18 墙沿左端出画、B14 / B16 / B18 右端出画：读成墙从画外伸进来）；
    挪了 at 以后那一边缩进画里，就是一截悬空的墙头，算出画不合格（out_of_canvas）"""
    out = []
    for q in c.get('parts', []):
        if not q.get('fixed'): continue
        a = q['at'] if isinstance(q['at'], list) else next(iter(q['at'].values()))
        w = Image.open(os.path.join(WEB, q['src'])).width
        xs = lambda A: A[0] + (a[0] - c['anchor'][0] - q['pivot'][0]) * A[2]
        x0c, x0 = xs(c['at']), xs(at)
        out.append((x0, x0 + w * at[2], x0c < 0, x0c + w * c['at'][2] > W))
    return out


def roll_of(c):
    E = c.get('enter')
    return int(round(E['roll'][0] + (E['roll'][2] if len(E['roll']) > 2 else 0))) if isinstance(E, dict) and E.get('roll') else 0


def out_of_canvas(p, d, slot, horiz=False):
    """在场各帧剪影出画多少 px（横向出 0~960、地板低过 1334、上方高过 200 的像素行 / 列数之和）+ 场景层该出画的那一边缩进画里多少 px。秋千摆到两头的那两帧不算。
    EXEMPT 里的人不算横向；horiz=True 只量横向（给豁免那一行报读数）"""
    bad = 0
    for f in p.frames:
        if ' 摆' in f.name: continue
        x0, y0, x1, y1 = f.body.box(); dx = d[0]
        lo, hi = min(sx for sx, _ in p.shifts), max(sx for sx, _ in p.shifts)
        if horiz or p.rid not in EXEMPT: bad += max(0, -(x0 + dx + lo)) + max(0, x1 + dx + hi - W)
        if horiz: continue
        if slot == 'floor': bad += max(0, y1 + d[1] - 1334)
        if slot == 'top': bad += max(0, 200 - (y0 + d[1]))
    if not horiz:
        for x0, x1, L, Rt in p.scene:                    # 场景层按设计出画的那一边缩进画里多少 px
            bad += (max(0, int(np.ceil(x0 + d[0]))) if L else 0) + (max(0, int(np.ceil(W - (x1 + d[0])))) if Rt else 0)
    return bad


_J = {}
def judge_c(back, db, front, dfr):
    """judge 的缓存版（suggest 里同一对被反复问）"""
    k = (back, tuple(db), front, tuple(dfr))            # 键里放对象本身（不是 id()）：缓存持有引用，旧 Person 回收后 id 复用不会串到别人的结果
    if k not in _J:
        if len(_J) > 200000: _J.clear()
        _J[k] = judge(back, db, front, dfr)
    return _J[k]


def judge(back, db, front, dfr):
    """后面那人（平移 db）× 前面那人（平移 dfr）：返回 (最坏帧占比, 那一帧名, 头框被挡 px, 认人点被挡 px, 认人点最差一项可见率, 那一项「名 @ 帧」)，
    都取所有帧里最坏的。可见率只在后排对自家主角时算（第二版第 5 / 6 条），别的恒为 1"""
    if not ov(back.all_g, db, front.all_g, dfr): return (0.0, '', 0, 0, 1.0, '')
    worst, wf, hd, ky, kp, kw = 0.0, '', 0, 0, 1.0, ''
    vis = back.loose == front.rid
    for sx, sy in back.shifts:
        d = (db[0] + sx, db[1] + sy)
        for f in back.frames:
            r = ov(f.body, d, front.all, dfr) / f.area
            if r > worst: worst, wf = r, f.name
            hd = max(hd, ov(f.head, d, front.all_g, dfr)); ky = max(ky, ov(f.key, d, front.all_g, dfr))
            if vis:
                for n, b in f.items:
                    v = 1 - ov(b, d, front.all, dfr) / b.area()
                    if v < kp: kp, kw = v, f'{n} @ {f.name}'
    return worst, wf, hd, ky, kp, kw


_OCC = {}
def _occ(back, db, p, dp):
    """back（平移 db）每个溜位 × 每一帧被 p（平移 dp）盖住的掩码（缓存：suggest 里同一对会被上百个组合反复问）"""
    k = (back, tuple(db), p, tuple(dp))                 # 同 judge_c：放对象本身，不用 id()
    if k not in _OCC:
        if len(_OCC) > 20000: _OCC.clear()
        _OCC[k] = [ovmask(f.body, (db[0] + sx, db[1] + sy), p.all, dp) for sx, sy in back.shifts for f in back.frames]
    return _OCC[k]


def total(back, db, fronts):
    """合计：后面那人每一帧被 fronts（[(Person, 平移)]，含主角）盖住的像素并集 / 自己的剪影 → (最坏占比, 那一帧)"""
    fronts = [(p, d) for p, d in fronts if ov(back.all_g, db, p.all_g, d)]
    if len(fronts) < 2 and not (fronts and fronts[0][0].rid in CP_IDS): return (0.0, '')   # 只有一个同伴挡：一对一的 8% 判过了（主角一对一不卡剪影，要算）
    ms = [_occ(back, db, p, d) for p, d in fronts]
    fr = [f for _ in back.shifts for f in back.frames]
    worst, wf = 0.0, ''
    for i, f in enumerate(fr):
        if sum(m[i].sum() for m in ms) / f.area <= worst: continue     # 并集 ≤ 各自之和：和都不超当前最坏，这一帧不用并
        u = ms[0][i].copy()
        for m in ms[1:]: u |= m[i]
        r = u.sum() / f.area
        if r > worst: worst, wf = r, f.name
    return worst, wf


def ok_cell(j, cp=False, loose=False):
    """cp：前面是主角（剪影只算进合计）；loose：后面是后排、前面是他自家主角（第二版第 5 / 6 条：头框 0、认人点逐项可见 ≥ KEEP）"""
    if cp and loose: return j[2] == 0 and j[4] >= KEEP
    return (cp or j[0] <= RATIO) and j[2] == 0 and j[3] == 0


def fmt(j, cp=False, loose=False):
    if not j[0] and not j[2] and not j[3]: return '0'
    t = f'{j[0]:.1%}'
    if j[2]: t += f' 头{j[2]}'
    if cp and loose: t += f' 见{j[4]:.0%}'
    elif j[3]: t += f' 认{j[3]}'
    return t + ('' if ok_cell(j, cp, loose) else ' ✗')


def back_rule(side, sl):
    """→ (loose, lim)：后排对自家主角放宽（第二版第 5 / 6 条），合计上限哥们后排 35%、其余 25%"""
    if sl != 'ground': return None, TOTAL
    return OWN[side], (TOTAL_BACK if side == 'buddy' else TOTAL)


def build(side, D, at_over=None):
    """cast 里每个人按 depth 分槽 → ids {槽: [编号]}、ppl {编号: Person}（含 '女主' / '男主'）"""
    data = D[side]; at_over = at_over or {}
    ids = {sl: [] for sl in DEPTH}; ppl = {}
    for rid, c in data['cast'].items():
        sl = SLOT.get(c.get('depth'))
        if not sl: continue
        ids[sl].append(rid)
        ppl[rid] = Person(rid, sl, 'sheet' if c.get('sheet') else '单张', sheet_person(c, at_over.get(rid, c['at']), rid in FOOTED, side), roll_of(c), *back_rule(side, sl),
                          scene_of(c, at_over.get(rid, c['at'])))
    for sl in ids: ids[sl].sort(key=lambda r: int(r[1:]))
    ppl.update(couple())
    return ids, ppl


def occluders(ids, slot):
    """画在这个槽位前面的槽位（主角另算：上方、后排都在主角后面）"""
    return [fr for bk, fr, _ in PAIRS if bk == slot]


def check_all(ids, ppl, at=None, who=None):
    """全部判一遍（at：{编号: (dx, dy)} 平移；who：只看涉及这些人的项）→ (对数, 不过的对, 组数, 不过的组)
    对：每个人 × 每个画在他前面的人 / 主角；组：每一组（后排 g, 上方 t, 地板 f）里后排、上方两个人的合计"""
    at = at or {}; d = lambda r: at.get(r, (0, 0))
    CP = [(ppl[c], (0, 0)) for c in CP_IDS]; pairs, badp = 0, []
    for bk in ('ground', 'top'):
        for r in ids[bk]:
            fronts = [(c, ppl[c]) for fr in occluders(ids, bk) for c in ids[fr]] + [(c, ppl[c]) for c in CP_IDS]
            for c, pc in fronts:
                if who and r not in who and c not in who: continue
                j = judge(ppl[r], d(r), pc, d(c)); pairs += 1
                if not ok_cell(j, c in CP_IDS, ppl[r].loose == c): badp.append((r, c, j))
    groups, badg = 0, []
    for g in ids['ground']:
        for f in ids['floor']:
            if who and not ({g, f} & set(who)): continue
            t_ = total(ppl[g], d(g), [(ppl[f], d(f))] + CP); groups += 1
            if t_[0] > ppl[g].lim: badg.append((g, (g, None, f), t_))
    for t in ids['top']:
        for g in ids['ground']:
            for f in ids['floor']:
                if who and not ({t, g, f} & set(who)): continue
                t_ = total(ppl[t], d(t), [(ppl[g], d(g)), (ppl[f], d(f))] + CP); groups += 1
                if t_[0] > ppl[t].lim: badg.append((t, (g, t, f), t_))
    return pairs, badp, groups, badg


def scan(side, D):
    ids, ppl = build(side, D)
    own, lim = OWN[side], back_rule(side, 'ground')[1]
    out = [f'# 组合遮挡矩阵 · {side}（combo_scan.py，2026-10-01 第二版判据：主角算遮挡物、帧里招牌道具算认人点、合计 ≤ {TOTAL:.0%}、不出画；'
           f'第 8 / 9 条：后排对自家主角（{own}）头框 0 + 认人点逐项可见 ≥ {KEEP:.0%}、后排合计 ≤ {lim:.0%}）',
           f'一对一：画在后面的人（上方 0.5 < 后排 0.8 < 主角 < 地板 1.3）逐帧被挡剪影 ≤ {RATIO:.0%}（主角不卡剪影）、头框被挡 0、认人点（躯干 + 帧里招牌道具 + 挂件 + 手里道具）被挡 0；'
           f'头 / 认人点按前面那人外扩 {DIL}px 比。合计：一组三人 + 两个主角同时在场，后面那人被挡的并集 ≤ {TOTAL:.0%}（后排 ≤ {lim:.0%}）。',
           f'后排 × {own}：只判头框 0 和认人点逐项可见 ≥ {KEEP:.0%}（主角不外扩，"见N%" = 最差一项可见率）；两个主角分开判，后排 × 另一个主角仍是认人点 0。',
           '格子：最坏一帧的被挡占比；"头N" 头框被挡 N px；"认N" 认人点被挡 N px；"见N%" 认人点最差一项可见；✗ 不过。行 = 后面的人，列 = 前面的人。']
    bad = []
    for bk, fr, title in PAIRS:
        rows, cols = ids[bk], ids[fr] + list(CP_IDS)
        out.append(f'\n== {title}（行在后 × 列在前；最后两列是两个主角）')
        out.append('        ' + ''.join(f'{c:>14}' for c in cols))
        for r in rows:
            cells = []
            for c in cols:
                if c in CP_IDS and bk == 'top' and fr == 'floor': cells.append(f'{"同上":>14}'); continue
                j = judge(ppl[r], (0, 0), ppl[c], (0, 0))
                cells.append(f'{fmt(j, c in CP_IDS, ppl[r].loose == c):>14}')
                if not ok_cell(j, c in CP_IDS, ppl[r].loose == c): bad.append((r, c, j))
            out.append(f'{r:>8}' + ''.join(cells))
    bad = list({(r, c): (r, c, j) for r, c, j in bad}.values())
    _, _, ng, badg = check_all(ids, ppl)
    out.append(f'\n== 一对一不过 {len(bad)} 对')
    for r, c, j in sorted(bad, key=lambda q: -q[2][0]):
        lo = ppl[r].loose == c
        out.append(f'  {r} 在 {c} 后面：最坏帧 {j[1]} 被挡 {j[0]:.1%}' + (f'，头框 {j[2]} px' if j[2] else '') +
                   (f'，认人点最差一项可见 {j[4]:.1%}（{j[5]}）' if lo else f'，认人点 {j[3]} px' if j[3] else ''))
    out.append(f'\n== 合计（{ng} 组 × 后面的人）超过上限（{TOTAL:.0%}；后排 {lim:.0%}）：{len(badg)} 项' + ('（只列每人最坏的一组）' if badg else ''))
    worst = {}
    for r, grp, t_ in badg:
        if r not in worst or t_[0] > worst[r][1][0]: worst[r] = (grp, t_)
    for r, (grp, t_) in sorted(worst.items(), key=lambda q: -q[1][1][0]):
        n = sum(1 for x in badg if x[0] == r)
        out.append(f'  {r}：{n} 组超，最坏 后排 {grp[0]} / 上方 {grp[1] or "-"} / 地板 {grp[2]}，帧 {t_[1]} 合计被挡 {t_[0]:.1%}')
    oc = [(r, out_of_canvas(ppl[r], (0, 0), ppl[r].slot)) for sl in ids for r in ids[sl]]
    oc = [(r, n) for r, n in oc if n]
    out.append('\n== 出画（在场帧剪影出 0~960 / 地板低过 1334 / 上方高过 200，逐帧像素和；场景层按设计出画的那一边缩进画里也算；豁免的人不查横向，秋千两头不算）：' +
               ('、'.join(f'{r} {n}' for r, n in oc) if oc else '无'))
    out.append(exempt_line(ids, ppl))
    np_ = sum(len(ids[bk]) * (sum(len(ids[fr]) for fr in occluders(ids, bk)) + len(CP_IDS)) for bk in ('ground', 'top'))
    out.append(f'\n== 结论（现站位 cfg.at）：一对一 {np_} 对不过 {len(bad)}；合计 {ng} 组超 {len(badg)}；出画 {len(oc)} 人（豁免另列，见上一行）')
    return '\n'.join(out), ids, ppl


def exempt_line(ids, ppl, at=None):
    """出画豁免：在场的豁免人各自横向出画多少 px + 理由（不算进出画）"""
    rs = [r for sl in ids for r in ids[sl] if r in EXEMPT]
    d = lambda r: (at or {}).get(r, (0, 0))
    return '\n== 出画豁免（按设计出画，不算进出画；读数 = 横向出画像素和）：' + ('无' if not rs else ''.join(
        f'\n  {r}：横向出画 {out_of_canvas(ppl[r], d(r), ppl[r].slot, horiz=True)} px —— {EXEMPT[r]}' for r in rs))


def suggest(side, D, ids, ppl, fixed_ids=(), start=None):
    """建议站位：轮流给不过的人找挪动最小的站位（|dx| + |dy|，10px 一档），让一对一、合计、不出画都满足。
    先挪，挪不开才缩：缩一档记 1000 分，后排缩到 s ≥ 0.8，别的槽位缩到 ≥ 本人现值 × 0.9。
    20px 一档，横向 ±200、竖向 −100 ~ +40（后排 −60 起，且脚底绝对 y 在 GROUND_Y 880~1080 以内：再往上就不在地板上了；上方 −260 起）；后排只在自己主角那一侧（哥们 x ≥ 600、闺蜜 x ≤ 360，
    中间是两人拉手机的地方），上方也只在自己那一侧（哥们 x ≥ 560、闺蜜 x ≤ 400），地板横向只挪 ±60（地板在两个下角，往中间挪会压到拉手机那一块）。主角不动。fixed_ids：不许挪的人（只当约束）。
    start：{编号: x}，从这个 x 起搜（主控已采纳的站位，如 B6 / B7 x 820；过了就不再挪）"""
    data = D[side]
    movers = [r for r in ppl if r not in CP_IDS]
    slot = {r: ppl[r].slot for r in movers}
    def scales(r):
        s0 = data['cast'][r]['at'][2]
        lo = 0.8 if slot[r] == 'ground' else S_FLOOR.get(r, s0 * 0.9)
        ks = [s0]; v = s0
        while v - 0.02 >= lo - 1e-9: v = round(v - 0.02, 3); ks.append(v)
        if ks[-1] > lo + 1e-9 and slot[r] == 'ground': ks.append(round(lo, 3))
        return ks
    var = {}
    def person(r, s):
        if r in CP_IDS: return ppl[r]
        var.setdefault(r, {})
        if s not in var[r]:
            a = data['cast'][r]['at']; c = data['cast'][r]
            var[r][s] = ppl[r] if s == a[2] else Person(r, slot[r], ppl[r].kind, sheet_person(c, [a[0], a[1], s], r in FOOTED, side), roll_of(c), ppl[r].loose, ppl[r].lim,
                                                                         scene_of(c, [a[0], a[1], s]))
        return var[r][s]
    cur = {r: (data['cast'][r]['at'][2], [(start or {}).get(r, data['cast'][r]['at'][0]) - data['cast'][r]['at'][0], 0]) for r in movers}
    P = lambda r, s=None, d=None: (person(r, cur[r][0] if s is None else s), cur[r][1] if d is None else d) if r not in CP_IDS else (ppl[r], [0, 0])
    def fronts_of(sl): return [c for fr in occluders(ids, sl) for c in ids[fr]]
    def fails(r, s, d, early=False, weighted=False):
        """不过的项数；early：搜索用，一对一先判（便宜），碰到第一项不过就返回。
        weighted：按受影响的组合数计（每边每槽 10 人 → 一组 1000 种里：对主角不过 = 这个人在的全部 100 种、一对一或两人合计 = 10 种、三人合计 = 1 种）"""
        W1 = lambda k: (100 if k == 'cp' else 10 if k == 'pair' else 1) if weighted else 1
        sev = 0                                          # weighted 时一起返回严重度：不过的一对一里被挡的头框 ×10 + 认人点像素 + 剪影占比 ×1e4（后排对自家主角：头框 ×10 + 认人点不可见率 ×1e4）
        me = {r: (s, d)}
        g = lambda x: (person(x, me[x][0]), me[x][1]) if x in me else P(x)
        n = 0
        pairs = []                                   # (后, 前)
        if slot[r] in ('ground', 'top'): pairs += [(r, c) for c in fronts_of(slot[r]) + list(CP_IDS)]
        for bk in ('ground', 'top'):
            if slot[r] in occluders(ids, bk): pairs += [(b, r) for b in ids[bk]]
        for b, f in pairs:
            j = judge_c(*g(b), *g(f))
            lo = g(b)[0].loose == f
            if not ok_cell(j, f in CP_IDS, lo):
                n += W1('cp' if f in CP_IDS else 'pair'); sev += j[2] * 10 + ((1 - j[4]) * 1e4 if lo else j[3] + j[0] * 1e4)
                if early: return n
        def tg(b, fs):
            fr = [g(x) for x in fs] + [(ppl[c], (0, 0)) for c in CP_IDS]
            lim = g(b)[0].lim
            if sum(judge_c(*g(b), *q)[0] for q in fr) <= lim: return False   # 并集 ≤ 各自最坏之和：和都不超就不用求并集
            return total(*g(b), fr)[0] > lim
        if slot[r] == 'ground': items = [(r, [f]) for f in ids['floor']] + [(t, [r, f]) for t in ids['top'] for f in ids['floor']]
        elif slot[r] == 'floor': items = [(b, [r]) for b in ids['ground']] + [(t, [b, r]) for t in ids['top'] for b in ids['ground']]
        else: items = [(r, [b, f]) for b in ids['ground'] for f in ids['floor']]
        for b, fs in items:
            if tg(b, fs):
                n += W1('pair' if len(fs) == 1 else 'tri')
                if early: return n
        return (n, sev) if weighted else n
    def inside(r, s, d): return out_of_canvas(person(r, s), d, slot[r]) == 0
    def search(r):
        best = None
        for i, s in enumerate(scales(r)):
            if best and i * 1000 >= best[0]: break
            cand = []
            for dx, dy in grid(side, data, r, slot[r]):
                cost = abs(dx) + abs(dy) + i * 1000
                if not best or cost < best[0]: cand.append((cost, dx, dy))
            for cost, dx, dy in sorted(cand):
                if best and cost >= best[0]: break
                if inside(r, s, [dx, dy]) and not fails(r, s, [dx, dy], early=True): best = (cost, s, [dx, dy]); break
        return best
    bad0 = lambda r: fails(r, *cur[r]) or not inside(r, *cur[r])
    tried, hopeless = set(), set()              # hopeless：整个范围都搜不到解的人（挪别人一般救不了他，后面不再重搜，省掉大半时间）
    for r, (s_, d_) in cur.items():
        if d_ != [0, 0]: print(f'  [{side}] {r} 起点 dx {d_[0]:+d}（start）', flush=True)
    for _ in range(40):
        todo = [r for r in movers if r not in fixed_ids and r not in hopeless and bad0(r)]
        cand = [(search(r), r) for r in todo]
        hopeless |= {r for b, r in cand if not b}
        cand = [(b, r) for b, r in cand if b and (r, b[1], tuple(b[2])) not in tried]
        if not cand: break
        (cost, s, d), r = min(cand, key=lambda q: q[0][0])
        tried.add((r, s, tuple(d))); cur[r] = (s, d)
        print(f'  [{side}] {r} → dx {d[0]:+d} dy {d[1]:+d} s {s}', flush=True)
    # 兜底：整个范围都找不到全过的人，取"受影响的组合最少"的站位（fails weighted），同分比严重度（被挡的头框 / 认人点像素），再同取挪得少的；标"无全过解"。
    # 兜底挪完的人可能挤到别人（G5 抬高压到 G11），所以兜底两遍，之后再给还不过、但有全过解的人补搜一轮
    nosol = set()
    def fallback(r):
        k0 = fails(r, *cur[r], weighted=True); best = (k0[0] + (0 if inside(r, *cur[r]) else 10 ** 6), k0[1], 0, cur[r][0], cur[r][1])
        for i, s_ in enumerate(scales(r)):
            for dx, dy in grid(side, data, r, slot[r]):
                if not inside(r, s_, [dx, dy]): continue
                n, sv = fails(r, s_, [dx, dy], weighted=True)
                k = (n, round(sv), abs(dx) + abs(dy) + i * 1000, s_, [dx, dy])
                if k[:3] < best[:3]: best = k
        cur[r] = (best[3], best[4])
        print(f'  [{side}] 兜底 {r} → dx {best[4][0]:+d} dy {best[4][1]:+d} s {best[3]}（受影响组合加权 {best[0]}，严重度 {best[1]}）', flush=True)
    for _ in range(2):
        for r in movers:
            if r in fixed_ids or not bad0(r): continue
            if r in hopeless or not search(r): nosol.add(r); fallback(r)
    for r in movers:
        if r in fixed_ids or r in nosol or not bad0(r): continue
        b = search(r)
        if b: cur[r] = (b[1], b[2]); print(f'  [{side}] 补搜 {r} → dx {b[2][0]:+d} dy {b[2][1]:+d} s {b[1]}', flush=True)
        else: nosol.add(r); fallback(r)
    out = ['\n== 建议站位（suggest，第二版判据：一对一 + 合计 + 不出画；先挪后缩，后排 s ≥ 0.8、其他 ≥ 现值 × 0.9）']
    at = {}
    for r in movers:
        a0 = data['cast'][r]['at']; s, d = cur[r]
        at[r] = [a0[0] + d[0], a0[1] + d[1], s]
        f = fails(r, s, d); o = out_of_canvas(person(r, s), d, slot[r])
        if at[r] != list(a0) or f or o:
            out.append(f'  {r}（{slot[r]}）at {a0} → {at[r]}' + (('  【无全过解，取受影响组合最少】' if f or o else '  （兜底搜出，别人挪完后全过）') if r in nosol else '') + (f'  仍有 {f} 项不过' if f else '') + (f'  仍出画 {o}' if o else ''))
    if len(out) == 1: out.append('  不用挪：全部都过')
    return '\n'.join(out), at


def grid(side, data, r, slot):
    """suggest / keep_best 的站位范围（相对本人现在的 at，文件头 suggest 说明；后排另加绝对 GROUND_Y）→ [(dx, dy)]"""
    out = []
    for dy in range(-260 if slot == 'top' else -60 if slot == 'ground' else -100, 41, 20):
        for dx in range(-200, 201, 20):
            x = data['cast'][r]['at'][0] + dx
            if slot == 'ground' and (x < 600 if side == 'buddy' else x > 360): continue
            if slot == 'ground' and not GROUND_Y[0] <= data['cast'][r]['at'][1] + dy <= GROUND_Y[1]: continue
            if slot == 'top' and (x < 560 if side == 'buddy' else x > 400): continue
            if slot == 'floor' and abs(dx) > 60: continue
            out.append((dx, dy))
    return out


def readings(ids, ppl, r, d=(0, 0)):
    """后排一人（平移 d）对自家主角的三项读数：(头框 px, 认人点最差一项可见率, 那一项, 合计最坏占比, 那一组的地板)"""
    j = judge(ppl[r], d, ppl[ppl[r].loose], (0, 0))
    tw, tf = 0.0, ''
    for f in ids['floor']:
        t_ = total(ppl[r], d, [(ppl[f], (0, 0))] + [(ppl[c], (0, 0)) for c in CP_IDS])[0]
        if t_ > tw: tw, tf = t_, f
    return j[2], j[4], j[5], tw, tf


def keep_best(side, D, r):
    """第二版第 5 / 6 条第 2 项（认人点逐项可见 ≥ 70%）在后排能站的全部位置（自己那一侧 x、脚底 y 在 GROUND_Y、20px 一档，可缩到 0.8）里能到多少：
    先要对自家主角头框 0、对另一个主角头框 0 认人点 0、不出画，再取可见率最高的；→ (at, 头框, 可见率, 那一项)"""
    data = D[side]; c = data['cast'][r]; a0 = c['at']; CPs = couple(); own, lim = back_rule(side, 'ground')
    other = next(x for x in CP_IDS if x != own)
    best = None
    for s in [a0[2]] + [round(a0[2] - 0.02 * k, 3) for k in range(1, 20) if a0[2] - 0.02 * k >= 0.8 - 1e-9]:
        p = Person(r, 'ground', '', sheet_person(c, [a0[0], a0[1], s], False, side), roll_of(c), own, lim)
        xs = range(600, W + 1, 20) if side == 'buddy' else range(0, 361, 20)
        for dx, dy in ((x - a0[0], y - a0[1]) for x in xs for y in range(GROUND_Y[0], GROUND_Y[1] + 1, 20)):
            if out_of_canvas(p, (dx, dy), 'ground'): continue
            j = judge(p, (dx, dy), CPs[own], (0, 0)); jo = judge(p, (dx, dy), CPs[other], (0, 0))
            k = (j[2] == 0 and ok_cell(jo, True, False), round(j[4], 3), -abs(dx) - abs(dy))
            if not best or k > best[0]: best = (k, [a0[0] + dx, a0[1] + dy, s], j)
    k, at, j = best
    return at, j[2], j[4], j[5]


def scene_blob(c, at):
    """fixed 场景层（trio.js drawScene）按 at 贴到屏幕上的剪影 → [Blob]"""
    out = []
    for q in c.get('parts', []):
        if not q.get('fixed'): continue
        a = q['at'] if isinstance(q['at'], list) else next(iter(q['at'].values()))
        x, y = at[0] + (a[0] - c['anchor'][0]) * at[2], at[1] + (a[1] - c['anchor'][1]) * at[2]
        out.append(render(alpha(os.path.join(WEB, q['src'])), x - q['pivot'][0] * at[2], y - q['pivot'][1] * at[2], at[2], a[2] if len(a) > 2 else 0.0, (x, y)))
    return out


def cross_section(D, built):
    """第 10 条跨边同屏：built {边: (ids, ppl)} → 文本（锚点越过中线的人 × 另一边全员；没有这样的人也写一行）"""
    other = {'buddy': 'bestie', 'bestie': 'buddy'}
    order = lambda side, r: (DEPTH[built[side][1][r].slot], side == 'bestie')          # 画的先后（小的先画）
    occ = {}                                                                           # 挡别人时的样子：人 + 自己的场景层
    def as_front(side, r):
        if (side, r) not in occ:
            p = built[side][1][r]; sc = scene_blob(D[side]['cast'][r], D[side]['cast'][r]['at'])
            occ[(side, r)] = p if not sc else Person(f'{r}+场景层', p.slot, p.kind, p.frames + [Frame('场景层', b, rect(0, 0, 1, 1), b) for b in sc], roll_of(D[side]['cast'][r]))
        return occ[(side, r)]
    def worst_total(side, r):
        """r 当后面那人：画在他前面的每个（边, 槽位）各取一人（只取跟他有交叠的；不交叠的哪一个都一样，记作空）+ 两个主角，所有组合里最坏的合计"""
        back = built[side][1][r]; CP = [(built[side][1][c], (0, 0)) for c in CP_IDS]
        slots = []
        for sd in ('buddy', 'bestie'):
            ids = built[sd][0]
            for sl in DEPTH:
                if sd == side and sl == back.slot: continue
                cand = [q for q in ids[sl] if order(sd, q) > order(side, r)]
                if not cand: continue
                hit = [(sd, q) for q in cand if ov(back.all_g, (0, 0), as_front(sd, q).all_g, (0, 0))]
                slots.append(hit + ([None] if len(hit) < len(cand) else []))
        worst = (0.0, '', ())
        for combo in itertools.product(*slots):
            fr = [x for x in combo if x]
            t_ = total(back, (0, 0), [(as_front(*x), (0, 0)) for x in fr] + CP)
            if t_[0] > worst[0]: worst = (t_[0], t_[1], tuple(q for _, q in fr))
        return worst
    out, nbad, npair = [], 0, 0
    movers = [(sd, r) for sd in ('buddy', 'bestie') for sl in built[sd][0] for r in built[sd][0][sl]
              if (D[sd]['cast'][r]['at'][0] > W / 2) == (sd == 'bestie')]
    out.append(f'\n== 跨边同屏（第 10 条：锚点越过中线的人 × 另一边全员，两组同时在场；口径同第 1 条，头框 0 / 认人点 0 / 一对一 ≤ {RATIO:.0%} / 合计 ≤ 各自上限）：'
               + ('没有锚点越过中线的人' if not movers else '、'.join(f'{r}（{sd} at {D[sd]["cast"][r]["at"]}）' for sd, r in movers)))
    for sd, r in movers:
        od = other[sd]; ids_o, ppl_o = built[od]; me = built[sd][1][r]
        out.append(f'  {r} × {"哥们" if od == "buddy" else "闺蜜"}全员（行：谁在后面 × 谁在前面；场景层算进前面那人）：')
        for sl in ('top', 'ground', 'floor'):
            cells = []
            for q in ids_o[sl]:
                if order(od, q) < order(sd, r): back, bs, front, fs_ = ppl_o[q], od, as_front(sd, r), sd
                else: back, bs, front, fs_ = me, sd, as_front(od, q), od
                j = judge(back, (0, 0), front, (0, 0)); ok = ok_cell(j); npair += 1; nbad += not ok
                cells.append(f'{back.rid}在{front.rid.split("+")[0]}后 {fmt(j)}')
            out.append(f'    {sl:>6}：' + '；'.join(cells))
        cp = built[sd][1]; j = judge(me, (0, 0), cp[OWN[od]], (0, 0))
        out.append(f'    {OWN[od]}（{r} 在他后面，认人点 0 口径）：{fmt(j, True, False)}')
        npair += 1; nbad += not ok_cell(j, True, False)
        rows = [(sd, r)] + [(od, q) for sl in ids_o for q in ids_o[sl] if order(od, q) < order(sd, r)
                            and ov(ppl_o[q].all_g, (0, 0), as_front(sd, r).all_g, (0, 0))]
        for bsd, br in rows:
            w = worst_total(bsd, br); lim = built[bsd][1][br].lim; nbad += w[0] > lim
            out.append(f'    合计 {br} 当后面那人（两组六人 + 主角里画在他前面的）：最坏 {w[0]:.1%}（帧 {w[1] or "-"}，前面 {"、".join(w[2]) or "只有主角"}）/ 上限 {lim:.0%}{" ✗" if w[0] > lim else ""}')
    out.append(f'  跨边结论：{npair} 对 + 合计，不过 {nbad}')
    return '\n'.join(out)


def rescan(side, D, at):
    """按建议站位重贴每人全部在场帧，一对一 + 合计 + 出画全部复核"""
    ids, ppl = build(side, D, at)
    n, badp, ng, badg = check_all(ids, ppl)
    oc = [r for sl in ids for r in ids[sl] if out_of_canvas(ppl[r], (0, 0), sl)]
    ks = [at[r][2] for r in ids['ground'] if r in at]
    return n, badp, ng, badg, oc, min(ks) if ks else None


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    only = next((a[7:].split(',') for a in sys.argv[1:] if a.startswith('--only=')), None)   # --only=B1,B2：建议站位只挪这几个人（别人只当约束）
    start = {k: int(v) for k, v in (q.split(':') for a in sys.argv[1:] if a.startswith('--start=') for q in a[8:].split(','))}   # --start=B6:820,B7:820
    which = args[0] if args else 'all'
    D = load_data()
    for side in (['buddy', 'bestie'] if which == 'all' else [which]):
        txt, ids, ppl = scan(side, D)
        print(txt, flush=True)
        if '--nosuggest' in sys.argv: print(cross_section(D, {sd: build(sd, D) for sd in ('buddy', 'bestie')})); continue
        sg, at = suggest(side, D, ids, ppl, fixed_ids=[r for r in ppl if only and r not in only], start=start)
        n, badp, ng, badg, oc, kmin = rescan(side, D, at)
        if ids['ground']:
            ids2, ppl2 = build(side, D, at); lim = back_rule(side, 'ground')[1]
            sg += (f'\n\n== {"哥们" if side == "buddy" else "闺蜜"}后排对{OWN[side]}三项读数（按建议站位；判据 头框 0 / 认人点逐项可见 ≥ {KEEP:.0%} / 合计 ≤ {lim:.0%}，合计取 10 个地板同伴里最坏的一组）')
            for r in ids2['ground']:
                h, kp, kw, tw, tf = readings(ids2, ppl2, r)
                sg += (f'\n  {r} at {at[r]}：头框 {h} px{"" if h == 0 else " ✗"}；认人点最差一项可见 {kp:.1%}（{kw or "-"}）{"" if kp >= KEEP else " ✗"}；'
                       f'合计最坏 {tw:.1%}（地板 {tf or "-"}）{"" if tw <= lim else " ✗"}')
            nk = [(r, keep_best(side, D, r)) for r in ids2['ground']]
            nk = [(r, q) for r, q in nk if q[2] < KEEP or q[1]]
            sg += f'\n\n== 在整个站位范围里都过不了认人点 ≥ {KEEP:.0%} 或头框 0 的人（后排能站的全部位置：x {"600~960" if side == "buddy" else "0~360"}、脚底 y {GROUND_Y[0]}~{GROUND_Y[1]}、20px 一档、可缩到 s 0.8、不出画）：' + ('无' if not nk else '')
            for r, (a_, h, kp, kw) in nk:
                sg += f'\n  {r}：最好的位置 at {a_}，头框 {h} px，认人点最差一项可见 {kp:.1%}（{kw}）'

        sg += (f'\n\n== 按建议站位复扫（重贴每人全部在场帧）：一对一 {n} 对不过 {len(badp)}；合计 {ng} 组不过 {len(badg)}；出画 {len(oc)} 人；后排最小 s {kmin}' +
               ''.join(f'\n  ✗ {r} 在 {c} 后面：{fmt(j, c in CP_IDS, back_rule(side, SLOT.get(D[side]["cast"][r].get("depth")))[0] == c)}（最坏帧 {j[1]}' + (f'；最差一项 {j[5]}' if j[5] else '') + '）' for r, c, j in badp) +
               ''.join(f'\n  ✗ 合计 {r}（组 {g}）{t_[0]:.1%}' for r, g, t_ in badg[:30]) + ''.join(f'\n  ✗ 出画 {r}' for r in oc) +
               '\n' + exempt_line(*build(side, D, at)))
        sg += '\n' + cross_section(D, {sd: build(sd, D) for sd in ('buddy', 'bestie')})
        p = os.path.join(ROOT, 'shots/trio_std', f'组合遮挡矩阵_{side}.txt')
        open(p, 'w').write(txt + '\n' + sg + '\n'); print(sg)
