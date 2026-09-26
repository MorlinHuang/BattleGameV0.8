/* buddy.js —— 灭迹党档 3「哥们」（2026-09-26 替换奶茶）
 *
 * 不是飞行物，是一个**角色**：男生的肌肉哥们从右边蹦进来，站到男生斜后方，
 * 端着水枪朝女生乱滋一阵，再蹦出去。画风跟两个主角同一套（预渲染立绘，
 * v14/buddy/src1.png 抠出来的），不走礼物那套 3D 转盘。
 *
 * 分层：人画在角色层、**男生底下**（斜后方 = 被男生挡住一部分）；水柱画在特效层，
 * 越过男生头顶飞向女生，不能被身体挡住。
 *
 * 水柱是一串水滴：每一滴出枪时挑好落在女生身上的哪一点（girlTarget(u)，u=0 脸 → 1 膝盖），
 * 按那一点反算抛物线初速，飞行中受重力，飞到那一点的横坐标就碎（每帧按同一个 u 重取，
 * 人动了跟着走）。**不碰外轮廓**：她伸出去的手臂和手机那一行轮廓在最前面，碰轮廓的话
 * 滋胸口的水全在手机上炸开，读成"滋手机"。相邻水滴连成线就是水柱 —— u 乱扫，水柱自己就甩成了弧。
 *
 * 数值不在这里：送礼的战力走 SHOP.push（main.js giveGift），这里只负责演出。
 * 命中反馈通过 onHit 回调交给 main.js 的 impact（染色、震屏、配方粒子）。
 */
'use strict';

const Buddy = (function () {
  /* 一次礼物的时间轴（秒）：蹦进来 → 滋 → 蹦出去。滋的途中再刷一次就把"滋"续上，
     不叠第二个人 —— 两个一模一样的肌肉男站一起读成复制粘贴。 */
  const T = { enter: 0.35, spray: 2.5, exit: 0.4 };
  /* 立绘：build 之外单独抠的（见 v14/buddy/）。foot 是两脚中点、muzzle 是枪口，都是贴图像素。
     depth：站在男生斜后方，远一点就小一点、脚底高一点（lift 像素），读得出前后。 */
  const SPR = { src: 'assets/world/buddy.webp', foot: [178, 488], muzzle: [2, 76], depth: 0.88, lift: 26 };
  const BEHIND = 120;          // 脚底中点在男生身体右沿再往右多少
  /* 水：每秒出 RATE 滴，出枪速度按距离给飞行时间（SPEED 像素/秒），重力 G。
     瞄点在女生身上从头到膝盖乱扫（sweep 两个不公约的正弦叠起来，读成"乱滋"不是来回刷）。
     扫得太快（4.1 / 9.7 rad/s 试过）相邻两滴落点差太远，水柱折成闪电；2.3 / 5.3 才是一条甩动的水。 */
  const RATE = 55, SPEED = 1150, G = 900, HIT_EVERY = 0.3;

  let img = null, st = null, o = {};
  const drops = [];

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

  function summon() {
    if (st && st.t < T.enter + st.spray) { st.spray = st.t - T.enter + T.spray; return; }
    st = { t: 0, spray: T.spray, emit: 0, hitCd: 0, first: true, ph: Math.random() * 6 };
  }

  const ease = (u) => 1 - Math.pow(1 - u, 3);

  /* 此刻人站在哪（脚底中点的屏幕坐标）和缩放 */
  function pose() {
    const s = SPR.depth, fx = o.boyRight() + BEHIND;
    const hw = (img ? img.width - SPR.foot[0] : 150) * s;
    const x1 = Math.min(fx, o.W - hw + 30);            // 右边最多出画 30 像素
    const y1 = o.ground() - SPR.lift;
    const t = st.t, sprayEnd = T.enter + st.spray;
    let x = x1, y = y1;
    if (t < T.enter) {                                  // 从右边画外蹦进来
      const u = t / T.enter;
      x = o.W + 260 + (x1 - o.W - 260) * ease(u); y = y1 - Math.sin(Math.PI * u) * 70;
    } else if (t > sprayEnd) {                          // 蹦回去
      const u = Math.min(1, (t - sprayEnd) / T.exit);
      x = x1 + (o.W + 300 - x1) * u * u; y = y1 - Math.sin(Math.PI * u) * 60;
    } else {                                            // 滋水时的后坐：一点点抖
      x += Math.sin(t * 47) * 1.5; y += Math.abs(Math.sin(t * 23)) * -2;
    }
    return [x, y, s];
  }

  function muzzle(p) {
    return [p[0] + (SPR.muzzle[0] - SPR.foot[0]) * p[2], p[1] + (SPR.muzzle[1] - SPR.foot[1]) * p[2]];
  }

  function update(dt) {
    for (let i = drops.length - 1; i >= 0; i--) {
      const d = drops[i];
      d.vy += G * dt; d.x += d.vx * dt; d.y += d.vy * dt; d.t += dt;
      const tg = o.girlTarget(d.u);
      if (tg && d.x <= tg[0]) {
        drops.splice(i, 1);
        o.onSplash(tg[0], d.y);
        if (st && st.hitCd <= 0) { o.onHit(tg[0], d.y, st.first); st.first = false; st.hitCd = HIT_EVERY; }
      } else if (d.t > 1.6 || d.x < -50) drops.splice(i, 1);
    }
    if (!st) return;
    st.t += dt; st.hitCd -= dt;
    const sprayEnd = T.enter + st.spray;
    if (st.t >= sprayEnd + T.exit) { st = null; return; }
    if (st.t < T.enter || st.t > sprayEnd) return;
    st.emit += dt * RATE;
    const p = pose(), m = muzzle(p);
    while (st.emit >= 1) {
      st.emit -= 1;
      const tt = st.t + st.ph;
      const u = Math.min(1, Math.max(0, 0.5 + 0.32 * Math.sin(tt * 2.3) + 0.2 * Math.sin(tt * 5.3 + 1.3)));
      const tg = o.girlTarget(u);
      if (!tg) continue;
      const [tx, ty] = tg, ft = Math.max(0.18, Math.hypot(tx - m[0], ty - m[1]) / SPEED);
      drops.push({ x: m[0], y: m[1], vx: (tx - m[0]) / ft, vy: (ty - m[1]) / ft - 0.5 * G * ft, t: 0, u,
                   seq: drops.length ? drops[drops.length - 1].seq + 1 : 0 });
    }
  }

  // 人：角色层，男生之前画（被男生挡住）
  function drawActor(ctx) {
    if (!st || !img) return;
    const [x, y, s] = pose();
    ctx.drawImage(img, x - SPR.foot[0] * s, y - SPR.foot[1] * s, img.width * s, img.height * s);
  }

  /* 水柱：相邻（出枪顺序相邻、离得不远）的水滴连成线。三遍：深蓝描边 → 浅蓝水身 → 白色高光，
     跟礼物"实体靠轮廓"是同一条规矩 —— 浅蓝在浅绿墙上不描边就化掉了。 */
  function drawWater(ctx) {
    if (!drops.length) return;
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (const [lw, col] of [[16, 'rgba(24,70,140,.75)'], [11, 'rgba(110,196,255,.95)'], [3.5, 'rgba(255,255,255,.9)']]) {
      ctx.lineWidth = lw; ctx.strokeStyle = col; ctx.beginPath();
      for (let i = 1; i < drops.length; i++) {
        const a = drops[i - 1], b = drops[i];
        if (b.seq !== a.seq + 1 || Math.hypot(b.x - a.x, b.y - a.y) > 60) continue;
        ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
      }
      ctx.stroke();
    }
  }

  const active = () => !!st;
  function reset() { st = null; drops.length = 0; }

  return { init, load, summon, update, drawActor, drawWater, active, reset };
})();
