/* buddy.js —— 灭迹党档 3「哥们」（2026-09-26 替换奶茶；同日改滑板、多人）
 *
 * 不是飞行物，是一个**角色**：男生的肌肉哥们踩着滑板从右边滑进来，停在男生那一侧的随机位置，
 * 端着水枪朝女生乱滋一阵，再滑出去。滑板替掉了走路/蹦跳动作 —— 人只要一张端枪滋水的立绘，
 * 位移全交给滑板。画风跟两个主角同一套（预渲染立绘，v14/buddy/make.py 抠的），不走礼物那套 3D 转盘。
 *
 * 同时最多 MAX 个。满了再刷，不加人，给剩余时间最短的那个续一段 T.spray。
 *
 * 分层：人画在角色层、**男生底下**（都在男生斜后方）；水柱画在特效层，越过男生头顶飞向女生。
 *
 * 水柱是一串水滴：每一滴出枪时挑好落在女生身上的哪一点（girlTarget(u)，u=0 脸 → 1 膝盖），
 * **出枪速度固定**（V），按那一点反解低弹道的仰角 —— 水从枪口顺着枪管方向射出去、再被重力压弯，
 * 读得出是一股有速度的水。（旧版按距离给飞行时间反算速度，近处的滴初速朝上翘，枪口那段水乱指。）
 * 飞到那一点的横坐标就碎（每帧按同一个 u 重取，人动了跟着走）。**不碰外轮廓**：她伸出去的手臂和
 * 手机那一行轮廓在最前面，碰轮廓的话滋胸口的水全在手机上炸开，读成"滋手机"。
 *
 * 数值不在这里：送礼的战力走 SHOP.push（main.js giveGift），这里只负责演出。
 * 命中反馈通过 onHit 回调交给 main.js 的 impact（染色、震屏、配方粒子）。
 */
'use strict';

const Buddy = (function () {
  /* 一个哥们的时间轴（秒）：滑进来 → 滋 → 滑出去 */
  const T = { enter: 0.55, spray: 2.5, exit: 0.5 };
  const MAX = 3;               // 场上最多几个哥们；满了再刷 = 给剩余时间最短的那个续 T.spray
  /* 立绘：v14/buddy/make.py 抠的。foot 是两组滑板轮子正中的底边、muzzle 是枪口，都是贴图像素。 */
  const SPR = { src: 'assets/world/buddy.webp', foot: [260, 436], muzzle: [2, 78] };
  /* 站位：每个哥们出场时随机抽一个远近 depth（最远的比最近的脚底高 LIFT 像素、缩到 DEPTH[0]）
     和一个横向位置 r∈[0,1]。横向按**枪口**排，不按滑板：滑板站姿两脚分得开，脚到枪口有 258 像素，
     按脚排的话枪口伸到手机那儿，离女生太近，水几乎竖着往下落。
     r=0 枪口在 sprayZone()[0]，r=1 人的右沿到 sprayZone()[1]（背和滑板尾可以出画）。
     屏幕只有 960 宽，横向只剩 ~140 像素拉不开，几个人主要靠远近错开：远近分 ROWS 排（depth 区间），
     每人占一排，远排小、脚底高 —— 枪口上下错开，几股水不会从同一点分叉出去读成"7"字。
     LIFT 是最远一排比最近一排脚底高多少像素；两人 r 至少差 GAP。 */
  const ROWS = [[0.86, 0.95], [0.74, 0.83], [0.62, 0.70]], DEPTH = [0.62, 0.95], LIFT = 140, GAP = 0.3;
  /* 水：每人每秒出 RATE 滴，出枪速度 V（像素/秒）固定，重力 G。
     瞄点在女生身上从头到膝盖乱扫（sweep 两个不公约的正弦叠起来，读成"乱滋"不是来回刷）。
     扫动的快慢要跟水在空中的时间（约 0.35 秒）比：扫得快，前后出枪的水滴落点差太远，一股水
     折成闪电（4.1 / 9.7 rad/s）或"7"字（2.3 / 5.3，固定出枪速度以后）；1.2 / 2.8 才是一条顺着甩的抛物线。 */
  const RATE = 55, V = 1250, G = 900, HIT_EVERY = 0.3, SWEEP = [1.2, 2.8];
  /* 水柱三遍描线的线宽与颜色：深蓝描边 → 浅蓝水身 → 白色高光 */
  const STROKE = [[26, 'rgba(24,70,140,.75)'], [19, 'rgba(110,196,255,.95)'], [6, 'rgba(255,255,255,.9)']];

  let img = null, o = {};
  const bs = [], drops = [];

  function init(opt) { o = opt; }

  function load(v, off) {
    if (off) return Promise.resolve(false);
    return new Promise((ok) => {
      const i = new Image();
      i.onload = () => { img = i; ok(true); };
      i.onerror = () => ok(false);
      i.src = SPR.src + (v ? '?v=' + encodeURIComponent(v) : '');
    });
  }

  const sprayEnd = (b) => T.enter + b.spray;

  /* 横向位置：抽 12 次，取离已有哥们最远的那个（够 GAP 就直接用） */
  function pickR() {
    let best = Math.random(), bestD = -1;
    for (let k = 0; k < 12; k++) {
      const r = Math.random(), d = Math.min(1, ...bs.map(b => Math.abs(b.r - r)));
      if (d >= GAP) return r;
      if (d > bestD) { best = r; bestD = d; }
    }
    return best;
  }

  function summon() {
    const staying = bs.filter(b => b.t <= sprayEnd(b));
    if (bs.length >= MAX) {
      if (staying.length) {               // 满了：剩余时间最短的续一段
        const b = staying.reduce((a, c) => (sprayEnd(a) - a.t <= sprayEnd(c) - c.t ? a : c));
        b.spray += T.spray;
        return;
      }
      bs.splice(bs.findIndex(b => b.t === Math.max(...bs.map(c => c.t))), 1);   // 全在离场：顶掉走得最远的
    }
    const free = ROWS.filter(R => !bs.some(b => b.s >= R[0] && b.s <= R[1]));
    const R = (free.length ? free : ROWS)[Math.floor(Math.random() * (free.length || ROWS.length))];
    const d = R[0] + Math.random() * (R[1] - R[0]);
    bs.push({ t: 0, spray: T.spray, emit: 0, hitCd: 0, first: true, ph: Math.random() * 6,
              r: pickR(), s: d, lift: LIFT * (DEPTH[1] - d) / (DEPTH[1] - DEPTH[0]), seq: 0 });
    bs.sort((a, b) => a.s - b.s);          // 远的先画
  }

  const easeOut = (u) => 1 - Math.pow(1 - u, 3);

  /* 此刻人站在哪（滑板底边中点的屏幕坐标）和缩放 */
  function pose(b) {
    const s = b.s, [lo, right] = o.sprayZone(), wid = img ? img.width : 440;
    const hi = Math.max(lo, right - (wid - SPR.muzzle[0]) * s);
    const x1 = lo + (hi - lo) * b.r + (SPR.foot[0] - SPR.muzzle[0]) * s, y = o.ground() - b.lift;
    const off = o.W + (SPR.foot[0] + 40) * s;                 // 整个人完全在画外的滑板中点横坐标
    const t = b.t, se = sprayEnd(b);
    let x;
    if (t < T.enter) x = off + (x1 - off) * easeOut(t / T.enter);           // 滑进来，减速停住
    else if (t > se) { const u = Math.min(1, (t - se) / T.exit); x = x1 + (off - x1) * u * u; }  // 往后溜出去
    else x = x1 + Math.sin((t - T.enter) * 1.1 + b.ph) * 10 + Math.sin(t * 47) * 1.5;  // 滑板慢慢晃 + 后坐抖
    return [x, y + Math.abs(Math.sin(t * 31)) * -1.2, s];     // 轮子压地面的细颤
  }

  function muzzle(p) {
    return [p[0] + (SPR.muzzle[0] - SPR.foot[0]) * p[2], p[1] + (SPR.muzzle[1] - SPR.foot[1]) * p[2]];
  }

  /* 固定出枪速度 V，打中 (dx, dy)（屏幕坐标，dx<0 朝左）的低弹道初速度。够不着就按 45° 打。 */
  function launch(dx, dy) {
    const D = Math.abs(dx), h = -dy, v2 = V * V;
    const disc = v2 * v2 - G * (G * D * D + 2 * h * v2);
    const th = disc >= 0 ? Math.atan((v2 - Math.sqrt(disc)) / (G * D)) : Math.PI / 4;
    return [Math.sign(dx) * V * Math.cos(th), -V * Math.sin(th)];
  }

  function update(dt) {
    for (let i = drops.length - 1; i >= 0; i--) {
      const d = drops[i];
      d.vy += G * dt; d.x += d.vx * dt; d.y += d.vy * dt; d.t += dt;
      const tg = o.girlTarget(d.u), b = d.b;
      if (tg && d.x <= tg[0]) {
        drops.splice(i, 1);
        o.onSplash(tg[0], d.y);
        if (bs.includes(b) && b.hitCd <= 0) { o.onHit(tg[0], d.y, b.first); b.first = false; b.hitCd = HIT_EVERY; }
      } else if (d.t > 1.6 || d.x < -50) drops.splice(i, 1);
    }
    for (let i = bs.length - 1; i >= 0; i--) {
      const b = bs[i];
      b.t += dt; b.hitCd -= dt;
      const se = sprayEnd(b);
      if (b.t >= se + T.exit) { bs.splice(i, 1); continue; }
      if (b.t < T.enter || b.t > se) continue;
      b.emit += dt * RATE;
      const m = muzzle(pose(b));
      while (b.emit >= 1) {
        b.emit -= 1;
        const tt = b.t + b.ph;
        const u = Math.min(1, Math.max(0, 0.5 + 0.32 * Math.sin(tt * SWEEP[0]) + 0.2 * Math.sin(tt * SWEEP[1] + 1.3)));
        const tg = o.girlTarget(u);
        if (!tg) continue;
        const [vx, vy] = launch(tg[0] - m[0], tg[1] - m[1]);
        drops.push({ x: m[0], y: m[1], vx, vy, t: 0, u, b, seq: b.seq++ });
      }
    }
  }

  // 人：角色层，男生之前画（被男生挡住）；bs 按远近排好，远的先画
  function drawActor(ctx) {
    if (!img) return;
    for (const b of bs) {
      const [x, y, s] = pose(b);
      ctx.drawImage(img, x - SPR.foot[0] * s, y - SPR.foot[1] * s, img.width * s, img.height * s);
    }
  }

  /* 水柱：同一个人出枪顺序相邻、离得不远的水滴连成线。三遍描线（STROKE），
     跟礼物"实体靠轮廓"是同一条规矩 —— 浅蓝在浅绿墙上不描边就化掉了。 */
  function drawWater(ctx) {
    if (!drops.length) return;
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (const [lw, col] of STROKE) {
      ctx.lineWidth = lw; ctx.strokeStyle = col; ctx.beginPath();
      const last = new Map();                 // 几个人的水滴在 drops 里是交错的，按人找上一滴
      for (const b of drops) {
        const a = last.get(b.b); last.set(b.b, b);
        if (!a || b.seq !== a.seq + 1 || Math.hypot(b.x - a.x, b.y - a.y) > 60) continue;
        ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
      }
      ctx.stroke();
    }
  }

  const active = () => bs.length > 0;
  function reset() { bs.length = 0; drops.length = 0; }

  return { init, load, summon, update, drawActor, drawWater, active, reset };
})();
