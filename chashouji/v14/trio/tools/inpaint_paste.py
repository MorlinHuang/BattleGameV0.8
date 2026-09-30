"""把局部重绘（generate_image 带蒙版）出来的那一块贴回原立绘（2026-10-01，老角色 B12 / G12 补姿势帧）。

用户："能用原图做底、只局部重绘手臂或腿的，就不要整张重出"。生图就算带蒙版，蒙版外面也会被整张轻微重画（颜色、线条都会漂 ——
G12 的纱整片变艳了），所以**只取蒙版框里那一块**，框外一律是原图的像素；框的边上 feather 像素宽渐变，接缝落在原图和新图本来就一样的地方。

  底图做法：原图放大 K 倍贴在 1024 见方的幕布（绿 / 品红）上，左上角 (ox, oy)；蒙版 = 同尺寸 PNG，框里透明（要重画）。
  生图回来是 1254 见方（同一张画面等比放大），先缩回 1024，按幕布抠像（crewart.cut；回来就是透明底的直接用它的 alpha），再按 (ox, oy, K) 缩回原图像素。

用法：python3 inpaint_paste.py <原图> <生图> <ox> <oy> <K> <green|magenta> '<[[x0,y0,x1,y1],...] 原图像素>' <输出.png> [feather=4]"""
import json, os, sys, tempfile
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))
from crewart import cut


def paste(orig, gen, ox, oy, K, screen, boxes, out, feather=4, key=(20, 90)):
    o = Image.open(orig).convert('RGBA'); w, h = o.size
    g0 = Image.open(gen).convert('RGBA').resize((1024, 1024), Image.LANCZOS)
    if (np.array(g0)[..., 3] < 250).mean() > 0.05:                  # 生图有时直接回透明底（幕布已经去掉了）：用它自己的 alpha
        a = np.array(g0).astype(np.float32); rgb, al = a[..., :3], a[..., 3] / 255
    else:
        tmp = tempfile.mktemp(suffix='.png'); g0.convert('RGB').save(tmp)
        rgb, al = cut(tmp, screen, key); os.remove(tmp)
    ga = np.dstack([rgb * al[..., None], al * 255]).clip(0, 255).astype(np.float32)          # 预乘，缩的时候边上不带出幕布色
    reg = Image.fromarray(ga.astype(np.uint8), 'RGBA').crop((ox, oy, ox + round(w * K), oy + round(h * K))).resize((w, h), Image.LANCZOS)
    G = np.array(reg).astype(np.float32)
    O = np.array(o).astype(np.float32); O[..., :3] *= O[..., 3:] / 255
    M = np.zeros((h, w), bool)
    for x0, y0, x1, y1 in boxes: M[y0:y1, x0:x1] = True
    wgt = np.clip(ndimage.distance_transform_edt(M) / feather, 0, 1)[..., None]               # 框边往里 feather 像素渐变到新图
    R = O * (1 - wgt) + G * wgt
    a = R[..., 3:]; R[..., :3] = np.where(a > 0, R[..., :3] * 255 / np.maximum(a, 1e-3), 0)
    Image.fromarray(R.clip(0, 255).astype(np.uint8), 'RGBA').save(out)
    print(out, o.size)


if __name__ == '__main__':
    a = sys.argv[1:]
    paste(a[0], a[1], int(a[2]), int(a[3]), float(a[4]), a[5], json.loads(a[6]), a[7], int(a[8]) if len(a) > 8 else 4)
