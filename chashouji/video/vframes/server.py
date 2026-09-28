#!/usr/bin/env python3
"""视频抽帧工具的网页版：打开页面 → 拖进 mp4 → 自动处理 → 看对比预览 / 下载 zip。

    python3 server.py [端口]        # 默认读 PORT_1，没有就 8765；监听 0.0.0.0

只用标准库。任务串行（抠像吃满 CPU，同时跑几个只会一起变慢）；结果留在 JOBS 目录，保留最近 KEEP 个。
结果文件支持 Range 请求：浏览器的 <video>/<audio> 靠它跳转，不支持的话预览页 ?t= 定格、
循环重播、音画对时全都跳不动（Chrome 会停在第 0 秒）。
"""
import json, os, re, shutil, sys, threading, time, traceback, uuid
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import vframes

HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = os.environ.get('VFRAMES_JOBS', os.path.expanduser('~/vframes_jobs'))
STANDEES = JOBS.rstrip('/') + '_standee'   # 先传上来、等视频来认领的立绘（跟 JOBS 分开：JOBS 里没有 status.json 的目录重启时会被清掉）
MAX_UPLOAD = 1 << 30        # 1 GB
MAX_STANDEE = 20 << 20      # 20 MB
KEEP = 30
UPLOAD_STALL = 60           # 上传中途超过这么多秒收不到数据就当断了（不设的话卡住的连接永远占着一个线程）
TYPES = {'.html': 'text/html; charset=utf-8', '.json': 'application/json; charset=utf-8', '.jpg': 'image/jpeg',
         '.png': 'image/png', '.webp': 'image/webp', '.webm': 'video/webm', '.mp4': 'video/mp4',
         '.m4a': 'audio/mp4', '.zip': 'application/zip'}
os.makedirs(JOBS, exist_ok=True)
os.makedirs(STANDEES, exist_ok=True)

jobs = {}                   # id → 状态；进程重启后从磁盘上的 status.json 恢复。读写都要拿 lock
lock = threading.Lock()
worker_lock = threading.Lock()


def update(j, **kw):
    """改任务状态并落盘。跟 /api/jobs 的列表序列化互斥，不然列表读到一半字典多了个键就报错。"""
    with lock:
        j.update(kw)
        snap = dict(j)
    with open(os.path.join(JOBS, j['id'], 'status.json'), 'w', encoding='utf-8') as f:
        json.dump(snap, f, ensure_ascii=False)


def load_jobs():
    for d in os.listdir(JOBS):
        jd = os.path.join(JOBS, d)
        p = os.path.join(jd, 'status.json')
        if not os.path.isfile(p):                          # 上传到一半服务就退出了留下的目录
            shutil.rmtree(jd, ignore_errors=True)
            continue
        with open(p, encoding='utf-8') as f:
            j = json.load(f)
        jobs[j['id']] = j
        if j['state'] in ('queued', 'running'):           # 上次进程退出时没跑完的，不会再有人接着跑
            for x in os.listdir(jd):                       # 半套产物、中间帧、原片都清掉，只留状态
                if x != 'status.json':
                    q = os.path.join(jd, x)
                    shutil.rmtree(q) if os.path.isdir(q) else os.remove(q)
            update(j, state='error', error='服务重启过，这个任务中断了，请重新上传。')


def prune():
    for t in os.listdir(STANDEES):                         # 立绘传上来一周没用就清掉
        p = os.path.join(STANDEES, t)
        if time.time() - os.path.getmtime(p) > 7 * 86400:
            os.remove(p)
    done = sorted((j for j in jobs.values() if j['state'] in ('done', 'error')), key=lambda j: j['created'])
    for j in done[:-KEEP] if len(done) > KEEP else []:
        shutil.rmtree(os.path.join(JOBS, j['id']), ignore_errors=True)
        jobs.pop(j['id'], None)


def work(j):
    progress = lambda step, pct: update(j, step=step, pct=round(pct, 3))
    with worker_lock:
        update(j, state='running', started=time.time())
        jd = os.path.join(JOBS, j['id'])
        try:
            m = vframes.process(j['src'], os.path.join(jd, 'out'), j['preset'], j['key'], progress, tmp_root=jd,
                                standee=j.get('standee'))
            big = max(m['frames'], key=lambda f: f['w'] * f['h'])
            update(j, state='done', pct=1.0, step='完成', zip=m['zip'], warnings=m['warnings'],
                   summary={'key': vframes.KEY_NAMES[m['key']], 'count': m['count'], 'fps': m['fps'],
                            'frame': [big['w'], big['h']],
                            'atlas_mb': round(m['stats']['atlas_bytes'] / 1e6, 1),
                            'decoded_mb': round(m['stats']['atlas_decoded_bytes'] / 1e6),
                            'seconds': m['stats']['seconds'],
                            'intro': m['intro'] and vframes.intro_snippet(m)})
        except vframes.VFError as e:
            update(j, state='error', error=str(e))
        except Exception as e:                               # 真正的 bug：原样记下来，页面上能看到
            update(j, state='error', error=f'内部错误：{e}', trace=traceback.format_exc())
        os.remove(j['src'])                                  # 原片只是中间产物，结果里已经有转码后的
        update(j, finished=time.time())
        with lock:
            prune()


def safe_name(name):
    name = os.path.basename(name.replace('\\', '/')).strip() or 'video.mp4'
    name = re.sub(r'[\x00-\x1f<>:"|?*]', '_', name)[:120]
    return name


class H(BaseHTTPRequestHandler):
    timeout = UPLOAD_STALL

    def log_message(self, fmt, *args):
        pass

    def send_json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ('/', '/index.html'):
            with open(os.path.join(HERE, 'index.html'), 'rb') as f:
                b = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        elif u.path == '/api/jobs':
            with lock:
                pub = [{k: v for k, v in j.items() if k not in ('src', 'trace', 'standee')} for j in jobs.values()]
            self.send_json(sorted(pub, key=lambda j: -j['created']))
        elif u.path.startswith('/jobs/'):
            # 结果文件：/jobs/<id>/<路径>，只映射到 JOBS/<id>/out/ 里面的文件（不列目录、不许跳出 out）
            parts = unquote(u.path).split('/', 3)
            with lock:
                known = len(parts) == 4 and parts[2] in jobs
            if not known:
                return self.send_error(404)
            root = os.path.realpath(os.path.join(JOBS, parts[2], 'out'))
            p = os.path.realpath(os.path.join(root, parts[3]))
            if not p.startswith(root + os.sep) or not os.path.isfile(p):
                return self.send_error(404)
            self.send_file(p)
        else:
            self.send_error(404)

    def send_file(self, p):
        """发一个文件，支持单段 Range（bytes=a-b / a- / -n）；多段或写错的 Range 按整个文件发。"""
        size = os.path.getsize(p)
        start, end, code = 0, size - 1, 200
        m = re.fullmatch(r'bytes=(\d*)-(\d*)', self.headers.get('Range', '').strip())
        if m and (m[1] or m[2]):
            if m[1]:
                start, end = int(m[1]), min(int(m[2]) if m[2] else size - 1, size - 1)
            else:
                start = max(0, size - int(m[2]))
            if start > end:
                self.send_response(416)
                self.send_header('Content-Range', f'bytes */{size}')
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
            code = 206
        self.send_response(code)
        self.send_header('Content-Type', TYPES.get(os.path.splitext(p)[1].lower(), 'application/octet-stream'))
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Accept-Ranges', 'bytes')
        if code == 206:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        with open(p, 'rb') as f:
            f.seek(start)
            left = end - start + 1
            while left > 0:
                chunk = f.read(min(left, 1 << 20))
                try:
                    self.wfile.write(chunk)
                except ConnectionError:     # 浏览器拖进度 / 换片段时会主动掐掉正在收的媒体请求，属正常
                    return
                left -= len(chunk)

    def receive(self, path, limit):
        """把请求体收进 path。返回 None 表示成功，否则是要回给前端的 (错误, 状态码)。"""
        try:
            n = int(self.headers.get('Content-Length', ''))
        except ValueError:
            return '缺少文件长度', 411
        if n <= 0:
            return '文件是空的', 400
        if n > limit:
            return f'文件超过 {limit >> 20} MB', 413
        left = n
        with open(path, 'wb') as f:
            while left > 0:
                try:
                    chunk = self.rfile.read(min(left, 1 << 20))
                except (TimeoutError, ConnectionError):      # 卡住超过 UPLOAD_STALL 秒 / 对方断开
                    break
                if not chunk:
                    break
                f.write(chunk)
                left -= len(chunk)
        return ('上传中断了，请重试。', 400) if left else None

    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == '/api/standee':
            # 立绘：先传，拿回 token；之后传的视频带上 token 就会量尾帧对齐
            token = uuid.uuid4().hex
            p = os.path.join(STANDEES, token)
            err = self.receive(p, MAX_STANDEE)
            if err:
                if os.path.exists(p):
                    os.remove(p)
                return self.send_json({'error': err[0]}, err[1])
            return self.send_json({'token': token})
        if u.path != '/api/upload':
            return self.send_error(404)
        preset = q.get('preset', ['均衡'])[0]
        key = q.get('key', ['auto'])[0]
        token = q.get('standee', [''])[0]
        if preset not in vframes.PRESETS or key not in vframes.KEY_CHOICES or (token and not re.fullmatch(r'[0-9a-f]{32}', token)):
            return self.send_json({'error': '参数不对'}, 400)
        if token and not os.path.isfile(os.path.join(STANDEES, token)):
            return self.send_json({'error': '立绘找不到了（服务重启过？），请重新选一次立绘。'}, 400)
        name = safe_name(unquote(q.get('name', ['video.mp4'])[0]))
        jid = time.strftime('%m%d-%H%M%S-') + uuid.uuid4().hex[:6]
        d = os.path.join(JOBS, jid)
        os.makedirs(d)
        src = os.path.join(d, 'src' + (os.path.splitext(name)[1][:8] or '.mp4'))
        err = self.receive(src, MAX_UPLOAD)
        if err:
            shutil.rmtree(d, ignore_errors=True)
            return self.send_json({'error': err[0]}, err[1])
        # 用原文件名做产物名（zip 名字里要看得出是哪条视频）
        named = os.path.join(d, name if name.lower().endswith(os.path.splitext(src)[1].lower()) else name + os.path.splitext(src)[1])
        os.rename(src, named)
        j = {'id': jid, 'name': name, 'preset': preset, 'key': key, 'src': named, 'state': 'queued',
             'step': '排队中', 'pct': 0, 'created': time.time()}
        if token:                                            # 立绘复制进任务目录：同一张立绘可以配好几条视频
            j['standee'] = os.path.join(d, 'standee')
            shutil.copy(os.path.join(STANDEES, token), j['standee'])
        with lock:
            jobs[jid] = j
        update(j)
        threading.Thread(target=work, args=(j,), daemon=True).start()
        self.send_json({'id': jid})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('PORT_1', 8765))
    load_jobs()
    srv = ThreadingHTTPServer(('0.0.0.0', port), H)
    print(f'视频抽帧工具：http://0.0.0.0:{port}/   结果目录 {JOBS}', flush=True)
    srv.serve_forever()


if __name__ == '__main__':
    main()
