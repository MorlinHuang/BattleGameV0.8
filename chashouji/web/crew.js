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
 * 形象 skins：哥们八个、闺蜜七个（同一姿势改图换人，make.py 用同一个裁边框出图，所以 foot / muzzle / 转轴全都一样，
 * 只换贴图）。贴图路径 spr.src 里 %n 换成形象编号、%k 换成层名。召唤时挑场上没人用的那个。
 *
 * **由落点反推枪口**：每帧看该打对方身上哪一点（o.target(u)），按喷出物的出口速度 V 和重力 G 反解要的
 * 仰角，转轴按转速上限 aim.rate 转过去、夹在 aim.lo~hi；喷出物**永远沿喷口此刻的方向、以 V 射出**。
 * 落在哪只由转角决定：转平滑，水柱/雾就平滑变形。（试过每滴反解初速去凑落点：前后两滴速度差大，水柱成锯齿。）
 * 仰角跟喷口位置互相依赖（一转喷口就挪），迭代到收敛；瞄点平滑跟随（步态是硬切帧，直接瞄会抖）。
 *
 * **比例按透视**：rows 是远近 d（1 = 跟主角一样远），画多大 = d × cfg.k（k 把立绘换到主角比例，见 pose），
 * 站得越远越小、脚底越靠近视平线：抬高 = (地面 − 视平线) × (1 − d)；d > 1 站在主角前面，画在主角之上。视平线是镜头的，两边共用 o.horizon。
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
  const WK = cfg.whole && cfg.whole.k != null ? cfg.whole.k : 1;
  const BM = cfg.beam || null;                    // 光束（嫦娥）：不喷东西，头顶几个光点轮流蓄力、轰一束直光（beamStep）
  const BW = cfg.bow || null;                     // 弓（后羿）：每 BW.cycle 秒放一箭（一颗粒子），弦、搭着的箭、拉弦的手臂跟着 b.bw 动（BW.pose）   // whole：整个人跟瞄准角转几成（白娘子 0.12：身子只轻轻倾，水流照样按完整角度出）
  let img = null, o = {};                       // img[形象]：{ arm, body, lo }（arm 可无）
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
    return Promise.all(cfg.skins.map(n => Promise.all(ks.map(k => one(src(k, n)))))).then((sets) => {
      if (sets.every(ims => ims.every(Boolean))) img = sets.map(ims => { const s = {}; ks.forEach((k, i) => { s[k] = ims[i]; }); return s; });
      return !!img;
    });
  }

  const sprayEnd = (b) => T.enter + b.spray;

  /* 横向位置：在 lo~hi 里抽 12 次，取离已有的人最远的那个（够 gap 就直接用） */
  function pickR(lo = 0, hi = 1) {
    const rnd = () => lo + Math.random() * (hi - lo);
    let best = rnd(), bestD = -1;
    for (let k = 0; k < 12; k++) {
      const r = rnd(), d = Math.min(1, ...bs.map(b => Math.abs(b.r - r)));
      if (d >= cfg.gap) return r;
      if (d > bestD) { best = r; bestD = d; }
    }
    return best;
  }

  /* 续上的这一份也是一次完整送礼：下一发按礼物力度打（first），并记下第几份、在她的第几秒续上（名字条据此重播「×N」） */
  function renew(b) { b.first = true; b.renew = (b.renew || 0) + 1; b.renewT = b.t; }

  /* 候场（b.hold，intro.js）：出场视频放着的时候她已经占了名额（再送走续时间、组里不轮到下一个），但不走时钟、不画、不喷。
     视频放完 intro.js 清掉 hold、把 t 归零、给 b.from = 视频尾帧里她的 [脚底 x, 脚底 y, 缩放]，hoverPose 从那里滑进悬停位。
     sk（可无）：指定形象编号（cfg.skins 的下标，越界夹到两头）；不给就挑场上没人用的。诊断参数 ?skin= 用它。 */
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
    /* 远近：每人占一排（rows 里挑没人的），远排小、脚底高 —— 喷口上下错开，几股不会从同一点分叉。
       一排 = [缩放下限, 上限, 横向 r 下限, 上限]（后两项可无 = 0~1）。缩放 > 1 的排在主角前面（离镜头近），main.js 画在主角之上 */
    const free = cfg.rows.filter(R => !bs.some(b => b.s >= R[0] && b.s <= R[1]));
    const pool = free.length ? free : cfg.rows, R = pool[Math.floor(Math.random() * pool.length)];
    /* 形象：挑一个场上没人用的（max 不超过形象数，同时在场的一定各不相同） */
    if (sk == null) {
      const skins = cfg.skins.map((_, i) => i), unused = freeSkins();
      sk = (unused.length ? unused : skins)[Math.floor(Math.random() * (unused.length || skins.length))];
    }
    const b = { t: 0, spray: T.spray, emit: 0, hitCd: 0, first: true, ph: Math.random() * 6, aim: 0,
                r: pickR(R[2], R[3]), s: R[0] + Math.random() * (R[1] - R[0]), seq: 0, tg: null, m: null, zone: null, zoneT: 0,
                pt: 0, kick: 0, lean: 0, skin: sk, landed: false, ex: 0, exP: null, av: 0, back: 0, backV: 0, backT: 0,
                hold: false, from: null };
    if (PATH.pop && o.origin) { b.pop = o.origin(); if (o.onPop) o.onPop(b.pop[0], b.pop[1]); }   // 从手机里蹦出来（绿茶妹妹）
    bs.push(b);
    bs.sort((a, b) => a.s - b.s);          // 远的先画
    return b;                              // 新来的人（续时间 / 叫回的返回 undefined）：main.js 据此决定要不要先放出场视频
  }

  /* 场上没人用的形象（下标） */
  function freeSkins() { return cfg.skins.map((_, i) => i).filter(i => !bs.some(b => b.skin === i)); }

  const easeOut = (u) => 1 - Math.pow(1 - u, 3);

  /* 悬停（档 4 六个人）：不站地，悬在半空。o.perch(b) 给脚底该停在屏幕哪一点、缩放多大 [x, y, s]
     （main.js G4STAND：每边同时一人，六个人各有一个大站位，缩放按身高统一，不用召唤时抽的 b.s）。
     来：从 PATH.from(s, hx, hy) 给的画外那一点冲过来，按 easeOut 减速刹停（不给就从正上方画外冲下来 —— 女神 / 恶魔）；
     走：朝 PATH.to(s, x, y) 加速离开（u²，不给就原地往上冲出画面）。悬着的时候慢慢晃一个横 8 字 + 上下浮（anim.bob）。
     进出场时整个人另外转多少（roll：白娘子、法海前倾着飞下来）见 rollOf。 */
  function hoverPose(b) {
    const [hx, hy, s] = o.perch(b), t = b.t, se = sprayEnd(b);
    const top = -(spr.foot[1] - spr.muzzle[1] + 120) * s;             // 脚底在这，整个人（含翘起的罐子）都在画外
    const sx = Math.sin(t * 0.9 + b.ph) * 8 * s, sy = Math.sin(t * 1.8 + b.ph) * 4 * s;
    const bob = A ? Math.sin(t * A.bob[1] + b.ph) * A.bob[0] * s : 0;
    if (t < T.enter) {
      const e = easeOut(t / T.enter);
      if (b.from) { const [fx, fy, fs] = b.from; return [fx + (hx - fx) * e, fy + (hy - fy) * e, fs + (s - fs) * e]; }   // 从出场视频里走出来
      /* 从手机里蹦出来（PATH.pop）：脚底从手机那一点起跳，走一道往上拱的弧线落到悬停点，人从 pop.s0 倍长到原大。
         横向、纵向按 easeOut 走，弧线另外加 h·sin(πu)（u 是线性时间，最高点在正中）；缩放比位移先长满（0.6 的时间） */
      if (b.pop && PATH.pop) {
        const P = PATH.pop, u = t / T.enter, [fx, fy] = b.pop, g = easeOut(Math.min(1, u / 0.6));
        return [fx + (hx - fx) * e, fy + (hy - fy) * e - P.h * s * Math.sin(Math.PI * u), s * (P.s0 + (1 - P.s0) * g)];
      }
      const [fx, fy] = PATH.from ? PATH.from(s, hx, hy) : [hx, top];
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
     来的时候从 roll0 + spin 圈转回 0（easeOut，跟位移同步刹住）；走的时候从 0 转到 rollOut（u²）。只管画，喷口 / 瞄准不吃它 ——
     转的时候都还没开火。 */
  function rollOf(b) {
    const t = b.t, se = sprayEnd(b);
    if (t < T.enter) return ((PATH.roll0 || 0) + (PATH.spin || 0) * 6.2832) * (1 - easeOut(t / T.enter));
    if (t > se) return (PATH.rollOut || 0) * Math.min(1, (t - se) / T.exit) ** 2;
    return 0;
  }

  /* 此刻人站在哪（脚下滑板/平衡车底边中点的屏幕坐标）和缩放。
     横向按**喷口**排：o.zone() = [喷口最多伸到哪（靠对方那边）, 人的外沿最多到哪（可以出画一点）]，
     r=0 喷口顶到第一个数，r=1 外沿顶到第二个数。
     远近 d = b.s（1 = 跟主角一样远）定脚踩多低；画多大 = d × cfg.k。k 是立绘换到主角比例的系数：帮手是成人体型、站得直、
     脚下还有滑板 / 平衡车，同样按"头一样大"出图，d = 1 时整个人比男女主大一圈 —— 放到主角前面（d > 1）就大很多
     （2026-09-29 用户："前面的看着太大了，比男女主大很多，不合理"）。返回的第三项是画多大。 */
  function pose(b) {
    if (cfg.move === 'hover') return hoverPose(b);
    const d = b.s, s = d * (cfg.k || 1), [near, edge] = o.zone(), wid = img ? img[0].lo.width : 400;
    let far = face < 0 ? edge - (wid - spr.muzzle[0]) * s : edge + spr.muzzle[0] * s;
    far = face < 0 ? Math.max(near, far) : Math.min(near, far);
    const x1 = near + (far - near) * b.r + (spr.foot[0] - spr.muzzle[0]) * s;
    const y = o.ground() - (o.ground() - o.horizon()) * (1 - d);
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
    return turn(m1, at(p, cfg.whole.pivot), th * WK);
  }
  function muzzle(p, th, b) {
    if (cfg.whole) return carried(p, spr.muzzle, th, b);
    const [bt, at_] = angles(b, th), c = at(p, spr.body.pivot), m = at(p, spr.muzzle);
    if (!spr.arm) return turn(m, c, bt);
    const sh = at(p, spr.arm.pivot), sh1 = turn(sh, c, bt);
    const m1 = turn(m, sh, at_);                   // 手臂绕肩转到 at_（绝对角），再跟着肩膀平移
    return [m1[0] + sh1[0] - sh[0], m1[1] + sh1[1] - sh[1]];
  }

  /* 出口速度 V、重力 G，打中 (dx, dy)（屏幕坐标）要的仰角（低弹道）。够不着就按 45°。
     F.arc 的不瞄（走 arcStep 的弧线，出口方向无所谓）：要的仰角就是喷口本来的指向，转角停在 0，人站得直直的。 */
  function elevation(dx, dy) {
    if (F.arc) return REST;
    const D = Math.abs(dx), h = -dy, v2 = F.V * F.V, g = F.G;
    if (g === 0) return Math.atan2(h, D);
    const disc = v2 * v2 - g * (g * D * D + 2 * h * v2);
    return disc >= 0 ? Math.atan((v2 - Math.sqrt(disc)) / (g * D)) : Math.PI / 4;
  }
  /* F.arc（绿茶妹妹的气泡）：不走重力，沿一条二次贝塞尔从手机飞到落点 —— 控制点在落点外侧 out、手机上方 up，
     弧往她面朝的那边上方鼓出去，最后从外上方砸下来；进度 e = (t / T)^ease 越飞越快（砸）。
     落点每帧取现在的（女生被拖着走也追得上）。为什么不用抛物线：她在女生右上方，横着差 ~280、竖着差 ~640，
     重力弹道不论多大仰角都是"往上一钩、再竖直掉下去"（叠帧实测一根竖柱）—— 用户要的是"有个弧度砸在女生身上，而不是直接掉下来"。 */
  function arcStep(d, dt) {
    const A = F.arc, tg = o.target(d.u);
    if (tg) d.p2 = tg;
    d.t += dt;
    const s = Math.min(1, d.t / A.T), e = Math.pow(s, A.ease), k = 0.7 + 0.6 * d.j;
    const p0 = d.p0, p2 = d.p2, p1 = [p2[0] + face * A.out * k, p0[1] - A.up * k];
    const q = 1 - e;
    d.x = q * q * p0[0] + 2 * q * e * p1[0] + e * e * p2[0];
    d.y = q * q * p0[1] + 2 * q * e * p1[1] + e * e * p2[1];
    const de = A.ease * Math.pow(Math.max(s, 1e-3), A.ease - 1) / A.T;          // 速度只给画气泡尾巴的朝向用
    d.vx = 2 * (q * (p1[0] - p0[0]) + e * (p2[0] - p1[0])) * de;
    d.vy = 2 * (q * (p1[1] - p0[1]) + e * (p2[1] - p1[1])) * de;
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
    /* F.radius（白娘子）：离落点这么近就算中。她从左上方往下泼，水快竖着落到脸上 —— 按"越过落点那一列"判的话，
       竖着落的水在那一列左边一点就一路掉下去了，永远越不过去（第一版整股水穿过男生砸到地板上） */
    /* 有 radius 的只按半径判：她 / 法海改打全身之后（落点可以在腿上、背上），"越过落点那一列、上下 miss 以内"那条规则在
       落点上方一百多像素就判中了（从左上往下泼，水先越过那一列、再往下落）—— 水柱画到判中那颗水滴为止，停在半空。 */
    if (tg && F.radius) return Math.hypot(d.x - tg[0], d.y - tg[1]) < F.radius ? [d.x, d.y] : null;
    if (tg && past(tg[0]) && Math.abs(d.y - tg[1]) < F.miss)
      return [tg[0], F.snap == null ? d.y : tg[1] + Math.max(-F.snap, Math.min(F.snap, d.y - tg[1]))];
    const fr = o.front(d.y);
    return fr != null && past(fr) ? [fr, d.y] : null;
  }

  /* 光束（cfg.beam，嫦娥 2026-09-29）：用户要"连续召唤月光束来轰击男生，有点像超人的红眼光束，召唤的位置是头顶出现 3 个光点，
     分别召唤月光束"，节奏选的"轮番蓄力点射"：一个光点先聚光 T.charge 秒（变亮、四周的光往里吸），轰出一条粗光束 T.fire 秒，
     隔 T.gap 换下一个，蓄—轰—蓄—轰。光点在贴图上的位置 orbs（跟着人一起倾、一起浮），进场时依次亮起（appear）。
     每一发：出手那一刻定下打他身上哪一点（u，跟着他身子动，不跟着瞄准扫），开轰那一下 onHit（第一发按礼物力度），
     轰着的时候每 drip 秒 onSplash 一次（碎光、小月牙）。状态记在 b.beam：k 第几个光点、ph 'charge' | 'fire' | 'gap'、pt 这一段过了几秒。
     b.beam.fx：画要的东西（光点位置由 items 画的时候现算，这里只管时间和打哪）。 */
  function beamStep(b, dt, on, u) {
    const S = b.beam || (b.beam = { k: 0, ph: 'charge', pt: 0, u: 0.5, dr: 0, motes: [] });
    for (let i = S.motes.length - 1; i >= 0; i--) if ((S.motes[i].t += dt) > S.motes[i].life) S.motes.splice(i, 1);
    if (!on) { S.ph = 'charge'; S.pt = 0; return; }
    S.pt += dt;
    const T_ = BM.T;
    if (S.ph === 'charge') {
      if (Math.random() < dt * BM.mote.rate) S.motes.push({ k: S.k, a: Math.random() * 6.283, t: 0, life: BM.mote.life });
      if (S.pt >= T_.charge) {
        S.ph = 'fire'; S.pt = 0; S.u = u; S.dr = 0;
        const h = o.target(S.u);
        if (h) { o.onHit(h[0], h[1], b.first, b); b.first = false; }
        if (A) b.kick = 1;
      }
    } else if (S.ph === 'fire') {
      if ((S.dr += dt) >= BM.drip) { S.dr -= BM.drip; const h = o.target(S.u); if (h) o.onSplash(h[0], h[1]); }
      if (S.pt >= T_.fire) { S.ph = 'gap'; S.pt = 0; }
    } else if (S.pt >= T_.gap) { S.ph = 'charge'; S.pt = 0; S.k = (S.k + 1) % BM.orbs.length; }
  }
  /* 此刻几个光点在屏幕哪（跟着人倾、浮），和光束该打到哪 */
  function beamGeo(b) {
    const p = pose(b);
    return { orbs: BM.orbs.map(q => carried(p, q, b.aim, b)), end: b.beam && b.beam.ph === 'fire' ? o.target(b.beam.u) : null, s: p[2] };
  }

  function update(dt) {
    for (let i = ps.length - 1; i >= 0; i--) {
      const d = ps[i];
      if (d.stuck != null) { if ((d.stuck += dt) > F.stick) ps.splice(i, 1); continue; }   // 钉在身上的箭：停 F.stick 秒
      if (d.p0) arcStep(d, dt);
      else {
        if (F.drag) { const k = Math.exp(-F.drag * dt); d.vx *= k; d.vy *= k; }
        d.vy += F.G * dt; d.x += d.vx * dt; d.y += d.vy * dt; d.t += dt;
      }
      if (d.ex) { if (d.t > cfg.exhaust.life) ps.splice(i, 1); continue; }
      const b = d.b, h = hitTest(d, o.target(d.u));
      if (h) {
        /* F.stick（后羿的箭）：打中了不消失，钉在命中点停一会儿（按飞来的方向画半截），再没掉 */
        if (F.stick) { d.stuck = 0; d.x = h[0]; d.y = h[1]; } else ps.splice(i, 1);
        o.onSplash(h[0], h[1]);
        if (bs.includes(b) && b.hitCd <= 0) { o.onHit(h[0], h[1], b.first, b); b.first = false; b.hitCd = F.hitEvery; }
      } else if (d.y > o.ground()) { ps.splice(i, 1); if (F.floor) o.onSplash(d.x, o.ground()); }   // 落空的在地上
      else if (d.t > F.life || d.x < -80 || d.x > o.W + 80) ps.splice(i, 1);
    }
    for (let i = bs.length - 1; i >= 0; i--) {
      const b = bs[i];
      if (b.hold) continue;                      // 候场：出场视频还在放
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
      if (tg) {
        /* 反解仰角：err(θ) = 从转到 θ 时的喷口打中落点要的仰角 − 喷口转到 θ 时的指向。θ 往上，指向涨 1:1、要的仰角只跟着
           喷口的挪动慢慢变，err 单调减 —— 在 [lo, hi] 里二分 16 次（精度 1e-5 rad）；两头同号就贴那一头。
           不用"按此刻喷口反解 → 转过去 → 再按新喷口反解"的迭代：转动半径跟喷口到落点的距离差不多大时，每转一点喷口挪得
           比角度变得还多，迭代发散 —— 悬空的真相喷雾第一版实测一次停在 −0.45、一次顶到上限 +0.1（要的是 −0.35）；
           哥们站到男生前排（2026-09-29）离女生近、人又放大，枪口离裤腰转轴 ~300 像素，一直往上翻到上限 +0.21，水从女生头顶飞过去。
           指向：整个人转的（whole）是 angles 的总指向 + REST；其余的指向就是 θ（后坐、前探不算进瞄准）。 */
        const dir = cfg.whole ? (th) => angles(b, th)[1] + REST : (th) => th;
        const err = (th) => { const m = muzzle(p, th, b); return elevation(tg[0] - m[0], tg[1] - m[1]) - dir(th); };
        if (err(AIM.lo) <= 0) want = AIM.lo;
        else if (err(AIM.hi) >= 0) want = AIM.hi;
        else {
          let lo = AIM.lo, hi = AIM.hi;
          for (let k = 0; k < 16; k++) { const mid = (lo + hi) / 2; if (err(mid) > 0) lo = mid; else hi = mid; }
          want = (lo + hi) / 2;
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
      b.m = null;
      const spraying = b.t >= T.enter + (T.fire || 0) && b.t <= se && tg;   // T.fire：刹停之后隔一拍再开火
      if (A) {                                   // 一段段按：每次按下后坐一震；喷的时候上身往前探
        b.kick *= Math.exp(-A.kick[2] * dt);
        b.lean += ((spraying ? 1 : 0) - b.lean) * (1 - Math.exp(-dt * 6));
        if (spraying && !BM && !BW) {            // 光束、弓的一震跟着每一发（beamStep / 放箭那一下）
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
      if (BM) { beamStep(b, dt, spraying, u); continue; }
      /* 弓：b.bw 是离上一次放箭过了几秒。不射的时候（进场、离场）停在满弓（cycle），开射后每 cycle 秒放一箭：
         攒一颗到 b.emit，下面照常出一颗（沿弓此刻的指向） */
      if (BW) {
        if (!spraying) { b.bw = BW.cycle; continue; }
        if ((b.bw = (b.bw ?? BW.cycle) + dt) < BW.cycle) continue;
        b.bw -= BW.cycle; b.emit = 1; if (A) b.kick = 1;
      }
      if (!spraying) continue;
      if (!BW && A && (b.pt % (A.pulse[0] + A.pulse[1])) > A.pulse[0]) { b.emit = 0; continue; }   // 松开那一下
      /* 喷：从转过之后的喷口，沿喷口方向，速度 V（雾再加一点散角和快慢）。一帧攒够几个就出几个，
         每个按它**实际该出口的时刻**补飞一段（age）—— 不补的话帧一卡几个叠成一坨，水柱起疙瘩。 */
      if (!BW) b.emit += dt * F.rate;
      const m = b.m = muzzle(p, b.aim, b), dir = angles(b, b.aim)[spr.arm || cfg.whole ? 1 : 0] + REST;   // 沿喷口此刻真的指向（含后坐）
      while (b.emit >= 1) {
        b.emit -= 1;
        const age = b.emit / F.rate, a = dir + (Math.random() - 0.5) * 2 * F.spread;
        const v = F.V * (1 + (Math.random() - 0.5) * 2 * F.vJit);
        const vx = face * v * Math.cos(a), vy = -v * Math.sin(a);
        if (F.arc && b.tg) { const d = { x: m[0], y: m[1], vx, vy, t: 0, u, b, seq: b.seq++, j: Math.random(), p0: m, p2: b.tg }; arcStep(d, age); ps.push(d); continue; }
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
    /* 悬停的人按此刻 pose 的缩放排（缩放由 o.perch 给，main.js G4STAND，不是召唤时抽的 b.s），站地的按召唤时定的远近 */
    const sOf = (b) => cfg.move === 'hover' && bs.includes(b) ? pose(b)[2] : b.s;
    for (const b of bs) if (!b.hold) out.push({ s: sOf(b), draw: (ctx) => drawOne(ctx, b) });
    /* 光束画在本人身后（从头顶光点往男生那边打，左边、正上方那两个光点的光束会斜穿过她的脸和身子 —— 第一版画在身前，像把她切开），
       光点画在本人之前（它们在头顶，不跟人重叠，被她挡住就看不见了） */
    if (BM) for (const b of bs) if (!b.hold) {
      out.push({ s: sOf(b) - 1e-6, draw: (ctx) => BM.draw(ctx, b, beamGeo(b), T, 'beam') });
      out.push({ s: sOf(b) + 1e-6, draw: (ctx) => BM.draw(ctx, b, beamGeo(b), T, 'orbs') });
    }
    /* 人已离场、水还在飞的，按原来那个人的远近画 */
    /* cfg.over（白娘子、法海）：放出去的东西画在所有帮手之上 —— 两人一左一右同时在场，法海的金字从白娘子半透明的广袖后面飞过去，
       被袖子蒙成一层白雾，读成"字在她身后"而不是"打向女生" */
    for (const [b, g] of groups) out.push({ s: sOf(b) + (cfg.over ? 100 : 1e-6), draw: (ctx) => F.draw(ctx, g, bs.includes(b) ? b : null) });
    return out;
  }

  /* 一个人：上身系里先画手臂（再绕肩转）、再画上身，最后画不动的下身（lo 可无：单层立绘整个人就是 body）。
     cfg.aura（可无）：画在本人身后、跟着她一起倾的东西（真相女神的光芒、光环），给它贴图点 → 屏幕的换算。 */
  function drawOne(ctx, b, probe) {
    const p = pose(b), [x, y, s] = p, [bt, at_] = cfg.whole ? [angles(b, b.aim)[0], 0] : angles(b, b.aim);
    const X = x - spr.foot[0] * s, Y = y - spr.foot[1] * s;
    const I = img[b.skin], put = (im) => ctx.drawImage(im, X, Y, im.width * s, im.height * s);
    const spin = (q, th) => { const [cx, cy] = at(p, q); ctx.translate(cx, cy); ctx.rotate(-face * th); ctx.translate(-cx, -cy); };
    const rl = cfg.move === 'hover' ? rollOf(b) : 0;
    /* probe：measure 量范围时画的那一遍 —— 只画"人"：贴图 + 光环 / 角光，不画身后的放射特效（女神的光芒、恶魔的烟雾和裂光）。
       那几样跟喷雾一样是特效层，可以伸进 HUD 底下（HUD 画在它们之上，恶魔的裂光 18c00c6 起就伸到 y≈110）。 */
    ctx.save();
    if (rl) { const [cx, cy] = at(p, PATH.pivot || cfg.whole.pivot); ctx.translate(cx, cy); ctx.rotate(rl); ctx.translate(-cx, -cy); }
    if (cfg.whole) spin(cfg.whole.pivot, b.aim * WK);  // 悬空：整个人先绕重心转（WK 成），上身再在这个基础上吃后坐
    if (cfg.aura) cfg.aura(ctx, b, s, (q) => at(p, q), probe);
    ctx.save();
    spin(spr.body.pivot, bt);
    if (I.arm && !BW) { ctx.save(); spin(spr.arm.pivot, at_ - bt); put(I.arm); ctx.restore(); }
    put(I.body);
    /* 弓（后羿）：拉弦的前臂在身子之上，沿 spr.arm.axis 前后挪（BW.pose 的 hand，贴图像素）；弦和搭着的箭画在最上 */
    if (I.arm && BW) {
      const q = BW.pose(b, T, sprayEnd(b));
      ctx.save(); ctx.translate(spr.arm.axis[0] * q.hand * s, spr.arm.axis[1] * q.hand * s); put(I.arm); ctx.restore();
      BW.draw(ctx, b, s, (q) => at(p, q), q);
    }
    ctx.restore();
    if (I.lo) put(I.lo);
    ctx.restore();
  }

  const active = () => bs.length > 0;
  function reset() { bs.length = 0; ps.length = 0; }

  /* 诊断用：在场的人（只读），?crewlog=1 时 main.js 打印瞄准角 */
  const peek = () => bs;
  /* 诊断（?crewlog=1）：这个人此刻画出来的范围，两个阈值各一个外框 [x0, y0, x1, y1]（屏幕像素）：
     solid（alpha > MEASURE.solid）：剪影 + 贴着轮廓的那圈亮边 —— 最高点（光环、角、发丝）、中线余量按它；
     glow（alpha > MEASURE.glow）：连外发光看得见的那圈 —— 最低点按它（用户定的：最低点含外发光）。
     在离屏画布上真画一遍再扫像素 —— 按贴图外框算的话，斜着的人外框角远大于剪影。 */
  let mc = null;
  function measure(b) {
    if (!img) return null;
    if (!mc) { mc = document.createElement('canvas'); mc.width = o.W; mc.height = 1400; }
    const c = mc.getContext('2d', { willReadFrequently: true });
    c.clearRect(0, 0, mc.width, mc.height); drawOne(c, b, true);
    const d = c.getImageData(0, 0, mc.width, mc.height).data;
    const box = (thr) => {
      let x0 = 1e9, y0 = 1e9, x1 = -1, y1 = -1;
      for (let y = 0; y < mc.height; y++) for (let x = 0; x < mc.width; x++) {
        if (d[(y * mc.width + x) * 4 + 3] <= thr) continue;
        if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
      }
      return x1 < 0 ? null : [x0, y0, x1, y1];
    };
    return { solid: box(MEASURE.solid), glow: box(MEASURE.glow) };
  }
  return { init, load, summon, update, items, active, reset, peek, measure, cfg };
}
/* measure 的两个阈值（alpha 0~255）。glow 32 = 外发光 1/8 不透明：再淡的那圈在明亮客厅底图上已经看不出来
   （贴图里 alpha 16 那圈比 32 那圈只往外多 ~12 贴图像素，肉眼分不出边）。 */
const MEASURE = { solid: 200, glow: 32 };

/* 一组帮手合起来调度（档 4 每边一组三个人，各是一份 Crew、max 1）。**同一时间只有一个人在场**
   （2026-09-28 用户看完三人同屏："三个女神太多了，每个都显得特别小，还是改一个，放大一些"）：
   · 有人在场（含正在离场的）再送 = 给这个人 summon：max 1 的 Crew 满员时续一段 T.spray、名字条重播「×N」，
     正在离场的从当前高度被叫回来（hoverPose 的 back）—— 不换人；
   · 场上没人时送 = 按成员顺序轮到下一个。从 0 号起（成员顺序见 main.js G4L / G4R：女生侧第一个是白娘子，男生侧是恶魔）。
   pick（可无）：场上没人时强制召第几个成员（诊断参数 ?g4L= / ?g4R=，越界夹到两头），不动轮换顺序；有人在场时照样只续。 */
function CrewGroup(members) {
  let next = 0;
  return {
    members,
    /* 返回 [召到的成员, 新来的人 b]（续时间 / 叫回时 b 为 undefined） */
    summon(pick) {
      const on = members.find(m => m.active());
      if (on) return [on, on.summon()];
      if (pick != null && !Number.isNaN(pick)) { const m = members[Math.max(0, Math.min(members.length - 1, pick | 0))]; return [m, m.summon()]; }
      const m = members[next];
      next = (next + 1) % members.length;
      return [m, m.summon()];
    },
    active: () => members.some(m => m.active()),
    reset() { members.forEach(m => m.reset()); next = 0; },
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
  spr: { src: 'assets/world/buddy%n_%k.webp', body: { src: 'up', pivot: [266, 200], k: 1 }, lo: { src: 'lo' },
         foot: [260, 446], muzzle: [2, 88] },
  /* 八个形象，点一次随机挑一个场上没人用的。1 是最早三个里留下的；4~10 是 2026-09-29 加的（用户嫌前三个"整体造型太相近"），
     借 80/90 后熟知的角色，只留认人特征、发型服饰重新设计（v14/buddy/make.py 有逐个说明）。
     2、3（反戴红帽 / 金发花衬衫）用户要求删掉，原图、贴图都删了。 */
  skins: [1,                        // skate1 棕发护目镜花短裤红滑板
          4, 5, 6, 7,               // skate4 金箍浪子（至尊宝）/ skate5 格格府贝勒（五阿哥）/ skate6 夜色假面绅士 / skate7 红发宿敌（八神庵）
          8, 9, 10],                // skate8 刺猬头武道家 / skate9 红发篮球少年 / skate10 草帽船长
  T: { enter: 0.55, spray: 2.5, exit: 0.5 },
  max: 3, gap: 0.3,
  /* 三排在男生身后（被男生挡住），两排在他前面（2026-09-29 用户："哥们出现的位置不一定是男生后面，也可以出现在前面，
     注意近大远小和遮挡"；"前面最多可以站两个"）：前排脚底往下（crew.js pose：抬高 = (地面 − 视平线) × (1 − d)，d > 1 就是往下），
     画在男生之上。前排只站右半边（r 0.5~1，人往屏幕右沿靠）：站中间会把手机和两人的手整个挡住。闺蜜（MIST.rows）同样。
     一排 = [远近 d 下限, 上限, r 下限, 上限]；画多大 = d × k。k 0.85：d = 1（跟男生一样远）时哥们跟男生一样大（截图对照 1 / 0.85 / 0.75 定的）。
     后排的 d 是原来的缩放 ÷ 0.85（原 0.74~0.80 / 0.66~0.71 / 0.58~0.63）：画出来一样大，脚底按透视往下挪 25~45 像素。
     前排 d 1.04~1.14 → 画出来是男生的 0.88~0.97 倍（第一版 k = 1、d 1.10~1.16，比男生大一圈多，用户："比男女主大很多，不合理"）。 */
  k: 0.85,
  rows: [[0.87, 0.94], [0.78, 0.84], [0.68, 0.74], [1.04, 1.08, 0.5, 1], [1.10, 1.14, 0.5, 1]],
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
  spr: { src: 'assets/world/bestie%n_%k.webp', arm: { src: 'arm', pivot: [198, 105] },
         body: { src: 'up', pivot: [174, 202], k: 0.3 }, lo: { src: 'lo' },
         foot: [184, 485], muzzle: [361, 20] },
  /* 七个形象，点一次随机挑一个场上没人用的（summon）。2 是最早三个比基尼里留下的那个；4~9 是 2026-09-29 加的（用户嫌前三个"整体造型太相近"），
     借 80/90 后熟知的角色，只留认人特征、发型服饰重新设计（v14/bestie/make.py 有逐个说明）。
     1、3（src2 棕色高马尾红比基尼、src4 金发双马尾黑比基尼）用户说"没特色"拿掉了，贴图删了，要回来重跑 make.py。 */
  skins: [2,                        // src3 黑短发头顶墨镜、条纹比基尼、粉平衡车
          4, 5, 6,                  // src5 红衣忍者扇娘（紫黑）/ src6 麻花辫探险家 / src7 蓝发发明家（自制喷雾器）
          7, 8, 9],                 // src8 月光水手少女 / src9 紫衣仙子 / src10 格格
  anim: { pulse: [0.42, 0.14], kick: [0.12, 0.05, 10], lean: 0.08, bob: [3, 2.6] },
  T: { enter: 0.55, spray: 2.5, exit: 0.5 },
  max: 3, gap: 0.3,                 // 同屏最多三个（≤ 形象数）：满员时续时间，同时在场的各不相同
  /* 同哥们（Buddy.rows、k）：三排在女生身后，两排在她前面（2026-09-29 用户："闺蜜也是一样的逻辑"）—— 脚往下、画在女生之上；
     前排只站左半边（r 0.5~1，人往屏幕左沿靠）。k 0.85：d = 1 时闺蜜跟女生一样高（她站得直、脚下有平衡车，k = 1 高出一截）。 */
  k: 0.85,
  rows: [[0.87, 0.94], [0.78, 0.84], [0.68, 0.74], [1.04, 1.08, 0.5, 1], [1.10, 1.14, 0.5, 1]],
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
function drawAura(ctx, b, s, at, probe) {
  const A = TRUTH_FX.aura, [cx, cy] = at(TRUTH.spr.chest), [hx, hy] = at(TRUTH.spr.head);
  const k = Math.min(1, b.t / 0.3), R = A.R * s;                 // 冲进来的头 0.3 秒里长出来
  ctx.save();
  if (!probe) {                                                  // measure 不量光芒（见 drawOne 的 probe）
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
    g.addColorStop(0, `rgba(${A.rgb},${(A.a * k).toFixed(3)})`); g.addColorStop(0.45, `rgba(${A.rgb},${(A.a * 0.45 * k).toFixed(3)})`);
    g.addColorStop(1, `rgba(${A.rgb},0)`);
    ctx.fillStyle = g; ctx.beginPath();
    for (let i = 0; i < A.rays; i++) {
      const a = i / A.rays * 6.283 + b.t * A.spin, w = A.ray * (i % 2 ? 0.6 : 1);   // 一长一短交替，不像齿轮
      ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(a - w) * R, cy + Math.sin(a - w) * R); ctx.lineTo(cx + Math.cos(a + w) * R, cy + Math.sin(a + w) * R);
    }
    ctx.fill();
  }
  const y = hy - A.haloY * s + Math.sin(b.t * 2.4) * 3 * s, rx = A.halo[0] * s, ry = A.halo[1] * s;
  ctx.globalAlpha = k;
  ctx.lineWidth = A.haloW[0] * s; ctx.strokeStyle = `rgba(${A.halo1},0.85)`;
  ctx.beginPath(); ctx.ellipse(hx, y, rx, ry, 0, 0, 6.283); ctx.stroke();
  ctx.lineWidth = A.haloW[1] * s; ctx.strokeStyle = `rgb(${A.halo2})`;
  ctx.beginPath(); ctx.ellipse(hx, y, rx, ry, 0, 0, 6.283); ctx.stroke();
  ctx.restore();
}
/* F：配色尺寸表（TRUTH_FX / DEMON_FX），C：角色配置（寿命在 C.fluid / C.exhaust）。真相女神、灭迹恶魔共用这一套画法，只换颜色。 */
/* 雾锥：每颗粒子一团雾（出口 r0 → 飞完 r1，托底一圈深色 + 雾身），刚出口那一小段叠亮芯。
   真相女神、灭迹恶魔的喷雾就是它；白娘子的水柱、法海的咒语外面也套一层（BAISU_FX.mist / FAHAI_FX.mist，用户："水流和咒语太细太小，参考真相女神的喷雾"） */
function drawFog(F, C, ctx, ps) {
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
}
function drawSpray(F, C, ctx, ps, b) {
  const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a.toFixed(3)})`;
  const us = (d) => Math.min(1, d.t / (d.ex ? C.exhaust.life : C.fluid.life));
  drawFog(F, C, ctx, ps);
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
   · 层级：2026-09-29 起在两个主角身后（main.js renderActors）：放大到跟白娘子、法海一样大之后，画在主角之前会把女主整个人盖住；
     档 4 六个人都一样（用户："法海和白娘子在男女主的下层"）。 */
const TRUTH = {
  face: +1,
  move: 'hover',
  /* 第二版立绘（2026-09-27，v14/truth/make2.py）：竖直悬浮、罐子夹在腰侧本来就斜朝右下（rest −0.505 rad ≈ 29°），
     单层（没有 lo）、三层金色外发光烘在贴图里。整个人绕腰胯（whole.pivot，重心附近）小幅前后倾着瞄：
     倾的时候头和脚一左一右摆、人留在画内；瞄准用二分反解（update）。量点都是贴图像素，由 make2.py 打印。
     第一版（truth1_*，横扛罐子）要前倾 0.7~1 rad 才对得准，人一抬高放大就甩出画面，见 make2.py 文件头。 */
  whole: { pivot: [168, 281] },
  exhaust: { at: [119, 195], rate: 40, V: 420, spread: 0.18, life: 0.4, gap: 14 },   // 罐尾（贴图像素）、每秒几团、出口速度、散角、寿命、人动时两团最多隔几像素
  spr: { src: 'assets/world/truth%n_%k.webp', body: { src: 'up', pivot: [168, 281], k: 1 },
         foot: [160, 608], muzzle: [370, 334], rest: -0.505, head: [211, 78], chest: [194, 185] },
  skins: [2],
  aura: (ctx, b, s, at, probe) => drawAura(ctx, b, s, at, probe),
  anim: { pulse: [0.7, 0.16], kick: [0, 0.06, 9], lean: 0.03, bob: [5, 2.2] },
  /* 在场 15 秒（2026-09-29，原来喷 2.8 秒）：跟白娘子、法海一样，底下铺一片自己的法术潮（sea.js TruthTide / DemonTide），
     潮推进来要 1.4 秒，只待 3.8 秒的话潮刚铺满就退。喷的时长只管画面，数值只在送礼那一刻加（main.js impact 只动画面）。 */
  T: { enter: 0.55, spray: 14.0, exit: 0.45, fire: 0.18 },   // fire：刹停后隔多久开喷（先"嘭"地停住，再"呲——"）
  max: 1, gap: 0.3,
  rows: [[0.94, 0.96]],                   // 悬停的人不用它的缩放（main.js G4STAND 直接给），summon 要一排才留着
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
function drawDemonAura(ctx, b, s, at, probe) {
  const A = DEMON_FX.aura, [cx, cy] = at(DEMON.spr.chest);
  const k = Math.min(1, b.t / 0.3), R = A.R * s;
  ctx.save();
  if (!probe) {                                                  // measure 不量烟雾、裂光（见 drawOne 的 probe）
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
  aura: (ctx, b, s, at, probe) => drawDemonAura(ctx, b, s, at, probe),
  fluid: { ...TRUTH.fluid, draw: (ctx, ps, b) => drawSpray(DEMON_FX, DEMON, ctx, ps, b) },
};
const Demon = Crew(DEMON);

/* ======== 档 4 每边一组三人（2026-09-28 起；同时只一个在场、轮换，见 CrewGroup）========
   三对，一对一对立：白娘子 vs 法海、真相女神 vs 灭迹恶魔、嫦娥 vs 后羿（2026-09-29 用户："删掉黑寡妇、超人、杨戬，新增一对嫦娥 vs 后羿，
   主题为月和日，制作规格和白娘子法海一致"）。每个人在场 15 秒，底下各铺一片自己的法术潮（sea.js）。
   每个人的武器都不一样（大水流 / 金字 / 雾 / 月牙 / 火球），不能走 skins 换皮（skins 要同一个裁边框、同一套 foot / muzzle），
   所以每人一份 Crew 配置，照 TRUTH / DEMON 的写法（悬停、whole 整个人小幅前后倾、二分反解瞄准），每边一个 CrewGroup（main.js），站位 main.js G4STAND。
   立绘 v14/<名>/make.py（共用 v14/crewart.py），量点都是它打印的贴图像素。
   配色按明亮底图的规矩（chashouji-fx）：发光靠色相、实体靠暖黑描边 WARM_INK。 */
const WARM_INK = [58, 44, 38];
const rgbaOf = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a.toFixed(3)})`;
/* ---- ② 白娘子（2026-09-28 替掉月亮查岗使 —— 用户："水月冰太像原著了，可能会有版权风险"） ----
   民间传说人物，没有版权问题；装束参考经典电视剧（白色广袖汉服 + 冰蓝银边、高髻珠钗、白披帛），脸是原创的（v14/baisu/make.py）。
   用户要的四件事：① 从屏幕左上侧飞下来；② 比真相女神大 30%（main.js G4STAND.baisu 第三项）；③ 全身自发光；
   ④ 念咒，从掌中召出大水流泼向男生，**持续 15 秒**；同时整个屏幕底部涌起海水、海里有虾兵蟹将（sea.js），她走海水就退。
   · 念咒：立绘就是念咒的姿势（左手胸前剑指、右手托水球），不靠转身瞄准 —— 她比女神大三成、裙摆披帛往左上飘一大片，
     整个人跟着瞄准倾 0.5 rad 的话，裙角要甩出去两百像素。所以 whole.k 只让身子跟瞄准角的一小份（轻轻前后倾，看着是活的），
     水流方向照样按完整的瞄准角出（crew.js angles：喷口指向 = th）。
   · 掌心水柱：3 渲 2 序列帧（drawJet）；一段"哗——"（pulse 1.0 秒）停一下（0.35），每喷一下身子微微一震（kick）。
   · 自发光：三层冰蓝外发光烘在贴图里（make.py），运行时再加身后一团会呼吸的冷白光 + 绕着她飘的水珠 + 掌心水球的光（drawBaisuAura）。 */
/* 掌心水柱：Blender 渲的 3 渲 2 循环帧（tools/3d/water/jet.py，贴图参数在 sea.js WaterArt.jet）。
   第一版用 drawStream 的粗线段连水滴（出口 40 像素宽、圆头一段段叠起来），读成一只倒扣的瓶子往下倒水 ——
   用户："不要用瓶子倒水，而是直接从手掌中喷水"。现在是一束高压水：掌心细、往前胀、表面水纹往前滚、末端碎成水珠。
   水滴（ps）照旧按物理飞、管命中（crew.js update / hitTest），但**不画**，只用来定水柱的两头：
     · 按住喷（b.m 有）：水柱从掌心接到最老那颗水滴，整张贴图按这段长度缩放（喷出去的那 0.3 秒里水柱一路伸长）；
     · 松开（b.m 没了）：掌心那头从最新那颗水滴起算 —— 尾巴离开掌心往前飞，贴图只截后面那一段。
   方向：掌心 → 瞄的落点（b.tg）。水滴走的是带重力的弧线，水柱画直线：打到脸上这段只有 0.3~0.4 秒，弧度看不出来。 */
const JET_BODY = 0.88;                                         // 贴图的这一成长度对准落点（柱身到 0.84，再带一点碎水）
/* 粗细再乘几倍：贴图里柱身从掌心 30 像素胀到末端 90；原样画时比真相女神的雾锥（直径 60 → 220）细一大圈，
   用户："水流太细太小，参考真相女神的喷雾"。2.2 倍 ≈ 66 → 200，外面再套一层水雾（BAISU_FX.mist） */
const JET_W = 2.2;
function drawJet(ctx, ps, b, hitR) {
  const J = WaterArt.jet;
  if (!J.img || !ps.length) return;
  const old = ps[0], neu = ps[ps.length - 1];
  if (b && b.m) b.jm = b.m;                                     // 记住掌心（松开之后还要按它截尾巴）
  const M = b && b.jm ? b.jm : [neu.x, neu.y];
  const T = b && b.tg ? b.tg : [old.x, old.y];
  /* 伸到哪：最老那颗水滴再往前 hitR（命中半径）—— 水滴一进半径就判中、被拿掉，最老的那颗永远差落点一截，
     只画到它的话水柱停在男生头顶上方六十像素（真页面上男生趴地时看得最清楚） */
  const D = Math.hypot(T[0] - M[0], T[1] - M[1]), reach = Math.min(D, Math.hypot(old.x - M[0], old.y - M[1]) + hitR);
  const tail = b && b.m ? 0 : Math.min(reach, Math.hypot(neu.x - M[0], neu.y - M[1]));
  if (reach - tail < 12) return;
  /* L：贴图里柱身 + 碎开那一段的长度。柱身在 jet.py 里只到全长的 84%，后面是散开的水珠 —— 按 JET_BODY 对准落点，
     柱身正好砸到脸上，水珠冲过去一点盖进水花里 */
  const L = (J.w - J.x0) * JET_BODY, ang = Math.atan2(T[1] - M[1], T[0] - M[0]);
  const k = (b && b.m ? reach : D) / L;                        // 长度方向的缩放：按住时整张缩到当前长度，松开后按全长截
  const ws = JET_W * Math.max(0.8, Math.min(1.05, D / L));     // 粗细：离得近细一点，不跟长度一起压扁
  const i = Math.floor(((b ? b.t : neu.t) / J.loop % 1) * J.n) % J.n;
  const [sx, sy, , sh] = atlasCell(J, J, i);
  const a = tail / k, e = (b && b.m ? J.w - J.x0 : reach / k);
  ctx.save();
  ctx.translate(M[0], M[1]); ctx.rotate(ang); ctx.scale(k, ws);
  ctx.drawImage(J.img, sx + J.x0 + a, sy, e - a, sh, a, -J.cy, e - a, sh);
  ctx.restore();
}
const BAISU_FX = {
  glow: { R: 380, a: 0.34, rgb: [150, 215, 255], core: [236, 248, 255], breath: [1.6, 0.18] },   // 身后冷光：半径、不透明度、颜色、亮芯、呼吸 [角频率, 幅度]
  motes: { n: 12, R: [170, 330], r: [5, 10], spin: 0.5, edge: [24, 84, 180], fill: [200, 236, 255] },  // 绕身水珠：几颗、绕的半径范围、珠子半径、转速
  orb: { R: 70, rgb: [120, 200, 255] },   // 掌心水球外的光团半径（贴图像素 × s）、颜色；泼的时候（kick）跟着胀一下
  /* 水柱外面一层水雾（drawFog）：大小同真相女神（30 → 110），深蓝托底 / 浅蓝雾身 / 近白亮芯；单团淡，靠叠 */
  mist: { r0: 30, r1: 110, rim: [30, 90, 190], body: [160, 220, 255], core: [245, 252, 255], a: [0.15, 0.24], star: 0 },   // 粒子只有女神的 1/3（80 vs 220），单团浓一些
};
function drawBaisuAura(ctx, b, s, at, probe) {
  const G = BAISU_FX.glow, M = BAISU_FX.motes, [cx, cy] = at(BAISU.spr.chest);
  const k = Math.min(1, b.t / 0.4);
  const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a.toFixed(3)})`;
  ctx.save();
  if (!probe) {                                                  // measure 不量身后的光和水珠（特效层，同女神的光芒）
    const br = 1 + G.breath[1] * Math.sin(b.t * G.breath[0]), R = G.R * s * br;
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
    g.addColorStop(0, rgba(G.core, G.a * k)); g.addColorStop(0.4, rgba(G.rgb, G.a * 0.55 * k)); g.addColorStop(1, rgba(G.rgb, 0));
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.283); ctx.fill();
    /* 水珠：椭圆轨道绕胸口转，各自半径不同、忽远忽近（前半圈大、后半圈小一点 —— 读成绕着她转，不是贴在平面上） */
    for (let i = 0; i < M.n; i++) {
      const a = i / M.n * 6.283 + b.t * M.spin * (i % 2 ? 1 : -0.7), rr = (M.R[0] + (M.R[1] - M.R[0]) * ((i * 0.618) % 1)) * s;
      const x = cx + Math.cos(a) * rr, y = cy + Math.sin(a) * rr * 0.55, r = (M.r[0] + (M.r[1] - M.r[0]) * ((i * 0.37) % 1)) * s * (0.8 + 0.2 * Math.sin(a));
      ctx.fillStyle = rgba(M.edge, 0.7 * k); ctx.beginPath(); ctx.arc(x, y, r + 2, 0, 6.283); ctx.fill();
      ctx.fillStyle = rgba(M.fill, 0.95 * k); ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
      ctx.fillStyle = rgba([255, 255, 255], k); ctx.beginPath(); ctx.arc(x - r * 0.3, y - r * 0.3, r * 0.3, 0, 6.283); ctx.fill();
    }
  }
  /* 掌心水球的光：跟着人画（算"人"的一部分，measure 量它） */
  const O = BAISU_FX.orb, [ox, oy] = at(BAISU.spr.muzzle), R = O.R * s * (1 + 0.25 * b.kick + 0.08 * Math.sin(b.t * 5));
  const g = ctx.createRadialGradient(ox, oy, 0, ox, oy, R);
  g.addColorStop(0, rgba([255, 255, 255], 0.85 * k)); g.addColorStop(0.35, rgba(O.rgb, 0.5 * k)); g.addColorStop(1, rgba(O.rgb, 0));
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(ox, oy, R, 0, 6.283); ctx.fill();
  ctx.restore();
}
const BAISU = {
  ...TRUTH,
  whole: { pivot: [534, 324], k: 0.12 },        // 身子只跟瞄准角的 12%（见上）
  over: true,                                   // 水柱画在所有帮手之上（crew.js items）
  exhaust: null,                                // 仙人本来就会飞，没有尾焰
  spr: { src: 'assets/world/baisu%n_%k.webp', body: { src: 'up', pivot: [534, 324], k: 1 },
         foot: [343, 751], muzzle: [732, 447], rest: -0.9, head: [516, 60], chest: [546, 264] },   // v14/baisu/make.py 打印；foot 是裙摆最低那一角
  skins: [1],
  aura: (ctx, b, s, at, probe) => drawBaisuAura(ctx, b, s, at, probe),
  /* rest -0.9：掌心 → 男生的脸大约朝右下 50°~70°（她悬在左上、男生在右下）；立绘里手腕 → 水球是 −0.70。
     瞄准角 ±0.55 在它上下，水流方向落在 −1.45 ~ −0.35，男生站着、趴地都够得着。 */
  aim: { lo: -0.55, hi: 0.55, rate: 1.6, follow: 8, stiff: 40 },
  /* 打全身（2026-09-28 用户："水流可以往男生身上各处洒，不用只洒头"）：main.js 给的落点 u 0 → 1 是他身上从一头到另一头的上沿，
     u 以 0.5 为中心扫 ±0.55（两个正弦叠，夹到 0~1），比女神慢一半：水柱在他身上一路扫过去看得清 */
  sweep: { a: [0.4, 0.15], w: [0.6, 1.5] },
  /* 出场：从左上画外斜着飞下来（带一点前倾 roll0，刹停时回正）；离场原路往左上飞走 */
  path: { from: (s, hx, hy) => [hx - 700 * s, hy - 700 * s], roll0: -0.2, to: (s, x, y) => [x - 800 * s, y - 800 * s], rollOut: -0.15 },
  anim: { pulse: [1.0, 0.35], kick: [0, 0.03, 6], lean: 0.02, bob: [8, 1.5] },
  /* 在场共 15 秒（用户定）：飞下来 1.0 + 施法 13.5 + 飞走 0.5。续送再加 13.5（crew.js summon 续一段 T.spray）。 */
  T: { enter: 1.0, spray: 13.5, exit: 0.5, fire: 0.3 },
  /* life 0.7：打到脸上 ~0.4 秒，没打中的再飞一小段就散（1.2 时越过男生一路砸到地板上） */
  fluid: { V: 1150, G: 700, drag: 0.3, rate: 80, spread: 0.12, vJit: 0.06, life: 0.7, miss: 130, radius: 75, snap: 14, hitEvery: 0.3, floor: false,
           draw: (ctx, ps, b) => { drawFog(BAISU_FX.mist, BAISU, ctx, ps); drawJet(ctx, ps, b, BAISU.fluid.radius); } },
};
const Baisu = Crew(BAISU);

/* ---- ⑦ 法海（男生档 4，2026-09-28，跟白娘子对立）----
   用户："给男生那边做个法海，与白娘子对立，在男生那边。法海可以向女神发送各种金光咒语，周身也是金光自发光。
          同样也需要跟白娘子海面的动效，可能是在金光虚化的佛经卷轴，也会和海平面一样波动，虾兵蟹将可以对应神兽小佛"。
   跟白娘子左右对称：从右上画外斜着飞下来，比同侧的人大 30%（main.js G4STAND.fahai 第三项），在场 15 秒，脚下铺金光经卷（sea.js Scroll）。
   立绘 v14/fahai/make.py：原创脸，光头戒疤、黄僧袍红金袈裟、托金钵，左掌朝女生伸出（掌心一团金光）—— 咒语从掌心出（muzzle）。
   · 咒语：一个个金字（卍 唵 嘛 呢 叭 咪 吽 轮着来）从掌心直直打出去（G 0），打在女生身上迸成更多金字（main.js RECIPE.fahai）；
     一段"念"（pulse 1.1 秒）停一下（0.35），跟白娘子一样只让身子跟瞄准角的一小份（whole.k），咒语按完整角度出。
   · 自发光：三层金色外发光烘在贴图里（make.py），运行时身后再加一圈慢慢转的佛光（放射金光 + 头后光轮）、掌心金光团（drawGodAura）。
   · 打全身：同白娘子，落点从她身上一头扫到另一头（main.js bodyTarget）。 */
const FAHAI_FX = {
  halo: { at: 'head', R: 92, lw: 7, rgb: [255, 206, 70], edge: [140, 70, 10] },       // 头后光轮：半径（贴图像素 × s）、线宽、金、深褐托底
  rays: { n: 14, R: [150, 420], w: 0.09, spin: 0.12, rgb: [255, 200, 60], a: 0.28 },   // 身后放射金光：几道、从多远到多远、每道张角、转速
  glow: { R: 360, a: 0.3, rgb: [255, 196, 70], core: [255, 244, 200] },               // 身后一团暖光
  orb: { R: 64, rgb: [255, 200, 60] },                                                 // 掌心金光团
  /* 咒语金字：出手时字号 → 飞 grow 秒后的字号；every：每几颗粒子画一个字（其余只当金光雾）。
     第一版 24 → 50、每秒 10 个字，一串小字 —— 用户："咒语太细太小，参考真相女神的喷雾"：字放到 40 → 90，外面套一层金光雾锥（mist） */
  /* lw：描边宽 = 字号的几成。原来 0.16（90 号字描 14 像素，一圈深褐粗边），用户："咒语描边不要那么粗" → 0.06，描边也半透一点（edge 0.8）；
     字从底图上跳出来靠身后那团金光（glow），不靠粗描边 */
  mantra: { chars: '卍唵嘛呢叭咪吽', size: [40, 90], grow: 0.22, every: 3, lw: 0.06, fill: [255, 220, 90], edge: [96, 40, 6], glow: [255, 190, 40] },
  mist: { r0: 30, r1: 110, rim: [170, 90, 10], body: [255, 214, 100], core: [255, 250, 225], a: [0.2, 0.3], star: 0 },      // 粒子只有女神的 1/7（30 vs 220），单团浓一些
};
/* 仙佛的光（法海、嫦娥、后羿共用，F 换颜色，spr 给 chest / halo / muzzle 三个贴图点）：身后一团暖光 + 慢慢转的放射光 + 头后光轮 + 掌心光团 */
function drawGodAura(F, spr, ctx, b, s, at, probe) {
  const k = Math.min(1, b.t / 0.4), [cx, cy] = at(spr.chest);
  const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a.toFixed(3)})`;
  ctx.save();
  if (!probe) {                                                  // measure 不量身后的光（特效层，同女神的光芒）
    const G = F.glow, g = ctx.createRadialGradient(cx, cy, 0, cx, cy, G.R * s);
    g.addColorStop(0, rgba(G.core, G.a * k)); g.addColorStop(0.45, rgba(G.rgb, G.a * 0.5 * k)); g.addColorStop(1, rgba(G.rgb, 0));
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, G.R * s, 0, 6.283); ctx.fill();
    /* 放射金光：一道道细长的扇形，慢慢转，一明一暗 */
    const R = F.rays;
    for (let i = 0; i < R.n; i++) {
      const a = i / R.n * 6.283 + b.t * R.spin, fl = 0.6 + 0.4 * Math.sin(b.t * 2.3 + i * 1.9);
      const r0 = R.R[0] * s, r1 = R.R[1] * s * (0.8 + 0.2 * Math.sin(i * 2.7));
      const rg = ctx.createRadialGradient(cx, cy, r0, cx, cy, r1);
      rg.addColorStop(0, rgba(R.rgb, R.a * fl * k)); rg.addColorStop(1, rgba(R.rgb, 0));
      ctx.fillStyle = rg; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.arc(cx, cy, r1, a - R.w, a + R.w); ctx.closePath(); ctx.fill();
    }
  }
  /* 头后光轮：算"人"的一部分（measure 量它） */
  const H = F.halo, [hx, hy] = at(spr.halo), hr = H.R * s;
  ctx.lineWidth = (H.lw + 4) * s; ctx.strokeStyle = rgba(H.edge, 0.55 * k); ctx.beginPath(); ctx.arc(hx, hy, hr, 0, 6.283); ctx.stroke();
  ctx.lineWidth = H.lw * s; ctx.strokeStyle = rgba(H.rgb, 0.9 * k); ctx.beginPath(); ctx.arc(hx, hy, hr, 0, 6.283); ctx.stroke();
  /* 掌心金光团：念的时候（kick）胀一下 */
  const O = F.orb, [ox, oy] = at(spr.muzzle), orR = O.R * s * (1 + 0.3 * b.kick + 0.08 * Math.sin(b.t * 6));
  const og = ctx.createRadialGradient(ox, oy, 0, ox, oy, orR);
  og.addColorStop(0, rgba([255, 255, 240], 0.95 * k)); og.addColorStop(0.35, rgba(O.rgb, 0.6 * k)); og.addColorStop(1, rgba(O.rgb, 0));
  ctx.fillStyle = og; ctx.beginPath(); ctx.arc(ox, oy, orR, 0, 6.283); ctx.fill();
  ctx.restore();
}
/* 咒语：每颗粒子画一个金字（按 seq 轮着取字），身后一团金光、拖一小截金色残影；出手时小、飞 grow 秒长到全尺寸 */
function drawMantra(ctx, ps) {
  const M = FAHAI_FX.mantra, rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a.toFixed(3)})`;
  ctx.save();
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  for (const d of ps) {
    if (d.ex || d.seq % M.every) continue;
    const e = Math.min(1, d.t / M.grow), sz = M.size[0] + (M.size[1] - M.size[0]) * e;
    const sp = Math.hypot(d.vx, d.vy) || 1, tx = -d.vx / sp, ty = -d.vy / sp;
    const g = ctx.createRadialGradient(d.x, d.y, 0, d.x, d.y, sz * 1.1);
    g.addColorStop(0, rgba(M.glow, 0.55)); g.addColorStop(1, rgba(M.glow, 0));
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(d.x, d.y, sz * 1.1, 0, 6.283); ctx.fill();
    ctx.lineCap = 'round';
    for (const [w, a, L] of [[sz * 0.5, 0.22, 2.2], [sz * 0.22, 0.5, 1.4]]) {   // 残影：往来的方向拖两道渐短的金光
      ctx.lineWidth = w; ctx.strokeStyle = rgba(M.glow, a);
      ctx.beginPath(); ctx.moveTo(d.x, d.y); ctx.lineTo(d.x + tx * sz * L, d.y + ty * sz * L); ctx.stroke();
    }
    ctx.save(); ctx.translate(d.x, d.y); ctx.rotate(Math.sin(d.t * 5 + d.j * 6) * 0.25);
    ctx.font = `900 ${sz.toFixed(1)}px "Noto Serif CJK SC","Songti SC","STSong","SimSun",serif`;
    const ch = M.chars[((d.seq % M.chars.length) + M.chars.length) % M.chars.length];
    ctx.lineWidth = Math.max(2, sz * M.lw); ctx.strokeStyle = rgba(M.edge, 0.8); ctx.strokeText(ch, 0, 1);
    ctx.fillStyle = rgba(M.fill, 1); ctx.fillText(ch, 0, 1);
    ctx.restore();
  }
  ctx.restore();
}
const FAHAI = {
  ...DEMON,
  whole: { pivot: [292, 310], k: 0.12 },        // 身子只跟瞄准角的 12%（同白娘子：大袖子、袈裟往右上飘一大片，整个人倾会甩出画）
  exhaust: null,                                // 仙佛本来就会飞，没有尾焰
  over: true,                                   // 咒语画在所有帮手之上（crew.js items）
  spr: { src: 'assets/world/fahai%n_%k.webp', body: { src: 'up', pivot: [292, 310], k: 1 },
         foot: [486, 716], muzzle: [77, 170], head: [262, 84], chest: [269, 250], halo: [262, 140],   // v14/fahai/make.py 打印；foot 是右脚草鞋底
         /* rest −1.15：掌心 → 女生身上大约朝左下 55°~75°（他悬在右上、女生在左下）。掌心不是枪管，rest 直接取典型俯角；
            瞄准角 −0.4 ~ +0.45 在它上下，咒语方向落在 −1.55 ~ −0.7，女生站着、倒地都够得着 */
         rest: -1.15 },
  skins: [1],
  aura: (ctx, b, s, at, probe) => drawGodAura(FAHAI_FX, FAHAI.spr, ctx, b, s, at, probe),
  aim: { lo: -0.4, hi: 0.45, rate: 1.6, follow: 8, stiff: 40 },
  sweep: { a: [0.4, 0.15], w: [0.6, 1.5] },      // 打全身，同白娘子
  /* 出场：从右上画外斜着飞下来（带一点前倾 roll0，刹停时回正）；离场原路往右上飞走 */
  path: { from: (s, hx, hy) => [hx + 700 * s, hy - 700 * s], roll0: 0.2, to: (s, x, y) => [x + 800 * s, y - 800 * s], rollOut: 0.15 },
  anim: { pulse: [1.1, 0.35], kick: [0, 0.03, 6], lean: 0.02, bob: [8, 1.5] },
  /* 在场共 15 秒（同白娘子）：飞下来 1.0 + 施法 13.5 + 飞走 0.5。续送再加 13.5。 */
  T: { enter: 1.0, spray: 13.5, exit: 0.5, fire: 0.3 },
  /* 咒语：直线（G 0）、不快（V 820，一个字看得清），每秒 10 个；radius 近距命中（同白娘子：从上往下打，越不过落点那一列） */
  /* rate 30：每 3 颗画一个字（每秒还是 10 个字），另外两颗只当金光雾 —— 雾锥要密才连成一股（真相女神是 220） */
  fluid: { V: 820, G: 0, drag: 0, rate: 30, spread: 0.12, vJit: 0.05, life: 1.3, miss: 110, radius: 70, snap: 14, hitEvery: 0.3, floor: false,
           draw: (ctx, ps) => { drawFog(FAHAI_FX.mist, FAHAI, ctx, ps); drawMantra(ctx, ps); } },
};
const Fahai = Crew(FAHAI);

/* ---- ⑧ 嫦娥（女生档 4，2026-09-29，跟后羿对立：月 vs 日）----
   用户："新增一对人物，嫦娥 vs 后羿，主题为月和日。制作规格和白娘子法海一致"。
   · 立绘 v14/change/make.py：月白浅紫广袖、飞天髻月牙发饰、长披帛，朝右飞，右掌心上方悬一弯银白小月牙（现在只是装饰，掌心光团 drawGodAura）；
     银蓝外发光烘在贴图里。
   · 规格照白娘子：从左上飞下来、在场 15 秒、whole.k 0.12 身子只轻轻倾、打男生全身（main.js BODY_AIM）、在男女主身后，
     底下铺明月银河（sea.js MoonSky）。
   · 攻击（2026-09-29 第二版）：头顶一道弧上三个光点，轮番蓄力、轰出一条月光束砸在男生身上（crew.js beamStep，画法 drawMoonBeams）。
     用户："连续召唤月光束来轰击男生，有点像超人的红眼光束。召唤的位置是头顶出现 3 个光点，分别召唤月光束"，节奏选"轮番蓄力点射"。
     第一版是掌心打一串月牙光刃 + 银蓝雾锥（照法海咒语的做法）—— 用户："太像水面了，跟白娘子的重复"。
     打中迸月光环、小月牙，蹦字（main.js RECIPE.change）。 */
const CHANGE_FX = {
  halo: { R: 96, lw: 6, rgb: [226, 236, 255], edge: [70, 90, 160] },                   // 头后一轮满月光环
  rays: { n: 12, R: [150, 400], w: 0.08, spin: -0.1, rgb: [190, 210, 255], a: 0.24 },  // 身后放射的月光
  glow: { R: 360, a: 0.3, rgb: [170, 196, 255], core: [245, 248, 255] },
  orb: { R: 60, rgb: [200, 220, 255] },                                                // 掌心月牙的光团
  /* 头顶的光点：半径 R（屏幕像素 × s）；蓄满时胀到 1 + grow 倍；芒长 flare × R；托底深靛描一圈（浅墙上银白会化掉，实体靠轮廓） */
  star: { R: 26, grow: 0.7, flare: 2.2, core: [255, 255, 255], rgb: [190, 205, 255], edge: [40, 50, 130] },
  /* 光束：芯宽 W（× s）；四层 [宽 × W, 颜色, 不透明度]（外晕 → 深靛托底 → 银蓝 → 白芯）；出手 rise、收尾 tail（占这一发的几成） */
  beam: { W: 30, layers: [[3.4, [150, 160, 255], 0.2], [1.4, [40, 50, 130], 0.55], [1.0, [196, 212, 255], 0.95], [0.42, [255, 255, 255], 1]],
          rise: 0.12, tail: 0.35, sparks: 7 },
};
/* 三个光点 + 正在轰的那一束。g：beamGeo（光点屏幕位置、光束终点、缩放）；T：CHANGE.T（进出场时刻，光点跟着亮起 / 熄掉）；
   what：'beam' 只画光束（在她身后）、'orbs' 只画光点（在她身前），见 Crew items */
function drawMoonBeams(ctx, b, g, T, what) {
  const F = CHANGE_FX, B = CHANGE.beam, S = b.beam, s = g.s, se = T.enter + b.spray;
  const out = b.t > se ? Math.max(0, 1 - (b.t - se) / T.exit) : 1;
  ctx.save();
  ctx.lineCap = 'round';
  /* 光束（在光点底下：光点盖住光束的根） */
  if (what === 'beam' && S && S.ph === 'fire' && g.end) {
    const O = g.orbs[S.k], E = g.end, f = S.pt / B.T.fire, M = F.beam;
    const env = f < M.rise ? f / M.rise : f > 1 - M.tail ? (1 - f) / M.tail : 1;
    const w = M.W * s * env * (1 + 0.08 * Math.sin(b.t * 70));
    for (const [k, c, a] of M.layers) {
      ctx.lineWidth = w * k; ctx.strokeStyle = rgbaOf(c, a);
      ctx.beginPath(); ctx.moveTo(O[0], O[1]); ctx.lineTo(E[0], E[1]); ctx.stroke();
    }
    /* 光束里往下冲的碎光 */
    const dx = E[0] - O[0], dy = E[1] - O[1], L = Math.hypot(dx, dy) || 1, nx = -dy / L, ny = dx / L;
    for (let i = 0; i < M.sparks; i++) {
      const u = (b.t * 2.6 + i / M.sparks) % 1, o = Math.sin(i * 7.3 + b.t * 9) * w * 0.9, r = (3 + (i % 3) * 1.5) * s;
      ctx.fillStyle = rgbaOf(F.star.core, 0.9 * env);
      ctx.beginPath(); ctx.arc(O[0] + dx * u + nx * o, O[1] + dy * u + ny * o, r, 0, 6.283); ctx.fill();
    }
    /* 落点一团白光 */
    const R = w * 2.4, rg = ctx.createRadialGradient(E[0], E[1], 0, E[0], E[1], R);
    rg.addColorStop(0, rgbaOf(F.star.core, 0.95 * env)); rg.addColorStop(0.4, rgbaOf(F.star.rgb, 0.6 * env)); rg.addColorStop(1, rgbaOf(F.star.rgb, 0));
    ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(E[0], E[1], R, 0, 6.283); ctx.fill();
  }
  /* 光点：依次亮起；轮到的那个蓄力时胀大、一圈光环往里收、四周的光往里吸，轰的时候最亮 */
  const St = F.star;
  if (what === 'orbs') g.orbs.forEach(([x, y], i) => {
    const vis = Math.max(0, Math.min(1, (b.t - B.appear[0] - i * B.appear[1]) / 0.2)) * out;
    if (vis <= 0) return;
    let c = 0;
    if (S && S.k === i) c = S.ph === 'charge' ? S.pt / B.T.charge : S.ph === 'fire' ? 1 : Math.max(0, 1 - S.pt / B.T.gap);
    const R = St.R * s * (1 + St.grow * c) * (1 + 0.06 * Math.sin(b.t * 5 + i * 2));
    const gl = ctx.createRadialGradient(x, y, 0, x, y, R * 2.8);
    gl.addColorStop(0, rgbaOf(St.core, 0.95 * vis)); gl.addColorStop(0.3, rgbaOf(St.rgb, 0.55 * vis)); gl.addColorStop(1, rgbaOf(St.rgb, 0));
    ctx.fillStyle = gl; ctx.beginPath(); ctx.arc(x, y, R * 2.8, 0, 6.283); ctx.fill();
    /* 十字芒：慢慢转，蓄力时拉长 */
    const fl = R * St.flare * (1 + c), a0 = b.t * 0.6 + i;
    ctx.lineWidth = 2.2 * s; ctx.strokeStyle = rgbaOf(St.core, 0.85 * vis);
    for (let k = 0; k < 2; k++) {
      const a = a0 + k * Math.PI / 2, cx = Math.cos(a) * fl, cy = Math.sin(a) * fl;
      ctx.beginPath(); ctx.moveTo(x - cx, y - cy); ctx.lineTo(x + cx, y + cy); ctx.stroke();
    }
    ctx.lineWidth = 2 * s; ctx.strokeStyle = rgbaOf(St.edge, 0.55 * vis);
    ctx.beginPath(); ctx.arc(x, y, R * 0.62, 0, 6.283); ctx.stroke();
    ctx.fillStyle = rgbaOf(St.core, vis); ctx.beginPath(); ctx.arc(x, y, R * 0.55, 0, 6.283); ctx.fill();
    if (S && S.k === i && S.ph === 'charge') {
      ctx.lineWidth = 3 * s; ctx.strokeStyle = rgbaOf(St.rgb, 0.8 * c * vis);
      ctx.beginPath(); ctx.arc(x, y, R * (3.2 - 2.2 * c), 0, 6.283); ctx.stroke();
    }
    if (S) for (const m of S.motes) {
      if (m.k !== i) continue;
      const u = m.t / m.life, d = B.mote.R * s * (1 - u);
      ctx.fillStyle = rgbaOf(St.core, (0.4 + 0.6 * u) * vis);
      ctx.beginPath(); ctx.arc(x + Math.cos(m.a) * d, y + Math.sin(m.a) * d, (2 + 2 * u) * s, 0, 6.283); ctx.fill();
    }
  });
  ctx.restore();
}
const CHANGE = {
  ...BAISU,
  whole: { pivot: [370, 409], k: 0.12 },
  spr: { src: 'assets/world/change%n_%k.webp', body: { src: 'up', pivot: [370, 409], k: 1 },
         foot: [280, 900], muzzle: [581, 355], head: [397, 88], chest: [451, 310], halo: [430, 175],   // v14/change/make.py 打印；foot 是裙摆最低点
         /* rest −0.9：同白娘子（她也悬在左上、朝右下对着男生）。光束不从掌心出，但身子照样按"掌心 → 落点"轻轻倾（whole.k） */
         rest: -0.9 },
  skins: [1],
  aura: (ctx, b, s, at, probe) => drawGodAura(CHANGE_FX, CHANGE.spr, ctx, b, s, at, probe),
  /* 光束是直线：瞄准按直线反解（G 0，V 用不上）；不喷东西 */
  fluid: { V: 1, G: 0 },
  /* orbs：三个光点在贴图上的位置（头顶一道弧：左后、正上、右前；弧心比发髻偏右一点，往男生那边）；appear：第一个几秒亮、之后每隔几秒亮一个（刹停前后依次亮起）；
     T：蓄力 / 轰 / 换下一个的间隔（秒），三个光点一轮 2.25 秒；drip：轰着的时候每几秒迸一次碎光（onSplash）；
     mote：蓄力时往光点里吸的光粒（每秒几颗、飞几秒、从多远吸进来） */
  beam: { orbs: [[290, 110], [470, 50], [650, 110]], appear: [0.55, 0.18], T: { charge: 0.4, fire: 0.3, gap: 0.05 }, drip: 0.06,
          mote: { rate: 45, life: 0.35, R: 70 },
          draw: (ctx, b, g, T, what) => drawMoonBeams(ctx, b, g, T, what) },
};
const Change = Crew(CHANGE);

/* ---- ⑨ 后羿（男生档 4，2026-09-29，跟嫦娥对立：日 vs 月）----
   · 立绘 v14/houyi2/make.py（第二版，持弓拉弦）：红金上古战甲、红披风，朝左下 45° 俯射 —— 左臂斜伸握金色长弓，右手拉到右脸颊。
     立绘里**没有弦、没有箭**：弦和搭在弦上的箭引擎现画（drawBow），拉弦的右前臂单独一层（spr.arm），沿箭的方向前后挪（BW.pose 的 hand）。
   · 攻击（2026-09-29 第二版，用户："连续射出箭矢飞向女生，从后羿手中的弓箭射出，所以立绘也需要相应的动作"；射箭选"匀速连射"，
     立绘选"立绘 + 引擎画弦和箭"）：每 bow.cycle 秒放一箭。一箭的过程（BW.pose，u = 离上一次放箭几秒）：
       0 放：弦从手指上弹回两梢之间的直线、抖几下（vib），箭飞出去；手往后一甩（recoil）再回来；
       0.09~0.13 手往前够弦（reach），0.11 起新箭在弦上燃起来（arrow 淡入）、弦被手指捏住；
       0.13~cycle 拉回满弓。不射的时候（飞进来的路上）停在满弓、箭搭着；飞走的时候弦是松的、没箭。
     箭：金杆、火焰箭头、红羽，身后拖一道金红火尾（drawArrows）；打中钉在身上 fluid.stick 秒，燃爆火星、蹦字（main.js RECIPE.houyi）。
     第一版是掌心打小太阳火球 + 火光雾锥（照法海咒语的做法），跟嫦娥的月牙光刃一起被换掉。
   · 规格照法海：从右上飞下来、在场 15 秒、打女生全身、在男女主身后，底下铺烈日火空（sea.js SunSky）。
     身子跟瞄准角的 0.6（whole.k，法海 / 嫦娥 0.12）：箭沿弓的指向出去，弓得真的对着女生 —— 只倾一成的话，画着的箭和飞出去的箭差十几度。 */
const HOUYI_FX = {
  halo: { R: 100, lw: 7, rgb: [255, 170, 40], edge: [150, 40, 10] },                   // 头后一轮日轮
  rays: { n: 16, R: [150, 440], w: 0.08, spin: 0.16, rgb: [255, 150, 40], a: 0.28 },   // 身后放射的日光
  glow: { R: 380, a: 0.32, rgb: [255, 150, 50], core: [255, 236, 190] },
  orb: { R: 34, rgb: [255, 160, 40] },                                                 // 箭台（握弓的拳头）上一团火光：放箭时胀一下
  string: { lw: 1.8, glow: 5, core: [255, 246, 214], rgb: [255, 190, 80] },            // 弦：芯线宽 + 外一层金光（× s）
  /* 箭（屏幕像素 × s）：飞着的杆长 L（搭在弦上的按满弓的长度画，见 drawBow）、杆宽 w、箭头长 / 宽、羽长；颜色：杆金、托底深褐、羽红、箭头的火；火尾 tail × L 长，三层（外橙红 → 金 → 白芯） */
  arrow: { L: 150, w: 3.2, head: [20, 12], fl: 18, shaft: [236, 186, 70], edge: [100, 40, 8], fletch: [220, 46, 20], fire: [255, 150, 40],
           tail: 1.4, trail: [[12, [255, 90, 20], 0.35], [7, [255, 200, 60], 0.5], [3, [255, 250, 225], 0.8]] },
};
/* 一支箭：箭头尖在 (x, y)、朝 (ux, uy)、全长 L（屏幕像素），不透明度 a；stuck：钉在身上，箭头那截埋进去（只画后半截） */
function drawArrow(ctx, x, y, ux, uy, s, L, a, stuck) {
  const A = HOUYI_FX.arrow, nx = -uy, ny = ux;
  const bx = x - ux * L, by = y - uy * L, hx = x - ux * A.head[0] * s, hy = y - uy * A.head[0] * s;
  const from = stuck ? 0.45 : 0;                  // 钉住：箭头和前一截在身子里
  const sx = x - ux * L * from, sy = y - uy * L * from;
  ctx.lineCap = 'round';
  ctx.lineWidth = (A.w + 2.4) * s; ctx.strokeStyle = rgbaOf(A.edge, 0.8 * a);
  ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(stuck ? sx : hx, stuck ? sy : hy); ctx.stroke();
  ctx.lineWidth = A.w * s; ctx.strokeStyle = rgbaOf(A.shaft, a);
  ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(stuck ? sx : hx, stuck ? sy : hy); ctx.stroke();
  /* 羽：尾巴上两片，往后张 */
  const f = A.fl * s;
  ctx.fillStyle = rgbaOf(A.fletch, a);
  for (const k of [1, -1]) {
    ctx.beginPath(); ctx.moveTo(bx + ux * f, by + uy * f); ctx.lineTo(bx + ux * f * 0.2 + nx * k * f * 0.45, by + uy * f * 0.2 + ny * k * f * 0.45);
    ctx.lineTo(bx - ux * f * 0.15 + nx * k * f * 0.45, by - uy * f * 0.15 + ny * k * f * 0.45); ctx.lineTo(bx, by); ctx.closePath(); ctx.fill();
  }
  if (stuck) return;
  /* 箭头：三角 + 一团火 */
  const hw = A.head[1] * s / 2;
  ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(hx + nx * hw, hy + ny * hw); ctx.lineTo(hx - nx * hw, hy - ny * hw); ctx.closePath();
  ctx.fillStyle = rgbaOf([255, 226, 130], a); ctx.fill();
  ctx.lineWidth = 1.5 * s; ctx.strokeStyle = rgbaOf(A.edge, 0.8 * a); ctx.stroke();
  const R = 18 * s, g = ctx.createRadialGradient(x, y, 0, x, y, R);
  g.addColorStop(0, rgbaOf([255, 250, 220], 0.9 * a)); g.addColorStop(0.4, rgbaOf(A.fire, 0.6 * a)); g.addColorStop(1, rgbaOf(A.fire, 0));
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, R, 0, 6.283); ctx.fill();
}
/* 飞着的箭（粒子）：先画火尾，再画箭；钉住的只画后半截、最后一段淡掉 */
function drawArrows(ctx, ps) {
  const A = HOUYI_FX.arrow, s = HOUYI_S;
  ctx.save();
  ctx.lineCap = 'round';
  for (const d of ps) {
    if (d.ex) continue;
    const sp = Math.hypot(d.vx, d.vy) || 1, ux = d.vx / sp, uy = d.vy / sp;
    if (d.stuck != null) { drawArrow(ctx, d.x, d.y, ux, uy, s, A.L * s, 1 - d.stuck / HOUYI.fluid.stick, true); continue; }
    const TL = A.L * A.tail * s * Math.min(1, d.t / 0.08);   // 刚离弦时火尾还没拖出来
    for (const [w, c, a] of A.trail) {
      ctx.lineWidth = w * s; ctx.strokeStyle = rgbaOf(c, a);
      ctx.beginPath(); ctx.moveTo(d.x - ux * A.head[0] * s, d.y - uy * A.head[0] * s); ctx.lineTo(d.x - ux * TL, d.y - uy * TL); ctx.stroke();
    }
    drawArrow(ctx, d.x, d.y, ux, uy, s, A.L * s, 1, false);
  }
  ctx.restore();
}
/* 粒子不带缩放：箭按后羿在屏幕上的缩放画（main.js G4STAND.houyi 第三项，悬停时就是它） */
const HOUYI_S = 0.96;
/* 此刻弓的样子（见上面"一箭的过程"）：hand 前臂沿 axis 挪几贴图像素（+ 往后），att 弦被手指捏住几成（0 = 弦是自由的），
   vib 弦中点横着抖多少（贴图像素），arrow 搭着的箭不透明度 */
function bowPose(b, T, se) {
  const W = HOUYI.bow, C = W.cycle;
  if (b.t > se) return { hand: 0, att: 0, vib: 0, arrow: 0 };
  const u = b.bw ?? C, e = (v) => v * v * (3 - 2 * v);
  let hand;
  if (u < 0.04) hand = W.recoil * u / 0.04;
  else if (u < 0.09) hand = W.recoil * (1 - (u - 0.04) / 0.05);
  else if (u < 0.13) hand = -W.reach * (u - 0.09) / 0.04;
  else hand = -W.reach * (1 - e(Math.min(1, (u - 0.13) / (C - 0.13))));
  return { hand, att: u < 0.11 ? 0 : Math.min(1, (u - 0.11) / 0.02), vib: W.vib * Math.exp(-u * 25) * Math.sin(u * 140),
           arrow: u < 0.11 ? 0 : Math.min(1, (u - 0.11) / 0.04) };
}
/* 弦：上梢 → 搭箭点 → 下梢；搭箭点捏在手指上时跟着手，放开时回到两梢连线上（跟箭的方向线的交点）再抖。搭着的箭从搭箭点指向箭台、箭头伸出箭台一截 */
function drawBow(ctx, b, s, at, q) {
  const sp = HOUYI.spr, F = HOUYI_FX, ax = sp.arm.axis;
  const T = at(sp.top), B = at(sp.bot), G = at(sp.muzzle), H0 = at(sp.nock);
  const H = [H0[0] + ax[0] * q.hand * s, H0[1] + ax[1] * q.hand * s];
  /* 两梢连线跟"箭台 → 手"这条线的交点 = 弦松开时的中点 */
  const d1 = [B[0] - T[0], B[1] - T[1]], d2 = [H0[0] - G[0], H0[1] - G[1]], den = d1[0] * d2[1] - d1[1] * d2[0];
  const k = ((G[0] - T[0]) * d2[1] - (G[1] - T[1]) * d2[0]) / den, R = [T[0] + d1[0] * k, T[1] + d1[1] * k];
  const L1 = Math.hypot(...d1), nx = -d1[1] / L1, ny = d1[0] / L1;
  const Rv = [R[0] + nx * q.vib * s, R[1] + ny * q.vib * s];
  const N = [Rv[0] + (H[0] - Rv[0]) * q.att, Rv[1] + (H[1] - Rv[1]) * q.att];
  ctx.save();
  ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  for (const [w, c, a] of [[F.string.glow, F.string.rgb, 0.35], [F.string.lw, F.string.core, 0.95]]) {
    ctx.lineWidth = w * s; ctx.strokeStyle = rgbaOf(c, a);
    ctx.beginPath(); ctx.moveTo(T[0], T[1]); ctx.lineTo(N[0], N[1]); ctx.lineTo(B[0], B[1]); ctx.stroke();
  }
  if (q.arrow > 0) {
    /* 箭尾在搭箭点，箭头伸出箭台 30 像素（× s）：满弓时箭长 ≈ 搭箭点到箭台 + 30，比飞出去的那支（arrow.L）长 —— 飞得快，看不出来 */
    const dx = G[0] - N[0], dy = G[1] - N[1], L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L, len = L + 30 * s;
    drawArrow(ctx, N[0] + ux * len, N[1] + uy * len, ux, uy, s, len, q.arrow, false);
  }
  ctx.restore();
}
const HOUYI = {
  ...FAHAI,
  whole: { pivot: [336, 478], k: 0.6 },
  spr: { src: 'assets/world/houyi%n_%k.webp', body: { src: 'up', pivot: [336, 478], k: 1 },
         /* 拉弦的右前臂：单独一层（v14/houyi2/make.py），沿 axis（箭台 → 搭箭点，= 往后拉的方向）前后挪 */
         arm: { src: 'arm', axis: [0.661, -0.751] },
         /* v14/houyi2/make.py 打印；foot 是右脚靴尖，muzzle 是箭台（握弓的拳头上沿），nock 满弓时捏弦的指尖，top / bot 弓两梢挂弦处 */
         foot: [531, 696], muzzle: [127, 538], nock: [290, 352], top: [60, 276], bot: [319, 787],
         head: [252, 258], chest: [328, 427], halo: [243, 310],
         rest: -0.849 },                         // 贴图里箭的指向（搭箭点 → 箭台）：朝左下 49°
  skins: [2],
  aura: (ctx, b, s, at, probe) => drawGodAura(HOUYI_FX, HOUYI.spr, ctx, b, s, at, probe),
  aim: { lo: -0.45, hi: 0.35, rate: 1.6, follow: 8, stiff: 40 },
  /* 箭：V 1300、带一点下坠（G 300），每 bow.cycle 秒一支（rate 只给放箭那一下补飞用，见 Crew update）；
     radius 近距命中（同法海）；stick 打中后钉住几秒；hitEvery 0.5：大约每隔一支一次整套命中反馈（impact：震屏、顿帧、冲击环），每支都有的是 drip */
  fluid: { V: 1300, G: 300, drag: 0, rate: 30, spread: 0.03, vJit: 0.03, life: 1.2, miss: 110, radius: 60, snap: 14, hitEvery: 0.5, stick: 0.15, floor: false,
           draw: (ctx, ps) => drawArrows(ctx, ps) },
  /* cycle：两箭间隔（每秒 3.6 支）；recoil / reach：放箭后手往后甩、往前够弦的距离（贴图像素）；vib：弦抖的幅度 */
  bow: { cycle: 0.28, recoil: 16, reach: 26, vib: 7, pose: (b, T, se) => bowPose(b, T, se), draw: (ctx, b, s, at, q) => drawBow(ctx, b, s, at, q) },
};
const Houyi = Crew(HOUYI);

/* ---- ⑨ 绿茶妹妹（男生档 4 第四人，2026-09-29）----
   用户："男生这边的召唤礼物增加一个，逻辑是从手机里跳出一个妹妹，疑似聊天列表的一个暧昧对象，然后抱怨说姐姐要查手机还脾气大啥的，
   碎碎念蛐蛐对面女生，话语攻击，绿茶角色"；四个设计方向里选了兔耳学妹："有兔耳朵的妹妹，很有绿茶的味道"，"做成男生灭迹恶魔挡的一个礼物"。
   · 立绘 v14/sister/make.py：奶白一字肩毛衣裙、白毛绒兔耳发箍、灰过膝袜、毛绒靴，左眼下美人痣；悬空侧身朝左，
     右手举粉色手机屏幕朝左，左手手背掩嘴偷偷嘀咕。粉白外发光烘在贴图里。
   · 出场：从男女主抢的那部手机里蹦出来（path.pop：脚底从手机起跳、一道弧线落到悬停点，人从 0.15 倍长到原大，手机那里迸一圈粉光 main.js RECIPE.sister.pop）。
   · 攻击「茶言茶语」：手机里往女生脸上飞一串聊天气泡，气泡里是她的碎碎念（SISTER_FX.chat.lines），气泡之间夹着粉色小爱心（drawChatter）；
     打中迸粉色爱心、蹦字（main.js RECIPE.sister）。规格同法海：在场 15 秒、whole.k 0.12、在男女主身后，底下铺绿茶白莲海（sea.js TeaTide）。 */
const SISTER_FX = {
  glow: { R: 330, a: 0.26, rgb: [255, 150, 200], core: [255, 236, 246] },    // 身后一团粉光
  screen: { R: 46, rgb: [255, 170, 215] },                                    // 手机屏幕亮着的光（说一句胀一下）
  /* 聊天气泡：出手时 size[0] → 飞 grow 秒后 size[1]（字号，像素 × 她的缩放以外的屏幕像素）；every：每几颗粒子画一个气泡（其余画小爱心）。
     白底粉边、深粉字、尾巴朝她（往来的方向），字从底图上跳出来靠白底 + 粉色描边，不靠发光 */
  chat: { size: [16, 30], grow: 0.25, every: 3, fill: [255, 255, 255], edge: [255, 110, 170], ink: [196, 30, 110], heart: [255, 120, 175],
          lines: ['姐姐好凶哦', '哥哥别怕~', '又查手机呀', '我好怕怕', '姐姐生气啦?', '人家只是妹妹', '哥哥手机好看', '别凶哥哥嘛',
                  '我走就是了~', '姐姐不累吗', '好可怕哦', '哥哥最好了'] },
};
function drawSisterAura(ctx, b, s, at, probe) {
  const F = SISTER_FX, k = Math.min(1, b.t / 0.4);
  ctx.save();
  if (!probe) {
    const G = F.glow, [cx, cy] = at(SISTER.spr.chest), g = ctx.createRadialGradient(cx, cy, 0, cx, cy, G.R * s);
    g.addColorStop(0, rgbaOf(G.core, G.a * k)); g.addColorStop(0.45, rgbaOf(G.rgb, G.a * 0.5 * k)); g.addColorStop(1, rgbaOf(G.rgb, 0));
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, G.R * s, 0, 6.283); ctx.fill();
  }
  const O = F.screen, [ox, oy] = at(SISTER.spr.muzzle), r = O.R * s * (1 + 0.3 * b.kick + 0.08 * Math.sin(b.t * 6));
  const og = ctx.createRadialGradient(ox, oy, 0, ox, oy, r);
  og.addColorStop(0, rgbaOf([255, 255, 255], 0.9 * k)); og.addColorStop(0.4, rgbaOf(O.rgb, 0.55 * k)); og.addColorStop(1, rgbaOf(O.rgb, 0));
  ctx.fillStyle = og; ctx.beginPath(); ctx.arc(ox, oy, r, 0, 6.283); ctx.fill();
  ctx.restore();
}
function heartPath(ctx, x, y, r) {          // 爱心：尖朝下，(x, y) 是中心，r 约等于半宽
  ctx.beginPath();
  ctx.moveTo(x, y + r * 0.9);
  ctx.bezierCurveTo(x - r * 1.3, y + r * 0.1, x - r * 0.7, y - r * 1.0, x, y - r * 0.35);
  ctx.bezierCurveTo(x + r * 0.7, y - r * 1.0, x + r * 1.3, y + r * 0.1, x, y + r * 0.9);
  ctx.closePath();
}
function drawChatter(ctx, ps) {
  const C = SISTER_FX.chat;
  ctx.save();
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  for (const d of ps) {
    if (d.ex) continue;
    const e = Math.min(1, d.t / C.grow), fade = Math.min(1, (SISTER.fluid.life - d.t) / 0.2);
    if (d.seq % C.every) {                  // 小爱心：往下飘、一闪一闪
      const r = (7 + 5 * d.j) * (0.5 + 0.5 * e);
      ctx.globalAlpha = Math.max(0, fade) * (0.6 + 0.4 * Math.sin(d.t * 12 + d.j * 9));
      heartPath(ctx, d.x, d.y, r); ctx.fillStyle = rgbaOf(C.heart, 1); ctx.fill();
      continue;
    }
    const sz = C.size[0] + (C.size[1] - C.size[0]) * e;
    const line = C.lines[((d.seq / C.every | 0) % C.lines.length + C.lines.length) % C.lines.length];
    ctx.font = `800 ${sz.toFixed(1)}px "PingFang SC","Noto Sans CJK SC","Microsoft YaHei",sans-serif`;
    const w = ctx.measureText(line).width + sz * 1.1, h = sz * 1.7, x = d.x - w / 2, y = d.y - h / 2, r = h / 2;
    const sp = Math.hypot(d.vx, d.vy) || 1, tx = -d.vx / sp;          // 尾巴朝她（往来的方向）那一侧
    ctx.globalAlpha = Math.max(0, fade);
    ctx.save(); ctx.translate(d.x, d.y); ctx.rotate(Math.sin(d.t * 4 + d.j * 6) * 0.08); ctx.translate(-d.x, -d.y);
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.arc(x + w - r, y + r, r, -Math.PI / 2, Math.PI / 2);
    ctx.lineTo(x + r, y + h); ctx.arc(x + r, y + r, r, Math.PI / 2, Math.PI * 1.5); ctx.closePath();
    const bx = d.x + tx * w * 0.32, by = y + h;                      // 尾巴：气泡下沿靠她那一侧
    ctx.moveTo(bx - sz * 0.35, by - 1); ctx.lineTo(bx + tx * sz * 0.5, by + sz * 0.55); ctx.lineTo(bx + sz * 0.35, by - 1);
    ctx.lineWidth = Math.max(2, sz * 0.16); ctx.strokeStyle = rgbaOf(C.edge, 1); ctx.stroke();
    ctx.fillStyle = rgbaOf(C.fill, 0.96); ctx.fill();
    ctx.fillStyle = rgbaOf(C.ink, 1); ctx.fillText(line, d.x, d.y + 1);
    heartPath(ctx, x + w - r * 0.35, y + r * 0.1, sz * 0.32); ctx.fillStyle = rgbaOf(C.heart, 1); ctx.fill();
    ctx.restore();
  }
  ctx.globalAlpha = 1;
  ctx.restore();
}
const SISTER = {
  ...FAHAI,
  whole: { pivot: [171, 449], k: 0.12 },
  spr: { src: 'assets/world/sister%n_%k.webp', body: { src: 'up', pivot: [171, 449], k: 1 },
         foot: [279, 984], muzzle: [73, 225], head: [148, 48], chest: [154, 319], face: [151, 205],   // v14/sister/make.py 打印；foot 是下面那只靴底
         /* 手机是竖着举在脸边的，不是枪管；气泡走 fluid.arc 不靠瞄准（crew.js elevation），rest 只定气泡刚出手时尾巴朝哪 */
         rest: 0.6 },
  aura: (ctx, b, s, at, probe) => drawSisterAura(ctx, b, s, at, probe),
  aim: { lo: -0.3, hi: 0.3, rate: 1.6, follow: 8, stiff: 40 },
  sweep: { a: [0.15, 0.08], w: [0.6, 1.5] },    // 打脸（同恶魔），扫得比打全身小
  /* 出场：从手机里蹦出来（crew.js hoverPose b.pop）：弧线拱起 h × 缩放、人从 0.15 倍长大；离场往右上飞走 */
  path: { pop: { h: 260, s0: 0.15 }, to: (s, x, y) => [x + 800 * s, y - 800 * s], rollOut: 0.15 },
  anim: { pulse: [1.1, 0.35], kick: [0, 0.03, 6], lean: 0.02, bob: [8, 1.5] },
  T: { enter: 0.9, spray: 13.6, exit: 0.5, fire: 0.3 },
  /* 气泡：往左上鼓出去一道弧、从女生外上方砸到脸上（crew.js arcStep；用户："让她嘴里的碎碎念有个弧度砸在女生身上，而不是直接掉下来"）。
     弧：控制点在落点外侧 out 170、手机上方 up 160（每颗 ×0.7~1.3 各不相同）；T 1.5 秒飞到（一句话看得清），ease 1.6 越飞越快。
     每秒 15 颗、每 3 颗一个气泡 = 每秒 5 句 */
  fluid: { V: 300, G: 0, arc: { T: 1.5, out: 170, up: 160, ease: 1.6 }, drag: 0, rate: 15, spread: 0, vJit: 0, life: 2.0, miss: 110, radius: 70, snap: 14, hitEvery: 0.3, floor: false,
           draw: (ctx, ps) => drawChatter(ctx, ps) },
};
const Sister = Crew(SISTER);
