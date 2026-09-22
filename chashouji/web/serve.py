#!/usr/bin/env python3
"""开发预览服务器。比 python3 -m http.server 只多做一件事：每个响应都带
   Cache-Control: no-store。

   起因：改完 js 部署上去，浏览器里看到的还是旧的。SimpleHTTPRequestHandler
   只发 Last-Modified、不发 Cache-Control，浏览器就自己估一个缓存期
   （(now - Last-Modified) 的十分之一），文件越久没动缓存越久 —— 一个放了
   两天的 main.js 能被缓存好几个小时。截图脚本靠 ?v=<时间戳> 绕过它，
   人拿浏览器看就绕不过去，会以为"你没部署"。

   用法：cd /home/op/chashouji/web && nohup python3 serve.py 40235 &
"""
import http.server
import sys


class NoStore(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        super().end_headers()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 40235
    # 多线程：一个页面要并发拉五个 js 和几十张贴图，单线程会排队
    http.server.ThreadingHTTPServer(('0.0.0.0', port), NoStore).serve_forever()
