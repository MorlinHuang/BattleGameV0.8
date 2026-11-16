// 全网总榜 · 服务器这一侧（抖音云，11-16）：所有直播间的周榜 / 月榜 / 省份榜 / 连胜 / 荣誉 / 城市积分记在同一份榜里，存 MongoDB。
//   POST /api/open/score  {room, ticket, batch:{id, ops}}  exe 报一批记账条目（../rankops.mjs）；batch.id 去重：同一批重报只记一次
//   GET  /api/open/rank?room=&ticket=&ver=  取整份榜（exe 当本地镜像）；ver 没变回 304
// 记账规则和 exe 本地是同一段代码（boards.mjs / medals.mjs / rankops.mjs）。实例数固定 1 个：榜在内存里，每批记完落盘。
// 存储：
//   kv     {_id:'boards', json}               周榜 / 月榜 / 上一期 / 荣誉榜（Boards.toJSON 的 JSON 字符串，一份文档）
//   medals {_id:观众, season, json}            城市积分一人一条（{name, avatar, p, g} 的 JSON 字符串），只读当季的；换季后旧季的删掉
//   榜里的键是观众 id / 昵称，可能带「.」「$」，MongoDB 4.0 的字段名不收，所以整块存成字符串
//   batches {_id:批次 id, room, at, n}         记过的批次（去重），留 30 天
//   kv     {_id:'room:直播间', json}          这个直播间自己的省份夺冠 / 连胜（见下）
// 省份榜（最美省份榜、省份连胜榜）不跨直播间合并，各直播间只看自己的：官方准入规则不许拿真实地区做跨直播间的异步对抗
// （docs/抖音提审下一步与合规自查_1106.md 第 9 条）。服务器替每个直播间单独记（'s' 条目），取榜时把这个直播间自己的那份换进去。
// 跨直播间合并的只有按「人」算的：周榜 / 月榜 / 上一期 / 荣誉 / 城市积分。
// 没配 MongoDB（本地测试）就只在内存里记。
import { gzipSync } from 'node:zlib';
import { Boards } from '../boards.mjs';
import { Medals } from '../medals.mjs';
import { cleanOp, applyOps } from '../rankops.mjs';

const BATCH_KEEP_DAYS = 30;
const MAX_OPS = 50000;
const LAUNCH_KEEP = 2 * 86400e3; // 服务重启后读回多久以内启动过的直播间（直播伴侣的启动 token 本来 30 分钟就过期，一场直播一般不超过一天）

// 内存存储（本地测试 / 没配数据库）
export class MemoryRankDB {
  constructor() { this.boards = null; this.medals = new Map(); this.batches = new Set(); this.rooms = new Map(); }
  async load() { return { boards: this.boards, medalDocs: [...this.medals.values()], rooms: [...this.rooms].map(([room, json]) => ({ room, data: JSON.parse(json) })) }; }
  async saveRoom(room, data) { this.rooms.set(room, JSON.stringify(data)); }
  async saveLaunch(x) { (this.launchMap ||= new Map()).set(x.anchor.openId, { ...x, at: Date.now() }); }
  async loadLaunches(since) { return [...(this.launchMap?.values() || [])].filter((x) => x.at >= since); }
  async claim(id) { if (this.batches.has(id)) return false; this.batches.add(id); return true; }
  async save({ boards, medalDocs, dropKeys, season }) {
    this.boards = JSON.parse(JSON.stringify(boards));
    for (const d of medalDocs) this.medals.set(d._id, JSON.parse(JSON.stringify(d)));
    for (const k of dropKeys) this.medals.delete(k);
    for (const [k, d] of this.medals) if (d.season !== season) this.medals.delete(k);
  }
}

// MongoDB（抖音云组件：开通后平台把 MONGO_ADDRESS / MONGO_USERNAME / MONGO_PASSWORD 注入环境变量）
export class MongoRankDB {
  constructor({ url, dbName = 'foodpk', log = console.log }) { this.url = url; this.dbName = dbName; this.log = log; }
  async connect() {
    const { MongoClient } = await import('mongodb');
    this.client = new MongoClient(this.url, { serverSelectionTimeoutMS: 15000, maxPoolSize: 10 });
    await this.client.connect();
    const db = this.client.db(this.dbName);
    this.kv = db.collection('kv'); this.medals = db.collection('medals'); this.batches = db.collection('batches');
    await this.batches.createIndex({ at: 1 }, { expireAfterSeconds: BATCH_KEEP_DAYS * 86400 });
    await this.medals.createIndex({ season: 1 });
  }
  async load(season) {
    const b = await this.kv.findOne({ _id: 'boards' });
    const medalDocs = await this.medals.find({ season }).toArray();
    const rooms = (await this.kv.find({ _id: /^room:/ }).toArray()).map((d) => ({ room: d._id.slice(5), data: JSON.parse(d.json) }));
    return { rooms, boards: b?.json ? JSON.parse(b.json) : null, medalDocs: medalDocs.map((d) => ({ _id: d._id, season: d.season, ...JSON.parse(d.json || '{}') })) };
  }
  // 先占下批次号再记：重复的批次直接跳过（宁可进程在记的半路崩掉丢一批，也不重复记分）
  async claim(id, room, n) {
    try { await this.batches.insertOne({ _id: id, room, n, at: new Date() }); return true; }
    catch (e) { if (e.code === 11000) return false; throw e; }
  }
  async saveLaunch(x) { await this.kv.replaceOne({ _id: 'launch:' + x.anchor.openId }, { _id: 'launch:' + x.anchor.openId, json: JSON.stringify(x), at: new Date() }, { upsert: true }); }
  async loadLaunches(since) { return (await this.kv.find({ _id: /^launch:/, at: { $gte: new Date(since) } }).toArray()).map((d) => JSON.parse(d.json)); }
  async saveRoom(room, data) { await this.kv.replaceOne({ _id: 'room:' + room }, { _id: 'room:' + room, json: JSON.stringify(data), at: new Date() }, { upsert: true }); }
  async save({ boards, medalDocs, dropKeys, season, seasonChanged }) {
    await this.kv.replaceOne({ _id: 'boards' }, { _id: 'boards', json: JSON.stringify(boards), at: new Date() }, { upsert: true });
    const ops = medalDocs.map(({ _id, season, ...rest }) => ({ replaceOne: { filter: { _id }, replacement: { _id, season, json: JSON.stringify(rest) }, upsert: true } }));
    for (const k of dropKeys) ops.push({ deleteOne: { filter: { _id: k } } });
    for (let i = 0; i < ops.length; i += 1000) await this.medals.bulkWrite(ops.slice(i, i + 1000), { ordered: false });
    if (seasonChanged) await this.medals.deleteMany({ season: { $ne: season } });
  }
}

// MONGO_URL 直接给完整连接串；否则按抖音云注入的三个变量拼（官方示例写法）。地址里没带参数就补 authSource=admin（root 账号建在 admin 库）
export function mongoUrlFromEnv(env = process.env) {
  if (env.MONGO_URL) return env.MONGO_URL;
  const { MONGO_ADDRESS: addr, MONGO_USERNAME: user, MONGO_PASSWORD: pass } = env;
  if (!addr) return '';
  const raw = addr.trim();
  if (!user && /^mongodb:\/\/[^/]*@/.test(raw)) return raw; // 整条连接串（自带账号密码）
  const auth = user ? `${encodeURIComponent(user)}:${encodeURIComponent(pass || '')}@` : '';
  const host = raw.replace(/^mongodb:\/\//, '').replace(/^[^/]*@/, ''); // 控制台「私网地址」整段照抄过来的，去掉里面的 <user>:<password>@
  return `mongodb://${auth}${host}${host.includes('/') ? '' : '/?authSource=admin'}`;
}

export class RankStore {
  constructor({ db = new MemoryRankDB(), log = console.log } = {}) {
    this.db = db; this.log = log;
    this.clock = { t: Date.now() };
    const now = () => this.clock.t;
    this.boards = new Boards({}, now); this.medals = new Medals({}, now);
    this.ver = 0; this.boot = Math.random().toString(36).slice(2, 8);
    this.chain = Promise.resolve(); // 一批一批地记，不交叉
    this.ready = false; this.mirror = null;
    this.rooms = new Map(); // 直播间 → 只记省份的 Boards
    this.roomGz = new Map(); // 直播间 → {ver, gz}：取榜的压缩结果
  }
  room(id) { let b = this.rooms.get(id); if (!b) this.rooms.set(id, (b = new Boards({}, () => this.clock.t))); return b; }
  async init() {
    const season = this.medals.season;
    const { boards, medalDocs, rooms = [] } = await this.db.load(season);
    const now = () => this.clock.t;
    this.boards = new Boards(boards || {}, now);
    for (const r of rooms) this.rooms.set(r.room, new Boards(r.data, now));
    this.launches = await this.db.loadLaunches(Date.now() - LAUNCH_KEEP); // 交给 hub.restore
    const players = {};
    for (const d of medalDocs) if (d.season === season) players[d._id] = { name: d.name, avatar: d.avatar, p: d.p || {}, g: d.g || {} };
    this.medals = new Medals({ season, players }, now);
    this.ready = true;
    this.log(`[总榜] 已读入：周榜 ${Object.keys(this.boards.week.players).length} 人、月榜 ${Object.keys(this.boards.month.players).length} 人、城市积分 ${medalDocs.length} 人（${season}）`);
  }
  // 直播间启动信息（主播 openId → 直播间），见 hub.restore
  saveLaunch(x) { return this.ready ? this.db.saveLaunch(x) : Promise.resolve(); }
  get tag() { return `${this.boot}.${this.ver}`; }

  // 一批：返回 {ok, dup, n}
  report(room, batch) {
    const run = this.chain.then(() => this.apply(room, batch));
    this.chain = run.catch(() => {});
    return run;
  }
  async apply(room, batch) {
    if (!this.ready) throw new Error('总榜还没准备好');
    const id = String(batch?.id || '');
    if (!/^[\w-]{8,64}$/.test(id)) throw new Error('批次号不对');
    if (!Array.isArray(batch.ops) || batch.ops.length > MAX_OPS) throw new Error('批次内容不对');
    const ops = batch.ops.map(cleanOp).filter(Boolean);
    if (!(await this.db.claim(id, String(room), ops.length))) return { ok: true, dup: true, n: 0, ver: this.tag };
    const season = this.medals.season;
    const touched = new Set();
    for (const o of ops) if (o.t === 'm') for (const g of o.gains) touched.add(g.key);
    const before = new Set(Object.keys(this.medals.players));
    const mine = ops.filter((o) => o.t === 's'), shared = ops.filter((o) => o.t !== 's');
    applyOps(this.boards, this.medals, shared, this.clock);
    const rb = this.room(String(room));
    if (mine.length) applyOps(rb, this.medals, mine, this.clock);
    this.boards.roll(); this.medals.roll(); rb.roll();
    const seasonChanged = this.medals.season !== season;
    const players = this.medals.players;
    const dropKeys = seasonChanged ? [] : [...before].filter((k) => !players[k]); // 人数超上限被删掉的
    const medalDocs = [...touched].filter((k) => players[k]).map((k) => ({ _id: k, season: this.medals.season, ...players[k] }));
    await this.db.save({ boards: this.boards.toJSON(), medalDocs, dropKeys, season: this.medals.season, seasonChanged });
    if (mine.length) await this.db.saveRoom(String(room), { week: rb.week, month: rb.month });
    this.ver++; this.mirror = null;
    this.log(`[总榜] 直播间 ${room} 报上 ${ops.length} 条（批次 ${id.slice(0, 8)}）→ 周榜 ${Object.keys(this.boards.week.players).length} 人 · 版本 ${this.tag}`);
    return { ok: true, dup: false, n: ops.length, ver: this.tag };
  }

  // 整份榜（gzip 好的 JSON）：人的榜全网一份，省份夺冠 / 连胜换成这个直播间自己的。同一直播间同一版本只压一次
  snapshot(room = '') {
    this.clock.t = Math.max(this.clock.t, Date.now());
    const before = `${this.boards.week.id}|${this.boards.month.id}|${this.medals.season}`;
    this.boards.roll(); this.medals.roll();
    if (`${this.boards.week.id}|${this.boards.month.id}|${this.medals.season}` !== before) { this.ver++; this.mirror = null; this.roomGz.clear(); } // 换周 / 换月 / 换季也算新版本
    this.mirror ||= { boards: this.boards.toJSON(), medals: this.medals.toJSON() };
    const hit = this.roomGz.get(room);
    if (hit?.ver === this.tag) return hit;
    const rb = this.rooms.get(room);
    if (rb) rb.roll();
    const own = (g, r) => ({ ...g, provs: r && r.id === g.id ? r.provs : {}, streak: r && r.id === g.id ? r.streak : {} });
    const boards = { ...this.mirror.boards, week: own(this.mirror.boards.week, rb?.week), month: own(this.mirror.boards.month, rb?.month) };
    const body = JSON.stringify({ ver: this.tag, at: Date.now(), boards, medals: this.mirror.medals });
    const out = { ver: this.tag, gz: gzipSync(body), size: body.length };
    this.roomGz.delete(room); this.roomGz.set(room, out);
    if (this.roomGz.size > 64) this.roomGz.delete(this.roomGz.keys().next().value); // 只留最近 64 个直播间的
    return out;
  }
}
