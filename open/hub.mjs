// 抖音直播小玩法 · 开发者服务端：收官方推送、管直播间推送任务、把事件转给玩法客户端。
//
//   玩法客户端（exe）被直播伴侣用 `-token=xxx` 启动 → POST /api/open/launch {token}
//     → 本服务用 appid/AppSecret 换 access_token → 用启动 token 换直播间信息（room_id、主播昵称头像）
//     → 对评论 / 礼物 / 点赞各启动一个推送任务 → 回 {roomId, anchor, ticket}
//   官方推送 → POST /api/open/push（校验签名 → 按 msg_id 去重 → 转成统一事件）
//   部署在抖音云（cloud 模式）时，官方推送走内网专线 → POST /api/open/cloudpush：不带签名，带 x-anchor-openid / x-tt-source；
//     这个路径不在抖音云「外网入流量」的授权路径里，外网打不进来（授权只给 launch / stop / events）
//     → 本进程里订阅了这个直播间的游戏（网页版/本地开发）直接收到；
//     → exe 用 GET /api/open/events?room=&ticket=&since=&boot= 长连接收（Server-Sent Events，断线带 since 续上，不丢不重）
//       seq 只在本进程内有效：服务端重启后从 1 重数，exe 带的 boot 和本进程不同就从头补发缓存（否则旧 since 会把新消息全挡掉）
//   礼物另外每分钟查一次「推送失败数据」补回来；收到 / 处理完的礼物按官方建议做履约上报。
//
// 没配置 appid/AppSecret = 模拟模式：只有本地「演练」和测试脚本发来的模拟推送（格式、签名和官方一模一样，走同一条校验路径）。
// 统一事件：{ seq, roomId, msgType, msgId, type:'chat'|'gift'|'like', user:{id,name,avatar}, content, giftId, magicGiftId, count, value, test, at, source }
import fs from 'node:fs';
import { EventEmitter } from 'node:events';
import { createHash, createHmac, randomBytes, randomUUID, timingSafeEqual } from 'node:crypto';
import { OpenApi, MSG_TYPES } from './api.mjs';
import { pushSignature, verifyPush, selfTest } from './sign.mjs';

// live_follow：服务端推送文档里没有这一类（只有客户端插件 API 有「关注状态」），先认上，平台以后推过来就能用
const TYPE = { live_comment: 'chat', live_gift: 'gift', live_like: 'like', live_fansclub: 'fansclub', live_follow: 'follow' };
const SEEN_MAX = 20000, BUF_MAX = 600;
export const DEV_PUSH_SECRET = 'foodpk-dev-push-secret'; // 只在模拟模式用；正式推送秘钥在配置文件里

// 配置：文件（JSON：{appid, appSecret, pushSecret}）+ 环境变量 DOUYIN_APPID / DOUYIN_APP_SECRET / DOUYIN_PUSH_SECRET 覆盖。仓库里不放真值
export function loadOpenConfig(file) {
  let c = {};
  if (file) try { c = JSON.parse(fs.readFileSync(file, 'utf8')); } catch (e) { if (e.code !== 'ENOENT') throw new Error(`读不了 ${file}：${e.message}`); }
  const env = process.env;
  return { appid: env.DOUYIN_APPID || c.appid || '', appSecret: env.DOUYIN_APP_SECRET || c.appSecret || '', pushSecret: env.DOUYIN_PUSH_SECRET || c.pushSecret || '', cloud: env.DOUYIN_CLOUD === '1' || c.cloud === true };
}

export class OpenHub extends EventEmitter {
  constructor({ appid = '', appSecret = '', pushSecret = '', cloud = false, log = console.log, api = null } = {}) {
    super();
    if (!selfTest()) throw new Error('推送签名算法自检没过（官方测试向量不符）');
    this.real = !!(appid && appSecret);
    this.cloud = !!cloud;
    if (this.real && !this.cloud && !pushSecret) throw new Error('正式模式要配置推送秘钥 pushSecret（后台「直播间互动数据配置」里填的那个）');
    this.appid = appid;
    this.pushSecret = pushSecret || (this.real ? '' : DEV_PUSH_SECRET); // 正式模式没配推送秘钥（抖音云内网推送用不到）= 外网签名推送一律不收
    this.ticketKey = createHash('sha256').update('foodpk-ticket\0' + (appSecret || this.pushSecret)).digest();
    this.log = log;
    this.api = this.real ? api || new OpenApi({ appid, appSecret, log }) : null;
    this.rooms = new Map();
    this.anchorRooms = new Map(); // 主播 openId → 直播间号（内网推送只带主播 openId）
    this.boot = randomUUID().slice(0, 8); // 本进程的序号纪元
    this.acks = new Map(); // roomId → {1: [], 2: []}
    this.timer = setInterval(() => this.maintain(), 60e3).unref();
    this.ackTimer = setInterval(() => this.flushAcks(), 1000).unref();
  }

  get mode() { return this.real ? 'live' : 'mock'; }
  room(id) {
    id = String(id);
    let r = this.rooms.get(id);
    if (!r) this.rooms.set(id, (r = { id, anchor: null, tasks: {}, seen: new Set(), seenQ: [], buf: [], seq: 0, subs: new Set(), real: this.real && !id.startsWith('mock-'), active: Date.now(), failChecked: 0 }));
    return r;
  }
  ticket(roomId) { return createHmac('sha256', this.ticketKey).update(String(roomId)).digest('base64url').slice(0, 32); }
  checkTicket(roomId, t) { const a = Buffer.from(String(t || '')), b = Buffer.from(this.ticket(roomId)); return a.length === b.length && timingSafeEqual(a, b); }

  // 启动 token → 直播间 + 开推送任务。模拟模式：任何 token 都给一个固定的模拟直播间
  async launch(token) {
    token = String(token || '').trim();
    if (!token) throw new Error('没有启动参数 token（要从直播伴侣启动玩法）');
    if (!this.real) {
      const r = this.room('mock-' + createHash('sha256').update(token).digest('hex').slice(0, 10));
      r.anchor = { openId: '', name: '模拟主播', avatar: '' };
      for (const t of MSG_TYPES) r.tasks[t] = '模拟';
      return this.summary(r);
    }
    const info = await this.api.roomInfo(token);
    const r = this.room(info.roomId);
    r.anchor = info.anchor; r.active = Date.now();
    if (r.anchor.openId) this.anchorRooms.set(r.anchor.openId, r.id);
    await this.startTasks(r);
    this.log(`[直播间] ${r.id} ${r.anchor.name} 已启动推送：${JSON.stringify(r.tasks)}`);
    return this.summary(r);
  }
  async startTasks(r) {
    await Promise.all(MSG_TYPES.map(async (t) => {
      try { await this.api.startTask(r.id, t); r.tasks[t] = '运行中'; } catch (e) { r.tasks[t] = e.message; }
    }));
  }
  async stop(roomId) {
    const r = this.rooms.get(String(roomId));
    if (!r) return;
    if (r.real) await Promise.all(MSG_TYPES.map((t) => this.api.stopTask(r.id, t).catch((e) => this.log(e.message))));
    for (const t of MSG_TYPES) r.tasks[t] = '已停止';
  }
  summary(r) { return { roomId: r.id, anchor: r.anchor, tasks: { ...r.tasks }, real: r.real, ticket: this.ticket(r.id), boot: this.boot }; }

  // 订阅一个直播间的事件：fn(event) 的返回值会带回给 ingest 的调用方（演练要知道计没计上）
  subscribe(roomId, fn) {
    const r = this.room(roomId);
    r.subs.add(fn); r.active = Date.now();
    return () => r.subs.delete(fn);
  }

  // 一次推送：headers 是小写头名的对象，raw 是 HTTP body 原文。返回 {code, ok, why, accepted, dup, results}
  // viaCloud：抖音云内网专线推来的（不签名；直播间按 x-roomid，没有就按 x-anchor-openid 找 launch 时记下的直播间）
  ingest(headers, raw, { viaCloud = false } = {}) {
    const msgType = String(headers['x-msg-type'] || '');
    const roomId = String(headers['x-roomid'] || (viaCloud && this.anchorRooms.get(String(headers['x-anchor-openid'] || ''))) || '');
    if (!viaCloud && !verifyPush(headers, raw, this.pushSecret)) return { code: 401, ok: false, why: '签名不对' };
    if (!TYPE[msgType] || !roomId) return { code: 400, ok: false, why: viaCloud ? '不认识的推送类型或找不到主播对应的直播间' : '不认识的推送类型或缺 x-roomid' };
    let items;
    try { items = JSON.parse(raw); } catch { return { code: 400, ok: false, why: 'body 不是 JSON' }; }
    if (!Array.isArray(items)) return { code: 400, ok: false, why: 'body 应该是数组' };
    return { code: 200, ok: true, ...this.accept(roomId, msgType, items, 'push') };
  }

  accept(roomId, msgType, items, source) {
    const r = this.room(roomId), out = { accepted: 0, dup: 0, results: [] };
    const now = Date.now();
    for (const it of items) {
      const msgId = String(it?.msg_id || '');
      if (!msgId) continue;
      if (r.seen.has(msgId)) { out.dup++; continue; } // 官方：消息可能重复，按 msg_id 去重
      r.seen.add(msgId); r.seenQ.push(msgId);
      if (r.seenQ.length > SEEN_MAX) r.seen.delete(r.seenQ.shift());
      const ev = {
        seq: ++r.seq, roomId: r.id, msgType, msgId, type: TYPE[msgType], source, at: +it.timestamp || now,
        user: { id: String(it.sec_openid || ''), name: String(it.nickname || '观众'), avatar: String(it.avatar_url || '') },
        content: msgType === 'live_comment' ? String(it.content || '') : '',
        giftId: it.sec_gift_id || '', magicGiftId: it.sec_magic_gift_id || '',
        count: Math.max(1, Math.floor(+(msgType === 'live_like' ? it.like_num : it.gift_num) || 1)),
        value: +it.gift_value || 0, test: it.test === true,
        reason: +it.fansclub_reason_type || 0, level: +it.fansclub_level || 0,
      };
      r.buf.push(ev); if (r.buf.length > BUF_MAX) r.buf.shift();
      out.accepted++;
      if (msgType === 'live_gift' && r.real) this.queueAck(r.id, 1, { msgId, msgType, at: now });
      for (const fn of r.subs) { try { out.results.push(fn(ev)); } catch (e) { this.log('处理推送出错：' + e.message); } }
      if (msgType === 'live_gift' && r.real && r.subs.size) this.queueAck(r.id, 2, { msgId, msgType, at: Date.now() });
    }
    if (out.accepted) r.active = now;
    return out;
  }

  // 本地演练 / 测试脚本：造一条和官方格式一样的推送（含签名），badSign 时故意签错
  mockPush(roomId, msgType, item, { badSign = false } = {}) {
    const raw = JSON.stringify([{ msg_id: item.msg_id || randomUUID().replace(/-/g, '').slice(0, 19), timestamp: Date.now(), ...item }]);
    const headers = { 'x-nonce-str': randomBytes(8).toString('hex'), 'x-timestamp': String(Date.now()), 'x-roomid': String(roomId), 'x-msg-type': msgType, 'content-type': 'application/json' };
    headers['x-signature'] = pushSignature(headers, raw, badSign ? this.pushSecret + 'x' : this.pushSecret);
    return { headers, raw };
  }

  queueAck(roomId, type, item) {
    const q = this.acks.get(roomId) || this.acks.set(roomId, { 1: [], 2: [] }).get(roomId);
    q[type].push(item);
  }
  flushAcks() {
    if (!this.real) return;
    for (const [roomId, q] of this.acks) for (const type of [1, 2]) {
      const items = q[type].splice(0, 100);
      if (items.length) this.api.ack(roomId, type, items).catch((e) => this.log('履约上报：' + e.message));
    }
  }

  // 每分钟：有人在收的正式直播间——推送任务不在运行就重开；礼物查一次推送失败数据补回来；半小时没动静的直播间清掉
  async maintain() {
    const now = Date.now();
    for (const r of this.rooms.values()) {
      if (!r.subs.size && now - r.active > 30 * 60e3) { this.rooms.delete(r.id); this.acks.delete(r.id); if (r.anchor?.openId && this.anchorRooms.get(r.anchor.openId) === r.id) this.anchorRooms.delete(r.anchor.openId); continue; }
      if (!r.real || !r.subs.size) continue;
      for (const t of MSG_TYPES) {
        try { const st = await this.api.taskStatus(r.id, t); if (st !== 3) { await this.api.startTask(r.id, t); this.log(`[直播间] ${r.id} ${t} 任务状态 ${st}，已重开`); } r.tasks[t] = '运行中'; }
        catch (e) { r.tasks[t] = e.message; }
      }
      try {
        for (let page = 1; page <= 10; page++) {
          const d = await this.api.failData(r.id, 'live_gift', page);
          for (const row of d.data_list || []) { let items = []; try { items = JSON.parse(row.payload); } catch { /* 坏数据跳过 */ } if (Array.isArray(items)) this.accept(r.id, 'live_gift', items, 'fail'); }
          if (!d.data_list?.length || page * 100 >= (d.total_count || 0)) break;
        }
      } catch (e) { this.log(e.message); }
    }
  }

  // ---------- HTTP：/api/open/* ----------
  async handle(req, res, url) {
    const p = url.pathname;
    if (!p.startsWith('/api/open/')) return false;
    const json = (code, o) => { res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }); res.end(JSON.stringify(o)); };
    const readRaw = () => new Promise((ok, bad) => { const chunks = []; let n = 0; req.on('data', (d) => { n += d.length; if (n > 2e6) { bad(new Error('太大')); req.destroy(); } else chunks.push(d); }); req.on('end', () => ok(Buffer.concat(chunks).toString('utf8'))); req.on('error', bad); });
    try {
      if (p === '/api/open/push' && req.method === 'POST') {
        const r = this.ingest(req.headers, await readRaw());
        if (r.code !== 200) this.log(`[推送] 拒收：${r.why}（${req.headers['x-msg-type'] || '-'} ${req.headers['x-roomid'] || '-'}）`);
        return json(r.code, r.code === 200 ? { err_no: 0, accepted: r.accepted, dup: r.dup } : { err_no: r.code, err_msg: r.why }), true;
      }
      if (p === '/api/open/cloudpush' && req.method === 'POST' && this.cloud) {
        if (!req.headers['x-tt-source']) return json(403, { err_no: 403, err_msg: '不是抖音云内网推送' }), true;
        const r = this.ingest(req.headers, await readRaw(), { viaCloud: true });
        if (r.code !== 200) this.log(`[内网推送] 拒收：${r.why}（${req.headers['x-msg-type'] || '-'} ${req.headers['x-roomid'] || req.headers['x-anchor-openid'] || '-'}）`);
        return json(r.code, r.code === 200 ? { err_no: 0, accepted: r.accepted, dup: r.dup } : { err_no: r.code, err_msg: r.why }), true;
      }
      if (p === '/api/open/launch' && req.method === 'POST') {
        let b = {};
        try { b = JSON.parse(await readRaw() || '{}'); } catch { return json(400, { error: '不是合法 JSON' }), true; }
        return json(200, await this.launch(b.token)), true;
      }
      if (p === '/api/open/stop' && req.method === 'POST') {
        const b = JSON.parse(await readRaw() || '{}');
        if (!this.checkTicket(b.room, b.ticket)) return json(403, { error: '凭证不对' }), true;
        await this.stop(b.room);
        return json(200, { ok: true }), true;
      }
      if (p === '/api/open/events' && req.method === 'GET') return this.stream(req, res, url), true;
      return json(404, { error: '没有这个接口' }), true;
    } catch (e) { return json(400, { error: e.message }), true; }
  }

  // Server-Sent Events：exe 收直播间事件。since = 上次收到的最后一个 seq（-1 = 从现在开始），boot = 那个 seq 所属的服务端进程
  stream(req, res, url) {
    const roomId = url.searchParams.get('room') || '', boot = url.searchParams.get('boot');
    const since = boot && boot !== this.boot ? 0 : Number(url.searchParams.get('since') ?? -1);
    if (!this.checkTicket(roomId, url.searchParams.get('ticket'))) { res.writeHead(403); return res.end(); }
    const r = this.room(roomId);
    res.writeHead(200, { 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no' });
    const send = (ev) => res.write(`id: ${ev.seq}\ndata: ${JSON.stringify(ev)}\n\n`);
    res.write(`event: room\ndata: ${JSON.stringify({ ...this.summary(r), seq: r.seq })}\n\n`);
    if (since >= 0) for (const ev of r.buf) if (ev.seq > since) send(ev);
    const off = this.subscribe(roomId, (ev) => { send(ev); return { ok: true, relayed: true }; });
    const ka = setInterval(() => res.write(': ping\n\n'), 15e3);
    req.on('close', () => { off(); clearInterval(ka); });
  }
}
