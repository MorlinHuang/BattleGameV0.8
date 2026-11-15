# 查手机 · 抖音云容器服务（只含开发者服务端；依赖只有抖音云服务端 SDK，全服榜存云数据库用）
FROM node:20-alpine
ENV TZ=Asia/Shanghai NODE_ENV=production
WORKDIR /opt/application
COPY package.json ./
RUN npm install --omit=dev --no-audit --no-fund
COPY open-server.mjs run.sh ./
COPY open/ ./open/
RUN mkdir -p /opt/application/data && chmod a+x /opt/application/run.sh
EXPOSE 8000
CMD ["/opt/application/run.sh"]
