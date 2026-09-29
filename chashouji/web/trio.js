/* trio.js —— 档 3 帮手三人组（2026-09-29，docs/帮手三人组.md）。
 *
 * 用户："一次礼物出三个不同的角色……形式上不要全部都是滑板或者滑轮车，现在出来都会挤在一个地方，不仅遮挡男女主，也互相遮挡，
 * 周围的空间要充分利用……还要给上方留出足够的空间大礼物出场不能挡住"；"攻击形式也不一定非要喷雾和水枪"。
 *
 * 一次送礼 = 三个槽位各出一人（Trio）：后排地面（crew.js 的滑板哥们 / 平衡车闺蜜，水枪 / 喷雾）+ 上方（扒墙 / 秋千）+ 前景地板（趴 / 半跪）。
 * 三个槽位在屏幕上不重叠：上方的在侧边、男女主头顶以下（HUD 和正上方留给档 4 与出场视频，档 4 画在它们之上），
 * 后排在主角身后，地板的在两个下角、主角脚以下的地板上（画在主角之前）。三个人错开 STAGGER 秒依次进场，一眼一个。
 *
 * 这里的每个人（Act）都是单张立绘（v14/trio/make.py 出图，贴图像素 = 屏幕像素 × s），不像 crew.js 那样切层转枪口：
 * 丢东西、出拳、发波、拍照都不需要持续瞄准，靠整个人绕 pivot 的一点前后倾（蓄力往后、出手往前一甩）读出动作，
 * 东西从手（hand）出去、按贝塞尔弧飞到打的那一点（每帧重取，人被拖着走也追得上）。
 * 打出去的东西、挂在人身上的记号（爱心、口红印、挂在头上的胸罩）、出拳的橡皮手臂、气功波都画在主角之上（drawOver），
 * 人本身按 depth 跟 crew.js 的帮手一起排远近（items）：上方的在主角身后，地板的在主角之前。
 */
'use strict';

const TRIO = {
  T: { enter: 0.75, stay: 3.2, exit: 0.55 },   // 进场 / 在场（续送每次加一份）/ 离场，秒
  STAGGER: [0, 0.3, 0.6],                       // 三个人依次进场的间隔（打乱分给三个槽位）
  lean: { wind: 0.09, snap: 0.06, decay: 9 },   // 蓄力往后倾、出手往前甩（rad），甩完衰减快慢
};

const easeOut = (u) => 1 - Math.pow(1 - u, 3);
const backOut = (u) => { const c = 2.2; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); };
const lerp = (a, b, k) => a + (b - a) * k;
const rnd = (a, b) => a + Math.random() * (b - a);

/* 一个人。cfg：
   face   +1 朝右（闺蜜，在左边）/ -1 朝左（哥们，在右边）
   src    贴图；at [x, y, s] 锚点落在屏幕哪、画多大；anchor 贴图上的锚点（扒墙的手脚、趴着的肚皮、秋千座板）
   pivot  前后倾绕的点（贴图像素，秋千是绳子顶端，在贴图外面）；hand 东西从哪出去
   depth  远近（< 1 主角身后，> 1 主角之前），main.js 按它跟别的帮手一起排
   enter  进场方式：crawl 爬 / spring 弹 / slide 扑地滑 / dash 斜冲 / roll 翻滚 / creep 匍匐 / swing 荡
   atk    攻击：{ kind: 'throw' | 'punch' | 'beam' | 'camera', ... }，见 update
   recipe 打中炸什么（main.js RECIPE 的键） */
function Act(cfg) {
  const F = cfg.face, A = cfg.atk;
  let img = null, prop = null, o = {}, b = null;
  const shots = [], marks = [];                 // 飞出去的东西、挂在人身上的记号

  function init(opt) { o = opt; }
  function load(v, off) {
    if (off) return Promise.resolve(false);
    const one = (src) => new Promise((ok) => {
      const i = new Image(); i.onload = () => ok(i); i.onerror = () => ok(null);
      i.src = src + (v ? '?v=' + encodeURIComponent(v) : '');
    });
    return Promise.all([one(cfg.src), A.prop ? one(A.prop) : null]).then(([a, p]) => { img = a; prop = p; return !!a; });
  }

  /* 来一个（wait 秒后才开始进场）；在场再送 = 续一份时间，下一下按礼物力度打 */
  function summon(_sk, wait = 0) {
    if (b && b.t <= TRIO.T.enter + b.stay) { b.stay += TRIO.T.stay; b.first = true; return; }
    /* 正在离场又被叫住：从现在退到的地方倒着走回来。离场退出去 out²，进场还差 (1 − u)³（easeOut），两者相等处接上 */
    if (b && b.wait <= 0) {
      const out = Math.min(1, (b.t - TRIO.T.enter - b.stay) / TRIO.T.exit);
      b.t = (1 - Math.pow(out, 2 / 3)) * TRIO.T.enter; b.stay = TRIO.T.stay; b.first = true; b.landed = false;
      return;
    }
    b = { t: 0, wait, stay: TRIO.T.stay, first: true, cd: rnd(0.15, 0.4), lean: 0, snap: 0, ph: Math.random() * 6,
          pk: null, bm: null, prevPh: 0, landed: false };
    return b;
  }
  const active = () => !!b;
  const busy = () => !!b || shots.length > 0 || marks.length > 0;
  function reset() { b = null; shots.length = 0; marks.length = 0; }

  /* 此刻的摆放：锚点在屏幕 (x, y)，画多大 s，整个人绕 rc（屏幕点）转 rot。 */
  function place() {
    const [ax, ay, s] = cfg.at, t = b.t, T = TRIO.T, se = T.enter + b.stay;
    const off = (img ? img.width : 300) * s + 30;       // 整个人挪出画外要多远
    let dx = 0, dy = 0, rot = 0, spin = 0;
    const u = Math.min(1, t / T.enter), out = t > se ? Math.min(1, (t - se) / T.exit) : 0;
    /* 进场 k：1 = 还在画外、0 = 到位；离场按 u² 退回画外（往来的方向回去） */
    const k = t < T.enter ? 1 - (cfg.enter === 'spring' ? backOut(u) : easeOut(u)) : out * out;
    const sd = F > 0 ? -1 : 1;                           // 画外在哪边：闺蜜在左、哥们在右
    switch (cfg.enter) {
      case 'crawl':   // 扒着屏幕边爬进来：一步一耸
        dx = sd * off * k; dy = Math.sin(u * Math.PI * 5) * 7 * (1 - u); rot = Math.sin(u * Math.PI * 5) * 0.05 * (1 - u); break;
      case 'spring':  // 橡皮人：一下弹进来、冲过头再弹回
        dx = sd * off * k; rot = -sd * 0.18 * k; break;
      case 'slide':   // 飞身扑地：从下角斜着滑进来，头略朝下
        dx = sd * off * k; dy = 110 * k; rot = sd * 0.12 * k; break;
      case 'dash':    // 斜着从下面冲上来
        dx = sd * off * 0.7 * k; dy = 300 * k; rot = sd * 0.2 * k; break;
      case 'roll':    // 翻滚进来：转一圈落成半跪
        dx = sd * off * k; dy = 220 * k; spin = -sd * 6.2832 * k; break;
      case 'creep':   // 匍匐爬进来：贴着地一耸一耸
        dx = sd * off * k; dy = -Math.abs(Math.sin(u * Math.PI * 6)) * 6 * (1 - u); break;
      case 'swing': { // 秋千从画外荡进来：摆角大、慢慢收到小幅来回，一直荡着；离场荡回画外
        const S = cfg.swing, A0 = S.a + (S.a0 - S.a) * Math.exp(-t / S.tau);
        rot = -sd * A0 * Math.cos(S.w * t) + (-sd) * 1.5 * out * out;
        break;
      }
    }
    if (t >= T.enter && t <= se) dy += Math.sin(t * 2.2 + b.ph) * 2 * s;   // 在场：呼吸
    rot += b.lean + b.snap;
    const at = (q) => [ax + dx + (q[0] - cfg.anchor[0]) * s, ay + dy + (q[1] - cfg.anchor[1]) * s];
    return { at, s, rot, spin, rc: at(cfg.pivot), sc: at([img ? img.width / 2 : 0, img ? img.height / 2 : 0]) };
  }
  /* 贴图上的点 q 此刻在屏幕哪（含整个人的倾角） */
  function pt(P, q) {
    let p = P.at(q);
    const rotAbout = (p, c, a) => { const co = Math.cos(a), si = Math.sin(a), x = p[0] - c[0], y = p[1] - c[1]; return [c[0] + x * co - y * si, c[1] + x * si + y * co]; };
    if (P.spin) p = rotAbout(p, P.sc, P.spin);
    if (P.rot) p = rotAbout(p, P.rc, P.rot);
    return p;
  }

  /* ---- 打的那一下 ---- */
  function hit(x, y, recipe) { o.onHit(x, y, b ? b.first : false, recipe || cfg.recipe); if (b) b.first = false; }

  /* 丢东西：从手出去，沿二次贝塞尔飞到落点（每帧重取），弧往上鼓 arc × 距离 */
  function launch(P) {
    const h = pt(P, cfg.hand);
    const miss = A.miss && Math.random() < A.miss;       // 玫瑰：一部分故意扔在她脚边，钉在地板上
    const u = rnd(0, 1);
    /* 扔偏的落在她脚前、两个人之间的地板上（她身后、脚下是前景地板那一个人的位置，插到人家头上了） */
    const tgt = miss ? (() => { const f = o.face(); return f ? [f[0] + rnd(40, 170), o.ground() - rnd(0, 14)] : null; })() : null;
    shots.push({ kind: A.kind === 'camera' ? 'photo' : A.item, x: h[0], y: h[1], p0: h, tgt, u, t: 0, T: A.T * rnd(0.9, 1.1),
                 arc: A.arc * rnd(0.8, 1.2), ang: 0, spin: (A.spin || 0) * (Math.random() < 0.5 ? 1 : -1), miss, j: Math.random() });
  }

  function update(dt) {
    for (let i = shots.length - 1; i >= 0; i--) if (!stepShot(shots[i], dt)) shots.splice(i, 1);
    for (let i = marks.length - 1; i >= 0; i--) if ((marks[i].t += dt) > marks[i].life) marks.splice(i, 1);
    if (!b) return;
    if (b.wait > 0) { b.wait -= dt; return; }
    b.t += dt;
    const T = TRIO.T, se = T.enter + b.stay;
    if (b.t >= se + T.exit) { b = null; return; }
    if (!b.landed && b.t >= T.enter) { b.landed = true; if (o.onLand) { const P = place(); o.onLand(...P.at(cfg.anchor), cfg.enter); } }
    b.snap *= Math.exp(-TRIO.lean.decay * dt);
    const on = b.t >= T.enter && b.t <= se;
    const L = TRIO.lean;
    if (A.kind === 'punch') { stepPunch(dt, on); return; }
    if (A.kind === 'beam') { stepBeam(dt, on); return; }
    /* 丢东西 / 拍照：秋千荡到最前面那一下出手（荡到高处抛）；其余按间隔，出手前 wind 秒往后蓄力 */
    if (!on) { b.lean *= Math.exp(-8 * dt); return; }
    if (cfg.enter === 'swing') {
      const S = cfg.swing, ph = (S.w * b.t) % 6.2832, prev = b.prevPh; b.prevPh = ph;
      const to = (Math.PI - ph + 6.2832) % 6.2832;                        // 离最前面（cos = −1）还差多少相位
      b.lean = to < 1.2 ? -F * L.wind * (1 - to / 1.2) : b.lean * Math.exp(-8 * dt);
      if (prev < Math.PI && ph >= Math.PI) fire();
      return;
    }
    b.cd -= dt;
    b.lean = b.cd < A.wind ? -F * L.wind * (1 - Math.max(0, b.cd) / A.wind) : b.lean * Math.exp(-8 * dt);
    if (b.cd <= 0) { fire(); b.cd = rnd(A.gap[0], A.gap[1]); }
  }
  function fire() {
    b.lean = 0; b.snap = F * TRIO.lean.snap;
    const P = place();
    if (A.kind === 'camera') { flash(P); return; }
    for (let k = 0; k < (A.n || 1); k++) launch(P);
  }

  /* 飞：t/T 走贝塞尔。落点：故意扔偏的是地板上那一点，其余是 o.aim(u)（打谁的哪里，main.js 给） */
  function stepShot(s, dt) {
    if (s.stuck != null) return (s.stuck += dt) < (A.stick || 2.2);        // 钉在地板上的玫瑰
    if (s.fall) {                                                         // 打中以后弹开 / 掉下去
      s.vy += 1800 * dt; s.x += s.vx * dt; s.y += s.vy * dt; s.ang += s.spin * dt; s.fall -= dt;
      return s.fall > 0;
    }
    if (s.kind === 'photo') {                                             // 相机吐出来的照片：往上一蹦、晃着落下
      s.vy += 700 * dt; s.x += s.vx * dt; s.y += s.vy * dt; s.ang += s.spin * dt; s.t += dt;
      return s.t < 1.6;
    }
    s.t += dt;
    const tg = s.tgt || o.aim(s.u);
    if (tg) s.p2 = [tg[0], tg[1]];
    if (!s.p2) return false;
    const e = Math.min(1, s.t / s.T), p0 = s.p0, p2 = s.p2, d = Math.hypot(p2[0] - p0[0], p2[1] - p0[1]);
    const p1 = [(p0[0] + p2[0]) / 2, Math.min(p0[1], p2[1]) - s.arc * d];
    const q = 1 - e, nx = q * q * p0[0] + 2 * q * e * p1[0] + e * e * p2[0], ny = q * q * p0[1] + 2 * q * e * p1[1] + e * e * p2[1];
    s.vx = (nx - s.x) / Math.max(dt, 1e-3); s.vy = (ny - s.y) / Math.max(dt, 1e-3);
    s.x = nx; s.y = ny; s.ang += s.spin * dt;
    if (e < 1) return true;
    if (s.miss) { s.stuck = 0; return true; }
    /* 到了：打中。后续看是什么东西 */
    hit(s.x, s.y);
    const f = o.face();
    if (A.onHit === 'heart' && f) marks.push({ kind: 'heart', t: 0, life: 1.3, dx: rnd(-0.3, 0.3), j: Math.random() });
    if (A.onHit === 'lips' && f) marks.push({ kind: 'lips', t: 0, life: 6, u: (s.x - f[0]) / f[2], v: (s.y - f[1]) / f[2], a: rnd(-0.5, 0.5) });
    if (A.onHit === 'wear' && f) { for (const m of marks) if (m.kind === 'wear') m.life = Math.min(m.life, m.t + 0.25); marks.push({ kind: 'wear', t: 0, life: 2.6, a: rnd(-0.3, 0.3) }); return false; }
    if (A.onHit === 'bounce' || A.onHit === 'heart') {                      // 弹开：往回、往上蹦，转着掉下去
      s.fall = 0.9; s.vx = -Math.sign(s.vx || -F) * rnd(160, 320); s.vy = -rnd(420, 620); s.spin = (A.spin || 6) * (s.vx > 0 ? 1 : -1);
      return true;
    }
    return false;
  }

  /* 出拳（草帽）：拳头顺着手臂方向"咻"地伸到她脑门、停一下、弹回来。手臂 = 腕 → 拳头之间画一截肉色的橡皮管。
     阶段 [伸, 停, 回] 秒；伸到那一刻打中 */
  function stepPunch(dt, on) {
    const P = A.phases;
    if (!b.pk) {
      if (!on) { b.lean *= Math.exp(-8 * dt); return; }
      b.cd -= dt;
      b.lean = b.cd < A.wind ? -F * TRIO.lean.wind * (1 - Math.max(0, b.cd) / A.wind) : b.lean * Math.exp(-8 * dt);
      if (b.cd <= 0) { b.pk = { t: 0, hit: false }; b.lean = 0; b.snap = F * TRIO.lean.snap; }
      return;
    }
    const k = b.pk; k.t += dt;
    if (!k.hit && k.t >= P[0]) {
      k.hit = true;
      const tg = o.aim(0);
      if (tg) { hit(tg[0], tg[1]); marks.push({ kind: 'stars', t: 0, life: 1.1, j: Math.random() }); }
    }
    if (k.t >= P[0] + P[1] + P[2]) { b.pk = null; b.cd = rnd(A.gap[0], A.gap[1]); }
  }
  /* 拳头伸出去多少（0 = 在手腕上、1 = 到落点）：伸 easeOut、回来带一点过冲（橡皮） */
  function punchK() {
    if (!b || !b.pk) return 0;
    const P = A.phases, t = b.pk.t;
    if (t < P[0]) return easeOut(t / P[0]);
    if (t < P[0] + P[1]) return 1;
    const u = Math.min(1, (t - P[0] - P[1]) / P[2]);
    return 1 - backOut(u);
  }

  /* 气功波（悟空）：手心聚一团水光（charge 秒，越聚越大）→ 一束水光轰过去（fire 秒，开轰那一下打中、之后每 drip 秒溅一下）→ 歇 rest 秒 */
  function stepBeam(dt, on) {
    if (!b.bm) { if (!on) return; b.bm = { ph: 'rest', t: rnd(0, 0.3), dr: 0, u: 0.5 }; }
    const S = b.bm, B = A.beam;
    S.t += dt;
    if (S.ph === 'rest') { if (on && S.t >= B.rest) { S.ph = 'charge'; S.t = 0; } return; }
    if (S.ph === 'charge') {
      b.lean = -F * TRIO.lean.wind * 0.6 * Math.min(1, S.t / B.charge);
      if (S.t >= B.charge) { S.ph = 'fire'; S.t = 0; S.u = rnd(0.1, 0.8); b.lean = 0; b.snap = F * TRIO.lean.snap; const tg = o.aim(S.u); if (tg) hit(tg[0], tg[1]); }
      return;
    }
    if ((S.dr += dt) >= B.drip) { S.dr -= B.drip; const tg = o.aim(S.u); if (tg && o.onSplash) o.onSplash(tg[0], tg[1]); }
    if (S.t >= B.fire) { S.ph = 'rest'; S.t = 0; if (!on) b.bm = null; }
  }

  /* 拍照（探险家）：镜头一闪、他脸上一闪（打中），相机里吐出一张照片往上蹦 */
  function flash(P) {
    const h = pt(P, cfg.hand), f = o.face();
    marks.push({ kind: 'flash', t: 0, life: 0.28, x: h[0], y: h[1] });
    if (f) { marks.push({ kind: 'blind', t: 0, life: 0.35 }); hit(f[0], f[1]); }
    shots.push({ kind: 'photo', x: h[0], y: h[1], vx: -F * rnd(60, 160), vy: -rnd(380, 520), ang: rnd(-0.3, 0.3), spin: rnd(-4, 4), t: 0 });
  }

  /* ---- 画 ---- */
  function drawBody(ctx) {
    if (!b || b.wait > 0 || !img) return;
    const P = place(), [x0, y0] = P.at([0, 0]);
    ctx.save();
    if (P.rot) { ctx.translate(P.rc[0], P.rc[1]); ctx.rotate(P.rot); ctx.translate(-P.rc[0], -P.rc[1]); }
    if (P.spin) { ctx.translate(P.sc[0], P.sc[1]); ctx.rotate(P.spin); ctx.translate(-P.sc[0], -P.sc[1]); }
    if (cfg.ropes) drawRopes(ctx, P);
    const pk = A.kind === 'punch' && punchK() > 0.001;
    if (pk) {                                               // 出拳时拳头那一块不画在原处（drawOver 画在伸出去的地方）
      const [fx0, fy0, fx1, fy1] = A.fist;
      ctx.save(); ctx.beginPath();
      ctx.rect(x0 - 1e4, y0 - 1e4, 3e4, 3e4);
      ctx.rect(x0 + fx1 * P.s, y0 + fy0 * P.s, (fx0 - fx1) * P.s, (fy1 - fy0) * P.s);   // 反向的矩形：挖掉
      ctx.clip('evenodd');
    }
    ctx.drawImage(img, x0, y0, img.width * P.s, img.height * P.s);
    if (pk) ctx.restore();
    ctx.restore();
  }
  /* 秋千绳：贴图里的绳子到贴图顶边为止，往上接到转轴那么高（画外），跟人一起摆 */
  function drawRopes(ctx, P) {
    const R = cfg.ropes;
    for (const x of R.x) {
      const [ax, ay] = P.at([x, R.y]), [, py] = P.at([x, cfg.pivot[1]]);
      ctx.lineCap = 'round';
      ctx.strokeStyle = R.edge; ctx.lineWidth = R.w * P.s + 3; ctx.beginPath(); ctx.moveTo(ax, ay + 2); ctx.lineTo(ax, py); ctx.stroke();
      ctx.strokeStyle = R.fill; ctx.lineWidth = R.w * P.s; ctx.beginPath(); ctx.moveTo(ax, ay + 2); ctx.lineTo(ax, py); ctx.stroke();
    }
  }

  function drawOver(ctx) {
    for (const s of shots) drawShot(ctx, s);
    const f = o.face();
    for (const m of marks) drawMark(ctx, m, f);
    if (!b || b.wait > 0 || !img) return;
    if (A.kind === 'punch' && punchK() > 0.001) drawArm(ctx);
    if (A.kind === 'beam' && b.bm && b.bm.ph !== 'rest') drawBeam(ctx);
  }

  function drawShot(ctx, s) {
    const a = s.stuck != null ? Math.min(1, ((A.stick || 2.2) - s.stuck) / 0.4) : s.fall != null ? Math.min(1, s.fall / 0.3) : 1;
    ctx.save(); ctx.globalAlpha = a; ctx.translate(s.x, s.y);
    if (s.kind === 'photo') { drawPhoto(ctx, s); ctx.restore(); return; }
    if (s.kind === 'heart') { ctx.rotate(s.ang * 0.1); drawHeart(ctx, 22 + 6 * Math.sin(s.t * 18), A.color); ctx.restore(); return; }
    if (s.kind === 'bball') { ctx.rotate(s.ang); drawBall(ctx, A.r); ctx.restore(); return; }
    if (!prop) { ctx.restore(); return; }
    let ang = s.ang;
    /* 玫瑰：花头朝前飞（贴图里花在左）；钉在地上时花朝上斜插 */
    if (s.kind === 'rose') ang = s.stuck != null ? -Math.PI / 2 + 0.5 * (s.j - 0.5) + Math.PI : Math.atan2(s.vy || 0, s.vx || -1) - Math.PI;
    ctx.rotate(ang);
    const w = prop.width * A.scale, h = prop.height * A.scale;
    const ox = s.kind === 'rose' ? -w * 0.12 : -w / 2;   // 玫瑰以花头为中心（钉住时花朝上、茎扎进地板）
    ctx.drawImage(prop, ox, -h / 2, w, h);
    ctx.restore();
  }

  /* 橡皮手臂：腕 → 拳头一截肉色管子，伸的时候往下垂一点、弹回时来回甩（二次曲线，控制点沿垂直方向偏 sag）；
     三遍画：深色描边 → 肉色 → 贴上沿一条亮光（只画一条直的肉色粗线读成木棍） */
  function drawArm(ctx) {
    const P = place(), k = punchK(), s = P.s;
    const wr = pt(P, A.wrist), fr = pt(P, A.fistC), tg = o.aim(0) || fr;
    const fx = lerp(fr[0], tg[0], k), fy = lerp(fr[1], tg[1], k);
    const len = Math.hypot(fx - wr[0], fy - wr[1]), nx = -(fy - wr[1]) / (len || 1), ny = (fx - wr[0]) / (len || 1);
    const wob = b.pk.t < A.phases[0] + A.phases[1] ? 0.08 : 0.16 * Math.sin(b.pk.t * 38);
    const sag = len * wob * (ny < 0 ? -1 : 1);                          // 往下垂（法线取朝下的那一边）
    const cx = (wr[0] + fx) / 2 + nx * sag, cy = (wr[1] + fy) / 2 + ny * sag;
    const ang = Math.atan2(fy - cy, fx - cx), rest = Math.atan2(fr[1] - wr[1], fr[0] - wr[0]);
    const tube = (w, c, dx = 0, dy = 0) => {
      ctx.strokeStyle = c; ctx.lineWidth = w; ctx.beginPath();
      ctx.moveTo(wr[0] + dx, wr[1] + dy); ctx.quadraticCurveTo(cx + dx, cy + dy, fx + dx, fy + dy); ctx.stroke();
    };
    const W = A.armW * s * (1 - 0.25 * Math.min(1, len / 500));       // 拉得越长越细
    ctx.save(); ctx.lineCap = 'round';
    tube(W + 5, A.skinEdge); tube(W, A.skin); tube(W * 0.45, A.skinShade, -nx * W * 0.22, -ny * W * 0.22);
    tube(W * 0.22, 'rgba(255,240,220,.85)', nx * W * 0.25, ny * W * 0.25);
    /* 拳头：从贴图里抠那一块，放大一点（远处也认得出是拳头），转到手臂末端的方向 */
    const [fx0, fy0, fx1, fy1] = A.fist, c = A.fistC, z = s * A.fistZ;
    ctx.translate(fx, fy); ctx.rotate(ang - rest + P.rot);
    ctx.drawImage(img, fx0, fy0, fx1 - fx0, fy1 - fy0, (fx0 - c[0]) * z, (fy0 - c[1]) * z, (fx1 - fx0) * z, (fy1 - fy0) * z);
    ctx.restore();
  }

  function drawBeam(ctx) {
    const P = place(), S = b.bm, B = A.beam, h = pt(P, cfg.hand);
    ctx.save(); ctx.globalCompositeOperation = 'source-over';
    if (S.ph === 'charge') {
      const r = B.ball * (0.3 + 0.7 * Math.min(1, S.t / B.charge)) * (1 + 0.08 * Math.sin(S.t * 40));
      orb(ctx, h[0], h[1], r, B);
    } else {
      const tg = o.aim(S.u);
      if (tg) {
        const e = Math.min(1, S.t / 0.08), fade = Math.min(1, (B.fire - S.t) / 0.15), x1 = lerp(h[0], tg[0], e), y1 = lerp(h[1], tg[1], e);
        ctx.globalAlpha = fade; ctx.lineCap = 'round';
        for (const [w, c, a] of B.layers) {
          ctx.strokeStyle = `rgba(${c[0]},${c[1]},${c[2]},${a})`; ctx.lineWidth = w * (1 + 0.1 * Math.sin(S.t * 50 + w));
          ctx.beginPath(); ctx.moveTo(h[0], h[1]); ctx.lineTo(x1, y1); ctx.stroke();
        }
        orb(ctx, h[0], h[1], B.ball, B); orb(ctx, x1, y1, B.ball * 1.2, B);
      }
    }
    ctx.restore();
  }
  function orb(ctx, x, y, r, B) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.35, `rgba(${B.glow[0]},${B.glow[1]},${B.glow[2]},0.95)`);
    g.addColorStop(0.75, `rgba(${B.edge[0]},${B.edge[1]},${B.edge[2]},0.6)`); g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill();
  }

  function drawMark(ctx, m, f) {
    const u = m.t / m.life;
    ctx.save();
    if (m.kind === 'flash') {                               // 镜头闪光：一颗四角星 + 一团白
      const r = 70 * (0.5 + u), a = 1 - u;
      ctx.globalAlpha = a; ctx.translate(m.x, m.y);
      const g = ctx.createRadialGradient(0, 0, 0, 0, 0, r); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.4, 'rgba(255,250,210,.8)'); g.addColorStop(1, 'rgba(255,240,180,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r, 0, 6.2832); ctx.fill();
      ctx.fillStyle = '#fff'; star4(ctx, r * 1.3, r * 0.12); ctx.restore(); return;
    }
    if (!f) { ctx.restore(); return; }
    if (m.kind === 'blind') {                               // 被闪到：脸上一团白光
      const r = f[2] * (1.6 + u), a = 0.85 * (1 - u);
      const g = ctx.createRadialGradient(f[0], f[1], 0, f[0], f[1], r); g.addColorStop(0, `rgba(255,255,255,${a})`); g.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(f[0], f[1], r, 0, 6.2832); ctx.fill();
    } else if (m.kind === 'heart') {                        // 头上冒爱心：蹦出来、往上飘、淡掉
      const pop = Math.min(1, m.t / 0.15), y = f[1] - f[2] * 1.9 - 40 * u, x = f[0] + m.dx * f[2] * 2;
      ctx.globalAlpha = 1 - Math.max(0, (u - 0.7) / 0.3);
      ctx.translate(x, y); drawHeart(ctx, 26 * (0.6 + 0.4 * pop) * (1 + 0.1 * Math.sin(m.t * 14)), [255, 60, 110]);
      ctx.translate(-34, 16); drawHeart(ctx, 14 * pop, [255, 110, 150]);
    } else if (m.kind === 'lips') {                         // 口红印：留在脸上，最后一秒淡掉
      ctx.globalAlpha = Math.min(1, (m.life - m.t) / 1);
      ctx.translate(f[0] + m.u * f[2], f[1] + m.v * f[2]); ctx.rotate(m.a); drawLips(ctx, f[2] * 0.42);
    } else if (m.kind === 'wear') {                         // 胸罩挂在他头上：套上去那一下晃，最后 0.3 秒淡掉
      ctx.globalAlpha = Math.min(1, (m.life - m.t) / 0.3);
      const w = Math.sin(m.t * 9) * 0.25 * Math.exp(-m.t * 2.5);
      ctx.translate(f[0], f[1] - f[2] * 0.95); ctx.rotate(m.a * 0.4 + w + F * 0.15);
      if (prop) { const W = f[2] * 3.0, H = W * prop.height / prop.width; ctx.drawImage(prop, -W / 2, -H * 0.55, W, H); }
    } else if (m.kind === 'stars') {                        // 被弹脑门：头上绕一圈小星星
      const n = 4, R = f[2] * 1.1;
      ctx.globalAlpha = 1 - Math.max(0, (u - 0.6) / 0.4);
      for (let i = 0; i < n; i++) {
        const a = m.t * 7 + i * 6.2832 / n + m.j * 6;
        ctx.save(); ctx.translate(f[0] + Math.cos(a) * R, f[1] - f[2] * 1.1 + Math.sin(a) * R * 0.35);
        ctx.fillStyle = '#ffd84a'; ctx.strokeStyle = 'rgba(120,70,0,.9)'; ctx.lineWidth = 2; star5(ctx, 11, 5); ctx.restore();
      }
    }
    ctx.restore();
  }

  function items() {
    if (!b || b.wait > 0 || !img) return [];
    return [{ s: cfg.depth, draw: drawBody }];
  }
  return { init, load, summon, update, items, drawOver, active, busy, reset, peek: () => (b ? [b] : []), cfg };
}

/* ---- 程序画的小东西 ---- */
function drawHeart(ctx, r, c) {
  ctx.beginPath();
  ctx.moveTo(0, r * 0.35);
  ctx.bezierCurveTo(r * 1.1, -r * 0.35, r * 0.55, -r * 1.1, 0, -r * 0.45);
  ctx.bezierCurveTo(-r * 0.55, -r * 1.1, -r * 1.1, -r * 0.35, 0, r * 0.35);
  ctx.closePath();
  ctx.fillStyle = `rgb(${c[0]},${c[1]},${c[2]})`; ctx.fill();
  ctx.lineWidth = Math.max(2, r * 0.12); ctx.strokeStyle = 'rgba(110,10,40,.9)'; ctx.stroke();
  ctx.beginPath(); ctx.ellipse(-r * 0.35, -r * 0.45, r * 0.16, r * 0.1, -0.6, 0, 6.2832); ctx.fillStyle = 'rgba(255,255,255,.8)'; ctx.fill();
}
function drawLips(ctx, r) {
  ctx.beginPath();
  ctx.moveTo(-r, 0);
  ctx.bezierCurveTo(-r * 0.6, -r * 0.55, -r * 0.2, -r * 0.5, 0, -r * 0.25);
  ctx.bezierCurveTo(r * 0.2, -r * 0.5, r * 0.6, -r * 0.55, r, 0);
  ctx.bezierCurveTo(r * 0.55, r * 0.6, -r * 0.55, r * 0.6, -r, 0);
  ctx.closePath();
  ctx.fillStyle = 'rgba(220,20,70,.88)'; ctx.fill();
  ctx.lineWidth = 1.5; ctx.strokeStyle = 'rgba(120,0,30,.8)'; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-r * 0.9, 0.02 * r); ctx.quadraticCurveTo(0, r * 0.12, r * 0.9, 0.02 * r); ctx.strokeStyle = 'rgba(120,0,30,.7)'; ctx.stroke();
}
function drawBall(ctx, r) {
  ctx.beginPath(); ctx.arc(0, 0, r, 0, 6.2832);
  const g = ctx.createRadialGradient(-r * 0.35, -r * 0.35, r * 0.1, 0, 0, r);
  g.addColorStop(0, '#ffb36b'); g.addColorStop(0.6, '#ec7a22'); g.addColorStop(1, '#b04c10');
  ctx.fillStyle = g; ctx.fill();
  ctx.lineWidth = 2.5; ctx.strokeStyle = '#2a1608'; ctx.stroke();
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(-r, 0); ctx.lineTo(r, 0); ctx.moveTo(0, -r); ctx.lineTo(0, r); ctx.stroke();
  ctx.beginPath(); ctx.arc(-r * 1.25, 0, r * 0.95, -0.9, 0.9); ctx.stroke();
  ctx.beginPath(); ctx.arc(r * 1.25, 0, r * 0.95, Math.PI - 0.9, Math.PI + 0.9); ctx.stroke();
}
function drawPhoto(ctx, s) {
  ctx.rotate(s.ang);
  ctx.fillStyle = '#fff'; ctx.strokeStyle = 'rgba(60,50,40,.9)'; ctx.lineWidth = 2;
  ctx.fillRect(-19, -23, 38, 46); ctx.strokeRect(-19, -23, 38, 46);
  const g = ctx.createLinearGradient(0, -18, 0, 12); g.addColorStop(0, '#6a86c8'); g.addColorStop(1, '#2c3558');
  ctx.fillStyle = g; ctx.fillRect(-15, -19, 30, 30);
  ctx.fillStyle = '#f2c9a0'; ctx.beginPath(); ctx.arc(-4, -2, 6, 0, 6.2832); ctx.arc(7, -1, 5, 0, 6.2832); ctx.fill();   // 两颗头：抓到了
  ctx.fillStyle = '#ff3b6b'; ctx.font = '900 11px system-ui'; ctx.textAlign = 'center'; ctx.fillText('实锤', 0, 20);
}
function star4(ctx, R, r) {
  ctx.beginPath();
  for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4, q = i % 2 ? r : R; ctx.lineTo(Math.cos(a) * q, Math.sin(a) * q); }
  ctx.closePath(); ctx.fill();
}
function star5(ctx, R, r) {
  ctx.beginPath();
  for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, q = i % 2 ? r : R; ctx.lineTo(Math.cos(a) * q, Math.sin(a) * q); }
  ctx.closePath(); ctx.fill(); ctx.stroke();
}

/* ---- 八个人 ---- 坐标：at 是 960×1334 版面上的屏幕像素（GROUND 1195 = 男女主脚底，1334 以下直播时被评论区盖着）；
   贴图点（anchor / pivot / hand / fist…）是 trio_<名>.webp 的像素（v14/trio/preview/<名>_grid.png 量的） */
const ROPE = { w: 7, y: 0, fill: '#c9a36a', edge: 'rgba(70,45,20,.85)' };

/* 哥们侧（右），打女生 */
const MaskMan = Act({       // 假面绅士：扒在右边屏幕壁上，甩玫瑰飞镖；打偏的钉在她脚边，打中她头上冒爱心（灭迹党靠分散注意力）
  face: -1, src: 'assets/world/trio_mask.webp', at: [958, 620, 1], anchor: [265, 175], pivot: [262, 175], hand: [30, 205],
  depth: 0.5, enter: 'crawl', recipe: 'petal',
  atk: { kind: 'throw', item: 'rose', prop: 'assets/world/trio_prop_rose.webp', scale: 0.55, T: 0.42, arc: 0.12, spin: 0,
         wind: 0.22, gap: [0.45, 0.7], miss: 0.35, stick: 2.2, onHit: 'heart' },
});
const StrawMan = Act({      // 草帽船长：扒在右边屏幕壁上，橡皮手臂伸长弹她脑门
  face: -1, src: 'assets/world/trio_straw.webp', at: [960, 620, 1], anchor: [300, 180], pivot: [298, 180], hand: [15, 70],
  depth: 0.5, enter: 'spring', recipe: 'star',
  atk: { kind: 'punch', fist: [0, 44, 36, 96], fistC: [16, 70], wrist: [36, 70], armW: 16, skin: '#f7cba0', skinShade: 'rgba(214,146,96,.5)', skinEdge: '#5a3420', fistZ: 1.35,
         phases: [0.16, 0.1, 0.34], wind: 0.3, gap: [0.55, 0.9] },
});
const Sakura = Act({        // 樱木：从右下角飞身扑地滑进来，趴着甩篮球，砸中弹开
  face: -1, src: 'assets/world/trio_sakura.webp', at: [812, 1330, 1.05], anchor: [235, 200], pivot: [110, 190], hand: [105, 22],
  depth: 1.3, enter: 'slide', recipe: 'thud',
  atk: { kind: 'throw', item: 'bball', r: 21, T: 0.5, arc: 0.3, spin: 10, wind: 0.25, gap: [0.6, 0.9], onHit: 'bounce' },
});
const Goku = Act({          // 悟空：从右下角斜冲上来半跪，推出水版龟派气功
  face: -1, src: 'assets/world/trio_goku.webp', at: [832, 1330, 1.05], anchor: [140, 297], pivot: [200, 285], hand: [8, 72],
  depth: 1.3, enter: 'dash', recipe: 'water',
  atk: { kind: 'beam', beam: { charge: 0.45, fire: 0.6, rest: 0.45, drip: 0.1, ball: 26, glow: [120, 210, 255], edge: [30, 90, 200],
         layers: [[34, [30, 90, 200], 0.35], [22, [90, 180, 255], 0.8], [11, [210, 240, 255], 0.95], [4, [255, 255, 255], 1]] } },
});

/* 闺蜜侧（左），打男生 */
const Gege = Act({          // 格格：秋千从左上画外荡进来，荡到最前面抛绣球砸他的头
  face: +1, src: 'assets/world/trio_gege.webp', at: [150, 370, 1], anchor: [82, 0], pivot: [82, -470], hand: [258, 105],
  depth: 0.5, enter: 'swing', recipe: 'bloom', ropes: { ...ROPE, x: [20, 143] },
  swing: { a0: 1.3, a: 0.13, tau: 0.45, w: 2.6 },
  atk: { kind: 'throw', item: 'ball', prop: 'assets/world/trio_prop_ball.webp', scale: 0.5, T: 0.5, arc: 0.25, spin: 5, onHit: 'bounce' },
});
const Fairy = Act({         // 紫衣仙子：秋千从左上画外荡进来，飞吻，爱心打到他脸上留下口红印（查岗证据）
  face: +1, src: 'assets/world/trio_fairy.webp', at: [165, 360, 1], anchor: [145, 0], pivot: [145, -480], hand: [238, 115],
  depth: 0.5, enter: 'swing', recipe: 'rouge', ropes: { ...ROPE, x: [100, 190], fill: '#a7864f' },
  swing: { a0: 1.3, a: 0.12, tau: 0.5, w: 2.4 },
  atk: { kind: 'throw', item: 'heart', n: 2, color: [255, 70, 130], T: 0.55, arc: 0.1, spin: 0, onHit: 'lips' },
});
const Ninja = Act({         // 忍者扇娘：从左下角翻滚进来半跪，胸罩当手里剑甩出去，打中挂在他头上
  face: +1, src: 'assets/world/trio_ninja.webp', at: [140, 1330, 1.05], anchor: [160, 288], pivot: [150, 280], hand: [305, 92],
  depth: 1.3, enter: 'roll', recipe: 'rouge',
  atk: { kind: 'throw', item: 'bra', prop: 'assets/world/trio_prop_bra.webp', scale: 0.55, T: 0.45, arc: 0.18, spin: 16,
         wind: 0.2, gap: [0.7, 1.0], onHit: 'wear' },
});
const Explorer = Act({      // 探险家：从左下角匍匐爬进来，举相机拍照取证，闪光晃他的眼，照片飞出来
  face: +1, src: 'assets/world/trio_explorer.webp', at: [150, 1345, 1.05], anchor: [215, 208], pivot: [330, 200], hand: [415, 48],
  depth: 1.3, enter: 'creep', recipe: 'star',
  atk: { kind: 'camera', wind: 0.18, gap: [0.75, 1.1] },
});

/* 三人组：slots = [[后排地面的 Crew], [上方的几个], [地板的几个]]。每次送礼每个槽位都要有人：
   这个槽位有人在场（含正在离场）→ 给他续一份；空着 → 随机抽一个进场。新进场的错开 STAGGER 依次来。
   （第一版"场上有人就只给在场的续"：后排的先走了，再送只剩两个人。）
   pick（诊断 ?buddy=1.0.1）：每个槽位指定第几个 */
function Trio(slots) {
  const all = slots.flat();
  return {
    slots, all,
    summon(pick) {
      const st = [...TRIO.STAGGER].sort(() => Math.random() - 0.5), ks = pick ? String(pick).split('.').map(Number) : [];
      let n = 0;
      slots.forEach((sl, i) => {
        const on = sl.find(m => m.active());
        if (on) { on.summon(); return; }
        const k = Number.isInteger(ks[i]) ? Math.max(0, Math.min(sl.length - 1, ks[i])) : Math.floor(Math.random() * sl.length);
        sl[k].summon(undefined, st[n++]);
      });
    },
    active: () => all.some(m => m.active()),
    reset() { all.forEach(m => m.reset()); },
  };
}
