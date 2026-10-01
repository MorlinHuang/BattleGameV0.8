"""量人物和背景的亮度、饱和度（docs/三人组角色规范.md「立体感 · 先量」）。
用法：python3 measure_lum.py <grab.py 的输出前缀>
人物 = 角色层 alpha > 200 的像素按连通块分人（面积 < 4000 的丢掉：飞行物、记号）；背景 = 这个人外框往外扩 60px 的一圈里、角色层透明的背景像素。
口径：L* = CIELAB 明度（0~100，sRGB → D65）；C* = CIELAB 彩度（色彩鲜艳程度，0 = 灰）；p90 L* 看高光有多亮（贴纸感主要来自高光比背景最亮处还亮）。"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage


def lab(rgb):
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    L = 116 * f[..., 1] - 16; a = 500 * (f[..., 0] - f[..., 1]); b = 200 * (f[..., 1] - f[..., 2])
    return L, np.hypot(a, b)


def stats(px):
    L, C = lab(px.astype(float))
    return dict(L=L.mean(), L90=np.percentile(L, 90), C=C.mean(), C90=np.percentile(C, 90))


def main(pre):
    bg = np.array(Image.open(pre + '_bg.png').convert('RGB'))
    ch = np.array(Image.open(pre + '_ch.png').convert('RGBA'))
    a = ch[..., 3]
    lbl, n = ndimage.label(a > 200)
    rows = []
    for i, sl in enumerate(ndimage.find_objects(lbl), 1):
        m = lbl[sl] == i
        if m.sum() < 4000: continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        p = stats(ch[sl][..., :3][m])
        Y0, Y1, X0, X1 = max(0, y0 - 60), min(bg.shape[0], y1 + 60), max(0, x0 - 60), min(bg.shape[1], x1 + 60)
        ring = a[Y0:Y1, X0:X1] < 10
        q = stats(bg[Y0:Y1, X0:X1][ring])
        rows.append((x0, y0, x1, y1, m.sum(), p, q))
    print(f"{'外框':>22} {'面积':>7} | 人 L*  p90  C*   p90 | 背景 L*  p90  C*   p90 | ΔL*   ΔC*")
    for x0, y0, x1, y1, ar, p, q in sorted(rows, key=lambda r: (r[1], r[0])):
        print(f"{x0:4d},{y0:4d}-{x1:4d},{y1:4d} {ar:7d} | {p['L']:5.1f} {p['L90']:5.1f} {p['C']:5.1f} {p['C90']:5.1f} | "
              f"{q['L']:6.1f} {q['L90']:5.1f} {q['C']:5.1f} {q['C90']:5.1f} | {p['L'] - q['L']:+5.1f} {p['C'] - q['C']:+5.1f}")
    m = a > 200
    allp = stats(ch[..., :3][m])
    print(f"全部人物像素 L* {allp['L']:.1f} p90 {allp['L90']:.1f} C* {allp['C']:.1f} p90 {allp['C90']:.1f}  （{m.sum()} 像素）")
    s = stats(bg.reshape(-1, 3))
    print(f"整幅背景 L* {s['L']:.1f} p90 {s['L90']:.1f} C* {s['C']:.1f} p90 {s['C90']:.1f}")

main(sys.argv[1])
