// 查手机 · 「历史第一次」台账（11-18 用户：关注主播、第一次获得灯牌只认这个观众在这个主播这里的历史第一次，不是每局一次）。
// 键 = 类别|主播|观众：类别 follow / fans；主播 = 主播 openId（模拟模式没有 openId，用直播间号）；观众 = sec_openid（没有就用昵称）。
// claim() 同步判定（推送进来当场要给事件打 first 标记），存储在后面慢慢写：
//   FileStore：本地开发，整本台账一个 JSON 文件，启动时全读进来；
//   CloudStore：抖音云云数据库集合 csj_first（一条一个键），主播从直播伴侣启动玩法时（hub.launch）把他名下的读进内存。
import fs from 'node:fs';

export class FirstBook {
  constructor(store, log = console.log) { this.store = store; this.log = log; this.keys = new Set(); this.ready = new Set(); }
  flush() { this.store.flush?.(); }
  async init() { if (this.store.loadAll) for (const k of await this.store.loadAll()) this.keys.add(k); }
  /* 主播开播：把他名下的记录读进来（文件存储启动时已经全读，这里什么都不做） */
  async open(anchor) {
    if (!this.store.loadAnchor || this.ready.has(anchor)) return;
    try { for (const k of await this.store.loadAnchor(anchor)) this.keys.add(k); this.ready.add(anchor); }
    catch (e) { this.log(`[历史首次] 读主播 ${anchor} 的台账失败：${e.message}`); }
  }
  /* 这个观众在这个主播这里是不是第一次做这件事；是就记上（之后都返回 false） */
  claim(kind, anchor, viewer) {
    const key = `${kind}|${anchor}|${viewer}`;
    if (this.keys.has(key)) return false;
    this.keys.add(key);
    this.store.add(key, anchor, this.keys).catch((e) => this.log(`[历史首次] 写台账失败（${key}）：${e.message}`));
    return true;
  }
}

export class FirstFileStore {
  constructor(file) { this.file = file; this.timer = null; }
  async loadAll() {
    try { const d = JSON.parse(fs.readFileSync(this.file, 'utf8')); return d.v === 1 && Array.isArray(d.keys) ? d.keys : []; }
    catch (e) { if (e.code === 'ENOENT') return []; throw new Error(`历史首次台账读不出（${this.file}）：${e.message}`); }
  }
  /* 整本重写：攒 1 秒写一次（tmp + rename） */
  async add(key, anchor, keys) {
    this.keysRef = keys;
    if (!this.timer) this.timer = setTimeout(() => this.flush(), 1000);
  }
  flush() {
    clearTimeout(this.timer); this.timer = null;
    if (!this.keysRef) return;
    fs.writeFileSync(this.file + '.tmp', JSON.stringify({ v: 1, keys: [...this.keysRef] })); fs.renameSync(this.file + '.tmp', this.file);
  }
}

const PAGE = 100;
export class FirstCloudStore {
  constructor(db) { this.col = db.collection('csj_first'); }
  async loadAnchor(anchor) {
    const out = [];
    for (let skip = 0; ; skip += PAGE) {
      const { data } = await this.col.where({ a: anchor }).skip(skip).limit(PAGE).get();
      for (const d of data) out.push(d.key);
      if (data.length < PAGE) return out;
    }
  }
  async add(key, anchor) { await this.col.doc(key).set({ key, a: anchor, t: Date.now() }); }
}
