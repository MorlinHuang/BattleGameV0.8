/* trio.js —— 档 3 帮手三人组的**引擎**（2026-09-29，docs/帮手三人组.md、docs/三人组角色规范.md）。
 *
 * 用户："一次礼物出三个不同的角色……形式上不要全部都是滑板或者滑轮车，现在出来都会挤在一个地方，不仅遮挡男女主，也互相遮挡，
 * 周围的空间要充分利用……还要给上方留出足够的空间大礼物出场不能挡住"；"攻击形式也不一定非要喷雾和水枪"。
 * 2026-09-29 夜扩到两边各 30 人、10 组固定搭配（docs/三人组30人名单.md），并要求"手臂身体该有的简单动作需要有……往帧动画方向做"。
 *
 * **角色数据不在这里**：每个人的 cfg 和 10 组搭配在 trio_buddy.js（哥们）/ trio_bestie.js（闺蜜），由美术照规范维护。这里只有引擎。
 *
 * 一次送礼 = 抽一组（Trio），组里三个槽位各一人：后排地面（crew.js 的滑板哥们 / 平衡车闺蜜，水枪 / 喷雾）+ 上方（扒墙 / 秋千）
 * + 前景地板（趴 / 半跪）。三个槽位在屏幕上不重叠：上方的在侧边、男女主头顶以下（HUD 和正上方留给档 4 与出场视频，档 4 画在它们
 * 之上），后排在主角身后，地板的在两个下角、主角脚以下的地板上（画在主角之前）。三个人错开 STAGGER 秒依次进场，一眼一个。
 *
 * 一个人（Act）有两种画法：
 *   · **帧序列（新标准，cfg.sheet）**：一张图集里若干个姿势帧（v14/trio/tools/frames.py 出，所有帧已按不动的部位配准、锚点同一个像素）。
 *     待机 = idle 帧 + 呼吸（绕锚点的竖向胀缩）+ 次级摆动（flex：头发 / 流苏 / 脚这类挂着的东西按条带错位，钉住的那一边不动）；
 *     出手 = atk.seq 一串帧（蓄力 → 出手那一帧东西离手 → 收势 → 回待机），帧之间硬切，切的那一下配整个人的前后倾 / 挤压；
 *     进场 = enter.seq 按时间换帧（扑地：腾空 → 砸地 → 滑行），秋千按摆的方向换"蹬腿 / 收腿"两帧（真人荡秋千就是这么蹬的）。
 *   · **单张立绘（旧，cfg.src）**：整张图绕 pivot 前后倾读出动作。紫衣仙子、假面、草帽、悟空、忍者、探险家还是这种，等按规范重做。
 * 东西从手（帧序列：atk.hold[出手帧]；单张：hand）出去、按贝塞尔弧飞到打的那一点（每帧重取，人被拖着走也追得上）。
 * 打出去的东西、挂在人身上的记号（爱心、口红印、挂在头上的胸罩）、出拳的橡皮手臂、气功波都画在主角之上（drawOver），
 * 人本身按 depth 跟 crew.js 的帮手一起排远近（items）：上方的在主角身后，地板的在主角之前。
 */
'use strict';

const TRIO = {
  T: { enter: 0.75, stay: 3.2, exit: 0.55 },   // 进场 / 在场（续送每次加一份）/ 离场，秒
  STAGGER: [0, 0.3, 0.6],                       // 三个人依次进场的间隔（打乱分给三个槽位）
  lean: { wind: 0.09, snap: 0.06, decay: 9 },   // 蓄力往后倾、出手往前甩（rad），甩完衰减快慢（帧序列的人再乘 cfg.leanK）
  sq: { decay: 12 },                            // 挤压（落地 / 出手那一下压扁）回弹快慢，1-exp(-k·dt)
  pop: 0.16,                                    // 出完手、手里重新冒出一个（篮球 / 绣球）用多少秒长到原大
  still: false,                                 // 诊断：在场时秋千不摆、整体不前后倾（胶片 ?trioswing=0，只剩换帧本身，量漂移用；出手时机照样按相位）
};

const easeOut = (u) => 1 - Math.pow(1 - u, 3);
const backOut = (u) => { const c = 2.2; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); };
const lerp = (a, b, k) => a + (b - a) * k;
const rnd = (a, b) => a + Math.random() * (b - a);

/* 一个人。cfg（逐字段说明见 docs/三人组角色规范.md 第六节）：
   face   +1 朝右（闺蜜，在左边）/ -1 朝左（哥们，在右边）
   sheet  帧序列图集 { src, cell: [w, h], cols, names }（frames.py 打印）；没有 sheet 就是旧的单张立绘 src
   at [x, y, s] 锚点落在屏幕哪、画多大；anchor 贴图上的锚点（帧序列：所有帧共用；扒墙的手脚、趴着的肚皮、秋千座板中心）
   pivot  前后倾 / 秋千摆绕的点（贴图像素，秋千是绳子顶端，在贴图外面）；leanK 前后倾打几折（帧序列里动作已经画在帧上，默认 1）
   depth  远近（< 1 主角身后，> 1 主角之前），main.js 按它跟别的帮手一起排
   enter  进场方式：crawl 爬 / spring 弹 / slide 扑地滑 / dive 腾空扑地再滑 / dash 斜冲 / roll 翻滚 / creep 匍匐 / swing 荡
          帧序列：enter { kind, seq: [[帧, 秒, 'land'?], ...], h: 腾空多高, air: 腾空几秒 }；exit { frame }
   idle   帧序列：{ frame: 待机帧, breathe: [胀缩幅度, 每秒几次, 横向补偿 (默认 0.4)] }；flex { 帧: [[x0, y0, x1, y1, 't'|'l', 幅度, 每秒几次, 跟摆], ...] }
   atk    攻击：{ kind: 'throw' | 'punch' | 'beam' | 'camera', ... }，见 update。帧序列的 throw：seq [[帧, 秒, 'fire'?], ...]、
          hold { 帧: [x, y] } 东西拿在哪（出手帧那一格就是出手点）、atlas 3D 转盘图集 { src, n, cols, cell, scale }（没有就用 prop 平面图）。
          帧序列支持 throw / camera / beam（蓄力帧手心聚光、出手帧开轰 beam.fire 秒，出手帧的时长要 ≥ beam.fire）；punch（伸缩手臂）只有单张立绘
   parts  帧序列：挂件层（扇子、靠旗、翎子这类单独拆出来随动作甩的东西）[{ src, pivot: [x, y] 挂件图上挂住的点, z: -1 画在人后 / 1 人前,
          at: { 帧: [x, y, 角度] } 这一帧挂在哪（格内像素）、没写的帧不画, sway: [幅度 rad, 每秒几次, 跟摆] }]（v14/trio/tools/part.py 出图）
   recipe 打中炸什么（main.js RECIPE 的键） */
function Act(cfg) {
  const F = cfg.face, A = cfg.atk, SH = cfg.sheet || null;
  const LK = cfg.leanK != null ? cfg.leanK : 1;
  const EK = typeof cfg.enter === 'string' ? cfg.enter : cfg.enter.kind;   // 进场方式（帧序列的 enter 是 { kind, seq, ... }）
  let img = null, prop = null, atlas = null, o = {}, b = null;
  const PARTS = (SH && cfg.parts) || [], partImg = [];
  const shots = [], marks = [];                 // 飞出去的东西、挂在人身上的记号
  /* 帧序列的出手：seq 里第几帧是出手帧、之前一共蓄力几秒、整段几秒 */
  const FI = SH && A.seq ? A.seq.findIndex(q => q[2] === 'fire') : -1;
  const LEAD = FI > 0 ? A.seq.slice(0, FI).reduce((a, q) => a + q[1], 0) : 0;
  const CLIP = SH && A.seq ? A.seq.reduce((a, q) => a + q[1], 0) : 0;
  /* 东西从哪出去：帧序列 = 出手帧那一格的 hold 点；单张立绘 = hand */
  const handPt = (P) => pt(P, SH ? A.hold[A.seq[FI][0]] : cfg.hand);
  const texW = () => (SH ? SH.cell[0] : img ? img.width : 300), texH = () => (SH ? SH.cell[1] : img ? img.height : 300);

  function init(opt) { o = opt; }
  function load(v, off) {
    if (off) return Promise.resolve(false);
    const one = (src) => new Promise((ok) => {
      const i = new Image(); i.onload = () => ok(i); i.onerror = () => ok(null);
      i.src = src + (v ? '?v=' + encodeURIComponent(v) : '');
    });
    return Promise.all([one(SH ? SH.src : cfg.src), A.prop ? one(A.prop) : null, A.atlas ? one(A.atlas.src) : null, ...PARTS.map(q => one(q.src))])
      .then(([a, p, t, ...ps]) => { img = a; prop = p; atlas = t; ps.forEach((im, i) => { partImg[i] = im; }); return !!a; });
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
          pk: null, bm: null, prevPh: 0, landed: false,
          clip: null, ammo: true, pop: 1, hang: Math.random() * 6, sq: 0, fn: null, tf: null };   // 帧序列：出手动作、手里有没有东西、挤压、当前帧
    return b;
  }
  const active = () => !!b;
  const busy = () => !!b || shots.length > 0 || marks.length > 0;
  function reset() { b = null; shots.length = 0; marks.length = 0; }

  /* 此刻的摆放：锚点在屏幕 (x, y)，画多大 s，整个人绕 rc（屏幕点）转 rot。 */
  function place() {
    const [ax, ay, s] = cfg.at, t = b.t, T = TRIO.T, se = T.enter + b.stay;
    const off = texW() * s + 30;                         // 整个人挪出画外要多远
    let dx = 0, dy = 0, rot = 0, spin = 0, w = 0;
    const u = Math.min(1, t / T.enter), out = t > se ? Math.min(1, (t - se) / T.exit) : 0;
    /* 进场 k：1 = 还在画外、0 = 到位；离场按 u² 退回画外（往来的方向回去） */
    const k = t < T.enter ? 1 - (EK === 'spring' ? backOut(u) : easeOut(u)) : out * out;
    const sd = F > 0 ? -1 : 1;                           // 画外在哪边：闺蜜在左、哥们在右
    switch (EK) {
      case 'crawl':   // 扒着屏幕边爬进来：一步一耸
        dx = sd * off * k; dy = Math.sin(u * Math.PI * 5) * 7 * (1 - u); rot = Math.sin(u * Math.PI * 5) * 0.05 * (1 - u); break;
      case 'spring':  // 橡皮人：一下弹进来、冲过头再弹回
        dx = sd * off * k; rot = -sd * 0.18 * k; break;
      case 'slide':   // 飞身扑地：从下角斜着滑进来，头略朝下
        dx = sd * off * k; dy = 110 * k; rot = sd * 0.12 * k; break;
      case 'dive': {  // 腾空扑地（帧序列）：前 air 秒在空中（抛物线落到地板、头略朝下），之后贴着地滑到位；离场贴地倒滑出去
        const E = cfg.enter, q = Math.min(1, t / E.air);
        dx = sd * off * k;
        if (t < E.air) { dy = -E.h * (1 - q * q); rot = sd * 0.08 * (1 - q); }
        break;
      }
      case 'dash':    // 斜着从下面冲上来
        dx = sd * off * 0.7 * k; dy = 300 * k; rot = sd * 0.2 * k; break;
      case 'roll':    // 翻滚进来：转一圈落成半跪
        dx = sd * off * k; dy = 220 * k; spin = -sd * 6.2832 * k; break;
      case 'creep':   // 匍匐爬进来：贴着地一耸一耸
        dx = sd * off * k; dy = -Math.abs(Math.sin(u * Math.PI * 6)) * 6 * (1 - u); break;
      case 'swing': { // 秋千从画外荡进来：摆角大、慢慢收到小幅来回，一直荡着；离场荡回画外
        const S = cfg.swing, A0 = TRIO.still && t >= T.enter ? 0 : S.a + (S.a0 - S.a) * Math.exp(-t / S.tau);
        rot = -sd * A0 * Math.cos(S.w * t) + (-sd) * 1.5 * out * out;
        w = sd * A0 * S.w * Math.sin(S.w * t);            // 摆的角速度（流苏跟摆、蹬腿换帧用）
        break;
      }
    }
    /* 在场：单张立绘整个人上下浮 2px 当呼吸。帧序列的人不浮 —— 呼吸是绕锚点的胀缩（drawBody），锚点（贴地的肚皮、压着座板的屁股）不能动 */
    if (!SH && t >= T.enter && t <= se) dy += Math.sin(t * 2.2 + b.ph) * 2 * s;
    if (!TRIO.still) rot += b.lean + b.snap;
    const at = (q) => [ax + dx + (q[0] - cfg.anchor[0]) * s, ay + dy + (q[1] - cfg.anchor[1]) * s];
    return { at, s, rot, spin, w, rc: at(cfg.pivot), sc: at([texW() / 2, texH() / 2]) };
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
    const h = handPt(P);
    const miss = A.miss && Math.random() < A.miss;       // 玫瑰：一部分故意扔在她脚边，钉在地板上
    const u = rnd(0, 1);
    /* 扔偏的落在她脚前、两个人之间的地板上（她身后、脚下是前景地板那一个人的位置，插到人家头上了） */
    const tgt = miss ? (() => { const f = o.face(); return f ? [f[0] + rnd(40, 170), o.ground() - rnd(0, 14)] : null; })() : null;
    shots.push({ kind: A.kind === 'camera' ? 'photo' : A.item, x: h[0], y: h[1], p0: h, tgt, u, t: 0, T: A.T * rnd(0.9, 1.1),
                 arc: A.arc * rnd(0.8, 1.2), ang: b ? b.hang : 0, spin: (A.spin || 0) * (A.atlas || Math.random() < 0.5 ? 1 : -1), miss, j: Math.random() });
  }

  function update(dt) {
    for (let i = shots.length - 1; i >= 0; i--) if (!stepShot(shots[i], dt)) shots.splice(i, 1);
    for (let i = marks.length - 1; i >= 0; i--) if ((marks[i].t += dt) > marks[i].life) marks.splice(i, 1);
    if (!b) return;
    if (b.wait > 0) { b.wait -= dt; return; }
    b.t += dt;
    const T = TRIO.T, se = T.enter + b.stay;
    if (b.t >= se + T.exit) { b = null; return; }
    if (!b.landed && b.t >= T.enter) { b.landed = true; if (o.onLand) { const P = place(); o.onLand(...P.at(cfg.anchor), EK); } }
    b.snap *= Math.exp(-TRIO.lean.decay * dt);
    const on = b.t >= T.enter && b.t <= se;
    const L = TRIO.lean;
    if (SH) { stepFrames(dt, on); return; }
    if (A.kind === 'punch') { stepPunch(dt, on); return; }
    if (A.kind === 'beam') { stepBeam(dt, on); return; }
    /* 丢东西 / 拍照：秋千荡到最前面那一下出手（荡到高处抛）；其余按间隔，出手前 wind 秒往后蓄力 */
    if (!on) { b.lean *= Math.exp(-8 * dt); return; }
    if (EK === 'swing') {
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
  /* ---- 帧序列 ---- */
  /* seq = [[帧, 秒, 事件?], ...]：t 秒时是第几段（过了最后一段停在最后一帧） */
  function seqAt(seq, t) {
    let a = 0;
    for (let i = 0; i < seq.length; i++) { a += seq[i][1]; if (t < a) return i; }
    return seq.length - 1;
  }
  /* 此刻画哪一帧：出手动作 > 进场序列 > 离场帧 > 秋千蹬腿 > 待机 */
  function frameName() {
    const t = b.t, T = TRIO.T, se = T.enter + b.stay;
    if (b.clip) return A.seq[seqAt(A.seq, b.clip.t)][0];
    if (t < T.enter && cfg.enter.seq) return cfg.enter.seq[seqAt(cfg.enter.seq, t)][0];
    if (t > se && cfg.exit) return cfg.exit.frame;
    if (cfg.swing && cfg.swing.pump) {
      /* 荡秋千：往前荡时伸腿（kick）、往后荡时收腿（tuck）—— 换帧正好落在摆到两头、人一瞬间停住的时候，硬切看不出跳。
         荡得小了（< min rad）就不蹬了，坐着待机 */
      const S = cfg.swing, P = S.pump, A0 = S.a + (S.a0 - S.a) * Math.exp(-t / S.tau);
      /* place：rot = F·A0·cos(wt)（sd = −F），往前荡 ⇔ −F·dθ/dt = A0·w·sin(wt) > 0 */
      if ((A0 >= P.min && !(TRIO.still && t >= T.enter)) || t > se) return Math.sin(S.w * t) > 0 ? P.fwd : P.back;
    }
    return cfg.idle.frame;
  }
  function stepFrames(dt, on) {
    const L = TRIO.lean, fn = frameName();
    if (fn !== b.fn) {                                          // 换帧那一下：落地压扁
      const q = !b.clip && b.t < TRIO.T.enter && cfg.enter.seq ? cfg.enter.seq[seqAt(cfg.enter.seq, b.t)] : null;
      if (q && q[2] === 'land') b.sq = cfg.enter.sq || 0.1;
      b.fn = fn;
    }
    b.sq *= Math.exp(-TRIO.sq.decay * dt);
    b.hang += (A.idleSpin || 0) * dt;                           // 拿在手里的球慢慢转（手指拨着玩）
    if (b.pop < 1) b.pop = Math.min(1, b.pop + dt / TRIO.pop);
    if (!A.seq) return;
    if (!b.clip) {
      b.lean *= Math.exp(-8 * dt);
      if (!on) return;
      if (cfg.swing) {
        /* 秋千：算好提前量，让"出手"那一帧正好落在荡到最前面（cos = −1）那一刻 */
        const S = cfg.swing, ph = (S.w * b.t) % 6.2832, tf = ((Math.PI - ph + 6.2832) % 6.2832) / S.w, prev = b.tf;
        b.tf = tf;
        if (prev != null && prev >= LEAD && tf < LEAD) {
          b.clip = { t: LEAD - tf, fired: false };
          if (A.kind === 'beam') b.bm = { ph: 'charge', t: b.clip.t, dr: 0, u: rnd(0.1, 0.8) };
        }
        return;
      }
      b.cd -= dt;
      if (b.cd <= 0) b.clip = { t: 0, fired: false };
      if (b.clip && A.kind === 'beam') b.bm = { ph: 'charge', t: 0, dr: 0, u: rnd(0.1, 0.8) };   // 发波：蓄力那几帧手心聚光
      return;
    }
    const C = b.clip; C.t += dt;
    if (b.bm) {                                                  // 发波：出手帧开轰（fire()），之后每 drip 秒溅一下，轰满 beam.fire 秒收
      const S = b.bm; S.t += dt;
      if (S.ph === 'fire') {
        if ((S.dr += dt) >= A.beam.drip) { S.dr -= A.beam.drip; const tg = o.aim(S.u); if (tg && o.onSplash) o.onSplash(tg[0], tg[1]); }
        if (S.t >= A.beam.fire) S.ph = 'rest';
      }
    }
    const i = seqAt(A.seq, C.t);
    /* 蓄力那几帧整个人再往后倾一点（帧上画的动作 + 一点整体惯性），出手那一下往前甩 */
    if (i < FI) b.lean = -F * L.wind * LK * Math.min(1, C.t / LEAD);
    if (!C.fired && i >= FI) { C.fired = true; b.lean = 0; b.snap = F * L.snap * LK; b.sq = -(A.stretch || 0.05); fire(); b.ammo = false; }
    if (C.t >= CLIP) { b.clip = null; b.bm = null; b.cd = rnd(A.gap ? A.gap[0] : 0.5, A.gap ? A.gap[1] : 0.8); b.ammo = true; b.pop = 0; }
  }

  function fire() {
    b.lean = 0; b.snap = F * TRIO.lean.snap * LK;
    const P = place();
    if (A.kind === 'camera') { flash(P); return; }
    if (A.kind === 'beam') {                                     // 帧序列的发波（单张立绘的走 stepBeam，不经过这里）
      b.bm.ph = 'fire'; b.bm.t = 0; b.bm.dr = 0;
      const tg = o.aim(b.bm.u); if (tg) hit(tg[0], tg[1]);
      return;
    }
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
    const h = handPt(P), f = o.face();
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
    if (SH) {
      const fn = frameName();
      if (cfg.ropes) drawSwing(ctx, P, fn);
      /* 呼吸 + 挤压：绕锚点竖向胀缩（横向反着补 breathe[2] 份，默认 0.4，体积不变；趴着的人给 0 —— 不然贴地的脚跟着左右挪）。
         只在待着的时候呼吸，进场离场不呼吸 */
      const [ax, ay] = P.at(cfg.anchor), br = cfg.idle.breathe, T = TRIO.T;
      let k = b.sq;
      if (br && b.t >= T.enter && b.t <= T.enter + b.stay) k -= br[0] * Math.sin(b.t * 6.2832 * br[1] + b.ph);
      ctx.translate(ax, ay); ctx.scale(1 + k * (br && br[2] != null ? br[2] : 0.4), 1 - k); ctx.translate(-ax, -ay);
      drawParts(ctx, P, fn, -1);
      drawFrame(ctx, P, fn);
      drawParts(ctx, P, fn, 1);
      if (b.ammo && A.hold && A.hold[fn]) drawHeld(ctx, P, fn);
      ctx.restore();
      return;
    }
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
  /* 画图集里的一帧。flex 区域不在原处画，按条带错位重画：钉住的那一边（'t' 顶 / 'l' 左）位移为 0、越往外越大（r^1.5），
     相位沿条带往外滞后一点（r × 1.6），读成挂着的东西在晃而不是整块平移。区域四周除了钉住那边都必须是透明的，不然错位会撕开 */
  function drawFrame(ctx, P, fn) {
    const i = SH.names.indexOf(fn), [cw, ch] = SH.cell, sx0 = (i % SH.cols) * cw, sy0 = Math.floor(i / SH.cols) * ch;
    const [x0, y0] = P.at([0, 0]), s = P.s, fx = cfg.flex && cfg.flex[fn];
    if (!fx) { ctx.drawImage(img, sx0, sy0, cw, ch, x0, y0, cw * s, ch * s); return; }
    ctx.save(); ctx.beginPath(); ctx.rect(x0 - 1e4, y0 - 1e4, 3e4, 3e4);
    for (const f of fx) ctx.rect(x0 + f[2] * s, y0 + f[1] * s, (f[0] - f[2]) * s, (f[3] - f[1]) * s);   // 反向矩形 = 挖掉
    ctx.clip('evenodd');
    ctx.drawImage(img, sx0, sy0, cw, ch, x0, y0, cw * s, ch * s);
    ctx.restore();
    const ST = 2;
    for (const [bx0, by0, bx1, by1, pin, amp, hz, lag] of fx) {
      const off = (r) => Math.pow(r, 1.5) * (amp * Math.sin(b.t * 6.2832 * hz + b.ph - r * 1.6) + (lag || 0) * P.w);
      if (pin === 't') for (let y = by0; y < by1; y += ST) {
        const h = Math.min(ST, by1 - y), d = off((y + h / 2 - by0) / (by1 - by0));
        ctx.drawImage(img, sx0 + bx0, sy0 + y, bx1 - bx0, h, x0 + (bx0 + d) * s, y0 + y * s, (bx1 - bx0) * s, h * s + 0.6);
      } else for (let x = bx0; x < bx1; x += ST) {
        const w = Math.min(ST, bx1 - x), d = off((x + w / 2 - bx0) / (bx1 - bx0));
        ctx.drawImage(img, sx0 + x, sy0 + by0, w, by1 - by0, x0 + x * s, y0 + (by0 + d) * s, w * s + 0.6, (by1 - by0) * s);
      }
    }
  }
  /* 挂件层：这一帧挂在 at[帧] 那一点、先转到帧上写的角度，再按 sway 甩（正弦 + 跟着秋千的摆往后拖）。z 选画在人后还是人前 */
  function drawParts(ctx, P, fn, z) {
    PARTS.forEach((q, i) => {
      const im = partImg[i], a = q.at[fn];
      if (!im || !a || (q.z || 1) !== z) return;
      const sw = q.sway || [0, 0, 0], ang = a[2] + sw[0] * Math.sin(b.t * 6.2832 * sw[1] + b.ph) + (sw[2] || 0) * P.w;
      const [x, y] = P.at([a[0], a[1]]);
      ctx.save(); ctx.translate(x, y); ctx.rotate(ang);
      ctx.drawImage(im, -q.pivot[0] * P.s, -q.pivot[1] * P.s, im.width * P.s, im.height * P.s);
      ctx.restore();
    });
  }
  /* 拿在手里的东西（出完手重新冒出来那一下从小长大） */
  function drawHeld(ctx, P, fn) {
    const [x, y] = P.at(A.hold[fn]), z = b.pop < 1 ? backOut(b.pop) : 1;
    ctx.save(); ctx.translate(x, y);
    if (atlas) drawAtlas(ctx, b.hang, A.r * z);
    else if (prop) { const w = prop.width * A.scale * z, h = prop.height * A.scale * z; ctx.rotate(b.hang * 0.2); ctx.drawImage(prop, -w / 2, -h / 2, w, h); }
    else if (A.item === 'bball') drawBall(ctx, A.r * z);
    ctx.restore();
  }
  /* 3D 转盘图集（art:danmu-3d-sprite 那条管线）：朝向角 ang → 第几格；半径 r（屏幕像素）× scale 是整格画多大 */
  function drawAtlas(ctx, ang, r) {
    const T = A.atlas, n = T.n, i = ((Math.floor(ang / 6.2832 * n) % n) + n) % n, d = 2 * r * T.scale;
    ctx.drawImage(atlas, (i % T.cols) * T.cell, Math.floor(i / T.cols) * T.cell, T.cell, T.cell, -d / 2, -d / 2, d, d);
  }
  /* 秋千（帧序列）：绳子和座板都是引擎画的（帧里的座板每格长短位置都不一样，frames.py 抠掉了）。
     绳子从座板两头（ropes.ends）往上：这一帧那只手握着绳（ropes.grip[帧][左 / 右]）就先拐到手上再上去，手画在绳子之上 = 握住；
     顶端在转轴那么高（画外）。座板 ropes.board [x0, y0, x1, y1]。都画在人之下。 */
  function drawSwing(ctx, P, fn) {
    const R = cfg.ropes, g = (R.grip && R.grip[fn]) || [];
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    R.ends.forEach((e, i) => {
      const pts = [P.at(e)]; if (g[i]) pts.push(P.at(g[i])); pts.push(P.at([e[0], cfg.pivot[1]]));
      for (const [w, c] of [[R.w * P.s + 3, R.edge], [R.w * P.s, R.fill]]) {
        ctx.strokeStyle = c; ctx.lineWidth = w; ctx.beginPath(); pts.forEach((p, j) => (j ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.stroke();
      }
      if (R.flowers) for (let j = 0; j + 1 < pts.length; j++) ropeFlowers(ctx, pts[j], pts[j + 1], R.flowers, i * 3 + j);
    });
    const [bx0, by0, bx1, by1] = R.board, [px0, py0] = P.at([bx0, by0]), [px1, py1] = P.at([bx1, by1]), h = py1 - py0;
    ctx.fillStyle = R.wood[0]; ctx.strokeStyle = R.edge; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.rect(px0, py0, px1 - px0, h); ctx.fill(); ctx.stroke();
    ctx.fillStyle = R.wood[1]; ctx.fillRect(px0 + 2, py0 + 2, px1 - px0 - 4, h * 0.32);          // 顶面亮
    ctx.strokeStyle = R.wood[2]; ctx.lineWidth = 1;                                              // 木纹
    ctx.beginPath(); ctx.moveTo(px0 + 10, py0 + h * 0.62); ctx.lineTo(px1 - 26, py0 + h * 0.62); ctx.moveTo(px0 + 40, py0 + h * 0.8); ctx.lineTo(px1 - 8, py0 + h * 0.8); ctx.stroke();
    for (const e of R.ends) {                                                                    // 绳子在板头绕一圈
      const [x, y] = P.at(e); ctx.fillStyle = R.fill; ctx.strokeStyle = R.edge; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.ellipse(x, y + h * 0.5, R.w * P.s * 0.9, h * 0.62, 0, 0, 6.2832); ctx.fill(); ctx.stroke();
    }
  }
  /* 绳上缠的小花：沿一段绳每 gap 像素一朵，左右交替 */
  function ropeFlowers(ctx, a, c, col, seed) {
    const L = Math.hypot(c[0] - a[0], c[1] - a[1]), gap = 58;
    for (let d = 24 + (seed * 17) % 30; d < L - 10; d += gap) {
      const u = d / L, x = a[0] + (c[0] - a[0]) * u, y = a[1] + (c[1] - a[1]) * u, side = (Math.round(d / gap) + seed) % 2 ? 1 : -1;
      ctx.save(); ctx.translate(x + side * 4, y);
      ctx.fillStyle = '#5d9a4a'; ctx.beginPath(); ctx.ellipse(side * 6, 3, 5, 2.4, side * 0.5, 0, 6.2832); ctx.fill();
      ctx.fillStyle = col; for (let k = 0; k < 5; k++) { const q = k * 1.2566; ctx.beginPath(); ctx.arc(Math.cos(q) * 3.2, Math.sin(q) * 3.2, 2.6, 0, 6.2832); ctx.fill(); }
      ctx.fillStyle = '#ffd24a'; ctx.beginPath(); ctx.arc(0, 0, 1.6, 0, 6.2832); ctx.fill();
      ctx.restore();
    }
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
    if (s.kind === 'bball') { if (atlas) drawAtlas(ctx, s.ang, A.r); else { ctx.rotate(s.ang); drawBall(ctx, A.r); } ctx.restore(); return; }
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
    const P = place(), S = b.bm, B = A.beam, h = handPt(P);
    ctx.save(); ctx.globalCompositeOperation = 'source-over';
    if (S.ph === 'charge') {
      const r = B.ball * (0.3 + 0.7 * Math.min(1, S.t / (SH ? LEAD : B.charge))) * (1 + 0.08 * Math.sin(S.t * 40));
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
  return { init, load, summon, update, items, drawOver, active, busy, reset, peek: () => (b ? [b] : []), frame: () => (b && SH ? frameName() : null), cfg };
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

/* 秋千绳的默认样子（数据文件里 { ...ROPE, ... } 再覆写） */
const ROPE = { w: 7, y: 0, fill: '#c9a36a', edge: 'rgba(70,45,20,.85)', wood: ['#b07a42', '#d9a468', 'rgba(90,55,25,.6)'] };

/* 三人组（2026-09-29 夜改成 10 组固定搭配，docs/三人组30人名单.md）。ground = 后排地面那个 crew.js 的 Crew（哥们 Buddy / 闺蜜 Bestie），
   data = trio_buddy.js / trio_bestie.js：{ ground: { 名单编号: Crew 的形象下标 }, cast: { 名单编号: cfg }, groups: [{ name, ground, top, floor }] }。
   每次送礼：上一组还有人在场（含正在离场）→ 同一组三个人各续一段（在场的续时间、走了的重新进场）；否则随机抽一组（不连着抽同一组）。
   **名单里还没做出来的人**（cast / ground 里没有这个编号）：这个槽位空着；一组一个都没做出来就整组跳过、不参与抽。
   pick（诊断 ?buddy=<组号 1~10>）：指定抽哪一组（那组一个人都没有就照常随机）。 */
function Trio(ground, data) {
  const acts = {};
  for (const [id, c] of Object.entries(data.cast)) acts[id] = Act({ id, ...c });
  const who = (id) => (id == null ? null : id in data.ground ? { m: ground, sk: data.ground[id] } : acts[id] ? { m: acts[id] } : null);
  const groups = data.groups.map((g, i) => ({ no: i + 1, name: g.name, mem: [g.ground, g.top, g.floor].map(who).filter(Boolean) }));
  const ready = groups.filter(g => g.mem.length);
  const all = [ground, ...Object.values(acts)];
  let cur = null;
  const stagger = () => [...TRIO.STAGGER].sort(() => Math.random() - 0.5);
  return {
    groups, ready, all, acts: Object.values(acts),
    summon(pick) {
      if (cur && cur.mem.some(x => x.m.active())) {
        const st = stagger();
        cur.mem.forEach((x, i) => x.m.summon(x.sk, x.m.active() ? 0 : st[i]));
        return;
      }
      const want = ready.find(g => g.no === +pick);
      const pool = ready.length > 1 ? ready.filter(g => g !== cur) : ready;
      cur = want || pool[Math.floor(Math.random() * pool.length)] || null;
      if (!cur) return;
      const st = stagger();
      cur.mem.forEach((x, i) => x.m.summon(x.sk, st[i]));
    },
    current: () => cur,
    active: () => all.some(m => m.active()),
    reset() { all.forEach(m => m.reset()); cur = null; },
  };
}
