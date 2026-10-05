"""挑好的挣扎候选 → struggle/<档>/s<k>.png（整张，区域外 = 原图）。
用法 comp.py <档> <s1 候选> <s2 候选> [<s3 候选>]   候选名是 cand2/ 下的文件名（不带 .png），如 s1_r2；写 = 沿用现有 s<k>。
取用区域同 build.py struggle_region；接缝按 ../seam.py 对齐后渐变（生图的短裤边、大腿轮廓和原图错开几像素，旧做法羽化 8 像素照样看得见）。
男生被拖时黑猫拖鞋的眼睛模型爱画成黄的（原图是白点/叉），区域里暗底上的黄色改回白。旧帧挪到 old/。"""
import sys, os, shutil, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(HERE, '..')
sys.path.insert(0, V)
import seam, build
name, picks = sys.argv[1], sys.argv[2:]
d = f'{HERE}/{name}'
os.makedirs(f'{d}/old', exist_ok=True)
base = np.array(Image.open(f'{d}/base.png').convert('RGB')).astype(np.float32)
r = build.struggle_region(name, f'{V}/gait/{name}/mask.png')
for k, pk in enumerate(picks, 1):
    if pk == '=':
        continue
    c = np.array(Image.open(f'{d}/cand2/{pk}.png').convert('RGB').resize((base.shape[1], base.shape[0]))).astype(np.float32)
    if name[0] == 'a':
        from scipy import ndimage
        dark = ndimage.binary_dilation(c.max(2) < 70, iterations=6)          # 黑猫拖鞋附近
        yel = dark & r & (c[..., 0] > 120) & (c[..., 1] > 100) & (c[..., 2] < 120) & (c[..., 0] - c[..., 2] > 50)
        c[yel] = c[yel].max(1, keepdims=True)                              # 黄 → 同亮度的白灰
    out = f'{d}/s{k}.png'
    if os.path.exists(out) and not os.path.exists(f'{d}/old/s{k}.png'):
        shutil.copy(out, f'{d}/old/s{k}.png')
    Image.fromarray(np.round(np.clip(seam.paste(base, c, r), 0, 255)).astype(np.uint8)).save(out)
    print(name, f's{k} ←', pk)
