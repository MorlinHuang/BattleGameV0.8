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
ORTHO      = 3.3       # 相机正交宽度。主体 NOMINAL 单位 → 占画幅 60.6%
NOMINAL    = 2.0       # 主体的标称直径（Blender 单位）。pack_atlas 靠它反算 scale
INK        = '3a2c26'  # 描边色，取角色线稿那个暖黑
OUTLINE_W  = 2.8       # 描边宽度，**观众屏幕上的像素**（不是渲染图里的）。见 render_turntable
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


def _ink_thickness(w):
    """把"想要的线宽（渲染图像素）"换算成 `linestyle.thickness` 该填的值。

    Freestyle 的线宽有两个入口 —— `render.line_thickness`（全局）和
    `linestyle.thickness`（每个 lineset 自己的）。ABSOLUTE 模式下这两个是
    **相乘**的，`tools/3d/probe_ink.py` 渲正方块标定出来：

        线宽 ≈ 0.85 × render.line_thickness × linestyle.thickness − 0.65

    （实测点：2.6×2.6→4.98px、2.6×5.2→10.94、5.2×2.6→10.94、5.2×5.2→22.23，
    交换两个入口结果完全一样，对称性说明就是乘法。）

    这个乘法坑过两次，两次都是**把同一个倍率乘进了两处**，于是线宽按平方涨：
    第一次是超采样 ss（ss=1/2/3 渲出 4/14/30px，发卡整根被描边吞成一条墨胶囊）；
    第二次是按屏幕倒推的倍率 k —— 戒指盒 k=1.97 两处一乘，描边到屏幕上是
    **11px**，整件糊成黑块，而调 INNER_W 完全没反应（因为那一档本来就是空的，
    见 _freestyle），害得人往"内部线太粗"的方向找了一轮。

    根治办法是让宽度只有一个入口：`render.line_thickness` 固定成中性的 1.0，
    所有倍率都只乘进 linestyle 这一边。"""
    return (w + 0.65) / 0.85


def _freestyle(ss, k=1.0):
    """描边只有一档。

    原先是两档（`select_silhouette` 一档、`select_border` 一档），想让外轮廓粗、
    内部结构线细。**但 border 指的是网格的开放边，而这些物品都是封闭网格，
    那一档一条线都不产生** —— 所谓"两档"一直只有一档在画。

    试过换成 `select_external_contour` 来单独拿最外一圈，正交相机下它同样
    不出线（probe_ink.py 渲正方块，一个描边像素都没有）。所以这套用法里
    外轮廓和自遮挡轮廓**分不开**，索性就只留一档，把宽度定准。

    `k` 是渲染图相对屏幕的放大倍率（render_turntable 按 screen_r 算出来的），
    只乘在 linestyle 这一个入口上 —— 理由见 _ink_thickness。"""
    sc = bpy.context.scene
    r = sc.render
    r.use_freestyle = True
    r.line_thickness_mode = 'ABSOLUTE'
    r.line_thickness = 1.0        # 中性基准，宽度全部走 linestyle，不要动它
    vl = sc.view_layers[0]
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    while fs.linesets:
        fs.linesets.remove(fs.linesets[0])

    ls = fs.linesets.new('Ink')
    # linesets.new() 建出来的 lineset 不自带 linestyle，直接设 .color 会
    # AttributeError: 'NoneType'。必须显式建一个。
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new('Ink')
    # 全部关掉再按需打开：漏关一个就会有第二档线悄悄叠上来，而它跟正主同色，
    # 看图根本分不出多出来的线是哪一档画的
    for a in ('select_silhouette', 'select_border', 'select_crease',
              'select_edge_mark', 'select_contour', 'select_external_contour'):
        setattr(ls, a, False)
    ls.select_silhouette = True
    ls.linestyle.color = srgb(INK)[:3]
    ls.linestyle.thickness = _ink_thickness(OUTLINE_W * k * ss)
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


def render_turntable(name, active=None, tilt=TILT, roll=ROLL, axis='X', lean=None, screen_r=None):
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
    绕斜轴转），不像 axis 模式那样会跟着转轴滚来滚去。

    ## screen_r —— 描边宽度必须一路算到观众屏幕上

    `screen_r` 是这件东西在引擎里的半径（main.js 的 `GIFT[x].r`）。给了它，
    描边就按"屏幕上 OUTLINE_W 像素"倒推渲染时该画多粗；不给则按老口径（渲染
    图里 OUTLINE_W 像素）。

    为什么必须倒推：素材从渲染图到观众眼睛要缩**两道**，
      渲染边长 R ──(并集裁切，边长 side)──▶ 图集单格 cell ──(引擎绘制)──▶ 屏幕 px
    把两道并起来，`屏幕描边 = 渲染描边 × cell/side × px/cell = 渲染描边 × px/side`
    —— cell 约掉了，所以调单格边长根本改变不了描边，之前那条"最终像素"的约定
    只管到图集为止，屏幕上早就走样了：实测八件落在 1.3~2.2px，小件细掉一半。
    而这套画风里实体全靠轮廓被看见（明亮客厅底图上亮度加不上去），描边一细
    东西就糊进背景。

    再把 side 换成已知量：`scale = side / (R × NOMINAL/ORTHO)`、`px = 2 × screen_r × scale`，
    代进去 scale 正好约掉：

        渲染描边 = OUTLINE_W × R × (NOMINAL/ORTHO) / (2 × screen_r)

    于是只跟渲染边长和引擎半径有关，跟并集、跟 cell 都无关 —— 换句话说这个数
    在开渲之前就能算准，不必先渲一轮量并集。

    ⚠️ 描边变粗会把并集撑大，**改完这个参数必须重量一次并集再定 cell**
    （`pack_atlas.py` 会打印出来）。"""
    A = argv()
    ob = join_all(active)
    _world_and_light()
    _camera()
    _render_settings(A['res'], A['samp'], A['ss'])
    k = A['res'] * (NOMINAL / ORTHO) / (2 * screen_r) if screen_r else 1.0
    if screen_r:
        print('[%s] 描边 ×%.2f（屏幕 %.1fpx → 渲染 %.1fpx）'
              % (name, k, OUTLINE_W, OUTLINE_W * k), flush=True)
    _freestyle(A['ss'], k)

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
