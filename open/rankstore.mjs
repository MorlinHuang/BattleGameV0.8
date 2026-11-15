// 查手机 · 全服榜的两种存储（open/rank.mjs 用）。接口一样：
//   load({week, month, lastMonth, top, keep}) → 榜（{v, week, month, last, streak}）或 null（还没有存档）
//   save(db, batch) → 写回 batch 里变了的那些条（Map 文档号 → {b, k, id, o}），返回没写进去的那部分（Map）
//   seen(局号) → 这一局报过没有（没报过顺手记上）
// FileStore：本地开发，整张榜一个 JSON 文件。CloudStore：抖音云「云数据库」（文档型，组件中心开通），
//   集合 csj_rank 一人一条（w|周|人 = 本周、m|月|人 = 本月、s|人 = 连胜），集合 csj_round 记报过的局。
import fs from 'node:fs';

export class FileStore {
  constructor(file) { this.file = file; this.name = '文件 ' + file; this.rounds = new Set(); this.roundQ = []; }
  async load() {
    try { const d = JSON.parse(fs.readFileSync(this.file, 'utf8')); return d.v === 1 ? d : null; }
    catch (e) { if (e.code === 'ENOENT') return null; throw new Error(`全服榜存档读不出（${this.file}）：${e.message}`); }
  }
  async save(db, batch) {
    try { fs.writeFileSync(this.file + '.tmp', JSON.stringify(db)); fs.renameSync(this.file + '.tmp', this.file); return new Map(); }
    catch { return batch; }
  }
  async seen(rk) {
    if (this.rounds.has(rk)) return true;
    this.rounds.add(rk); this.roundQ.push(rk);
    if (this.roundQ.length > 5000) this.rounds.delete(this.roundQ.shift());
    return false;
  }
}

const PAGE = 100, PAR = 8;
export class CloudStore {
  constructor(db) { this.db = db; this.name = '抖音云云数据库'; this.rank = db.collection('csj_rank'); this.round = db.collection('csj_round'); }
  // 按条件分页读全（每页 PAGE 条，按分数从高到低，最多 max 条）
  async all(where, field, max) {
    const out = [];
    for (let skip = 0; skip < max; skip += PAGE) {
      const { data } = await this.rank.where(where).orderBy(field, 'desc').skip(skip).limit(Math.min(PAGE, max - skip)).get();
      out.push(...data);
      if (data.length < PAGE) break;
    }
    return out;
  }
  async load({ week, month, lastMonth, top, keep }) {
    const [w, m, s, l] = await Promise.all([this.all({ b: 'w', k: week }, 'v', keep), this.all({ b: 'm', k: month }, 'v', keep), this.all({ b: 's' }, 'n', keep), this.all({ b: 'm', k: lastMonth }, 'v', top)]);
    const map = (L, f) => Object.fromEntries(L.map((e) => [e.id, { [f]: e[f], name: e.name, av: e.av, side: e.side }]));
    return { v: 1, week: { key: week, m: map(w, 'v') }, month: { key: month, m: map(m, 'v') }, streak: { m: map(s, 'n') },
      last: { key: l.length ? lastMonth : '', top: l.map((e) => ({ id: e.id, name: e.name, av: e.av, side: e.side, v: e.v })) } };
  }
  async save(db, batch) {
    const failed = new Map(), list = [...batch];
    const one = async ([key, { b, k, id, o }]) => {
      try {
        if (!o) await this.rank.doc(key).remove();
        else await this.rank.doc(key).set(b === 's' ? { b, id, n: o.n, name: o.name, av: o.av || '', side: o.side } : { b, k, id, v: o.v, name: o.name, av: o.av || '', side: o.side });
      } catch (e) { failed.set(key, batch.get(key)); this.err = e.message; }
    };
    for (let i = 0; i < list.length; i += PAR) await Promise.all(list.slice(i, i + PAR).map(one));
    if (failed.size) console.log('[全服榜] 云数据库写入失败：' + this.err);
    return failed;
  }
  async seen(rk) {
    const ref = this.round.doc('r|' + rk), { data } = await ref.get();
    if (data.length) return true;
    await ref.set({ t: Date.now() });
    return false;
  }
}
