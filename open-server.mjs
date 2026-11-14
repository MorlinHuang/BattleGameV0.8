// 查手机 · 直播小玩法开发者服务端（照美食大赛 / 墨娃快跑）：收官方推送（评论 / 礼物 / 点赞 / 粉丝团）、管直播间推送任务、把事件转给直播画面。
// 接口在 open/hub.mjs：POST /api/open/launch {token} · POST /api/open/push（官方推送）· GET /api/open/events（SSE）· POST /api/open/stop
// 全服榜：GET /api/open/rank/board?room=&ticket= · POST /api/open/rank/report {room, ticket, round, winner, list}（open/rank.mjs，存 data/rank-global.json）
// 本文件另加：GET /api/open/gifts（礼物映射表，open/gifts.mjs）· POST /api/open/mock（只在模拟模式：演练一条推送，走和官方一样的验签路径）· GET /api/health
//
// 用法：node server/open-server.mjs [端口=41004] [--host=127.0.0.1] [--open-config=配置文件]
//   配置 JSON {appid, appSecret, pushSecret, cloud, selftest}（cloud=部署在抖音云、推送走内网 /api/open/cloudpush；selftest=后台自测工具的模拟数据转给正连着的直播间，只在测试环境开），默认 server/data/open.json（不进包、不进仓库）；或环境变量 DOUYIN_APPID / DOUYIN_APP_SECRET / DOUYIN_PUSH_SECRET。
//   没配 appid = 模拟模式：任何启动 token 都给一个模拟直播间（mock-<sha256(token) 前 10 位>）。
// 本地开发：只听 127.0.0.1:41004，由 web/serve.py 把 :31004/api/open/* 转进来（31001~31020 端口都已占满）。
// 正式上线：部署到抖音云（只能听 8000、要 GET /v1/ping），或放到有备案域名的 https 反代后面——推送地址必须 https。
import http from 'node:http';
import path from 'node:path';
import { OpenHub, loadOpenConfig } from './open/hub.mjs';
import { table, findGift, FEN_PER_DIAMOND } from './open/gifts.mjs';
import { GlobalRank } from './open/rank.mjs';

const args = process.argv.slice(2);
const flag = (k) => args.find((a) => a.startsWith(`--${k}=`))?.slice(k.length + 3);
const port = +(args.find((a) => /^\d+$/.test(a)) || process.env.PORT || 41004);
const host = flag('host') || '127.0.0.1';
const here = path.dirname(new URL(import.meta.url).pathname);
const hub = new OpenHub({ ...loadOpenConfig(flag('open-config') || path.join(here, 'data', 'open.json')), log: (s) => console.log(new Date().toISOString().slice(11, 19), s) });

const log = (s) => console.log(new Date().toISOString().slice(11, 19), s);
const rank = new GlobalRank({ file: flag('rank-file') || path.join(here, 'data', 'rank-global.json'), log });
for (const sig of ['SIGTERM', 'SIGINT']) process.on(sig, () => { rank.flush(); process.exit(0); });
const json = (res, code, o) => { res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }); res.end(JSON.stringify(o)); };
const body = (req) => new Promise((ok) => { const c = []; req.on('data', (d) => c.push(d)); req.on('end', () => { try { ok(JSON.parse(Buffer.concat(c).toString() || '{}')); } catch { ok({}); } }); });
const viewer = (name) => ({ sec_openid: 'mock_' + Buffer.from(name).toString('hex').slice(0, 16), nickname: name, avatar_url: '' });

// 演练：{token, kind:'gift'|'chat'|'like', gift?, n?, text?, name?, test?}
async function mock(b) {
  if (hub.real) return [403, { error: '正式模式不收演练推送' }];
  const room = await hub.launch(b.token || 'local-dev'), name = String(b.name || '模拟观众'), n = Math.max(1, Math.floor(+b.n || 1));
  let msgType, item;
  if (b.kind === 'gift') {
    const g = findGift(b.gift);
    if (!g) return [400, { error: '没有这个礼物：' + b.gift }];
    msgType = 'live_gift'; item = { ...viewer(name), sec_gift_id: g.id, gift_num: n, gift_value: g.diamond * n * FEN_PER_DIAMOND, test: !!b.test };
  } else if (b.kind === 'chat') { msgType = 'live_comment'; item = { ...viewer(name), content: String(b.text ?? '') }; }
  else if (b.kind === 'like') { msgType = 'live_like'; item = { ...viewer(name), like_num: n }; }
  else if (b.kind === 'follow') { msgType = 'live_follow'; item = { ...viewer(name), follow_type: 1 }; }
  else return [400, { error: 'kind 只能是 gift / chat / like / follow' }];
  const { headers, raw } = hub.mockPush(room.roomId, msgType, item);
  const r = hub.ingest(headers, raw);
  return [r.code, { ...r, roomId: room.roomId }];
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  /* 跨域：直播画面在安装包的本机地址（http://127.0.0.1:随机端口）里跑，连的是这个服务端 —— 不同源，浏览器先发预检（美食大赛的连接在 Node 主进程里，没这一步） */
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (req.method === 'OPTIONS') { res.writeHead(204, { 'Access-Control-Allow-Methods': 'GET, POST', 'Access-Control-Allow-Headers': 'content-type', 'Access-Control-Max-Age': '86400' }); return res.end(); }
  try {
    if (url.pathname === '/api/open/gifts') return json(res, 200, table());
    if (url.pathname === '/api/open/mock' && req.method === 'POST') { const [c, o] = await mock(await body(req)); return json(res, c, o); }
    /* 全服榜（open/rank.mjs）：都要直播间凭证（launch 给的 ticket） */
    if (url.pathname === '/api/open/rank/board') {
      if (!hub.checkTicket(url.searchParams.get('room'), url.searchParams.get('ticket'))) return json(res, 403, { error: '凭证不对' });
      return json(res, 200, rank.board());
    }
    if (url.pathname === '/api/open/rank/report' && req.method === 'POST') {
      const b = await body(req);
      if (!hub.checkTicket(b.room, b.ticket)) return json(res, 403, { error: '凭证不对' });
      const r = rank.report(String(b.room), b);
      return json(res, r.ok ? 200 : 400, r.ok ? { ...r, board: rank.board() } : { error: r.why });
    }
    if (await hub.handle(req, res, url)) return;
    if (url.pathname === '/api/health' || url.pathname === '/v1/ping') return json(res, 200, { ok: true, mode: hub.mode });
  } catch (e) { return json(res, 500, { error: e.message }); }
  res.writeHead(404); res.end();
}).listen(port, host, () => console.log(`查手机开发者服务端 http://${host}:${port}/  ${hub.real ? '正式（appid ' + hub.appid + '）' : '模拟模式'}`));
