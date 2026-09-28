#!/usr/bin/env python3
"""出场视频的人物遮罩：isnet-anime（二次元人物分割，rembg 同款模型）逐帧出 alpha。

    python3 matte.py 帧目录 遮罩目录 [--model ~/isnet-anime.onnx] [--jobs 12]

输入帧是 ffmpeg 解出来的 PNG；输出同名灰度 PNG（255 = 人物）。
模型输入是 1024×1024 直接拉伸（跟 rembg 的做法一致，不补边），归一化 mean (0.485,0.456,0.406)、std 1。
"""
import argparse, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image

sess = None


def init(model, threads):
    global sess
    import onnxruntime as ort
    o = ort.SessionOptions(); o.intra_op_num_threads = threads; o.inter_op_num_threads = 1
    sess = ort.InferenceSession(model, o, providers=['CPUExecutionProvider'])


def one(job):
    src, dst = job
    im = Image.open(src).convert('RGB')
    x = np.asarray(im.resize((1024, 1024), Image.LANCZOS)).astype(np.float32) / 255.0
    x = (x - np.array([0.485, 0.456, 0.406], np.float32)).transpose(2, 0, 1)[None]
    y = sess.run(None, {sess.get_inputs()[0].name: x})[0][0, 0]
    y = (y - y.min()) / max(1e-6, y.max() - y.min())
    Image.fromarray((y * 255).astype(np.uint8)).resize(im.size, Image.LANCZOS).save(dst)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--model', default=os.path.expanduser('~/isnet-anime.onnx'))
    ap.add_argument('--jobs', type=int, default=12)
    a = ap.parse_args()
    os.makedirs(a.dst, exist_ok=True)
    fs = sorted(f for f in os.listdir(a.src) if f.endswith('.png'))
    threads = max(1, (os.cpu_count() or 4) // a.jobs)
    with ProcessPoolExecutor(a.jobs, initializer=init, initargs=(a.model, threads)) as ex:
        for i, _ in enumerate(ex.map(one, [(os.path.join(a.src, f), os.path.join(a.dst, f)) for f in fs])):
            if i % 24 == 0: print(f'{i}/{len(fs)}', flush=True)
    print(f'{len(fs)} 帧完成')


if __name__ == '__main__':
    main()
