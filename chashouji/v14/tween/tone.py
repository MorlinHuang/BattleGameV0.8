"""发色对齐：生图重画输方时头发常被画成偏浅的棕色（原图男生近黑、女生深棕近黑），一格黑一格棕连播会闪。
只动输方蒙版里「像头发」的像素：暗（亮度 < HI）、不偏蓝（r ≥ b − 8；男生藏青短裤偏蓝、不动）、
不是品红底和抠图毛边（绿通道 ≥ 0.55 × 红、蓝 —— 品红的亮度也只有 105 上下，不排除的话均值全是背景）。
按 base 同类像素的平均色逐通道乘增益（浅棕 → 近黑是整体压暗），亮度 LO 以下全量、LO~HI 之间渐弱到 0
（肤色暗部、睡衣褶子的边缘不被拽暗）。
用法：python3 tone.py <档> <图> [<图> ...]   （原地改；原图备份到 <档>/old_tone/）"""
import os, sys, shutil
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
LO, HI = 110, 135


def hairish(a, who):
    L = a @ np.array([0.299, 0.587, 0.114])
    g = a[..., 1]
    return who & (L < HI) & (a[..., 0] >= a[..., 2] - 8) & (g >= 0.55 * a[..., 0]) & (g >= 0.55 * a[..., 2]), L


def main(name, paths):
    d = os.path.join(HERE, name)
    who = np.array(Image.open(os.path.join(d, 'mask.png')).getchannel('A')) < 128
    b = np.array(Image.open(os.path.join(d, 'base.png')).convert('RGB')).astype(np.float32)
    mb, _ = hairish(b, who)
    ref = b[mb].mean(0)
    for p in paths:
        bk = os.path.join(d, 'old_tone'); os.makedirs(bk, exist_ok=True)
        if not os.path.exists(os.path.join(bk, os.path.basename(p))):
            shutil.copy2(p, bk)
        a = np.array(Image.open(p).convert('RGB')).astype(np.float32)
        m, L = hairish(a, who)
        gain = ref / a[m].mean(0)
        w = (np.clip((HI - L) / (HI - LO), 0, 1) * m)[..., None]
        out = a * (1 - w) + np.clip(a * gain, 0, 255) * w
        Image.fromarray(out.round().astype(np.uint8)).save(p)
        print(os.path.basename(p), '增益', gain.round(2))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
