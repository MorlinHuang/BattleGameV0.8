// 抖音云容器服务入口：只做「直播小玩法开发者服务端」这一件事（open/hub.mjs），不带网页版、素材、存档。
//   抖音云规定：只能监听 8000 端口；必须有 GET /v1/ping 返回 200（探活）；日志打到标准输出。
//   配置全走环境变量（在抖音云「服务设置 → 环境变量」里填，不进镜像）：
//     DOUYIN_APPID、DOUYIN_APP_SECRET：小玩法 appid / AppSecret
//     DOUYIN_CLOUD=1：官方推送走内网专线到 /api/open/cloudpush（不签名）
//     DOUYIN_PUSH_SECRET：可不填；填了 /api/open/push 也收外网签名推送
//     DOUYIN_SELFTEST=1：只在 dev 环境填。后台「openAPI自测工具」的模拟数据转给正在调试的直播间（标 test：出效果、不进榜）；prod 环境不要填
//   直播间状态在内存里：实例数必须固定 1 个（最小=最大=1），否则推送和 exe 的长连接会落到不同实例。
//   全网总榜（11-16）：各直播间 exe 报上来的跨局榜记在这里，存 MongoDB（抖音云组件，开通后平台注入 MONGO_ADDRESS / MONGO_USERNAME / MONGO_PASSWORD；
//     也可以直接给 MONGO_URL）。没配数据库只记在内存里、重启就没了（日志开头有警告）。其余存档仍在 exe 里。
import http from 'node:http';
import { OpenHub, loadOpenConfig } from './open/hub.mjs';
import { RankStore, MongoRankDB, MemoryRankDB, mongoUrlFromEnv } from './open/rankstore.mjs';

const port = +(process.env.PORT || 8000);
const log = (s) => console.log(new Date().toISOString(), s);
const mongoUrl = mongoUrlFromEnv();
const rank = new RankStore({ db: mongoUrl ? new MongoRankDB({ url: mongoUrl, log }) : new MemoryRankDB(), log });
const hub = new OpenHub({ ...loadOpenConfig(''), log, rank });
// 连数据库、读入总榜：连不上隔 10 秒再试（榜没读进来之前 /api/open/score 回错，exe 会留着批次重报；推送转发不受影响）
(async function initRank() {
  try {
    if (mongoUrl) { log('[总榜] 连 MongoDB：' + mongoUrl.replace(/\/\/[^@/]*@/, '//***@')); await rank.db.connect(); }
    else log('警告：没配置 MongoDB（MONGO_ADDRESS），全网总榜只记在内存里，重启就没了');
    await rank.init();
  } catch (e) { log('[总榜] 读入失败，10 秒后重试：' + e.message); setTimeout(initRank, 10e3); }
})();
if (!hub.real) console.log('警告：没配置 DOUYIN_APPID / DOUYIN_APP_SECRET，当前是模拟模式');
if (hub.selftest) console.log('自测转发已开（DOUYIN_SELFTEST=1）：自测工具的模拟数据会转给最近启动的直播间；上线环境不要开');

http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  if (url.pathname === '/v1/ping') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end('pong'); }
  if (await hub.handle(req, res, url)) return;
  res.writeHead(404, { 'Content-Type': 'application/json; charset=utf-8' }); res.end('{"error":"没有这个接口"}');
}).listen(port, '0.0.0.0', () => console.log(`全国美食大赛 开发者服务端 :${port}  ${hub.real ? '正式（appid ' + hub.appid + '）' : '模拟模式'}  ${hub.cloud ? '抖音云内网推送' : '外网签名推送'}`));
for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => process.exit(0));

