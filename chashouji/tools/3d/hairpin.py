"""发卡（档 1，查岗党）—— 一根粉色小棒 + 一端一颗浅粉珠子。

照搬 ammo.js ITEM.hairpin 的几何：总长 2r、棒粗 ≈0.6r（roundRect 半高 0.3r）、
一端一颗珠子。

四条形状结论：

- **转轴必须是 Y（绕观察轴自转），不能是 X（翻面）。** 判据 3 是按整条转盘判的，
  不是按最好那几帧判的：礼物飞过来 0.65 秒要转 1.45 圈，一半帧认不出就是不合格。
  按实际绘制尺寸铺到客厅米色底上数了一遍 —— 绕 X 8 帧里有 2 帧（棒指着镜头那两帧）塌成一颗珠子加个小疙瘩，
  6/8；绕 Y 全长永远在画面里，8/8。
  花束绕 X 翻面好用是因为它各向同性，转到哪一面都是花；发卡是绕自身长轴的
  旋转体，绕 X 翻面等于绕长轴自转，既看不出变化又要在两个相位上塌成一团。
  axis='Y' 时相机沿 +Y 看，世界 Y 就是相机轴，所以 Ry(θ) 是**画面内自转**：
  姿态不变、题材永远认得出，而光源仍然钉在世界坐标里不跟着转 —— 后面这半句
  才是换 3D 真正买到的东西（矢量版 ctx.rotate 会把光影一起转走）。
  厚度靠固定的 tilt/roll 给一点 3/4 角就够，不值得拿一半可读帧去换。
  注意 tilt/roll 是按 e[(idx+1)%3] / e[(idx+2)%3] 挂上去的，跟着 axis 滚：
  axis='Y' 时 tilt 变成绕屏幕竖轴的偏航、roll 变成物体自身的俯仰，
  数值跟 axis='X' 的那套不通用，是照着出图重调的。
- **棒做成圆柱不是扁片。** 横截面最粗处直径 0.53、珠头直径 0.84，缩到观众端的
  44px 每一帧都是一坨带描边的粉色；扁片在 3/4 角上会直接消失。
- **棒身一端必须收成尖，不能是两头一样粗的胶囊。** 等粗棒 + 一端一颗圆珠，
  在画面内自转、又放大到图集尺寸去看的时候，形状会读得很难听 —— 这是要挂在
  直播间里当礼物的东西，不能冒这个险。收成尖之后读的是"发簪"：一头尖、
  一头带珠头，既没歧义，也比胶囊更像真发卡。珠头再沿棒轴压扁 14%，
  跟棒身拉开 1.6 倍宽度差，看着是"装饰头"而不是"圆帽"。
- **棒不能收太尖、珠子不能太大。** 第一轮 0.15→0.30 的锥度配 0.48 的珠子，
  渲出来是一支麦克风；现在棒几乎等粗、可见棒长:珠径 = 1.66:1，才读得出"发卡"。
- **棒是一块整网格，不是锥台加小球拼的。** 拼的时候小球半径正好等于锥台底半径，
  两个面在底沿相切，Freestyle 把这一圈判成忽有忽无的可见轮廓，棒身上就挂着
  几根来回闪的小黑杠。

公共灯光会把每个通道往白里抬一大截（实测矢量版的珠色 #ffd9e8 渲出来是
(223,215,218) 的中性灰，一点粉味都不剩），所以珠子素材色比矢量版深两档 ——
跟 bouquet 把包装纸 #f7e3cf 加深成 #e8c79e 是同一件事：对齐的是**渲染结果**，
不是素材数值。

跑：blender -b --python hairpin.py -- 36 150 128 <out> 1
    pack_atlas.py <帧目录> hairpin_atlas.webp --cell 96

    渲染边长 150 = 单格 96 / 并集占比 0.640。common.py 说描边宽度是
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

init()
mat('bar',  '#ff7aab')   # 粉棒
mat('bead', '#ffb8d4')   # 浅粉珠

BAR_R  = 0.265           # 棒身最粗处 ≈ 矢量版 roundRect 半高 0.3r
TIP_R  = 0.10            # 另一端收成尖：见开头第五条
BEAD_R = 0.42
BEAD_FLAT = 0.86         # 珠子沿棒轴压扁一点，读成"珠头"而不是"圆帽"
SEG    = 18


def lathe(prof, seg, matname, name):
    # (r, z) 剖面绕 Z 旋成一块封闭网格，两端 r=0 的点收成极点
    verts, faces, ring = [], [], []
    for r, z in prof:
        if r <= 1e-9:
            ring.append(('p', len(verts)))
            verts.append((0.0, 0.0, z))
        else:
            ring.append(('r', len(verts)))
            for i in range(seg):
                a = i * 2 * math.pi / seg
                verts.append((r * math.cos(a), r * math.sin(a), z))
    for k in range(len(prof) - 1):
        (t0, b0), (t1, b1) = ring[k], ring[k + 1]
        for i in range(seg):
            j = (i + 1) % seg
            if t0 == 'p':
                faces.append((b0, b1 + j, b1 + i))
            elif t1 == 'p':
                faces.append((b0 + i, b0 + j, b1))
            else:
                faces.append((b0 + i, b0 + j, b1 + j, b1 + i))
    return add_mesh(name, verts, faces, matname)


# 下端收成尖 → 一路变粗的棒身 → 顶端平收（被珠子盖住，看不见）
PROF = [(TIP_R * math.sin(k * math.pi / 12), -0.92 - TIP_R * math.cos(k * math.pi / 12))
        for k in range(7)]
PROF += [(TIP_R + (BAR_R - TIP_R) * (k / 4.0) ** 0.85, -0.92 + 1.62 * k / 4.0)
         for k in range(1, 5)]
PROF += [(0.0, 0.70)]
bar = lathe(PROF, SEG, 'bar', 'bar')

# 珠头：压在棒顶上，两者相交处由 Freestyle 的可见轮廓自然分开
bead = prim('uv_sphere', 'bead', segments=24, ring_count=14, radius=BEAD_R,
            location=(0, 0, 0.62))
bead.scale = (1.0, 1.0, BEAD_FLAT)

render_turntable('hairpin', active=bar, axis='Y', tilt=0.38, roll=0.14)
