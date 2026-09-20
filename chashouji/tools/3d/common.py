"""《查手机》3D 物品转盘的公共框架 —— 所有物品脚本 import 它。

这套参数是玫瑰花束试点调出来的（见 docs/3D方案评估.md 第六节），**不要逐件重调**：
八件物品共用同一套灯光、同一套描边、同一个正交相机，它们才会看着像一套东西。
物品脚本只负责建模，风格全由这里决定。

用法（物品脚本）：

    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from common import *

    init()                              # 清场 + 材质
    mat('body', '#e63a62')              # 这件物品要用的颜色，先声明再用
    ob = add_mesh('box', verts, faces, 'body')
    ...
    render_turntable('ringbox', [ob, ...])

跑法：

    blender -b --python tools/3d/ringbox.py -- <帧数> <边长> <采样> <输出前缀> [超采样]

## 两条尺寸约定（破了它引擎侧就对不上）

1. **主体直径做成 2.0 个 Blender 单位**，相机 ortho_scale 固定 3.3。
   `pack_atlas.py` 靠这两个数反算 ammo.js 里的 `scale` 字段，自己改相机就对不上了。
2. **描边宽度是最终像素的绝对值**，所以渲染要超采样时描边必须同倍放大，
   否则下采样完描边就细了 —— 不同物品描边不一样粗，一眼就能看出不是一套。
"""
import bpy, math, sys, os
from mathutils import Vector, Matrix

# ---------- 全局常量：八件共用，改一处等于改全套风格 ----------
ORTHO      = 3.3       # 相机正交宽度。主体 2.0 单位 → 占画幅 60.6%
INK        = '3a2c26'  # 描边色，取角色线稿那个暖黑
OUTLINE_W  = 2.6       # 外轮廓线宽（最终像素）。它决定这东西在明亮底图上认不认得出
INNER_W    = 1.1       # 内部结构线宽。粗了内部叠成一团黑，细了撑不住，分两档是试点结论
TILT       = 0.75      # 转轴倾角（rad）。纯绕横轴会转到正底面，那一帧只剩一个梯形
ROLL       = 0.30      # 转盘整体侧倾

_MATS = {}


def argv():
    """命令行：帧数 边长 采样 输出前缀 [超采样]。

    边长是**最终**单格像素；超采样 ss>1 时实际渲 边长*ss 再由 pack_atlas 缩回来，
    描边同倍放大保证缩回后宽度不变。小物件（发卡、瓜子）单格才几十像素，
    直接渲会全是锯齿，靠 ss=2 解决。"""
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    return dict(
        frames=int(a[0]) if len(a) > 0 else 4,
        res=int(a[1]) if len(a) > 1 else 320,
        samp=int(a[2]) if len(a) > 2 else 64,
        out=a[3] if len(a) > 3 else '/tmp/out_',
        ss=int(a[4]) if len(a) > 4 else 1,
    )


def srgb(h):
    """材质颜色必须是 linear，直接填 sRGB 十六进制会整体偏亮一档。"""
    h = h.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def init():
    """清场。物品脚本第一句就该调它。"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()


def mat(name, hexcolor):
    """赛璐璐的硬边二分光影：Toon BSDF，size=0.5 让明暗交界落在中间，
       smooth=0 让它一刀切而不是渐变 —— 渐变正是三维塑料感的来源，
       而塑料感是这个项目明令禁止的（美术方向定死 2D）。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    toon = nt.nodes.new('ShaderNodeBsdfToon')
    toon.component = 'DIFFUSE'
    toon.inputs['Color'].default_value = srgb(hexcolor)
    toon.inputs['Size'].default_value = 0.5
    toon.inputs['Smooth'].default_value = 0.0
    nt.links.new(toon.outputs[0], out.inputs['Surface'])
    _MATS[name] = m
    return m


def _apply(ob, matname):
    ob.data.materials.append(_MATS[matname])
    for p in ob.data.polygons:
        p.use_smooth = False       # 平面着色：赛璐璐不要圆滑过渡
    return ob


def add_mesh(name, verts, faces, matname):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return _apply(ob, matname)


def prim(kind, matname, **kw):
    """包一层 bpy.ops.mesh.primitive_*_add：建出来就套材质、关平滑。

    kind: cube / uv_sphere / cone / cylinder / torus / ico_sphere ...
    其余参数原样转给 Blender（radius / depth / location / segments ...）。"""
    getattr(bpy.ops.mesh, 'primitive_%s_add' % kind)(**kw)
    return _apply(bpy.context.object, matname)


def _world_and_light():
    """一盏硬光定明暗交界，环境补一点免得暗面死黑。

    Blender 默认环境色是近黑的深灰，只调 strength 没用 —— Toon 的暗面本来就是
    纯黑，没有环境光补进去就死成一片。给偏暖的亮灰，暗面才落成主色的暗调。"""
    sc = bpy.context.scene
    light = bpy.data.lights.new('key', 'SUN')
    light.angle = 0.02            # 接近平行光 = 硬边阴影；柔光会把 toon 的硬边糊掉
    light.energy = 2.6
    lo = bpy.data.objects.new('key', light)
    lo.rotation_euler = (math.radians(52), 0, math.radians(20))
    sc.collection.objects.link(lo)
    w = bpy.data.worlds.new('w')
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.86, 0.88, 0.92, 1.0)
    bg.inputs[1].default_value = 1.25
    sc.world = w


def _camera():
    """必须正交。透视会让逐帧缩放不一致，转盘就会"呼吸"。"""
    sc = bpy.context.scene
    cam = bpy.data.cameras.new('cam')
    cam.type = 'ORTHO'
    cam.ortho_scale = ORTHO
    co = bpy.data.objects.new('cam', cam)
    co.location = (0, -6, 0)
    co.rotation_euler = (math.radians(90), 0, 0)
    sc.collection.objects.link(co)
    sc.camera = co


def _render_settings(res, samp, ss):
    sc = bpy.context.scene
    r = sc.render
    r.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samp
    sc.cycles.use_denoising = False   # apt 版没编 OpenImageDenoise，开了直接报错退出
    r.resolution_x = r.resolution_y = res * ss
    r.film_transparent = True         # 直接出带 alpha 的 PNG，不用品红抠像
    r.image_settings.file_format = 'PNG'
    r.image_settings.color_mode = 'RGBA'


def _freestyle(ss):
    """描边分两档。只用一档：粗了内部结构叠成一团黑，细了外轮廓撑不住。"""
    sc = bpy.context.scene
    r = sc.render
    r.use_freestyle = True
    r.line_thickness_mode = 'ABSOLUTE'
    r.line_thickness = OUTLINE_W * ss
    vl = sc.view_layers[0]
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    while fs.linesets:
        fs.linesets.remove(fs.linesets[0])

    def mk(name, thick, silhouette, border):
        ls = fs.linesets.new(name)
        # linesets.new() 建出来的 lineset 不自带 linestyle，直接设 .color 会
        # AttributeError: 'NoneType'。必须显式建一个。
        if ls.linestyle is None:
            ls.linestyle = bpy.data.linestyles.new(name + 'Ink')
        ls.select_silhouette = silhouette
        ls.select_border = border
        ls.select_crease = False
        ls.select_edge_mark = False
        ls.linestyle.color = srgb(INK)[:3]
        ls.linestyle.thickness = thick * ss
        return ls

    mk('Outline', OUTLINE_W, True, False)
    mk('Inner', INNER_W, False, True)
    fs.crease_angle = math.radians(105)


def join_all(active=None):
    """把场上所有网格并成一个物体，并把原点挪到几何中心。

    join 之后原点留在最后一个 active 物体上，直接转 rotation_euler 是绕那个点转，
    物体会甩着画大圈飞出画外。必须 origin_set，转盘才是"原地翻滚"。"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = active or bpy.context.selected_objects[0]
    bpy.ops.object.join()
    ob = bpy.context.object
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    ob.location = (0, 0, 0)
    return ob


def render_turntable(name, active=None, tilt=TILT, roll=ROLL, axis='X', lean=None):
    """建完模调这一句：合并 → 布光布景 → 绕一根轴转满一圈渲 N 帧。

    **优先用 `lean`，它才是这套东西的主参数。** `axis` 是早期只能绕三根世界轴时
    留下的，两条极端各自都有毛病：

      `axis='X'`（绕屏幕横轴翻跟头）—— 体积感最足，依次看到正面顶部背面底部。
        但有天然正面的物件（手柄、相框、戒指盒）翻过去就是背面，一半的帧认不出。
      `axis='Y'`（绕视线轴）—— 正面永远朝着观众，每一帧都认得出。
        但那是**纯屏幕内旋转，物体自身根本没转**，看上去就是一张 2D 贴纸在打旋，
        3D 白渲了。这条路踩过：八件里七件这么渲，用户一眼看出"不够 3D"。

    这两者不是二选一，中间是连续的 —— `lean` 就是那根转轴从视线轴往屏幕横轴
    偏多少度：

        lean=0      绕视线轴，等于 axis='Y'，平
        lean=35     斜着翻滚（默认推荐），可见面连续变化、明暗在变，
                    而正面最多偏转 2*lean = 70°，始终认得出
        lean=90     绕横轴翻跟头，等于 axis='X'

    正面朝向在转过 180° 时偏转 2*lean —— 这是选档的依据：要体积就加大，
    认不出了就收小。各向同性的物件（花束）没有"正面"，lean 随便，用 90 最好看。

    `tilt` / `roll` 在 lean 模式下是**物体的固定姿态偏置**（先摆好姿势，再整个
    绕斜轴转），不像 axis 模式那样会跟着转轴滚来滚去。"""
    A = argv()
    ob = join_all(active)
    _world_and_light()
    _camera()
    _render_settings(A['res'], A['samp'], A['ss'])
    _freestyle(A['ss'])

    if lean is None:
        idx = {'X': 0, 'Y': 1, 'Z': 2}[axis]
        spin_axis = None
    else:
        # 相机在 -Y 沿 +Y 看：世界 Y 是视线轴，世界 X 是屏幕横轴。
        # 转轴在这两者张成的平面里，从视线轴往横轴偏 lean 度。
        a = math.radians(lean)
        spin_axis = Vector((math.sin(a), math.cos(a), 0.0)).normalized()
        base = Matrix.Rotation(roll, 4, 'Y') @ Matrix.Rotation(tilt, 4, 'X')

    for i in range(A['frames']):
        theta = i * 2 * math.pi / A['frames']
        if spin_axis is None:
            e = [0.0, 0.0, 0.0]
            e[idx] = theta
            # 固定倾角叠在转轴之外。注意它加在哪根轴上是跟着 axis 滚的，
            # 换 axis 之后 tilt/roll 各自管什么会变，数字不能照抄。
            e[(idx + 1) % 3] += tilt
            e[(idx + 2) % 3] += roll
            ob.rotation_euler = tuple(e)
        else:
            ob.rotation_euler = (Matrix.Rotation(theta, 4, spin_axis) @ base).to_euler()
        bpy.context.scene.render.filepath = '%s%03d' % (A['out'], i)
        bpy.ops.render.render(write_still=True)
        print('[%s] %d/%d' % (name, i + 1, A['frames']), flush=True)
    print('TURNTABLE_DONE', name, flush=True)
