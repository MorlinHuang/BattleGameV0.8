// 周榜 / 月榜（10-27 用户：左上角排行榜按钮点开看「玩家周榜 / 玩家月榜 / 最美省份榜 / 省份连胜榜」，结算页写玩家本场票数、周榜排名、月榜排名）。
// 纯数据，跟着存档走（core.mjs save）。周从北京时间周六 0 点算（11-14 用户：和开播文档一致）、月按北京时间自然月；换周 / 换月那一刻旧榜清空重来。
//   players：观众 → {name, avatar, v}，v = 这个周期里给自己的队出的票（礼物按 gifts.mjs worth，入队、点赞、666 的免费票也算）
//   provs：省 → {name, wins, v}，wins = 这个周期赢了几局，v = 这个周期所有局里拿到的票（结算时的最终票数，被减掉的不算）
//   streak：省 → {name, best}，这个周期里最高打到几连胜
//   players[key].g = 其中送礼的那部分（礼物面值）。大哥入场的门槛只看 g（11-06：只点赞两局就成了「周榜第一」放金龙）
//   prev：上一期（上周 / 上月）结束时的前 PREV_TOP 名，换期那一刻存下：排行榜「上周 / 上月」页，以及新一期还没重新上榜的大哥照样按上期名次入场
const BJ = 8 * 3600e3;
export const weekOf = (t) => { const d = new Date(t + BJ), day = (d.getUTCDay() + 1) % 7; return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() - day)).toISOString().slice(0, 10); };
export const monthOf = (t) => new Date(t + BJ).toISOString().slice(0, 7);
const KEEP = 4000; // 一个周期最多记多少观众：超了把票最少的那一半删掉（只影响排在几千名以后的人）
const TOP = 50; // 排行榜面板每页列多少
const PREV_TOP = 100; // 上一期留多少名（大哥入场看前 100）
const DAY = 864e5;
// 百强还要有真金白银的贡献（11-03 第十七轮代码审核：榜上不到 100 人时，上一局报过名的人全是「百强」，每局开头几十段全屏神兽轮番放、把大礼特效全堵住）。
// 周榜送礼 ≥ 6000（一个甜甜圈）或月榜送礼 ≥ 2 万才算；报名、点赞这些免费分攒不到。荣誉称号同一道门槛
export const VIP_MIN = { 周榜: 6000, 月榜: 20000 };
const HALL_KEEP = { week: 12, month: 3 }; // 荣誉榜「历届」各留多少期：都不超过 3 个月（抖音准入规则：用户资产和信息统计时效最长 3 个月）
// 荣誉称号（11-06）：上一期送礼达标的评委里，按贡献排的前 3 名
const honored = (b, min) => b.list.filter((x) => x.g >= min).slice(0, 3);
const hallEntry = (b, min) => ({ id: b.id, top: honored(b, min).map(({ name, avatar, v }) => ({ name, avatar, v })) });

const fresh = (id) => ({ id, players: {}, provs: {}, streak: {} });
// 上一期的榜：按贡献排好的前 PREV_TOP 名 [{key, name, avatar, v, g}]
const snapshot = (b) => ({ id: b.id, list: Object.entries(b.players).sort(([x, a], [y, c]) => c.v - a.v || (x < y ? -1 : 1)).slice(0, PREV_TOP).map(([key, p]) => ({ key, name: p.name, avatar: p.avatar, v: p.v, g: p.g || 0 })) });
const prevOf = (saved) => (saved && Array.isArray(saved.list) ? saved : { id: '', list: [] });
// 存档里的周编号 = 那一周第一天的日期。11-14 之前一周从周一起，编号是周一的日期：换算成它所在那一周的周六，榜上的数据原样留着
const weekId = (id) => (id ? weekOf(Date.parse(id + 'T00:00:00+08:00')) : id);
export class Boards {
  constructor(saved = {}, now = () => Date.now()) {
    this.now = now;
    this.week = saved.week?.players ? saved.week : fresh('');
    this.month = saved.month?.players ? saved.month : fresh('');
    this.prevWeek = prevOf(saved.prevWeek); this.prevMonth = prevOf(saved.prevMonth);
    // 荣誉榜「历届」：每期结束时送礼达标的前 3 名，最新的在前（11-06 之前的存档没有，用存着的上一期补一条）
    this.hall = { week: Array.isArray(saved.hall?.week) ? saved.hall.week : [], month: Array.isArray(saved.hall?.month) ? saved.hall.month : [] };
    for (const k of ['week', 'month']) this.hall[k].length = Math.min(this.hall[k].length, HALL_KEEP[k]);
    this.week.id = weekId(this.week.id); this.prevWeek.id = weekId(this.prevWeek.id);
    for (const e of this.hall.week) e.id = weekId(e.id);
    if (!saved.hall) { if (this.prevWeek.id) this.hall.week.push(hallEntry(this.prevWeek, VIP_MIN.周榜)); if (this.prevMonth.id) this.hall.month.push(hallEntry(this.prevMonth, VIP_MIN.月榜)); }
    this.roll();
  }
  // 换周 / 换月：旧榜存成「上一期」（只有紧挨着的上一期才算：隔了几周没开播，上周榜就是空的），新一期从零开始
  roll() {
    const t = this.now(), w = weekOf(t), m = monthOf(t);
    const lastW = weekOf(t - 7 * DAY), lastM = monthOf(Date.parse(m + '-01T00:00:00+08:00') - 1);
    if (this.week.id !== w) { if (this.week.id) { this.prevWeek = snapshot(this.week); this.enshrine('week', hallEntry(this.prevWeek, VIP_MIN.周榜)); } this.week = fresh(w); this.sorted = null; }
    if (this.month.id !== m) { if (this.month.id) { this.prevMonth = snapshot(this.month); this.enshrine('month', hallEntry(this.prevMonth, VIP_MIN.月榜)); } this.month = fresh(m); this.sorted = null; }
    if (this.prevWeek.id && this.prevWeek.id !== lastW) this.prevWeek = { id: '', list: [] };
    if (this.prevMonth.id && this.prevMonth.id !== lastM) this.prevMonth = { id: '', list: [] };
  }
  enshrine(kind, e) { if (!e.top.length) return; const h = this.hall[kind]; h.unshift(e); h.length = Math.min(h.length, HALL_KEEP[kind]); }
  // 荣誉名次：这位观众在上周（kind 'week'）/ 上月（'month'）送礼达标的评委里排第几（前 3 名才有，没有 = 0）
  honorRank(key, kind) {
    this.roll();
    const b = kind === 'week' ? this.prevWeek : this.prevMonth;
    return honored(b, VIP_MIN[kind === 'week' ? '周榜' : '月榜']).findIndex((x) => x.key === key) + 1;
  }
  // 观众出了 v 分贡献，其中 paid 是送礼（礼物面值）
  credit(key, who, v, paid = 0) {
    if (!key || !(v > 0)) return;
    this.roll();
    for (const b of [this.week, this.month]) {
      const p = (b.players[key] ||= { name: who.name, avatar: '', v: 0, g: 0 });
      p.v += v; p.g = (p.g || 0) + Math.max(0, Math.min(v, paid)); p.name = who.name || p.name; if (who.avatar) p.avatar = who.avatar;
      if (Object.keys(b.players).length > KEEP) this.trim(b);
    }
    this.sorted = null;
  }
  trim(b) { const keys = Object.keys(b.players).sort((x, y) => b.players[y].v - b.players[x].v); for (const k of keys.slice(KEEP / 2)) delete b.players[k]; }
  // 一局结算：赢的省 +1 局，每个省加上本局最终票数，连胜记最高
  settle(board, winner, streak) {
    this.roll();
    for (const b of [this.week, this.month]) {
      for (const x of board) { if (!(x.score > 0)) continue; const p = (b.provs[x.id] ||= { name: x.name, wins: 0, v: 0 }); p.v += x.score; }
      if (winner) {
        b.provs[winner.id].wins++;
        const s = (b.streak[winner.id] ||= { name: winner.name, best: 0 }); s.best = Math.max(s.best, streak);
      }
    }
  }
  // 观众在周榜 / 月榜的名次（没上榜 = 0）。按票数从高到低排，同票按名字（稳定）
  order(b) {
    this.sorted ||= {};
    return (this.sorted[b.id + (b === this.week ? 'w' : 'm')] ||= Object.keys(b.players).sort((x, y) => b.players[y].v - b.players[x].v || (x < y ? -1 : 1)));
  }
  rankOf(key) {
    this.roll();
    const one = (b) => { const i = this.order(b).indexOf(key); return i < 0 ? { rank: 0, v: 0, g: 0 } : { rank: i + 1, v: b.players[key].v, g: b.players[key].g || 0 }; };
    const old = (b) => { const i = b.list.findIndex((x) => x.key === key); return i < 0 ? { rank: 0, v: 0, g: 0 } : { rank: i + 1, v: b.list[i].v, g: b.list[i].g }; };
    return { week: one(this.week), month: one(this.month), prevWeek: old(this.prevWeek), prevMonth: old(this.prevMonth) };
  }
  // 排行榜面板四页
  view() {
    this.roll();
    const players = (b) => this.order(b).slice(0, TOP).map((k) => ({ name: b.players[k].name, avatar: b.players[k].avatar, v: b.players[k].v }));
    const provs = Object.values(this.week.provs).sort((a, b) => b.wins - a.wins || b.v - a.v).slice(0, TOP);
    const streak = Object.values(this.week.streak).sort((a, b) => b.best - a.best).slice(0, TOP);
    const old = (b) => b.list.slice(0, TOP).map(({ name, avatar, v }) => ({ name, avatar, v }));
    return { week: this.week.id, month: this.month.id, prevWeekId: this.prevWeek.id, prevMonthId: this.prevMonth.id,
      playersWeek: players(this.week), playersMonth: players(this.month), playersPrevWeek: old(this.prevWeek), playersPrevMonth: old(this.prevMonth), provs, streak,
      hall: this.hall, honorWeek: honored(this.prevWeek, VIP_MIN.周榜).map(({ name, avatar, v }) => ({ name, avatar, v })), honorMonth: honored(this.prevMonth, VIP_MIN.月榜).map(({ name, avatar, v }) => ({ name, avatar, v })) };
  }
  toJSON() { return { week: this.week, month: this.month, prevWeek: this.prevWeek, prevMonth: this.prevMonth, hall: this.hall }; }
}
