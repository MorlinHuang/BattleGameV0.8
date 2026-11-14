#!/bin/sh
# 抖音云容器服务：只能听 8000，要对外网卡（0.0.0.0）
exec node /opt/application/open-server.mjs 8000 --host=0.0.0.0
