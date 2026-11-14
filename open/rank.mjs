// 查手机 · 全服榜（11-11，照熊猫：周榜 / 月榜 / 连胜都是服务端的一份，所有直播间共用；大哥入场只认全服名次）。
//   每局结算，直播画面把这一局每人拿到的积分报上来（POST /api/open/rank/report，凭 launch 给的直播间凭证）；
//   服务端按观众 openId 累计进本周榜、本月榜，赢的一边连胜 +1、输的清零。周一 0 点换周榜、每月 1 日 0 点换月榜（北京时间），上个月的前 100 名留着。
//   GET /api/open/rank/board 给直播画面：周榜 / 月榜 / 连胜榜前 100 名 + 大哥名单 vip（openId → [名次, 哪张榜]）。
//   大哥名次（熊猫 BigBrotherEnterManager.GetMiniRank）：本月榜、本周榜、上月榜三个名次里最好的那个，前 100 名才算；
//     另加一条：那张榜上的积分要满 VIP_MIN（积分约等于 1400 钻的礼物；开服头几周榜上不满 100 人，不加这条就是谁上过榜谁是大哥）。
// 存一个 JSON 文件（改动后几秒落盘、先写临时文件再改名）。上抖音云多实例时把 load / flush 换成云数据库，别的不动。
import fs from 'node:fs';

const TOP = 100, KEEP = 20000, VIP_MIN = 100000, ROUND_MAX = 5000, V_MAX = 1e9;
const pad = (n) => String(n).padStart(2, '0');
const bj = (now) => new Date(now + 8 * 3600e3);                     // 用 UTC 读数当北京时间
const dayKey = (d) => `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;
export const monthKey = (now) => { const d = bj(now); return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}`; };
export const weekKey = (now) => { const d = bj(now); d.setUTCDate(d.getUTCDate() - (d.getUTCDay() + 6) % 7); return dayKey(d); };
const bare = (o) => Object.assign(Object.create(null), o);
const str = (s, n) => String(s ?? '').slice(0, n);

export class GlobalRank {
  constructor({ file = '', log = () => {}, now = () => Date.now() } = {}) {
    this.file = file; this.log = log; this.now = now;
    this.db = { v: 1, week: { key: '', m: bare() }, month: { key: '', m: bare() }, last: { key: '', top: [] }, streak: { m: bare() } };
    this.rounds = new Set(); this.roundQ = [];
    this.cache = null; this.dirty = false; this.timer = null;
    if (file) try {
      const d = JSON.parse(fs.readFileSync(file, 'utf8'));
      if (d.v === 1) { this.db = d; for (const b of [d.week, d.month, d.streak]) b.m = bare(b.m); }
    } catch (e) { if (e.code !== 'ENOENT') log('[全服榜] 存档读不出，从空榜开始：' + e.message); }
    this.roll();
  }
  sorted(m, val) { return Object.entries(m).filter(([, o]) => val(o) > 0).sort((a, b) => val(b[1]) - val(a[1])); }
  roll() {
    const t = this.now(), wk = weekKey(t), mk = monthKey(t), d = this.db;
    if (d.week.key !== wk) { d.week = { key: wk, m: bare() }; this.touch(); }
    if (d.month.key !== mk) {
      if (d.month.key) d.last = { key: d.month.key, top: this.sorted(d.month.m, (o) => o.v).slice(0, TOP).map(([id, o]) => ({ id, name: o.name, av: o.av, side: o.side, v: o.v })) };
      d.month = { key: mk, m: bare() }; this.touch();
    }
  }
  touch() {
    this.cache = null; this.dirty = true;
    if (this.file && !this.timer) { this.timer = setTimeout(() => { this.timer = null; this.flush(); }, 3000); this.timer.unref?.(); }
  }
  flush() {
    if (!this.file || !this.dirty) return;
    this.dirty = false;
    try { fs.writeFileSync(this.file + '.tmp', JSON.stringify(this.db)); fs.renameSync(this.file + '.tmp', this.file); }
    catch (e) { this.dirty = true; this.log('[全服榜] 存档写不进：' + e.message); }
  }
  // 一局的结果：{ round 这一局的编号（重发不重记）, winner 1 / -1, list: [{ id, name, av, side, v }] }
  report(roomId, b) {
    const round = str(b?.round, 64), winner = +b?.winner > 0 ? 1 : -1, list = Array.isArray(b?.list) ? b.list.slice(0, ROUND_MAX) : null;
    if (!round || !list) return { ok: false, why: '缺 round 或 list' };
    const rk = roomId + ':' + round;
    if (this.rounds.has(rk)) return { ok: true, dup: true };
    this.rounds.add(rk); this.roundQ.push(rk);
    if (this.roundQ.length > 5000) this.rounds.delete(this.roundQ.shift());
    this.roll();
    const d = this.db;
    let n = 0, sum = 0;
    for (const e of list) {
      const id = str(e?.id, 128), v = Math.floor(+e?.v);
      if (!id || !(v > 0) || v > V_MAX) continue;
      const side = +e.side > 0 ? 1 : -1, name = str(e.name, 64) || '观众', av = str(e.av, 512);
      for (const m of [d.week.m, d.month.m]) {
        const o = m[id] || (m[id] = { v: 0, name, av, side });
        o.v += v; o.name = name; o.side = side; if (av) o.av = av;
      }
      if (side !== winner) delete d.streak.m[id];
      else { const o = d.streak.m[id] || (d.streak.m[id] = { n: 0, name, av, side }); o.n++; o.name = name; o.side = side; if (av) o.av = av; }
      n++; sum += v;
    }
    for (const m of [d.week.m, d.month.m]) {
      const ids = Object.keys(m);
      if (ids.length > KEEP) ids.sort((x, y) => m[y].v - m[x].v).slice(KEEP).forEach((id) => delete m[id]);
    }
    this.touch();
    this.log(`[全服榜] 直播间 ${roomId} 报一局：${n} 人 ${sum} 分，${winner > 0 ? '小美' : '大帅'}赢`);
    return { ok: true, n };
  }
  board() {
    this.roll();
    if (this.cache) return this.cache;
    const d = this.db, t = this.now(), day = bj(t);
    const top = (m, val, f) => this.sorted(m, val).slice(0, TOP).map(([id, o]) => ({ id, name: o.name, av: o.av, side: o.side, [f]: val(o) }));
    const week = top(d.week.m, (o) => o.v, 'v'), month = top(d.month.m, (o) => o.v, 'v');
    const vip = bare();
    const put = (L, tab) => L.forEach((e, i) => { if (e.v >= VIP_MIN && (!vip[e.id] || i + 1 < vip[e.id][0])) vip[e.id] = [i + 1, tab]; });
    put(month, 'month'); put(week, 'week'); put(d.last.top, 'last');
    const monthEnd = Date.UTC(day.getUTCFullYear(), day.getUTCMonth() + 1, 1), weekDay = (day.getUTCDay() + 6) % 7;
    return this.cache = {
      week: { key: d.week.key, left: 7 - weekDay, top: week }, month: { key: d.month.key, left: Math.ceil((monthEnd - day.getTime()) / 864e5), top: month },
      streak: { top: top(d.streak.m, (o) => o.n, 'n') }, last: { key: d.last.key }, vip,
    };
  }
}
