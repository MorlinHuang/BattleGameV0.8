"""水的 3 渲 2 公共件（2026-09-28）：白娘子的掌心水柱（jet.py）、水花（splash.py）共用。

跟八件礼物（tools/3d/common.py）同一套画风 —— 硬边分档明暗 + Freestyle 描边，但**不走 Cycles 的光照**：
明暗在材质里用法线现算（N·L 按 TONES 硬切几档），用自发光输出。试过 common.mat 的 Toon BSDF + 太阳 + 环境补光：
水的大片暗面全是环境光采样噪点，Toon 高光把均匀环境反射成一层灰（已删的海面 sea.py 头两版试渲）。
颜色：base 属性（0~1）按 ramp 取色（水柱：出口白 → 越往前越蓝），foam 属性（0~1）> 0.5 的地方硬边白。
描边线色深海蓝（暖黑在水上发脏），宽度按屏幕像素给。
"""
import bpy, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import srgb, _ink_thickness

INK = '173a78'


def args(defaults):
    """命令行：blender -b --python x.py -- <帧数> <采样> <输出目录> [起始帧 步长]"""
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    frames = int(a[0]) if len(a) > 0 else defaults[0]
    samp = int(a[1]) if len(a) > 1 else 16
    out = a[2] if len(a) > 2 else defaults[1]
    start = int(a[3]) if len(a) > 3 else 0
    step = int(a[4]) if len(a) > 4 else 1
    return frames, samp, out, start, step


def setup(W, H, samp, outline_px):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    r = sc.render
    r.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samp; sc.cycles.use_denoising = False
    r.resolution_x, r.resolution_y = W, H
    r.film_transparent = True
    r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'Standard'     # 自发光颜色 = 贴图颜色（默认 AgX 会把饱和蓝压灰）
    r.use_freestyle = True; r.line_thickness_mode = 'ABSOLUTE'; r.line_thickness = 1.0
    vl = sc.view_layers[0]; vl.use_freestyle = True
    fs = vl.freestyle_settings
    while fs.linesets: fs.linesets.remove(fs.linesets[0])
    ls = fs.linesets.new('Ink')
    if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new('Ink')
    for a in ('select_silhouette', 'select_border', 'select_crease', 'select_edge_mark', 'select_contour', 'select_external_contour'):
        setattr(ls, a, False)
    ls.select_silhouette = True                       # 一档，理由见 common._freestyle
    ls.linestyle.color = srgb(INK)[:3]
    ls.linestyle.thickness = _ink_thickness(outline_px)
    return sc


def ortho_camera(scale, loc=(0, -10, 0)):
    """正交、沿 +Y 看（屏幕右 = 世界 +X，屏幕上 = 世界 +Z）。scale = 画面宽对应多少世界单位。"""
    sc = bpy.context.scene
    cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = scale
    co = bpy.data.objects.new('cam', cam); co.location = loc; co.rotation_euler = (math.radians(90), 0, 0)
    sc.collection.objects.link(co); sc.camera = co


def material(name, colors, tones, light, foam_color='f4fbff'):
    """colors：base 属性 0 → 1 对应的颜色（sRGB 十六进制，均匀分布在 ramp 上）；tones：[(N·L 门槛, 亮度)]；light：指向光源的方向。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N('ShaderNodeOutputMaterial')
    geo = N('ShaderNodeNewGeometry')
    lv = N('ShaderNodeCombineXYZ')
    n = math.sqrt(sum(c * c for c in light))
    for i, c in enumerate(light): lv.inputs[i].default_value = c / n
    dl = N('ShaderNodeVectorMath'); dl.operation = 'DOT_PRODUCT'
    L(geo.outputs['Normal'], dl.inputs[0]); L(lv.outputs[0], dl.inputs[1])
    tone = N('ShaderNodeValToRGB'); tone.color_ramp.interpolation = 'CONSTANT'
    el = tone.color_ramp.elements
    while len(el) < len(tones): el.new(0.5)
    for e, (pos, v) in zip(el, tones): e.position = pos; e.color = (v, v, v, 1)
    L(dl.outputs['Value'], tone.inputs['Fac'])
    base = N('ShaderNodeAttribute'); base.attribute_name = 'base'
    ramp = N('ShaderNodeValToRGB')
    el = ramp.color_ramp.elements
    while len(el) < len(colors): el.new(0.5)
    for i, (e, c) in enumerate(zip(el, colors)): e.position = i / (len(colors) - 1); e.color = srgb(c)
    L(base.outputs['Fac'], ramp.inputs['Fac'])
    foam = N('ShaderNodeAttribute'); foam.attribute_name = 'foam'
    fr = N('ShaderNodeMath'); fr.operation = 'GREATER_THAN'; fr.inputs[1].default_value = 0.5   # 白沫硬边
    L(foam.outputs['Fac'], fr.inputs[0])
    mix = N('ShaderNodeMix'); mix.data_type = 'RGBA'
    L(fr.outputs[0], mix.inputs['Factor']); L(ramp.outputs['Color'], mix.inputs[6]); mix.inputs[7].default_value = srgb(foam_color)
    lit = N('ShaderNodeMix'); lit.data_type = 'RGBA'; lit.blend_type = 'MULTIPLY'; lit.inputs['Factor'].default_value = 1.0
    L(mix.outputs[2], lit.inputs[6]); L(tone.outputs['Color'], lit.inputs[7])
    em = N('ShaderNodeEmission'); L(lit.outputs[2], em.inputs['Color'])
    L(em.outputs[0], out.inputs['Surface'])
    return m


def mesh(name, verts, faces, m, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for a in ('base', 'foam'): me.color_attributes.new(a, 'FLOAT_COLOR', 'POINT')
    me.materials.append(m)
    for p in me.polygons: p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def set_attr(ob, name, vals):
    d = ob.data.color_attributes[name].data
    for i, v in enumerate(vals): d[i].color = (v, v, v, 1)


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
