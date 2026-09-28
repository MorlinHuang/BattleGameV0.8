"""白娘子的海（2026-09-28 第二版）：3D 渲 2D 的循环海面序列帧。
用户："当前的水流和海面美术风格实在是太 Q 了，需要更写实，参考之前的花束等礼物，做出类似 3 渲 2 的体积感"。
第一版是 sea.js 在 canvas 上现画的四条正弦色带 + 白线，平的。

这里在 Blender 里搭一片真的有起伏的海：
  · 波：几列 Gerstner 波叠加（浪尖尖、浪谷平，水平方向往浪尖挤 —— 真海浪的形），**每列在 LOOP 秒里正好走整数个周期**，
    所以第 FRAMES 帧 = 第 0 帧，循环无缝；
  · 画风跟八件礼物一套（tools/3d/common.py）：Toon BSDF 硬边二分光 + 一道 Toon 高光 + Freestyle 描边（线色换成深海蓝，暖黑在水上发脏）；
  · 浪尖白沫：顶点按"比平均水面高出多少 + 被挤得多密"算一个 foam 值写进颜色属性，材质里拿它混白；
  · 远近：远处浅青、近处深蓝（按 Y 写进另一个属性）。
**分三层渲**（BANDS）：同一片海按离镜头远近切成三条（远 / 中 / 近），每条单独出一套帧（别的条不渲）。
引擎按 远 → 第一排虾兵蟹将 → 中 → 第二排 → 近 叠起来：兵的下半截被它前面那条海盖住，才是泡在水里（画在整片海上面的话像站在水面上）。

跑法（桌面）：blender -b --python sea.py -- <帧数> <采样> <输出目录> [起始帧 步长 [test]]
输出：<目录>/<条名>_<帧>.png，960 宽（= 画布宽，贴图 1:1 上屏），高度按 CROP 定；打包见 pack_sea.py。
"""
import bpy, bmesh, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import srgb, _ink_thickness

A = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FRAMES = int(A[0]) if len(A) > 0 else 36
SAMP = int(A[1]) if len(A) > 1 else 16    # 不走光照，采样只管抗锯齿
OUT = A[2] if len(A) > 2 else '/tmp/sea'
START = int(A[3]) if len(A) > 3 else 0         # 从第几帧起、隔几帧渲一张：几个进程并行分着渲（桌面 8 核）
STEP = int(A[4]) if len(A) > 4 else 1
TEST = len(A) > 5 and A[5] == 'test'            # 试渲：只渲 START 这一帧，并多出一张三条合在一起的 all_<帧>.png

LOOP = 3.0                  # 循环一圈几秒（引擎按这个速度播）
W, H = 960, 520             # 渲染画幅（像素）：宽 = 画布宽；引擎把第 0 行摆在屏幕 y ≈ 1190（海平线上的浪尖顶到两人脚下）
SEA_X = (-15.0, 15.0)       # 海的横向范围（世界单位）：最远处画面宽 ~30，两边都伸出画面
SEA_Y = (1.2, 28.0)         # 纵深：近边 1.2（画面下沿以外；2.0 时近处浪谷里露出海的近边）→ 远边 28（画面顶上那条海平线）
NX, NY = 330, 150           # 网格细分；纵向按距离指数分布（近处一格在屏幕上大，要密）
# 镜头：站在齐腰高处平着往前看（俯角 10°）—— 一排排浪头在画面上半截前后叠起来（有纵深、浪头多）。
# 第一版俯角 24°：画面下半截被最近的一道大浪占满，而直播画面下半截压着礼物面板（屏幕 y 1373 以下），露出来的只剩远处一条细浪。
CAM_H, CAM_PITCH, LENS, SHIFT_Y = 2.0, 10.0, 30.0, -0.14
BANDS = [('far', 9.0, 28.0), ('mid', 5.0, 9.0), ('near', 1.2, 5.0)]   # 三条：[名, 近边 y, 远边 y]
INK = '173a78'              # 描边：深海蓝
OUTLINE_W = 2.8             # 屏幕描边像素（同八件礼物）；渲染画幅 = 屏幕像素，不用换算

# 波：[方向（度，0 = 往右，-90 = 朝镜头涌来）, 波长, 振幅, 陡度 Q（0~1，越大浪尖越尖）, 一个循环里走几个周期]
WAVES = [
    (-90, 4.2, 0.55, 0.45, 2),   # 主浪：一排排朝镜头涌过来
    (-62, 2.7, 0.24, 0.32, 3),   # 斜着的两列：把主浪的长条浪脊打碎成一块块浪头
    (-122, 2.1, 0.17, 0.28, 3),
    (-10, 1.3, 0.06, 0.2, 4),    # 横着的碎波：浪身上的小褶子（Freestyle 在这些褶子上出细线 = 内部结构）
    (-150, 0.9, 0.04, 0.2, 5),
]
AMP = sum(w[2] for w in WAVES)
# 各列陡度合起来 Σ Q·A·k 必须 < 1，否则浪尖处网格翻折（第一版 1.22：浪前坡上一条条竖的碎面，被渲成白条）
assert sum(q * a * 2 * math.pi / L for _, L, a, q, _ in WAVES) < 0.95


def gerstner(x, y, t):
    """返回 (dx, dy, dz, 压缩量)。压缩量 = 水平位移场的散度取负（浪尖处被挤得最密，拿来出白沫）。"""
    dx = dy = dz = 0.0
    comp = 0.0
    for ang, L, a, q, n in WAVES:
        k = 2 * math.pi / L
        w = 2 * math.pi * n / LOOP
        ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        ph = k * (ux * x + uy * y) - w * t
        c, s = math.cos(ph), math.sin(ph)
        dx += q * a * ux * c
        dy += q * a * uy * c
        dz += a * s
        comp += q * a * k * s        # Gerstner 的 Jacobian：1 − Σ Q·A·k·sin
    return dx, dy, dz, comp


LIGHT = (-0.35, -0.55, 0.76)   # 光从哪来（世界方向，指向光源）：左上、镜头这一侧 —— 朝镜头的浪面是亮面
TONES = [(0.0, 0.62), (0.28, 0.8), (0.6, 1.0), (0.86, 1.22)]   # 硬切四档明暗：N·L 过了第一个数 → 亮度取第二个数；最亮一档（>1）是正对光的亮面
# 没有 N·H 高光：按每个像素的视线方向算，透视下在陡的浪前坡上拖成一条条竖白条（试过阈值 0.985 / 0.996 都有），最亮那档亮面顶替它


def material():
    """自己算光的自发光材质（不走 Cycles 的光照）。
    第一版照 common.mat 用 Toon BSDF + 太阳 + 环境补光：环境光在暗面全是采样噪点、Toon 高光把均匀的环境也反射进来蒙一层灰，
    太阳一放到对面整片海就黑了。这里明暗、高光都在材质节点里用法线现算，结果确定、没有噪点，出来就是硬边赛璐璐：
      亮度 = TONES 三档（按 N·L 硬切）；颜色 = 远近渐变（depth）混白沫（foam，硬边）。"""
    m = bpy.data.materials.new('sea')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    L = nt.links.new
    out = N('ShaderNodeOutputMaterial')
    geo = N('ShaderNodeNewGeometry')
    lv = N('ShaderNodeCombineXYZ')
    n = math.sqrt(sum(c * c for c in LIGHT))
    for i, c in enumerate(LIGHT): lv.inputs[i].default_value = c / n
    # 明暗三档
    dl = N('ShaderNodeVectorMath'); dl.operation = 'DOT_PRODUCT'
    L(geo.outputs['Normal'], dl.inputs[0]); L(lv.outputs[0], dl.inputs[1])
    tone = N('ShaderNodeValToRGB'); tone.color_ramp.interpolation = 'CONSTANT'
    el = tone.color_ramp.elements
    while len(el) < len(TONES): el.new(0.5)
    for e, (pos, v) in zip(el, TONES): e.position = pos; e.color = (v, v, v, 1)
    L(dl.outputs['Value'], tone.inputs['Fac'])
    # 底色：远近 + 白沫
    foam = N('ShaderNodeAttribute'); foam.attribute_name = 'foam'
    depth = N('ShaderNodeAttribute'); depth.attribute_name = 'depth'
    ramp = N('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = srgb('1a56b0')
    ramp.color_ramp.elements[1].color = srgb('62bdf0')
    L(depth.outputs['Fac'], ramp.inputs['Fac'])
    fr = N('ShaderNodeValToRGB'); fr.color_ramp.interpolation = 'CONSTANT'
    fr.color_ramp.elements[0].color = (0, 0, 0, 1); fr.color_ramp.elements[1].position = 0.5
    # 白沫 = 浪尖区域（foam，顶点算的，平滑）× 噪声纹理：浪尖上一片碎花边，不是整块白。
    # 噪声按顶点的**原始**位置（base 属性）取 —— 花纹钉在网格上，浪峰扫过哪里哪里翻白，跟着浪走不闪。
    # 第一版直接拿 foam 硬切：浪尖那一整块变白，顺着浪的前坡往下挂成一条条白"鼻涕"。
    bs = N('ShaderNodeAttribute'); bs.attribute_name = 'base'
    nz = N('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.2; nz.inputs['Detail'].default_value = 3.0
    nz.inputs['Roughness'].default_value = 0.6
    L(bs.outputs['Vector'], nz.inputs['Vector'])
    fm = N('ShaderNodeMath'); fm.operation = 'MULTIPLY'
    # 噪声先拉对比度（0.42 以下归零、往上 3.5 倍）再乘浪尖：浪尖上一片片分开的白沫；直接乘（第一版 ×1.9）整个浪尖全白成一块
    nc = N('ShaderNodeMapRange'); nc.inputs['From Min'].default_value = 0.41; nc.inputs['From Max'].default_value = 0.7
    L(nz.outputs['Fac'], nc.inputs['Value'])
    L(foam.outputs['Fac'], fm.inputs[0]); L(nc.outputs['Result'], fm.inputs[1])
    L(fm.outputs[0], fr.inputs['Fac'])
    mix = N('ShaderNodeMix'); mix.data_type = 'RGBA'
    L(fr.outputs['Color'], mix.inputs['Factor']); L(ramp.outputs['Color'], mix.inputs[6])
    mix.inputs[7].default_value = srgb('eef8ff')
    lit = N('ShaderNodeMix'); lit.data_type = 'RGBA'; lit.blend_type = 'MULTIPLY'
    lit.inputs['Factor'].default_value = 1.0
    L(mix.outputs[2], lit.inputs[6]); L(tone.outputs['Color'], lit.inputs[7])
    em = N('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0
    L(lit.outputs[2], em.inputs['Color'])
    L(em.outputs[0], out.inputs['Surface'])
    return m


def build_band(name, y0, y1, m):
    """一条海：规则网格，顶点每帧由 animate 重算。"""
    nx, ny = NX, max(2, round(NY * math.log(y1 / y0) / math.log(SEA_Y[1] / SEA_Y[0])))
    me = bpy.data.meshes.new(name)
    ys = [y0 * (y1 / y0) ** (j / ny) for j in range(ny + 1)]    # 按距离指数分布：每行在屏幕上差不多一样高
    vs = [(SEA_X[0] + (SEA_X[1] - SEA_X[0]) * i / nx, ys[j], 0) for j in range(ny + 1) for i in range(nx + 1)]
    fs = [(j * (nx + 1) + i, j * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i + 1, (j + 1) * (nx + 1) + i) for j in range(ny) for i in range(nx)]
    me.from_pydata(vs, [], fs)
    me.color_attributes.new('foam', 'FLOAT_COLOR', 'POINT')
    me.color_attributes.new('depth', 'FLOAT_COLOR', 'POINT')
    ba = me.color_attributes.new('base', 'FLOAT_COLOR', 'POINT')   # 原始位置（白沫花纹的噪声坐标），不随浪变
    for i, v in enumerate(vs): ba.data[i].color = (v[0], v[1], 0, 1)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True          # 海面要平滑法线（Toon 的明暗交界才是一条顺的线；平面着色是一格格马赛克）
    ob['base'] = [c for v in vs for c in v[:2]]
    return ob


def animate(ob, t):
    me = ob.data
    base = ob['base']
    foam = me.color_attributes['foam'].data
    depth = me.color_attributes['depth'].data
    for i, v in enumerate(me.vertices):
        x, y = base[2 * i], base[2 * i + 1]
        dx, dy, dz, comp = gerstner(x, y, t)
        v.co = (x + dx, y + dy, dz)
        # 浪尖区域：高出平均水面 28% 总振幅起渐强（材质里再乘噪声出碎白沫）
        f = max(0.0, min(1.0, (dz / AMP - 0.22) / 0.25))
        foam[i].color = (f, f, f, 1)
        d = math.log(y / SEA_Y[0]) / math.log(SEA_Y[1] / SEA_Y[0])
        depth[i].color = (d, d, d, 1)
    me.update()


def scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    r = sc.render
    r.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMP; sc.cycles.use_denoising = False
    r.resolution_x, r.resolution_y = W, H
    r.film_transparent = True
    r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'
    # 不用灯：明暗在材质里算（material()）。色彩管理用 Standard：自发光颜色 = 贴图颜色（默认 AgX 会把饱和蓝压灰）
    sc.view_settings.view_transform = 'Standard'
    # 相机：透视（远处的浪小、近处的大 —— 这就是纵深），参数见 CAM_*
    cam = bpy.data.cameras.new('cam'); cam.lens = LENS; cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36; cam.shift_y = SHIFT_Y
    cam.clip_end = 200
    co = bpy.data.objects.new('cam', cam)
    co.location = (0, 0, CAM_H); co.rotation_euler = (math.radians(90 - CAM_PITCH), 0, 0)
    sc.collection.objects.link(co); sc.camera = co
    # 描边：一档 silhouette（common._freestyle 同款），线色深海蓝
    r.use_freestyle = True; r.line_thickness_mode = 'ABSOLUTE'; r.line_thickness = 1.0
    vl = sc.view_layers[0]; vl.use_freestyle = True
    fs = vl.freestyle_settings
    while fs.linesets: fs.linesets.remove(fs.linesets[0])
    ls = fs.linesets.new('Ink')
    if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new('Ink')
    for a in ('select_silhouette', 'select_border', 'select_crease', 'select_edge_mark', 'select_contour', 'select_external_contour'):
        setattr(ls, a, False)
    ls.select_silhouette = True
    ls.linestyle.color = srgb(INK)[:3]
    ls.linestyle.thickness = _ink_thickness(OUTLINE_W)


scene()
m = material()
bands = [build_band(n, y0, y1, m) for n, y0, y1 in BANDS]
os.makedirs(OUT, exist_ok=True)
for f in [START] if TEST else range(START, FRAMES, STEP):
    t = LOOP * f / FRAMES
    for b in bands: animate(b, t)
    for b in bands:
        for o in bands: o.hide_render = o is not b      # 一条一条单独渲
        bpy.context.scene.render.filepath = os.path.join(OUT, '%s_%03d' % (b.name, f))
        bpy.ops.render.render(write_still=True)
    if TEST:                                            # 试渲：再出一张三条合在一起的，看整体
        for o in bands: o.hide_render = False
        bpy.context.scene.render.filepath = os.path.join(OUT, 'all_%03d' % f)
        bpy.ops.render.render(write_still=True)
    print('SEA frame', f, flush=True)
print('SEA_DONE', flush=True)
