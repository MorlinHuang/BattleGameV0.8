/* crew.js —— 档 3 的两个"帮手"角色（2026-09-26）：灭迹党的**哥们**（替换奶茶）、查岗党的**闺蜜**（替换花束）。
 *
 * 不是飞行物，是**角色**：踩着滑板 / 平衡车从自己那一侧画外滑进来，停在自己主角身后的随机位置，
 * 朝对方喷一阵，再滑出去。位移全交给脚下的滑板/平衡车，人只做一个动作 —— **身体绕转轴转，
 * 喷口跟着落点瞄**。立绘切成几层（v14/buddy/make.py、v14/bestie/make.py），画的顺序 arm → body → lo：
 *   body 绕腰（body.pivot）转，转总仰角的 body.k 份（哥们 1：整个上半身端着枪转；闺蜜 0.3：上身跟着前倾）；
 *   arm（可无）挂在 body 上、绕肩（arm.pivot）转剩下的，喷口在它上面；body 画在 arm 之上，肩膀盖住手臂根；
 *   lo 不动、画在最上，裤腰 / 腰盖住接缝。
 * anim（可无）是闺蜜那种"呲—呲—"一段段按的喷法：按一下（pulse.on 秒）松一下（pulse.off 秒），
 * 每次按下手臂后坐往上一震（kick），上身喷的时候往前探（lean）；平衡车上人轻轻浮（bob）。
 * 只转一条胳膊、其余一动不动（闺蜜第一版）读成静帧。
 * 形象 skins：每人三个（同一姿势改图换人，make.py 用同一个裁边框出图，所以 foot / muzzle / 转轴全都一样，
 * 只换贴图）。贴图路径 spr.src 里 %n 换成形象编号、%k 换成层名。召唤时挑场上没人用的那个。
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
  const A = cfg.anim || null;
  const REST = spr.rest || 0;                    // 贴图里喷口本来的指向（仰角，朝下为负）：真相女神第二版罐子本身就斜朝右下
  const PATH = cfg.path || {};                    // 悬停的人怎么来、怎么走（见 hoverPose）
  let img = null, xi = {}, o = {};               // img[形象]：{ arm, body, lo }（arm 可无）；xi：cfg.xtra 的附属贴图（哮天犬）
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
    const ks = ['arm', 'body', 'lo'].filter(k => spr[k]), src = (k, n) => spr.src.replace('%n', n).replace('%k', spr[k].src);
    const xs = Object.entries(cfg.xtra || {});
    return Promise.all([...cfg.skins.map(n => Promise.all(ks.map(k => one(src(k, n))))), Promise.all(xs.map(([, f]) => one(f)))]).then((all) => {
      const xim = all.pop(), sets = all;
      if (sets.every(ims => ims.every(Boolean)) && xim.every(Boolean)) {
        img = sets.map(ims => { const s = {}; ks.forEach((k, i) => { s[k] = ims[i]; }); return s; });
        xs.forEach(([k], i) => { xi[k] = xim[i]; });
      }
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

  /* 续上的这一份也是一次完整送礼：下一发按礼物力度打（first），并记下第几份、在她的第几秒续上（名字条据此重播「×N」） */
  function renew(b) { b.first = true; b.renew = (b.renew || 0) + 1; b.renewT = b.t; }

  /* sk（可无）：指定形象编号（cfg.skins 的下标，越界夹到两头）；不给就挑场上没人用的。诊断参数 ?skin= 用它。 */
  function summon(sk) {
    if (sk != null) sk = Math.max(0, Math.min(cfg.skins.length - 1, sk | 0));
    const staying = bs.filter(b => b.t <= sprayEnd(b));
    if (bs.length >= cfg.max) {
      if (staying.length) {               // 满了：剩余时间最短的续一段
        const b = staying.reduce((a, c) => (sprayEnd(a) - a.t <= sprayEnd(c) - c.t ? a : c));
        b.spray += T.spray; renew(b);
        return;
      }
      const far = bs.reduce((a, c) => (a.t >= c.t ? a : c));
      if (cfg.move === 'hover') {         // 悬停的人离场时还在画面正中，顶掉会凭空消失：把她叫回来，从当前高度落回悬停点
        const y = hoverPose(far)[1], vy = (hoverPose({ ...far, t: far.t + 1e-3 })[1] - y) / 1e-3;   // 被叫住时的高度、竖直速度
        far.spray = far.t - T.enter + T.spray;
        far.back = 0; far.back = y - hoverPose(far)[1]; far.backV = vy; far.backT = far.t;   // 先清掉上一次召回的余量再量
        renew(far); return;
      }
      bs.splice(bs.indexOf(far), 1);      // 全在离场：顶掉走得最远的（站地的往画外溜，被顶掉看不出来）
    }
    /* 远近：每人占一排（rows 里挑没人的），远排小、脚底高 —— 喷口上下错开，几股不会从同一点分叉 */
    const free = cfg.rows.filter(R => !bs.some(b => b.s >= R[0] && b.s <= R[1]));
    const pool = free.length ? free : cfg.rows, R = pool[Math.floor(Math.random() * pool.length)];
    /* 形象：挑一个场上没人用的（max 不超过形象数，同时在场的一定各不相同） */
    if (sk == null) {
      const skins = cfg.skins.map((_, i) => i), unused = freeSkins();
      sk = (unused.length ? unused : skins)[Math.floor(Math.random() * (unused.length || skins.length))];
    }
    bs.push({ born: ++Crew.born, t: 0, spray: T.spray, emit: 0, hitCd: 0, first: true, ph: Math.random() * 6, aim: 0,
              r: pickR(), s: R[0] + Math.random() * (R[1] - R[0]), seq: 0, tg: null, m: null, zone: null, zoneT: 0,
              pt: 0, kick: 0, lean: 0, skin: sk, landed: false, ex: 0, exP: null, av: 0, back: 0, backV: 0, backT: 0 });
    bs.sort((a, b) => a.s - b.s);          // 远的先画
  }

  /* 在场这个人还剩几秒（离场途中为负），没人为 null。CrewGroup 满员时挑最短的续 */
  function left() { return bs.length ? Math.min(...bs.map(b => sprayEnd(b) - b.t)) : null; }

  /* 场上没人用的形象（下标） */
  function freeSkins() { return cfg.skins.map((_, i) => i).filter(i => !bs.some(b => b.skin === i)); }

  const easeOut = (u) => 1 - Math.pow(1 - u, 3);

  /* 悬停（档 4 六个人）：不站地，悬在半空。o.perch(b) 给脚底该停在屏幕哪一点、缩放多大 [x, y, s]
     （main.js 的槽位管理：同边 1 人是大站位，2~3 人滑到斜线三槽，换槽时位置和缩放一起按 0.4 秒 Hermite 平滑过去，
     所以 s 不再是召唤那一刻定死的 b.s）。
     来：从 PATH.from(s, hx, hy) 给的画外那一点冲过来，按 easeOut 减速刹停（不给就从正上方画外冲下来 —— 女神 / 恶魔）；
     走：朝 PATH.to(s, x, y) 加速离开（u²，不给就原地往上冲出画面）。悬着的时候慢慢晃一个横 8 字 + 上下浮（anim.bob）。
     进出场时整个人另外转多少（roll：内裤侠横着飞进来、月亮查岗使转着圈落下）见 rollOf。 */
  function hoverPose(b) {
    const pc = o.perch(b), hx = pc[0], hy = pc[1], s = pc[2] != null ? pc[2] : b.s, t = b.t, se = sprayEnd(b);
    const top = -(spr.foot[1] - spr.muzzle[1] + 120) * s;             // 脚底在这，整个人（含翘起的罐子）都在画外
    const sx = Math.sin(t * 0.9 + b.ph) * 8 * s, sy = Math.sin(t * 1.8 + b.ph) * 4 * s;
    const bob = A ? Math.sin(t * A.bob[1] + b.ph) * A.bob[0] * s : 0;
    if (t < T.enter) {
      const [fx, fy] = PATH.from ? PATH.from(s, hx, hy) : [hx, top], e = easeOut(t / T.enter);
      return [fx + (hx - fx) * e, fy + (hy - fy) * e, s];
    }
    const k = Math.min(1, (t - T.enter) / 0.3);                        // 刹停后 0.3 秒里晃动从 0 长满，不跳
    /* back：离场途中又被召唤（summon），从被叫住那一刻的高度落回悬停点，用三次 Hermite：
       起点带着当时往上冲的速度（backV），先减速到顶再落回来、到位速度 0 —— 位置、速度都不跳。
       只用 easeOut 的话，速度一帧里从向上 1800 翻成向下 660 px/s。 */
    let bk = 0;
    if (b.back) {
      const D = T.enter, u = Math.min(1, (t - b.backT) / D);
      bk = b.back * (2 * u ** 3 - 3 * u * u + 1) + b.backV * D * (u ** 3 - 2 * u * u + u);
    }
    const x = hx + sx * k, y = hy + (sy + bob) * k + bk;
    if (t > se) {
      const u = Math.min(1, (t - se) / T.exit), [tx, ty] = PATH.to ? PATH.to(s, x, y) : [x, top];
      return [x + (tx - x) * u * u, y + (ty - y) * u * u, s];
    }
    return [x, y, s];
  }
  /* 进出场时整个人额外转的角（canvas 顺时针为正），绕 PATH.pivot（贴图点，不给就是 whole.pivot）：
     来的时候从 roll0 + spin 圈转回 0（easeOut，跟位移同步刹住）；走的时候从 0 转到 rollOut（u²）；
     悬着时 swing = [幅度, 角频率] 轻轻摆（黑蛛女特工吊在丝上，绕抓丝的手摆）。只管画，喷口 / 瞄准不吃它 ——
     转的时候都还没开火。 */
  function rollOf(b) {
    const t = b.t, se = sprayEnd(b);
    if (t < T.enter) return ((PATH.roll0 || 0) + (PATH.spin || 0) * 6.2832) * (1 - easeOut(t / T.enter));
    if (t > se) return (PATH.rollOut || 0) * Math.min(1, (t - se) / T.exit) ** 2;
    return PATH.swing ? PATH.swing[0] * Math.sin((t - T.enter) * PATH.swing[1] + b.ph) * Math.min(1, (t - T.enter) / 0.4) : 0;
  }

  /* 此刻人站在哪（脚下滑板/平衡车底边中点的屏幕坐标）和缩放。
     横向按**喷口**排：o.zone() = [喷口最多伸到哪（靠对方那边）, 人的外沿最多到哪（可以出画一点）]，
     r=0 喷口顶到第一个数，r=1 外沿顶到第二个数。 */
  function pose(b) {
    if (cfg.move === 'hover') return hoverPose(b);
    const s = b.s, [near, edge] = o.zone(), wid = img ? img[0].lo.width : 400;
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
    const bob = A ? Math.sin(t * A.bob[1] + b.ph) * A.bob[0] * s : 0;                          // 平衡车上轻轻浮
    return [x, y + Math.abs(Math.sin(t * 31)) * -1.2 + bob, s];                               // 轮子压地面的细颤
  }

  /* 贴图上的点 → 屏幕坐标（没转之前）。转角：canvas 上转 φ（顺时针为正）；喷口朝 face 那边，
     仰角 θ（抬高为正）对应 φ = −face·θ，出口方向 (face·cosθ, −sinθ)。 */
  const at = (p, q) => [p[0] + (q[0] - spr.foot[0]) * p[2], p[1] + (q[1] - spr.foot[1]) * p[2]];
  function turn(q, c, th) {
    const ph = -face * th, co = Math.cos(ph), si = Math.sin(ph), dx = q[0] - c[0], dy = q[1] - c[1];
    return [c[0] + dx * co - dy * si, c[1] + dx * si + dy * co];
  }
  /* 喷口指向 th 时两层各转多少：[上身, 手臂（绝对，含上身）]。后坐 kick 把手臂往上甩、上身往后仰；
     喷的时候上身往前探 lean。没 arm 的（哥们）上身就是全部，= th。 */
  function angles(b, th) {
    if (cfg.whole) {                             // 悬空（真相喷雾）：整个人转 th，上身只额外吃后坐 / 前探；[上身额外, 喷口总指向]
      const bt = A ? A.kick[1] * b.kick - A.lean * b.lean : 0;
      return [bt, th + bt];
    }
    if (!spr.arm) {                              // 整个上身端着东西转（哥们）：后坐、前探都加在上身上
      const bt = th + (A ? A.kick[1] * b.kick - A.lean * b.lean : 0);
      return [bt, bt];
    }
    const k = A ? b.kick : 0, ln = A ? b.lean : 0;
    return [spr.body.k * th - (A ? A.lean : 0) * ln + (A ? A.kick[1] : 0) * k, th + (A ? A.kick[0] : 0) * k];
  }
  /* 贴图上的点 q 跟着人转到哪：whole 先上身绕腰转 bt，再整个人绕 whole.pivot 转 th */
  function carried(p, q, th, b) {
    const bt = angles(b, th)[0], m1 = turn(at(p, q), at(p, spr.body.pivot), bt);
    return turn(m1, at(p, cfg.whole.pivot), th);
  }
  function muzzle(p, th, b) {
    if (cfg.whole) return carried(p, spr.muzzle, th, b);
    const [bt, at_] = angles(b, th), c = at(p, spr.body.pivot), m = at(p, spr.muzzle);
    if (!spr.arm) return turn(m, c, bt);
    const sh = at(p, spr.arm.pivot), sh1 = turn(sh, c, bt);
    const m1 = turn(m, sh, at_);                   // 手臂绕肩转到 at_（绝对角），再跟着肩膀平移
    return [m1[0] + sh1[0] - sh[0], m1[1] + sh1[1] - sh[1]];
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
     雾团大、判定宽（miss 60），擦着头顶飞过也算 —— 命中点按飞到的高度记的话，爆点一路叠到头顶上方
     （男生被拖倒、脸很低时成了一根橙色烟柱）。所以 F.snap 给了就把命中点收到落点上下 snap 像素以内。
     倒地（落点第三项 'top'）：落到这一列的上沿（o.top）以下 —— 不看前沿：横躺时每一行的前沿都是
     伸出去的手臂和头，浇背的水一降到那几行就会全碎在头上。 */
  function hitTest(d, tg) {
    const past = (x) => face < 0 ? d.x <= x : d.x >= x;
    if (tg && tg[2] === 'top') {
      const top = o.top && o.top(d.x);
      return top != null && d.y >= top ? [d.x, top] : null;
    }
    if (tg && past(tg[0]) && Math.abs(d.y - tg[1]) < F.miss)
      return [tg[0], F.snap == null ? d.y : tg[1] + Math.max(-F.snap, Math.min(F.snap, d.y - tg[1]))];
    const fr = o.front(d.y);
    return fr != null && past(fr) ? [fr, d.y] : null;
  }

  function update(dt) {
    if (o.tick) o.tick();                        // 槽位管理（main.js）：人数变了就开始往新槽位滑
    for (let i = ps.length - 1; i >= 0; i--) {
      const d = ps[i];
      if (F.drag) { const k = Math.exp(-F.drag * dt); d.vx *= k; d.vy *= k; }
      d.vy += F.G * dt; d.x += d.vx * dt; d.y += d.vy * dt; d.t += dt;
      if (d.ex) { if (d.t > cfg.exhaust.life) ps.splice(i, 1); continue; }
      const b = d.b, h = hitTest(d, o.target(d.u));
      if (h) {
        ps.splice(i, 1);
        o.onSplash(h[0], h[1]);
        if (bs.includes(b) && b.hitCd <= 0) { o.onHit(h[0], h[1], b.first, b); b.first = false; b.hitCd = F.hitEvery; }
      } else if (d.y > o.ground()) { ps.splice(i, 1); if (F.floor) o.onSplash(d.x, o.ground()); }   // 落空的在地上
      else if (d.t > F.life || d.x < -80 || d.x > o.W + 80) ps.splice(i, 1);
    }
    for (let i = bs.length - 1; i >= 0; i--) {
      const b = bs[i];
      b.t += dt; b.hitCd -= dt;
      const se = sprayEnd(b);
      if (!b.landed && b.t >= T.enter) {        // 到位（刹停 / 滑停）那一刻通知 main.js（真相喷雾：刹停的冲击环）
        b.landed = true;
        if (o.onArrive) {                        // 悬空的给腰（转过之后的位置），站地的给脚底
          const p = pose(b), c = cfg.whole ? carried(p, spr.body.pivot, b.aim, b) : p;
          o.onArrive(c[0], c[1], p[2]);
        }
      }
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
      if (tg && cfg.whole) {
        /* 整个人绕 whole.pivot 倾：喷口跟着挪，不能用下面那套"按喷口反解再迭代"—— 转动半径比喷口到落点的距离还大时，
           每转一点喷口挪得比角度变得还多，迭代来回振荡（第一版立绘实测一次停在 −0.45、一次顶到上限 +0.1，要的是 −0.35）。
           改成二分：err(θ) = 从此刻喷口打中落点要的仰角 − 喷口此刻的指向。θ 往上，指向涨 1:1、要的仰角只跟着喷口的挪动慢慢变，
           err 单调减 —— 在 [lo, hi] 里二分 16 次（精度 1e-5 rad）；两头同号就贴那一头。 */
        const err = (th) => { const m = muzzle(p, th, b); return elevation(tg[0] - m[0], tg[1] - m[1]) - (angles(b, th)[1] + REST); };
        if (err(AIM.lo) <= 0) want = AIM.lo;
        else if (err(AIM.hi) >= 0) want = AIM.hi;
        else {
          let lo = AIM.lo, hi = AIM.hi;
          for (let k = 0; k < 16; k++) { const mid = (lo + hi) / 2; if (err(mid) > 0) lo = mid; else hi = mid; }
          want = (lo + hi) / 2;
        }
      } else if (tg) {
        want = b.aim;
        for (let k = 0; k < 6; k++) {
          const m0 = muzzle(p, want, b);
          want = Math.min(AIM.hi, Math.max(AIM.lo, elevation(tg[0] - m0[0], tg[1] - m0[1])));
        }
      }
      if (cfg.whole) {
        /* 整个人转：带角速度的临界阻尼（AIM.stiff），角速度限在 ±rate。直接限速跟随的话，want 一变向
           角速度一帧里从 −1.6 翻到 +1.2 rad/s，甩着的腿"咔"地换方向（离场 want 一帧跳到 0 也是）。 */
        const K = AIM.stiff;
        b.av += ((want - b.aim) * K - b.av * 2 * Math.sqrt(K)) * dt;
        b.av = Math.max(-AIM.rate, Math.min(AIM.rate, b.av));
        b.aim += b.av * dt;
      } else b.aim += Math.max(-AIM.rate * dt, Math.min(AIM.rate * dt, want - b.aim));
      b.want = want;
      b.m = null; b.eyes = null;
      const spraying = b.t >= T.enter + (T.fire || 0) && b.t <= se && tg;   // T.fire：刹停之后隔一拍再开火
      if (A) {                                   // 一段段按：每次按下后坐一震；喷的时候上身往前探
        b.kick *= Math.exp(-A.kick[2] * dt);
        b.lean += ((spraying ? 1 : 0) - b.lean) * (1 - Math.exp(-dt * 6));
        if (spraying) {
          const cyc = A.pulse[0] + A.pulse[1];
          if (b.pt === 0 || Math.floor((b.pt + dt) / cyc) > Math.floor(b.pt / cyc)) b.kick = 1;
          b.pt += dt;
        }
      }
      /* 尾焰（cfg.exhaust，真相喷雾）：罐子尾巴朝喷口反方向喷，读成"是后坐力把她顶在半空"。
         人在场就一直喷（进场刹车、悬着、离场都靠它），按住喷的时候加倍。尾焰不算命中（hitTest 跳过 ex）。 */
      if (cfg.exhaust && b.t <= se + T.exit) {
        const X = cfg.exhaust;
        const th = b.aim, r = carried(p, X.at, th, b), r0 = b.exP || r;
        /* 人一动（进场 3000~8000 px/s），按时间匀速出的尾焰两团之间差出几十上百像素，断成一串珠子：
           按罐尾这一帧挪了多远补发（每 X.gap 像素至少一团），出生点沿上一帧→这一帧的罐尾摆开、按出生时刻补飞。 */
        const n0 = b.ex + dt * X.rate * (spraying ? 2 : 1) + Math.hypot(r[0] - r0[0], r[1] - r0[1]) / X.gap;
        const n = Math.floor(n0);
        b.ex = n0 - n; b.exP = r;
        /* 方向：悬着时朝罐子反方向；冲下来刹车、往上冲走时朝正下方（她往上顶全靠它）。进场从全朝下渐变到罐尾方向。 */
        const dn = b.t < T.enter ? 1 - b.t / T.enter : b.t > se ? Math.min(1, (b.t - se) / 0.2) : 0;
        const dir = (angles(b, th)[1] + REST) * (1 - dn) + (Math.PI / 2) * dn;
        for (let i = 0; i < n; i++) {
          const f = (i + 1) / n, age = (1 - f) * dt;
          const a = dir + (Math.random() - 0.5) * 2 * X.spread, v = X.V * (0.7 + Math.random() * 0.6);
          const vx = -face * v * Math.cos(a), vy = v * Math.sin(a);
          ps.push({ x: r0[0] + (r[0] - r0[0]) * f + vx * age, y: r0[1] + (r[1] - r0[1]) * f + vy * age,
                    vx, vy, t: age, u: 0, b, seq: -1, j: 1, ex: true });
        }
      }
      if (!spraying) continue;
      if (A && (b.pt % (A.pulse[0] + A.pulse[1])) > A.pulse[0]) { b.emit = 0; continue; }   // 松开那一下
      /* 喷：从转过之后的喷口，沿喷口方向，速度 V（雾再加一点散角和快慢）。一帧攒够几个就出几个，
         每个按它**实际该出口的时刻**补飞一段（age）—— 不补的话帧一卡几个叠成一坨，水柱起疙瘩。 */
      b.emit += dt * F.rate * (o.rateK ? o.rateK() : 1);   // rateK：同边几个人一起喷时各自减量（main.js，F2）
      const m = b.m = muzzle(p, b.aim, b), dir = angles(b, b.aim)[spr.arm || cfg.whole ? 1 : 0] + REST;   // 沿喷口此刻真的指向（含后坐）
      if (spr.eyes) b.eyes = spr.eyes.map(q => carried(p, q, b.aim, b));   // 射线从几只眼睛各出一道（内裤外穿侠两只、二郎一只天眼）
      while (b.emit >= 1) {
        b.emit -= 1;
        const age = b.emit / F.rate, a = dir + (Math.random() - 0.5) * 2 * F.spread;
        const v = F.V * (1 + (Math.random() - 0.5) * 2 * F.vJit);
        const vx = face * v * Math.cos(a), vy = -v * Math.sin(a);
        ps.push({ x: m[0] + vx * age, y: m[1] + vy * age + 0.5 * F.G * age * age, vx, vy: vy + F.G * age,
                  t: age, u, b, seq: b.seq++, j: Math.random() });
      }
    }
  }

  /* 画的顺序（层级）交给 main.js：items() 给出这一帧要画的每一样东西和它的远近 s，main.js 把哥们、闺蜜的
     合在一起按 s 从远到近排，全画在**两个主角之前**。
     每个人自己的那股水 / 雾紧跟在他本人之后（从他枪口出来，盖在他身上），被比他近的人挡住。
     喷的东西在主角身后：帮手站得比主角远，水 / 雾从主角身后穿过去，碰到对方身体轮廓就被对方挡住 ——
     "被挡住的那一截"本身就读成打中了（溅开的水花在特效层，照样盖在人身上）。
     画在主角之上的话（第一版），哥们的水从男生脑袋上横穿过去，像把男生的头切开。 */
  function items() {
    if (!img) return [];
    const out = [], groups = new Map();
    for (const d of ps) { const g = groups.get(d.b); g ? g.push(d) : groups.set(d.b, [d]); }
    const front = !!cfg.front;                   // 站在主角前面（真相喷雾）：main.js 把它们挪到主角之后画
    /* 悬停的人按此刻的缩放排（槽位会变：1 号前排 s 最大、画在最上），站地的按召唤时定的远近 */
    const sOf = (b) => cfg.move === 'hover' && bs.includes(b) ? pose(b)[2] : b.s;
    for (const b of bs) out.push({ s: sOf(b), front, draw: (ctx) => drawOne(ctx, b) });
    /* 人已离场、水还在飞的，按原来那个人的远近画 */
    for (const [b, g] of groups) out.push({ s: sOf(b) + 1e-6, front, draw: (ctx) => F.draw(ctx, g, bs.includes(b) ? b : null) });
    return out;
  }

  /* 一个人：上身系里先画手臂（再绕肩转）、再画上身，最后画不动的下身（lo 可无：单层立绘整个人就是 body）。
     cfg.aura（可无）：画在本人身后、跟着她一起倾的东西（真相女神的光芒、光环），给它贴图点 → 屏幕的换算。 */
  function drawOne(ctx, b) {
    const p = pose(b), [x, y, s] = p, [bt, at_] = cfg.whole ? [angles(b, b.aim)[0], 0] : angles(b, b.aim);
    const X = x - spr.foot[0] * s, Y = y - spr.foot[1] * s;
    const I = img[b.skin], put = (im) => ctx.drawImage(im, X, Y, im.width * s, im.height * s);
    const spin = (q, th) => { const [cx, cy] = at(p, q); ctx.translate(cx, cy); ctx.rotate(-face * th); ctx.translate(-cx, -cy); };
    const rl = cfg.move === 'hover' ? rollOf(b) : 0;
    /* cfg.extra（可无）：画在屏幕坐标里、不跟着人倾的东西（黑蛛女特工的丝、哮天犬）。carry(q) 给贴图点转过之后的屏幕位置
       （不含进出场的 roll —— 丝绕抓丝的手摆，手本身不动）。先画 'back' 层，人画完再画 'fore' 层。 */
    const carry = (q) => cfg.whole ? carried(p, q, b.aim, b) : at(p, q);
    if (cfg.extra) cfg.extra(ctx, b, s, carry, 'back', xi);
    ctx.save();
    if (rl) { const [cx, cy] = at(p, PATH.pivot || cfg.whole.pivot); ctx.translate(cx, cy); ctx.rotate(rl); ctx.translate(-cx, -cy); }
    if (cfg.whole) spin(cfg.whole.pivot, b.aim);  // 悬空：整个人先绕重心转，上身再在这个基础上吃后坐
    if (cfg.aura) cfg.aura(ctx, b, s, (q) => at(p, q));
    ctx.save();
    spin(spr.body.pivot, bt);
    if (I.arm) { ctx.save(); spin(spr.arm.pivot, at_ - bt); put(I.arm); ctx.restore(); }
    put(I.body);
    ctx.restore();
    if (I.lo) put(I.lo);
    ctx.restore();
    if (cfg.extra) cfg.extra(ctx, b, s, carry, 'fore', xi);
  }

  const active = () => bs.length > 0;
  function reset() { bs.length = 0; ps.length = 0; }

  /* 诊断用：在场的人（只读），?crewlog=1 时 main.js 打印瞄准角 */
  const peek = () => bs;
  const width = () => (img ? img[0].body.width : 0);   // 贴图宽（main.js 槽位按外框中线排）
  /* 诊断（?crewlog=1）：这个人此刻画出来的实心范围 [x0, y0, x1, y1]（屏幕像素，alpha > 200：剪影 + 贴着轮廓的那圈亮边，
     不含外圈柔光）。在离屏画布上真画一遍再扫像素 —— 按贴图外框算的话，斜着的人外框角远大于剪影，量不出中线余量。 */
  let mc = null;
  function measure(b) {
    if (!img) return null;
    if (!mc) { mc = document.createElement('canvas'); mc.width = o.W; mc.height = 1400; }
    const c = mc.getContext('2d', { willReadFrequently: true });
    c.clearRect(0, 0, mc.width, mc.height); drawOne(c, b);
    const d = c.getImageData(0, 0, mc.width, mc.height).data;
    let x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
    for (let y = 0; y < mc.height; y++) for (let x = 0; x < mc.width; x++) {
      if (d[(y * mc.width + x) * 4 + 3] <= 200) continue;
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
    return x1 < 0 ? null : [x0, y0, x1, y1];
  }
  return { init, load, summon, update, items, active, reset, peek, left, freeSkins, width, measure, where: (b) => pose(b), cfg };
}
Crew.born = 0;                                   // 召唤流水号：同边几个人按到场先后排槽（新来的占 1 号前排）

/* 一组帮手合起来调度（档 4 每边三个人，各是一份 Crew、max 1）：送一次召一个**没在场**的成员（随机挑）；
   三个都在场了（含正在离场的），给剩余时间最短的那个 summon —— max 1 的 Crew 满员时就是续一段 T.spray、
   名字条重播「×N」；正在离场的剩余时间是负的，最先被挑中，从当前高度被叫回来（hoverPose 的 back）。
   pick（可无）：强制召第几个成员（诊断参数 ?g4L= / ?g4R=，越界夹到两头）。 */
function CrewGroup(members) {
  return {
    members,
    summon(pick) {
      if (pick != null && !Number.isNaN(pick)) return members[Math.max(0, Math.min(members.length - 1, pick | 0))].summon();
      const off = members.filter(m => !m.active());
      if (off.length) return off[Math.floor(Math.random() * off.length)].summon();
      members.reduce((a, c) => (a.left() <= c.left() ? a : c)).summon();
    },
    active: () => members.some(m => m.active()),
    reset: () => members.forEach(m => m.reset()),
  };
}

/* 水柱（哥们）。ps 是同一个人喷出去的水滴（按出口顺序），b 是这个人（已离场为 null）。
   相邻两滴连成一段，外加一段喷口 → 最新一滴（最新那滴已经飞了最多一帧 ~23 像素，不补的话水柱跟枪口之间是空的）。
   第一版三遍等粗描线（深蓝描边 26 → 浅蓝 19 → 白芯 6）读成**光柱**：从头到尾一样粗、白芯连成一条、边缘硬，
   是霓虹灯管不是水。水该有的几样：
     · 出口细、越飞越散越粗（WATER.w0 → w1，飞 grow 秒长满），也越飞越透（a1）；
     · 飞到后半段（t > breakT）会断：每滴出口时抽一次，WATER.brk 的概率在它身后断开，断开处两头画成水珠；
     · 高光不是一条线，是贴着上沿、一段有一段没有的碎亮光（seq 按 glint 取模）；
     · 水柱周围甩出细水沫（每滴按自己的随机数 j 偏到两侧）。
   颜色仍要深蓝托底（浅蓝在浅绿墙上不描边就化掉），但托底是半透明的淡描边，不是实线框。 */
const WATER = {
  w0: 7, w1: 20, grow: 0.3,          // 出口宽、长满宽（像素）、多久长满（秒）
  a1: 0.55,                          // 飞到 grow 之后水身剩多少不透明度（出口 1）
  breakT: 0.14, brk: 0.16,           // 飞过多少秒以后开始会断、每滴身后断开的概率
  edge: [40, 110, 190], body: [150, 214, 255], glint: [4, 7],   // 描边色、水身色、高光：每 7 段亮 4 段
  mist: 0.35,                        // 水沫：每滴甩出的概率（按 j 取，同一滴每帧一样，不闪）
};
function drawStream(ctx, ps, b) {
  const W = WATER, wOf = (d) => W.w0 + (W.w1 - W.w0) * Math.min(1, d.t / W.grow);
  const aOf = (d) => 1 - (1 - W.a1) * Math.min(1, d.t / W.grow);
  /* 连成段：[前一滴, 这一滴]；喷口那一段用一个 t=0 的假水滴 */
  const segs = [];
  for (let i = 1; i < ps.length; i++) {
    const p = ps[i - 1], d = ps[i];
    if (d.seq !== p.seq + 1 || Math.hypot(d.x - p.x, d.y - p.y) > 60) continue;
    if (d.t > W.breakT && d.j < W.brk) continue;           // 断开
    segs.push([p, d]);
  }
  const last = ps[ps.length - 1];
  if (b && b.m && last && Math.hypot(last.x - b.m[0], last.y - b.m[1]) < 60)
    segs.push([last, { x: b.m[0], y: b.m[1], t: 0, seq: last.seq + 1, j: 1 }]);
  ctx.lineCap = 'round';
  const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a.toFixed(3)})`;
  /* 描边 → 水身：两遍，每段按两头的平均宽度/透明度 */
  for (const [pad, col, k] of [[5, W.edge, 0.5], [0, W.body, 0.85]]) {
    for (const [p, d] of segs) {
      const m = { t: (p.t + d.t) / 2 };
      ctx.lineWidth = wOf(m) + pad; ctx.strokeStyle = rgba(col, aOf(m) * k);
      ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(d.x, d.y); ctx.stroke();
    }
  }
  /* 断开之后的水珠：后半段没连上的水滴，各画一颗 */
  const linked = new Set(); for (const [p, d] of segs) { linked.add(p); linked.add(d); }
  for (const d of ps) {
    if (linked.has(d) && d.j >= W.brk) continue;
    const r = wOf(d) * (0.35 + 0.2 * ((d.j * 7) % 1));   // 大小按 j 散开一点，同一滴每帧一样
    ctx.fillStyle = rgba(W.edge, aOf(d) * 0.6); ctx.beginPath(); ctx.arc(d.x, d.y, r + 2, 0, 6.283); ctx.fill();
    ctx.fillStyle = rgba(W.body, aOf(d) * 0.9); ctx.beginPath(); ctx.arc(d.x, d.y, r, 0, 6.283); ctx.fill();
  }
  /* 碎高光：贴着上沿（法线朝上那侧偏 1/4 宽），隔几段亮一段 */
  ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(255,255,255,.85)'; ctx.beginPath();
  for (const [p, d] of segs) {
    if (d.seq % W.glint[1] >= W.glint[0]) continue;
    const dx = d.x - p.x, dy = d.y - p.y, L = Math.hypot(dx, dy) || 1;
    let nx = dy / L, ny = -dx / L; if (ny > 0) { nx = -nx; ny = -ny; }
    const o = wOf({ t: (p.t + d.t) / 2 }) * 0.25;
    ctx.moveTo(p.x + nx * o, p.y + ny * o); ctx.lineTo(d.x + nx * o, d.y + ny * o);
  }
  ctx.stroke();
  /* 水沫：飞过 breakT 的水滴，按 j 甩到两侧一点 */
  for (const d of ps) {
    if (d.t < W.breakT || d.j > W.mist) continue;
    const k = d.j / W.mist, off = (k - 0.5) * 2 * wOf(d) * 1.3, r = 1.8 + 2 * k;
    const vl = Math.hypot(d.vx, d.vy) || 1, x = d.x - d.vy / vl * off, y = d.y + d.vx / vl * off;
    ctx.fillStyle = rgba(W.edge, 0.55); ctx.beginPath(); ctx.arc(x, y, r + 1.2, 0, 6.283); ctx.fill();
    ctx.fillStyle = rgba(W.body, 0.95); ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
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

/* 哥们：v14/buddy/skate1~3.png 踩滑板端水枪。rot = 腰以上（绕裤腰正中转），fix = 裤子、腿、滑板。
   aim：最低 lo（再往下弯就不是端枪是鞠躬了）、最高 hi，rate 每秒最多转多少（瞄点跳过手机那行是跳变，
   枪不能瞬移），follow 瞄点平滑跟随的快慢。
   sweep：瞄点在对方身上 u=0.5 附近两个不公约的正弦叠起来乱扫；w 要跟水在空中的时间（~0.35s）比，
   快了（2.3/5.3 rad/s）前后水滴落点差太远，水柱折成"7"字，1.2/2.8 才是一条顺着甩的抛物线。
   zone：对方倒地后每 every 秒随机换一个部位（u∈lo~hi：后脑、背、屁股、腿），在它前后 ±span 扫。
   fluid：出口速度 V、重力 G，每人每秒 rate 滴；miss、snap 见 hitTest；hitEvery 每人多久补一下命中反馈。 */
const Buddy = Crew({
  face: -1,
  spr: { src: 'assets/world/buddy%n_%k.webp', body: { src: 'up', pivot: [266, 190], k: 1 }, lo: { src: 'lo' },
         foot: [260, 436], muzzle: [2, 78] },
  skins: [1, 2, 3],                 // skate1 棕发护目镜花短裤红滑板 / skate2 反戴红帽黑短裤蓝滑板 / skate3 金发花衬衫迷彩裤黄滑板
  T: { enter: 0.55, spray: 2.5, exit: 0.5 },
  max: 3, gap: 0.3,
  rows: [[0.74, 0.80], [0.66, 0.71], [0.58, 0.63]],
  aim: { lo: -0.52, hi: 0.21, rate: 2.4, follow: 10 },
  sweep: { a: [0.32, 0.2], w: [1.2, 2.8] },
  zone: { every: 1.0, lo: 0.2, hi: 0.85, span: 0.1 },
  fluid: { V: 1250, G: 900, drag: 0, rate: 55, spread: 0, vJit: 0, life: 1.6, miss: 90, hitEvery: 0.3, floor: true,
           draw: drawStream },
});

/* 闺蜜：v14/bestie/src2~4.png 比基尼、踩平衡车、单手伸直举一罐小灭火器那么大的防狼喷雾。
   arm = 伸直的右臂 + 喷雾罐（绕肩），body = 腰以上（绕腰，转总仰角的 k 份：跟着往下瞄时上身一起前倾），lo = 腰以下 + 平衡车。
   只瞄男生的脸（喷雾就是冲眼睛去的），所以 sweep 幅度小、不分倒地部位（zone: null）。
   aim.lo -0.7：男生被拖倒后脸贴着地，-0.35 压不下去，雾从他头顶上飘过去。
   anim：pulse [按几秒, 松几秒]；kick [手臂往上甩, 上身往后仰, 衰减快慢]；lean 喷的时候上身往前探多少；bob [浮多高, 多快]。
   fluid：雾出口快、阻力大（drag）、几乎不受重力，飞一段就散（life）；每个雾团 ±spread 散角、±vJit 快慢，
   合起来是一个张开的喷锥。雾要**密而透**：雾团多（rate 90）、彼此重叠连成一片，但每团很淡（见 drawMist）。
   太浓（不透明度 0.5）三个人一起喷成一条橙色烟带，读成喷火器；太稀（rate 45、半径小）是一串分开的橙点。 */
const MIST = {
  face: +1,
  spr: { src: 'assets/world/bestie%n_%k.webp', arm: { src: 'arm', pivot: [127, 103] },
         body: { src: 'up', pivot: [103, 200], k: 0.3 }, lo: { src: 'lo' },
         foot: [113, 483], muzzle: [290, 18] },
  skins: [1, 2, 3],                 // src2 棕色高马尾红比基尼白平衡车 / src3 黑短发条纹比基尼粉平衡车 / src4 金发双马尾黑比基尼紫平衡车
  anim: { pulse: [0.42, 0.14], kick: [0.12, 0.05, 10], lean: 0.08, bob: [3, 2.6] },
  T: { enter: 0.55, spray: 2.5, exit: 0.5 },
  max: 3, gap: 0.3,                 // = 形象数：满员时续时间，不会加出重复形象
  rows: [[0.74, 0.80], [0.66, 0.71], [0.58, 0.63]],
  aim: { lo: -0.7, hi: 0.35, rate: 2.4, follow: 10 },
  sweep: { a: [0.3, 0.15], w: [1.3, 3.1] },
  zone: null,
  fluid: { V: 1100, G: 60, drag: 1.0, rate: 90, spread: 0.1, vJit: 0.15, life: 0.8, miss: 60, snap: 12, hitEvery: 0.3, floor: false,
           draw: drawMist },
};
const Bestie = Crew(MIST);

/* 真相雾（闺蜜第三个形象：真相喷雾）。每个雾团出口时小、越飞越胀越淡；三遍画：
     深绿托底（明亮底图上发光靠不住，实体靠轮廓）→ 亮青柠雾身 → 雾里夹带的星星和聊天气泡。
   雾团按出生时的随机数 j 分三种：j < TRUTH_FX.chat 是聊天气泡、再往上到 star 是星星、其余是雾。
   同一团每帧同一种，不闪。喷口上还有一朵按喷射节奏闪的喷口焰（b.m 只在按住喷的时候有）。 */
const TRUTH_FX = {
  r0: 30, r1: 110,                        // 雾团出口半径 → 飞完的半径（像素）。出口就是大团 = 读成高压喷出来的（10 时喷口前只有两三团小点）；
                                          // 2026-09-27 用户要"范围更大、更夸张，符合最高级礼物"：20/56 → 30/110，雾锥盖住男生整个上半身
  rim: [28, 120, 46], body: [156, 238, 96], core: [236, 255, 200],   // 深绿托底 / 雾身 / 喷口附近的亮芯
  a: [0.13, 0.2],                         // 托底、雾身每团的不透明度（雾团多、互相叠，单团要淡，见 MIST 的教训）
  chat: 0.035, star: 0.1,                 // 夹带气泡、星星的比例
  chatFill: [255, 255, 255], starFill: [255, 251, 210],   // 气泡、星星的填色（描边用 rim）
  icon: [15, 30],                         // 气泡 / 星星 出口半宽 → 飞完的半宽
  flare: [40, 64],                        // 喷口焰半径 [小, 大]，随喷射节奏在两者间跳。第一版喷口离脸 ~110px 时只能 20~32（再大盖掉半股喷流）；
                                          // 第二版立绘人抬高了、喷口离脸 ~400px，放大到 40~64 读成"大炮开火"
  exK: 0.32,                              // 尾焰雾团按喷雾的几成大：罐尾在她脑后，雾团放大后 0.6 成的尾焰整团糊在她脸上
  aura: { rays: 16, ray: 0.07, R: 360, spin: 0.35, a: 0.42, rgb: [255, 225, 120],   // 身后光芒：几道、每道半角、多长、转速 rad/s、中心不透明度
          halo: [58, 15], haloY: 28, haloW: [11, 4], halo1: [255, 170, 40], halo2: [255, 246, 200] },   // 光环：半轴、悬在头顶上方多高、外圈 / 内圈线宽、颜色
};
/* 女神的光：身后一圈放射光芒（慢慢转、往外渐隐）+ 头顶一个光环。画在她本人之前、跟着她一起倾（crew.js drawOne 的 cfg.aura）。
   剪影的三层金色外发光是烘在贴图里的（v14/truth/make2.py），这两样要动，所以运行时画。
   配色：明亮底图上 lighter 加不上去，发光靠色相 —— 金色光芒在浅绿墙 / 粉墙上靠饱和度跳出来，光环外圈橙金托底、内圈近白。 */
function drawAura(ctx, b, s, at) {
  const A = TRUTH_FX.aura, [cx, cy] = at(TRUTH.spr.chest), [hx, hy] = at(TRUTH.spr.head);
  const k = Math.min(1, b.t / 0.3), R = A.R * s;                 // 冲进来的头 0.3 秒里长出来
  ctx.save();
  const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
  g.addColorStop(0, `rgba(${A.rgb},${(A.a * k).toFixed(3)})`); g.addColorStop(0.45, `rgba(${A.rgb},${(A.a * 0.45 * k).toFixed(3)})`);
  g.addColorStop(1, `rgba(${A.rgb},0)`);
  ctx.fillStyle = g; ctx.beginPath();
  for (let i = 0; i < A.rays; i++) {
    const a = i / A.rays * 6.283 + b.t * A.spin, w = A.ray * (i % 2 ? 0.6 : 1);   // 一长一短交替，不像齿轮
    ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(a - w) * R, cy + Math.sin(a - w) * R); ctx.lineTo(cx + Math.cos(a + w) * R, cy + Math.sin(a + w) * R);
  }
  ctx.fill();
  const y = hy - A.haloY * s + Math.sin(b.t * 2.4) * 3 * s, rx = A.halo[0] * s, ry = A.halo[1] * s;
  ctx.globalAlpha = k;
  ctx.lineWidth = A.haloW[0] * s; ctx.strokeStyle = `rgba(${A.halo1},0.85)`;
  ctx.beginPath(); ctx.ellipse(hx, y, rx, ry, 0, 0, 6.283); ctx.stroke();
  ctx.lineWidth = A.haloW[1] * s; ctx.strokeStyle = `rgb(${A.halo2})`;
  ctx.beginPath(); ctx.ellipse(hx, y, rx, ry, 0, 0, 6.283); ctx.stroke();
  ctx.restore();
}
/* F：配色尺寸表（TRUTH_FX / DEMON_FX），C：角色配置（寿命在 C.fluid / C.exhaust）。真相女神、灭迹恶魔共用这一套画法，只换颜色。 */
function drawSpray(F, C, ctx, ps, b) {
  const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a.toFixed(3)})`;
  const us = (d) => Math.min(1, d.t / (d.ex ? C.exhaust.life : C.fluid.life));   // 尾焰按自己的寿命走
  for (const [pad, col, a] of [[5, F.rim, F.a[0]], [0, F.body, F.a[1]]]) {
    for (const d of ps) {
      if (d.j < F.star) continue;
      const u = us(d), r = (F.r0 + (F.r1 - F.r0) * Math.sqrt(u)) * (d.ex ? F.exK : 1) + pad;   // 尾焰小几号
      ctx.fillStyle = rgba(col, (1 - u * u) * a);
      ctx.beginPath(); ctx.arc(d.x, d.y, r, 0, 6.283); ctx.fill();
    }
  }
  /* 亮芯：刚出口的一小段（u < 0.25）叠一层近白，读成"高压喷出来的"而不是飘出来的 */
  for (const d of ps) {
    const u = us(d);
    if (d.j < F.star || u > 0.25) continue;
    ctx.fillStyle = rgba(F.core, (1 - u / 0.25) * 0.35);
    ctx.beginPath(); ctx.arc(d.x, d.y, F.r0 * 0.8 + 20 * u, 0, 6.283); ctx.fill();
  }
  /* 喷口焰：八角尖星 + 深绿描边，大小随后坐（b.kick）跳 */
  if (b && b.m) {
    const r = F.flare[0] + (F.flare[1] - F.flare[0]) * b.kick, [mx, my] = b.m;
    ctx.save(); ctx.translate(mx, my); ctx.rotate(b.t * 3);
    ctx.beginPath();
    for (let i = 0; i < 16; i++) { const a = i * 0.3927, rr = i % 2 ? r * 0.38 : r; i ? ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : ctx.moveTo(rr, 0); }
    ctx.closePath();
    ctx.fillStyle = rgba(F.body, 0.9); ctx.fill(); ctx.lineWidth = 4; ctx.strokeStyle = rgba(F.rim, 0.9); ctx.stroke();
    ctx.fillStyle = rgba(F.core, 0.95); ctx.beginPath(); ctx.arc(0, 0, r * 0.3, 0, 6.283); ctx.fill();
    ctx.restore();
  }
  /* 星星、气泡：实体、描边，盖在雾上；越飞越大、最后 30% 淡掉 */
  for (const d of ps) {
    if (d.j >= F.star) continue;
    const u = us(d), r = F.icon[0] + (F.icon[1] - F.icon[0]) * Math.sqrt(u), a = u > 0.7 ? (1 - u) / 0.3 : 1;
    ctx.save(); ctx.globalAlpha = a; ctx.translate(d.x, d.y);
    if (d.j < F.chat) {
      ctx.rotate(Math.sin(d.t * 5 + d.j * 90) * 0.2);
      drawChatIcon(ctx, r, rgba(F.chatFill, 1), rgba(F.rim, 1), 3, rgba(F.rim, 1));
    } else {
      ctx.rotate(d.t * 4 + d.j * 40);
      ctx.beginPath();
      for (let i = 0; i < 8; i++) { const an = i * 0.7854, rr = i % 2 ? r * 0.3 : r * 0.9; i ? ctx.lineTo(Math.cos(an) * rr, Math.sin(an) * rr) : ctx.moveTo(rr, 0); }
      ctx.closePath();
      ctx.fillStyle = rgba(F.starFill, 1); ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = rgba(F.rim, 1); ctx.stroke();
    }
    ctx.restore();
  }
}

/* 真相喷雾：v14/truth/src2.png（第一版 src1.png 横扛在右肩，已换掉）。用户认可的概念图（concept/gift-spray/）改出来的游戏立绘：
   金发绿挑染、青柠色赛车服短裙白色过膝靴，腰侧夹一罐比她人还长的「真相喷雾」、罐口斜朝右下，身外一圈金光（女神）。
   女生第五档礼物「真相女神」（档 4 左，GIFT.truth，2026-09-27 替掉戒指盒；之前短暂当过闺蜜的第三个形象）。
   档 4 的"贵"靠出场：她冲下来的那 1.4 秒全场压暗、只有她亮着，再打一条名字条（main.js truthIntro）。

   **她不站地，被罐子的后坐力顶在半空**（move 'hover'，悬停点 main.js perch）。为什么：竖屏里两个主角占着下半屏中间，
   女主左边只剩 ~100 像素宽，大号全身角色塞不进去 —— 试过两版站地的：
     · 站女主身后（s 0.9）：身子和脸被女主的长发挡掉一大半，只剩腿和罐子，而这个角色要看的恰恰是被挡的那部分；
     · 站女主左前方、画在主角前面（s 1.08）：罐子横着把女主的脸整个盖住，她自己一半出画。
   整个画面唯一大块的空地是上半屏的墙，所以让她悬在左上方：全身都露着、谁也不挡，罐子斜着往下对准男生的脸。
   · 整个人绕腰胯小幅前后倾着瞄（whole.pivot）：罐子本来就朝右下，人始终是竖着的（第二版立绘，见下面 whole 的注释）。
     在此基础上只吃后坐（anim.kick[1]）和前探（lean）。
   · 尾焰（exhaust）：罐子尾巴一直往反方向喷青柠色的气，喷的时候加倍 —— 这是"为什么她能悬着"的全部解释。
   · 来：从画外顶上冲下来刹停（T.enter），刹停那一刻 main.js onArrive 出一圈冲击环；走：原地往上加速冲出去（T.exit）。
   · 喷法：anim.pulse 一长段"呲——"（0.7 秒）松一下（0.16），每次按下上身往上一震；bob 是悬着的上下浮。
     雾量比平衡车闺蜜大得多：雾团多（rate 220）、胀得大（TRUTH_FX.r1 110）、飞得远（life 1.15）。
     出口慢（fluid.V 650，平衡车 1100）：喷口离男生脸只有 ~110 像素，V 1250 时 0.09 秒就到脸上，路上只剩两三团，
     看不到"一股雾冲出去"；减半后路上的雾团翻倍、连成一个锥。
   · front：画在两个主角之前（她在半空、离镜头近，雾从她身前喷出去）。 */
const TRUTH = {
  face: +1,
  move: 'hover', front: true,
  /* 第二版立绘（2026-09-27，v14/truth/make2.py）：竖直悬浮、罐子夹在腰侧本来就斜朝右下（rest −0.505 rad ≈ 29°），
     单层（没有 lo）、三层金色外发光烘在贴图里。整个人绕腰胯（whole.pivot，重心附近）小幅前后倾着瞄：
     倾的时候头和脚一左一右摆、人留在画内；瞄准用二分反解（update）。量点都是贴图像素，由 make2.py 打印。
     第一版（truth1_*，横扛罐子）要前倾 0.7~1 rad 才对得准，人一抬高放大就甩出画面，见 make2.py 文件头。 */
  whole: { pivot: [168, 281] },
  exhaust: { at: [119, 195], rate: 40, V: 420, spread: 0.18, life: 0.4, gap: 14 },   // 罐尾（贴图像素）、每秒几团、出口速度、散角、寿命、人动时两团最多隔几像素
  spr: { src: 'assets/world/truth%n_%k.webp', body: { src: 'up', pivot: [168, 281], k: 1 },
         foot: [160, 608], muzzle: [370, 334], rest: -0.505, head: [211, 78], chest: [194, 185] },
  skins: [2],
  aura: (ctx, b, s, at) => drawAura(ctx, b, s, at),
  anim: { pulse: [0.7, 0.16], kick: [0, 0.06, 9], lean: 0.03, bob: [5, 2.2] },
  T: { enter: 0.55, spray: 2.8, exit: 0.45, fire: 0.18 },   // fire：刹停后隔多久开喷（先"嘭"地停住，再"呲——"）
  max: 1, gap: 0.3,
  rows: [[0.94, 0.96]],                   // 贴图里人高 566 → 画面里 ~535，占女生这半边的左上（用户："整体再大一些，占女生这半边一半区域"）
  aim: { lo: -0.6, hi: 0.3, rate: 1.6, follow: 8, stiff: 40 },    // 前后倾的范围：罐子本来就朝下，站着的男生只要小倾；stiff 见 update 临界阻尼
  sweep: { a: [0.25, 0.12], w: [1.2, 2.9] },
  zone: null,
  /* 2026-09-27 放大（审查在引擎里实测过，雾锥盖住男生整个上半身，p5 / p95 都打得中）：rate 120 → 220、spread 0.13 → 0.28、
     life 0.95 → 1.15（喷口离脸从 ~110 变成 ~400 像素，要飞得到）、miss 70 → 150（雾锥宽了，判定跟着宽） */
  fluid: { V: 650, G: 40, drag: 0.85, rate: 220, spread: 0.28, vJit: 0.18, life: 1.15, miss: 150, snap: 14, hitEvery: 0.25, floor: false,
           draw: (ctx, ps, b) => drawSpray(TRUTH_FX, TRUTH, ctx, ps, b) },
};
const Truth = Crew(TRUTH);

/* 灭迹恶魔（男生档 4，GIFT.demon，2026-09-27 替掉相框）。用户：「男生这边可以召唤一个男恶魔，对应对方的女神」。
   跟真相女神左右对称：悬在右上、面朝左，腰侧夹一罐「一键清空」、罐口本来就斜朝左下（spr.rest），整个人绕腰胯小幅前后倾着瞄
   女生的脸；喷出暗紫色的"撤回烟雾"，打中了从她脸上蹦「已撤回」「记录已清空」（main.js RECIPE.demon）——
   灭迹党要的就是把聊天记录删干净。立绘 v14/demon/make.py：单层、暗红 → 紫 → 品红三层外发光烘在贴图里，量点由它打印。
   运行时画的：身后一团慢慢转的黑紫烟雾 + 几道暗红裂光（女神是金色光芒），两只角发光（女神是光环）。
   喷法、节奏、雾量跟女神一样（档 4 对档 4），只换颜色。 */
const DEMON_FX = {
  ...TRUTH_FX,
  rim: [40, 10, 60], body: [150, 80, 220], core: [236, 214, 255],    // 深紫托底 / 紫雾身 / 喷口亮芯
  chatFill: [150, 152, 162], starFill: [255, 150, 225],             // 雾里夹带的灰色气泡（被撤回的消息）、品红星
  aura: { R: 330, spin: 0.25, smoke: [[40, 12, 60], [95, 30, 130]], puffs: 9, a: 0.4,   // 身后烟雾：多大、转速、两种烟色、几团、不透明度
          crack: [200, 30, 70], cracks: 7, crackA: 0.75,                               // 暗红裂光：颜色、几道、不透明度
          horn: [255, 120, 220], horns: [[208, 54], [191, 67]], hornR: 26 },           // 角的光：颜色、两只角尖（贴图像素）、光团半径
};
function drawDemonAura(ctx, b, s, at) {
  const A = DEMON_FX.aura, [cx, cy] = at(DEMON.spr.chest);
  const k = Math.min(1, b.t / 0.3), R = A.R * s;
  ctx.save();
  /* 烟雾：几团大软球绕胸口慢慢转，各自一呼一吸 —— 不是一个圆盘 */
  for (let i = 0; i < A.puffs; i++) {
    const a = i / A.puffs * 6.283 + b.t * A.spin, rr = R * (0.35 + 0.25 * Math.sin(i * 2.1 + b.t * 0.8));
    const x = cx + Math.cos(a) * rr, y = cy + Math.sin(a) * rr * 0.8, r = R * (0.38 + 0.08 * Math.sin(i * 1.7 + b.t * 1.3));
    const c = A.smoke[i % 2], g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(${c},${(A.a * k).toFixed(3)})`); g.addColorStop(1, `rgba(${c},0)`);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
  }
  /* 裂光：从胸口往外几道折线，一闪一闪 */
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (let i = 0; i < A.cracks; i++) {
    const a0 = i / A.cracks * 6.283 + 0.4 + b.t * A.spin * 0.5, fl = 0.55 + 0.45 * Math.sin(b.t * 7 + i * 2.3);
    ctx.strokeStyle = `rgba(${A.crack},${(A.crackA * fl * k).toFixed(3)})`; ctx.lineWidth = 5 * s;
    ctx.beginPath(); ctx.moveTo(cx + Math.cos(a0) * R * 0.25, cy + Math.sin(a0) * R * 0.25);
    for (let j = 1; j <= 3; j++) {
      const a = a0 + (j % 2 ? 0.12 : -0.1), d = R * (0.25 + j * 0.22);
      ctx.lineTo(cx + Math.cos(a) * d, cy + Math.sin(a) * d);
    }
    ctx.stroke();
  }
  /* 角：两团品红光垫在角尖后面 */
  for (const q of A.horns) {
    const [x, y] = at(q), r = A.hornR * s * (0.85 + 0.15 * Math.sin(b.t * 4)), g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(${A.horn},${(0.9 * k).toFixed(3)})`); g.addColorStop(1, `rgba(${A.horn},0)`);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
  }
  ctx.restore();
}
const DEMON = {
  ...TRUTH,
  face: -1,
  whole: { pivot: [216, 258] },
  exhaust: { ...TRUTH.exhaust, at: [287, 179] },
  spr: { src: 'assets/world/demon%n_%k.webp', body: { src: 'up', pivot: [216, 258], k: 1 },
         foot: [244, 555], muzzle: [53, 305], rest: -0.497, head: [204, 59], chest: [202, 152] },
  skins: [1],
  aura: (ctx, b, s, at) => drawDemonAura(ctx, b, s, at),
  fluid: { ...TRUTH.fluid, draw: (ctx, ps, b) => drawSpray(DEMON_FX, DEMON, ctx, ps, b) },
};
const Demon = Crew(DEMON);

/* ======== 档 4 每边三人（2026-09-28，规格 shots/review/trio/trio_spec.md）========
   女生侧：真相女神 + 月亮查岗使 + 黑蛛女特工；男生侧：灭迹恶魔 + 内裤外穿侠 + 二郎·打码神。
   每个人的武器都不一样（雾 / 爱心光流 / 蛛网 / 射线 / 天眼 + 马赛克），不能走 skins 换皮（skins 要同一个裁边框、同一套 foot / muzzle），
   所以每人一份 Crew 配置，照 TRUTH / DEMON 的写法（悬停、whole 整个人小幅前后倾、二分反解瞄准），每边一个 CrewGroup（main.js）。
   立绘 v14/<名>/make.py（共用 v14/crewart.py），量点都是它打印的贴图像素。
   配色按明亮底图的规矩（chashouji-fx）：发光靠色相、实体靠暖黑描边 WARM_INK。 */
const WARM_INK = [58, 44, 38];
const rgbaOf = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a.toFixed(3)})`;
function heartAt(ctx, x, y, r, rot) {             // 爱心路径（同 fx.js heartPath，顶点偏下：视觉重心在下半）
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  ctx.beginPath(); ctx.moveTo(0, r * 0.92);
  ctx.bezierCurveTo(-r * 1.08, r * 0.10, -r * 0.62, -r * 1.02, 0, -r * 0.34);
  ctx.bezierCurveTo(r * 0.62, -r * 1.02, r * 1.08, r * 0.10, 0, r * 0.92);
  ctx.closePath(); ctx.restore();
}

/* ---- ② 月亮查岗使（水冰月底子）：短杖顶上的放大镜喷出一股粉色爱心 + 小月牙的光流，形状跟女神的雾锥一样，只换粒子 ----
   爱心本体饱和粉、暖黑描边 3px（不描边在浅绿墙上看不见）；月牙暖金。底下垫一层很淡的粉雾把一颗颗连成一股。 */
const MOON_FX = {
  heart: [255, 90, 160], crescent: [255, 200, 60], mist: [255, 150, 205], ink: WARM_INK,
  r: [9, 22],                // 爱心出口半径 → 飞完的半径
  cr: [8, 16],               // 月牙
  mistR: [14, 48], mistA: 0.1,
  kinds: [0.5, 0.72],        // j < 0.5 爱心、< 0.72 月牙、其余只是雾（让一股里有疏有密，不是一串等距的心）
  ring: [255, 110, 180], ringHi: [255, 225, 240],   // 脚下缎带光环（外圈 / 内圈）
  flare: [26, 42],           // 放大镜口的闪光星半径 [小, 大]，随喷射节奏跳
};
function drawHeartFlow(ctx, ps, b) {
  const F = MOON_FX, L = MOON.fluid.life;
  for (const d of ps) {                          // 托底粉雾
    const u = Math.min(1, d.t / L), r = F.mistR[0] + (F.mistR[1] - F.mistR[0]) * Math.sqrt(u);
    ctx.fillStyle = rgbaOf(F.mist, (1 - u * u) * F.mistA); ctx.beginPath(); ctx.arc(d.x, d.y, r, 0, 6.283); ctx.fill();
  }
  ctx.lineJoin = 'round';
  for (const d of ps) {
    if (d.j >= F.kinds[1]) continue;
    const u = Math.min(1, d.t / L), a = u > 0.7 ? (1 - u) / 0.3 : 1;
    ctx.globalAlpha = a;
    if (d.j < F.kinds[0]) {
      heartAt(ctx, d.x, d.y, F.r[0] + (F.r[1] - F.r[0]) * Math.sqrt(u), Math.sin(d.t * 6 + d.j * 50) * 0.35);
      ctx.fillStyle = rgbaOf(F.heart, 1); ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = rgbaOf(F.ink, 1); ctx.stroke();
    } else {
      const r = F.cr[0] + (F.cr[1] - F.cr[0]) * Math.sqrt(u);
      ctx.save(); ctx.translate(d.x, d.y); ctx.rotate(d.t * 5 + d.j * 40);
      ctx.beginPath(); ctx.arc(0, 0, r, 0.35, 6.283 - 0.35); ctx.arc(r * 0.45, -r * 0.1, r * 0.78, 6.283 - 0.62, 0.62, true); ctx.closePath();
      ctx.fillStyle = rgbaOf(F.crescent, 1); ctx.fill(); ctx.lineWidth = 2.5; ctx.strokeStyle = rgbaOf(F.ink, 1); ctx.stroke();
      ctx.restore();
    }
  }
  ctx.globalAlpha = 1;
  if (b && b.m) {                                 // 放大镜口一颗八角闪光星，大小随后坐跳
    const r = F.flare[0] + (F.flare[1] - F.flare[0]) * b.kick, [mx, my] = b.m;
    ctx.save(); ctx.translate(mx, my); ctx.rotate(b.t * 3); ctx.beginPath();
    for (let i = 0; i < 16; i++) { const a = i * 0.3927, rr = i % 2 ? r * 0.38 : r; i ? ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : ctx.moveTo(rr, 0); }
    ctx.closePath(); ctx.fillStyle = rgbaOf(F.ringHi, 0.95); ctx.fill(); ctx.lineWidth = 3.5; ctx.strokeStyle = rgbaOf(F.heart, 1); ctx.stroke();
    ctx.restore();
  }
}
/* 脚下一圈粉色缎带光环（转着圈落下来的时候就有，悬着时一直在），画在她身后、跟着她倾 */
function drawMoonAura(ctx, b, s, at) {
  const F = MOON_FX, [fx, fy] = at(MOON.spr.foot), k = Math.min(1, b.t / 0.3);
  const rx = 120 * s, ry = 26 * s, y = fy - 40 * s;
  ctx.save(); ctx.globalAlpha = 0.9 * k; ctx.lineCap = 'round';
  for (const [w, c] of [[14 * s, F.ring], [5 * s, F.ringHi]]) {
    ctx.lineWidth = w; ctx.strokeStyle = rgbaOf(c, 1);
    ctx.beginPath(); ctx.ellipse(fx, y, rx, ry, 0, b.t * 2.2, b.t * 2.2 + 5.2); ctx.stroke();   // 缺一口的环在转：读成缎带不是呼啦圈
  }
  ctx.restore();
}
const MOON = {
  ...TRUTH,
  whole: { pivot: [195, 256] },
  exhaust: null,                                // 她不靠后坐力悬着（魔法少女本来就会飞），没有尾焰
  spr: { src: 'assets/world/moon%n_%k.webp', body: { src: 'up', pivot: [195, 256], k: 1 },
         foot: [180, 612], muzzle: [365, 355], rest: -0.685, head: [209, 50], chest: [224, 191] },
  skins: [1],
  aura: (ctx, b, s, at) => drawMoonAura(ctx, b, s, at),
  /* 出场：从左上画外转一圈半落下来（spin），刹停时 main.js 出一个爱心冲击环（RECIPE.moon.arrive） */
  path: { from: (s, hx, hy) => [hx - 420, hy - 700 * s], spin: -1.5 },
  anim: { pulse: [0.55, 0.18], kick: [0, 0.06, 9], lean: 0.03, bob: [6, 2.4] },
  T: { enter: 0.6, spray: 2.8, exit: 0.45, fire: 0.18 },
  /* 爱心每颗都要描边画，比女神的雾团贵：rate 110（女神 220），靠每颗更大、更实来撑体量 */
  fluid: { V: 620, G: 40, drag: 0.85, rate: 110, spread: 0.26, vJit: 0.18, life: 1.1, miss: 150, snap: 14, hitEvery: 0.25, floor: false,
           draw: drawHeartFlow },
};
const Moon = Crew(MOON);

/* ---- ③ 黑蛛女特工（黑寡妇底子）：吊着一根丝从天花板降下来，腕部钩索装置朝右下射一张蛛网 ----
   不是雾：一发一发的网弹（anim.pulse 每按一下出一发），飞的时候拖一根丝连回腕口；打中了在男生脸上张开一张网
   （fx.js kind 'web'，贴在脸上停一会儿），网上挂红色定位图钉。白丝在浅色底图上会消失：丝一律暗红描边 + 白芯。 */
const WIDOW_FX = { edge: [120, 20, 30], core: [255, 255, 255], ball: 15 };
function drawWebShots(ctx, ps, b) {
  const F = WIDOW_FX;
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (const d of ps) {
    if (d.ex) continue;
    if (b) {                                      // 丝：腕口 → 这发网弹（腕口按此刻姿态算，人离场了就不画丝）
      const m = b.wrist;
      if (m) for (const [w, c] of [[5, F.edge], [2, F.core]]) {
        ctx.lineWidth = w; ctx.strokeStyle = rgbaOf(c, 1);
        ctx.beginPath(); ctx.moveTo(m[0], m[1]); ctx.lineTo(d.x, d.y); ctx.stroke();
      }
    }
    const r = F.ball * (0.7 + Math.min(1, d.t / 0.15) * 0.3);   // 飞行中的网弹：一团收拢的小网
    ctx.save(); ctx.translate(d.x, d.y); ctx.rotate(d.t * 9);
    ctx.beginPath();
    for (let i = 0; i < 6; i++) { const a = i * 1.047; ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
    for (let i = 0; i <= 6; i++) { const a = i * 1.047, rr = r * 0.6; i ? ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr) : ctx.moveTo(rr, 0); }
    ctx.lineWidth = 6; ctx.strokeStyle = rgbaOf(F.edge, 1); ctx.stroke();
    ctx.lineWidth = 2.5; ctx.strokeStyle = rgbaOf(F.core, 1); ctx.stroke();
    ctx.restore();
  }
}
/* 吊着她的那根丝：从抓丝的手连到画面顶（一直往上出画），跟女神的尾焰是同一个作用 —— "为什么她能悬着" */
function drawWidowRope(ctx, b, s, carry, layer) {
  if (layer !== 'back') return;
  const F = WIDOW_FX, [hx, hy] = carry(WIDOW.spr.hand);
  b.wrist = carry(WIDOW.spr.muzzle);             // 网弹的丝从腕口出（drawWebShots 读）
  ctx.save(); ctx.lineCap = 'round';
  for (const [w, c] of [[6, F.edge], [2.5, F.core]]) {
    ctx.lineWidth = w; ctx.strokeStyle = rgbaOf(c, 1);
    ctx.beginPath(); ctx.moveTo(hx, hy); ctx.lineTo(hx, -40); ctx.stroke();   // 摆动绕的就是这只手，丝始终竖直
  }
  ctx.restore();
}
const WIDOW = {
  ...TRUTH,
  whole: { pivot: [103, 288] },
  exhaust: null,
  spr: { src: 'assets/world/widow%n_%k.webp', body: { src: 'up', pivot: [103, 288], k: 1 },
         foot: [99, 608], muzzle: [241, 269], rest: -0.471, hand: [80, 55], head: [107, 119], chest: [111, 213] },
  skins: [1],
  aura: null,
  extra: (ctx, b, s, carry, layer) => drawWidowRope(ctx, b, s, carry, layer),
  /* 出场：从正上方画外顺着丝降下来（身体始终竖直、不倒挂）；离场收丝往上拉走。悬着时绕抓丝的手轻轻摆 */
  path: { pivot: [80, 55], swing: [0.035, 1.7] },
  anim: { pulse: [0.12, 0.42], kick: [0, 0.07, 10], lean: 0.02, bob: [3, 1.6] },
  T: { enter: 0.7, spray: 2.8, exit: 0.5, fire: 0.18 },
  /* 网弹：每按一下出 1 发（pulse 0.12 秒 × rate 10 ≈ 1.2）；打中了 main.js 在脸上张网。
     **抛出去的，不是直射**：V 1000、G 2200，沿腕口 27° 往右下出手、半秒落到男生脸上。直射（G 120）的话要从她的腕口打到下方的脸
     得往下 ~50°，整个人要前倾 0.4~0.7 rad（第一版实测吊在丝上斜成 40°）；抛物线把这段落差交给重力，人只需小幅倾。 */
  fluid: { V: 1000, G: 2200, drag: 0, rate: 10, spread: 0.02, vJit: 0, life: 0.9, miss: 90, snap: 10, hitEvery: 0.25, floor: false,
           draw: drawWebShots },
};
const Widow = Crew(WIDOW);

/* ---- ⑤ 内裤外穿侠（超人底子）：两只眼睛射出两道红橙色射线，直线、硬，跟恶魔的软雾一粗一细好分辨 ----
   射线由运行时从贴图的两个眼睛点（spr.eyes）画：每道都是一串 G 0 的高速粒子连成的折线（粒子负责命中判定），
   芯 EMBER、外层红橙、描边暗红 —— 这张底图上最显眼的色相。 */
const BEAM_BRIEFS = { w: 9, edge: [110, 20, 10], outer: [255, 60, 30], core: [255, 156, 38], hot: [255, 236, 190] };
const BEAM_ERLANG = { w: 15, edge: [120, 80, 10], outer: [255, 200, 60], core: [255, 236, 150], hot: [255, 252, 230] };
/* 一个人的射线：粒子按出口顺序连成一串（seq 断开的地方 = 松开那一下，射线断开），每只眼睛各画一道（眼睛相对喷口平移） */
function drawBeams(B, ctx, ps, b) {
  if (!b || !b.eyes || !b.m) return;              // 只在按住射的那几帧有；松开时整道消失（射线不是飘出去的东西）
  const run = [];
  for (let i = ps.length - 1; i >= 0; i--) {     // 从最新一颗往回，接到 seq 断开为止
    if (run.length && ps[i].seq !== run[run.length - 1].seq - 1) break;
    run.push(ps[i]);
  }
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (const e of b.eyes) {
    const ox = e[0] - b.m[0], oy = e[1] - b.m[1];
    const line = () => { ctx.beginPath(); ctx.moveTo(e[0], e[1]); for (const d of run) ctx.lineTo(d.x + ox, d.y + oy); };
    for (const [w, c, a] of [[B.w + 8, B.edge, 0.9], [B.w + 3, B.outer, 1], [B.w * 0.45, B.core, 1]]) {
      line(); ctx.lineWidth = w; ctx.strokeStyle = rgbaOf(c, a); ctx.stroke();
    }
    ctx.fillStyle = rgbaOf(B.hot, 1); ctx.strokeStyle = rgbaOf(B.outer, 1); ctx.lineWidth = 3;   // 眼睛上一个小亮点
    ctx.beginPath(); ctx.arc(e[0], e[1], B.w * 0.7, 0, 6.283); ctx.fill(); ctx.stroke();
  }
}
/* 横着飞进来时身后拖的速度线：画在他身后、跟着他转（进场他是横着的，身体坐标里"脚那头"就是身后） */
function drawBriefsAura(ctx, b, s, at) {
  const u = b.t / BRIEFS.T.enter;
  if (u >= 1) return;
  const [fx, fy] = at(BRIEFS.spr.foot), [cx] = at(BRIEFS.spr.chest), a = 1 - u;
  ctx.save(); ctx.lineCap = 'round';
  for (let i = 0; i < 6; i++) {
    const x = cx + (i - 2.5) * 55 * s, y0 = fy - 260 * s + (i % 2) * 60 * s, len = (220 + (i * 37) % 90) * s;
    for (const [w, c] of [[9, WARM_INK], [4, [255, 255, 255]]]) {
      ctx.lineWidth = w * s; ctx.strokeStyle = rgbaOf(c, 0.85 * a);
      ctx.beginPath(); ctx.moveTo(x, y0); ctx.lineTo(x, y0 + len); ctx.stroke();
    }
  }
  ctx.restore();
}
const BRIEFS = {
  ...DEMON,
  whole: { pivot: [225, 272] },
  exhaust: null,
  spr: { src: 'assets/world/briefs%n_%k.webp', body: { src: 'up', pivot: [225, 272], k: 1 },
         foot: [256, 603], muzzle: [190, 88], eyes: [[180, 89], [199, 86]], head: [202, 48], chest: [239, 189],
         /* 射线出眼睛，眼睛不是一根有朝向的枪管：rest 直接取"从头顶的站位看女生脸"的典型俯角（~55°），
            人只为了跟着脸上下扫而小幅倾（aim ±0.3）。第一版 rest −0.5（眼神的画法）要整个人前倾 0.6 rad 才够得着，斜成 40°。 */
         rest: -0.95 },
  aim: { lo: -0.35, hi: 0.3, rate: 1.6, follow: 8, stiff: 40 },
  skins: [1],
  aura: (ctx, b, s, at) => drawBriefsAura(ctx, b, s, at),
  /* 出场：从右边画外横着飞进来（一拳朝前 = 头朝左，roll0 −1.45 rad），刹停后竖起来；离场时一拳朝上冲出画面（转 +1.3 往上飞） */
  path: { from: (s, hx, hy) => [hx + 760, hy - 180 * s], roll0: -1.45, to: (s, x, y) => [x - 80, y - 1200 * s], rollOut: 1.3 },
  anim: { pulse: [0.55, 0.2], kick: [0, 0.03, 9], lean: 0.02, bob: [5, 2.0] },
  T: { enter: 0.55, spray: 2.8, exit: 0.45, fire: 0.18 },
  /* 射线：极快（V 2600）、无重力、无散角 → 一条直线；miss 60（射线细，判定比雾窄） */
  fluid: { V: 2600, G: 0, drag: 0, rate: 70, spread: 0, vJit: 0, life: 0.5, miss: 60, snap: 12, hitEvery: 0.25, floor: false,
           draw: (ctx, ps, b) => drawBeams(BEAM_BRIEFS, ctx, ps, b) },
};
const Briefs = Crew(BRIEFS);

/* ---- ⑥ 二郎·打码神（杨戬底子）：天眼一开射出一道金色竖光，打中的地方铺一块马赛克（main.js RECIPE.erlang）----
   天眼：立绘里那只竖眼很小，运行时在 eye 点上画一只随喷射睁开的金色竖眼（spraying 时 b.lean 从 0 长到 1）。
   哮天犬（cfg.xtra.dog）：圆滚滚的柴犬在祥云边上绕圈，二郎打中时 main.js 让一个聊天气泡飞向它嘴里（dogEat），到嘴时它扑起来一口吃掉。 */
function drawErlangAura(ctx, b, s, at) {
  const [ex, ey] = at(ERLANG.spr.eye), o = Math.max(0.15, b.lean);   // 睁开程度
  ctx.save();
  ctx.fillStyle = rgbaOf([255, 200, 60], 0.35 * o); ctx.beginPath(); ctx.arc(ex, ey, 26 * s, 0, 6.283); ctx.fill();
  ctx.beginPath(); ctx.ellipse(ex, ey, 5 * s, 13 * s * o, 0, 0, 6.283);
  ctx.fillStyle = rgbaOf([255, 236, 150], 1); ctx.fill(); ctx.lineWidth = 2.5 * s; ctx.strokeStyle = rgbaOf([120, 80, 10], 1); ctx.stroke();
  ctx.fillStyle = rgbaOf([90, 40, 10], 1); ctx.beginPath(); ctx.ellipse(ex, ey, 2 * s, 5 * s * o, 0, 0, 6.283); ctx.fill();
  ctx.restore();
}
const DOG = { R: 120, H: 16, w: 1.6, lift: 34, k: 0.9, eatT: 0.35, hop: 60 };   // 绕云半径、上下半轴、角速度、脚离云底多高、缩放（×s）、扑咬多久、扑多高
/* 狗此刻在哪、朝哪：绕着祥云转圈（椭圆轨道，远半圈画在他身后），b.dogEat 到点时往上扑一下 */
function dogPose(b, s, carry) {
  const [fx, fy] = carry(ERLANG.spr.foot), a = b.t * DOG.w + b.ph;
  const x = fx + Math.cos(a) * DOG.R * s, back = Math.sin(a) < 0;
  let y = fy - DOG.lift * s + Math.sin(a) * DOG.H * s;
  const eu = b.dogEat != null ? (b.t - b.dogEat) / DOG.eatT : -1;
  if (eu >= 0 && eu <= 1) y -= Math.sin(Math.PI * eu) * DOG.hop * s;
  return { x, y, back, left: -Math.sin(a) < 0, eu };
}
function drawDog(ctx, b, s, carry, layer, xi) {
  const im = xi.dog;
  if (!im) return;
  const d = dogPose(b, s, carry);
  const k = DOG.k * s * (d.eu >= 0 && d.eu <= 1 ? 1 + 0.12 * Math.sin(Math.PI * d.eu) : 1), w = im.width * k, h = im.height * k;
  const [mx, my] = ERLANG.dog.foot;              // 贴图里狗脚底（make.py 打印），对到轨道点
  const [qx, qy] = ERLANG.dog.mouth;
  if (layer === 'back') b.dogMouth = [d.x + (qx - mx) * k * (d.left ? 1 : -1), d.y + (qy - my) * k];   // main.js 让气泡飞向这里
  if ((layer === 'back') !== d.back) return;
  ctx.save(); ctx.translate(d.x, d.y);
  if (!d.left) ctx.scale(-1, 1);                // 贴图朝左；往右跑时翻过来
  ctx.drawImage(im, -mx * k, -my * k, w, h);
  ctx.restore();
}
const ERLANG = {
  ...DEMON,
  whole: { pivot: [179, 257] },
  exhaust: null,
  spr: { src: 'assets/world/erlang%n_%k.webp', body: { src: 'up', pivot: [179, 257], k: 1 },
         foot: [194, 609], muzzle: [156, 111], eye: [156, 111], eyes: [[156, 111]], head: [171, 55], chest: [175, 196],
         rest: -0.95 },                         // 天眼同内裤外穿侠：rest 取典型俯角，人只小幅倾
  aim: { lo: -0.35, hi: 0.3, rate: 1.6, follow: 8, stiff: 40 },
  dog: { mouth: [55, 104], foot: [120, 184] },  // 哮天犬贴图量点（v14/erlang/make.py 打印）
  xtra: { dog: 'assets/world/dog1_up.webp' },
  skins: [1],
  aura: (ctx, b, s, at) => drawErlangAura(ctx, b, s, at),
  extra: (ctx, b, s, carry, layer, xi) => drawDog(ctx, b, s, carry, layer, xi),
  /* 出场：脚踩祥云从右上画外斜着降下来；云留在脚下当悬停的理由 */
  path: { from: (s, hx, hy) => [hx + 420, hy - 760 * s] },
  anim: { pulse: [0.6, 0.25], kick: [0, 0.03, 9], lean: 0.02, bob: [4, 1.8] },
  T: { enter: 0.65, spray: 2.8, exit: 0.45, fire: 0.18 },
  fluid: { V: 2200, G: 0, drag: 0, rate: 60, spread: 0, vJit: 0, life: 0.55, miss: 80, snap: 12, hitEvery: 0.3, floor: false,
           draw: (ctx, ps, b) => drawBeams(BEAM_ERLANG, ctx, ps, b) },
};
const Erlang = Crew(ERLANG);
