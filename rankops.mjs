// 全网总榜的「记账条目」（11-16 用户：一定要服务器来做总榜）。
// 各直播间的 exe 照旧在本地算（boards.mjs 周榜/月榜/省份榜、medals.mjs 城市积分），同时把每一笔变动记成一条 op，
// 攒成一批报给抖音云（open/rankstore.mjs）；服务器按同样的规则把所有直播间的 op 记进同一份榜，存 MongoDB，
// exe 再把服务器的整份榜取回来当本地镜像，把还没报上去的 op 重放一遍叠在上面。
// 本地和服务器跑的是同一段代码（applyOps），同样的 op 记出来的结果一样。
//   {t:'c', at, key, name, avatar, v, paid}   观众贡献 v 分、其中送礼 paid（Boards.credit）
//   {t:'s', at, board:[{id,name,score}], winner:{id,name}|null, streak}   一局结算的省份成绩（Boards.settle）
//   {t:'m', at, gains:[{key,id,votes,paid,name,avatar}]}   一局结算的城市积分（Medals.settle）
const num = (x, max) => { const n = Math.floor(Number(x)); return Number.isFinite(n) ? Math.max(0, Math.min(max, n)) : 0; };
const str = (x, max) => String(x ?? '').slice(0, max);
const MAX_V = 1e8; // 一笔最多算多少分（防坏数据）

// 收到的 op 先过一遍：字段收成规定的类型和长度，认不得的丢掉
export function cleanOp(o) {
  if (!o || typeof o !== 'object') return null;
  const at = Number(o.at) || 0;
  if (o.t === 'c') {
    const key = str(o.key, 128), v = num(o.v, MAX_V);
    return key && v > 0 ? { t: 'c', at, key, name: str(o.name, 32), avatar: str(o.avatar, 512), v, paid: num(o.paid, MAX_V) } : null;
  }
  if (o.t === 's') {
    if (!Array.isArray(o.board)) return null;
    const board = o.board.slice(0, 64).map((x) => ({ id: str(x?.id, 32), name: str(x?.name, 16), score: num(x?.score, 1e12) })).filter((x) => x.id);
    const winner = o.winner?.id ? { id: str(o.winner.id, 32), name: str(o.winner.name, 16) } : null;
    if (winner && !board.some((x) => x.id === winner.id && x.score > 0)) return null; // Boards.settle 只给有分的省建档
    return { t: 's', at, board, winner, streak: num(o.streak, 1e6) };
  }
  if (o.t === 'm') {
    if (!Array.isArray(o.gains)) return null;
    const gains = o.gains.slice(0, 20000).map((g) => ({ key: str(g?.key, 128), id: str(g?.id, 32), votes: num(g?.votes, MAX_V), paid: num(g?.paid, MAX_V), name: str(g?.name, 32), avatar: str(g?.avatar, 512) })).filter((g) => g.key && g.id && g.votes > 0);
    return { t: 'm', at, gains };
  }
  return null;
}

// 把 op 记进 boards / medals。clock（可选）：{t} 是 Boards/Medals 用的「现在」，按 op 的时间往前走（只进不退，也不超过真实时间），
// 这样一批里跨了周末的 op 各记各的周；本地重放不传 clock，用真实时间
export function applyOps(boards, medals, ops, clock = null) {
  for (const o of ops) {
    if (clock) clock.t = Math.max(clock.t, Math.min(Number(o.at) || 0, Date.now()));
    if (o.t === 'c') boards.credit(o.key, { name: o.name, avatar: o.avatar }, o.v, o.paid);
    else if (o.t === 's') boards.settle(o.board, o.winner, o.streak);
    else if (o.t === 'm') medals.settle(o.gains);
  }
  if (clock) clock.t = Math.max(clock.t, Date.now());
}
