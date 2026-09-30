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
  /* 叠第二组（2026-09-30 用户："最多在场 5 个人，两边各 5 个"，选的是"再送叠第二组"）：有人在场时再送，
     在场的续时间，再从别的组里挑人补到 MAX 个（一组三人在场 → 补两个 = 3 + 2）。组还没做齐、或叠上来的人先走了，下一次送照样补满。
     站位：自己的 at（第一组这个槽位空着时站这）和备用位（SLOT2），每个槽位最多站 CAP 个人。
     地板只有自己那个下角一个位：备用位往中间挪，两边的趴着 / 半跪的人在两个主角脚下叠成一堆（2026-09-30 截图），所以 2 + 2 + 1 = 5。
     挑人先后 PREFER：后排地面最好塞（在主角身后、被挡一部分也读得出）；上方其次；地板最后。
     SLOT2[槽位] = [往屏幕中间挪几像素, 往下挪几像素（负 = 往上）, 缩放倍数]，按这个人自己的 at 换算：
       ground 往里、往上、缩小 = 站得更远（透视：远的小、脚底高），depth 同乘，排远近时在第一组那位之后；
       top    同侧贴得更高（第一组上方那位和 HUD 之间），缩小一点；正上方仍空给档 4；
     crew.js 的滑板哥们 / 平衡车闺蜜不走 SLOT2：同一份 Crew 最多站两人（cfg.max 2），第二个自己挑没人的那一排。 */
  MAX: 5,
  CAP: { ground: 2, top: 2, floor: 1 },
  PREFER: ['ground', 'top', 'floor'],
  SLOT2: { ground: [110, -45, 0.85], top: [0, -210, 0.85] },
};

const easeOut = (u) => 1 - Math.pow(1 - u, 3);
const backOut = (u) => { const c = 2.2; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); };
const lerp = (a, b, k) => a + (b - a) * k;
const rnd = (a, b) => a + Math.random() * (b - a);
/* 二次贝塞尔 p0 → c → p2 在 e 处的点，和那一点的切线方向 */
const bez = (p0, c, p2, e) => { const q = 1 - e; return [q * q * p0[0] + 2 * q * e * c[0] + e * e * p2[0], q * q * p0[1] + 2 * q * e * c[1] + e * e * p2[1]]; };
const bezDir = (p0, c, p2, e) => Math.atan2((1 - e) * (c[1] - p0[1]) + e * (p2[1] - c[1]), (1 - e) * (c[0] - p0[0]) + e * (p2[0] - c[0]));

/* 一个人。cfg（逐字段说明见 docs/三人组角色规范.md 第六节）：
   face   +1 朝右（闺蜜，在左边）/ -1 朝左（哥们，在右边）
   sheet  帧序列图集 { src, cell: [w, h], cols, names }（frames.py 打印）；没有 sheet 就是旧的单张立绘 src
   at [x, y, s] 锚点落在屏幕哪、画多大；anchor 贴图上的锚点（帧序列：所有帧共用；扒墙的手脚、趴着的肚皮、秋千座板中心）
   pivot  前后倾 / 秋千摆绕的点（贴图像素，秋千是绳子顶端，在贴图外面）；leanK 前后倾打几折（帧序列里动作已经画在帧上，默认 1）
   depth  远近（< 1 主角身后，> 1 主角之前），main.js 按它跟别的帮手一起排
   enter  进场方式：crawl 爬 / spring 弹 / slide 扑地滑 / dive 腾空扑地再滑 / dash 斜冲 / roll 翻滚 / creep 匍匐（crawl、creep 帧序列：一个爬行帧一步、手 / 肘钉住，bob 奇数帧抬几 px）/ swing 荡 /
          walk 走（跑，stride 接地帧两脚距离：一帧一步、脚钉地）/ ride 骑、滑 / fly 飞下 / leap 跳落（fly、leap 同一条路：from 起点、h 抛物线高、air 几秒到）/ drop 倒挂垂下 /
          appear 原地出现（fx 闪光 / 烟，rise 从一条线后面升上来）/ rope 横绳（ends 两头屏幕点、touch 压绳点）。见 place()
          帧序列：enter { kind, T: 几秒, seq: [[帧或帧数组, 秒, 'land'?], ...], fps, ... }；exit { frame（可为数组）, T, fps, flip }
   idle   帧序列：{ frame: 待机帧, breathe: [胀缩幅度, 每秒几次, 横向补偿 (默认 0.4)] }；flex { 帧: [[x0, y0, x1, y1, 't'|'b'|'l'|'r' 钉住哪边, 幅度, 每秒几次, 跟摆], ...] }
   atk    攻击：{ kind: 'throw' | 'punch' | 'beam' | 'camera' | 'whip' | 'rush' | 'slash' | 'spray', ... }。帧序列：seq [[帧或帧数组, 秒, 'fire'?], ...]、
          hold { 帧: [x, y] } 东西拿在哪（出手帧那一格就是出手点）或 from [x, y]、atlas 3D 转盘图集 { src, n, cols, cell, scale }（没有就用 prop 平面图）、
          tether 手和丢出去的东西连一根线；onHit 另有 net 网兜、freeze 冻住。throw / camera / beam / punch 帧序列和单张立绘都能用，
          whip 抽打 / rush 连打（残影）/ slash 斩痕 / spray 喷只有帧序列（fire() 起头、stepFx 按时间推）。持续型的出手帧时长要盖住它
   parts  帧序列：挂件层（扇子、靠旗、翎子这类单独拆出来随动作甩的东西）[{ src, pivot: [x, y] 挂件图上挂住的点, z: -1 画在人后 / 1 人前,
          at: { 帧: [x, y, 角度] } 这一帧挂在哪（格内像素）、没写的帧不画, sway: [幅度 rad, 每秒几次, 跟摆] }]（v14/trio/tools/part.py 出图）
   recipe 打中炸什么（main.js RECIPE 的键） */
function Act(cfg) {
  const F = cfg.face, A = cfg.atk, SH = cfg.sheet || null;
  const LK = cfg.leanK != null ? cfg.leanK : 1;
  const E = typeof cfg.enter === 'string' ? { kind: cfg.enter } : cfg.enter, EK = E.kind;   // 进场方式（帧序列的 enter 是 { kind, seq, ... }）
  /* 走：位移跟帧走 —— 只在换帧那一刻迈一步，同一帧停留时人不动，踩在地上的那只脚就钉在地上（连续平移 + 7fps 换帧 = 着地的脚一帧滑 30px）。
     一步 = enter.stride（接地帧两脚距离，格内像素）/ 2 × s；步数 = 距离 ÷ 步长取整，步长按步数匀一下让最后一步正好落到 at；进场几秒由步数和 fps 定。
     没写 stride 的按 T × fps 步匀分（仍然钉脚，只是步子大小不一定对得上腿） */
  const WK = EK === 'walk' ? (() => {
    const fps = E.fps || 10, D = E.dist || (SH ? SH.cell[0] : 300) * cfg.at[2] + 30;
    const n = Math.max(1, Math.round(E.stride ? D / (E.stride / 2 * cfg.at[2]) : (E.T || TRIO.T.enter) * fps));
    return { fps, D, n, step: D / n };
  })() : null;
  /* 爬 / 匍匐（帧序列）：同 walk，位移跟帧走。进场 seq 开头的爬行段（到 'land' 段或最后一段为止，数组段按 fps 每格算一帧）
     每换一帧往前挪一步、同一帧停着时人不动 —— 扒墙的手、贴地的手肘就钉住（连续平移时同一帧 70ms 能滑 40px）。
     步子 = 画外距离 ÷ 爬行帧数，第一帧已经露出一截，最后一个爬行帧落到 at，之后的 land / 到位帧原地换 */
  const CK = (EK === 'crawl' || EK === 'creep') && SH && E.seq ? (() => {
    const st = [], fps = E.fps || 10;
    let a = 0;
    for (let i = 0; i < E.seq.length - 1 && E.seq[i][2] !== 'land'; i++) {
      const [f, d] = E.seq[i];
      if (Array.isArray(f)) for (let j = 0; j * (1 / fps) < d - 1e-9; j++) st.push(a + j / fps);
      else st.push(a);
      a += d;
    }
    return st.length ? { st, end: a } : null;
  })() : null;
  const TE = WK ? WK.n / WK.fps : E.T || TRIO.T.enter, TX = (cfg.exit && cfg.exit.T) || TRIO.T.exit;   // 这个人进场 / 离场用几秒（走进来的要比扑进来的慢）
  let img = null, prop = null, atlas = null, o = {}, b = null;
  const PARTS = (SH && cfg.parts) || [], partImg = [];
  const shots = [], marks = [];
  let iceBuf = null;                            // 冻住的冰壳先画在这上面（drawMark）                 // 飞出去的东西、挂在人身上的记号
  /* 帧序列的出手：seq 里第几帧是出手帧、之前一共蓄力几秒、整段几秒 */
  const FI = SH && A.seq ? A.seq.findIndex(q => q[2] === 'fire') : -1;
  const LEAD = FI > 0 ? A.seq.slice(0, FI).reduce((a, q) => a + q[1], 0) : 0;
  const CLIP = SH && A.seq ? A.seq.reduce((a, q) => a + q[1], 0) : 0;
  /* 带线的东西（A.tether）飞出去、弹开掉完之前还连在手上：还在线上的那一只（钉在地板上的不算，线不画它） */
  const FALL = 0.9;                                              // 打中弹开以后掉多久（stepShot）
  const onLine = (s) => !!A.tether && s.kind === A.item && s.stuck == null;
  /* 一整下出手从起头到收完要几秒：帧序列 = 整段 seq；出拳 = 伸停回；单张立绘发波 = 聚光 + 轰；带线的还要等东西飞到、弹开掉完（线才收回手上）。
     离场前装不下一整下就不起手 —— 起了手再离场，要么整张摆着出手姿势滑出去，要么半截收掉硬切成离场帧（规范 §离场与出手） */
  const ACT = Math.max(SH && A.seq ? CLIP : A.kind === 'punch' ? A.phases.reduce((a, q) => a + q, 0) : A.kind === 'beam' ? A.beam.charge + A.beam.fire : 0,
                       A.tether ? LEAD + A.T * 1.1 + (A.onHit === 'bounce' || A.onHit === 'heart' ? FALL : 0) : 0);
  /* 东西从哪出去：帧序列 = 出手帧那一格的 hold 点；单张立绘 = hand */
  const handPt = (P) => pt(P, SH ? A.from || A.hold[A.seq[FI][0]] : cfg.hand);   // 帧序列可以直接给 atk.from（出手帧是循环帧、手里不画东西的：连打、抽打、喷）
  /* 手此刻在哪：当前帧写了 hold 就用它（蓄力时手在腰侧、甩线时手在跟着动），没写就退回出手点 */
  const holdPt = (P) => { const fn = SH ? frameName() : null; return fn && A.hold && A.hold[fn] ? pt(P, A.hold[fn]) : handPt(P); };
  /* 出手的东西从 p0 到 p2 走的二次贝塞尔的控制点（横坐标取中点，纵坐标默认 cy）。
     后排（depth < 1）的人站在自己主角身后，出手点和他的头一样高，东西、链子、手臂、雾都画在主角之上 —— 直着过去一定横穿他的脸。
     所以后排的路要从他头顶翻过去：曲线经过他脸框（o.shield() = [x, y, r]）那几列（左右各再放宽 pad）时，要在脸框上沿 − 40 − pad 以上，按这个反推控制点够多高。
     pad = 走在路上的这件东西自己的半径（雾团、道具、棍影都有个头，路过去了它的下沿还会蹭到脸）。
     出发点本身得在头顶以上（后排的人出手帧把手举过头顶，from / hold 写在那一点）—— 路只管中间那一段。 */
  const REAR = (cfg.depth || 1) < 1;
  function over(p0, p2, cy, pad = 0) {
    const c = [(p0[0] + p2[0]) / 2, cy], f = REAR && o.shield && o.shield();
    if (!f || Math.abs(p2[0] - p0[0]) < 1) return c;
    const Y = f[1] - f[2] - 40 - pad;
    for (const x of [f[0] - f[2] - pad, f[0], f[0] + f[2] + pad]) {      // 列也按 pad 放宽：物件中心走到脸框外侧 pad 以内时，它的边还压在脸框上
      const e = (x - p0[0]) / (p2[0] - p0[0]);                     // 控制点横坐标在中点 ⇒ 曲线的 x 对 e 是线性的
      if (e > 0.02 && e < 0.98) c[1] = Math.min(c[1], (Y - (1 - e) * (1 - e) * p0[1] - e * e * p2[1]) / (2 * e * (1 - e)));
    }
    return c;
  }
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

  /* 来一个（wait 秒后才开始进场）；在场再送 = 续一份时间，下一下按礼物力度打。
     slot（可无）：{ at, depth } 这一趟站哪、排多远（叠第二组时站备用位，见 TRIO.SLOT2）；不给就是自己的 cfg.at / cfg.depth */
  function summon(_sk, wait = 0, slot = null) {
    if (b && b.t <= TE + b.stay) { b.stay += TRIO.T.stay; b.first = true; return; }
    /* 正在离场又被叫住：从现在退到的地方倒着走回来。离场退出去 out²，进场还差 (1 − u)³（easeOut），两者相等处接上 */
    if (b && b.wait <= 0) {
      const out = Math.min(1, (b.t - TE - b.stay) / TX);
      b.t = (1 - Math.pow(out, 2 / 3)) * TE; b.stay = TRIO.T.stay; b.first = true; b.landed = false;
      b.cd = rnd(0.15, 0.4);                                     // 和头一次来一样落地后隔一下才出手（离场前最后一下没起手，cd 可能早就 ≤ 0）
      return;
    }
    b = { t: 0, wait, stay: TRIO.T.stay, first: true, cd: rnd(0.15, 0.4), lean: 0, snap: 0, ph: Math.random() * 6,
          pk: null, bm: null, prevPh: 0, landed: false,
          clip: null, ammo: true, pop: 1, hang: Math.random() * 6, sq: 0, fn: null, tf: null,   // 帧序列：出手动作、手里有没有东西、挤压、当前帧
          at: slot ? slot.at : cfg.at, depth: slot ? slot.depth : cfg.depth };                 // 这一趟站哪、排多远
    return b;
  }
  /* 从现在起 lead 秒后起手，一整下（ACT）能不能在离场前收完 */
  const room = (lead) => b.t + lead + ACT <= TE + b.stay;
  const active = () => !!b;
  const busy = () => !!b || shots.length > 0 || marks.length > 0;
  function reset() { b = null; shots.length = 0; marks.length = 0; }

  /* 此刻的摆放：锚点在屏幕 (x, y)，画多大 s，整个人绕 rc（屏幕点）转 rot。 */
  function place() {
    const [ax, ay, s] = b.at, t = b.t, T = TRIO.T, se = TE + b.stay;
    const off = texW() * s + 30;                         // 整个人挪出画外要多远
    let dx = 0, dy = 0, rot = 0, spin = 0, w = 0;
    const u = Math.min(1, t / TE), out = t > se ? Math.min(1, (t - se) / TX) : 0;
    /* 进场 k：1 = 还在画外、0 = 到位；离场按 u² 退回画外（往来的方向回去） */
    const k = t < TE ? 1 - (EK === 'spring' ? backOut(u) : easeOut(u)) : out * out;
    const sd = F > 0 ? -1 : 1;                           // 画外在哪边：闺蜜在左、哥们在右
    /* 帧序列的爬 / 匍匐进场：第 j 个爬行帧停在 (1 − (j+1)/n) × 画外距离；一耸（bob）也跟帧，奇数帧抬起 */
    const crawlStep = (bob) => {
      if (t >= CK.end) return;
      let j = 0;
      while (j + 1 < CK.st.length && t >= CK.st[j + 1]) j++;
      dx = sd * (E.dist || off) * (1 - (j + 1) / CK.st.length);
      dy = -(j % 2) * (E.bob != null ? E.bob : bob) * s;
    };
    switch (EK) {
      case 'crawl':   // 扒着屏幕边爬进来：一步一耸（帧序列走 CK，见 crawlStep）
        if (CK && t < TE) { crawlStep(6); break; }
        dx = sd * off * k; dy = Math.sin(u * Math.PI * 5) * 7 * (1 - u); rot = Math.sin(u * Math.PI * 5) * 0.05 * (1 - u); break;
      case 'spring':  // 橡皮人：一下弹进来、冲过头再弹回
        dx = sd * off * k; rot = -sd * 0.18 * k; break;
      case 'slide':   // 飞身扑地：从下角斜着滑进来，头略朝下
        dx = sd * off * k; dy = 110 * k; rot = sd * 0.12 * k; break;
      case 'dive': {  // 腾空扑地（帧序列）：前 air 秒在空中（抛物线落到地板、头略朝下），之后贴着地滑到位；离场贴地倒滑出去
        const q = Math.min(1, t / E.air);
        dx = sd * off * k;
        if (t < E.air) { dy = -E.h * (1 - q * q); rot = sd * 0.08 * (1 - q); }
        break;
      }
      case 'dash':    // 斜着从下面冲上来
        dx = sd * off * 0.7 * k; dy = 300 * k; rot = sd * 0.2 * k; break;
      case 'roll':    // 翻滚进来：转一圈落成半跪
        dx = sd * off * k; dy = 220 * k; spin = -sd * 6.2832 * k; break;
      case 'creep':   // 匍匐爬进来：贴着地一耸一耸（帧序列走 CK：起伏已经画在帧上，整个人再抬会让贴地的手肘离地，默认不抬）
        if (CK && t < TE) { crawlStep(0); break; }
        dx = sd * off * k; dy = -Math.abs(Math.sin(u * Math.PI * 6)) * 6 * (1 - u); break;
      case 'walk': {  // 走 / 跑（帧序列，enter.seq 第一段写循环帧，接地帧起头）：从自己那侧画外一帧一步走进来（WK）；离场同样一帧一步走回去
        let i = -1;
        if (t < TE) { i = Math.floor(t * WK.fps); dx = sd * (WK.D - i * WK.step); }
        else if (t > se) {
          const fx = (cfg.exit && cfg.exit.fps) || WK.fps;   // 与 frameName 的离场循环同一个时钟
          i = Math.floor((t - se) * fx); dx = sd * i * Math.max(WK.step, WK.D / Math.max(1, Math.floor(TX * fx)));
        }
        /* 一步一伏也跟帧：接地帧（偶数帧）最低、交错帧（奇数帧）最高 */
        if (i >= 0) dy = -(i % 2) * (E.bob != null ? E.bob : 6) * s;
        break;
      }
      case 'ride': {  // 骑 / 滑（平衡车、电动车、滑冰、轮滑）：匀减速滑到位，身子往来的方向仰（tilt）、轮子压地细颤。轮子带着走，整个人平移是对的
        dx = sd * (E.dist || off) * (t < TE ? 1 - easeOut(u) : out * out);
        rot = sd * (E.tilt != null ? E.tilt : 0.08) * (t < TE ? 1 - u : out);
        if (t < TE || t > se) dy = Math.sin(t * 31) * 0.8 * s;
        break;
      }
      case 'leap':    // 跳落（跃下单膝、撑棒跃进、轻跳落地）：从 from 出发，抛物线（顶点比直线高 h）在 air 秒落到位；落地那一帧 seq 标 'land' 压扁
      case 'fly': {   // 飞下 / 飘下（御剑、酒坛、月亮、无人机、船头）：同一条路、h 0、减速滑到位。离场都原路倒回去
        const fly = EK === 'fly', air = E.air || TE, h = E.h != null ? E.h : fly ? 0 : 160;
        const fr = E.from || (fly ? [sd * off * 0.6, -720] : [sd * off, 0]);   // 起点 = 锚点的屏幕位置 + from（屏幕像素）
        const q = t <= se ? Math.min(1, t / air) : 1 - out * out, e = fly ? easeOut(q) : q;
        dx = fr[0] * (1 - e); dy = fr[1] * (1 - e) - h * 4 * q * (1 - q); rot = sd * (E.tilt || 0) * (1 - e);
        break;
      }
      case 'drop': {  // 倒挂垂下：顺着一根丝 / 绳从上面掉下来，冲过头再弹回（蹦极）；在场绕 pivot（绳顶，画外）轻轻荡；离场被拽回去
        dy = -(E.len || 700) * (t < TE ? 1 - backOut(u) : out * out);
        if (t >= TE && t <= se) rot = (E.sway != null ? E.sway : 0.04) * Math.sin(t * 1.7 + b.ph);
        break;
      }
      case 'appear':  // 原地出现（闪现、变身、钻出、坐上墙头）：不走位，显形在 drawBody（淡入 + 由小弹大，或从一条线后面升上来）+ 闪光 / 烟
        if (E.rise) dy = E.rise * s * (t < TE ? 1 - easeOut(u) : out * out);
        break;
      case 'rope': {  // 横绳：一根两头系在 ends（屏幕点）的绳，人躺 / 坐在绳上从自己那侧滑进来，在场随绳上下颠、来回荡；离场滑回去
        dx = sd * off * k;
        if (t >= TE && t <= se) {
          const sw = E.sway != null ? E.sway : 14;
          dx += Math.sin((t - TE) * 1.6 + b.ph) * sw * s; dy = -Math.abs(Math.cos((t - TE) * 1.6 + b.ph)) * sw * 0.3 * s; rot = Math.sin((t - TE) * 1.6 + b.ph) * 0.03;
        }
        break;
      }
      case 'swing': { // 秋千从画外荡进来：摆角大、慢慢收到小幅来回，一直荡着；离场荡回画外
        const S = cfg.swing, A0 = TRIO.still && t >= TE ? 0 : S.a + (S.a0 - S.a) * Math.exp(-t / S.tau);
        rot = -sd * A0 * Math.cos(S.w * t) + (-sd) * 1.5 * out * out;
        w = sd * A0 * S.w * Math.sin(S.w * t);            // 摆的角速度（流苏跟摆、蹬腿换帧用）
        break;
      }
    }
    /* 在场：单张立绘整个人上下浮 2px 当呼吸。帧序列的人不浮 —— 呼吸是绕锚点的胀缩（drawBody），锚点（贴地的肚皮、压着座板的屁股）不能动 */
    if (!SH && t >= TE && t <= se) dy += Math.sin(t * 2.2 + b.ph) * 2 * s;
    if (!TRIO.still) rot += b.lean + b.snap;
    const at = (q) => [ax + dx + (q[0] - cfg.anchor[0]) * s, ay + dy + (q[1] - cfg.anchor[1]) * s];
    return { at, s, rot, spin, w, dy, rc: at(cfg.pivot), sc: at([texW() / 2, texH() / 2]) };
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
  /* 丢出去的东西在屏幕上多大（半径）：3D 转盘 / 程序画的按 r，平面图按长边 */
  const itemR = () => A.r || (prop ? Math.max(prop.width, prop.height) * (A.scale || 1) / 2 : 20);
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
    const T = TRIO.T, se = TE + b.stay;
    if (b.t >= se + TX) { b = null; return; }
    if (!b.landed && b.t >= TE) { b.landed = true; if (o.onLand) { const P = place(); o.onLand(...P.at(cfg.anchor), EK); } }
    b.snap *= Math.exp(-TRIO.lean.decay * dt);
    const on = b.t >= TE && b.t <= se;
    const L = TRIO.lean;
    if (SH) { stepFrames(dt, on); return; }
    if (A.kind === 'punch') { stepPunch(dt, on); return; }
    if (A.kind === 'beam') { stepBeam(dt, on); return; }
    /* 丢东西 / 拍照：秋千荡到最前面那一下出手（荡到高处抛）；其余按间隔，出手前 wind 秒往后蓄力 */
    if (!on || (EK !== 'swing' && !room(Math.max(0, b.cd)))) { b.lean *= Math.exp(-8 * dt); return; }
    if (EK === 'swing') {
      const S = cfg.swing, ph = (S.w * b.t) % 6.2832, prev = b.prevPh; b.prevPh = ph;
      const to = (Math.PI - ph + 6.2832) % 6.2832;                        // 离最前面（cos = −1）还差多少相位
      b.lean = to < 1.2 ? -F * L.wind * (1 - to / 1.2) : b.lean * Math.exp(-8 * dt);
      if (prev < Math.PI && ph >= Math.PI && room(0)) fire();
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
  /* seq 里 t 秒时画哪一帧。一段的帧名可以是数组 = 这一段里按 fps 循环（走路 [walk1, walk2, walk3, walk2]、连打 [hitA, hitB]） */
  function seqFrame(seq, t, fps) {
    let a = 0, i = 0;
    for (; i < seq.length - 1 && t >= a + seq[i][1]; i++) a += seq[i][1];
    const f = seq[i][0];
    return Array.isArray(f) ? f[Math.floor(Math.max(0, t - a) * (fps || 10)) % f.length] : f;
  }
  /* 此刻画哪一帧：出手动作 > 进场序列 > 离场帧 > 秋千蹬腿 > 待机 */
  function frameName() {
    const t = b.t, T = TRIO.T, se = TE + b.stay;
    if (b.clip) return seqFrame(A.seq, b.clip.t, A.fps);
    if (t < TE && E.seq) return seqFrame(E.seq, t, E.fps);
    if (t > se && cfg.exit) { const X = cfg.exit.frame; return Array.isArray(X) ? X[Math.floor((t - se) * (cfg.exit.fps || E.fps || 10)) % X.length] : X; }
    if (cfg.swing && cfg.swing.pump) {
      /* 荡秋千：往前荡时伸腿（kick）、往后荡时收腿（tuck）—— 换帧正好落在摆到两头、人一瞬间停住的时候，硬切看不出跳。
         荡得小了（< min rad）就不蹬了，坐着待机 */
      const S = cfg.swing, P = S.pump, A0 = S.a + (S.a0 - S.a) * Math.exp(-t / S.tau);
      /* place：rot = F·A0·cos(wt)（sd = −F），往前荡 ⇔ −F·dθ/dt = A0·w·sin(wt) > 0 */
      if ((A0 >= P.min && !(TRIO.still && t >= TE)) || t > se) return Math.sin(S.w * t) > 0 ? P.fwd : P.back;
    }
    return cfg.idle.frame;
  }
  function stepFrames(dt, on) {
    const L = TRIO.lean, fn = frameName();
    if (fn !== b.fn) {                                          // 换帧那一下：落地压扁
      const q = !b.clip && b.t < TE && E.seq ? E.seq[seqAt(E.seq, b.t)] : null;
      if (q && q[2] === 'land') b.sq = E.sq || 0.1;
      b.fn = fn;
    }
    b.sq *= Math.exp(-TRIO.sq.decay * dt);
    stepFx(dt);
    b.hang += (A.idleSpin || 0) * dt;                           // 拿在手里的球慢慢转（手指拨着玩）
    if (b.pop < 1) b.pop = Math.min(1, b.pop + dt / TRIO.pop);
    reload();
    if (!A.seq) return;
    if (!b.clip) {
      b.lean *= Math.exp(-8 * dt);
      if (!on) return;
      if (cfg.swing) {
        /* 秋千：算好提前量，让"出手"那一帧正好落在荡到最前面（cos = −1）那一刻 */
        const S = cfg.swing, ph = (S.w * b.t) % 6.2832, tf = ((Math.PI - ph + 6.2832) % 6.2832) / S.w, prev = b.tf;
        b.tf = tf;
        if (prev != null && prev >= LEAD && tf < LEAD && b.ammo && room(tf - LEAD)) {
          b.clip = { t: LEAD - tf, fired: false };
          if (A.kind === 'beam') b.bm = { ph: 'charge', t: b.clip.t, dr: 0, u: rnd(0.1, 0.8) };
        }
        return;
      }
      b.cd -= dt;
      if (b.cd <= 0 && b.ammo && room(0)) b.clip = { t: 0, fired: false };
      if (b.clip && A.kind === 'beam') b.bm = { ph: 'charge', t: 0, dr: 0, u: rnd(0.1, 0.8) };   // 发波：蓄力那几帧手心聚光
      return;
    }
    const C = b.clip; C.t += dt;
    if (b.bm) {                                                  // 发波：出手帧开轰（fire()），之后每 drip 秒溅一下，轰满 beam.fire 秒收
      const S = b.bm; S.t += dt;
      if (S.ph === 'fire') { beamTick(S, dt); if (S.t >= A.beam.fire) S.ph = 'rest'; }
    }
    const i = seqAt(A.seq, C.t);
    /* 蓄力那几帧整个人再往后倾一点（帧上画的动作 + 一点整体惯性），出手那一下往前甩 */
    if (i < FI) b.lean = -F * L.wind * LK * Math.min(1, C.t / LEAD);
    if (!C.fired && i >= FI) { C.fired = true; b.lean = 0; b.snap = F * L.snap * LK; b.sq = -(A.stretch || 0.05); fire(); b.ammo = false; }
    if (C.t >= CLIP) { b.clip = null; b.bm = null; b.cd = rnd(A.gap ? A.gap[0] : 0.5, A.gap ? A.gap[1] : 0.8); reload(); }
  }
  /* 手里重新冒出一个：出手动作收完、带线的那一只也收回来了（还在线上就不画手里这只，不然同时两只） */
  function reload() {
    if (!b.ammo && !b.clip && !shots.some(onLine)) { b.ammo = true; b.pop = 0; }
  }

  function fire() {
    b.lean = 0; b.snap = F * TRIO.lean.snap * LK;
    const P = place();
    if (A.kind === 'camera') { flash(P); return; }
    /* 帧序列的近身 / 连续攻击：出手帧开始，后面由 stepFx 按时间推（出手那一段 seq 的时长要盖住它） */
    if (A.kind === 'whip') { b.wh = { t: 0, hit: false, u: rnd(0.15, 0.7) }; return; }
    if (A.kind === 'rush') { b.ru = { t: 0, n: 0 }; return; }
    if (A.kind === 'spray') { b.sp = { t: 0, e: 0, h: 0, u: rnd(0.2, 0.7) }; return; }
    if (A.kind === 'punch') { b.pk = { t: 0, hit: false }; return; }
    if (A.kind === 'slash') {
      const Q = A.slash, u = rnd(0.2, 0.6);
      for (let i = 0; i < Q.n; i++) shots.push({ kind: 'slash', t: -i * Q.gap, u: u + rnd(-0.12, 0.12), ang: Q.ang + rnd(-1, 1) * Q.spread + (i % 2 ? Math.PI * 0.12 : 0) });
      return;
    }
    if (A.kind === 'beam') { Object.assign(b.bm, { ph: 'fire', t: 0, dr: 0, hit: false }); return; }   // 帧序列的发波（单张立绘的走 stepBeam）：光头伸到脸上才打中（beamTick）
    for (let k = 0; k < (A.n || 1); k++) launch(P);
  }

  /* 飞：t/T 走贝塞尔。落点：故意扔偏的是地板上那一点，其余是 o.aim(u)（打谁的哪里，main.js 给） */
  function stepShot(s, dt) {
    if (s.stuck != null) return (s.stuck += dt) < (A.stick || 2.2);        // 钉在地板上的玫瑰
    if (s.fall) {                                                         // 打中以后弹开 / 掉下去
      s.vy += 1800 * dt; s.x += s.vx * dt; s.y += s.vy * dt; s.ang += s.spin * dt; s.fall -= dt;
      return s.fall > 0;
    }
    if (s.kind === 'ghost') {                                             // 连打的残影：easeOut 冲到落点，到了打一下，再淡掉
      s.t += dt;
      const tg = o.aim(s.u); if (tg) s.p2 = tg;
      if (!s.p2) return false;
      if (!s.hit && s.t >= s.T) {
        s.hit = true; hit(s.p2[0], s.p2[1]);
        if (s.i === 0) { mark(s.p2[0], s.p2[1]); if (A.rush.text) marks.push({ kind: 'text', t: 0, life: 0.7, s: A.rush.text, j: rnd(-1, 1) }); }
      }
      return s.t < s.T + 0.14;
    }
    if (s.kind === 'slash') {                                             // 斩痕：一道弧光在落点划出来（0.07 秒），划到那一下打中，之后淡掉
      s.t += dt;
      if (s.t < 0) return true;
      if (!s.p) s.p = o.aim(s.u);
      if (!s.p) return false;
      if (!s.hit && s.t >= 0.05) { s.hit = true; hit(s.p[0], s.p[1]); mark(s.p[0], s.p[1]); }
      return s.t < (A.slash.life || 0.45);
    }
    if (s.kind === 'puff') {                                              // 喷出去的一团雾：沿路飞、越飞越大越淡，飞过头就减速散开
      s.t += dt;
      if (s.t < s.T) {
        const e = s.t / s.T, [x, y] = bez(s.p0, s.c, s.p2, e);
        s.vx = (x - s.x) / Math.max(dt, 1e-3); s.vy = (y - s.y) / Math.max(dt, 1e-3); s.x = x; s.y = y;
      } else {
        if (s.t > s.life * 0.55) { const q = Math.exp(-6 * dt); s.vx *= q; s.vy *= q; }
        s.x += s.vx * dt; s.y += s.vy * dt;
      }
      return s.t < s.life;
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
    const [nx, ny] = bez(p0, over(p0, p2, Math.min(p0[1], p2[1]) - s.arc * d, itemR()), p2, e);
    s.vx = (nx - s.x) / Math.max(dt, 1e-3); s.vy = (ny - s.y) / Math.max(dt, 1e-3);
    s.x = nx; s.y = ny; s.ang += s.spin * dt;
    if (e < 1) return true;
    if (s.miss) { s.stuck = 0; return true; }
    /* 到了：打中。后续看是什么东西 */
    hit(s.x, s.y);
    const f = o.face();
    mark(s.x, s.y);
    if (A.onHit === 'wear' && f) { for (const m of marks) if (m.kind === 'wear') m.life = Math.min(m.life, m.t + 0.25); marks.push({ kind: 'wear', t: 0, life: 2.6, a: rnd(-0.3, 0.3) }); return false; }
    if (A.onHit === 'bounce' || A.onHit === 'heart') {                      // 弹开：往回、往上蹦，转着掉下去
      s.fall = FALL; s.vx = -Math.sign(s.vx || -F) * rnd(160, 320); s.vy = -rnd(420, 620); s.spin = (A.spin || 6) * (s.vx > 0 ? 1 : -1);
      return true;
    }
    return false;
  }

  /* 打中之后留在他 / 她身上的记号（onHit）：heart 头上冒爱心 / lips 口红印（x, y = 打中那一点）/ net 网兜罩住头 / freeze 冻住（半透明冰壳包住头） */
  function mark(x, y) {
    const f = o.face();
    if (!f) return;
    if (A.onHit === 'heart') marks.push({ kind: 'heart', t: 0, life: 1.3, dx: rnd(-0.3, 0.3), j: Math.random() });
    if (A.onHit === 'lips' && x != null) marks.push({ kind: 'lips', t: 0, life: 6, u: (x - f[0]) / f[2], v: (y - f[1]) / f[2], a: rnd(-0.5, 0.5) });
    if (A.onHit === 'net') { for (const m of marks) if (m.kind === 'net') m.life = Math.min(m.life, m.t + 0.2); marks.push({ kind: 'net', t: 0, life: 2.4, a: rnd(-0.25, 0.25) }); }
    if (A.onHit === 'freeze') { for (const m of marks) if (m.kind === 'ice') m.life = Math.min(m.life, m.t + 0.2); marks.push({ kind: 'ice', t: 0, life: 1.8, j: Math.random() * 6 }); }
  }

  /* 出拳（草帽）：拳头顺着手臂方向"咻"地伸到她脑门、停一下、弹回来。手臂 = 腕 → 拳头之间画一截肉色的橡皮管。
     阶段 [伸, 停, 回] 秒；伸到那一刻打中 */
  function stepPunch(dt, on) {
    const P = A.phases;
    if (!b.pk) {
      if (!on || !room(Math.max(0, b.cd))) { b.lean *= Math.exp(-8 * dt); return; }
      b.cd -= dt;
      b.lean = b.cd < A.wind ? -F * TRIO.lean.wind * (1 - Math.max(0, b.cd) / A.wind) : b.lean * Math.exp(-8 * dt);
      if (b.cd <= 0) { b.pk = { t: 0, hit: false }; b.lean = 0; b.snap = F * TRIO.lean.snap; }
      return;
    }
    if (!advancePunch(dt)) b.cd = rnd(A.gap[0], A.gap[1]);
  }
  /* 拳头往外伸 → 伸到那一刻打中（头上绕星星）→ 停 → 弹回；收完返回 false（b.pk 清掉） */
  function advancePunch(dt) {
    const P = A.phases, k = b.pk; k.t += dt;
    if (!k.hit && k.t >= P[0]) {
      k.hit = true;
      const tg = o.aim(0);
      if (tg) { hit(tg[0], tg[1]); marks.push({ kind: 'stars', t: 0, life: 1.1, j: Math.random() }); }
    }
    if (k.t >= P[0] + P[1] + P[2]) { b.pk = null; return false; }
    return true;
  }

  /* ---- 帧序列的近身 / 连续攻击（fire() 起头，这里按时间推；不跟 clip 绑，收势帧里抽出去的鞭子照样收回来） ---- */
  function stepFx(dt) {
    if (b.pk) advancePunch(dt);
    if (b.wh) {                                                  // 抽打：甩出去（phases[0]）→ 抽到那一下打中 → 停 → 收回
      const W = b.wh, Ph = A.phases; W.t += dt;
      if (!W.hit && W.t >= Ph[0]) { W.hit = true; const tg = o.aim(W.u); if (tg) { hit(tg[0], tg[1]); mark(); } }
      if (W.t >= Ph[0] + Ph[1] + Ph[2]) b.wh = null;
    }
    if (b.ru) {                                                  // 连打：每 every 秒从手上飞出一个残影（拳影 / 腿影 / 棍影），到了算一下
      const R = b.ru, Q = A.rush; R.t += dt;
      while (R.n < Q.n && R.t >= R.n * Q.every) {
        shots.push({ kind: 'ghost', t: 0, T: Q.T || 0.1, p0: handPt(place()), u: rnd(0.1, 0.85), i: R.n, j: rnd(-1, 1) });
        R.n++;
      }
      if (R.n >= Q.n) b.ru = null;
    }
    if (b.sp) {                                                  // 喷：dur 秒里每秒 rate 团雾从手上喷向落点，雾头到了之后每 tick 秒算一下
      const S = b.sp, Q = A.spray; S.t += dt; S.e += dt * Q.rate;
      const P = place(), h = handPt(P), tg = o.aim(S.u);
      while (S.e >= 1 && S.t <= Q.dur) {
        S.e -= 1;
        if (!tg) continue;
        const a = Math.atan2(tg[1] - h[1], tg[0] - h[0]) + rnd(-1, 1) * (Q.spread || 0.12), d = Math.hypot(tg[0] - h[0], tg[1] - h[1]);
        const v = d / (Q.T || 0.3) * rnd(0.85, 1.1), T = Q.T || 0.3, p2 = [h[0] + Math.cos(a) * v * T, h[1] + Math.sin(a) * v * T];
        /* 雾团：前 T 秒沿 h → p2 飞（前排直线，后排翻过主角头顶），之后顺着切线飘、减速散开 */
        shots.push({ kind: 'puff', x: h[0], y: h[1], p0: h, c: over(h, p2, (h[1] + p2[1]) / 2, (Q.r || 14) * 2.8), p2, T, vx: 0, vy: 0, t: 0, life: T * rnd(1.3, 1.8), j: Math.random() });
      }
      if (tg && S.t >= (Q.T || 0.3) + S.h * Q.tick && S.t <= Q.dur + (Q.T || 0.3)) {
        if (S.h === 0 || !o.onSplash) hit(tg[0], tg[1]); else o.onSplash(tg[0], tg[1]);
        if (S.h === 0) mark();
        S.h++;
      }
      if (S.t > Q.dur + (Q.T || 0.3)) b.sp = null;
    }
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

  /* 气功波（悟空）：手心聚一团水光（charge 秒，越聚越大）→ 一束水光轰过去（fire 秒，光头伸到脸上那一下打中、之后每 drip 秒溅一下（beamTick））→ 歇 rest 秒 */
  function stepBeam(dt, on) {
    if (!b.bm) { if (!on) return; b.bm = { ph: 'rest', t: rnd(0, 0.3), dr: 0, u: 0.5 }; }
    const S = b.bm, B = A.beam;
    S.t += dt;
    if (S.ph === 'rest') { if (on && S.t >= B.rest && room(0)) { S.ph = 'charge'; S.t = 0; } return; }
    if (S.ph === 'charge') {
      b.lean = -F * TRIO.lean.wind * 0.6 * Math.min(1, S.t / B.charge);
      if (S.t >= B.charge) { S.ph = 'fire'; S.t = 0; S.dr = 0; S.hit = false; S.u = rnd(0.1, 0.8); b.lean = 0; b.snap = F * TRIO.lean.snap; }
      return;
    }
    beamTick(S, dt);
    if (S.t >= B.fire) { S.ph = 'rest'; S.t = 0; if (!on) b.bm = null; }
  }

  /* 光束开轰（fire 阶段，S.t 从 0 起）：前 reach 秒光头从手伸到脸上（drawBeam 同一个 e），伸到那一刻才打中；之后每 drip 秒溅一下。
     打中挂着爆点和顿帧，顿帧冻的是逻辑时钟（S.t 一起停）—— 开轰那一刻就打中的话，光束被冻在长度 0、爆点先于光束出现在脸上 */
  const beamReach = () => A.beam.reach || 0.08;
  function beamTick(S, dt) {
    if (!S.hit) { if (S.t < beamReach()) return; S.hit = true; S.dr = 0; const tg = o.aim(S.u); if (tg) hit(tg[0], tg[1]); return; }
    if ((S.dr += dt) >= A.beam.drip) { S.dr -= A.beam.drip; const tg = o.aim(S.u); if (tg && o.onSplash) o.onSplash(tg[0], tg[1]); }
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
    if (EK === 'rope') drawSling(ctx, P);
    ctx.save();
    if (P.rot) { ctx.translate(P.rc[0], P.rc[1]); ctx.rotate(P.rot); ctx.translate(-P.rc[0], -P.rc[1]); }
    if (P.spin) { ctx.translate(P.sc[0], P.sc[1]); ctx.rotate(P.spin); ctx.translate(-P.sc[0], -P.sc[1]); }
    if (SH) {
      const fn = frameName(), T = TRIO.T, se = TE + b.stay, [ax, ay] = P.at(cfg.anchor);
      if (cfg.ropes) drawSwing(ctx, P, fn);
      if (EK === 'drop') drawLine(ctx, P);
      /* 离场掉头（exit.flip）：绕锚点左右翻过来，走出去是背朝她 / 他走的 */
      if (b.t > se && cfg.exit && cfg.exit.flip) { ctx.translate(ax, 0); ctx.scale(-1, 1); ctx.translate(-ax, 0); }
      /* 原地出现：淡入、由小弹大（从一条线后面升上来的按那条线剪掉线以下）；离场反过来 */
      const ap = EK === 'appear' ? appearK() : 1;
      if (EK === 'appear') {
        ctx.globalAlpha *= Math.min(1, ap * 1.6);
        /* 升上来的：只在升 / 降的时候剪，线默认在人的最低点（锚点往下 texH − anchor.y），在场不剪 */
        if (E.rise && (b.t < TE || b.t > se)) { const [, cy] = P.at([0, E.cut != null ? E.cut : texH()]); ctx.beginPath(); ctx.rect(-1e4, -1e4, 3e4, 1e4 + cy - P.dy); ctx.clip(); }   // 线不跟着人升（- dy）
        else { const z = 0.8 + 0.2 * backOut(ap); ctx.translate(ax, ay); ctx.scale(z, z); ctx.translate(-ax, -ay); }
      }
      /* 呼吸 + 挤压：绕锚点竖向胀缩（横向反着补 breathe[2] 份，默认 0.4，体积不变；趴着的人给 0 —— 不然贴地的脚跟着左右挪）。
         只在待着的时候呼吸，进场离场不呼吸 */
      const br = cfg.idle.breathe;
      let k = b.sq;
      if (br && b.t >= TE && b.t <= TE + b.stay) k -= br[0] * Math.sin(b.t * 6.2832 * br[1] + b.ph);
      ctx.translate(ax, ay); ctx.scale(1 + k * (br && br[2] != null ? br[2] : 0.4), 1 - k); ctx.translate(-ax, -ay);
      drawParts(ctx, P, fn, -1);
      const pk = A.kind === 'punch' && punchK() > 0.001;
      if (pk) clipFist(ctx, P, x0, y0);                        // 出拳：拳头那一块不画在原处（drawOver 画在伸出去的地方）
      drawFrame(ctx, P, fn);
      if (pk) ctx.restore();
      drawParts(ctx, P, fn, 1);
      if (b.ammo && A.hold && A.hold[fn]) drawHeld(ctx, P, fn);
      ctx.restore();
      if (EK === 'appear' && E.fx && ap < 1) appearFx(ctx, P, ap);
      return;
    }
    if (cfg.ropes) drawRopes(ctx, P);
    const pk = A.kind === 'punch' && punchK() > 0.001;
    if (pk) clipFist(ctx, P, x0, y0);                      // 出拳时拳头那一块不画在原处（drawOver 画在伸出去的地方）
    ctx.drawImage(img, x0, y0, img.width * P.s, img.height * P.s);
    if (pk) ctx.restore();
    ctx.restore();
  }
  function clipFist(ctx, P, x0, y0) {
    const [fx0, fy0, fx1, fy1] = A.fist;
    ctx.save(); ctx.beginPath();
    ctx.rect(x0 - 1e4, y0 - 1e4, 3e4, 3e4);
    ctx.rect(x0 + fx1 * P.s, y0 + fy0 * P.s, (fx0 - fx1) * P.s, (fy1 - fy0) * P.s);   // 反向的矩形：挖掉
    ctx.clip('evenodd');
  }
  /* 原地出现显形到几成（0 没有 → 1 全出来）：进场 0 → 1（前 fade 秒），离场反过来 */
  function appearK() {
    const se = TE + b.stay, fa = E.fade || 0.35;
    return b.t < TE ? Math.min(1, b.t / fa) : b.t > se ? Math.max(0, 1 - (b.t - se) / Math.min(TX, fa)) : 1;
  }
  /* 出现时的特效（画在人之上）：flash 一圈亮光 + 八道光芒；smoke 一圈烟团往外散（钻出、阴影一闪）。颜色 E.color */
  function appearFx(ctx, P, ap) {
    const [cx, cy] = P.sc, c = E.color || [255, 240, 180], R = Math.max(texW(), texH()) * P.s * 0.55, a = 1 - ap;
    ctx.save();
    if (E.fx === 'flash') {
      const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * (0.6 + ap));
      g.addColorStop(0, `rgba(255,255,255,${a})`); g.addColorStop(0.35, `rgba(${c[0]},${c[1]},${c[2]},${0.8 * a})`); g.addColorStop(1, `rgba(${c[0]},${c[1]},${c[2]},0)`);
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, R * (0.6 + ap), 0, 6.2832); ctx.fill();
      ctx.globalAlpha = a; ctx.fillStyle = '#fff'; ctx.translate(cx, cy); ctx.rotate(ap * 0.8); star4(ctx, R * (0.9 + ap), R * 0.05);
      ctx.rotate(Math.PI / 4); star4(ctx, R * (0.5 + ap * 0.6), R * 0.04);
    } else {
      for (let i = 0; i < 9; i++) {
        const q = i * 0.698 + b.ph, d = R * (0.25 + 0.7 * ap), r = R * (0.22 + 0.25 * ap) * (0.8 + 0.4 * ((i * 7) % 3) / 2);
        ctx.globalAlpha = 0.75 * a; ctx.fillStyle = `rgb(${c[0]},${c[1]},${c[2]})`;
        ctx.beginPath(); ctx.arc(cx + Math.cos(q) * d, cy + Math.sin(q) * d * 0.8 + R * 0.25, r, 0, 6.2832); ctx.fill();
      }
    }
    ctx.restore();
  }
  /* 倒挂垂下的丝 / 绳：从 enter.line（贴图上系住的点，默认 pivot 正下方的脚）一直拉到绳顶（pivot 那么高，画外），跟人一起荡 */
  function drawLine(ctx, P) {
    const L = E.line || [cfg.pivot[0], 0], a = P.at(L), c = P.at([L[0], cfg.pivot[1]]);
    ctx.lineCap = 'round';
    for (const [w, col] of [[(E.w || 3) + 2, E.edge || 'rgba(60,60,70,.7)'], [E.w || 3, E.fill || '#f2f2f2']]) {
      ctx.strokeStyle = col; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(c[0], c[1]); ctx.stroke();
    }
  }
  /* 横绳：ends 两个屏幕点之间一根绳，被人压在 enter.touch（贴图上压着绳的点）那里往下坠成两段弧；画在人之下 */
  function drawSling(ctx, P) {
    const [e0, e1] = E.ends, m = pt(P, E.touch), sag = (E.sag || 18);
    ctx.save(); ctx.lineCap = 'round';
    for (const [w, col] of [[(E.w || 6) + 3, E.edge || 'rgba(70,45,20,.85)'], [E.w || 6, E.fill || '#e9dcc0']]) {
      ctx.strokeStyle = col; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(e0[0], e0[1]);
      ctx.quadraticCurveTo((e0[0] + m[0]) / 2, Math.max(e0[1], m[1]) + sag, m[0], m[1]);
      ctx.quadraticCurveTo((m[0] + e1[0]) / 2, Math.max(e1[1], m[1]) + sag, e1[0], e1[1]); ctx.stroke();
    }
    ctx.restore();
  }
  /* 画图集里的一帧。flex 区域不在原处画，按条带错位重画：钉住的那一边（'t' 顶 / 'b' 底 / 'l' 左 / 'r' 右）位移为 0、越往外越大（r^1.5），
     相位沿条带往外滞后一点（r × 1.6），读成挂着的东西在晃而不是整块平移。区域四周除了钉住那边都必须是透明的，不然错位会撕开。
     钉右 / 钉底是给朝右的闺蜜：拖在身后（左边）的头发、飘带挂在右边，翘起来的脚、往上飘的东西根在底边 */
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
      /* 横条（钉上 / 下边，条带左右错位）或竖条（钉左 / 右边，上下错位）；r = 离钉住那边多远（0 ~ 1） */
      if (pin === 't' || pin === 'b') for (let y = by0; y < by1; y += ST) {
        const h = Math.min(ST, by1 - y), m = (y + h / 2 - by0) / (by1 - by0), d = off(pin === 't' ? m : 1 - m);
        ctx.drawImage(img, sx0 + bx0, sy0 + y, bx1 - bx0, h, x0 + (bx0 + d) * s, y0 + y * s, (bx1 - bx0) * s, h * s + 0.6);
      } else for (let x = bx0; x < bx1; x += ST) {
        const w = Math.min(ST, bx1 - x), m = (x + w / 2 - bx0) / (bx1 - bx0), d = off(pin === 'l' ? m : 1 - m);
        ctx.drawImage(img, sx0 + x, sy0 + by0, w, by1 - by0, x0 + x * s, y0 + (by0 + d) * s, w * s + 0.6, (by1 - by0) * s);
      }
    }
  }
  /* 挂件层：这一帧挂在 at[帧] 那一点、先转到帧上写的角度，再按 sway 甩（正弦 + 跟着秋千的摆往后拖，rad）。z 选画在人后还是人前 */
  function drawParts(ctx, P, fn, z) {
    PARTS.forEach((q, i) => {
      const im = partImg[i], a = q.at[fn];
      if (!im || !a || (q.z || 1) !== z) return;
      /* 跟摆：身子（秋千 / 荡）以角速度 P.w 转，挂着的东西跟不上，相对身子往反方向拖 */
      const sw = q.sway || [0, 0, 0], ang = a[2] + sw[0] * Math.sin(b.t * 6.2832 * sw[1] + b.ph) - (sw[2] || 0) * P.w;
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
    if (A.tether && b && b.wait <= 0 && img) drawTether(ctx);
    for (const s of shots) drawShot(ctx, s);
    const f = o.face();
    for (const m of marks) drawMark(ctx, m, f);
    if (!b || b.wait > 0 || !img) return;
    if (A.kind === 'punch' && punchK() > 0.001) drawArm(ctx);
    if (A.kind === 'beam' && b.bm && b.bm.ph !== 'rest') drawBeam(ctx);
    if (b.wh) drawWhip(ctx);
  }

  /* 抽打：手 → 落点一根软的长条（鞭、红绸、铃索、链子），甩出去时沿着它有一道波往前走、中段往下坠，末端可挂一截硬的（tip：棍 / 铃 / 剑尖）。
     A.whip { w 粗, taper 末端细到几成, amp 波幅 px, waves 几道波, hz, color, edge, tip: [长, 粗, 颜色] } */
  function drawWhip(ctx) {
    const W = b.wh, Ph = A.phases, Q = A.whip, P = place(), h = handPt(P), tg = o.aim(W.u) || h, t = W.t;
    const e = t < Ph[0] ? easeOut(t / Ph[0]) : t < Ph[0] + Ph[1] ? 1 : 1 - Math.pow(Math.min(1, (t - Ph[0] - Ph[1]) / Ph[2]), 2);
    const dx = tg[0] - h[0], dy = tg[1] - h[1], L = Math.hypot(dx, dy) || 1, nx = -dy / L, ny = dx / L, N = 22;
    /* 鞭身沿 h → tg 的中线甩出去（前排中线是直的、往下垂 sag；后排中线翻过主角头顶，不垂） */
    const c = over(h, tg, (h[1] + tg[1]) / 2, (Q.amp || 24) * 1.2 + (Q.w || 8) * P.s), arch = c[1] < (h[1] + tg[1]) / 2 - 1;
    const pts = [];
    for (let i = 0; i <= N; i++) {
      const f = i / N, w = Math.sin(Math.PI * f) * (Q.amp || 24) * (1.2 - e) * Math.sin(6.2832 * (f * (Q.waves || 1.5) - t * (Q.hz || 4)));
      const sag = arch ? 0 : Math.sin(Math.PI * f) * L * 0.08 * (1 - e * 0.6), [mx, my] = arch ? bez(h, c, tg, f * e) : [h[0] + dx * f * e, h[1] + dy * f * e];
      pts.push([mx + nx * w, my + ny * w + sag]);
    }
    ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (const [grow, col] of [[4, Q.edge || 'rgba(40,20,10,.85)'], [0, Q.color || '#c0302a']]) {
      ctx.strokeStyle = col;
      for (let i = 0; i < N; i++) {
        ctx.lineWidth = (Q.w || 8) * P.s * (1 - (1 - (Q.taper != null ? Q.taper : 0.5)) * i / N) + grow;
        ctx.beginPath(); ctx.moveTo(pts[i][0], pts[i][1]); ctx.lineTo(pts[i + 1][0], pts[i + 1][1]); ctx.stroke();
      }
    }
    if (Q.tip) {                                                   // 末端那一截硬的，顺着最后一段的方向
      const [tl, tw, tc] = Q.tip, a = pts[N], c = pts[N - 2], ang = Math.atan2(a[1] - c[1], a[0] - c[0]);
      ctx.translate(a[0], a[1]); ctx.rotate(ang);
      ctx.lineWidth = tw * P.s + 4; ctx.strokeStyle = Q.edge || 'rgba(40,20,10,.85)'; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(tl * P.s, 0); ctx.stroke();
      ctx.lineWidth = tw * P.s; ctx.strokeStyle = tc; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(tl * P.s, 0); ctx.stroke();
      ctx.lineWidth = tw * P.s * 0.3; ctx.strokeStyle = 'rgba(255,255,255,.45)'; ctx.beginPath(); ctx.moveTo(tl * P.s * 0.15, -tw * P.s * 0.2); ctx.lineTo(tl * P.s * 0.85, -tw * P.s * 0.2); ctx.stroke();
    }
    ctx.restore();
  }
  /* 带线的东西（鼠标、流星锤）：手 → 飞出去的那个东西之间一根线，飞的时候绷直、弹开时松下来往下坠。A.tether { w, color } */
  function drawTether(ctx) {
    const P = place(), h = holdPt(P), Q = A.tether;
    ctx.save(); ctx.lineCap = 'round';
    for (const s of shots) {
      if (!onLine(s)) continue;
      const d = Math.hypot(s.x - h[0], s.y - h[1]), slack = s.fall != null ? d * 0.25 : d * 0.06, c = over(h, [s.x, s.y], Math.max(h[1], s.y) + slack, Q.w || 2.5);
      ctx.strokeStyle = Q.color || '#222'; ctx.lineWidth = Q.w || 2.5;
      ctx.beginPath(); ctx.moveTo(h[0], h[1]); ctx.quadraticCurveTo(c[0], c[1], s.x, s.y); ctx.stroke();
    }
    ctx.restore();
  }

  function drawShot(ctx, s) {
    if (s.kind === 'ghost') { drawGhost(ctx, s); return; }
    if (s.kind === 'slash') { drawSlash(ctx, s); return; }
    if (s.kind === 'puff') {
      const Q = A.spray, c = Q.color, u = s.t / s.life, r = (Q.r || 14) * (0.8 + 2.6 * u);   // 越飞越大：一股雾是个锥
      const g = ctx.createRadialGradient(s.x, s.y, 0, s.x, s.y, r);
      g.addColorStop(0, `rgba(255,255,255,${0.5 * (1 - u)})`); g.addColorStop(0.35, `rgba(${c[0]},${c[1]},${c[2]},${0.8 * (1 - u)})`); g.addColorStop(1, `rgba(${c[0]},${c[1]},${c[2]},0)`);
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(s.x, s.y, r, 0, 6.2832); ctx.fill();
      return;
    }
    const a = s.stuck != null ? Math.min(1, ((A.stick || 2.2) - s.stuck) / 0.4) : s.fall != null ? Math.min(1, s.fall / 0.3) : 1;
    ctx.save(); ctx.globalAlpha = a; ctx.translate(s.x, s.y);
    if (s.kind === 'photo') { drawPhoto(ctx, s); ctx.restore(); return; }
    if (s.kind === 'heart') { ctx.rotate(s.ang * 0.1); drawHeart(ctx, 22 + 6 * Math.sin(s.t * 18), A.color); ctx.restore(); return; }
    if (atlas) { drawAtlas(ctx, s.ang, A.r); ctx.restore(); return; }                      // 有 3D 转盘图集就走图集，item 只是名字（命中反馈、带线认它）
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

  /* 连打的残影：从手冲到落点，一路拖三道越来越淡的影子；影子是出手帧里的一块（A.rush.ghost { frame, box }，拳头 / 腿 / 棍） */
  function drawGhost(ctx, s) {
    if (!s.p2) return;
    const Q = A.rush, G = Array.isArray(Q.ghost) ? Q.ghost[s.i % Q.ghost.length] : Q.ghost, [bx0, by0, bx1, by1] = G.box, i = SH.names.indexOf(G.frame), [cw, ch] = SH.cell;
    const sx = (i % SH.cols) * cw + bx0, sy = Math.floor(i / SH.cols) * ch + by0, sc = (b ? b.at : cfg.at)[2] * (G.z || 1.1), w = (bx1 - bx0) * sc, hh = (by1 - by0) * sc;
    const e = easeOut(Math.min(1, s.t / s.T)), fade = s.t > s.T ? 1 - (s.t - s.T) / 0.14 : 1;
    const p2 = [s.p2[0] + s.j * 18, s.p2[1] + s.j * 14], c = over(s.p0, p2, (s.p0[1] + p2[1]) / 2, Math.max(w, hh) / 2);   // 前排是直线（控制点在中点），后排翻过主角头顶；残影是横着的长条，半径按长边
    ctx.save();
    for (let k = 3; k >= 0; k--) {
      const q = Math.max(0, e - k * 0.12), [x, y] = bez(s.p0, c, p2, q);
      ctx.globalAlpha = Math.max(0, fade) * (k ? 0.22 / k : 0.8);
      ctx.drawImage(img, sx, sy, bx1 - bx0, by1 - by0, x - w / 2, y - hh / 2, w, hh);
    }
    if (s.t < s.T + 0.06) {                                        // 速度线
      ctx.globalAlpha = 0.6 * Math.max(0, fade); ctx.strokeStyle = Q.line || '#fff'; ctx.lineWidth = 2;
      const [x, y] = bez(s.p0, c, p2, e), a = bezDir(s.p0, c, p2, e);
      for (let k = -1; k <= 1; k++) { ctx.beginPath(); ctx.moveTo(x - Math.cos(a) * 60 + k * 8 * Math.sin(a), y - Math.sin(a) * 60 - k * 8 * Math.cos(a)); ctx.lineTo(x - Math.cos(a) * 15, y - Math.sin(a) * 15); ctx.stroke(); }
    }
    ctx.restore();
  }
  /* 斩痕：落点上一道月牙形弧光，0.07 秒从一头划到另一头，停一下淡掉。A.slash { n, gap, len, w, color, ang, spread } */
  function drawSlash(ctx, s) {
    if (s.t < 0 || !s.p) return;
    const Q = A.slash, c = Q.color, R = Q.len / 2, life = Q.life || 0.45, draw = Math.min(1, s.t / 0.07), fade = Math.min(1, (life - s.t) / (life * 0.5));
    ctx.save(); ctx.translate(s.p[0], s.p[1]); ctx.rotate(s.ang); ctx.globalAlpha = Math.max(0, fade);
    const a0 = -0.9, a1 = a0 + 1.8 * draw;
    /* 深色托底一圈（亮底图 + 命中爆点上，光靠亮色读不出来，skill chashouji-fx：实体靠轮廓）→ 外晕 → 本色 → 白芯 */
    for (const [w, col] of [[Q.w * 1.35, 'rgba(15,30,70,.55)'], [Q.w * 2.2, `rgba(${c[0]},${c[1]},${c[2]},.35)`], [Q.w, `rgba(${c[0]},${c[1]},${c[2]},.95)`], [Q.w * 0.35, 'rgba(255,255,255,1)']]) {
      ctx.fillStyle = col; ctx.beginPath();                          // 月牙：外弧 R、内弧往里收 w（两头尖）
      ctx.arc(0, R * 0.4, R, a0 - Math.PI / 2, a1 - Math.PI / 2);
      ctx.arc(0, R * 0.4 + w, R - w * 0.2, a1 - Math.PI / 2, a0 - Math.PI / 2, true);
      ctx.closePath(); ctx.fill();
    }
    ctx.restore();
  }

  /* 橡皮手臂：腕 → 拳头一截肉色管子，伸的时候往下垂一点、弹回时来回甩（二次曲线，控制点沿垂直方向偏 sag）；
     三遍画：深色描边 → 肉色 → 贴上沿一条亮光（只画一条直的肉色粗线读成木棍） */
  function drawArm(ctx) {
    const P = place(), k = punchK(), s = P.s;
    const wr = pt(P, A.wrist), fr = pt(P, A.fistC), tg = o.aim(0) || fr;
    const fz = (A.fist[3] - A.fist[1]) * s * A.fistZ / 2;             // 拳头半高
    const [fx, fy] = bez(fr, over(fr, tg, (fr[1] + tg[1]) / 2, fz), tg, k);    // 拳头走的路：前排直线，后排翻过主角头顶
    const len = Math.hypot(fx - wr[0], fy - wr[1]), nx = -(fy - wr[1]) / (len || 1), ny = (fx - wr[0]) / (len || 1);
    const wob = b.pk.t < A.phases[0] + A.phases[1] ? 0.08 : 0.16 * Math.sin(b.pk.t * 38);
    const sag = len * wob * (ny < 0 ? -1 : 1);                          // 往下垂（法线取朝下的那一边）
    let cx = (wr[0] + fx) / 2 + nx * sag, cy = (wr[1] + fy) / 2 + ny * sag;
    const up = over(wr, [fx, fy], cy, A.armW * s); if (up[1] < cy) [cx, cy] = up;   // 后排：管子往上拱过主角的头
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
    const fi = SH ? SH.names.indexOf(A.seq[FI][0]) : 0, ox = SH ? (fi % SH.cols) * SH.cell[0] : 0, oy = SH ? Math.floor(fi / SH.cols) * SH.cell[1] : 0;   // 帧序列：拳头从出手帧那一格抠
    ctx.drawImage(img, ox + fx0, oy + fy0, fx1 - fx0, fy1 - fy0, (fx0 - c[0]) * z, (fy0 - c[1]) * z, (fx1 - fx0) * z, (fy1 - fy0) * z);
    ctx.restore();
  }

  function drawBeam(ctx) {
    const P = place(), S = b.bm, B = A.beam, h = S.ph === 'charge' ? holdPt(P) : handPt(P);   // 蓄力球跟着蓄力帧的手，放出去从出手点
    ctx.save(); ctx.globalCompositeOperation = 'source-over';
    if (S.ph === 'charge') {
      const r = B.ball * (0.3 + 0.7 * Math.min(1, S.t / (SH ? LEAD : B.charge))) * (1 + 0.08 * Math.sin(S.t * 40));
      orb(ctx, h[0], h[1], r, B);
    } else {
      const tg = o.aim(S.u);
      if (tg) {
        const e = Math.min(1, S.t / beamReach()), fade = Math.min(1, (B.fire - S.t) / 0.15), x1 = lerp(h[0], tg[0], e), y1 = lerp(h[1], tg[1], e);
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
    } else if (m.kind === 'text') {                         // 连打的喊声字（"啊哒"）：在头顶一侧弹出来、抖、淡掉
      const pop = backOut(Math.min(1, m.t / 0.15)), sz = Math.max(40, f[2] * 1.3) * pop;
      ctx.globalAlpha = 1 - Math.max(0, (u - 0.6) / 0.4);
      ctx.translate(f[0] + (0.8 + 0.3 * m.j) * f[2] * -F, f[1] - f[2] * 2.6);   // 头顶斜上方、往喊的人那边偏（命中的闪光在脸上，别压着） ctx.rotate(-0.15 + m.j * 0.1 + Math.sin(m.t * 60) * 0.03 * (1 - u));
      ctx.font = `900 ${Math.max(1, sz)}px system-ui, sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.lineWidth = sz * 0.18; ctx.strokeStyle = 'rgba(30,10,0,.95)'; ctx.strokeText(m.s, 0, 0);
      ctx.fillStyle = '#ffd21a'; ctx.fillText(m.s, 0, 0);
    } else if (m.kind === 'net') {                          // 网兜：从上面罩下来扣在头上，网眼随着晃
      const drop = easeOut(Math.min(1, m.t / 0.18)), R = f[2] * 1.5, w = Math.sin(m.t * 8) * 0.12 * Math.exp(-m.t * 2);
      ctx.globalAlpha = Math.min(1, (m.life - m.t) / 0.3);
      ctx.translate(f[0], f[1] - f[2] * 0.3 - (1 - drop) * f[2] * 3); ctx.rotate(m.a * 0.3 + w);
      ctx.save(); ctx.beginPath(); ctx.ellipse(0, 0, R, R * 1.05, 0, 0, 6.2832); ctx.clip();
      ctx.strokeStyle = 'rgba(245,238,215,.95)'; ctx.lineWidth = 2.2;
      for (let k = -6; k <= 6; k++) {
        ctx.beginPath(); ctx.moveTo(k * R / 3 - R, -R); ctx.lineTo(k * R / 3 + R, R); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(k * R / 3 + R, -R); ctx.lineTo(k * R / 3 - R, R); ctx.stroke();
      }
      ctx.restore();
      ctx.strokeStyle = 'rgba(90,60,30,.95)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.ellipse(0, R * 0.55, R * 0.95, R * 0.3, 0, 0, 6.2832); ctx.stroke();
    } else if (m.kind === 'ice') {                          // 冻住：一层半透明冰壳包住头，脸从冰里透出来
      /* 整块冰先不透明地画到离屏画布上，再整体按 ≤ 0.5 贴上去 —— 各层分开半透明画的话，霜边、高光叠在填色上会叠到 0.7 */
      const r = f[2], R = r * 2.2, grow = easeOut(Math.min(1, m.t / 0.15));   // 0.15 秒从脸中间结出来
      if (!iceBuf) iceBuf = document.createElement('canvas');
      const S = Math.ceil(2 * R); if (iceBuf.width !== S) { iceBuf.width = S; iceBuf.height = S; }
      const g = iceBuf.getContext('2d'), cx = R, cy = R - r * 0.2;
      g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, S, S);
      const shell = (k) => {                                  // 冰壳：九边的不规则冰块（棱角 = 冰，不是气泡），k 往里缩
        g.beginPath();
        for (let i = 0; i < 9; i++) {
          const a = i * 0.6981 + m.j, q = (1 + 0.12 * Math.sin(m.j * 3 + i * 2.3)) * grow * k;
          g[i ? 'lineTo' : 'moveTo'](cx + Math.cos(a) * r * 1.35 * q, cy + Math.sin(a) * r * 1.5 * q);
        }
        g.closePath();
      };
      const lg = g.createLinearGradient(cx - r, cy - r * 1.5, cx + r, cy + r * 1.5);
      lg.addColorStop(0, 'rgba(230,250,255,.8)'); lg.addColorStop(1, 'rgba(120,195,245,.6)');
      g.fillStyle = lg; shell(1); g.fill();
      g.lineJoin = 'round'; g.strokeStyle = '#2370b4'; g.lineWidth = 3; shell(1); g.stroke();                       // 冰块外沿（亮底图上要靠轮廓）
      g.setLineDash([5, 6]); g.strokeStyle = '#fff'; g.lineWidth = 2; shell(0.86); g.stroke(); g.setLineDash([]);   // 霜边
      g.lineCap = 'round'; g.lineWidth = 4;                                                                        // 左上两道高光
      for (const [a0, a1, k] of [[3.5, 4.1, 0.72], [3.3, 3.55, 0.55]]) { g.beginPath(); g.ellipse(cx, cy, r * 1.35 * k * grow, r * 1.5 * k * grow, 0, a0, a1); g.stroke(); }
      g.fillStyle = '#c8f0ff'; g.strokeStyle = '#2370b4'; g.lineWidth = 1.5;                                      // 下沿挂四根冰棱
      for (let i = 0; i < 4; i++) {
        const x = cx + (i - 1.5) * r * 0.45, y = cy + r * 1.3 * grow * (1 - Math.abs(i - 1.5) * 0.12), L = r * (0.35 + 0.2 * ((i * 7 + Math.floor(m.j * 3)) % 3) / 2) * grow;
        g.beginPath(); g.moveTo(x - 5, y); g.lineTo(x, y + L); g.lineTo(x + 5, y); g.closePath(); g.fill(); g.stroke();
      }
      ctx.globalAlpha = 0.5 * Math.min(1, (m.life - m.t) / 0.5);                                                  // 最后半秒化开
      ctx.drawImage(iceBuf, f[0] - R, f[1] - R);
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
    return [{ s: b.depth, draw: drawBody }];
  }
  /* 此刻在哪一段：wait 等着上 / enter 进场 / on 在场 / exit 离场（胶片标格用：出手中途离场这种冲突只看帧名分不出来） */
  const phase = () => (!b ? null : b.wait > 0 ? 'wait' : b.t < TE ? 'enter' : b.t <= TE + b.stay ? 'on' : 'exit');
  return { init, load, summon, update, items, drawOver, active, busy, reset, peek: () => (b ? [b] : []), frame: () => (b && SH ? frameName() : null), phase, cfg };
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
  const who = (id, slot) => (id == null ? null : id in data.ground ? { m: ground, sk: data.ground[id], slot } : acts[id] ? { m: acts[id], slot } : null);
  const groups = data.groups.map((g, i) => ({ no: i + 1, name: g.name, mem: ['ground', 'top', 'floor'].map(k => who(g[k], k)).filter(Boolean) }));
  const ready = groups.filter(g => g.mem.length);
  const all = [ground, ...Object.values(acts)];
  /* cur 第一组；extra 第二次送时叠上来的人 [{ m, sk, slot, b }]；一个人在场 = 他那一趟的 b 还在 m 里。
     滑板哥们 / 平衡车闺蜜两个人同在一份 Crew 里，只能按 b 分，不能看 m.active() */
  let cur = null, extra = [];
  const live = (x) => !!x.b && x.m.peek().includes(x.b);
  const come = (x, wait, slot) => { const b = x.m.summon(x.sk, wait, slot); if (b) x.b = b; };
  /* 续：Act 在场 / 离场中再 summon 就是续 / 叫回；Crew 按这个人续（同一份 Crew 里另一个人不动），他已经在走就让他走 ——
     这时 Crew.summon 满员会去续另一个人，不会把他叫回来。下一次送他不在场了，按第一组走掉的人叫回来 */
  const stay = (x) => (x.m.extend ? x.m.extend(x.b) : x.m.summon(x.sk));
  const stagger = () => [...TRIO.STAGGER].sort(() => Math.random() - 0.5);
  /* 从别的组里挑 n 个能上场的人补位，返回 [{ m, sk, slot, pos }]（pos 1 = 自己的 at，2 = 备用位）。
     每个槽位最多 CAP 个站位，被在场的人（on）占掉的不能再用；Crew 的人各占一个后排站位（Crew 自己挑没人的那一排）。
     组按随机顺序、组内按 PREFER 挑 —— 先把一组挑够再看下一组，读起来是"又来了一组"。
     这个人此刻不能已经在场；Crew 还要有空位、形象跟场上的不重复 */
  function pickExtra(on, n) {
    const used = { ground: 0, top: 0, floor: 0 }, pos1 = { ground: false, top: false, floor: false };
    for (const x of on) { used[x.slot]++; if (!x.m.extend && x.pos !== 2) pos1[x.slot] = true; }
    const can = (x) => used[x.slot] < TRIO.CAP[x.slot] && (x.m.extend ? x.m.peek().length < x.m.cfg.max && !x.m.peek().some(b => b.skin === x.sk) : !x.m.active());
    const got = [];
    for (const g of [...ready].sort(() => Math.random() - 0.5)) {
      if (cur && g.no === cur.no) continue;
      for (const k of TRIO.PREFER) {
        const x = g.mem.find(y => y.slot === k);
        if (!x || got.length >= n || !can(x) || got.some(y => y.m === x.m && !x.m.extend)) continue;
        const pos = x.m.extend || !pos1[k] ? 1 : 2;
        if (pos === 1 && !x.m.extend) pos1[k] = true;
        used[k]++;
        got.push({ ...x, pos });
      }
    }
    return got;
  }
  const slot2 = (x) => {
    const c = x.m.cfg, [dx, dy, k] = TRIO.SLOT2[x.slot];
    return { at: [c.at[0] + c.face * dx, c.at[1] + dy, c.at[2] * k], depth: c.depth * (x.slot === 'ground' ? k : 1) };
  };
  return {
    groups, ready, all, acts: Object.values(acts),
    summon(pick) {
      if ([...(cur ? cur.mem : []), ...extra].some(live)) {
        const st = stagger();
        cur.mem.forEach((x, i) => (live(x) ? stay(x) : come(x, st[i])));   // 第一组：在场的续，走掉的叫回来
        extra = extra.filter(live);
        extra.forEach(stay);
        const on = [...cur.mem, ...extra].filter(live);
        const add = pickExtra(on, TRIO.MAX - on.length);   // 补满 MAX（叠第二组）
        add.forEach((x, i) => come(x, (i + 1) * 0.3, x.pos === 2 ? slot2(x) : null));
        extra.push(...add.filter(live));
        return;
      }
      const want = ready.find(g => g.no === +pick);
      const pool = ready.length > 1 ? ready.filter(g => !cur || g.no !== cur.no) : ready;
      const g = want || pool[Math.floor(Math.random() * pool.length)];
      extra = [];
      if (!g) { cur = null; return; }
      cur = { ...g, mem: g.mem.map(x => ({ ...x })) };       // 这一趟的 b 记在副本上，别写进组表
      const st = stagger();
      cur.mem.forEach((x, i) => come(x, st[i]));
    },
    current: () => cur,
    active: () => all.some(m => m.active()),
    reset() { all.forEach(m => m.reset()); cur = null; extra = []; },
  };
}
