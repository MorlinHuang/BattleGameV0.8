#!/bin/sh
# 启动 / 重启网页版（桌面容器上跑）：sh start.sh [端口]，默认 40232（公网 1.14.252.30:40232）
cd "$(dirname "$0")"
PORT=${1:-40232}
pkill -f "vframes/server.py" 2>/dev/null; sleep 0.5
setsid nohup python3 "$PWD/server.py" "$PORT" > "$HOME/vframes_server.log" 2>&1 < /dev/null &
sleep 1; tail -2 "$HOME/vframes_server.log"
