#!/bin/bash
# 在桌面搭测试页（docs/三人组角色规范.md 第十节）：/home/op/trio_t/ 里全部符号链接到正式 web/，index.html 复制一份多加载 kinds.js，
# 端口 40236（port-5）。测完 stop 拆掉，正式目录一个字节都不动。
# 用法（本机）：bash serve.sh start | stop
set -e
H=$(dirname "$0")
if [ "$1" = start ]; then
  scp -q -o ConnectTimeout=20 "$H/kinds.js" kf-deployment:/tmp/kinds.js
  ssh -o ConnectTimeout=20 kf-deployment 'set -e; rm -rf /home/op/trio_t; mkdir /home/op/trio_t; cd /home/op/trio_t
    for f in /home/op/chashouji/web/*; do ln -s "$f" .; done
    rm index.html; sed "s/'"'"'trio_bestie.js'"'"', /'"'"'trio_bestie.js'"'"', '"'"'kinds.js'"'"', /" /home/op/chashouji/web/index.html > index.html
    cp /tmp/kinds.js kinds.js; grep -c kinds.js index.html
    (setsid nohup python3 /home/op/chashouji/web/serve.py 40236 > /tmp/trio_t.log 2>&1 &) ; sleep 1; curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:40236/index.html'
else
  ssh -o ConnectTimeout=20 kf-deployment 'pkill -f "[s]erve.py 40236" || true; rm -rf /home/op/trio_t; echo stopped'
fi
