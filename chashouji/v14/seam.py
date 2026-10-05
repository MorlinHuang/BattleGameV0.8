"""生图贴回原图时的接缝对齐（10-05 用户截图：女生大腿根、男生/女生趴地短裤后沿「像腿被切过错位」）。

walk/comp.py（后退步态）和 build.py struggle_load（输方挣扎）都是「放开区里取生图、放开区外取原图」。
生图在放开区外和原图逐像素对得上（相位相关量过六档 42 格，整体偏移都 < 0.5 像素），
可放开区里贴着分界的那一截（短裤花边、大腿轮廓）模型是重画的：轮廓左右差 3~10 像素、花边高低不一。
旧做法只羽化 3~8 像素，一刀切下去轮廓线在分界处断开、错一个台阶。

做法：在分界往里 R 像素的带子里量生图相对原图的稠密位移（TV-L1 光流），按离分界的距离把位移从 1 渐到 0
拉生图 —— 分界上生图被拽回到原图的轮廓，越往里越是生图自己的样子；颜色再按同一段距离渐变混合。
这样接缝处轮廓连续，腿的姿势（离分界远的地方）一点不改。"""
import numpy as np
from scipy import ndimage
from skimage.registration import optical_flow_tvl1
from skimage.transform import warp

SEAM_R = 90          # 对齐带宽（原图像素）：分界往里多远内把生图往原图上拽，超过这个距离完全是生图
SEAM_BLEND = 24      # 颜色混合带宽：分界往里这么多像素内由原图渐变到（对齐后的）生图
SEAM_PAD = 40        # 量光流时带子外多带的边，光流在边上不准
# TV-L1 参数：默认（attachment 10、迭代 30）在平涂色块上对不齐 —— bF 短裤边差 10 多像素、整片藏青没纹理，
# 接缝带残差 99 分位 364（一道紫色糊边）；aF 大腿内侧的细描边对不准，渐变带里叠出两条线。
# 加大数据项、多迭代，灰度先糊 1.5 像素（细线变宽，金字塔粗层也看得见）：残差 99 分位 bF 364→47、aF 54→39、aK 38→33（10-05 实测）
FLOW = dict(attachment=30, tightness=0.3, num_warp=10, num_iter=60)
FLOW_BLUR = 1.5
# 不对齐的地方 = 前后向光流对不上的像素（光流的标准遮挡检测）：base→cand 走过去、cand→base 走不回原处，
# 说明这里是只有一边有的内容。分界附近生图画了原图没有的东西（bK 挣扎帧踢起的小腿横过另一条大腿，就在腰线下 40 像素），
# 光流会硬把它压扁拽成原图的样子，轮廓撕开一道（10-05 实测）；这些地方不拽，靠颜色渐变过渡。
# 按位移场伸缩量设阈值分不开：bF 短裤边合法的压缩和 bK 撕裂的伸缩分布重叠。
FB_TOL = 3.0         # 往返误差超过这么多像素算对不上
FB_GROW = 6          # 对不上的区域外扩再糊开，免得拽与不拽的交界又撕一道


def _gray(a):
    return (a[..., :3].astype(np.float32) @ np.array([.299, .587, .114], np.float32)) / 255


def seam_weights(region):
    """region（放开区，True = 取生图）→ (对齐权重, 混合权重)，都是离放开区边界的距离的函数：
    边界上对齐 1、混合 0，往里 SEAM_R 对齐降到 0，往里 SEAM_BLEND 混合升到 1。放开区外两者都是 0。
    贴着图边的那条边界不算（图外面没有原图可接）。"""
    pad = np.pad(region, 1, mode='edge')
    d = ndimage.distance_transform_edt(pad)[1:-1, 1:-1]
    t = np.clip(d / SEAM_R, 0, 1)
    align = np.where(region, 1 - t * t * (3 - 2 * t), 0).astype(np.float32)
    s = np.clip(d / SEAM_BLEND, 0, 1)
    blend = np.where(region, s * s * (3 - 2 * s), 0).astype(np.float32)
    return align, blend


def align_to_base(base, cand, region):
    """把 cand（H×W×3，和 base 同尺寸）在 region 边界附近拽到 base 上，返回对齐后的 cand（float32）。
    只动边界往里 SEAM_R 以内的像素，其余原样。"""
    align, _ = seam_weights(region)
    ys, xs = np.nonzero(align > 0)
    if not len(ys):
        return cand.astype(np.float32)
    y0, y1 = max(0, ys.min() - SEAM_PAD), min(base.shape[0], ys.max() + SEAM_PAD + 1)
    x0, x1 = max(0, xs.min() - SEAM_PAD), min(base.shape[1], xs.max() + SEAM_PAD + 1)
    b, c = (ndimage.gaussian_filter(_gray(q[y0:y1, x0:x1]), FLOW_BLUR) for q in (base, cand))
    # v, u：base 上 (y, x) 处的内容在 cand 里位于 (y + v, x + u)
    v, u = optical_flow_tvl1(b, c, **FLOW)
    vb, ub = optical_flow_tvl1(c, b, **FLOW)            # 反向：cand 上 (y, x) 的内容在 base 里位于 (y + vb, x + ub)
    rr, cc = np.meshgrid(np.arange(y1 - y0), np.arange(x1 - x0), indexing='ij')
    there = np.array([rr + v, cc + u])
    back_v = ndimage.map_coordinates(vb, there, order=1, mode='nearest')
    back_u = ndimage.map_coordinates(ub, there, order=1, mode='nearest')
    bad = ndimage.binary_dilation(np.hypot(v + back_v, u + back_u) > FB_TOL, iterations=FB_GROW)
    a = align[y0:y1, x0:x1] * (1 - np.clip(ndimage.gaussian_filter(bad.astype(np.float32), FB_GROW / 2) * 2, 0, 1))
    coords = np.array([rr + v * a, cc + u * a])
    out = cand.astype(np.float32).copy()
    for k in range(3):
        out[y0:y1, x0:x1, k] = warp(cand[y0:y1, x0:x1, k].astype(np.float32), coords, order=1, mode='edge', preserve_range=True)
    return out


def paste(base, cand, region):
    """放开区 region 里取生图（边界附近先对齐、再渐变混合），区外原图原样。返回 float32 H×W×3"""
    c = align_to_base(base, cand, region)
    _, blend = seam_weights(region)
    w = blend[..., None]
    return base.astype(np.float32) * (1 - w) + c * w
