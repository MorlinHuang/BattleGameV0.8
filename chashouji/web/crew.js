/* crew.js —— 档 3 的两个"帮手"角色（2026-09-26）：灭迹党的**哥们**（替换奶茶）、查岗党的**闺蜜**（替换花束）。
 *
 * 不是飞行物，是**角色**：踩着滑板 / 平衡车从自己那一侧画外滑进来，停在自己主角身后的随机位置，
 * 朝对方喷一阵，再滑出去。位移全交给脚下的滑板/平衡车，人只做一个动作 —— **一部分身体绕转轴转，
 * 喷口跟着落点瞄**。立绘切成两层（v14/buddy/make.py、v14/bestie/make.py）：
 *   rot 层绕 pivot 转（哥们：腰以上整个上半身；闺蜜：伸直的那条手臂 + 喷雾罐），
 *   fix 层不动、**画在 rot 之上**（哥们的裤腰 / 闺蜜的肩膀盖住接缝）。
 *
 * **由落点反推枪口**：每帧看该打对方身上哪一点（o.target(u)），按喷出物的出口速度 V 和重力 G 反解要的
 * 仰角，转轴按转速上限 aim.rate 转过去、夹在 aim.lo~hi；喷出物**永远沿喷口此刻的方向、以 V 射出**。
 * 落在哪只由转角决定：转平滑，水柱/雾就平滑变形。（试过每滴反解初速去凑落点：前后两滴速度差大，水柱成锯齿。）
 * 仰角跟喷口位置互相依赖（一转喷口就挪），迭代到收敛；瞄点平滑跟随（步态是硬切帧，直接瞄会抖）。
 *
 * **比例按透视**：rows 是缩放 s（1 = 跟自己主角一样大：两张立绘都按"头半径 = 主角头半径"出的图），
 * 站得越远越小、脚底越靠近视平线：抬高 = (地面 − 视平线) × (1 − s)。视平线是镜头的，两边共用 o.horizon。
 * （第一版哥们 s 0.86~0.95、抬高另给：站在男生身后却比男生还壮一圈。）
 *
 * 同时最多 max 个，满了再刷：不加人，给剩余时间最短的那个续一段 T.spray。
 * 数值不在这里（送礼的战力走 SHOP.push），这里只负责演出；命中反馈通过 o.onHit 交给 main.js 的 impact。
 */
'use strict';

function Crew(cfg) {
  const { face, spr, aim: AIM, T } = cfg;       // face：-1 朝左（站右边），+1 朝右（站左边）
  const F = cfg.fluid;
  let img = null, imgFix = null, o = {};
  const bs = [], ps = [];                        // 在场的人、喷出去的东西（水滴 / 雾团）

  function init(opt) { o = opt; }

  function load(v, off) {
    if (off) return Promise.resolve(false);
    const one = (src) => new Promise((ok) => {
      const i = new Image();
      i.onload = () => ok(i);
      i.onerror = () => ok(null);
      i.src = src + (v ? '?v=' + encodeURIComponent(v) : '');
    });
    return Promise.all([one(spr.rot), one(spr.fix)]).then(([r, f]) => {
      if (r && f) { img = r; imgFix = f; }
      return !!img;
    });
  }

  const sprayEnd = (b) => T.enter + b.spray;

  /* 横向位置：抽 12 次，取离已有的人最远的那个（够 gap 就直接用） */
  function pickR() {
    let best = Math.random(), bestD = -1;
    for (let k = 0; k < 12; k++) {
      const r = Math.random(), d = Math.min(1, ...bs.map(b => Math.abs(b.r - r)));
      if (d >= cfg.gap) return r;
      if (d > bestD) { best = r; bestD = d; }
    }
    return best;
  }

  function summon() {
    const staying = bs.filter(b => b.t <= sprayEnd(b));
    if (bs.length >= cfg.max) {
      if (staying.length) {               // 满了：剩余时间最短的续一段
        const b = staying.reduce((a, c) => (sprayEnd(a) - a.t <= sprayEnd(c) - c.t ? a : c));
        b.spray += T.spray;
        return;
      }
      bs.splice(bs.findIndex(b => b.t === Math.max(...bs.map(c => c.t))), 1);   // 全在离场：顶掉走得最远的
    }
    /* 远近：每人占一排（rows 里挑没人的），远排小、脚底高 —— 喷口上下错开，几股不会从同一点分叉 */
    const free = cfg.rows.filter(R => !bs.some(b => b.s >= R[0] && b.s <= R[1]));
    const pool = free.length ? free : cfg.rows, R = pool[Math.floor(Math.random() * pool.length)];
    bs.push({ t: 0, spray: T.spray, emit: 0, hitCd: 0, first: true, ph: Math.random() * 6, aim: 0,
              r: pickR(), s: R[0] + Math.random() * (R[1] - R[0]), seq: 0, tg: null, m: null, zone: null, zoneT: 0 });
    bs.sort((a, b) => a.s - b.s);          // 远的先画
  }

  const easeOut = (u) => 1 - Math.pow(1 - u, 3);

  /* 此刻人站在哪（脚下滑板/平衡车底边中点的屏幕坐标）和缩放。
     横向按**喷口**排：o.zone() = [喷口最多伸到哪（靠对方那边）, 人的外沿最多到哪（可以出画一点）]，
     r=0 喷口顶到第一个数，r=1 外沿顶到第二个数。 */
  function pose(b) {
    const s = b.s, [near, edge] = o.zone(), wid = img ? img.width : 400;
    let far = face < 0 ? edge - (wid - spr.muzzle[0]) * s : edge + spr.muzzle[0] * s;
    far = face < 0 ? Math.max(near, far) : Math.min(near, far);
    const x1 = near + (far - near) * b.r + (spr.foot[0] - spr.muzzle[0]) * s;
    const y = o.ground() - (o.ground() - o.horizon()) * (1 - s);
    const off = face < 0 ? o.W + (spr.foot[0] + 40) * s : -((wid - spr.foot[0]) + 40) * s;   // 整个人在画外
    const t = b.t, se = sprayEnd(b);
    let x;
    if (t < T.enter) x = off + (x1 - off) * easeOut(t / T.enter);                             // 滑进来，减速停住
    else if (t > se) { const u = Math.min(1, (t - se) / T.exit); x = x1 + (off - x1) * u * u; }  // 往后溜出去
    else x = x1 + Math.sin((t - T.enter) * 1.1 + b.ph) * 10 * s + Math.sin(t * 47) * 1.5 * s;  // 慢慢晃 + 后坐抖
    return [x, y + Math.abs(Math.sin(t * 31)) * -1.2, s];                                     // 轮子压地面的细颤
  }

  /* 转轴和喷口的屏幕坐标。rot 层在 canvas 上转 φ（顺时针为正）；喷口朝 face 那边，
     仰角 θ（抬高为正）对应 φ = −face·θ，出口方向 (face·cosθ, −sinθ)。 */
  function pivotAt(p) {
    return [p[0] + (spr.pivot[0] - spr.foot[0]) * p[2], p[1] + (spr.pivot[1] - spr.foot[1]) * p[2]];
  }
  function muzzle(p, th) {
    const [cx, cy] = pivotAt(p), dx = (spr.muzzle[0] - spr.pivot[0]) * p[2], dy = (spr.muzzle[1] - spr.pivot[1]) * p[2];
    const ph = -face * th, c = Math.cos(ph), s = Math.sin(ph);
    return [cx + dx * c - dy * s, cy + dx * s + dy * c];
  }

  /* 出口速度 V、重力 G，打中 (dx, dy)（屏幕坐标）要的仰角（低弹道）。够不着就按 45°。 */
  function elevation(dx, dy) {
    const D = Math.abs(dx), h = -dy, v2 = F.V * F.V, g = F.G;
    if (g === 0) return Math.atan2(h, D);
    const disc = v2 * v2 - g * (g * D * D + 2 * h * v2);
    return disc >= 0 ? Math.atan((v2 - Math.sqrt(disc)) / (g * D)) : Math.PI / 4;
  }

  /* 碰到对方了没有（有就返回命中点 [x, y]）。
     站着：飞到落点那一列、高度离落点 F.miss 以内算正中；打偏了碰到对方轮廓前沿（o.front）也算。
     倒地（落点第三项 'top'）：落到这一列的上沿（o.top）以下 —— 不看前沿：横躺时每一行的前沿都是
     伸出去的手臂和头，浇背的水一降到那几行就会全碎在头上。 */
  function hitTest(d, tg) {
    const past = (x) => face < 0 ? d.x <= x : d.x >= x;
    if (tg && tg[2] === 'top') {
      const top = o.top && o.top(d.x);
      return top != null && d.y >= top ? [d.x, top] : null;
    }
    if (tg && past(tg[0]) && Math.abs(d.y - tg[1]) < F.miss) return [tg[0], d.y];
    const fr = o.front(d.y);
    return fr != null && past(fr) ? [fr, d.y] : null;
  }

  function update(dt) {
    for (let i = ps.length - 1; i >= 0; i--) {
      const d = ps[i];
      if (F.drag) { const k = Math.exp(-F.drag * dt); d.vx *= k; d.vy *= k; }
      d.vy += F.G * dt; d.x += d.vx * dt; d.y += d.vy * dt; d.t += dt;
      const b = d.b, h = hitTest(d, o.target(d.u));
      if (h) {
        ps.splice(i, 1);
        o.onSplash(h[0], h[1]);
        if (bs.includes(b) && b.hitCd <= 0) { o.onHit(h[0], h[1], b.first); b.first = false; b.hitCd = F.hitEvery; }
      } else if (d.y > o.ground()) { ps.splice(i, 1); if (F.floor) o.onSplash(d.x, o.ground()); }   // 落空的在地上
      else if (d.t > F.life || d.x < -80 || d.x > o.W + 80) ps.splice(i, 1);
    }
    for (let i = bs.length - 1; i >= 0; i--) {
      const b = bs[i];
      b.t += dt; b.hitCd -= dt;
      const se = sprayEnd(b);
      if (b.t >= se + T.exit) { bs.splice(i, 1); continue; }
      /* 瞄：该打的落点 → 要的仰角 → 转轴按转速上限转过去。滑进来时就开始瞄，溜走时放平。
         对方倒地（o.down）不再整条扫，每 zone.every 秒随机挑一个部位、在它前后小幅扫。 */
      const tt = b.t + b.ph, sw = cfg.sweep;
      let u;
      if (o.down && o.down() && cfg.zone) {
        const Z = cfg.zone;
        if (b.zone == null || (b.zoneT -= dt) <= 0) { b.zone = Z.lo + Math.random() * (Z.hi - Z.lo); b.zoneT = Z.every; }
        u = b.zone + Z.span * (0.65 * Math.sin(tt * sw.w[0]) + 0.35 * Math.sin(tt * sw.w[1] + 1.3));
      } else {
        b.zone = null;
        u = 0.5 + sw.a[0] * Math.sin(tt * sw.w[0]) + sw.a[1] * Math.sin(tt * sw.w[1] + 1.3);
      }
      u = Math.min(1, Math.max(0, u));
      const p = pose(b), raw = b.t <= se && o.target(u);
      if (raw) {
        const k = b.tg ? 1 - Math.exp(-dt * AIM.follow) : 1;
        b.tg = b.tg ? [b.tg[0] + (raw[0] - b.tg[0]) * k, b.tg[1] + (raw[1] - b.tg[1]) * k] : raw;
      }
      const tg = raw && b.tg;
      let want = 0;
      if (tg) {
        want = b.aim;
        for (let k = 0; k < 6; k++) {
          const m0 = muzzle(p, want);
          want = Math.min(AIM.hi, Math.max(AIM.lo, elevation(tg[0] - m0[0], tg[1] - m0[1])));
        }
      }
      b.aim += Math.max(-AIM.rate * dt, Math.min(AIM.rate * dt, want - b.aim));
      b.m = null;
      if (b.t < T.enter || b.t > se || !tg) continue;
      /* 喷：从转过之后的喷口，沿喷口方向，速度 V（雾再加一点散角和快慢）。一帧攒够几个就出几个，
         每个按它**实际该出口的时刻**补飞一段（age）—— 不补的话帧一卡几个叠成一坨，水柱起疙瘩。 */
      b.emit += dt * F.rate;
      const m = b.m = muzzle(p, b.aim);
      while (b.emit >= 1) {
        b.emit -= 1;
        const age = b.emit / F.rate, a = b.aim + (Math.random() - 0.5) * 2 * F.spread;
        const v = F.V * (1 + (Math.random() - 0.5) * 2 * F.vJit);
        const vx = face * v * Math.cos(a), vy = -v * Math.sin(a);
        ps.push({ x: m[0] + vx * age, y: m[1] + vy * age + 0.5 * F.G * age * age, vx, vy: vy + F.G * age,
                  t: age, u, b, seq: b.seq++ });
      }
    }
  }

  /* 人：角色层、自己主角之前画（被主角挡住）；bs 按远近排好，远的先画。先 rot 层（转过的）再 fix 层。 */
  function drawActor(ctx) {
    if (!img) return;
    for (const b of bs) {
      const p = pose(b), [x, y, s] = p, [cx, cy] = pivotAt(p);
      const X = x - spr.foot[0] * s, Y = y - spr.foot[1] * s;
      ctx.save();
      ctx.translate(cx, cy); ctx.rotate(-face * b.aim); ctx.translate(-cx, -cy);
      ctx.drawImage(img, X, Y, img.width * s, img.height * s);
      ctx.restore();
      ctx.drawImage(imgFix, X, Y, imgFix.width * s, imgFix.height * s);
    }
  }

  function drawFluid(ctx) { if (ps.length) F.draw(ctx, ps, bs); }

  const active = () => bs.length > 0;
  function reset() { bs.length = 0; ps.length = 0; }

  return { init, load, summon, update, drawActor, drawFluid, active, reset };
}

/* 水柱（哥们）：同一个人出口顺序相邻、离得不远的水滴连成线，外加一段喷口 → 最新一滴
   （最新那滴已经飞了最多一帧 ~23 像素，不补的话水柱跟枪口之间是空的）。
   三遍描线 STROKE：深蓝描边 → 浅蓝水身 → 白色高光 —— 浅蓝在浅绿墙上不描边就化掉了。 */
const WATER_STROKE = [[26, 'rgba(24,70,140,.75)'], [19, 'rgba(110,196,255,.95)'], [6, 'rgba(255,255,255,.9)']];
function drawStream(ctx, ps, bs) {
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (const [lw, col] of WATER_STROKE) {
    ctx.lineWidth = lw; ctx.strokeStyle = col; ctx.beginPath();
    const last = new Map();                 // 几个人的水滴在 ps 里是交错的，按人找上一滴
    for (const b of ps) {
      const a = last.get(b.b); last.set(b.b, b);
      if (!a || b.seq !== a.seq + 1 || Math.hypot(b.x - a.x, b.y - a.y) > 60) continue;
      ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
    }
    for (const b of bs) {
      const a = last.get(b);
      if (b.m && a && Math.hypot(a.x - b.m[0], a.y - b.m[1]) < 60) { ctx.moveTo(b.m[0], b.m[1]); ctx.lineTo(a.x, a.y); }
    }
    ctx.stroke();
  }
}

/* 雾（闺蜜的防狼喷雾）：每个雾团出口时小、越飞越胀、越来越淡。两遍：先画一圈深橙红托底
   （明亮底图上发光靠不住，实体靠轮廓），再画亮橙的雾身。 */
function drawMist(ctx, ps) {
  const L = MIST.fluid.life;
  for (const [grow, col, k] of [[3, '176,52,20', 0.08], [0, '255,160,90', 0.16]]) {
    for (const d of ps) {
      const u = Math.min(1, d.t / L), r = 7 + 22 * Math.sqrt(u) + grow, a = (1 - u * u) * k;
      ctx.fillStyle = `rgba(${col},${a.toFixed(3)})`;
      ctx.beginPath(); ctx.arc(d.x, d.y, r, 0, 6.283); ctx.fill();
    }
  }
}

/* ---- 两个帮手的配置 ---- */

/* 哥们：v14/buddy/skate1.png 踩滑板端水枪。rot = 腰以上（绕裤腰正中转），fix = 裤子、腿、滑板。
   aim：最低 lo（再往下弯就不是端枪是鞠躬了）、最高 hi，rate 每秒最多转多少（瞄点跳过手机那行是跳变，
   枪不能瞬移），follow 瞄点平滑跟随的快慢。
   sweep：瞄点在对方身上 u=0.5 附近两个不公约的正弦叠起来乱扫；w 要跟水在空中的时间（~0.35s）比，
   快了（2.3/5.3 rad/s）前后水滴落点差太远，水柱折成"7"字，1.2/2.8 才是一条顺着甩的抛物线。
   zone：对方倒地后每 every 秒随机换一个部位（u∈lo~hi：后脑、背、屁股、腿），在它前后 ±span 扫。
   fluid：出口速度 V、重力 G，每人每秒 rate 滴；miss 见 hitTest；hitEvery 每人多久补一下命中反馈。 */
const Buddy = Crew({
  face: -1,
  spr: { rot: 'assets/world/buddy_up.webp', fix: 'assets/world/buddy_lo.webp',
         foot: [260, 436], muzzle: [2, 78], pivot: [266, 190] },
  T: { enter: 0.55, spray: 2.5, exit: 0.5 },
  max: 3, gap: 0.3,
  rows: [[0.74, 0.80], [0.66, 0.71], [0.58, 0.63]],
  aim: { lo: -0.52, hi: 0.21, rate: 2.4, follow: 10 },
  sweep: { a: [0.32, 0.2], w: [1.2, 2.8] },
  zone: { every: 1.0, lo: 0.2, hi: 0.85, span: 0.1 },
  fluid: { V: 1250, G: 900, drag: 0, rate: 55, spread: 0, vJit: 0, life: 1.6, miss: 90, hitEvery: 0.3, floor: true,
           draw: drawStream },
});

/* 闺蜜：v14/bestie/src1.png 比基尼、踩平衡车、单手伸直举防狼喷雾。rot = 伸直的右臂 + 喷雾罐（绕肩关节转），
   fix = 其余。只瞄男生的脸（喷雾就是冲眼睛去的），所以 sweep 幅度小、不分倒地部位（zone: null）。
   手臂转的范围比哥们弯腰小（lo/hi ±0.35）：胳膊再往下压就戳到自己胸口了。
   fluid：雾出口快、阻力大（drag）、几乎不受重力，飞一段就散（life）；每个雾团 ±spread 散角、±vJit 快慢，
   合起来是一个张开的喷锥。雾要**密而透**：雾团多（rate 90）、彼此重叠连成一片，但每团很淡（见 drawMist）。
   太浓（不透明度 0.5）三个人一起喷成一条橙色烟带，读成喷火器；太稀（rate 45、半径小）是一串分开的橙点。 */
const MIST = {
  face: +1,
  spr: { rot: 'assets/world/bestie_rot.webp', fix: 'assets/world/bestie_fix.webp',
         foot: [108, 481], muzzle: [274, 55], pivot: [122, 100] },
  T: { enter: 0.55, spray: 2.5, exit: 0.5 },
  max: 3, gap: 0.3,
  rows: [[0.74, 0.80], [0.66, 0.71], [0.58, 0.63]],
  aim: { lo: -0.35, hi: 0.35, rate: 2.4, follow: 10 },
  sweep: { a: [0.3, 0.15], w: [1.3, 3.1] },
  zone: null,
  fluid: { V: 1100, G: 60, drag: 1.0, rate: 90, spread: 0.1, vJit: 0.15, life: 0.8, miss: 60, hitEvery: 0.3, floor: false,
           draw: drawMist },
};
const Bestie = Crew(MIST);
