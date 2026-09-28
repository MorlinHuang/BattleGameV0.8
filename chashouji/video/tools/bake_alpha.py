#!/usr/bin/env python3
"""把出场视频烤成带透明通道的 webm：人物不透明、环境半透明且往画框边淡掉、亮部（金光/亮片）多留、最后一秒环境退干净。

    python3 bake_alpha.py 帧目录 遮罩目录 原视频.mp4 输出.webm [--bg 0.22 --glow 0.9 --feather 0.16 --edge 0.03]

帧目录：ffmpeg -vsync 0 解出的全部帧（%04d.png）；遮罩目录：matte.py 的输出（同名，255 = 人物）。
为什么烤进视频、不在游戏里用 WebGL 实时合成：桌面容器的 Chrome（无 GPU）里 WebGL 上下文一建就丢，
直播伴侣 / OBS 的环境同样没法保证；带 alpha 的 VP9 webm 用普通 <video> 就能放，Chromium 内核都支持。
"""
import argparse, json, os, subprocess, tempfile
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image

A = None


def ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def one(job):
    src, msk, dst, env = job
    c = np.asarray(Image.open(src).convert('RGB')).astype(np.float32) / 255
    m = np.asarray(Image.open(msk).convert('L')).astype(np.float32) / 255
    h, w = m.shape
    yy, xx = np.mgrid[0:h, 0:w]
    u, v, asp = (xx + 0.5) / w, (yy + 0.5) / h, h / w
    e = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v) * asp)              # 到画框四边的距离（按宽量）
    ec = np.minimum(np.minimum(u, 1 - u), np.minimum(v, (1 - v) * 0.25) * asp)     # 人物：底边软得宽 4 倍（特写被画框底边截断）
    hl = ss(0.62, 0.95, c.max(2))                                                  # 亮部：光柱、亮片、金光
    a = np.maximum(m * ss(0, A.edge, ec), ss(0, A.feather, e) * env * np.maximum(A.bg, A.glow * hl))
    Image.fromarray(np.dstack([(c * 255).round(), (a * 255).round()]).astype(np.uint8), 'RGBA').save(dst, compress_level=1)


def main():
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument('frames'); ap.add_argument('mattes'); ap.add_argument('video'); ap.add_argument('out')
    ap.add_argument('--bg', type=float, default=0.22)       # 环境留多少不透明度
    ap.add_argument('--glow', type=float, default=0.9)      # 亮部留多少
    ap.add_argument('--feather', type=float, default=0.16)  # 环境从画框边往里多宽淡进来（占宽的比例）
    ap.add_argument('--edge', type=float, default=0.03)     # 人物在画框边软掉多宽
    ap.add_argument('--env-off', type=float, nargs=2, default=[1.25, 0.45])   # 环境 + 光从离结尾几秒开始退、退到离结尾几秒退完
    ap.add_argument('--jobs', type=int, default=16)
    A = ap.parse_args()
    info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                               'stream=avg_frame_rate', '-show_entries', 'format=duration', '-of', 'json', A.video]))
    rate = info['streams'][0]['avg_frame_rate']; n, d = map(float, rate.split('/')); fps = n / d
    fs = sorted(f for f in os.listdir(A.frames) if f.endswith('.png'))
    dur = len(fs) / fps
    tmp = tempfile.mkdtemp(prefix='bake_')
    jobs = []
    for i, f in enumerate(fs):
        left = dur - (i + 0.5) / fps
        env = min(1, max(0, (left - A.env_off[1]) / (A.env_off[0] - A.env_off[1])))
        jobs.append((os.path.join(A.frames, f), os.path.join(A.mattes, f), os.path.join(tmp, f), env))
    with ProcessPoolExecutor(A.jobs) as ex:
        list(ex.map(one, jobs, chunksize=4))
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-framerate', rate, '-i', os.path.join(tmp, '%04d.png'), '-i', A.video,
                           '-map', '0:v', '-map', '1:a', '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '26',
                           '-row-mt', '1', '-deadline', 'good', '-cpu-used', '2', '-auto-alt-ref', '0',
                           '-c:a', 'libopus', '-b:a', '128k', '-shortest', A.out])
    subprocess.call(['rm', '-rf', tmp])
    print(f'{len(fs)} 帧 @ {fps:.3f}fps → {A.out}（{os.path.getsize(A.out) / 1e6:.1f} MB）')


if __name__ == '__main__':
    main()
