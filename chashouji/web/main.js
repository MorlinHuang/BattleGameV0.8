/* 《查手机》网页版 —— 单一真源驱动。
 *
 * 三层，别混：
 *   拉力 S.fA / S.fB  礼物注入的存量，双方互相对冲，慢慢自然流失
 *   血量 S.hpA / S.hpB  **胜负只看它**：拉力差每秒按 X/M/Z 扣对方的血，归零者负
 *   对抗线 S.p（0~100）  拉力差的**当前读数**，决定手机被拽到哪 —— 它不是
 *                        积分量，对面追上来手机自己会走回去，这才是拔河
 *
 * 场景这一侧读的是 FX.pDraw = S.p + 空闲拉锯（derive 里算）。对抗线、地面
 * 分色、角色取哪一帧、手机位移，**全部读同一个 pDraw**，所以"对抗线对不上
 * 画面"在构造上仍然不可能发生。HUD 的血条读的是 S.hpA / S.hpB 真值。
 * 拉锯只进表现层：它是"双方都在使劲、谁也没占上风"的样子，不该改战况 ——
 * 让那点来回去改 S.p，观众刚刷完礼物就会看见手机往回跌。
 */
const W = 960, H = 1334;
const TOP = 128, BOT = 1232, MID = 480;
const FRAME_TOP = 308, FRAME_W = 960, FRAME_H = 900;  // 帧纹理只覆盖人物那条横带
const ROWS = 15;
const GREEN = [126, 217, 87], RED = [255, 72, 72];

const P = {
  /* 进度→位移的曲线，**线性**：每涨一个百分点，手机走同样远。
     曾经是 1.55（中段慢、末段快），那跟下面那段注释写的设计意图正好是反的 ——
     中段姿态差别本来就小、全指望平移补，而 1.55 把中段压得最扁：p 从 50 走到
     60 手机一共只动 9px，在 960 宽的画面上等于没动，观众看到的是比赛最长的
     那一段画面静止。两头反倒是姿态已经够夸张、最不缺平移的地方。
     改成 1.0 之后同样 50→60 走 30px，而两头的行程一点没少。 */
  curve: 1.0,
  /* 关键帧本身已经把"谁被拖过去"画进姿态里了，half/drag 管的是在此之上
     整组人物平移多少：中段那几档姿态差别很小，全靠这段平移把"手机正在被
     拽走"读出来；两头则相反 —— 姿态已经够夸张，再平移就该出画了。
     half 从 108 提到 150 是量过的：p=0/100 两格里人物组离画框还剩 100px 以上。
     drag 同步从 0.58 收到 0.55，角色的最大平移 63→82px，吃掉其中 19px，
     余量仍有 80px；多出来的行程留给手机自己走。 */
  half: 150,       // 对抗线最大偏移
  drag: 0.55,      // 角色整体跟随对抗线的比例
  /* 空闲拉锯的幅度，单位是**进度的百分点**。见 derive 里的 FX.pDraw。 */
  sway: 5,
  tilt: 1.55, bulge: 46, linkW: 0.80, shapeRate: 2.6,
  phoneY: 560,     // 对抗线上"手机所在高度"，气泡与辉光的锚
  rug: { top: 738, bot: 1128, tl: 88, tr: 872, bl: 28, br: 912 },  // 底版里地毯四角

  /* 挨一下之后的反应。冲击沿对抗线传播、角色被推开又弹回，两件事各有一套
     参数：线是软的（传得快、留得久），人是硬的（推得动、马上站回来）。 */
  waveSpread: 7.0,   // 冲量向相邻行传播的速率
  waveDecay: 0.945,  // 冲量每帧的留存；再高线会晃到一秒开外，像被风吹着
  hitK: 620,         // 角色回中的弹力
  hitDamp: 0.90,     // 角色横向速度的阻尼
  punchDecay: 0.88,  // 缩放脉冲的衰减
  tintDecay: 0.82,   // 染色的衰减
};

/* 数值参数表 —— 整局的手感全在这十来个数上，集中一处方便手改。
   模型是**两层**的：礼物注入的是"拉力"，双方拉力互相对冲，**只有差值**
   才扣血、才拽得动手机。两边拉力相等时刷得再凶也谁都不掉血、手机停在中间
   —— 那正是拔河该有的样子，也是这个玩法最长的一段时间。
   （错误的做法是让礼物直接扣血：那样没有对冲、先刷的人白刷、一次爆发就能
   结束比赛。） */
const NUM = {
  /* BURN / LOSS / HP_Z 是**同一根时间轴**上的刻度，改一个必须三个一起按同样
     倍数改，否则动的就不只是快慢，还有谁赢谁输：稳态拉力差 = Δ注入 / LOSS，
     三个同乘 k 之后差值 ÷k 而每点差的伤害 ×k，正好抵消。
     曾经是 0.05 / 0.012，火力的时间常数 83 秒 —— 观众刷一件「爱的爆炸③」
     出去，血条 20 秒纹丝不动，60 秒才跳 1 滴（这条是截图量出来的）。礼物的
     效果全在，只是摊得太薄，在直播间里等同于没发生。现在时间常数 25 秒。 */
  BURN: 0.165,     // 对冲系数：双方等量消耗，由火力少的一方定速
  LOSS: 0.040,     // 自然流失：势头会过去。时间常数 25 秒
  /* 稳态时  拉力差 = 注入速度差 / LOSS  —— 对冲项在两边完全相同，推导时直接
     消掉了。所以掉血的快慢只取决于"两边刷礼物的速度差"，与刷了多少总量
     无关：都在猛刷就差值小、画面激烈而谁也不掉血；一方停手就立刻开始挨打。 */

  /* ── 拉力差 → 掉血（X / M / Z）──
     公式：拉力差 > X 时，每 M 点拉力差，每秒扣对方 Z% 的血。
     X 和 M 取自《螂人杀》文档（3000 兵 ÷100、兵数 ÷100 的刻度），Z 取自
     需求里给过的例子，文档本身没写掉血速率。推导写在 battle 里。 */
  PULL_X: 30,      // 死区：拉力差没到这个数，谁也不掉血（≈1.5 个魔法镜②）
  PULL_M: 1000,    // 每这么多拉力差……
  HP_Z: 5,         // ……每秒扣对方这么多滴血（满血 100）
  /* 掉血速度的上限。拉力差是没有上限的 —— 大哥一秒注入 600 而对面只有 80 时，
     差值能到四万，折合每秒 200 滴血，半个回合都撑不过。那不叫碾压，那叫没有
     过程：观众还没看清发生了什么，比赛已经结束。10 表示再怎么碾压也要 10 秒。 */
  HP_MAX: 10,
  /* 对抗线的满幅刻度：拉力差到这么多，手机就被拽到底（p=0 或 100）。
     取 1000 是让它和上面的 M 共用一把尺 —— 手机顶到端点的那一刻，正好就是
     "每秒扣对方 Z 滴血"的那一刻，画面读数和伤害读数对得上。 */
  LINE_FULL: 1000,
  LINE_RATE: 2.2,  // 对抗线趋近拉力差的速率（时间常数 0.45 秒）

  SHOT: 9,         // 每消耗这么多火力打出一发弹幕 —— 弹幕就是火力的消耗形式
  MATCH: 720,      // 单局 12 分钟
  SUDDEN_LEAD: 35, // 血量被拉开这么多滴，持续 SUDDEN_WAIT 秒就进绝杀
  SUDDEN_WAIT: 60,
  SUDDEN: 30,      // 绝杀倒计时
  STAND_AT: 8,     // 有人掉到最后这么多滴血时触发反击时刻
  STAND: 120,      // 反击时刻时长：劣势方注入翻倍，全局只触发一次
  SHIELD_AT: 10,   // 濒死护盾：血量低于这么多滴时，火力按比例替他挡伤害
  SHIELD_MAX: 0.75,// 濒死减伤的上限：再能扛也不能扛到打不动
};

const S = {
  /* auto 默认**关**：展示时自动演示会自己来回拽手机，观众分不清哪一下是
     刷礼物推的、哪一下是演示程序推的。要看关键帧过渡时用 ?auto=1 打开。 */
  p: 50, t: 0, auto: false, line: 3,  // line: 0 全无 / 1 原发光柱 / 2 地面战线+指针 / 3 只要指针
  fA: 0, fB: 0,                       // 拉力（火力）：A=查岗党(左) B=灭迹党(右)
  hpA: 100, hpB: 100,                 // 血量：胜负只看它，归零的一方输
  dpsA: 0, dpsB: 0,                   // 此刻每秒正在掉多少血（battle 算出来的读数，HUD 画它）
  budA: 0, budB: 0,                   // 发射预算：火力消耗到一发弹幕的量就打一发
  debA: 0, debB: 0, debKA: 0, debKB: 0,  // 受到的注入减益：剩余秒数与折扣
  clock: NUM.MATCH, phase: 'idle',    // idle 不跑数值（诊断与老演示模式）/ play / sudden / over
  big: 0, sudden: 0,
  stand: 0, standUsed: false,
  winner: 0,
  overT: 0,                           // 结算已经播了几秒，入场动画与两帧循环都读它
  giftA: 0, giftB: 0,                 // 本局各送出多少件，结算那格数据用
  /* 送礼榜。网页版没有观众身份，接直播时由外部填成
     [{name, side, amt}, ...]（已按 amt 倒序），结算取前三。
     这里**不造假数据** —— 空着的时候结算画面自己会说"接入直播后显示"。 */
  board: [],
};
const FX = {
  phoneX: MID, phoneY: P.phoneY,
  pDraw: 50,                         // 画面读的进度（= S.p 叠上空闲拉锯），见 derive
  rowOff: new Array(ROWS).fill(0), rowHeat: new Array(ROWS).fill(0),
  rowImp: new Array(ROWS).fill(0),   // 冲击波，独立于常规形变
  struggle: 1, actorX: 0, jit: 0,
  busy: 0,                           // 场上还有多少火力在烧（0~1），拉锯按它让位

  hitX: 0, hitV: 0,                  // 角色被推开的位移与速度
  punch: 0,                          // 缩放脉冲
  tint: [255, 255, 255], tintA: 0,   // 命中染色
};

const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;
// 帧率无关的指数趋近：min(1,dt*k) 会让节奏随帧率漂移
const approach = (dt, k) => 1 - Math.exp(-k * dt);

/* ---------- 数值层：算出 S.p ---------- */

/* battle 算"手机该往哪走"，derive 算"算出来之后画面长什么样"。分成两个函数
   是因为它们回答的是两个问题，而把它们混在一起正是上一版最大的错误：礼物
   直接改了 S.p，等于把火力这一层整个删掉了。 */
function battle(dt) {
  if (S.phase !== 'play' && S.phase !== 'sudden') return;

  // 减益倒计时。它作用在**注入**上（见 giveGift），不作用在手机上
  if (S.debA > 0 && (S.debA -= dt) <= 0) S.debKA = 0;
  if (S.debB > 0 && (S.debB -= dt) <= 0) S.debKB = 0;
  if (S.stand > 0) S.stand -= dt;

  /* 对冲：双方等量消耗，速度由火力**少**的一方决定。
     这一条是整个模型的关键，它自带一根橡皮筋 —— 劣势方火力少，所以流失慢、
     补起来划算；而优势方想维持差距就得一直喂。不必另外再加"劣势方 x1.5"
     那种补丁，橡皮筋是从机制里长出来的。 */
  const lo = Math.min(S.fA, S.fB);
  const burn = NUM.BURN * lo;
  const useA = (burn + NUM.LOSS * S.fA) * dt;
  const useB = (burn + NUM.LOSS * S.fB) * dt;
  S.fA = Math.max(0, S.fA - useA);
  S.fB = Math.max(0, S.fB - useB);

  /* 打出去的火力就是屏幕上的弹幕。消耗多少就打多少发 —— 于是"对冲掉的那
     部分"和"穿过去的那部分"在画面上是分开的：前者在中线撞掉，后者才砸到人
     身上。观众刷了礼物手机没动时，屏幕上有答案：你的东西被对面在半空撞掉了。 */
  const denA = burn + NUM.LOSS * S.fA, denB = burn + NUM.LOSS * S.fB;
  S.budA += useA; S.budB += useB;
  emitFire(+1, denA > 0 ? burn / denA : 0);
  emitFire(-1, denB > 0 ? burn / denB : 0);

  /* ── 胜负层：血量 ──
     拉力差（= 双方火力之差）一件事管两头：**当下**它决定对抗线停在哪，
     **持续**它每秒扣对方的血。血量归零的一方输。

     和上一版的区别在于"手机位置"换了身份：它从**积分量**（被推过去就再也
     不回来）变成了**当前读数**（此刻谁的拉力大、大多少）。于是
       · 送礼物立刻看得见 —— 注入是瞬间的，对抗线半秒内就被拽过去；
       · 对面追上来，手机自己会走回去 —— 这才是拔河，绳子本来就能拉回来；
       · 输赢不再由"手机到没到底"决定，而是由这段时间里**一直被压着**的
         累积伤害决定。擦一下端点不算什么，压住对方三十秒才是赢。

     三个数的出处（X / M / Z，见 NUM 表）：
       M = 1000 拉力：本项目的 push = 螂人杀兵数 ÷ 100，所以 1000 拉力就是
           螂人杀的 10 万兵；上一版 DPS 的分母本来就是它，刻度没变。
       X = 30 拉力：螂人杀"最后 100 滴血，兵力大于 3000 才优先掉兵"里的
           3000 兵 ÷ 100。那是文档里唯一一个"低于它就不作数"的兵力门槛，
           拿来当死区正合适 —— 双方拉力咬在一起的时候不该有人掉血。
       Z = 5%/秒：⚠️ 螂人杀公开文档里**没有**掉血速率，它只写了兵数表、绝杀
           线（差 500w）和血量保护（最后 1000 / 100 滴血）。这个 5% 取自
           需求里给过的那个例子——"一方 1000 另一方 0，每秒扣对方 5%"，
           也就是 docs/数值设计.md 零节记着的那条。按它算，一件「爱的爆炸③」
           打掉对方 28.75%（四件见底），一方猛刷而对面不还手约 70 秒分胜负。
           要回到 12 分钟的局长，Z 得取 0.27（正好是上一版 DPS 的值，同一个
           单位）。两个都能跑，改一个数的事，见 ?z= 。 */
  const diff = S.fA - S.fB;

  /* 对抗线：拉力差的当前读数，**不积分**。
     趋近而不是直接取值 —— 礼物注入是瞬间跳变的，直接赋值会让手机"咯噔"
     闪一下；0.45 秒的时间常数既跟得上，又让那一下读成"被拽过去"。 */
  const want = 50 + 50 * clamp(diff / NUM.LINE_FULL, -1, 1);
  S.p += (want - S.p) * approach(dt, NUM.LINE_RATE);

  /* 掉血。差距过不了 X 就一个血都不掉 —— 这是僵持区：双方咬得紧的时候
     画面照样激烈（弹幕全在中线对撞），但谁也伤不到谁。
     扣血按**差的全量**算，不是"超出 X 的那部分"：X 是开关不是起征点。
     跨过门槛那一下伤害是 30/1000×Z，一秒零点几个血，看不出跳变。 */
  const gap = Math.abs(diff);
  /* 每秒正在掉多少血，写成读数给 HUD 用。它本来就是上面算出来的中间量，
     摆出来是因为观众真正想知道的就是这个数 —— "我刷的这件把他的血扣快了
     多少"。血条自己回答不了，它只显示存量。 */
  S.dpsA = S.dpsB = 0;
  if (gap > NUM.PULL_X) {
    let z = Math.min(NUM.HP_MAX, gap / NUM.PULL_M * NUM.HP_Z);
    const losing = diff > 0 ? -1 : +1;                   // 正在挨打的一方

    /* 濒死护盾：血量见底时，火力越足越扛得住。这是螂人杀"最后 100 滴血，
       兵力大于 3000 就优先掉兵"的原意 —— 刷礼物能直接保命，而且看得见：
       火力条长就是在替你挡。

       ⚠️ 它**不能去扣火力存量**。试过那种写法，结果是一条正反馈：护盾吃掉
       劣势方的火力 → min 变小 → 对冲跟着变弱 → 优势方的火力不再被烧掉 →
       差值反而越拉越大。实测净差冲到理论值（Δ注入/LOSS）的 2.4 倍，越接近
       终点崩得越快。根因是火力同时担着两个职责：它既是护盾的燃料，又是对冲
       的输入，扣一处动两处。所以护盾只能按**比例**减伤，不碰存量。 */
    const hp = losing > 0 ? S.hpA : S.hpB;
    if (hp < NUM.SHIELD_AT) {
      const mine = losing > 0 ? S.fA : S.fB, his = losing > 0 ? S.fB : S.fA;
      z *= 1 - Math.min(NUM.SHIELD_MAX, mine / (his + 1) * 1.5);
    }
    if (losing > 0) { S.hpA = Math.max(0, S.hpA - z * dt); S.dpsA = z; }
    else { S.hpB = Math.max(0, S.hpB - z * dt); S.dpsB = z; }
  }

  if (S.hpA <= 0 || S.hpB <= 0) { finish(S.hpA <= 0 ? -1 : +1); return; }

  /* 反击时刻：第一次有人掉到最后 8 滴血时，劣势方注入翻倍两分钟，全局只
     触发一次。放大的是注入不是伤害 —— 在两层模型里，"更有力"只能是更多火力。 */
  if (!S.standUsed && Math.min(S.hpA, S.hpB) < NUM.STAND_AT) {
    S.standUsed = true; S.stand = NUM.STAND;
  }

  /* 绝杀：血量被拉开这么多还一直追不回来，就别耗了，给 30 秒最后的机会。
     判据从"手机压在一边多久"换成了"血差多大"—— 手机位置现在是瞬时读数，
     一件大礼物就能把它顶到端点，再拿它当"一直被压着"的证据已经不成立。 */
  const lead = Math.abs(S.hpA - S.hpB);
  if (S.phase === 'play') {
    S.big = lead >= NUM.SUDDEN_LEAD ? S.big + dt : 0;
    if (S.big >= NUM.SUDDEN_WAIT) { S.phase = 'sudden'; S.sudden = NUM.SUDDEN; }
  } else if ((S.sudden -= dt) <= 0) { finish(S.hpA > S.hpB ? +1 : -1); return; }

  // 时间到：血多的一方胜，差在 3 滴血以内判平
  if ((S.clock -= dt) <= 0) finish(S.hpA > S.hpB + 3 ? +1 : S.hpB > S.hpA + 3 ? -1 : 0);
}

function finish(who) { S.phase = 'over'; S.winner = who; S.dpsA = S.dpsB = 0; S.overT = 0; }

/* 火力转成弹幕。clash 的那些飞到中线就互相撞掉，只有剩下的才砸到人身上 ——
   这是"对冲"唯一的可视化，没有它观众看不懂自己刷的东西去哪了。 */
function emitFire(side, clashRatio) {
  const bud = side > 0 ? 'budA' : 'budB';
  let n = 0;
  while (S[bud] >= NUM.SHOT && n < 3) { S[bud] -= NUM.SHOT; n++; }
  for (let i = 0; i < n; i++) {
    const g = GIFT[side > 0 ? 'hairpin' : 'seed'];
    Ammo.launch(g, null, { one: true, clash: Math.random() < clashRatio });
  }
}

/* 送一件礼物。数值走火力，表现走弹幕 —— 两件事同一个入口，但不是同一层。 */
function giveGift(side, key) {
  const it = SHOP[key]; if (!it) return;
  const deb = side > 0 ? S.debKA : S.debKB;
  const loser = S.hpA < S.hpB ? +1 : -1;            // 谁正落后（看血，不看手机位置）
  const boost = (S.stand > 0 && side === loser) ? 2 : 1;
  const amt = it.push * (1 - deb) * boost;
  if (side > 0) { S.fA += amt; S.giftA++; } else { S.fB += amt; S.giftB++; }

  /* 高档礼物的第二维度：压制。光靠 push 拉开差距会逼出很难看的数值，而
     "让对方刷的每一件都打折"才是贵真正买到的东西。 */
  if (it.tier === 3) hexDebuff(-side, 0.30, 5);
  if (it.tier === 4) {
    hexDebuff(-side, 0.50, 8);
    // 直接削存量是唯一能瞬间改变差值的手段，也是翻盘的唯一来源
    if (side > 0) S.fB *= 0.5; else S.fA *= 0.5;
  }
  if (it.tier >= 1) {
    const g = GIFT[ITEM_OF[side > 0 ? 'L' : 'R'][it.tier]];
    Ammo.launch(g, null, { gift: true, exec: it.tier === 4 });
  } else {
    // 免费档不飞实体，只在自己那侧冒一小串火花 —— 它买的是参与感，不是战力
    RECIPE.star.burst(side > 0 ? 46 : W - 46, 300 + Math.random() * 520, -side, 0.3);
  }
}

function hexDebuff(side, k, sec) {
  if (side > 0) { S.debKA = Math.max(S.debKA, k); S.debA = Math.max(S.debA, sec); }
  else { S.debKB = Math.max(S.debKB, k); S.debB = Math.max(S.debB, sec); }
}

function startMatch() {
  S.p = 50; S.fA = S.fB = 0; S.budA = S.budB = 0;
  S.hpA = S.hpB = 100; S.dpsA = S.dpsB = 0;
  S.debA = S.debB = S.debKA = S.debKB = 0;
  S.clock = NUM.MATCH; S.phase = 'play';
  S.big = S.sudden = S.stand = 0; S.standUsed = false; S.winner = 0;
  S.overT = 0; S.giftA = S.giftB = 0; S.board = [];
  S.auto = false;
  Ammo.clear(); Particles.clear();
}

/* ---------- 表现层：由 S.p 派生画面 ---------- */
function derive(dt) {
  /* 空闲拉锯。双方都不送礼物时拉力差是 0，S.p 停在正中一动不动，画面就僵在
     同一档关键帧上很久 —— 可拔河里"没人占上风"不等于"没人使劲"，绳子该一直
     在小幅来回。
     扰动只进**表现层**：S.p 是拉力差的读数，画面上的手机、角色姿态、对抗线、
     地面分色一律改读 FX.pDraw，血条读的是 S.hpA / S.hpB。
     不能直接摇 S.p —— 它下一帧就会被 battle 按拉力差重算，摇进去的量当场就
     没了；真要摇也不该摇，那会让观众以为拉力差在变。
     三个频率叠加，不是单频也不是两频。单频读出来是钟摆，一眼看穿；两频会
     周期性地互相抵消 —— 实测 0.83/1.41 那一组有长达 3.6 秒的平台期，胶片上
     连着四格 pDraw 都卡在 51.2，正好把"长时间同一个动作"原样复现了一遍。
     这一组每 0.6 秒的极差中位 1.9 个百分点，最长的呆滞只有 0.6 秒。
     越接近端点越收敛（calm）。用三次方而不是一次方：一次方衰减太快，p=78
     就只剩四成幅度，可"长时间不动"在任何进度上都会发生，不是中点专有的毛病；
     三次方让它在 p=90 之前基本满幅，只在最后几个点收住。收住是必须的 ——
     手机已经被拽到画面边上了，再叠一层来回摆就会读成"推到底了还在晃"。 */
  const calm = 1 - Math.pow(Math.abs(S.p - 50) / 50, 3);

  /* 拉锯只在**双方都没送礼物**的时候才满幅 —— 这是需求的原话，而上一版把它做成了
     无条件常开，那个实现错误会直接吃掉玩法：
     一次拉锯摆动是 10 个百分点（±5 来回）。礼物推得动多少是同一把尺子上的数：
     拉力差 100 才换来手机偏 5 个百分点 —— 一件「魔法镜②」（注入 20）自己
     只值 1 个百分点，整个埋在 10 个点的来回晃里，读出来就是"我刷了，什么都
     没发生"。信号比噪声小，加多少浓度都没用。
     所以拉锯必须给战况让位：场上还有拉力差，手机本来就被拽着在动，不需要
     填充；拉力烧干了、两边归零了，才是真的僵住。
     指标用**拉力差**，不是拉力总量，也不是"最近几秒有没有人点礼物"：
     · 手机位置就是拉力差的读数（battle 里 p = 50 + 50×差/LINE_FULL），所以
       差值才是"画面在不在动"的正确度量；
     · 拉力总量是错的 —— 双方对着刷小礼物时它会被撑得很高（各 0.3 件/秒的
       魔法镜②就能让总量稳在 1000），而那时差值是 0、手机停在正中，按总量
       判就会把拉锯关死，僵局原样回来。而这恰恰是最需要拉锯的场面之一；
     · 拉力是慢衰减的，所以不用另外维护计时器去猜"这一波推完了没有"，差值
       自己会一路烧到手机真的停下来。
     阈值 100 ≈ 一个能量电池②，也正好是掉血死区 PULL_X(30) 的三倍多：小到
     推不动画面的那些礼物，不该、也不需要把拉锯关掉。
     趋近而不是直接取值：礼物注入是瞬间跳变的，直接乘会让画面"咯噔"一下。 */
  const busy = Math.min(1, Math.abs(S.fA - S.fB) / 100);
  FX.busy += (busy - FX.busy) * approach(dt, 1.6);

  FX.pDraw = clamp(S.p + (Math.sin(S.t * 1.65) * 0.55
                        + Math.sin(S.t * 2.73 + 2.1) * 0.30
                        + Math.sin(S.t * 4.65 + 4.3) * 0.15)
                       * P.sway * calm * (1 - FX.busy), 0, 100);

  if (S.phase === 'over') {
    S.overT += dt;
    /* ?overt=<秒> 把结算钉在指定时刻。判词砸下来只有半秒、气泡和面板各自也
       就零点几秒，不钉住根本截不到入场的样子 —— 和 ?hudflash 同一个道理。 */
    if (Result.pin >= 0) S.overT = Result.pin;
  }

  const bias = (FX.pDraw - 50) / 50;
  // p 大 = 查岗党(女方,在左)占优 = 手机被拽向左
  const target = MID - Math.sign(bias) * Math.pow(Math.abs(bias), P.curve) * P.half;
  FX.phoneX += (target - FX.phoneX) * approach(dt, 4.2);

  FX.struggle = 1 - Math.abs(bias) * 0.78;          // 僵持度：五五开时最高
  FX.jit = Math.sin(S.t * 47) * 2.4 * FX.struggle;
  FX.phoneY = P.phoneY + Math.sin(S.t * 9.3) * 6 * FX.struggle - Math.abs(bias) * 14;

  /* 角色被推开又站回来：弹簧-阻尼，不是单纯衰减 —— 单纯衰减只有"飘回去"，
     看不出"被推动了"。挨一下给的是速度不是位移。 */
  FX.hitV += -FX.hitX * P.hitK * dt;
  FX.hitV *= Math.pow(P.hitDamp, dt * 60);
  FX.hitX += FX.hitV * dt;
  FX.actorX = (FX.phoneX - MID) * P.drag + FX.hitX;

  FX.punch *= Math.pow(P.punchDecay, dt * 60);
  if (FX.punch < 0.002) FX.punch = 0;
  FX.tintA *= Math.pow(P.tintDecay, dt * 60);
  if (FX.tintA < 0.004) FX.tintA = 0;

  /* 对抗线上的冲击波：命中那一行注入冲量，随后沿线上下传播并衰减。它与
     rowOff 分开演化、最后一起读 —— rowOff 管"谁在推"（慢、由 p 决定），
     冲量管"刚刚挨了一下"（快、由事件决定）。混在一个数组里的话，一次命中
     会被 shapeRate 的趋近吃掉大半，读不出撞击。 */
  const im = FX.rowImp, nim = new Array(ROWS);
  for (let r = 0; r < ROWS; r++) {
    const nb = ((r > 0 ? im[r - 1] : im[r]) + (r < ROWS - 1 ? im[r + 1] : im[r])) / 2;
    nim[r] = (im[r] + (nb - im[r]) * approach(dt, P.waveSpread)) * Math.pow(P.waveDecay, dt * 60);
  }
  for (let r = 0; r < ROWS; r++) im[r] = Math.abs(nim[r]) < 0.05 ? 0 : nim[r];

  const o = FX.rowOff, next = new Array(ROWS);
  for (let r = 0; r < ROWS; r++) {
    const d = r / (ROWS - 1);
    const tilt = (0.5 - d) * 2 * bias * P.tilt;
    const wob = Math.sin(S.t * 0.41 + r * 0.78) * 0.62 + Math.sin(S.t * 0.83 + r * 1.7) * 0.31;
    const desire = (tilt * 0.62 + wob * 0.42) * P.bulge;
    const nb = ((r > 0 ? o[r - 1] : o[r]) + (r < ROWS - 1 ? o[r + 1] : o[r])) / 2;
    const goal = (desire + P.linkW * nb) / (1 + P.linkW);
    next[r] = o[r] + (goal - o[r]) * approach(dt, P.shapeRate);
  }
  for (let r = 0; r < ROWS; r++) o[r] = clamp(next[r], -110, 110);

  const hot = 1 - Math.abs(bias) * 0.42;
  for (let r = 0; r < ROWS; r++) {
    const d = r / (ROWS - 1);
    const g = Math.exp(-Math.pow((d - 0.36) / 0.44, 2));
    FX.rowHeat[r] += (clamp(g * 1.3 * hot, 0, 1) - FX.rowHeat[r]) * approach(dt, 3.4);
  }
}

/* ---------- 命中：一次礼物/点赞落地时发生的全部事情 ---------- */

/* 一次命中同时动五样东西：粒子、对抗线冲量、角色位移与染色、屏幕震动、顿帧。
   写成单一入口而不是散在各处，是因为这五样的强度必须一起缩放 —— 分开调的话
   小礼物会震得比大礼物还狠，而观众读到的"这一下有多重"正是它们的合力。

   side: +1 打向查岗党(左/女方)，-1 打向灭迹党(右/男方)
   power: 1 点赞级  2 普通礼物  3 大礼物 */
function impact(side, y, power, recipe) {
  const r = recipe || RECIPE.thud;
  const s = power >= 4 ? 2.8 : power === 3 ? 1.7 : power === 2 ? 1.0 : 0.55;
  const x = frontAt(y);

  // 冲量注入命中高度那一行，方向朝被打的一侧
  const d = clamp((y - TOP) / (BOT - TOP), 0, 1) * (ROWS - 1);
  const i0 = clamp(Math.floor(d), 0, ROWS - 1);
  FX.rowImp[i0] += -side * 40 * s;
  if (i0 > 0) FX.rowImp[i0 - 1] += -side * 22 * s;
  if (i0 < ROWS - 1) FX.rowImp[i0 + 1] += -side * 22 * s;

  FX.hitV += -side * 320 * s;
  FX.punch = Math.max(FX.punch, 0.045 * s);
  /* 染色只是"挨了一下"的提示，不是照明。超过 0.21 角色的线稿和睡衣花纹就被
     洗掉了，而那正是这个玩法唯一能看的东西 —— 所以它有一个**可读性天花板**，
     档 3 起就顶在那儿，档 4 不会更红。写成 min(天花板, …) 而不是 min(1.4, s)，
     是因为后者看起来像"按分量缩放"，实际从档 3 就封死了，读代码会被骗一次。
     档 4 强在独占那 0.8 秒，不在染得更狠。 */
  const TINT_MAX = 0.21;
  FX.tint = r.tint; FX.tintA = Math.max(FX.tintA, Math.min(TINT_MAX, 0.15 * s));

  Particles.addShake(7 * s);
  Particles.addFlash(power >= 4 ? 0.34 : power >= 3 ? 0.22 : power >= 2 ? 0.10 : 0.03);
  /* 点赞级不顿帧。连珠一串八颗，每颗都冻 35ms 的话，这串"哒哒哒"就被拆成
     八次停顿 —— 而它的表现力全在快。顿帧留给看得出分量的那两档，在那里它
     才是"全世界停下来看这一击"，而不是一段接一段的停摆。 */
  /* 档 4 是"全世界停下来看这一击"：冻 320ms，配合 ammo.js 里的独占窗口，
     这段时间别的礼物只排队不落地。它买的不是更大的数字，是一段没人打断的时间。 */
  Particles.hitStop(power >= 4 ? 0.32 : power >= 3 ? 0.11 : power >= 2 ? 0.07 : 0);

  r.burst(x, y, side, s);
}

/* 配方表：一件礼物炸出什么，只在这里定义。形态（dot/spark/ring/chip/star/soft）
   是通用的，换题材皮不用动 fx.js。

   颜色有一条硬规矩，是这张底图逼出来的：客厅是浅绿墙 + 米色地板，**白色在
   这上面几乎加不亮**。所以发光的那几种一律用高饱和暖橙 —— 它靠色相跳出来
   而不是靠亮度；实体那几种一律深色 + 描边 —— 它靠轮廓跳出来。上一版整套
   用的奶白和浅米，在胶片上基本看不见。

   thud 是通用撞击，任何还没单独配方的东西都落到它上面。 */
const INK = [58, 44, 38];        // 描边色，取角色线稿那个暖黑
const EMBER = [255, 156, 38];    // 发光基色，高饱和暖橙

const RECIPE = {
  thud: {
    tint: [255, 224, 186],
    burst(x, y, side, s) {
      Particles.spawn({ kind: 'dot', x, y, r: 16 * s, r1: 70 * s, life: 0.20,
                        rgb: [255, 196, 110], a: 0.9 });
      Particles.spawn({ kind: 'ring', x, y, r: 10 * s, r1: 120 * s, life: 0.38,
                        rgb: EMBER, lw: 6 * s });
      // 第二道环晚 70ms 出场，读起来是"砰—砰"两下而不是一下
      setTimeout(() => Particles.spawn({ kind: 'ring', x, y, r: 8 * s, r1: 180 * s,
                        life: 0.44, rgb: [255, 132, 54], lw: 4 * s }), 70);
      /* 火花给足数量。画布 960x1334，二三十个粒子铺开就只剩零星几点，
         读不出"炸开"—— 这里的密度感是靠数量堆的，不是靠单颗更亮。 */
      for (let i = 0; i < Math.round(26 * s); i++) {
        const a = (Math.random() - 0.5) * 2.2;
        const sp = (240 + Math.random() * 560) * s;
        Particles.spawn({ kind: 'spark', x, y, vx: -side * Math.cos(a) * sp, vy: Math.sin(a) * sp - 110,
                          g: 980, drag: 0.985, life: 0.24 + Math.random() * 0.3,
                          rgb: i % 4 ? EMBER : [255, 238, 150],
                          lw: 1.6 + Math.random() * 2.4 * s });
      }
      for (let i = 0; i < Math.round(14 * s); i++) {
        Particles.spawn({ kind: 'soft', x: x + (Math.random() - 0.5) * 60 * s, y: y + (Math.random() - 0.3) * 40,
                          vx: -side * (40 + Math.random() * 150) * s, vy: -20 - Math.random() * 80,
                          g: 90, drag: 0.94, r: 10 * s, r1: (46 + Math.random() * 34) * s,
                          life: 0.7 + Math.random() * 0.7, rgb: [150, 128, 110], a: 0.30 });
      }
      // 翻滚的小片：撞击总要崩下点什么，没有它只有光，像是凭空亮了一下
      for (let i = 0; i < Math.round(9 * s); i++) {
        const a = (Math.random() - 0.5) * 2.4;
        const sp = (170 + Math.random() * 330) * s;
        Particles.spawn({ kind: 'chip', shape: 'debris', x, y, vx: -side * Math.cos(a) * sp, vy: Math.sin(a) * sp - 200,
                          g: 780, drag: 0.99, life: 0.7 + Math.random() * 0.6,
                          w: 6 + Math.random() * 8 * s, h: 4 + Math.random() * 6 * s,
                          rot: Math.random() * 6.28, vrot: (Math.random() - 0.5) * 16,
                          rgb: [122, 96, 78], edge: INK, lw: 1.6, a: 0.95 });
      }
    },
  },

  /* 枕头砸脸。全场唯一一个不出火花的配方 —— 枕头砸下去的是一团闷响和漫天
     绒毛，给它配火花就成了爆炸。冲击感全靠数量和滞空：羽毛重力只有常规的
     八分之一、阻力极大，所以命中半秒之后画面里还在飘，而火花那时候早没了。 */
  feather: {
    tint: [255, 238, 240],
    burst(x, y, side, s) {
      Particles.spawn({ kind: 'dot', x, y, r: 22 * s, r1: 72 * s, life: 0.20,
                        rgb: [255, 206, 198], a: 0.40 });
      // 绒絮：贴着撞击点炸开的那一蓬，用来糊住撞击瞬间。别给多 —— 它是浅色
      // 的，在浅色沙发前面堆厚了就是一团白雾，把羽毛的形状全吃掉。
      for (let i = 0; i < Math.round(11 * s); i++) {
        const a = Math.random() * 6.283;
        Particles.spawn({ kind: 'soft', x, y, vx: Math.cos(a) * (70 + Math.random() * 240) * s,
                          vy: Math.sin(a) * (60 + Math.random() * 180) * s - 90,
                          g: 60, drag: 0.92, r: 14 * s, r1: (48 + Math.random() * 38) * s,
                          life: 0.5 + Math.random() * 0.6, rgb: [214, 200, 206], a: 0.26 });
      }
      /* 羽毛本体：sway 左右摆，慢慢打着旋往下落。
         尺寸和数量是按"直播画面上看得见"定的，不是按真羽毛定的 —— 一根真
         羽毛在 960 宽的画布上只有十几像素，观众端再缩一半就是几个像素的白
         点，等于没有。阻力也不能给真实值：0.958 每帧意味着三分之一秒后羽毛
         就地停住，全堆在命中点上，看着像一摊泡沫而不是炸开的枕头。 */
      for (let i = 0; i < Math.round(30 * s); i++) {
        const a = (Math.random() - 0.5) * 2.8;
        const sp = (200 + Math.random() * 560) * s;
        Particles.spawn({ kind: 'chip', shape: 'feather', x: x + (Math.random() - 0.5) * 60, y: y + (Math.random() - 0.5) * 80,
                          vx: -side * Math.cos(a) * sp, vy: Math.sin(a) * sp - 170,
                          g: 150, drag: 0.988, sway: 40 + Math.random() * 55,
                          life: 1.5 + Math.random() * 1.4,
                          w: 20 + Math.random() * 17 * s, h: 12 + Math.random() * 9,
                          rot: Math.random() * 6.28, vrot: (Math.random() - 0.5) * 5.0,
                          rgb: i % 5 ? [252, 250, 250] : [250, 232, 236], edge: [138, 118, 122],
                          lw: 1.9, a: 1 });
      }
    },
  },

  /* 打懵了：头顶转圈的星星。这是全套里最"卡通"的一个，也是最省事的一个 ——
     星星本身就是观众对"挨了一下"的默认图示，不需要任何解释。
     spin 让它绕着命中点公转，不是原地飞散：飞散读成爆炸，公转才读成眩晕。 */
  star: {
    tint: [255, 242, 196],
    burst(x, y, side, s) {
      Particles.spawn({ kind: 'dot', x, y, r: 14 * s, r1: 74 * s, life: 0.18,
                        rgb: [255, 214, 96], a: 0.85 });
      Particles.spawn({ kind: 'ring', x, y, r: 8 * s, r1: 108 * s, life: 0.32,
                        rgb: [255, 196, 72], lw: 5 * s });
      // 公转的大星星：数量少，每颗都要看得清，所以描边给足
      for (let i = 0; i < Math.round(7 * s); i++) {
        const a = Math.random() * 6.283;
        Particles.spawn({ kind: 'star', shape: 'star', x: x - side * 20, y: y - 40 - Math.random() * 60,
                          vx: -side * (20 + Math.random() * 90), vy: -60 - Math.random() * 90,
                          g: 180, drag: 0.95, spin: 26 + Math.random() * 34,
                          r: (13 + Math.random() * 11) * s, r1: 3,
                          life: 0.7 + Math.random() * 0.6,
                          rot: a, vrot: (Math.random() - 0.5) * 7,
                          rgb: [255, 208, 56], edge: [126, 74, 18], lw: 2.4, a: 1 });
      }
      // 小星星飞散，补密度
      for (let i = 0; i < Math.round(11 * s); i++) {
        const a = (Math.random() - 0.5) * 2.8;
        const sp = (200 + Math.random() * 440) * s;
        Particles.spawn({ kind: 'star', shape: 'star', x, y, vx: -side * Math.cos(a) * sp, vy: Math.sin(a) * sp - 180,
                          g: 640, drag: 0.982, r: (6 + Math.random() * 6) * s, r1: 2,
                          life: 0.5 + Math.random() * 0.45,
                          rot: a, vrot: (Math.random() - 0.5) * 14,
                          rgb: [255, 226, 120], edge: [150, 96, 24], lw: 1.6, a: 1 });
      }
      for (let i = 0; i < Math.round(14 * s); i++) {
        const a = (Math.random() - 0.5) * 2.4;
        const sp = (260 + Math.random() * 480) * s;
        Particles.spawn({ kind: 'spark', x, y, vx: -side * Math.cos(a) * sp, vy: Math.sin(a) * sp - 120,
                          g: 900, drag: 0.985, life: 0.2 + Math.random() * 0.22,
                          rgb: [255, 198, 70], lw: 1.4 + Math.random() * 2 * s });
      }
    },
  },

  /* 硬东西砸碎（遥控器、马克杯）。碎片一律深色 —— 这是三个配方里唯一能在
     米色地板上自带对比的，所以它不描边也认得出，描边只是为了和另外两个
     配方看起来是同一套东西。 */
  debris: {
    tint: [226, 238, 255],
    burst(x, y, side, s) {
      Particles.spawn({ kind: 'dot', x, y, r: 18 * s, r1: 82 * s, life: 0.16,
                        rgb: [255, 236, 190], a: 0.95 });
      Particles.spawn({ kind: 'ring', x, y, r: 12 * s, r1: 150 * s, life: 0.30,
                        rgb: [255, 176, 60], lw: 7 * s });
      // 碎片：重、快、弹不起来，落地就停 —— 和羽毛正好是两个极端
      for (let i = 0; i < Math.round(24 * s); i++) {
        const a = (Math.random() - 0.5) * 2.5;
        const sp = (300 + Math.random() * 620) * s;
        const dark = i % 3 === 0;
        Particles.spawn({ kind: 'chip', shape: 'debris', x, y, vx: -side * Math.cos(a) * sp, vy: Math.sin(a) * sp - 300,
                          g: 1450, drag: 0.995, life: 0.55 + Math.random() * 0.5,
                          w: 5 + Math.random() * 12 * s, h: 4 + Math.random() * 8 * s,
                          rot: Math.random() * 6.28, vrot: (Math.random() - 0.5) * 22,
                          rgb: dark ? [48, 54, 64] : [96, 106, 120], edge: INK, lw: 1.5, a: 1 });
      }
      for (let i = 0; i < Math.round(30 * s); i++) {
        const a = (Math.random() - 0.5) * 2.0;
        const sp = (320 + Math.random() * 700) * s;
        Particles.spawn({ kind: 'spark', x, y, vx: -side * Math.cos(a) * sp, vy: Math.sin(a) * sp - 140,
                          g: 1020, drag: 0.984, life: 0.18 + Math.random() * 0.26,
                          rgb: i % 3 ? EMBER : [255, 244, 176],
                          lw: 1.4 + Math.random() * 2.6 * s });
      }
      // 一小撮灰，落在碎片后面，撞击点不至于干干净净
      for (let i = 0; i < Math.round(9 * s); i++) {
        Particles.spawn({ kind: 'soft', x: x + (Math.random() - 0.5) * 70 * s, y: y + (Math.random() - 0.2) * 50,
                          vx: -side * (50 + Math.random() * 170) * s, vy: -30 - Math.random() * 70,
                          g: 70, drag: 0.93, r: 12 * s, r1: (50 + Math.random() * 40) * s,
                          life: 0.6 + Math.random() * 0.6, rgb: [138, 132, 128], a: 0.34 });
      }
    },
  },

  /* 玫瑰花束炸开（档 3 左）。结构照抄 feather —— 枕头和花束在物理上是同一
     件事：一团轻的东西散开、长时间滞空。差别只在颜色和形状。
     这也是为什么它值得换掉棉被：白羽毛在这张浅色底图上本来就偏淡，全靠
     数量才看得见；深玫红的花瓣自带对比，同样的数量亮一倍。 */
  petal: {
    tint: [255, 214, 226],
    burst(x, y, side, s) {
      Particles.spawn({ kind: 'dot', x, y, r: 20 * s, r1: 78 * s, life: 0.22,
                        rgb: [255, 138, 172], a: 0.55 });
      Particles.spawn({ kind: 'ring', x, y, r: 10 * s, r1: 128 * s, life: 0.34,
                        rgb: [255, 96, 140], lw: 5 * s });
      // 花瓣：sway 让它们打着旋往下飘，重力只有碎片的十分之一
      for (let i = 0; i < Math.round(32 * s); i++) {
        const a = (Math.random() - 0.5) * 2.9;
        const sp = (210 + Math.random() * 580) * s;
        const deep = i % 3 === 0;
        Particles.spawn({ kind: 'chip', shape: 'petal', x: x + (Math.random() - 0.5) * 60, y: y + (Math.random() - 0.5) * 80,
                          vx: -side * Math.cos(a) * sp, vy: Math.sin(a) * sp - 180,
                          g: 140, drag: 0.987, sway: 44 + Math.random() * 60,
                          life: 1.4 + Math.random() * 1.4,
                          // 长宽比压到 1:0.7 左右。第一版是 1:0.45，翻滚时被 cos
                          // 压扁，一屏读成几十根粉色胶囊而不是花瓣
                          w: 19 + Math.random() * 14 * s, h: 15 + Math.random() * 10 * s,
                          rot: Math.random() * 6.28, vrot: (Math.random() - 0.5) * 3.2,
                          rgb: deep ? [198, 40, 78] : [255, 92, 130], edge: [122, 30, 58],
                          lw: 1.8, a: 1 });
      }
      // 一点金粉。花束里那层包装纸的反光，也把粉色压不住的地方提亮
      for (let i = 0; i < Math.round(12 * s); i++) {
        const a = (Math.random() - 0.5) * 2.6;
        const sp = (240 + Math.random() * 460) * s;
        Particles.spawn({ kind: 'spark', x, y, vx: -side * Math.cos(a) * sp, vy: Math.sin(a) * sp - 150,
                          g: 820, drag: 0.983, life: 0.22 + Math.random() * 0.26,
                          rgb: [255, 216, 132], lw: 1.4 + Math.random() * 2 * s });
      }
    },
  },

  /* 奶茶泼一身（档 3 右）。和花瓣正好相反：液体是**重**的，落地就停，
     所以走 debris 的物理参数而不是 feather 的 —— 一杯奶茶泼出去要是像羽毛
     那样飘半秒，读起来就成了雾。 */
  splash: {
    tint: [246, 226, 198],
    burst(x, y, side, s) {
      Particles.spawn({ kind: 'dot', x, y, r: 18 * s, r1: 86 * s, life: 0.18,
                        rgb: [236, 202, 158], a: 0.8 });
      Particles.spawn({ kind: 'ring', x, y, r: 12 * s, r1: 142 * s, life: 0.30,
                        rgb: [214, 158, 96], lw: 6 * s });
      /* 奶茶渍：**糊住不动**。drag 给到 0.86，冲出去三分之一秒就停在原地，
         然后一直挂在被泼的那个人身上 —— 这是这个配方唯一在做的事。
         颜色必须是饱和焦糖不能是淡奶油色：底图是浅绿墙加米色地板，淡色的浆
         泼上去等于没泼。第一版就是栽在这儿，整个配方几乎是隐形的。 */
      for (let i = 0; i < Math.round(15 * s); i++) {
        const a = (Math.random() - 0.5) * 2.4;
        Particles.spawn({ kind: 'soft', x, y, vx: -side * Math.cos(a) * (110 + Math.random() * 330) * s,
                          vy: Math.sin(a) * (80 + Math.random() * 230) * s - 110,
                          g: 180, drag: 0.86, r: 14 * s, r1: (36 + Math.random() * 30) * s,
                          life: 1.2 + Math.random() * 0.8, rgb: [176, 120, 64], a: 0.5 });
      }
      /* 珍珠：深褐、够大、弹得开。它们是全套里对比最强的一组 —— 深色在浅底
         上本来就跳，所以奶茶的可见度主要靠它们扛，浆只负责"湿了一片"。
         尺寸从 7 提到 13 起步：小于十几像素在观众端缩一半就成了灰点。 */
      for (let i = 0; i < Math.round(20 * s); i++) {
        const a = (Math.random() - 0.5) * 2.7;
        const sp = (240 + Math.random() * 520) * s;
        const d = 13 + Math.random() * 9 * s;
        Particles.spawn({ kind: 'chip', shape: 'pearl', x, y, vx: -side * Math.cos(a) * sp, vy: Math.sin(a) * sp - 300,
                          g: 1180, drag: 0.992, sway: 12 + Math.random() * 20,
                          life: 1.1 + Math.random() * 0.8,
                          w: d, h: d,
                          rot: Math.random() * 6.28, vrot: (Math.random() - 0.5) * 18,
                          rgb: i % 4 ? [52, 34, 22] : [96, 62, 38], edge: INK, lw: 1.8, a: 1 });
      }
      // 糖浆丝
      for (let i = 0; i < Math.round(14 * s); i++) {
        const a = (Math.random() - 0.5) * 2.1;
        const sp = (300 + Math.random() * 620) * s;
        Particles.spawn({ kind: 'spark', x, y, vx: -side * Math.cos(a) * sp, vy: Math.sin(a) * sp - 160,
                          g: 960, drag: 0.985, life: 0.16 + Math.random() * 0.24,
                          rgb: i % 3 ? [232, 190, 128] : [255, 240, 208],
                          lw: 1.5 + Math.random() * 2.2 * s });
      }
    },
  },

  /* 求婚戒指盒绽放（档 4 左）。**绽放式**：不朝被打的一侧溅，而是从命中点
     向四周全向炸开 —— 这是它跟前面所有配方唯一的结构差别，也是"绽放"和
     "溅射"的分界。独占那 0.8 秒里画面重心必须在被砸的那个人身上，全向才
     能把他整个圈住。
     爱心给负重力：往上飘。这是全套里唯一一个不往下掉的配方。 */
  bloom: {
    tint: [255, 232, 214],
    burst(x, y, side, s) {
      Particles.spawn({ kind: 'dot', x, y, r: 30 * s, r1: 150 * s, life: 0.30,
                        rgb: [255, 226, 150], a: 0.95 });
      Particles.spawn({ kind: 'ring', x, y, r: 14 * s, r1: 210 * s, life: 0.40,
                        rgb: [255, 206, 92], lw: 8 * s });
      // 三道环依次荡开，"绽"的那一下就是它
      setTimeout(() => Particles.spawn({ kind: 'ring', x, y, r: 10 * s, r1: 300 * s,
                        life: 0.50, rgb: [255, 170, 88], lw: 5 * s }), 80);
      setTimeout(() => Particles.spawn({ kind: 'ring', x, y, r: 8 * s, r1: 380 * s,
                        life: 0.58, rgb: [255, 140, 170], lw: 3.5 * s }), 180);
      /* 爱心：先向外冲开一圈（高初速 + 大阻力，0.2 秒内就减速停住），再靠
         负重力慢慢飘起来。两段连起来读就是"绽开、然后升上去"。 */
      for (let i = 0; i < Math.round(11 * s); i++) {
        const a = Math.random() * 6.283;
        const sp = (300 + Math.random() * 420) * s;
        /* 半径拿 s 放大之后很容易失控：第一版 (15+16)*2.8 得到 42~87 的半径，
           一颗爱心就有 190px 宽、占屏宽五分之一，四十颗直接把两张脸糊死。
           档 4 确实该铺满屏，但**脸是这个玩法仅有的两个可读信息之一**，而
           爱心要在画面上待一秒半到两秒半，不是一闪而过。密度靠数量，不靠
           单颗更大。 */
        Particles.spawn({ kind: 'heart', shape: 'heart', x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp,
                          g: -46, drag: 0.90, sway: 26 + Math.random() * 34,
                          r: (9 + Math.random() * 9) * s, r1: 4,
                          life: 1.5 + Math.random() * 1.1,
                          rot: (Math.random() - 0.5) * 0.7, vrot: (Math.random() - 0.5) * 2.4,
                          rgb: i % 3 ? [255, 92, 130] : [255, 150, 180],
                          edge: [150, 34, 70], lw: 2.2, a: 1 });
      }
      // 金色星光，绕着命中点公转 —— 借 star 配方那套"眩晕"的读法
      for (let i = 0; i < Math.round(10 * s); i++) {
        const a = Math.random() * 6.283;
        Particles.spawn({ kind: 'star', shape: 'star', x, y, vx: Math.cos(a) * (60 + Math.random() * 170),
                          vy: Math.sin(a) * (60 + Math.random() * 150) - 70,
                          g: 150, drag: 0.94, spin: 30 + Math.random() * 40,
                          r: (11 + Math.random() * 12) * s, r1: 3,
                          life: 0.8 + Math.random() * 0.7,
                          rot: a, vrot: (Math.random() - 0.5) * 7,
                          rgb: [255, 214, 74], edge: [140, 84, 20], lw: 2.4, a: 1 });
      }
      // 金粉全向铺满
      for (let i = 0; i < Math.round(26 * s); i++) {
        const a = Math.random() * 6.283;
        const sp = (280 + Math.random() * 700) * s;
        Particles.spawn({ kind: 'spark', x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp,
                          g: 700, drag: 0.982, life: 0.24 + Math.random() * 0.34,
                          rgb: i % 4 ? [255, 214, 120] : [255, 248, 214],
                          lw: 1.6 + Math.random() * 2.6 * s });
      }
    },
  },

  /* 合照相框绽放（档 4 右）。同样全向，但落点相反：爱心往上飘，照片往下落。
     一张张翻着往下掉的照片比爆炸更有分量 —— 它占的是**时间**不是亮度，
     生命期给到 2.6 秒，独占窗口结束之后它还在飘，这段余韵才是档 4 的味道。 */
  memory: {
    tint: [252, 240, 222],
    burst(x, y, side, s) {
      Particles.spawn({ kind: 'dot', x, y, r: 28 * s, r1: 146 * s, life: 0.28,
                        rgb: [255, 236, 200], a: 0.9 });
      Particles.spawn({ kind: 'ring', x, y, r: 14 * s, r1: 206 * s, life: 0.38,
                        rgb: [236, 196, 140], lw: 8 * s });
      setTimeout(() => Particles.spawn({ kind: 'ring', x, y, r: 10 * s, r1: 320 * s,
                        life: 0.54, rgb: [206, 168, 120], lw: 4 * s }), 120);
      /* 照片。走 card 而不是 chip —— 理由见 fx.js 里 card 那段：chip 带描边
         时永远是胶囊，照片必须是矩形。
         配色回到这张底图的老规矩上：**相纸保持浅色，对比靠那圈粗深边**。
         中间试过把整张压成复古棕来"让它看得见"，那是绕开规律不是用它 ——
         看得见了，但不再像照片。
         初速比第一版降了三成、阻力加大：原来冲得太猛，一秒后全飞出屏幕，
         留在画面里的反而是空的。慢落的余韵才是档 4 买到的东西。 */
      for (let i = 0; i < Math.round(20 * s); i++) {
        const a = Math.random() * 6.283;
        const sp = (130 + Math.random() * 330) * s;
        const old = i % 4 === 0;
        Particles.spawn({ kind: 'card', shape: 'card', x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 150,
                          g: 190, drag: 0.976, sway: 62 + Math.random() * 70,
                          life: 2.0 + Math.random() * 0.8,
                          w: 30 + Math.random() * 17 * s, h: 24 + Math.random() * 13 * s,
                          rot: (Math.random() - 0.5) * 1.5, vrot: (Math.random() - 0.5) * 1.1,
                          rgb: old ? [242, 226, 198] : [252, 247, 238],
                          edge: [74, 52, 34], lw: 3.6, a: 1 });
      }
      // 少量爱心，把这一下和戒指盒认作同一档
      for (let i = 0; i < Math.round(7 * s); i++) {
        const a = Math.random() * 6.283;
        Particles.spawn({ kind: 'heart', shape: 'heart', x, y, vx: Math.cos(a) * (200 + Math.random() * 300) * s,
                          vy: Math.sin(a) * (200 + Math.random() * 260) * s,
                          g: -40, drag: 0.90, sway: 24 + Math.random() * 30,
                          r: (8 + Math.random() * 8) * s, r1: 3,
                          life: 1.4 + Math.random() * 1.0,
                          rot: (Math.random() - 0.5) * 0.6, vrot: (Math.random() - 0.5) * 2.2,
                          rgb: [255, 122, 152], edge: [150, 48, 82], lw: 2.0, a: 1 });
      }
      for (let i = 0; i < Math.round(16 * s); i++) {
        const a = Math.random() * 6.283;
        const sp = (240 + Math.random() * 560) * s;
        Particles.spawn({ kind: 'spark', x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp,
                          g: 760, drag: 0.983, life: 0.2 + Math.random() * 0.3,
                          rgb: i % 3 ? [255, 226, 168] : [255, 248, 226],
                          lw: 1.5 + Math.random() * 2.4 * s });
      }
    },
  },
};

/* 礼物有两张表，因为它是两件事。

   SHOP —— **数值**。九件抖音平台礼物，相对价值直接继承《螂人杀》已验证的
   兵数比例（push = 兵数 ÷ 100）：点赞 1、仙女棒 100、魔法镜 2000、
   爱的爆炸 23000、神秘空投 60000……这一套在两个上线玩法里都跑过，不必重定。
   push 注入的是**拉力**，不是血 —— 血由双方拉力的差值每秒扣出来。

   GIFT —— **表现**。一件物品飞出去长什么样：样式、体积、命中配方。

   两张表用 tier 连起来：数值分九档跟着平台礼物走，表现只做五档。档数的上限
   不是价格带定的，是"观众能不能分辨"定的 —— 单投和重投靠体积(56 vs 78)加
   顿帧(70 vs 110ms)已经是可分辨的临界，中间再插一档做出来也白做。所以多件
   平台礼物共用一档表现，扩档只靠质变：有没有实体 → 震不震 → 染不染色 →
   独不独占屏幕。 */
const SHOP = {
  like:    { tier: 0, push: 0.01, name: '点赞' },
  six:     { tier: 0, push: 0.06, name: '666' },
  wand:    { tier: 1, push: 1,    name: '仙女棒' },
  chest:   { tier: 1, push: 10,   name: '技能宝箱' },
  mirror:  { tier: 2, push: 20,   name: '魔法镜' },
  battery: { tier: 2, push: 110,  name: '能量电池' },
  boom:    { tier: 3, push: 230,  name: '爱的爆炸' },
  mic:     { tier: 3, push: 360,  name: '派对话筒' },
  drop:    { tier: 4, push: 600,  name: '神秘空投' },
};

/* tier → 该阵营飞出去的是什么。

   物品方案：**档 1~2 客厅现场 + 档 3~4 甜蜜反击**（见 docs/礼物设计.md 第六节）。
   这不是折中，是两段要的东西本来就不同：档 1~2 一局出现上百次，它的好处恰恰
   是不够特别；档 3~4 一局只有几次，要的是"我没见过"—— 而这个题材里观众最没
   见过的，就是吵到最后砸过来的是一束花。 */
const ITEM_OF = {
  L: [null, 'hairpin', 'pillow', 'bouquet', 'ringbox'],
  R: [null, 'seed',    'gamepad', 'milktea', 'photo'],
};

/* 三种样式的差别是节奏与体量，不是物品：
     volley 连珠  一串小件快速飞来，每颗单独命中 —— 也是常规火力用的那一种
     single 单投  单件中等速度，看得清是什么东西
     heavy  重投  先预警再慢慢压过来
   观众不需要认出飞过来的是什么，光看节奏就知道这一发有多重。

   push 是这件物品被直接发射时的默认注入量（诊断胶片会用到）；走 SHOP 送礼
   时以 SHOP 的 push 为准 —— 同一个抱枕，魔法镜刷出来和能量电池刷出来
   份量差 5.5 倍，但飞起来是同一个东西。 */
/* spin 是贴图转盘的转速（rad/s），八件都要给。

   定它的规矩是**飞行途中转半圈**，不是"转够一圈"。
   原来那条"必须转够一圈以上，观众才看得出它是个有厚度的东西"是错的，
   而且错得很贵 —— 按它给出来的 14~15，每帧要转 14°，转盘每格才 10°，
   等于**每帧跳 1.4 格**。那已经进了走马灯区：眼睛读不出"一个刚体在转"，
   只读到一连串跳变的形状，也就是"闪"。用户的原话是"不够三d，没有体积感"。

   半圈就够了 —— 从正面转到背面，可见面已经完整换过一遍，体积感全在里头。
   而每帧只转 5~8°（半格到 0.8 格），姿态是连着的，眼睛跟得上。
   飞行时长按各自的速度算：volley 0.36s、single 0.56s、heavy 0.47s
   （heavy 带 900 的加速度），spin = π / 飞行时长。

   处决弹速度减半、时长翻倍，`fire()` 里把转速一起减半，仍是半圈。 */
const GIFT = {
  // 查岗党（女方，在左，from=+1）
  hairpin: { name: '发卡',   from: +1, style: 'volley', item: 'hairpin', r: 22, n: 8, spin: 8.8, power: 1, recipe: 'star',    push: 1 },
  pillow:  { name: '抱枕',   from: +1, style: 'single', item: 'pillow',  r: 56,       spin: 5.7, power: 2, recipe: 'feather', push: 20 },
  bouquet: { name: '花束',   from: +1, style: 'heavy',  item: 'bouquet', r: 76,       spin: 6.7, power: 3, recipe: 'petal',   push: 230 },
  /* 档 4 的 r 看着不大，是因为 exec 会再乘 1.8（ammo.js）：64→115、68→122，
     占屏宽的 24% 与 25%。飞行体积负责预告"这一下很重"，兑现在命中那一刻的
     绽放里 —— 所以本体不必再大，大的是绽开的东西。 */
  ringbox: { name: '戒指盒', from: +1, style: 'heavy',  item: 'ringbox', r: 64,       spin: 6.7, power: 4, recipe: 'bloom',   push: 600 },
  // 灭迹党（男方，在右，from=-1）
  seed:    { name: '瓜子',   from: -1, style: 'volley', item: 'seed',    r: 21, n: 8, spin: 8.8, power: 1, recipe: 'star',    push: 1 },
  gamepad: { name: '手柄',   from: -1, style: 'single', item: 'gamepad', r: 52,       spin: 5.7, power: 2, recipe: 'debris',  push: 20 },
  milktea: { name: '奶茶',   from: -1, style: 'heavy',  item: 'milktea', r: 72,       spin: 6.7, power: 3, recipe: 'splash',  push: 230 },
  photo:   { name: '相框',   from: -1, style: 'heavy',  item: 'photo',   r: 68,       spin: 6.7, power: 4, recipe: 'memory',  push: 600 },
};

function sampleRow(arr, y) {
  const d = clamp((y - TOP) / (BOT - TOP), 0, 1) * (ROWS - 1);
  const i = clamp(Math.floor(d), 0, ROWS - 2), f = d - i;
  const p0 = arr[Math.max(0, i - 1)], p1 = arr[i], p2 = arr[i + 1], p3 = arr[Math.min(ROWS - 1, i + 2)];
  return p1 + 0.5 * f * (p2 - p0 + f * (2 * p0 - 5 * p1 + 4 * p2 - p3 + f * (3 * (p1 - p2) + p3 - p0)));
}
// 对抗线在高度 y 处的横坐标 —— 手机、光柱、顶端指针、地面分色全读这一个函数
const frontAt = (y) => FX.phoneX + sampleRow(FX.rowOff, y) + sampleRow(FX.rowImp, y);
const heatAt = (y) => clamp(sampleRow(FX.rowHeat, y), 0, 1);
const phonePos = () => [frontAt(FX.phoneY) + FX.jit, FX.phoneY];

/* ---------- 角色：预渲染关键帧 ---------- */
/* 0~100 每 1% 一张。其中 29 张是生图画的关键档，其余由 interp_frames.py 用
   光流从相邻关键档插出来。从网格变形改走帧序列，是因为两个人抢同一部
   手机时，肩、肘、腕的相对关系每一档都不一样 —— 这种成对的姿态用一套骨骼
   去凑，永远是在"手够不到机身"和"肘折过头"之间取舍。

   不做相邻帧的交叉淡化：两张画的是不同姿态而不是同一姿态的不同时刻，叠在
   一起就是两副骨架互相穿透的重影，越是姿态差得远的档位越糊。硬切虽然跳，
   但每一帧都是清清楚楚的一张画。 */
class FrameSeq {
  /* imgs 是 0~100 共 101 项，缺的那几档是 null —— 姿态跨度太大的区间光流插
     不出干净的中间帧（会长出两个红发夹），只能等生图补上。缺档先映射到最近
     的邻居，画面照常，只是那里的跳变还是原来的大小。 */
  constructor(imgs) {
    this.imgs = imgs;
    this.map = imgs.map((im, i) => {
      if (im) return i;
      let best = -1, bd = 1e9;
      imgs.forEach((o, j) => { const d = Math.abs(j - i); if (o && d < bd) { bd = d; best = j; } });
      return best;
    });
  }

  /* punch 是缩放脉冲，tint 是命中染色 —— 角色是预渲染帧，做不了受击变形，
     打击反馈只能来自贴图之外。缩放以脚底为锚，人挨了一下会"胀"一下但脚不
     离地；染色走 source-atop，只盖在已画出的角色像素上，不会糊到背景。 */
  draw(ctx, p, offsetX, punch, tint, tintA) {
    const i = this.map[clamp(Math.round(clamp(p, 0, 100)), 0, 100)];
    const k = 1 + (punch || 0);
    const w = FRAME_W * k, h = FRAME_H * k;
    const foot = FRAME_TOP + FRAME_H;
    const dx = offsetX + (FRAME_W - w) / 2;
    ctx.drawImage(this.imgs[i], dx, foot - h, w, h);
    if (tintA > 0.004) {
      ctx.save();
      ctx.globalCompositeOperation = 'source-atop';
      ctx.fillStyle = rgba(tint, tintA);
      // source-atop 只会落在已经画出来的像素上，所以填满整张画布是白费的 ——
      // 角色帧就占中间那条横带，按它的实际矩形填，结果一模一样
      ctx.fillRect(dx, foot - h, w, h);
      ctx.restore();
    }
    this.shown = i;
  }
}

/* ---------- 2D 绘制（背景层 / 特效层） ---------- */
function tex(g2, stops) {
  const c = document.createElement('canvas'); c.width = 64; c.height = 1;
  const g = c.getContext('2d'), grad = g.createLinearGradient(0, 0, 64, 0);
  stops.forEach(s => grad.addColorStop(s[0], s[1]));
  g.fillStyle = grad; g.fillRect(0, 0, 64, 1); return c;
}
function glowTex(c) {
  const s = 192, cv = document.createElement('canvas'); cv.width = cv.height = s;
  const g = cv.getContext('2d'), gr = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  gr.addColorStop(0, rgba(c, .85)); gr.addColorStop(.45, rgba(c, .3)); gr.addColorStop(1, rgba(c, 0));
  g.fillStyle = gr; g.fillRect(0, 0, s, s); return cv;
}
let TX, GLOW;
function initTex() {
  TX = {
    band: tex(0, [[0, 'rgba(255,255,255,0)'], [.42, 'rgba(255,250,235,.9)'], [.5, 'rgba(255,255,255,1)'],
      [.58, 'rgba(255,250,235,.9)'], [1, 'rgba(255,255,255,0)']]),
    gL: tex(0, [[0, rgba(GREEN, 0)], [.55, rgba(GREEN, .55)], [1, rgba(GREEN, 1)]]),
    rR: tex(0, [[0, rgba(RED, 1)], [.45, rgba(RED, .55)], [1, rgba(RED, 0)]]),
  };
  GLOW = glowTex([255, 244, 220]);
}

function ribbon(ctx, t, top, bot, slices, widthAt, alphaAt, anchor) {
  const h = (bot - top) / slices;
  for (let i = 0; i < slices; i++) {
    const y0 = top + h * i, d = (i + .5) / slices;
    const a = alphaAt(d, i), w = widthAt(d, i);
    if (a <= .004 || w <= .5) continue;
    const x = frontAt(y0 + h / 2) + FX.jit;
    ctx.globalAlpha = a;
    ctx.drawImage(t, anchor < 0 ? x - w : anchor > 0 ? x : x - w / 2, y0, w, h + 1);
  }
}

/* k 是整体强度。这条线要画两遍：一遍在角色之下当背景光柱，一遍以更低的
   强度叠在角色之上 —— 两个人正好在中间抢东西，只画在下面的话对抗线全程
   被两具身体挡死，而它是这个玩法唯一的战况读数。 */
function drawLine(ctx, k = 1) {
  const pulse = .76 + Math.sin(S.t * 13) * .14 + Math.sin(S.t * 29) * .08;
  const depth = d => .42 + d * .58;
  const yAt = d => TOP + (BOT - TOP) * d;
  const fade = d => Math.min(1, d * 7) * Math.min(1, (1 - d) * 9);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const sideW = d => (92 + d * 150) * (.55 + heatAt(yAt(d)) * .45);
  const sideA = d => pulse * depth(d) * (.35 + heatAt(yAt(d)) * .65) * fade(d) * .38 * k;
  ribbon(ctx, TX.gL, TOP, BOT, 26, sideW, sideA, -1);
  ribbon(ctx, TX.rR, TOP, BOT, 26, sideW, sideA, +1);
  ribbon(ctx, TX.band, TOP, BOT, 56,
    (d, i) => (16 + d * 40) * (.86 + Math.sin(S.t * 21 + i * .4) * .14) * (.42 + heatAt(yAt(d)) * .85),
    d => pulse * depth(d) * (.3 + heatAt(yAt(d)) * .8) * fade(d) * 0.95 * k, 0);
  ctx.globalAlpha = heatAt(BOT) * .3 * k;
  ctx.drawImage(GLOW, frontAt(BOT - 40) + FX.jit - 96, BOT - 168, 192, 192);
  ctx.restore(); ctx.globalAlpha = 1;
}

/* 对抗线的替代画法（?line=2）。
   原来那根贯穿全屏的发光柱（?line=1）在这张底图上表现力差，根因和白闪过曝
   是同一个：它走 lighter，而底图是明亮客厅 —— 浅绿墙本来就接近饱和，往上
   加光几乎不改变什么，只剩一团雾；龙王那边同样的写法很炸，是因为它的底图
   是暗色战场。更要命的是它正好横在两个人中间，把抢手机的手和脸挡掉了，而
   那是这个玩法唯一值得看的东西。

   所以战线改成在地上走：深色带 + 势力色描边，靠轮廓而不是靠发光，明亮底图
   上反而更显眼；又完全不挡人。读数一点没少 —— 战线横坐标仍然是 frontAt，
   和手机、顶端指针、地面辉光同一个源。 */
function drawFrontGround(ctx, bias) {
  const R = P.rug, col = Math.abs(bias) < 0.06 ? [250, 250, 250] : (bias > 0 ? GREEN : RED);
  const N = 14;
  const xs = [], ys = [], ws = [];
  for (let i = 0; i <= N; i++) {
    const d = i / N, y = R.top + (R.bot - R.top) * d;
    ys.push(y); xs.push(frontAt(y) + FX.jit);
    ws.push(8 + d * 20);          // 下宽上窄，跟着地毯的透视走
  }
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(R.tl, R.top); ctx.lineTo(R.tr, R.top);
  ctx.lineTo(R.br, R.bot); ctx.lineTo(R.bl, R.bot); ctx.closePath();
  ctx.clip();
  ctx.beginPath();
  for (let i = 0; i <= N; i++) (i ? ctx.lineTo : ctx.moveTo).call(ctx, xs[i] - ws[i], ys[i]);
  for (let i = N; i >= 0; i--) ctx.lineTo(xs[i] + ws[i], ys[i]);
  ctx.closePath();
  /* 双描边：外圈暗、内圈势力色。单描边在地毯的绿和地板的米色上各有一段
     会掉对比，而这条带子从地毯一直压到地板边缘，横跨两种底色。 */
  ctx.fillStyle = 'rgba(22,18,26,.70)';
  ctx.fill();
  ctx.lineWidth = 7; ctx.strokeStyle = 'rgba(12,10,16,.55)'; ctx.stroke();
  ctx.lineWidth = 3.5; ctx.strokeStyle = rgba(col, .98); ctx.stroke();
  ctx.restore();
}

/* 战线在画面顶端的读数：一个不会被任何东西挡住的指针。
   它能脱离地面带单独存在（?line=3，默认），而且这正是推荐的用法 —— 地上
   那条带子横在两个人的腿中间，激烈的时候被挡掉大半，剩下的半截读起来像
   一根立在地上的杆子；指针在画面顶端，既不挡人也永远看得见。
   完全不画（?line=0）也能看出谁占优（地面辉光、血条都在），但读不
   出战线此刻**具体**压在哪一条竖线上，而手机位移就是这个玩法的进度条。 */
function drawFrontMark(ctx, bias) {
  const col = Math.abs(bias) < 0.06 ? [255, 255, 255] : (bias > 0 ? GREEN : RED);
  /* 指针整体压到 HUD 下沿之外。它的 x 随对抗线跑、三角有 42px 宽，留在原来
     的 TOP-2 会横着划过血条和拉力条 —— HUD 一放大就没地方躲了。 */
  const y = TOP + 36, x = frontAt(y) + FX.jit;
  ctx.save();
  ctx.strokeStyle = 'rgba(12,14,20,.6)'; ctx.lineWidth = 11;
  ctx.beginPath(); ctx.moveTo(x, y + 6); ctx.lineTo(x, y + 52); ctx.stroke();
  ctx.strokeStyle = rgba(col, .98); ctx.lineWidth = 6;
  ctx.beginPath(); ctx.moveTo(x, y + 6); ctx.lineTo(x, y + 52); ctx.stroke();
  ctx.fillStyle = rgba(col, 1);
  ctx.beginPath();
  ctx.moveTo(x, y + 16); ctx.lineTo(x - 21, y - 16); ctx.lineTo(x + 21, y - 16);
  ctx.closePath(); ctx.fill();
  ctx.lineWidth = 3.5; ctx.strokeStyle = 'rgba(12,14,20,.7)'; ctx.stroke();
  ctx.restore();
}

/* 地面辉光：手机被拽向谁，谁脚下的地就烧起来，浓度 = 领先幅度。
   不用"线两侧分色"——拔河里绳结被拽过去不等于对面丢了地盘，
   那个画法在极端档会把颜色铺反。 */
function drawGround(ctx, bias) {
  const R = P.rug, span = R.bot - R.top, k = Math.abs(bias);
  if (k < 0.02) return;
  const col = bias > 0 ? GREEN : RED;
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(R.tl, R.top); ctx.lineTo(R.tr, R.top);
  ctx.lineTo(R.br, R.bot); ctx.lineTo(R.bl, R.bot); ctx.closePath();
  ctx.clip();
  ctx.globalCompositeOperation = 'lighter';
  const win = bias > 0 ? 0 : W;                       // 赢家所在的那一侧
  const g = ctx.createLinearGradient(win, 0, W - win, 0);
  g.addColorStop(0, rgba(col, 0.42 * k));
  g.addColorStop(1, rgba(col, 0.04 * k));
  ctx.fillStyle = g; ctx.fillRect(0, R.top, W, span);
  // 手机正下方的落点亮斑：战线此刻具体压在地上的哪个位置
  const fx = frontAt(R.bot - 90) + FX.jit;
  const rg = ctx.createRadialGradient(fx, R.bot - 70, 0, fx, R.bot - 70, 250);
  rg.addColorStop(0, rgba(col, 0.30 + 0.28 * k));
  rg.addColorStop(1, rgba(col, 0));
  ctx.fillStyle = rg; ctx.fillRect(0, R.top, W, span);
  ctx.restore();
}

/* ── HUD ──
   顶上一侧是一个整体：头像 · 队名 · 血条 · 拉力条，左右严格镜像。做成一个
   单元是因为观众要在半秒内读出"绿色这边是谁、他还剩多少、他现在猛不猛"——
   零散摆着的色块做不到这件事，那是调试面板不是直播画面。

   三个数各有各的位置，谁也不冒充谁：
     血条   存量。只减不增，归零就输，所以它最大、最上面。
     侵蚀带 血条末端那截脉动的暖色 —— 宽度 = 再这样扣两秒会没掉的量。
            血量制下掉血是连续的小数，一秒扣一滴时血条几乎不动，光看长度
            读不出"正在挨打"。这截暖色就是把 S.dpsA/B 画出来。
     拉力条 存量之下的细条。双方一起涨 = 在对拼（谁也不掉血）；长出来的
            那一截才是战况。开方标度是为了让小额礼物也推得动它。
   中间是时钟，时钟下面一行小字直接报"此刻每秒扣谁多少血"——这是全屏唯一
   一处把因果写成字的地方，僵持时它就写"僵持"。 */

// 两侧严格镜像：右侧的 x 一律由 W - x - w 推出来，改一处两边一起动
const UI = {
  /* 直播间里这块画面会被缩到手机屏的三分之一宽，条细一点、字小一号就彻底
     看不清了。所以横向**顶满**：头像缩成贴在队名左边的小圆，血条从边缘 18px
     一直铺到离中线 20px，两条之间只留 40px 缝。
     竖向吃到 145 为止 —— 对抗线的指针三角从 y=148 开始横扫全宽，越过去就会
     被它划一道（指针的 x 随对抗线跑，不是待在中间）。
     排这一块要连**描边**一起算：文字的 lineWidth 5 会往外扩 2.5px，按字号
     算出来刚好够的位置，画出来就啃到血条底边了。 */
  avR: 30, avCX: 44, avCY: 35,       // 头像圆：左侧圆心，右侧 = W - 它
  barX: 18, barW: 442, barY: 66, barH: 44,    // 血条
  /* 时钟在血条**上方**、拉力在血条**下方**。两块都在中间那段，左右是头像和队名。
     下面这条带子只有 38px 净空：血条底边 110，再往下 148 就是指针三角横扫的
     那一行。所以拉力的底板压到 30 高（116~146），34px 的数字墨区约 24px，
     上下各剩 3px。和血条之间留 6px 缝 —— 两条深色描边贴在一起会并成一道粗黑带，
     读成"血条破了"。 */
  clkCY: 33,                         // 时钟那一行的中心（血条上面）
  pwCY: 131,                         // 拉力那一行的中心（血条下面，见 drawPowerText）
  sk: 12,                            // 斜切量：顶边相对底边右移多少（右侧取反）
};

/* HUD 自己的表现层状态。单独放一坨，是为了让人一眼看出改这里不会改谁输谁赢 ——
   战况全在 S 里，这里只有"闪一下""跳一下"这种活儿。 */
const HUD = {
  avA: null, avB: null,   // 两张头像（assets/ui/av_*.webp，加载不到就画纯色盘）
  lfA: 0, lfB: 0,         // 注入闪光余量：礼物砸进来那一下，拉力条整条亮一次
  pfA: 0, pfB: 0,         // 上一帧的拉力，用来把"礼物注入"和"自然增长"分开
  t: 0,                   // 脉动用的自走时钟
  pin: -1,                // ?hudflash= 把闪光钉住，见下（-1 = 不钉，正常衰减）
};

/* 斜切平行四边形：顶边相对底边横移 sk。直播 HUD 不用正方角是有道理的 ——
   正矩形在任何底图上都读成"控件"，切一刀就变成"装备"。 */
const skew = (ctx, x, y, w, h, sk) => {
  ctx.beginPath();
  ctx.moveTo(x + sk, y); ctx.lineTo(x + w + sk, y);
  ctx.lineTo(x + w, y + h); ctx.lineTo(x, y + h); ctx.closePath();
};
const txt = (ctx, str, x, y, fill, lw) => {
  ctx.lineWidth = lw; ctx.strokeStyle = 'rgba(0,0,0,.80)'; ctx.strokeText(str, x, y);
  ctx.fillStyle = fill; ctx.fillText(str, x, y);
};

/* 认出"这是一次注入"：礼物是瞬间跳变（最小的仙女棒也有 1 点），而自然增长
   在 60 帧下每帧只有零点几。2.5 这道坎把两者分得很干净。 */
function hudTick(dt) {
  HUD.t += dt;
  /* 注入闪光只亮半秒，截图永远抓不到它 —— 判断动态效果必须有专门的胶片参数，
     不然调强弱只能靠脑补。?hudflash=0..1 把两侧都钉在指定强度。 */
  if (HUD.pin >= 0) { HUD.lfA = HUD.lfB = HUD.pin; HUD.pfA = S.fA; HUD.pfB = S.fB; return; }
  if (S.fA - HUD.pfA > 2.5) HUD.lfA = 1;
  if (S.fB - HUD.pfB > 2.5) HUD.lfB = 1;
  HUD.pfA = S.fA; HUD.pfB = S.fB;
  HUD.lfA = Math.max(0, HUD.lfA - dt * 1.7);
  HUD.lfB = Math.max(0, HUD.lfB - dt * 1.7);
}

function drawAvatar(ctx, A) {
  const img = A ? HUD.avA : HUD.avB, c = A ? GREEN : RED;
  const dps = A ? S.dpsA : S.dpsB, hp = A ? S.hpA : S.hpB;
  const cx = A ? UI.avCX : W - UI.avCX, cy = UI.avCY, r = UI.avR;
  ctx.save();
  ctx.beginPath(); ctx.arc(cx, cy, r + 4, 0, 7); ctx.fillStyle = 'rgba(8,10,14,.92)'; ctx.fill();
  if (img) {
    ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.clip();
    ctx.drawImage(img, cx - r, cy - r, r * 2, r * 2);
    /* 底部压一层队色，让头像和血条是同一个人 —— 不然两个圆脸浮在那儿，
       跟下面的绿条红条没有任何关系。 */
    const g = ctx.createLinearGradient(0, cy + r * 0.1, 0, cy + r);
    g.addColorStop(0, rgba(c, 0)); g.addColorStop(1, rgba(c, .42));
    ctx.fillStyle = g; ctx.fillRect(cx - r, cy - r, r * 2, r * 2);
    ctx.restore();
  } else { ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.fillStyle = rgba(c, .55); ctx.fill(); }
  // 挨打时外圈红色脉动：谁在掉血，扫一眼头像就知道，不用去比两条的长度
  if (dps > 0.01) {
    const k = 0.5 + 0.5 * Math.sin(HUD.t * 7.5);
    ctx.beginPath(); ctx.arc(cx, cy, r + 6, 0, 7);
    ctx.lineWidth = 3; ctx.strokeStyle = `rgba(255,190,72,${0.34 + 0.56 * k})`; ctx.stroke();
  }
  /* 圈色就是身份：赢了镀金、倒下转灰、其余时候是队色。结算画面上观众第一眼
     找的是脸，让脸自己把结果说了，比在中间多写一行字快。 */
  const win = S.phase === 'over' && (A ? S.winner > 0 : S.winner < 0);
  const out = hp <= 0 || (S.phase === 'over' && S.winner !== 0 && !win);
  ctx.beginPath(); ctx.arc(cx, cy, r + 1.5, 0, 7);
  ctx.lineWidth = win ? 4.5 : 3.5;
  if (win) { ctx.shadowColor = 'rgba(255,208,80,.95)'; ctx.shadowBlur = 18; }
  ctx.strokeStyle = rgba(win ? [255, 212, 90] : out ? [110, 110, 118] : c, .96);
  ctx.stroke(); ctx.shadowBlur = 0;
  ctx.restore();
}

function drawHpBar(ctx, A) {
  const hp = clamp(A ? S.hpA : S.hpB, 0, 100), dps = A ? S.dpsA : S.dpsB;
  const c = A ? GREEN : RED;
  const x = A ? UI.barX : W - UI.barX - UI.barW, w = UI.barW, y = UI.barY, h = UI.barH;
  const sk = A ? UI.sk : -UI.sk, fw = w * hp / 100;
  ctx.save();
  // 见血了才报警：低于两成整条外缘透红呼吸，观众远远地就知道有人要没了
  if (hp < 20) {
    const k = 0.5 + 0.5 * Math.sin(HUD.t * 5.5);
    ctx.save(); ctx.shadowColor = `rgba(255,60,50,${0.5 + 0.45 * k})`; ctx.shadowBlur = 16;
    skew(ctx, x - 2, y - 2, w + 4, h + 4, sk); ctx.fillStyle = 'rgba(255,60,50,.22)'; ctx.fill();
    ctx.restore();
  }
  skew(ctx, x - 3, y - 3, w + 6, h + 6, sk); ctx.fillStyle = 'rgba(6,8,11,.88)'; ctx.fill();

  skew(ctx, x, y, w, h, sk); ctx.save(); ctx.clip();
  ctx.fillStyle = 'rgba(16,19,25,.70)'; ctx.fillRect(x - 20, y, w + 40, h);
  // 空槽里的斜纹：让"还剩多少"有个可数的底，纯黑一块读不出刻度
  ctx.fillStyle = 'rgba(255,255,255,.045)';
  for (let i = -2; i * 20 < w + 40; i++) { skew(ctx, x + i * 20, y, 9, h, sk); ctx.fill(); }

  if (fw > 0.5) {
    const fx0 = A ? x : x + w - fw;
    const g = ctx.createLinearGradient(0, y, 0, y + h);
    g.addColorStop(0, rgba(c.map(v => Math.min(255, v * 1.22 | 0)), 1));
    g.addColorStop(0.52, rgba(c, 1));
    g.addColorStop(1, rgba(c.map(v => v * 0.55 | 0), 1));
    ctx.fillStyle = g; ctx.fillRect(fx0, y, fw, h);
    ctx.fillStyle = 'rgba(255,255,255,.20)'; ctx.fillRect(fx0, y, fw, h * 0.28);
    /* 侵蚀带 —— 末端正在被啃掉的那截。宽度按"再扣两秒会没多少"算，所以
       对面刷得越猛这截越宽，一眼能看出是被小刀割还是被大哥碾。 */
    if (dps > 0.01) {
      const er = Math.min(clamp(w * dps / 100 * 4.5, 22, w * 0.34), fw);
      const ex = A ? x + fw - er : x + w - fw;
      const pk = 0.42 + 0.38 * Math.sin(HUD.t * 7.5);
      const eg = ctx.createLinearGradient(A ? ex : ex + er, 0, A ? ex + er : ex, 0);
      eg.addColorStop(0, 'rgba(255,190,60,0)');
      eg.addColorStop(1, `rgba(255,222,110,${0.26 + 0.5 * pk})`);
      ctx.fillStyle = eg; ctx.fillRect(ex, y, er, h);
    }
    // 末端亮口：血条的"当前位置"，退的时候这一条在动，比看整块色块灵敏
    ctx.fillStyle = 'rgba(255,255,255,.88)';
    ctx.fillRect(A ? x + fw - 4 : x + w - fw, y, 4, h);
  }
  ctx.restore();
  skew(ctx, x, y, w, h, sk);
  ctx.lineWidth = 1.5; ctx.strokeStyle = 'rgba(255,255,255,.22)'; ctx.stroke();
  ctx.restore();
}

/* 拉力直接写成"拉力 575"，不画条，而且**两边的数并排摆在正中**。
   不画条：条要成立得有个量程，而拉力是没有上限的存量（大哥一秒注入 600、对面
   只有 80 时差值能到四万），画条只能开方压缩 —— 压完小额礼物推不动它、大额又
   早早顶到头，两头都读不出来。写成数字两头都准：刷一件跳一截，跳多少和礼物的
   push 值一一对应。
   放正中：分列左右两侧时没人会去比，而这两个数**必须放在一起比** —— 扣血算的
   就是它们的差，差过了 X 才有人掉血。并排摆着，"我比他多多少"不用算。
   它比倒计时显眼一档也是故意的：观众刷礼物改变的是这个数，不是那个钟。
   排在血条**下方**：上方那行归时钟。 */
function drawPowerText(ctx) {
  const cy = UI.pwCY;
  ctx.save();
  ctx.textBaseline = 'middle';
  /* 底板宽度写死，不随位数变 —— 跟着数字宽窄伸缩的话，刷一件礼物牌子自己
     会抖一下，观众会以为是画面卡了。288 够放到五位数。 */
  ctx.beginPath(); ctx.roundRect(336, 116, 288, 30, 13);
  ctx.fillStyle = 'rgba(8,10,14,.74)'; ctx.fill();
  ctx.lineWidth = 1.5; ctx.strokeStyle = 'rgba(255,255,255,.20)'; ctx.stroke();

  ctx.textAlign = 'center';
  ctx.font = 'bold 22px system-ui,"PingFang SC","Microsoft YaHei",sans-serif';
  txt(ctx, '拉力', MID, cy, 'rgba(232,238,246,.80)', 4);

  ctx.font = 'bold 34px ui-monospace,Menlo,monospace';
  for (const A of [true, false]) {
    const f = A ? S.fA : S.fB, c = A ? GREEN : RED, lf = A ? HUD.lfA : HUD.lfB;
    ctx.textAlign = A ? 'right' : 'left';
    // 礼物砸进来那一下数字整个亮一次 —— 原先条上那个菱形滑块的活
    if (lf > 0) { ctx.shadowColor = rgba(c, .95); ctx.shadowBlur = 22 * lf; }
    txt(ctx, f.toFixed(0), A ? MID - 38 : MID + 38, cy,
        `rgb(${c.map(v => Math.min(255, (v * (1.18 + .5 * lf)) | 0)).join(',')})`, 5.5);
    ctx.shadowBlur = 0;
  }
  ctx.restore();
}

function drawHUD(ctx) {
  const hA = clamp(S.hpA, 0, 100), hB = clamp(S.hpB, 0, 100);
  ctx.save();
  for (const A of [true, false]) {
    ctx.textBaseline = 'middle';
    drawAvatar(ctx, A);
    drawHpBar(ctx, A);
    /* 队名和百分比并排在血条**上方**的外侧，条里一个字都不放。
       放进条里试过两版，压外端会在残血时和末端亮口叠在一起，压内端满血时
       又被侵蚀带盖住 —— 填充的末端迟早要扫过整条，数字待在条里就没有安全
       位置。挪出来之后两边各是一行"谁 · 剩多少"，条本身只管长度。
       放外侧是为了避开中线：那儿归时钟和战况读数。 */
    const hv = A ? hA : hB, ox = A ? 1 : -1;
    const nx = (A ? UI.avCX : W - UI.avCX) + ox * (UI.avR + 12);   // 队名从头像右缘起
    ctx.textAlign = A ? 'left' : 'right';
    ctx.font = 'bold 30px system-ui,"PingFang SC","Microsoft YaHei",sans-serif';
    txt(ctx, A ? '查岗党' : '灭迹党', nx, UI.avCY, '#fff', 6);
    ctx.font = 'bold 37px ui-monospace,Menlo,monospace';
    txt(ctx, hv.toFixed(0) + '%', nx + ox * 114, UI.avCY, hv < 20 ? '#ff8a7a' : '#fff', 6.5);
  }

  /* 时钟和拉力**不等开局**：页面一打开就摆在那儿（时钟满时长、拉力 0:0）。
     等 phase 变成 play 才画的话，观众进直播间看到的是半块 HUD，第一件礼物
     砸下来才突然冒出两行字 —— 会读成"卡了一下"，而不是"开打了"。 */
  {
    const idle = S.phase === 'idle';
    const mm = Math.max(0, S.clock);
    let tip = `${mm / 60 | 0}:${String(mm % 60 | 0).padStart(2, '0')}`, col = '#fff', bg = 'rgba(8,10,14,.74)';
    if (S.phase === 'sudden') { tip = `绝杀 ${S.sudden.toFixed(0)}`; col = '#ff6a5a'; bg = 'rgba(52,8,10,.86)'; }
    else if (S.phase === 'over') { tip = S.winner > 0 ? '查岗党胜' : S.winner < 0 ? '灭迹党胜' : '平局'; col = '#ffd45a'; bg = 'rgba(46,34,6,.88)'; }
    else if (S.stand > 0) { tip = `反击 ${S.stand.toFixed(0)}`; col = '#ffd45a'; bg = 'rgba(46,34,6,.86)'; }
    /* 时钟和战况读数并排成一行，放在血条上方；拉力在血条下方。
       倒计时排在拉力对面、字也小一号是有意的：观众刷礼物改变的是拉力，
       不是那个钟；钟只在最后半分钟才重要，而那时它会变成"绝杀 18"自己跳出来。 */
    drawPowerText(ctx);
    const d = S.dpsA > 0.01 ? S.dpsA : S.dpsB, hurtA = S.dpsA > 0.01;
    const over = S.phase === 'over';
    // 还没开局时不写"僵持"——那是对局里"谁都没掉血"的读数，待机时写它是假的
    const note = over || idle ? '' : d > 0.01
      ? (hurtA ? `◀ 每秒 ${d.toFixed(1)}` : `每秒 ${d.toFixed(1)} ▶`) : '僵 持';
    ctx.textBaseline = 'middle';
    ctx.font = `bold ${over ? 27 : 23}px ui-monospace,Menlo,monospace`;
    const tw = ctx.measureText(tip).width;
    ctx.font = 'bold 21px system-ui,"PingFang SC","Microsoft YaHei",sans-serif';
    const nw = note ? ctx.measureText(note).width + 18 : 0;
    /* 这块底板得跟着内容伸缩 —— 它下面 18px 就是指针三角横扫的那一行，
       写死一个够宽的值会在"僵持"时空出一大片压在画面上。 */
    const bw = tw + nw + 36, bx = MID - bw / 2;
    ctx.save();
    ctx.beginPath(); ctx.roundRect(bx, UI.clkCY - 17, bw, 34, 15);
    ctx.fillStyle = bg; ctx.fill();
    ctx.lineWidth = 1.5; ctx.strokeStyle = 'rgba(255,255,255,.18)'; ctx.stroke();
    ctx.restore();
    ctx.textAlign = 'left';
    ctx.font = `bold ${over ? 27 : 23}px ui-monospace,Menlo,monospace`;
    txt(ctx, tip, bx + 18, UI.clkCY, col, 4);
    if (note) {
      ctx.font = 'bold 21px system-ui,"PingFang SC","Microsoft YaHei",sans-serif';
      txt(ctx, note, bx + 18 + tw + 18, UI.clkCY,
          d > 0.01 ? '#ffd86e' : 'rgba(232,236,242,.70)', 4);
    }
  }
  ctx.restore();
}

/* ---------- 启动 ---------- */
const load = (src) => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = src; });

(async function boot() {
  const cvBg = document.getElementById('bg'), cvCh = document.getElementById('ch'), cvFx = document.getElementById('fx');
  const bctx = cvBg.getContext('2d'), cctx = cvCh.getContext('2d'), fctx = cvFx.getContext('2d');
  initTex();

  /* ?sim=1 纯数值快进：不渲染、不发弹幕，只跑 battle，用来核对局长和手感。
     数值调参不该靠看画面 —— 一局十二分钟，肉眼比对两组参数根本比不出来，
     而这里两秒钟就能把三个场景各跑一遍。
       simA/simB  两边每秒注入多少火力（一个爱的爆炸是 230）
       simT       最多模拟多少秒
     例：?sim=1&simA=23&simB=11.5  = 优势方每 10 秒一个爱的爆炸、劣势方一半 */
  const Q0 = new URLSearchParams(location.search);
  if (Q0.has('sim')) {
    const injA = +(Q0.get('simA') || 23), injB = +(Q0.get('simB') || 0);
    const cap = +(Q0.get('simT') || 1800);
    Ammo.launch = () => {};                     // 纯数值，不要表现层
    startMatch();
    const H = 1 / 30;
    let el = 0, mark50 = -1, mark80 = -1;
    while (S.phase !== 'over' && el < cap) {
      S.fA += injA * H; S.fB += injB * H;
      battle(H); el += H;
      // 挨打那一方掉到半血 / 只剩两成的时刻 —— 局长看的是血，不是手机位置
      const low = Math.min(S.hpA, S.hpB);
      if (mark50 < 0 && low <= 50) mark50 = el;
      if (mark80 < 0 && low <= 20) mark80 = el;
    }
    const fmt = (v) => v < 0 ? '—' : `${v / 60 | 0}:${String(v % 60 | 0).padStart(2, '0')}`;
    document.getElementById('msg').textContent =
      `注入 ${injA}:${injB}／秒 → 结束于 ${fmt(el)}  血 ${S.hpA.toFixed(1)}:${S.hpB.toFixed(1)}  `
      + `拉力 ${S.fA.toFixed(0)}:${S.fB.toFixed(0)}  差 ${(S.fA - S.fB).toFixed(0)}  `
      + `对抗线 p=${S.p.toFixed(1)}  `
      + `半血 ${fmt(mark50)}  两成血 ${fmt(mark80)}  `
      + `${S.winner > 0 ? '查岗党胜' : S.winner < 0 ? '灭迹党胜' : '平/未分'}`;
    document.title = 'SIMDONE ' + document.getElementById('msg').textContent;
    return;
  }


  /* 弹幕命中的是对抗线在**它自己那个高度**上的横坐标，不是中点。所以从不同
     高度飞来的弹幕会在不同的行注入冲量 —— 在这之前所有命中都发生在 phoneY
     一个位置上，那条线永远只在同一处抖。 */
  Ammo.init({
    W, frontAt,
    /* 命中只负责演出，**不扣血也不推手机**。血是双方拉力差每秒扣出来的、手机
       位置是拉力差的读数（都见 battle）—— 让命中再推一次，等于同一份伤害算
       两遍，而且会把"两边都在刷时谁也不掉血"这条最要紧的手感破坏掉。
       弹幕是拉力的表现形式，不是伤害的来源。 */
    onHit(p) {
      impact(-p.from, p.y, p.exec ? 4 : p.g.power, RECIPE[p.g.recipe]);
    },
    /* 对冲掉的那些在中线互相撞掉：粒子照爆，但不推角色、不染色、不顿帧。
       它要回答的问题只有一个 —— "我刷了礼物怎么手机没动"。答案就在画面上：
       你的东西被对面在半空撞掉了。 */
    onClash(p, x) {
      RECIPE[p.g.recipe].burst(x, p.y, p.from, 0.42);
      Particles.addShake(0.6);
    },
  });

  /* 气泡挂在手机上 —— phonePos 是对抗线在手机高度上的横坐标，跟手机、地面
     辉光同一个源，所以消息永远是从正在被抢的那部手机里冒出来的。 */
  Bubble.init({ phoneAt: phonePos });

  const bg = await load('assets/bg.jpg');
  /* 每 1% 一张。缺的档位解码失败是预期内的，取 null 交给 FrameSeq 映射到邻居。 */
  const frames = await Promise.all(
    Array.from({ length: 101 }, (_, p) =>
      load(`assets/frames/f${String(p).padStart(3, '0')}.png`).catch(() => null)));
  const seq = new FrameSeq(frames);
  /* HUD 头像。离线从 girl.png / boy.png 裁好的 160 方图，两张共 21KB ——
     立绘原图是 760×1145，只为取两个脸去加载它们不值当。 */
  [HUD.avA, HUD.avB] = await Promise.all(
    ['av_a', 'av_b'].map(n => load(`assets/ui/${n}.webp`).catch(() => null)));
  /* 3D 转盘贴图，两套：飞行物品的（ammo.js）和命中粒子的（fx.js）。
     失败不阻塞 —— 加载不到就退回各自的矢量画法，?nosprite=1 同时关掉两套。 */
  // 结算演出图。失败不阻塞：缺素材时结算退到纯色板，照样把结果交代清楚
  const resN = await Result.load(Q0.get('v'));
  const noSpr = Q0.get('nosprite') === '1';
  const [sprOK, shpOK] = await Promise.all([
    Ammo.loadSprites(Q0.get('v'), noSpr),
    Particles.loadShapes(Q0.get('v'), noSpr),
  ]);
  document.getElementById('msg').textContent =
    `${frames.filter(Boolean).length}/101 档 · 每 1%` +
    (sprOK.some(Boolean) ? ` · 物品转盘 ${sprOK.filter(Boolean).length}` : '') +
    (shpOK.some(Boolean) ? ` · 粒子 ${shpOK.filter(Boolean).length}` : '') +
    (resN ? ` · 结算 ${resN}` : '');

  const Q = new URLSearchParams(location.search);

  /* ?live=1&liveA=&liveB=&livet= 真实对局截图模式。
     数值可以用 ?sim 验，但"火力条好不好读""对撞看不看得出来""处决够不够狠"
     只能看画面。快进到指定秒数再渲染，就能截到任意战况下的那一帧。 */
  let liveA = 0, liveB = 0, live = false, freeze = false, stopAll = false;
  if (Q.has('live')) {
    live = true;
    liveA = +(Q.get('liveA') || 23); liveB = +(Q.get('liveB') || 11.5);
    startMatch();
    const warm = clamp(+(Q.get('livet') || 0), 0, 600);
    // liveGift 在预热的最后一刻送一件礼物出去 —— 顿帧、独占、处决这些只在
    // 落地后的零点几秒里存在，不指定时刻的话截不到
    const gk = Q.get('liveGift'), gAt = clamp(+(Q.get('liveAt') || warm), 0, 600);
    /* ?liveEvery=<秒>&liveGA=<礼物>&liveGB=<礼物> 按**真实送礼节奏**预热。
       liveA/liveB 是直接往 S.fA 上加数，绕开了 giveGift —— 于是礼物计数、
       tier3/4 的减益、反击时刻的加成这些统统不发生。要看"一局真的这么打下来
       是什么样"（含结算那格礼物数），只能走这条路。 */
    const every = Math.max(0, +(Q.get('liveEvery') || 0));
    const gA = Q.get('liveGA'), gB = Q.get('liveGB');
    for (let k = 0; k < warm * 30; k++) {
      /* 分出胜负之后不再注入。这一局已经打完了，照注的话结算面板上"最终拉力"
         和"礼物"会一路涨下去，跟旁边那格"本局时长"对不上 —— 截出来的图自相
         矛盾（实测：26 秒结束的一局显示送了 12 件礼物）。 */
      if (S.phase !== 'over') {
        S.fA += liveA / 30; S.fB += liveB / 30;
        if (every > 0 && k % Math.round(every * 30) === 0) {
          if (gA) giveGift(+1, gA);
          if (gB) giveGift(-1, gB);
        }
        if (gk && k === Math.floor(gAt * 30)) giveGift(+(Q.get('liveSide') || 1), gk);
      }
      battle(1 / 30); Ammo.update(1 / 30); Particles.update(1 / 30); S.t += 1 / 30; derive(1 / 30);
    }
    // 预热完冻住**进度**：战况定在这一刻，而火力、弹幕、粒子照跑 —— 截图要的
    // 是"打到这个比分时画面是活的什么样"，不是一张静止的死图
    if (Q.get('liveFreeze') === '1') freeze = true;
    // liveStop 把整个世界停在预热结束那一帧：要看清"处决落地的瞬间"只能这样，
    // 它只存在零点几秒，主循环再跑一下就过去了
    if (Q.get('liveStop') === '1') { stopAll = true; live = false; }
  }
  if (Q.has('p')) { S.p = clamp(+Q.get('p'), 0, 100); S.auto = false; }
  /* 自动演示默认就是关的（见 S.auto），?auto=1 才打开 —— 展示时它会自己来回
     拽手机，观众分不清哪一下是刷礼物推的。?auto=0 保留着，写脚本时不用管
     默认值是什么。 */
  if (Q.get('auto') === '0') S.auto = false;
  if (Q.get('auto') === '1') S.auto = true;
  /* X / M / Z 三个数就地试：?x=30&m=1000&z=5。Z 决定局长 —— 5 是需求例子里
     那个"差 1000 每秒扣 5%"（约 70 秒一局），0.27 是 12 分钟局长的值。 */
  if (Q.has('x')) NUM.PULL_X = Math.max(0, +Q.get('x'));
  if (Q.has('m')) NUM.PULL_M = Math.max(1, +Q.get('m'));
  if (Q.has('z')) NUM.HP_Z = Math.max(0, +Q.get('z'));
  if (Q.has('linefull')) NUM.LINE_FULL = Math.max(1, +Q.get('linefull'));
  // ?hudflash=0..1 钉住拉力条的注入闪光，专门用来截"礼物砸进来那一下"的形态
  if (Q.has('hudflash')) HUD.pin = clamp(+Q.get('hudflash'), 0, 1);
  if (Q.has('overt')) Result.setPin(Math.max(0, +Q.get('overt')));   // 结算定帧
  if (Q.has('line')) S.line = clamp(+Q.get('line') | 0, 0, 3);
  // ?zoom=1 用画布原生尺寸铺开，截图时才看得清脸和手的实际画法
  if (Q.get('zoom') === '1') document.getElementById('stage').style.width = W + 'px';
  document.getElementById('pv').value = S.p;
  document.getElementById('auto').checked = S.auto;
  for (let i = 0; i < 90; i++) derive(1 / 60);   // 预热，让指数趋近收敛到位

  /* 震动只作用在"正在发生冲突的东西"上 —— 对抗线、角色、粒子。
     房间和地毯不动：机位是固定的，整幅画面一起震就得把背景放大做 overscan
     才不露边，而背景一放大，地毯四角那组标定坐标就全偏了。HUD 也不震，它
     不在场景里。 */
  /* 拆成三段是因为它本来就是三张画布、三种代价：底版每帧重画一张 960x1334
     的照片，角色每帧重画一张 900 高的 PNG，特效层则随着场上有多少东西线性
     涨。"哪一层在拖后腿"只有分开计时才答得出，而合在一个函数里就只能猜。 */
  function renderBg() {
    const bias = (FX.pDraw - 50) / 50;
    const ox = Particles.off.x, oy = Particles.off.y;
    bctx.clearRect(0, 0, W, H);
    bctx.drawImage(bg, 0, 0, W, H);
    drawGround(bctx, bias);
    bctx.save(); bctx.translate(ox, oy);
    if (S.line === 1) drawLine(bctx);
    else if (S.line === 2) drawFrontGround(bctx, bias);
    bctx.restore();
  }

  function renderActors() {
    const ox = Particles.off.x, oy = Particles.off.y;
    cctx.clearRect(0, 0, W, H);
    cctx.save(); cctx.translate(ox, oy);
    seq.draw(cctx, FX.pDraw, FX.actorX, FX.punch, FX.tint, FX.tintA);
    cctx.restore();
  }

  function renderFx() {
    const bias = (FX.pDraw - 50) / 50;
    const ox = Particles.off.x, oy = Particles.off.y;
    fctx.clearRect(0, 0, W, H);
    fctx.save(); fctx.translate(ox, oy);
    /* line=1 要在角色之上再叠一遍，否则光柱全程被两具身体挡死；line=2 的
       带子在地上，挡住了也没关系 —— 顶端那个指针替它做读数。 */
    if (S.line === 1) drawLine(fctx, 0.42);
    else if (S.line >= 2) drawFrontMark(fctx, bias);
    // 气泡在弹幕之下：它贴在后面那堵墙上，弹幕是前景，飞过时该压过去
    Bubble.draw(fctx);
    /* 弹幕在角色之上、粒子之下：它飞向两个人中间，画在角色底下的话命中前
       最后那段就被身体挡掉了；而粒子是命中的爆炸，该盖在弹幕上面。 */
    Ammo.draw(fctx);
    Particles.draw(fctx);
    fctx.restore();
    /* 血条读 S.hpA / S.hpB，不读手机位置。手机位置是"这一刻谁拽赢了"，会
       来回晃、也会被对面追回去；血量是"这段时间里被压了多久"的累计，只减
       不增。两者本来就是两件事 —— 拔河时绳子来回而没有人真的前进，正是这个
       意思，而血条要回答的是"这么耗下去谁先倒"。 */
    /* 结算全屏接管：演出图铺满整幅，血条不再画。顶上那两条属于对局中，
       结果已经写在画面里（谁在抡枕头、谁跪着哭），再摆一遍是重复。 */
    if (S.phase === 'over') Result.draw(fctx);
    else drawHUD(fctx);
    Particles.drawFlash(fctx, W, H);
  }

  function render() { renderBg(); renderActors(); renderFx(); }

  /* ?strip=N 出一条连帧胶片：一次看清 N 个档位之间过不过得去。
     动画在静止截图里看不出问题，只有把相邻档位并排摆着才看得出哪一格在跳。 */
  if (Q.has('strip')) {
    // 胶片要的是各档之间的**纯**差异，拉锯会给每格叠上同一个偏移，关掉
    P.sway = 0;
    const n = clamp(+Q.get('strip') | 0, 2, 21), sc = 0.5;
    const out = document.createElement('canvas');
    out.width = n * W * sc; out.height = H * sc;
    const o = out.getContext('2d');
    o.fillStyle = '#0c0e12'; o.fillRect(0, 0, out.width, out.height);
    for (let i = 0; i < n; i++) {
      S.p = i * 100 / (n - 1); S.auto = false;
      FX.phoneX = MID; FX.rowOff.fill(0); FX.rowHeat.fill(0); S.t = 3.0;
      for (let k = 0; k < 150; k++) derive(1 / 60);
      render();
      const dx = i * W * sc;
      for (const c of [cvBg, cvCh, cvFx]) o.drawImage(c, dx, 0, W * sc, H * sc);
      o.fillStyle = 'rgba(0,0,0,.66)'; o.fillRect(dx, 0, 86, 26);
      o.fillStyle = '#fff'; o.font = '600 15px system-ui';
      o.fillText(`p=${S.p.toFixed(0)}`, dx + 8, 18);
    }
    const stage = document.getElementById('stage');
    stage.style.width = out.width + 'px';
    stage.style.aspectRatio = `${out.width}/${out.height}`;
    stage.innerHTML = '';
    out.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    stage.appendChild(out);
    return;
  }

  /* ?swaystrip=N 看空闲拉锯：**同一个 S.p**，只让时间往前走，N 格并排。
     这是唯一能看清它的办法 —— 拉锯是纯时间函数，单张截图里跟静止画面长得
     一模一样，而两张不同时刻的截图又分不清"是拉锯在动"还是"页面还没加载完"。
     每格标出 pDraw 与手机 x，位移直接读数。
     ?swayp= 定在哪个进度看（默认 50）；越靠近端点 calm 越小，拉锯该越弱，
     这条也靠它验证。?swayms= 每格之间推进多少毫秒（默认 700）。
     ?swayfire= 给查岗党一侧注入这么多火力（净差＝它本身）—— 验的是"战况正在
     被推时拉锯有没有让位"。给 0 和给 230（一件爱的爆炸③）各拍一条，前者该摆、
     后者该基本不动，两条并排看就知道让位是不是真的生效了。 */
  if (Q.has('swaystrip')) {
    const n = clamp(+Q.get('swaystrip') | 0, 2, 12), sc = 0.5;
    const MS = clamp(+(Q.get('swayms') || 700), 60, 4000) / 1000;
    S.p = clamp(+(Q.get('swayp') || 50), 0, 100); S.auto = false;
    const fire = clamp(+(Q.get('swayfire') || 0), 0, 4000);
    S.fA = fire; S.fB = 0;
    const out = document.createElement('canvas');
    out.width = n * W * sc; out.height = H * sc;
    const o = out.getContext('2d');
    o.fillStyle = '#0c0e12'; o.fillRect(0, 0, out.width, out.height);
    // 先空跑两秒：phoneX 是趋近过去的，不预热的话第一格还停在画面正中
    S.t = 0;
    for (let k = 0; k < 120; k++) { S.t += 1 / 60; derive(1 / 60); }
    for (let i = 0; i < n; i++) {
      if (i) for (let k = 0, m = Math.round(MS * 60); k < m; k++) { S.t += 1 / 60; derive(1 / 60); }
      render();
      const dx = i * W * sc;
      for (const c of [cvBg, cvCh, cvFx]) o.drawImage(c, dx, 0, W * sc, H * sc);
      o.fillStyle = 'rgba(0,0,0,.66)'; o.fillRect(dx, 0, 196, 26);
      o.fillStyle = '#fff'; o.font = '600 15px system-ui';
      o.fillText(`t=${S.t.toFixed(1)}s  pDraw=${FX.pDraw.toFixed(1)}  x=${FX.phoneX.toFixed(0)}`, dx + 8, 18);
    }
    const stage = document.getElementById('stage');
    stage.style.width = out.width + 'px';
    stage.style.aspectRatio = `${out.width}/${out.height}`;
    stage.innerHTML = '';
    out.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    stage.appendChild(out);
    return;
  }

  /* ?ammostrip=N 看一发弹幕从出场到命中的全过程。飞行节奏是这个功能的全部，
     而它在静止截图里根本不存在 —— 得把整条轨迹按时间摊开才看得出速度合不
     合适、预警够不够长、命中点准不准。
     ?ammogift=<礼物名> 选哪一件，?ammoy=<高度> 固定发射高度（随机高度会让
     每次截出来的图不一样，没法对比）。 */
  if (Q.has('ammostrip')) {
    const n = clamp(+Q.get('ammostrip') | 0, 2, 12);
    const MS = clamp(+(Q.get('ammoms') || 110), 16, 400) / 1000;
    const sc = 0.5, gname = Q.get('ammogift') || 'pillow';
    /* ?ammospin=<rad/s> 临时换转速、?ammobare=1 只画本体（关掉色晕/拖尾/残影）。
       "看不出体积感"可能是转太快、也可能是被特效糊住，这两个因素在成品图里
       纠缠在一起，分不开就只能靠猜。给两个开关才能一次分清。 */
    const g = Q.has('ammospin')
      ? { ...(GIFT[gname] || GIFT.pillow), spin: clamp(+Q.get('ammospin'), 0, 40) }
      : (GIFT[gname] || GIFT.pillow);
    Ammo.setBare(Q.get('ammobare') === '1');
    S.auto = false; S.t = 3.0;
    for (let k = 0; k < 150; k++) derive(1 / 60);

    const out = document.createElement('canvas');
    out.width = n * W * sc; out.height = H * sc;
    const o = out.getContext('2d');
    o.fillStyle = '#0c0e12'; o.fillRect(0, 0, out.width, out.height);

    Ammo.launch(g, clamp(+(Q.get('ammoy') || 560), 300, 960));
    let el = 0;
    for (let i = 0; i < n; i++) {
      const step = i === 0 ? 1 / 60 : MS;
      for (let k = 0; k < Math.max(1, Math.round(step * 60)); k++) {
        const d = Particles.tick(1 / 60);
        Particles.update(1 / 60);
        Ammo.update(d);
        Bubble.update(d, FX.struggle);
        derive(d); hudTick(d);
      }
      el += step;
      render();
      const dx = i * W * sc;
      for (const c of [cvBg, cvCh, cvFx]) o.drawImage(c, dx, 0, W * sc, H * sc);
      o.fillStyle = 'rgba(0,0,0,.66)'; o.fillRect(dx, 0, 168, 26);
      o.fillStyle = '#fff'; o.font = '600 15px system-ui';
      o.fillText(`+${Math.round(el * 1000)}ms 弹${Ammo.count()} 粒${Particles.count()}`, dx + 8, 18);
      if (i === 0) {
        o.fillStyle = 'rgba(0,0,0,.66)'; o.fillRect(dx, 26, 168, 24);
        o.fillStyle = '#ffd36b';
        o.fillText(`${g.name || gname} · ${g.style} · spin ${g.spin} · p=${S.p.toFixed(0)}`, dx + 8, 42);
      }
    }
    const stage = document.getElementById('stage');
    stage.style.width = out.width + 'px';
    stage.style.aspectRatio = `${out.width}/${out.height}`;
    stage.innerHTML = '';
    out.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    stage.appendChild(out);
    return;
  }

  /* ?bubblestrip=N 专看气泡：每格推一条，四种轮流。
     混在别的胶片里碰运气是拍不到的 —— 气泡自己按一两秒的节奏随机冒，想看
     的那一种（比如语音条、撤回提示）多半正好没出现；而要检查的恰恰是它们
     堆起来之后挡不挡脸、四种底色在这张墙上分不分得开。
     ?bubblems=M 每格间隔，默认 420ms。 */
  if (Q.has('bubblestrip')) {
    const n = clamp(+Q.get('bubblestrip') | 0, 2, 12);
    const MS = clamp(+(Q.get('bubblems') || 420), 16, 2000) / 1000;
    const sc = 0.5, types = ['text', 'hot', 'sys', 'voice'];
    S.auto = false; S.t = 3.0;
    for (let k = 0; k < 150; k++) derive(1 / 60);
    Bubble.clear();

    const out = document.createElement('canvas');
    out.width = n * W * sc; out.height = H * sc;
    const o = out.getContext('2d');
    o.fillStyle = '#0c0e12'; o.fillRect(0, 0, out.width, out.height);
    for (let i = 0; i < n; i++) {
      Bubble.push(types[i % 4]);
      for (let k = 0; k < Math.max(1, Math.round(MS * 60)); k++) {
        Bubble.update(1 / 60, FX.struggle);
        derive(1 / 60);
      }
      render();
      const dx = i * W * sc;
      for (const c of [cvBg, cvCh, cvFx]) o.drawImage(c, dx, 0, W * sc, H * sc);
      o.fillStyle = 'rgba(0,0,0,.70)'; o.fillRect(dx, 0, 150, 26);
      o.fillStyle = '#ffd36b'; o.font = '600 15px system-ui';
      o.fillText(`+${Math.round(i * MS * 1000)}ms 气泡${Bubble.count()}`, dx + 8, 18);
    }
    const stage = document.getElementById('stage');
    stage.style.width = out.width + 'px';
    stage.style.aspectRatio = `${out.width}/${out.height}`;
    stage.innerHTML = '';
    out.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    stage.appendChild(out);
    return;
  }

  /* ?linestrip=1 把对抗线的三种画法并排摆着比。三档各截一张再拼是不行的
     —— 每张 headless 截图要等一百秒，而且三张之间 S.t 不同，线的抖动相位
     对不上，看到的差别有一半是相位差不是画法差。 */
  if (Q.has('linestrip')) {
    const sc = 0.5, names = ['line=0 全去掉', 'line=1 原发光柱', 'line=2 地面战线+指针', 'line=3 只要指针'];
    S.auto = false; S.t = 3.0;
    for (let k = 0; k < 150; k++) derive(1 / 60);
    const out = document.createElement('canvas');
    out.width = names.length * W * sc; out.height = H * sc;
    const o = out.getContext('2d');
    o.fillStyle = '#0c0e12'; o.fillRect(0, 0, out.width, out.height);
    for (let i = 0; i < names.length; i++) {
      S.line = i;
      render();
      const dx = i * W * sc;
      for (const c of [cvBg, cvCh, cvFx]) o.drawImage(c, dx, 0, W * sc, H * sc);
      o.fillStyle = 'rgba(0,0,0,.72)'; o.fillRect(dx, 0, 160, 26);
      o.fillStyle = '#ffd36b'; o.font = '600 15px system-ui';
      o.fillText(`${names[i]}  p=${S.p.toFixed(0)}`, dx + 8, 18);
    }
    const stage = document.getElementById('stage');
    stage.style.width = out.width + 'px';
    stage.style.aspectRatio = `${out.width}/${out.height}`;
    stage.innerHTML = '';
    out.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    stage.appendChild(out);
    return;
  }

  /* ?fxstrip=N 出一条特效胶片：打一下，然后每 MS 毫秒抓一格。
     特效是瞬时的，单张截图什么也验证不了 —— 只有把同一次命中的前后若干
     毫秒并排摆着，才看得出顿帧有没有生效、冲击波是不是沿线传出去了、
     粒子的衰减节奏对不对。 */
  if (Q.has('fxstrip')) {
    const n = clamp(+Q.get('fxstrip') | 0, 2, 12);
    const MS = clamp(+(Q.get('fxms') || 60), 16, 400) / 1000;
    const sc = 0.5, power = clamp(+(Q.get('fxpower') || 3), 1, 3);
    const rcp = RECIPE[Q.get('fxrecipe')] || RECIPE.thud;
    S.auto = false; S.t = 3.0;
    for (let k = 0; k < 150; k++) derive(1 / 60);

    const out = document.createElement('canvas');
    out.width = n * W * sc; out.height = H * sc;
    const o = out.getContext('2d');
    o.fillStyle = '#0c0e12'; o.fillRect(0, 0, out.width, out.height);

    impact(-1, FX.phoneY, power, rcp);
    let el = 0;
    for (let i = 0; i < n; i++) {
      /* 第一格只推进一帧。命中那一瞬间粒子都还没展开，拿一整格去拍它等于
         白扔八分之一的胶片宽度。 */
      const step = i === 0 ? 1 / 60 : MS;
      for (let k = 0; k < Math.max(1, Math.round(step * 60)); k++) {
        const d = Particles.tick(1 / 60);   // 与主循环同构：粒子走真实时间，逻辑走 d
        Particles.update(1 / 60);
        derive(d); hudTick(d);
      }
      el += step;
      render();
      const dx = i * W * sc;
      for (const c of [cvBg, cvCh, cvFx]) o.drawImage(c, dx, 0, W * sc, H * sc);
      o.fillStyle = 'rgba(0,0,0,.66)'; o.fillRect(dx, 0, 132, 26);
      o.fillStyle = '#fff'; o.font = '600 15px system-ui';
      o.fillText(`+${Math.round(el * 1000)}ms 粒子${Particles.count()}`, dx + 8, 18);
      if (i === 0) {
        o.fillStyle = 'rgba(0,0,0,.66)'; o.fillRect(dx, 26, 132, 24);
        o.fillStyle = '#ffd36b';
        o.fillText(`${Q.get('fxrecipe') || 'thud'} p${power} line${S.line}`, dx + 8, 42);
      }
    }
    const stage = document.getElementById('stage');
    stage.style.width = out.width + 'px';
    stage.style.aspectRatio = `${out.width}/${out.height}`;
    stage.innerHTML = '';
    out.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    stage.appendChild(out);
    return;
  }

  /* ?bench=1 —— 连点压测。"卡不卡"是主观的，而它在静止截图里完全不存在：
     要么拿到每一帧的真实耗时，要么就是在猜。这个模式关掉自动演示、用固定
     dt 推进（弹幕节奏每次跑都一样，两次测量才可比），按 benchrate 的间隔
     轮流发六件礼物，逐层计时，最后把读数画在画布上 —— 读数得跟着截图一起
     出来，否则在无头环境里取不回来。

     ?benchoff=ammo|part|both 用差值法定位热点：把某一层的绘制换成空函数再
     跑一遍，两次的差就是那一层的代价。比在渲染代码里埋计时点干净 ——
     生产代码一行都不用改。 */
  if (Q.has('bench')) {
    const N = clamp(+(Q.get('benchframes') || 420), 60, 2000);
    const RATE = clamp(+(Q.get('benchrate') || 110), 40, 2000) / 1000;
    const bOff = Q.get('benchoff') || '';
    if (bOff === 'ammo' || bOff === 'both') Ammo.draw = () => {};
    if (bOff === 'part' || bOff === 'both') Particles.draw = () => {};

    /* 压测必须走真实链路：礼物注入火力 → 火力自动派弹幕 → 一部分在中线对撞。
       直接 Ammo.launch 测出来的是旧模型的密度，而新模型场上还多着常规火力那
       一路，负载完全是另一回事。 */
    /* 礼物组合要贴近真实分布：小额是绝大多数，神秘空投八件里才有一件。
       四种等概率轮流的话，每 1.2 秒就来一次处决，那不是压测是造假 —— 独占窗口
       会一直开着，常规火力全被挡掉，量出来的负载比真实情况低一个数量级。 */
    const gnames = ['wand', 'wand', 'mirror', 'wand', 'boom', 'wand', 'mirror', 'drop'];
    const T = { logic: 0, bg: 0, ch: 0, fx: 0, all: 0 };
    const each = new Float64Array(N);
    const M = { logic: 0, bg: 0, ch: 0, fx: 0, all: 0, at: 0 };
    let bi = 0, bacc = 0, gi = 0, maxP = 0, maxA = 0, sumP = 0, sumA = 0, drops = 0, froze = 0;
    S.t = 3.0;
    document.getElementById('auto').checked = false;
    startMatch();
    for (let k = 0; k < 150; k++) derive(1 / 60);

    const benchStep = () => {
      const dt = 1 / 60;
      const t0 = performance.now();
      bacc += dt;
      if (bacc >= RATE) { bacc -= RATE; giveGift(gi % 2 ? +1 : -1, gnames[gi++ % gnames.length]); }
      battle(dt);
      const d = Particles.tick(dt);
      /* 冻结帧占比 —— 帧率正常但画面不动，观众读到的同样是"卡"。每次命中
         都冻 35~110ms，而连点时命中是密集的，顿帧会一段一段接上。这个数
         在耗时曲线上完全看不出来：那些帧的渲染一切正常，只是世界没动。 */
      if (d === 0) froze++;
      Particles.update(dt);
      Ammo.update(d);
      Bubble.update(d, FX.struggle);
      S.t += d;
      derive(d); hudTick(d);
      const t1 = performance.now(); renderBg();
      const t2 = performance.now(); renderActors();
      const t3 = performance.now(); renderFx();
      const t4 = performance.now();
      T.logic += t1 - t0; T.bg += t2 - t1; T.ch += t3 - t2; T.fx += t4 - t3; T.all += t4 - t0;
      each[bi] = t4 - t0;
      /* 均值说明不了卡顿 —— 均值 3ms 的同时可以有一帧 39ms，而观众看到的
         就是那一帧。所以每层都要留峰值，否则只知道"有尖峰"，不知道尖峰在
         哪一层；再记下它出现在第几帧，用来分辨"开头一次性的预热"和"运行中
         周期性发作"。 */
      if (t1 - t0 > M.logic) M.logic = t1 - t0;
      if (t2 - t1 > M.bg) M.bg = t2 - t1;
      if (t3 - t2 > M.ch) M.ch = t3 - t2;
      if (t4 - t3 > M.fx) M.fx = t4 - t3;
      if (t4 - t0 > M.all) { M.all = t4 - t0; M.at = bi; }
      if (t4 - t0 > 16.7) drops++;
      const np = Particles.count(), na = Ammo.count();
      sumP += np; sumA += na;
      if (np > maxP) maxP = np;
      if (na > maxA) maxA = na;
      if (++bi < N) { requestAnimationFrame(benchStep); return; }

      const sorted = Array.from(each).sort((a, b) => a - b);
      const p95 = sorted[Math.floor(N * 0.95)], worst = sorted[N - 1];
      const rows = [
        `连点压测  ${N} 帧 · 每 ${Math.round(RATE * 1000)}ms 一件礼物` + (bOff ? `  [关掉 ${bOff}]` : ''),
        ``,
        `           均值      峰值`,
        `每帧总计   ${(T.all / N).toFixed(2)}      ${M.all.toFixed(1)} ms  (第 ${M.at} 帧)`,
        `  逻辑     ${(T.logic / N).toFixed(2)}      ${M.logic.toFixed(1)}`,
        `  底版层   ${(T.bg / N).toFixed(2)}      ${M.bg.toFixed(1)}`,
        `  角色层   ${(T.ch / N).toFixed(2)}      ${M.ch.toFixed(1)}`,
        `  特效层   ${(T.fx / N).toFixed(2)}      ${M.fx.toFixed(1)}`,
        ``,
        `p95 ${p95.toFixed(2)}ms   掉帧(>16.7ms) ${drops}/${N} = ${(drops * 100 / N).toFixed(1)}%`,
        `世界被顿帧冻住 ${froze}/${N} 帧 = ${(froze * 100 / N).toFixed(1)}%`,
        `粒子 均 ${(sumP / N).toFixed(0)} 峰 ${maxP}     弹幕 均 ${(sumA / N).toFixed(1)} 峰 ${maxA}`,
        `16.7ms = 60fps    33.3ms = 30fps`,
      ];
      fctx.fillStyle = 'rgba(6,8,12,.93)';
      fctx.fillRect(24, 150, W - 48, 46 + rows.length * 42);
      fctx.strokeStyle = '#ffd36b'; fctx.lineWidth = 3;
      fctx.strokeRect(24, 150, W - 48, 46 + rows.length * 42);
      fctx.textAlign = 'left'; fctx.textBaseline = 'middle';
      rows.forEach((r, k) => {
        fctx.font = (k === 0 ? 'bold 30px ' : '600 30px ') + 'ui-monospace,Menlo,monospace';
        fctx.fillStyle = k === 0 ? '#ffd36b' : (k === 2 ? '#8fe3ff' : '#e8ecf2');
        fctx.fillText(r, 48, 196 + k * 42);
      });
      document.getElementById('stat').textContent = rows.join(' | ');
      // 无头环境里没法按时间猜跑完没跑完，用标题当完成信号，外面轮询它
      document.title = 'BENCHDONE';
    };
    requestAnimationFrame(benchStep);
    return;
  }

  let last = performance.now(), fps = 0, fr = 0, acc = 0, dir = 1;
  function frame(now) {
    if (stopAll) { render(); requestAnimationFrame(frame); return; }
    const raw = Math.min(.05, (now - last) / 1000); last = now;
    fr++; acc += raw;
    if (acc >= .5) { fps = fr / acc; fr = 0; acc = 0; }
    /* 顿帧冻住的是游戏逻辑（角色姿态、对抗线、进度），特效照真实时间走。
       两者用的是不同的时钟：定格是为了让观众多看两眼"他被打中了"，而火花
       和闪光正是这一下的可视化 —— 把它们一起冻住，爆炸就会迟到一百毫秒，
       读起来是"闪了一下、卡住、然后才炸开"。 */
    const dt = Particles.tick(raw);
    Particles.update(raw);
    /* 弹幕走 dt，跟游戏逻辑一起冻。这和粒子走真实时间并不矛盾：爆炸是"刚刚
       这一下"的可视化，冻住它就迟到了；而正在飞的弹幕是**下一下**的前奏，
       顿帧的意思就是全世界停下来看这一击，此刻别的东西还在飞就散掉了。 */
    Ammo.update(dt);
    // 气泡跟着逻辑时钟：顿帧时它也该停，那半秒全世界都在看刚才那一击
    Bubble.update(dt, FX.struggle);
    S.t += dt;

    /* 对局跑数值，调试台跑演示。两者互斥：idle 下 battle 不动，进度由滑块或
       自动演示给；play 下滑块失效，进度只能由火力差推出来。混在一起的话
       "礼物到底推了多少"永远说不清。 */
    // 同理：结算画面上的数是这一局的战果，不该在结算期间还往上跳
    if (live && S.phase !== 'over') { S.fA += liveA * raw; S.fB += liveB * raw; }
    /* liveFreeze 冻的是**战况**：对抗线、血量、比赛阶段与三个计时器都定在预热
       那一刻，而拉力、弹幕、粒子照跑 —— 截图要的是"打到这个比分时画面是活的
       什么样"，不是死图。
       阶段和计时器必须一起冻：只冻血量的话，绝杀的累计照走（lead 被冻在一个
       大值上，等于每一帧都在给它加码），截一张残血图能等出个"查岗党胜"来。 */
    const k = { p: S.p, hpA: S.hpA, hpB: S.hpB, clock: S.clock, phase: S.phase,
                big: S.big, sudden: S.sudden, stand: S.stand, winner: S.winner };
    battle(dt);
    if (freeze) Object.assign(S, k);
    if (S.auto && S.phase === 'idle') {
      S.p += dir * dt * 9 * (0.35 + Math.abs(Math.sin(S.t * .27)) * 1.5);
      if (S.p > 97) { S.p = 97; dir = -1; } if (S.p < 3) { S.p = 3; dir = 1; }
    }
    if (S.phase !== 'idle') document.getElementById('pv').value = S.p;
    else if (S.auto) document.getElementById('pv').value = S.p;
    derive(dt); hudTick(dt);
    /* 结算停够了就自动开下一局 —— 直播是连着开的，没人会在结算画面上手点。
       这一句必须待在主循环里，不能塞进 derive：?live 的预热是靠反复调
       derive 快进的，开新局这种流程副作用混进去，预热跑到结算就会自己把
       这一局重置掉（截图全白忙一场）。derive 只负责由 S 派生画面量。
       钉住时刻时不自动开局，否则截图会被下一局冲掉。 */
    if (S.phase === 'over' && Result.pin < 0 && S.overT >= Result.NEXT) startMatch();
    render();
    const mm = Math.max(0, S.clock);
    document.getElementById('stat').textContent =
      (S.phase === 'idle'
        ? `p=${S.p.toFixed(1)}  对抗线x=${phonePos()[0].toFixed(0)}  f${String(seq.shown).padStart(3, '0')}  `
        : `血 ${S.hpA.toFixed(1)}:${S.hpB.toFixed(1)}  拉力 ${S.fA.toFixed(0)}:${S.fB.toFixed(0)}  `
          + `差${(S.fA - S.fB).toFixed(0)}  p=${S.p.toFixed(1)}  `
          + `${(mm / 60 | 0)}:${String(mm % 60 | 0).padStart(2, '0')}`
          + (S.phase === 'sudden' ? `  绝杀${S.sudden.toFixed(0)}` : '')
          + (S.stand > 0 ? `  反击${S.stand.toFixed(0)}` : '')
          + (S.phase === 'over' ? `  ${S.winner > 0 ? '查岗党胜' : S.winner < 0 ? '灭迹党胜' : '平局'}` : '') + '  ')
      + `粒子${Particles.count()}  ${fps.toFixed(0)}fps`;
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  const pv = document.getElementById('pv');
  pv.oninput = () => { if (S.phase !== 'idle') return; S.p = +pv.value; S.auto = false; document.getElementById('auto').checked = false; };
  document.getElementById('auto').onchange = e => S.auto = e.target.checked;
  const nudge = d => { if (S.phase !== 'idle') return;
                       S.auto = false; document.getElementById('auto').checked = false;
                       S.p = clamp(S.p + d, 0, 100); pv.value = S.p; };
  /* 按钮既推进度也打一下：进度是玩法，命中是演出，观众看到的是同一件事。
     side 取推力的反方向 —— 查岗党加分等于灭迹党挨了一下。 */
  const power = () => +document.getElementById('pw').value;
  const hit = (d, rcp) => {
    nudge(d);
    impact(d > 0 ? -1 : +1, FX.phoneY, power(), rcp);
  };
  document.getElementById('hitL').onclick = () => hit(+7, RECIPE.thud);
  document.getElementById('hitR').onclick = () => hit(-7, RECIPE.thud);
  // 三个配方都由查岗党打出去，落在灭迹党身上；力度由上面那个下拉决定
  /* 礼物按钮只负责发射，进度和特效都等弹幕真的撞上对抗线才结算 —— 玩法和
     演出走的是同一个事件，观众看到的因果关系才对得上。 */
  /* 礼物按钮注入火力，而不是直接发弹幕。发不发、发几颗由火力的消耗量决定
     （见 emitFire）—— 于是"刷得越多扔得越密"是从数值里长出来的，不是写死的。 */
  /* 按钮上写的是**飞出来的那件东西**，不是平台礼物名。九件平台礼物两边共用，
     左右两排按钮于是长得一模一样（仙女棒、魔法镜……），可点下去左边飞发卡、
     右边飞瓜子 —— 看着同一个名字，对不上号。标签由 ITEM_OF + GIFT.name 现算，
     以后改映射表按钮自动跟着变，不会出现按钮写着一件、飞出来另一件。
     平台礼物名和注入量退到 title，要查数值时悬停即可。 */
  for (const b of document.querySelectorAll('[data-shop]')) {
    const it = SHOP[b.dataset.shop];
    const key = ITEM_OF[+b.dataset.side > 0 ? 'L' : 'R'][it.tier];
    b.textContent = (key ? GIFT[key].name : it.name) + ' ' + '⓪①②③④'[it.tier];
    b.title = `平台礼物 ${it.name}　档 ${it.tier}　注入 ${it.push}`;
    b.onclick = () => {
      if (S.phase === 'idle') startMatch();
      giveGift(+b.dataset.side, b.dataset.shop);
    };
  }
  document.getElementById('start').onclick = () => {
    if (S.phase === 'idle') { startMatch(); document.getElementById('start').textContent = '回到调试台'; }
    else { S.phase = 'idle'; S.fA = S.fB = 0; S.clock = NUM.MATCH; Ammo.clear(); document.getElementById('start').textContent = '开始对局'; }
  };
  const lv = document.getElementById('lv');
  lv.value = S.line;
  lv.onchange = () => S.line = +lv.value;
})();
