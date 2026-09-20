"""描边宽度探针：渲一个正方块，量墨边到底有多宽。

Freestyle 的线宽有两个入口 —— `render.line_thickness`（全局）和
`linestyle.thickness`（每个 lineset 自己的）。两者在 ABSOLUTE 模式下是什么
关系，文档没写清楚，只能量。踩过两次亏：超采样 ss 和屏幕倒推倍率 k 都曾经
被同时乘进这两处，渲出来的描边按平方变粗，而看单帧图根本看不出是平方还是
线性，只觉得"怎么这么黑"。

    blender -b --python probe_ink.py -- <边长> <render线宽> <linestyle线宽> <输出前缀>

物体是个 2.0 单位的正方块，正对相机，剪影就是个正方形 —— 横向扫描线切过
左右两条竖边，游程长度就是描边宽度，没有斜切误差。
"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
from common import init, mat, prim, srgb, INK

a = sys.argv[sys.argv.index('--') + 1:]
res, rt, lt, out = int(a[0]), float(a[1]), float(a[2]), a[3]

init()
mat('block', '#e8c9a0')
ob = prim('cube', 'block', size=2.0, location=(0, 0, 0))
common._world_and_light()
common._camera()
common._render_settings(res, 32, 1)

sc = bpy.context.scene
r = sc.render
r.use_freestyle = True
r.line_thickness_mode = 'ABSOLUTE'
r.line_thickness = rt
vl = sc.view_layers[0]
vl.use_freestyle = True
fs = vl.freestyle_settings
while fs.linesets:
    fs.linesets.remove(fs.linesets[0])
ls = fs.linesets.new('P')
if ls.linestyle is None:
    ls.linestyle = bpy.data.linestyles.new('PInk')
for at in ('select_silhouette', 'select_border', 'select_crease',
           'select_edge_mark', 'select_contour', 'select_external_contour'):
    setattr(ls, at, False)
ls.select_silhouette = True
ls.linestyle.color = srgb(INK)[:3]
ls.linestyle.thickness = lt

r.filepath = out
bpy.ops.render.render(write_still=True)
print('PROBE_DONE render=%.2f linestyle=%.2f' % (rt, lt), flush=True)
