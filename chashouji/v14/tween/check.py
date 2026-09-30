"""过渡帧体检（2026-09-30 用户：「需要检查每帧的形体比例，防止胳膊、腿过长或其他部位不协调」）。

每档 tween/<档>/t*.png 都是拿 base.png 蒙版重绘输方得来的，同一个人、同一缩放，所以输方的头应当跟 base 里一样大。
生图画人物有自己的习惯比例（头偏大），base 的头在 2026-09-26 已经按 arms/heads.py 收过，重绘出来的输方往往又大回去。
这里逐格量输方的头（arms/heads.py 的多尺度 NCC，对着 n0 成品贴图），跟 base 比：
  头 / base > 1 + TOL → 用 heads.pinch 在 t*.png 上把头收回（原图备份到 old_heads/）；
  头 / base < 1 − TOL → 只报，不放大（放大会糊）；
另外报输方最低点离 base 最低点多少（原图像素，正 = 比 base 高 = 可能悬空）。
胳膊、腿长短量不准（姿势不同，外框不可比），出一张全帧并排总览图 /workspace/tmp/check_<档>.jpg 人眼看。
用法：python3 check.py [--fix] [档 ...]
"""
import os, sys, shutil
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'arms'))
import heads as H      # noqa: E402  （它 exec 了 build.py 的前半截，拿 cutout / SCALE / BODY）
B = H.B
TOL = 0.04
REF = Image.open(os.path.join(HERE, '..', '..', 'web', 'assets', 'world', 'pose_n0.webp')).convert('RGBA')


def loser_side(name):
    return 'b' if name[0] == 'a' else 'a'


def head(path, name):
    """原图坐标下输方头的 (k, cx, cy, r)"""
    s = B['SCALE'] / B['BODY'][name]
    rgb, al = B['cutout'](path)
    im = Image.fromarray(np.concatenate([rgb, al[..., None] * 255], -1).astype(np.uint8), 'RGBA')
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    k, cx, cy, r = H.head_find(REF, im, loser_side(name))
    return k, cx / s, cy / s, r / s


def bottom(path, name):
    """输方（蒙版透明区）最低的不透明像素 y（原图坐标）"""
    rgb, al = B['cutout'](path)
    who = np.array(Image.open(os.path.join(HERE, name, 'mask.png')).getchannel('A')) < 128
    ys = np.nonzero((al > 0.5) & who)[0]
    return int(ys.max())


def main():
    fix = '--fix' in sys.argv
    names = [a for a in sys.argv[1:] if not a.startswith('--')] or ['aK', 'aF', 'aL', 'bK', 'bF', 'bL']
    for name in names:
        d = os.path.join(HERE, name)
        ts = sorted([f for f in os.listdir(d) if f[0] == 't' and f[1:-4].isdigit()], key=lambda f: int(f[1:-4]))
        kb, *_ = head(os.path.join(d, 'base.png'), name)
        yb = bottom(os.path.join(d, 'base.png'), name)
        print(f'{name} base 头 {kb:.2f}  最低点 {yb}')
        for f in ts:
            p = os.path.join(d, f)
            k, cx, cy, r = head(p, name)
            q = k / kb
            flag = '头大' if q > 1 + TOL else '头小' if q < 1 - TOL else ''
            print(f'  {f}: 头 {k:.2f} ({q:.2f}×base) {flag}  最低点比 base 高 {yb - bottom(p, name)}')
            if fix and q > 1 + TOL:
                bk = os.path.join(d, 'old_heads'); os.makedirs(bk, exist_ok=True)
                if not os.path.exists(os.path.join(bk, f)):
                    shutil.copy2(p, bk)
                rgb = np.array(Image.open(p).convert('RGB'))
                Image.fromarray(H.pinch(rgb, cx, cy + 0.5 * r, r, 1 / q)).save(p)
                k2 = head(p, name)[0]
                print(f'     收头 → {k2:.2f} ({k2 / kb:.2f}×base)')


if __name__ == '__main__':
    main()
