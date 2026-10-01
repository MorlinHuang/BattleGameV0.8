#!/usr/bin/env python3
"""查手机网页的静态服务器（正式页 :40235）。2026-10-01 按 docs/首屏加载诊断.md P4 重写，比 python3 -m http.server 多做五件事：

1. HTTP/1.1 保持连接。原来是 HTTP/1.0，每个文件新开一条 TCP，每条都从慢启动爬起：浏览器对一个 host 只开 6 条，
   实测公网有效吞吐 19.4 Mbps，保持连接后 45.0 Mbps。
2. gzip：js / json / html / css（Accept-Encoding 带 gzip 时）。13 个 js 763 KB → 282 KB，world.json 371 KB → 35 KB。
   压好的按（路径, mtime, 大小）缓存在内存里，文件一改自动重压。图片 / 视频本身已压缩，不再压。
3. 缓存校验：Cache-Control: no-cache + ETag + Last-Modified，没变的回 304。
   原来是 no-store —— 为的是"改完 js 部署上去，浏览器还拿旧的"（SimpleHTTPRequestHandler 只发 Last-Modified，浏览器自己估缓存期）。
   no-cache 一样每次都问服务器，所以永远拿到新版；没变就是一个 304，不再每次重下 38.8 MB。
4. Range（单段 bytes=a-b）→ 206：视频边下边放、能 seek。原来不支持，浏览器媒体栈读一截就断开重来。
5. backlog 128（socketserver 默认 5，HTTP/1.0 每个文件一条连接时多人同时打开会排满）。

客户端中途断开（媒体栈读够了就断、页面关了）是正常结束：只结束这条连接，不打堆栈。

用法：cd /home/op/chashouji/web && setsid nohup python3 serve.py 40235 > /tmp/serve40235.log 2>&1 &
重启见 docs/首屏加载诊断.md「改后 · 部署与重启」。
"""
import email.utils
import gzip
import http.server
import io
import os
import re
import sys
import threading

GZIP_TYPES = ('text/', 'application/javascript', 'application/json', 'text/javascript')
_gz, _gz_lock = {}, threading.Lock()


def gz_body(path, st):
    """压好的内容（按 路径 + mtime + 大小 缓存，文件一改 key 就变）"""
    key = (path, st.st_mtime_ns, st.st_size)
    with _gz_lock:
        hit = _gz.get(key)
    if hit is None:
        with open(path, 'rb') as f:
            hit = gzip.compress(f.read(), 6)
        with _gz_lock:
            for k in [k for k in _gz if k[0] == path]: del _gz[k]
            _gz[key] = hit
    return hit


class Part(io.RawIOBase):
    """文件里 [start, start + n) 这一段（Range 用）：copyfile 读到 n 字节为止"""
    def __init__(self, f, start, n):
        self.f, self.left = f, n
        f.seek(start)
    def readable(self): return True
    def read(self, size=-1):
        if self.left <= 0: return b''
        b = self.f.read(self.left if size < 0 else min(size, self.left))
        self.left -= len(b)
        return b
    def close(self):
        self.f.close(); super().close()


class Handler(http.server.SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):                      # 目录：照 SimpleHTTP（补斜杠重定向 / index.html / 列表）
            return super().send_head()
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, 'File not found')
            return None
        st = os.fstat(f.fileno())
        ctype = self.guess_type(path)
        gz = ctype.startswith(GZIP_TYPES) and 'gzip' in self.headers.get('Accept-Encoding', '')
        etag = '"%x-%x%s"' % (st.st_size, st.st_mtime_ns, '-gz' if gz else '')
        last = email.utils.formatdate(st.st_mtime, usegmt=True)
        if self.not_modified(etag, st.st_mtime):
            f.close()
            self.send_response(304)
            self.send_header('ETag', etag); self.send_header('Last-Modified', last)
            if gz: self.send_header('Vary', 'Accept-Encoding')
            self.end_headers()
            return None
        if gz:
            f.close()
            body = gz_body(path, st)
            self.send_response(200)
            self.send_header('Content-Type', ctype); self.send_header('Content-Encoding', 'gzip')
            self.send_header('Content-Length', str(len(body))); self.send_header('Vary', 'Accept-Encoding')
            self.send_header('ETag', etag); self.send_header('Last-Modified', last)
            self.end_headers()
            return io.BytesIO(body)
        size, rng = st.st_size, self.byte_range(st.st_size)
        if rng == 'bad':
            f.close()
            self.send_response(416); self.send_header('Content-Range', 'bytes */%d' % size)
            self.send_header('Content-Length', '0'); self.end_headers()
            return None
        self.send_response(206 if rng else 200)
        self.send_header('Content-Type', ctype); self.send_header('Accept-Ranges', 'bytes')
        self.send_header('ETag', etag); self.send_header('Last-Modified', last)
        if rng:
            a, b = rng
            self.send_header('Content-Range', 'bytes %d-%d/%d' % (a, b, size))
            self.send_header('Content-Length', str(b - a + 1))
            self.end_headers()
            return Part(f, a, b - a + 1)
        self.send_header('Content-Length', str(size))
        self.end_headers()
        return f

    def not_modified(self, etag, mtime):
        inm = self.headers.get('If-None-Match')
        if inm is not None:
            return etag in [t.strip() for t in inm.split(',')] or inm.strip() == '*'
        ims = self.headers.get('If-Modified-Since')
        if not ims: return False
        try:
            t = email.utils.parsedate_to_datetime(ims)
        except (TypeError, ValueError):              # 日期写错的 If-Modified-Since 按没带处理（RFC 9110 13.1.3）
            return False
        return t is not None and int(mtime) <= t.timestamp()

    def byte_range(self, size):
        """Range: bytes=a-b / a- / -n（只认一段）→ (a, b)；没有 Range → None；越界 → 'bad'"""
        h = self.headers.get('Range')
        if not h: return None
        m = re.fullmatch(r'bytes=(\d*)-(\d*)', h.strip())
        if not m or (m.group(1) == '' and m.group(2) == ''): return None   # 多段 / 写错：按整份给（RFC 7233 允许忽略）
        if m.group(1) == '':
            n = int(m.group(2)); a, b = max(0, size - n), size - 1
        else:
            a = int(m.group(1)); b = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
        return 'bad' if a >= size or a > b else (a, b)

    def copyfile(self, source, outputfile):
        """客户端读够了就断（视频）/ 关了页面：这条连接到此为止"""
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True


class Server(http.server.ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 40235
    Server(('0.0.0.0', port), Handler).serve_forever()
