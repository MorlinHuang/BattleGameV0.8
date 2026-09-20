"""抱枕（档 2，查岗党）—— 圆角方枕 + 缝线 + 两点兔耳。

照搬 ammo.js ITEM.pillow：2r × 1.68r 的圆角方（圆角 0.4r）、内缩一圈缝线、
两枚竖椭圆当兔耳。

五条形状结论（第二条、第三条是第一轮渲出来才发现的）：

- **直边要凹、四角要鼓。** 填充物把角撑出去，直边就被拽得凹进来 —— 这条凹弧是
  "软"的全部来源。但第一轮给到 0.052/0.060 渲出来是个四角星，一眼读不出抱枕；
  现在压到 0.020/0.024，凹得出来又不喧宾夺主。
- **不许给四角单独加厚。** 第一轮试过"角上的经线厚 20%"，结果圆角和直边的交界
  变成一道折痕，Freestyle 在掠射角上把它当可见轮廓描了出来 —— 正面那八条从中心
  放射出去的黑线就是它。软硬过渡只能靠外轮廓形状和经线指数，不能靠局部加厚：
  **任何 C0 不连续的地方都会长出一条描边。**
- **正面要平，中心再微微塌一点。** 经线用超椭圆（指数 3.4）而不是圆：从边缘滚上来
  以后很快接近满厚度，中间一大片是平的；正中再压 7% 做出"被压过"的窝。
  纯半圆经线就是个气球，那是塑料感的来源。
- **转轴必须是 Y（绕观察轴自转），不能是 X（翻面）。** 判据 3 是按整条转盘判的，
  不是按最好那几帧判的：礼物飞过来 0.65 秒要转 1.45 圈，一半帧认不出就是不合格。
  按实际绘制尺寸铺到客厅米色底上数了一遍 —— 绕 X 8 帧里有 2 帧转到侧沿，只剩一块肥皂，6/8；绕 Y 8/8。
  花束绕 X 翻面好用是因为它各向同性，转到哪一面都是花；抱枕虽然两面
  一样（缝线兔耳是对称贴在两面上的），但它是扁的，转到侧沿那两帧照样没题材。
  axis='Y' 时相机沿 +Y 看，世界 Y 就是相机轴，所以 Ry(θ) 是**画面内自转**：
  姿态不变、题材永远认得出，而光源仍然钉在世界坐标里不跟着转 —— 后面这半句
  才是换 3D 真正买到的东西（矢量版 ctx.rotate 会把光影一起转走）。
  厚度靠固定的 tilt/roll 给一点 3/4 角就够，不值得拿一半可读帧去换。
  注意 tilt/roll 是按 e[(idx+1)%3] / e[(idx+2)%3] 挂上去的，跟着 axis 滚：
  axis='Y' 时 tilt 变成绕屏幕竖轴的偏航、roll 变成物体自身的俯仰，
  数值跟 axis='X' 的那套不通用，是照着出图重调的。
- **缝线和兔耳全部用材质分区，不做凸起几何。** 凸起会被 Freestyle 描一圈黑边，
  观众端 150px 上缝线自带黑框就是一圈脏线。同一块网格换材质不产生任何描边。
- 主体保持粉白、可见度靠外轮廓那 2.6px 描边撑住。素材色 #f6cfe0 比矢量版的
  #fdf2f6 深一档是**为了渲出来一样**：公共灯光往每个通道加一大份白，
  #fdf2f6 实测渲成 (222,220,221) 的中性灰，粉味被洗干净了。

跑：blender -b --python pillow.py -- 36 224 128 <out> 1
    pack_atlas.py <帧目录> pillow_atlas.webp --cell 160

    渲染边长 224 = 单格 160 / 并集占比 0.714。common.py 说描边宽度是
    "最终像素的绝对值"，要真做到，得让 pack_atlas 不缩放 —— 也就是
    **并集边长正好等于单格**，反推出渲染边长 = 单格 / 并集占比。
    并集占比是先渲一轮量出来的（它跟分辨率无关，只跟形状和描边有关）。
    ss 一律留 1。common.py 的 `_freestyle(ss)` 把 ss 同时乘进了
    `render.line_thickness` 和 `linestyle.thickness`，而这两个值在 ABSOLUTE 模式下
    是**相乘**的，所以描边宽度按 ss² 长：实测同一场景 ss=1/2/3 描边 4 / 14 / 30 像素。
    ss=3 时那 30px 是绝对像素、不随渲染边长缩，发卡的棒才 0.55 单位宽，
    整根被描边吞成一条纯墨色的胶囊。common.py 不许改，所以超采样这条路直接不走：
    Cycles 每像素 128 个采样本身就带足了抗锯齿，锯齿并不是实际问题。
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import bpy

A, C, RAD = 1.00, 0.84, 0.42   # 半宽 / 半高 / 圆角，比例照搬矢量版 1 : 0.84
THICK     = 0.34               # 半厚。翻到侧面剪影仍有 2.0 × 0.68，不会薄成一条
N, M      = 128, 30            # 轮廓点数 / 单面经线环数（兔耳要这个密度才不是锯齿块）
PINCH_X, PINCH_Z = 0.020, 0.024
SEAM_LO, SEAM_HI = 0.755, 0.825   # 缝线落在轮廓的 ~79%，对上矢量版内缩的那一圈
EAR_X, EAR_Z, EAR_RX, EAR_RZ = 0.26, 0.16, 0.135, 0.30

init()
mat('body', '#f6cfe0')
seam_m = mat('seam', '#ff86b4')
ear_m  = mat('ear',  '#ff8ab8')


def _resample(pts, n, closed):
    d = [0.0]
    for i in range(1, len(pts)):
        d.append(d[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    out, j = [], 0
    for k in range(n if closed else n + 1):
        tg = d[-1] * k / n
        while j < len(d) - 2 and d[j + 1] < tg:
            j += 1
        seg = d[j + 1] - d[j]
        u = 0.0 if seg < 1e-12 else (tg - d[j]) / seg
        a, b = pts[j], pts[j + 1]
        out.append(tuple(a[m] + (b[m] - a[m]) * u for m in range(len(a))))
    return out


def rrect(a, c, rad, n, px, pz):
    """等弧长采样的圆角矩形轮廓（XZ 平面）。直边中点往里压 px/pz。"""
    ax, cz, K, d = a - rad, c - rad, 24, []

    def arc(cx, cy, a0):
        for k in range(K + 1):
            t = a0 + k / K * math.pi / 2
            d.append((cx + rad * math.cos(t), cy + rad * math.sin(t)))

    def edge(p0, p1, ax_, amt):
        for k in range(K + 1):
            s = k / K
            x = p0[0] + (p1[0] - p0[0]) * s
            z = p0[1] + (p1[1] - p0[1]) * s
            dd = amt * math.sin(math.pi * s)
            if ax_ == 'x':
                x -= math.copysign(dd, x)
            else:
                z -= math.copysign(dd, z)
            d.append((x, z))

    edge((a, -cz), (a, cz), 'x', px);   arc(ax, cz, 0.0)
    edge((ax, c), (-ax, c), 'z', pz);   arc(-ax, cz, math.pi / 2)
    edge((-a, cz), (-a, -cz), 'x', px); arc(-ax, -cz, math.pi)
    edge((-ax, -c), (ax, -c), 'z', pz); arc(ax, -cz, 3 * math.pi / 2)
    d.append(d[0])
    return _resample(d, n, True)


def meridian(m, ea, eb, t, ref):
    """赤道 (s=1, y=0) 到极点 (s=0, y=1) 的超椭圆经线，按**弧长**均分成 m 段。
       按参数均分会让赤道那一圈只剩一两个面，边缘就滚不起来。"""
    fine, p = 600, []
    for i in range(fine + 1):
        u = i / fine * math.pi / 2
        p.append((math.cos(u) ** ea * ref, math.sin(u) ** eb * t))
    out = _resample(p, m, False)
    out[0], out[-1] = (ref, 0.0), (0.0, t)
    return [(x / ref, y / t) for x, y in out]


OUT = rrect(A, C, RAD, N, PINCH_X, PINCH_Z)
MER = meridian(M, 0.833, 0.588, THICK, A)     # 指数 2.4 / 3.4：方一点、正面平一点


def dimple(s):
    """正中压 7%：抱枕不是气球，中间总有个被压过的窝。"""
    return 1.0 - 0.07 * math.exp(-(s / 0.42) ** 2)


def P(x, y, z):
    """绕 Y 转 -90°：建模时的长边 X 变成 object-Z，转盘才转得起来（见开头第三条）。"""
    return (-z, y, x)


verts = [P(x, 0.0, z) for x, z in OUT]         # 赤道，两面共用
ring = {}
for sgn in (1, -1):
    for k in range(1, M):
        s, y = MER[k]
        ring[(sgn, k)] = len(verts)
        for x, z in OUT:
            verts.append(P(s * x, sgn * y * THICK * dimple(s), s * z))
    ring[(sgn, M)] = len(verts)
    verts.append(P(0.0, sgn * THICK * dimple(0.0), 0.0))


def vid(sgn, k, i):
    return i % N if k == 0 else ring[(sgn, k)] + (i % N if k < M else 0)


def face_mat(k, i):
    """面心的正面坐标 → 兔耳 / 缝线 / 本体，全是同一块网格上的材质分区。"""
    s = (MER[k][0] + MER[k + 1][0]) / 2
    ox = (OUT[i % N][0] + OUT[(i + 1) % N][0]) / 2 * s
    oz = (OUT[i % N][1] + OUT[(i + 1) % N][1]) / 2 * s
    for sx in (-1, 1):
        if ((ox - sx * EAR_X) / EAR_RX) ** 2 + ((oz - EAR_Z) / EAR_RZ) ** 2 < 1.0:
            return 2
    return 1 if SEAM_LO <= s <= SEAM_HI else 0


faces, fmat = [], []
for sgn in (1, -1):
    for k in range(M):
        for i in range(N):
            a, b = vid(sgn, k, i), vid(sgn, k, i + 1)
            c, d = vid(sgn, k + 1, i + 1), vid(sgn, k + 1, i)
            if k == M - 1:                       # 极点退化成一个顶点
                faces.append((a, d, b) if sgn > 0 else (a, b, d))
            else:
                faces.append((a, d, c, b) if sgn > 0 else (a, b, c, d))
            fmat.append(face_mat(k, i))

ob = add_mesh('pillow', verts, faces, 'body')
ob.data.materials.append(seam_m)
ob.data.materials.append(ear_m)
for p, m in zip(ob.data.polygons, fmat):
    p.material_index = m

render_turntable('pillow', active=ob, axis='Y', tilt=0.40, roll=0.24)
