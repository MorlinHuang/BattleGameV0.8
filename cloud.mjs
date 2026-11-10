// 抖音云容器服务入口：只做「直播小玩法开发者服务端」这一件事（open/hub.mjs），不带网页版、素材、存档。
//   抖音云规定：只能监听 8000 端口；必须有 GET /v1/ping 返回 200（探活）；日志打到标准输出。
//   配置全走环境变量（在抖音云「服务设置 → 环境变量」里填，不进镜像）：
//     DOUYIN_APPID、DOUYIN_APP_SECRET：小玩法 appid / AppSecret
//     DOUYIN_CLOUD=1：官方推送走内网专线到 /api/open/cloudpush（不签名）
//     DOUYIN_PUSH_SECRET：可不填；填了 /api/open/push 也收外网签名推送
//     DOUYIN_SELFTEST=1：只在 dev 环境填。后台「openAPI自测工具」的模拟数据转给正在调试的直播间（标 test：出效果、不进榜）；prod 环境不要填
//   直播间状态在内存里：实例数必须固定 1 个（最小=最大=1），否则推送和 exe 的长连接会落到不同实例。
//   排行榜、存档都在主播电脑上的 exe 里，这里不落盘，重启只会让 exe 自动重连。
import http from 'node:http';
import { OpenHub, loadOpenConfig } from './open/hub.mjs';

const port = +(process.env.PORT || 8000);
const hub = new OpenHub({ ...loadOpenConfig(''), log: (s) => console.log(new Date().toISOString(), s) });
if (!hub.real) console.log('警告：没配置 DOUYIN_APPID / DOUYIN_APP_SECRET，当前是模拟模式');
if (hub.selftest) console.log('自测转发已开（DOUYIN_SELFTEST=1）：自测工具的模拟数据会转给最近启动的直播间；上线环境不要开');

http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  if (url.pathname === '/v1/ping') { res.writeHead(200, { 'Content-Type': 'text/plain' }); return res.end('pong'); }
  if (await hub.handle(req, res, url)) return;
  res.writeHead(404, { 'Content-Type': 'application/json; charset=utf-8' }); res.end('{"error":"没有这个接口"}');
}).listen(port, '0.0.0.0', () => console.log(`全国美食大赛 开发者服务端 :${port}  ${hub.real ? '正式（appid ' + hub.appid + '）' : '模拟模式'}  ${hub.cloud ? '抖音云内网推送' : '外网签名推送'}`));
for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => process.exit(0));

// 诊断（11-10 评论不生效）：官方抖音云示例开推送任务走内网专线 OpenAPI（http、不带 access_token），我们走的是公网 webcast.bytedance.com。
// 启动时探一下内网专线通不通、回什么，结果进日志，决定要不要换
if (hub.real && hub.cloud) {
  const u = `http://webcast-bytedance-com.openapi.dyc.ivolces.com/api/live_data/task/get?roomid=1&appid=${hub.appid}&msg_type=live_comment`;
  fetch(u, { signal: AbortSignal.timeout(8000) })
    .then(async (r) => console.log(new Date().toISOString(), `[内网OpenAPI探测] HTTP ${r.status}：${(await r.text()).slice(0, 300)}`))
    .catch((e) => console.log(new Date().toISOString(), `[内网OpenAPI探测] 不通：${e.cause?.code || e.message}`));
}
