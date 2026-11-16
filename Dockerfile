# 全国美食大赛 · 抖音云容器服务（开发者服务端 + 全网总榜；依赖只有 mongodb 驱动，已随包带上 node_modules，构建时不用联网装包）
FROM node:20-alpine
ENV TZ=Asia/Shanghai NODE_ENV=production
WORKDIR /opt/application
COPY package.json cloud.mjs run.sh boards.mjs medals.mjs rankops.mjs ./
COPY node_modules ./node_modules
COPY open/api.mjs open/hub.mjs open/sign.mjs open/rankstore.mjs ./open/
RUN chmod a+x /opt/application/run.sh
EXPOSE 8000
CMD ["/opt/application/run.sh"]
