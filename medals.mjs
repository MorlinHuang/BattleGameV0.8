// 城市助力积分 + 美食奖章 + 城市榜（11-04 发行方测试反馈第 3、4 条）。纯数据，跟着存档走（core.mjs save）。
//   · 每局结算时，观众本局给哪个省加了多少分，就给这位观众在这个省记多少「助力积分」：一人一省一本账，各省之间不互通；
//     按季度累计：北京时间每年 1/4/7/10 月 1 日 0 点全部清零（抖音准入规则：玩法内用户资产统计时效最长 3 个月，并在界面写明有效期）；
//     11-06 起按面值记（礼物面值 + 点赞 / 666 + 报名 1 分，和周榜月榜同一口径）：甜甜圈加成、最后 60 秒翻倍、首礼 +500 只算本局比分，不进积分；
//     冠军省送过礼的观众另加冠军加成（arena.settle）。g = 其中送礼的那部分，城市大哥的门槛只看它
//   · 每个省的积分到线就升一档奖章（MEDALS）：普通食客 → 探店达人 → 风味行家 → 超级吃货 → 资深老饕，画面上写成「广东·探店达人」；
//   · 奖章只做外显（名字旁的牌子、播报、城市榜），不影响比分（抖音 FAQ：积分不能影响玩法内数值，外显权益可以）；
//   · 城市榜：同一个省里按助力积分排名（「北京榜第 2」），排行榜面板「城市榜」一页；城市榜前 CITY_VIP 名、积分够 CITY_VIP_MIN 的观众本局第一次露面也放大哥入场。
// 门槛按分数量级定：免费互动（点赞 / 666）一局最多 3000 分，打满一局就是探店达人、十来局风味行家；一个生命药水 10 万分。
export const MEDALS = [
  { at: 1, name: '普通食客' },
  { at: 3000, name: '探店达人' },
  { at: 30000, name: '风味行家' },
  { at: 200000, name: '超级吃货' },
  { at: 1000000, name: '资深老饕' },
];
export const medalOf = (pts) => MEDALS.findLastIndex((m) => pts >= m.at); // -1 = 还没有奖章
export const CITY_VIP = 3; // 城市榜前几名算城市大哥
export const CITY_VIP_MIN = 30000; // 城市大哥：在这个省送礼累计至少这么多（11-06 起只算送礼；不然冷门省份报过一次名、或只点赞十来局就是「第一」，每局开头一串入场视频）
const KEEP = 20000; // 最多记多少观众：超了把总积分最少的那一半删掉
const TOP = 50; // 城市榜面板列多少
const BJ = 8 * 3600e3;
// 季度：'2026-Q4'；end = 下一季度第一天北京时间 0 点
export const seasonOf = (t) => { const d = new Date(t + BJ), q = Math.floor(d.getUTCMonth() / 3); return { id: `${d.getUTCFullYear()}-Q${q + 1}`, end: Date.UTC(d.getUTCFullYear(), q * 3 + 3, 1) - BJ }; };

export class Medals {
  constructor(saved = {}, now = () => Date.now()) {
    this.now = now;
    this.players = saved?.players && typeof saved.players === 'object' ? saved.players : {}; // key → {name, avatar, p: {省 id: 积分}, g: {省 id: 其中送礼的}}
    this.season = typeof saved?.season === 'string' ? saved.season : ''; // 这份积分属于哪个季度（11-06 之前的存档没有：当作上一季，读进来就清零）
    this.cache = new Map(); // 省 id → 按积分排好的观众 key（只在结算时变，结算时清掉）
    this.end = 0;
    this.roll();
  }
  // 换季：积分、奖章、城市榜全部清零
  roll() {
    const t = this.now();
    if (t < this.end) return;
    const s = seasonOf(t);
    if (this.season !== s.id) { this.players = {}; this.season = s.id; this.cache.clear(); }
    this.end = s.end;
  }
  // 本季积分什么时候清零（画面上写有效期）：'2027-01-01'
  resetDay() { this.roll(); return new Date(this.end + BJ).toISOString().slice(0, 10); }
  pts(key, id) { this.roll(); return this.players[key]?.p[id] || 0; }
  paid(key, id) { this.roll(); return this.players[key]?.g?.[id] || 0; }
  // 这位观众在这个省的奖章：{lv, name, pts, next}（lv -1 = 没有）
  medal(key, id) {
    const pts = this.pts(key, id), lv = medalOf(pts), m = MEDALS[lv];
    return { lv, name: m?.name || '', pts, next: MEDALS[lv + 1]?.at || 0 };
  }
  // 一局结算：gains = [{key, id, votes, paid, name, avatar}]（votes 含冠军加成，paid = 其中送礼面值）→ 每人每省加积分，返回 [{key, id, gain, pts, lv, from}]
  settle(gains) {
    this.roll();
    const out = [];
    for (const g of gains) {
      if (!(g.votes > 0) || !g.key || !g.id) continue;
      const p = (this.players[g.key] ||= { name: g.name, avatar: '', p: {}, g: {} });
      p.name = g.name || p.name; if (g.avatar) p.avatar = g.avatar;
      const before = p.p[g.id] || 0, after = before + g.votes;
      p.p[g.id] = after;
      if (g.paid > 0) { p.g ||= {}; p.g[g.id] = (p.g[g.id] || 0) + g.paid; }
      out.push({ key: g.key, id: g.id, gain: g.votes, pts: after, lv: medalOf(after), from: medalOf(before) });
    }
    if (Object.keys(this.players).length > KEEP) this.trim();
    this.cache.clear();
    return out;
  }
  trim() {
    const total = (k) => Object.values(this.players[k].p).reduce((a, b) => a + b, 0);
    const keys = Object.keys(this.players).sort((a, b) => total(b) - total(a));
    for (const k of keys.slice(KEEP / 2)) delete this.players[k];
  }
  order(id) {
    this.roll();
    if (!this.cache.has(id)) this.cache.set(id, Object.keys(this.players).filter((k) => this.players[k].p[id] > 0).sort((a, b) => this.players[b].p[id] - this.players[a].p[id] || (a < b ? -1 : 1)));
    return this.cache.get(id);
  }
  // 城市榜名次（0 = 不在榜上）
  cityRank(key, id) { return this.order(id).indexOf(key) + 1; }
  // 这位观众积分最高的省（还没报名时，城市大哥按这个省算）
  homeOf(key) { this.roll(); const p = this.players[key]?.p || {}; let best = '', v = 0; for (const [id, x] of Object.entries(p)) if (x > v) { v = x; best = id; } return best; }
  // 画面上要标的：奖章 + 城市榜名次（前 10 才标）
  badge(key, id) {
    if (!key || !id) return {};
    const m = this.medal(key, id), cr = this.cityRank(key, id);
    return m.lv < 0 ? {} : { md: m.lv, mdn: m.name, cr: cr && cr <= 10 ? cr : 0 };
  }
  // 排行榜面板「城市榜」：这个省前 TOP 名
  board(id) {
    return this.order(id).slice(0, TOP).map((k) => { const p = this.players[k], v = p.p[id]; return { name: p.name, avatar: p.avatar, v, lv: medalOf(v), md: MEDALS[medalOf(v)].name }; });
  }
  // 我的奖章（测试控制台）：按积分从高到低
  mine(key) { this.roll(); const p = this.players[key]?.p || {}; return Object.entries(p).sort((a, b) => b[1] - a[1]).map(([id, v]) => ({ id, v, lv: medalOf(v), md: MEDALS[medalOf(v)]?.name || '', cr: this.cityRank(key, id) })); }
  toJSON() { return { season: this.season, players: this.players }; }
}
