// 抖音云容器服务入口：只做「直播小玩法开发者服务端」这一件事（open/hub.mjs），不带网页版、素材、存档。
//   抖音云规定：只能监听 8000 端口；必须有 GET /v1/ping 返回 200（探活）；日志打到标准输出。
//   配置全走环境变量（在抖音云「服务设置 → 环境变量」里填，不进镜像）：
//     DOUYIN_APPID、DOUYIN_APP_SECRET：小玩法 appid / AppSecret
//     DOUYIN_CLOUD=1：官方推送走内网专线到 /api/open/cloudpush（不签名）
//     DOUYIN_PUSH_SECRET：可不填；填了 /api/open/push 也收外网签名推送
//   直播间状态在内存里：实例数必须固定 1 个（最小=最大=1），否则推送和 exe 的长连接会落到不同实例。
//   排行榜、存档都在主播电脑上的 exe 里，这里不落盘，重启只会让 exe 自动重连。
import http from 'node:http';
import { OpenHub, loadOpenConfig } from './open/hub.mjs';

const port = +(process.env.PORT || 8000);
const hub = new OpenHub({ ...loadOpenConfig(''), log: (s) => console.log(new Date().toISOString(), s) });
if (!hub.real) console.log('警告：没配置 DOUYIN_APPID / DOUYIN_APP_SECRET，当前是模拟模式');

http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  if (url.pathname === '/v1/ping') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end('pong'); }
  if (await hub.handle(req, res, url)) return;
  res.writeHead(404, { 'Content-Type': 'application/json; charset=utf-8' }); res.end('{"error":"没有这个接口"}');
}).listen(port, '0.0.0.0', () => console.log(`全国美食大赛 开发者服务端 :${port}  ${hub.real ? '正式（appid ' + hub.appid + '）' : '模拟模式'}  ${hub.cloud ? '抖音云内网推送' : '外网签名推送'}`));
for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => process.exit(0));
