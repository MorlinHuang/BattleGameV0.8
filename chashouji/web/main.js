/* 《查手机》网页版 —— 单一真源驱动。
 *
 * 三层，别混：
 *   拉力 S.fA / S.fB  礼物注入的存量，双方互相对冲，慢慢自然流失
 *   位置 S.pos（米）  **胜负只看它**：拉力差每秒把两个人往拉力大的那边拖，
 *                    正 = 往左拖进女生卧室（查岗党占优），负 = 往右拖进电竞房。
 *                    拖到 ±NUM.END 那一头就分出胜负（2026-09-24 起；此前是血量制）
 *   姿态 S.p（0~100）  拉力差的**当前读数**，决定两个人此刻摆哪套动作 —— 它不是
 *                    积分量，对面追上来就换回僵持，这才是拔河
 *
 * 位置管"已经被拖了多远"（背景卷到哪、距离条），姿态管"此刻谁在使劲"
 * （僵持 / 拽着走 / 拖在地上）。两个都从同一个拉力差来，所以画面和读数
 * 在构造上对得上：拽着走的时候背景一定在卷，背景停了姿态一定回僵持。
 */
const W = 960, H = 1334;
const MID = 480;
/* 地面线：两个人的脚底落在这一行。背景三间房的墙根在 y≈720，地板往下铺到底，
   1195 让人站在地板中段偏下 —— 再往下脚就贴底边了，往上头会顶进 HUD。 */
const GROUND = 1195;
const GREEN = [126, 217, 87], RED = [255, 72, 72];

const P = {
  /* 米 → 世界像素。三间房拼起来 6700px 宽，客厅正中是 0 米。取 82 让 ±30 米
     （NUM.END）正好停在两头房间的深处、镜头还不露边：左端 3396-2460=936，
     右端 5856，镜头半宽 480，两头都还有余量。卧室门在 +13 米、电竞房门在 −14 米
     （距离条上的房间分段按 world.json 现算，不用这两个数）。 */
  pxPerM: 82,

  /* 姿态怎么选：两把尺取更狼狈的那个 ——
       拉力：S.p 的偏离量 |bias|（0 = 势均力敌，1 = 拉力差顶满）—— 一件大礼物能瞬间把人拽倒；
       距离：|S.pos| / END（0 = 客厅正中，1 = 到头）—— 被拖得越远倒得越低。
     只看拉力的话，礼物刷得匀时拉力差几乎不变，一整局停在同一档：实测 2:1 对刷
     94 秒全是僵持，人站着被平移 30 米。距离这把尺保证每局四档都看得到。
     例外：被拖远的那方正在往回拽（拉力反号且够跪那档）时只看拉力 —— 他在反攻，
     不能还趴着。
     带回差（hys）：刚好压在门槛上时，拉锯的一点点抖动会让动作一秒换好几次，
     读出来是抽搐。进门槛要超过 +hys，退出来要低于 -hys。 */
  /* 落后方被拉倒分三档，一档比一档低：跪着 → 往前扑倒 → 趴在地上被拖。
     领先方全程站着、面朝对方倒退着拽（任何一档都不转身）。
     四档**平分**（用户定）：两把尺都按 1/4、2/4、3/4 切 —— 拉力差 250/500/750，
     距离 7.5/15/22.5 米。 */
  kneelAt: 0.25,   // 超过它：落后方被拽得跪下
  fallAt: 0.50,    // 超过它：落后方往前扑倒（一条腿跪着、一条腿往后滑）
  lieAt: 0.75,     // 超过它：落后方趴在地上被拖
  hys: 0.05,
  /* 一次只走一档，每档至少停这么久。一件戒指盒能让拉力差 1 秒内从 0 冲到
     趴下那档，不拦的话跪和扑倒各一闪而过；人摔倒本来也是先跪、再扑、再趴。 */
  stageHold: 0.6,
  /* 步态：八格一个循环（两步），按**位移**推进、不按时间 —— 背景不动脚就不动，被拽回来
     就倒着播。一个循环对应背景卷过多少像素，由 build.py 按每档原图里两脚的间距量出来
     （world.json 的 gaits[档].cycle，约 400~650）：这样站地的那只脚在画面上往前挪的速度
     正好等于地板卷过去的速度，脚像钉在地上。
     gaitSlip 是在这个基础上的倍率：1 = 脚不打滑；调大 = 步子更碎更快，但脚会在地上往后蹭。
     以前固定 100（四格版），步频是地板的五倍多，看着像在冰上倒腾。 */
  gaitSlip: 1,
  /* 僵持循环的播放速度（格/秒）。手绘动画"一拍二"是 12 格/秒，这里只有 5 张
     来回用，8 格/秒一个来回正好一秒 —— 再快就成了抖，不是拉锯。 */
  loopFps: 8,
  /* 被拉倒的三档各只有一张图（循环帧还没画），靠上下颠一下假装领先方在走。
     这是占位：等循环帧画出来就删掉。bobHz 是每秒几步，bobPx 是颠多高
     （落后方贴着地，只有领先方在迈步，所以颠得比站着走小）。 */
  bobHz: 2.6, bobPx: 4,

  /* 挨一下之后的反应：角色被推开又弹回。人是硬的，推得动、马上站回来。 */
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
  /* BURN / LOSS / V_Z 是**同一根时间轴**上的刻度，改一个必须三个一起按同样
     倍数改，否则动的就不只是快慢，还有谁赢谁输：稳态拉力差 = Δ注入 / LOSS，
     三个同乘 k 之后差值 ÷k 而每点差的拖动速度 ×k，正好抵消。
     曾经是 0.05 / 0.012，火力的时间常数 83 秒 —— 观众刷一件「爱的爆炸③」
     出去，血条 20 秒纹丝不动，60 秒才跳 1 滴（这条是截图量出来的）。礼物的
     效果全在，只是摊得太薄，在直播间里等同于没发生。现在时间常数 25 秒。 */
  BURN: 0.165,     // 对冲系数：双方等量消耗，由火力少的一方定速
  LOSS: 0.040,     // 自然流失：势头会过去。时间常数 25 秒
  /* 稳态时  拉力差 = 注入速度差 / LOSS  —— 对冲项在两边完全相同，推导时直接
     消掉了。所以被拖的快慢只取决于"两边刷礼物的速度差"，与刷了多少总量
     无关：都在猛刷就差值小、画面激烈而谁也拖不动谁；一方停手就立刻被拖走。 */

  /* ── 拉力差 → 拖动速度（X / M / V_Z）──
     公式：拉力差 > X 时，每 M 点拉力差，每秒把两个人往拉力大的一方拖 V_Z 米。
     X 和 M 取自《螂人杀》文档（3000 兵 ÷100、兵数 ÷100 的刻度）。
     V_Z 是从血量制原样换算过来的，局的节奏一点没变：原来差 1000 每秒扣 5%
     的血，现在差 1000 每秒拖 END 的 5%（30 米 × 5% = 1.5 米）。 */
  PULL_X: 30,      // 死区：拉力差没到这个数，谁也拖不动谁（≈1.5 个魔法镜②）
  PULL_M: 1000,    // 每这么多拉力差……
  V_Z: 1.5,        // ……每秒拖这么多米
  /* 拖动速度的上限。拉力差是没有上限的 —— 大哥一秒注入 600 而对面只有 80 时，
     差值能到四万，折合每秒拖 60 米，一眨眼就到头了。那不叫碾压，那叫没有
     过程。3 米/秒 = END 的 10%：再怎么碾压，从中间拖到头也要 10 秒。 */
  V_MAX: 3,
  /* 拖到哪算赢：离客厅正中 END 米。30 米正好在两头房间的深处（见 P.pxPerM）。
     改它不用动背景：镜头按米数算，房间只是铺在那儿的地皮。 */
  END: 30,
  /* 姿态的满幅刻度：拉力差到这么多，姿态读数 p 就顶到 0 或 100。
     取 1000 是让它和上面的 M 共用一把尺。试过 2000（= 拖动速度封顶时的差）：
     标杆的一方猛刷 23:0 拉力差只有 516，整局停在僵持 —— 太钝。 */
  LINE_FULL: 1000,
  LINE_RATE: 2.2,  // 姿态读数趋近拉力差的速率（时间常数 0.45 秒）

  SHOT: 9,         // 每消耗这么多火力打出一发弹幕 —— 弹幕就是火力的消耗形式
  MATCH: 720,      // 单局 12 分钟
  SUDDEN_LEAD: 0.35, // 被拖出去 END 的这么多（35% = 10.5 米），持续 SUDDEN_WAIT 秒就进绝杀
  SUDDEN_WAIT: 60,
  SUDDEN: 30,      // 绝杀倒计时
  STAND_AT: 0.08,  // 离终点只剩 END 的这么多（8% = 2.4 米）时触发反击时刻
  STAND: 120,      // 反击时刻时长：劣势方注入翻倍，全局只触发一次
  SHIELD_AT: 0.10, // 抓门框：离终点不到 END 的这么多（3 米）时，火力按比例替他顶住
  SHIELD_MAX: 0.75,// 抓门框的减速上限：再能扛也不能扛到拖不动
};

const S = {
  /* auto 默认**关**：展示时自动演示会自己来回拽，观众分不清哪一下是
     刷礼物推的、哪一下是演示程序推的。要看动作切换时用 ?auto=1 打开。 */
  p: 50, t: 0, auto: false,
  fA: 0, fB: 0,                       // 拉力（火力）：A=查岗党(左) B=灭迹党(右)
  pos: 0,                             // 位置（米）：胜负只看它。正 = 被拖向左边（查岗党占优）
  vel: 0,                             // 此刻每秒被拖多少米（带符号，battle 算出来的读数，HUD 画它）
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
/* 表现层状态：全部由 derive(dt) 从 S 算出来，绘制只读不写。 */
const FX = {
  pose: 'n',                         // 当前动作：n 僵持 / aK aF aL 查岗党占优、男方跪·扑倒·趴 / bK bF bL 反之
  poseT: 0,                          // 进入这个动作多久了（循环帧与颠步读它）
  frame: 'n0',                       // 这一帧用哪张贴图（world.json 里的名字）
  camX: 0,                           // 镜头中心在世界里的横坐标（像素）
  pairX: MID,                        // 两个人的锚点在屏幕上的横坐标
  bob: 0,                            // 颠步的上下位移
  phoneX: MID, phoneY: 750,          // 手机在屏幕上的位置 —— 弹幕打它、气泡从它冒
  struggle: 1,                       // 僵持度 0~1，气泡的冒出节奏读它
  gaitPh: 0,                         // 步态相位（循环数，带小数），只随位移变

  hitX: 0, hitV: 0,                  // 角色被推开的位移与速度
  punch: 0,                          // 缩放脉冲
  tint: [255, 255, 255], tintA: 0,   // 命中染色
};

const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a})`;
// 帧率无关的指数趋近：min(1,dt*k) 会让节奏随帧率漂移
const approach = (dt, k) => 1 - Math.exp(-k * dt);

/* ---------- 数值层：算出 S.pos 与 S.p ---------- */

/* battle 算"两个人该往哪走"，derive 算"算出来之后画面长什么样"。分成两个函数
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

  /* ── 胜负层：位置 ──
     拉力差（= 双方火力之差）一件事管两头：**当下**它决定两个人摆哪套动作，
     **持续**它每秒把两个人往拉力大的那边拖。拖到 ±END 米就分出胜负。

     这是拔河本来的样子：位置是**积分量**，谁拽得久谁就走得远；而且可以
     拽回来 —— 对面追上来，拉力差反号，两个人就往回走，背景倒着卷。
     跟上一版血量制比，"被压着打"变成了"被拖着走"，观众不用去读两条血条的
     长短，看背景里是谁的房间就知道谁占上风。

     三个数的出处（X / M / V_Z，见 NUM 表）：
       M = 1000 拉力：本项目的 push = 螂人杀兵数 ÷ 100，1000 拉力就是 10 万兵。
       X = 30 拉力：螂人杀"最后 100 滴血，兵力大于 3000 才优先掉兵"里的
           3000 兵 ÷ 100，拿来当死区 —— 双方拉力咬在一起的时候谁也拖不动谁。
       V_Z = 1.5 米/秒：从血量制的 Z = 5%/秒 原样换算（END 的 5%）。
           ⚠️ 5% 取自需求里给过的例子，螂人杀公开文档里**没有**这个速率。
           按它算，一方猛刷而对面不还手约 70 秒分胜负；想拉长就调小 V_Z 和
           V_MAX（同一个倍数），见 ?vz= 。 */
  const diff = S.fA - S.fB;

  /* 姿态读数：拉力差的当前值，**不积分**。趋近而不是直接取值 —— 礼物注入
     是瞬间跳变的，直接赋值会让动作一帧之内从僵持跳到拖地。 */
  const want = 50 + 50 * clamp(diff / NUM.LINE_FULL, -1, 1);
  S.p += (want - S.p) * approach(dt, NUM.LINE_RATE);

  /* 拖动。差距过不了 X 就谁也拖不动 —— 这是僵持区：双方咬得紧的时候画面照样
     激烈（弹幕全在中间对撞），但背景一动不动。
     速度按**差的全量**算，不是"超出 X 的那部分"：X 是开关不是起征点。 */
  const gap = Math.abs(diff);
  S.vel = 0;
  if (gap > NUM.PULL_X) {
    let v = Math.min(NUM.V_MAX, gap / NUM.PULL_M * NUM.V_Z);
    const dir = diff > 0 ? +1 : -1;                      // 往哪边拖：+1 = 往左（查岗党那头）

    /* 抓门框：快被拖到头时，火力越足越顶得住。这是螂人杀"最后 100 滴血，
       兵力大于 3000 就优先掉兵"的原意 —— 刷礼物能直接保命，而且看得见。
       ⚠️ 它**不能去扣火力存量**：火力同时是对冲的输入，扣掉劣势方的火力 →
       对冲变弱 → 优势方的火力不再被烧 → 差值越拉越大，越接近终点崩得越快
       （血量制时实测净差冲到理论值的 2.4 倍）。所以只按**比例**减速。 */
    const left = NUM.END - S.pos * dir;                  // 被拖的那一方离终点还剩几米
    if (left < NUM.END * NUM.SHIELD_AT) {
      const mine = dir > 0 ? S.fB : S.fA, his = dir > 0 ? S.fA : S.fB;
      v *= 1 - Math.min(NUM.SHIELD_MAX, mine / (his + 1) * 1.5);
    }
    S.vel = v * dir;
    S.pos = clamp(S.pos + S.vel * dt, -NUM.END, NUM.END);
  }

  if (Math.abs(S.pos) >= NUM.END) { finish(S.pos > 0 ? +1 : -1); return; }

  /* 反击时刻：第一次有人被拖到离终点只剩 8% 时，劣势方注入翻倍两分钟，全局只
     触发一次。放大的是注入不是速度 —— 在两层模型里，"更有力"只能是更多火力。 */
  if (!S.standUsed && Math.abs(S.pos) > NUM.END * (1 - NUM.STAND_AT)) {
    S.standUsed = true; S.stand = NUM.STAND;
  }

  /* 绝杀：被拖出去这么远还一直拽不回来，就别耗了，给 30 秒最后的机会。
     判据是位置而不是姿态 —— 姿态是瞬时读数，一件大礼物就能把人拽倒一下。 */
  const lead = Math.abs(S.pos) / NUM.END;
  if (S.phase === 'play') {
    S.big = lead >= NUM.SUDDEN_LEAD ? S.big + dt : 0;
    if (S.big >= NUM.SUDDEN_WAIT) { S.phase = 'sudden'; S.sudden = NUM.SUDDEN; }
  } else if ((S.sudden -= dt) <= 0) { finish(S.pos > 0 ? +1 : -1); return; }

  // 时间到：被拖向谁那边谁赢，离正中不到 1 米判平
  if ((S.clock -= dt) <= 0) finish(S.pos > 1 ? +1 : S.pos < -1 ? -1 : 0);
}

/* 调试台（idle）不跑数值：姿态由滑块或自动演示直接给 S.p。位置照同一把尺子
   从 S.p 积分出来 —— 不然拖滑块只换动作、背景不动，看不出卷轴对不对。 */
function drift(dt) {
  const bias = (S.p - 50) / 50, gap = Math.abs(bias) * NUM.LINE_FULL;
  // 跟 battle() 同一个公式：差值 → 速度，封顶 V_MAX
  S.vel = gap > NUM.PULL_X ? Math.sign(bias) * Math.min(NUM.V_MAX, gap / NUM.PULL_M * NUM.V_Z) : 0;
  S.pos = clamp(S.pos + S.vel * dt, -NUM.END, NUM.END);
}

function finish(who) { S.phase = 'over'; S.winner = who; S.vel = 0; S.overT = 0; }

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
  const loser = S.pos > 0 ? -1 : +1;                // 谁正落后（看位置，不看此刻的姿态）
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
  S.pos = 0; S.vel = 0;
  S.debA = S.debB = S.debKA = S.debKB = 0;
  S.clock = NUM.MATCH; S.phase = 'play';
  S.big = S.sudden = S.stand = 0; S.standUsed = false; S.winner = 0;
  S.overT = 0; S.giftA = S.giftB = 0; S.board = [];
  S.auto = false;
  Ammo.clear(); Particles.clear();
}

/* ---------- 表现层：由 S 派生画面 ---------- */

/* 世界与贴图的元数据，boot 时从 assets/world/world.json 读进来（v14/build.py 生成）：
   rooms 三间房各多宽、center 客厅正中（= 0 米）在世界里的横坐标、
   poses 每张贴图的尺寸、锚点（外框中点或脚的质心 × 脚底线）、手机位置。 */
let WORLD = null;

/* 僵持循环：5 张来回放成 8 格 —— 手机从正中往左拽过去、回来、往右、回来。
   这是拔河里"谁也没占上风"的样子：一直在使劲、一直在来回，但哪头也没赢。 */
const LOOP_N = ['n0', 'nL1', 'nL2', 'nL1', 'n0', 'nR1', 'nR2', 'nR1'];

/* 由 |bias|（derive 里两把尺取大之后的值）选动作，带回差。返回 n，或 a/b + K(跪) F(扑倒) L(趴)。
   held = 当前这档已经停够 P.stageHold：没停够就不换；停够了也只往目标走一档。
   局势翻转（原来男方倒、现在女方占优）时，先一档档站回僵持，再往另一边倒。 */
const STAGES = 'KFL';
function pickPose(prev, bias, held) {
  const k = Math.abs(bias), side = bias > 0 ? 'a' : 'b';
  const lvl = prev === 'n' ? 0 : STAGES.indexOf(prev[1]) + 1;
  const same = prev === 'n' || prev[0] === side;
  const at = [P.kneelAt, P.fallAt, P.lieAt];
  let want = 0;
  // 回差只对"留在原档"起作用：已经趴下的，要掉到 lieAt-hys 以下才撑起来
  if (same) for (let l = 3; l >= 1; l--) {
    if (k > (lvl >= l ? at[l - 1] - P.hys : at[l - 1] + P.hys)) { want = l; break; }
  }
  if (want === lvl || !held) return prev;
  const next = lvl + Math.sign(want - lvl);
  return next === 0 ? 'n' : (lvl === 0 ? side : prev[0]) + STAGES[next - 1];
}

function derive(dt) {
  if (S.phase === 'over') {
    S.overT += dt;
    /* ?overt=<秒> 把结算钉在指定时刻。判词砸下来只有半秒、气泡和面板各自也
       就零点几秒，不钉住根本截不到入场的样子 —— 和 ?hudflash 同一个道理。 */
    if (Result.pin >= 0) S.overT = Result.pin;
  }

  // p 大 = 查岗党(女方,在左)占优 = 两个人被往左拽
  const bias = (S.p - 50) / 50;
  const dist = S.pos / NUM.END;
  const back = Math.sign(bias) !== Math.sign(dist) && Math.abs(bias) >= P.kneelAt;
  const sev = back || Math.abs(bias) >= Math.abs(dist) ? bias : dist;
  const pose = pickPose(FX.pose, sev, FX.poseT >= P.stageHold);
  if (pose !== FX.pose) { FX.pose = pose; FX.poseT = 0; } else FX.poseT += dt;

  /* 这一帧用哪张图。僵持走时间循环；被拉倒的各档有步态帧的（world.json 的 gaits）
     走步态循环；还没画步态的先靠颠步（bob）假装在走。 */
  const gait = WORLD && WORLD.gaits && WORLD.gaits[FX.pose];
  if (FX.pose === 'n') {
    FX.frame = LOOP_N[Math.floor(FX.poseT * P.loopFps) % LOOP_N.length];
    FX.bob = 0;
  } else if (gait) {
    // 往赢的那一方拖 = 正着走（倒退）；被拽回来 = 倒着播（往前走）
    const toward = FX.pose[0] === 'a' ? 1 : -1;
    FX.gaitPh += S.vel * toward * dt * P.pxPerM * P.gaitSlip / gait.cycle;
    const n = gait.frames.length;
    FX.frame = gait.frames[((Math.floor(FX.gaitPh * n) % n) + n) % n];
    FX.bob = 0;
  } else {
    FX.frame = FX.pose;
    /* 一步一颠，取 |sin| 是因为人只会往上颠、不会陷进地板。
       速度为 0（抓门框顶住了、或调试台里 p 刚过门槛）时不颠 —— 背景没在卷，
       人还在原地踏步就是滑冰。 */
    const moving = Math.min(1, Math.abs(S.vel) / 0.5);
    const amp = P.bobPx * moving;
    FX.bob = -Math.abs(Math.sin(FX.poseT * Math.PI * P.bobHz)) * amp;
  }

  /* 镜头：两个人在世界里的位置 = 客厅正中 − 米数 × 每米像素（往左拖是正）。
     镜头跟着他们走，但不出世界的边 —— 走到头时镜头停住、人往画面边上走，
     这正是"拖到墙根了"的样子。 */
  if (WORLD) {
    const wx = WORLD.center - S.pos * P.pxPerM;
    FX.camX = clamp(wx, MID, WORLD.total - MID);
    FX.pairX = MID + (wx - FX.camX);
  }
  FX.struggle = 1 - Math.abs(bias) * 0.78;          // 僵持度：五五开时最高

  /* 角色被推开又站回来：弹簧-阻尼，不是单纯衰减 —— 单纯衰减只有"飘回去"，
     看不出"被推动了"。挨一下给的是速度不是位移。 */
  FX.hitV += -FX.hitX * P.hitK * dt;
  FX.hitV *= Math.pow(P.hitDamp, dt * 60);
  FX.hitX += FX.hitV * dt;

  // 手机位置 = 这张贴图里标好的手机点，跟着人一起平移、颠步、被推开
  const m = WORLD && WORLD.poses[FX.frame];
  if (m && m.phone) {
    FX.phoneX = FX.pairX + FX.hitX + (m.phone[0] - m.ax);
    FX.phoneY = GROUND + FX.bob + (m.phone[1] - m.ay);
  }

  FX.punch *= Math.pow(P.punchDecay, dt * 60);
  if (FX.punch < 0.002) FX.punch = 0;
  FX.tintA *= Math.pow(P.tintDecay, dt * 60);
  if (FX.tintA < 0.004) FX.tintA = 0;
}

/* ---------- 命中：一次礼物/点赞落地时发生的全部事情 ---------- */

/* 一次命中同时动四样东西：粒子、角色位移与染色、屏幕震动、顿帧。
   写成单一入口而不是散在各处，是因为这四样的强度必须一起缩放 —— 分开调的话
   小礼物会震得比大礼物还狠，而观众读到的"这一下有多重"正是它们的合力。

   side: +1 打向查岗党(左/女方)，-1 打向灭迹党(右/男方)
   power: 1 点赞级  2 普通礼物  3 大礼物 */
/* x：爆在哪儿（弹幕传它碰到轮廓的那一点）；不给就爆在挨打那个人这个高度的轮廓上 */
function impact(side, y, power, recipe, x) {
  const r = recipe || RECIPE.thud;
  const s = power >= 4 ? 2.8 : power === 3 ? 1.7 : power === 2 ? 1.0 : 0.55;
  if (x == null) x = frontAt(y, -side) ?? FX.phoneX;

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

/* 礼物碰到**挨打那个人的轮廓**才爆：在它的飞行高度上，对方身体朝着这边的那条边在哪儿。
   from = +1（查岗党从左边扔）打男生，-1 打女生；路过自己这方的人不算碰到。
   轮廓是 build.py 按行量好的（world.json 的 poses[帧].edge，每 step 行一个，-1 = 这行没这个人），
   这里再叠上当前的站位、被推开的位移（hitX）、颠步和受击放大（punch，以脚底为锚）。
   以前任何高度都打在手机那条竖线上：打头的、打腿的都在半空同一条线上碎掉，碰不到人。
   这一行没有人（头顶上方、对方趴下后的上半截）就往上下找最近的一行，找 EDGE_SNAP 像素
   以内；再没有返回 null —— 那一发从人身边飞过去。发射时已经把高度压进了对方身体的范围
   （targetSpan），走到这一步只会是飞行途中对方正好倒下。 */
const EDGE_SNAP = 80;
function frontAt(y, from) {
  const m = WORLD && WORLD.poses[FX.frame];
  if (!m || !m.edge) return FX.phoneX;
  const e = m.edge, row = from > 0 ? e.b : e.a, k = 1 + FX.punch;
  const i = Math.round(((y - GROUND - FX.bob) / k + m.ay) / e.step);
  for (let d = 0; d * e.step <= EDGE_SNAP; d++) {
    for (const j of d ? [i - d, i + d] : [i]) {
      if (row[j] >= 0) return FX.pairX + FX.hitX + (row[j] - m.ax) * k;
    }
  }
  return null;
}
/* 挨打那个人此刻在屏幕上占的高度范围 [上, 下]。发射高度要落在这里面 —— 对方趴下以后
   只剩贴地那一截，按站着的人给的高度带去扔，大半都会从他头顶上飞过去。 */
function targetSpan(from) {
  const m = WORLD && WORLD.poses[FX.frame];
  if (!m || !m.edge) return null;
  const e = m.edge, row = from > 0 ? e.b : e.a, k = 1 + FX.punch;
  let lo = -1, hi = -1;
  for (let j = 0; j < row.length; j++) if (row[j] >= 0) { if (lo < 0) lo = j; hi = j; }
  if (lo < 0) return null;
  const at = (j) => GROUND + FX.bob + (j * e.step - m.ay) * k;
  return [at(lo), at(hi)];
}
// 对冲掉的那些不碰人，在中线（手机）前互相撞掉
const midAt = () => FX.phoneX;
const phonePos = () => [FX.phoneX, FX.phoneY];

/* ---------- 角色：姿势贴图 ---------- */
/* 每张贴图按 world.json 里的锚点贴：锚点 (ax, ay) 对到屏幕上的 (pairX, GROUND)。
   不做相邻帧的交叉淡化：两张画的是不同姿态，叠在一起是两副骨架互相穿透的
   重影。硬切虽然跳，但每一帧都是清清楚楚的一张画。 */
class PoseView {
  constructor(imgs) { this.imgs = imgs; }

  /* punch 是缩放脉冲，tint 是命中染色 —— 角色是预渲染图，做不了受击变形，
     打击反馈只能来自贴图之外。缩放以脚底为锚，人挨了一下会"胀"一下但脚不
     离地；染色走 source-atop，只盖在已画出的角色像素上，不会糊到背景。 */
  draw(ctx, name, x, y, punch, tint, tintA) {
    const img = this.imgs[name], m = WORLD.poses[name];
    if (!img) return;
    const k = 1 + (punch || 0);
    const w = m.w * k, h = m.h * k;
    const dx = x - m.ax * k, dy = y - m.ay * k;
    ctx.drawImage(img, dx, dy, w, h);
    if (tintA > 0.004) {
      ctx.save();
      ctx.globalCompositeOperation = 'source-atop';
      ctx.fillStyle = rgba(tint, tintA);
      ctx.fillRect(dx, dy, w, h);
      ctx.restore();
    }
    this.shown = name;
  }
}

/* ---------- 背景：三间房拼成的长卷 ---------- */
/* 只画镜头里看得见的那一两间。三张图各两千多宽，全画一遍白费两倍填充。
   背景**不跟着震**：机位是固定的，整幅一起震就得把背景放大做 overscan 才不
   露边；震动留给人、弹幕和粒子 —— 那些才是正在发生冲突的东西。 */
function drawWorld(ctx, rooms) {
  let x = -(FX.camX - MID);
  for (let i = 0; i < rooms.length; i++) {
    const w = WORLD.rooms[i];
    if (x + w > 0 && x < W) ctx.drawImage(rooms[i], Math.round(x), 0, w, H);
    x += w;
  }
}

/* ── HUD ──
   顶上三行，从上到下：
     名字行   头像 · 队名 · 这一方已经把对面拽过来多少米（左右镜像）
     距离条   全宽一根。正中是起点（客厅正中），往左是女生卧室、往右是电竞房，
              条上按三间房分段铺底色 —— 它同时是小地图：手机图标在哪一段，两个人
              此刻就在谁的房间里。从正中到手机那一截涂领先方的颜色。
     拉力     两边的数并排摆在正中（见 drawPowerText）
   时钟跨在名字行正中。

   距离条是**一根**，不是左右两条：位置是一个数（S.pos），拽过来多少对面就
   退回去多少，劈成两条读起来像两个人各自有一份血，那是上一版的模型。 */

// 两侧严格镜像：右侧的 x 一律由 W - x - w 推出来，改一处两边一起动
const UI = {
  /* 直播间里这块画面会被缩到手机屏的三分之一宽，条细一点、字小一号就彻底
     看不清了。所以距离条横向**顶满**，从左边缘 18px 铺到右边缘 18px。
     排这一块要连**描边**一起算：文字的 lineWidth 5 会往外扩 2.5px。 */
  avR: 30, avCX: 44, avCY: 35,       // 头像圆：左侧圆心，右侧 = W - 它
  barX: 18, barY: 68, barH: 44,      // 距离条（68~112），宽 = W - 2×barX
  clkCY: 33,                         // 时钟那一行的中心（距离条上面）
  pwCY: 158,                         // 拉力那一行的中心（距离条下面，见 drawPowerText）
  sk: 12,                            // 斜切量：梯形两端各内切多少
};

/* HUD 自己的表现层状态。单独放一坨，是为了让人一眼看出改这里不会改谁输谁赢 ——
   战况全在 S 里，这里只有"闪一下""跳一下"这种活儿。 */
const HUD = {
  avA: null, avB: null,   // 两张头像（assets/ui/av_*.webp，加载不到就画纯色盘）
  lfA: 0, lfB: 0,         // 注入闪光余量：礼物砸进来那一下，拉力数字整个亮一次
  pfA: 0, pfB: 0,         // 上一帧的拉力，用来把"礼物注入"和"自然增长"分开
  mf: 0,                  // 过米闪光余量：距离条每跨过一整米，手机图标亮一下
  pm: 0,                  // 上一帧的位置，用来认出"又跨过一米"
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
/* 中线上那两块牌子（时钟、拉力）用的形。血条是平行四边形（顶边整体右移 sk），
   但它们跨在正中间，跟哪一侧对齐都会显得偏 —— 做成两端对称内切的梯形，
   既和血条是同一套切角语言，又不偏向任何一边。 */
const plate = (ctx, x, y, w, h, sk) => {
  ctx.beginPath();
  ctx.moveTo(x + sk, y); ctx.lineTo(x + w - sk, y);
  ctx.lineTo(x + w, y + h); ctx.lineTo(x, y + h); ctx.closePath();
};
/* 牌面的底：竖向渐变 + 顶边一道内亮线。纯色平涂在照片底图上会像贴了块塑料，
   上深下浅加一条高光，才读得出"一块有厚度的板"。 */
const plateFill = (ctx, x, y, w, h, sk, a) => {
  plate(ctx, x, y, w, h, sk);
  const g = ctx.createLinearGradient(0, y, 0, y + h);
  g.addColorStop(0, `rgba(26,31,43,${a})`);
  g.addColorStop(1, `rgba(9,12,19,${Math.min(1, a + .05)})`);
  ctx.save();
  ctx.shadowColor = 'rgba(0,0,0,.40)'; ctx.shadowBlur = 14; ctx.shadowOffsetY = 5;
  ctx.fillStyle = g; ctx.fill();
  ctx.restore();
  ctx.save(); ctx.clip();
  ctx.fillStyle = 'rgba(255,255,255,.10)'; ctx.fillRect(x, y, w, 2);
  ctx.restore();
  plate(ctx, x, y, w, h, sk);
  ctx.lineWidth = 1.5; ctx.strokeStyle = 'rgba(255,255,255,.22)'; ctx.stroke();
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
  if (HUD.pin >= 0) HUD.lfA = HUD.lfB = HUD.pin;
  else {
    if (S.fA - HUD.pfA > 2.5) HUD.lfA = 1;
    if (S.fB - HUD.pfB > 2.5) HUD.lfB = 1;
    HUD.lfA = Math.max(0, HUD.lfA - dt * 1.7);
    HUD.lfB = Math.max(0, HUD.lfB - dt * 1.7);
  }
  HUD.pfA = S.fA; HUD.pfB = S.fB;

  /* 过米闪光：位置**每跨过一个整米**闪一次，不是"在动就亮着"。按连续变化判
     的话，被拖期间每一帧都满足条件，闪光常亮，读出来是"这个图标是白的"。
     按整米跨越，拖得越快闪得越密，节拍本身就是速度。（血条时代掉血闪光的
     同一条规矩，衰减也沿用那次试出来的 7/秒。） */
  if (Math.floor(S.pos) !== Math.floor(HUD.pm)) HUD.mf = 1;
  HUD.mf = Math.max(0, HUD.mf - dt * 7);
  HUD.pm = S.pos;
}

function drawAvatar(ctx, A) {
  const img = A ? HUD.avA : HUD.avB, c = A ? GREEN : RED;
  // 正在被拖走的那一方：往右拖是查岗党被拖，往左拖是灭迹党被拖
  const dragged = A ? S.vel < -0.01 : S.vel > 0.01;
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
  // 被拖时外圈暖橙脉动：谁正在被拖走，扫一眼头像就知道
  if (dragged) {
    const k = 0.5 + 0.5 * Math.sin(HUD.t * 7.5);
    ctx.beginPath(); ctx.arc(cx, cy, r + 6, 0, 7);
    ctx.lineWidth = 3; ctx.strokeStyle = `rgba(255,190,72,${0.34 + 0.56 * k})`; ctx.stroke();
  }
  /* 圈色就是身份：赢了镀金、倒下转灰、其余时候是队色。结算画面上观众第一眼
     找的是脸，让脸自己把结果说了，比在中间多写一行字快。 */
  const win = S.phase === 'over' && (A ? S.winner > 0 : S.winner < 0);
  const out = S.phase === 'over' && S.winner !== 0 && !win;
  ctx.beginPath(); ctx.arc(cx, cy, r + 1.5, 0, 7);
  ctx.lineWidth = win ? 4.5 : 3.5;
  if (win) { ctx.shadowColor = 'rgba(255,208,80,.95)'; ctx.shadowBlur = 18; }
  ctx.strokeStyle = rgba(win ? [255, 212, 90] : out ? [110, 110, 118] : c, .96);
  ctx.stroke(); ctx.shadowBlur = 0;
  ctx.restore();
}

/* 米 → 距离条上的横坐标。正（查岗党拽过来）往左。 */
const barAt = (m) => MID - m / NUM.END * (W / 2 - UI.barX);

function drawDistBar(ctx) {
  const x = UI.barX, w = W - 2 * UI.barX, y = UI.barY, h = UI.barH, sk = UI.sk;
  const pos = clamp(S.pos, -NUM.END, NUM.END), px = barAt(pos);
  const lead = pos > 0 ? GREEN : RED;
  ctx.save();

  /* 快被拖到头了：终点那一端透红呼吸。按离终点剩多少算，不按领先多少 ——
     观众要知道的是"还有几步就完了"。 */
  const danger = Math.abs(pos) / NUM.END;
  if (danger > 0.75) {
    const k = (0.5 + 0.5 * Math.sin(HUD.t * 5.5)) * (danger - 0.75) / 0.25;
    const ex = pos > 0 ? x : x + w - 120;
    ctx.save(); ctx.shadowColor = `rgba(255,60,50,${0.5 + 0.45 * k})`; ctx.shadowBlur = 18;
    ctx.fillStyle = `rgba(255,60,50,${0.18 + 0.3 * k})`; ctx.fillRect(ex, y - 3, 120, h + 6);
    ctx.restore();
  }

  // 外框带投影：HUD 不浮起来就像直接印在墙上
  ctx.save();
  ctx.shadowColor = 'rgba(0,0,0,.42)'; ctx.shadowBlur = 12; ctx.shadowOffsetY = 4;
  plate(ctx, x - 3, y - 3, w + 6, h + 6, sk); ctx.fillStyle = 'rgba(6,8,11,.88)'; ctx.fill();
  ctx.restore();

  plate(ctx, x, y, w, h, sk); ctx.save(); ctx.clip();
  ctx.fillStyle = 'rgba(16,19,25,.70)'; ctx.fillRect(x, y, w, h);
  /* 三间房的底色分段 —— 小地图。按 world.json 现算门在几米，换背景不用改这里。
     压得很淡：它是地图不是战况，领先方的颜色要能盖在它上面读得出来。 */
  if (WORLD) {
    const dA = (WORLD.center - WORLD.rooms[0]) / P.pxPerM;                    // 卧室门（正）
    const dB = -(WORLD.rooms[0] + WORLD.rooms[1] - WORLD.center) / P.pxPerM;  // 电竞房门（负）
    const seg = [[NUM.END, dA, 'rgba(255,150,190,.30)', '女生卧室'],
                 [dA, dB, 'rgba(170,220,160,.20)', '客厅'],
                 [dB, -NUM.END, 'rgba(130,110,230,.34)', '电竞房']];
    ctx.font = 'bold 19px system-ui,"PingFang SC","Microsoft YaHei",sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    for (const [m0, m1, c, name] of seg) {
      const a0 = barAt(m0), a1 = barAt(m1);
      ctx.fillStyle = c; ctx.fillRect(a0, y, a1 - a0, h);
      ctx.fillStyle = 'rgba(255,255,255,.34)'; ctx.fillText(name, (a0 + a1) / 2, y + h / 2 + 1);
    }
    // 门：一道竖缝
    ctx.fillStyle = 'rgba(255,255,255,.30)';
    for (const m of [dA, dB]) ctx.fillRect(barAt(m) - 1, y, 2, h);
  }

  /* 从起点到手机：领先方的颜色。四段渐变 + 顶部高光 + 底边一道暗，是一根
     有圆度的管，不是一块涂了渐变的色块（血条时代定下的形制，照用）。 */
  const f0 = Math.min(px, MID), fw = Math.abs(px - MID);
  if (fw > 0.5) {
    const g = ctx.createLinearGradient(0, y, 0, y + h);
    g.addColorStop(0, rgba(lead.map(v => Math.min(255, v * 1.30 | 0)), .92));
    g.addColorStop(0.18, rgba(lead.map(v => Math.min(255, v * 1.12 | 0)), .92));
    g.addColorStop(0.58, rgba(lead, .92));
    g.addColorStop(1, rgba(lead.map(v => v * 0.52 | 0), .92));
    ctx.fillStyle = g; ctx.fillRect(f0, y, fw, h);
    const hg = ctx.createLinearGradient(0, y, 0, y + h * 0.30);
    hg.addColorStop(0, 'rgba(255,255,255,.26)'); hg.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = hg; ctx.fillRect(f0, y, fw, h * 0.30);
    ctx.fillStyle = 'rgba(0,0,0,.14)'; ctx.fillRect(f0, y + h - 3, fw, 3);

    /* 正在被拖：填充里有一串箭头朝拖的方向流。流速跟着 S.vel 走，停下来箭头
       就停 —— 距离条本身只显示"已经拖了多远"，这串箭头回答"现在还在拖吗、
       拖得多快"。血条时代的侵蚀带是同一个职责。 */
    if (Math.abs(S.vel) > 0.01) {
      const dir = S.vel > 0 ? -1 : 1, gap = 34;
      const ph = ((HUD.t * (40 + Math.abs(S.vel) * 60)) % gap) * dir;
      ctx.save(); ctx.beginPath(); ctx.rect(f0, y, fw, h); ctx.clip();
      ctx.strokeStyle = 'rgba(255,255,255,.55)'; ctx.lineWidth = 5; ctx.lineCap = 'round';
      for (let cx = f0 - gap + ph; cx < f0 + fw + gap; cx += gap) {
        ctx.beginPath();
        ctx.moveTo(cx - 6 * dir, y + 11); ctx.lineTo(cx + 6 * dir, y + h / 2); ctx.lineTo(cx - 6 * dir, y + h - 11);
        ctx.stroke();
      }
      ctx.restore();
    }
  }
  // 刻度：每 5 米一道淡缝，起点那道白而粗
  ctx.fillStyle = 'rgba(0,0,0,.28)';
  for (let m = -NUM.END + 5; m < NUM.END; m += 5) if (m) ctx.fillRect(barAt(m) - 1, y + h - 10, 2, 10);
  ctx.restore();
  plate(ctx, x, y, w, h, sk);
  ctx.lineWidth = 1.5; ctx.strokeStyle = 'rgba(255,255,255,.26)'; ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,.95)'; ctx.fillRect(MID - 2, y - 5, 4, h + 10);

  /* 手机图标：就是正在被抢的那部手机，它在条上的位置就是两个人在世界里的位置。
     比一个三角滑块多交代了一件事 —— 被拖来拖去的是什么。过一整米亮一下。 */
  const iw = 30, ih = 54, ix = px - iw / 2, iy = y + h / 2 - ih / 2;
  ctx.save();
  if (HUD.mf > 0.01) { ctx.shadowColor = `rgba(255,255,255,${HUD.mf})`; ctx.shadowBlur = 22 * HUD.mf; }
  ctx.beginPath(); ctx.roundRect(ix, iy, iw, ih, 7);
  ctx.fillStyle = '#15161b'; ctx.fill();
  ctx.shadowBlur = 0;
  ctx.lineWidth = 3.5; ctx.strokeStyle = '#fff'; ctx.stroke();
  ctx.beginPath(); ctx.roundRect(ix + 5, iy + 7, iw - 10, ih - 16, 3);
  ctx.fillStyle = rgba(Math.abs(pos) < 0.05 ? [230, 236, 246] : lead, .95); ctx.fill();
  ctx.restore();
  ctx.restore();
}

/* 拉力直接写成"拉力 575"，不画条，而且**两边的数并排摆在正中**。
   不画条：条要成立得有个量程，而拉力是没有上限的存量（大哥一秒注入 600、对面
   只有 80 时差值能到四万），画条只能开方压缩 —— 压完小额礼物推不动它、大额又
   早早顶到头，两头都读不出来。写成数字两头都准：刷一件跳一截，跳多少和礼物的
   push 值一一对应。
   放正中：分列左右两侧时没人会去比，而这两个数**必须放在一起比** —— 拖动速度
   算的就是它们的差，差过了 X 才拖得动。并排摆着，"我比他多多少"不用算。
   它比倒计时显眼一档也是故意的：观众刷礼物改变的是这个数，不是那个钟。
   排在距离条**下方**：上方那行归时钟和名字。 */
function drawPowerText(ctx) {
  const cy = UI.pwCY;
  ctx.save();
  ctx.textBaseline = 'middle';
  /* 底板宽度写死，不随位数变 —— 跟着数字宽窄伸缩的话，刷一件礼物牌子自己
     会抖一下，观众会以为是画面卡了。660 够两边各放到五位数：85px 的等宽
     数字每位约 51px，五位 255，加上中间"拉力"两个字和左右各 24 的缝。 */
  const px = MID - 330, py = cy - 38, pw = 660, ph = 76;
  plateFill(ctx, px, py, pw, ph, 14, .80);
  /* 归属靠**两端各一道队色亮边**，不是大片染色。整片渗色试过（120px、.26）：
     板是深的，队色叠上去只会变成一块墨绿和一块暗红，脏，而且待机时两个 0
     撑不住那么大两片颜色。细边亮度足、面积小，反而一眼分得清左右是谁的。 */
  ctx.save(); plate(ctx, px, py, pw, ph, 14); ctx.clip();
  for (const A of [true, false]) {
    const col = A ? GREEN : RED;
    ctx.save();
    ctx.shadowColor = rgba(col, .85); ctx.shadowBlur = 14;
    ctx.fillStyle = rgba(col, .92);
    /* 这道边要**跟着斜边倾斜**（skew 而不是 fillRect）：板是梯形，
       竖着画的矩形会被斜边切掉大半，只剩底下一个小三角。 */
    skew(ctx, A ? px : px + pw - 7, py, 7, ph, A ? 14 : -14);
    ctx.fill();
    ctx.restore();
  }
  ctx.restore();

  ctx.textAlign = 'center';
  ctx.font = 'bold 55px system-ui,"PingFang SC","Microsoft YaHei",sans-serif';
  txt(ctx, '拉力', MID, cy, 'rgba(232,238,246,.80)', 6);

  ctx.font = 'bold 85px ui-monospace,Menlo,monospace';
  for (const A of [true, false]) {
    const f = A ? S.fA : S.fB, c = A ? GREEN : RED, lf = A ? HUD.lfA : HUD.lfB;
    ctx.textAlign = A ? 'right' : 'left';
    // 礼物砸进来那一下数字整个亮一次 —— 原先条上那个菱形滑块的活
    if (lf > 0) { ctx.shadowColor = rgba(c, .95); ctx.shadowBlur = 30 * lf; }
    txt(ctx, f.toFixed(0), A ? MID - 79 : MID + 79, cy,
        `rgb(${c.map(v => Math.min(255, (v * (1.18 + .5 * lf)) | 0)).join(',')})`, 8);
    ctx.shadowBlur = 0;
  }
  ctx.restore();
}

function drawHUD(ctx) {
  ctx.save();
  drawDistBar(ctx);
  for (const A of [true, false]) {
    ctx.textBaseline = 'middle';
    drawAvatar(ctx, A);
    /* 队名 + 这一方拽过来的米数，并排在距离条**上方**的外侧。只写自己拽过来
       的那部分：对面占优时自己这边是 0.0 —— 两个数一个在涨另一个就是 0，
       哪边的数在跳，就是哪边在赢。 */
    const m = Math.max(0, A ? S.pos : -S.pos), ox = A ? 1 : -1;
    const nx = (A ? UI.avCX : W - UI.avCX) + ox * (UI.avR + 12);   // 队名从头像右缘起
    ctx.textAlign = A ? 'left' : 'right';
    ctx.font = 'bold 30px system-ui,"PingFang SC","Microsoft YaHei",sans-serif';
    txt(ctx, A ? '查岗党' : '灭迹党', nx, UI.avCY, '#fff', 6);
    ctx.font = 'bold 37px ui-monospace,Menlo,monospace';
    txt(ctx, m.toFixed(1) + 'm', nx + ox * 114, UI.avCY,
        m > 0.05 ? rgba((A ? GREEN : RED).map(v => Math.min(255, v * 1.15 | 0)), 1) : '#fff', 6.5);
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
    drawPowerText(ctx);
    const v = Math.abs(S.vel), over = S.phase === 'over';
    // 还没开局时不写"僵持"——那是对局里"谁都拖不动谁"的读数，待机时写它是假的
    const note = over || idle ? '' : v > 0.01
      ? (S.vel > 0 ? `◀ ${v.toFixed(1)}米/秒` : `${v.toFixed(1)}米/秒 ▶`) : '僵 持';
    ctx.textBaseline = 'middle';
    ctx.font = `bold ${over ? 27 : 23}px ui-monospace,Menlo,monospace`;
    const tw = ctx.measureText(tip).width;
    ctx.font = 'bold 21px system-ui,"PingFang SC","Microsoft YaHei",sans-serif';
    const nw = note ? ctx.measureText(note).width + 18 : 0;
    // 底板跟着内容伸缩：写死一个够宽的值会在"僵持"时空出一大片压在名字上
    const bw = tw + nw + 46, bx = MID - bw / 2;
    ctx.save();
    /* 常态用和拉力板同一套梯形；绝杀/反击/结算这三种要变色，就还用它们
       自己的底色平涂 —— 那几下是"出事了"，形一样但颜色必须跳出来。 */
    if (bg === 'rgba(8,10,14,.74)') plateFill(ctx, bx, UI.clkCY - 18, bw, 36, 9, .80);
    else {
      plate(ctx, bx, UI.clkCY - 18, bw, 36, 9);
      ctx.fillStyle = bg; ctx.fill();
      ctx.lineWidth = 1.5; ctx.strokeStyle = 'rgba(255,255,255,.26)'; ctx.stroke();
    }
    ctx.restore();
    ctx.textAlign = 'left';
    ctx.font = `bold ${over ? 27 : 23}px ui-monospace,Menlo,monospace`;
    txt(ctx, tip, bx + 23, UI.clkCY, col, 4);
    if (note) {
      ctx.font = 'bold 21px system-ui,"PingFang SC","Microsoft YaHei",sans-serif';
      txt(ctx, note, bx + 23 + tw + 18, UI.clkCY,
          v > 0.01 ? '#ffd86e' : 'rgba(232,236,242,.70)', 4);
    }
  }
  ctx.restore();
}

/* ---------- 启动 ---------- */
const load = (src) => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = src; });

(async function boot() {
  const cvBg = document.getElementById('bg'), cvCh = document.getElementById('ch'), cvFx = document.getElementById('fx');
  const bctx = cvBg.getContext('2d'), cctx = cvCh.getContext('2d'), fctx = cvFx.getContext('2d');

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
      // 被拖出去一半 / 八成的时刻 —— 局长看的是位置，不是此刻的姿态
      const far = Math.abs(S.pos) / NUM.END;
      if (mark50 < 0 && far >= 0.5) mark50 = el;
      if (mark80 < 0 && far >= 0.8) mark80 = el;
    }
    const fmt = (v) => v < 0 ? '—' : `${v / 60 | 0}:${String(v % 60 | 0).padStart(2, '0')}`;
    document.getElementById('msg').textContent =
      `注入 ${injA}:${injB}／秒 → 结束于 ${fmt(el)}  位置 ${S.pos.toFixed(1)}m  `
      + `拉力 ${S.fA.toFixed(0)}:${S.fB.toFixed(0)}  差 ${(S.fA - S.fB).toFixed(0)}  `
      + `姿态 p=${S.p.toFixed(1)}  `
      + `过半 ${fmt(mark50)}  八成 ${fmt(mark80)}  `
      + `${S.winner > 0 ? '查岗党胜' : S.winner < 0 ? '灭迹党胜' : '平/未分'}`;
    document.title = 'SIMDONE ' + document.getElementById('msg').textContent;
    return;
  }


  /* 弹幕往手机那条竖线上打。发射高度按人物站位给：从头顶往上一点到膝盖，
     脸那一段常规火力要绕开（见 ammo.js）。这几个数跟着 GROUND 走 —— 人物
     挪了，弹幕的高度自动跟着挪。 */
  Ammo.init({
    W, frontAt, midAt, targetSpan,
    band: { top: GROUND - 660, bot: GROUND - 90, face: [GROUND - 600, GROUND - 490] },
    /* 命中只负责演出，**不拖人**。位置是双方拉力差每秒拖出来的（见 battle）
       —— 让命中再推一次，等于同一份力算两遍，而且会把"两边都在刷时谁也拖不动
       谁"这条最要紧的手感破坏掉。弹幕是拉力的表现形式，不是位移的来源。 */
    onHit(p, x) {
      impact(-p.from, p.y, p.exec ? 4 : p.g.power, RECIPE[p.g.recipe], x);
    },
    /* 对冲掉的那些在中线互相撞掉：粒子照爆，但不推角色、不染色、不顿帧。
       它要回答的问题只有一个 —— "我刷了礼物怎么没拖动"。答案就在画面上：
       你的东西被对面在半空撞掉了。 */
    onClash(p, x) {
      RECIPE[p.g.recipe].burst(x, p.y, p.from, 0.42);
      Particles.addShake(0.6);
    },
  });

  /* 气泡挂在手机上 —— phonePos 取自当前贴图里标好的手机点，所以消息永远是
     从正在被抢的那部手机里冒出来的。 */
  Bubble.init({ phoneAt: phonePos });

  /* 长卷背景与姿势贴图，都由 v14/build.py 生成。world.json 是它们的说明书：
     每间房多宽、客厅正中在哪、每张贴图的锚点和手机位置。 */
  const vq = Q0.get('v') ? '?v=' + encodeURIComponent(Q0.get('v')) : '';
  WORLD = await (await fetch('assets/world/world.json' + vq)).json();
  WORLD.total = WORLD.rooms.reduce((a, b) => a + b, 0);
  const rooms = await Promise.all(WORLD.rooms.map((_, i) => load(`assets/world/room${i}.webp`)));
  const poseNames = Object.keys(WORLD.poses);
  const poseImgs = {};
  await Promise.all(poseNames.map(n => load(`assets/world/pose_${n}.webp`).then(im => { poseImgs[n] = im; })));
  const actors = new PoseView(poseImgs);
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
    `长卷 ${WORLD.total}px · 姿势 ${Object.keys(poseImgs).length} 张` +
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
      /* hudTick 也要跟着快进：它管两种闪光的余量。不调的话预热结束那一帧的
         HUD 永远是"刚开局、什么都没闪过"的样子，?livet 微调也扫不到闪光。 */
      battle(1 / 30); Ammo.update(1 / 30); Particles.update(1 / 30); S.t += 1 / 30;
      derive(1 / 30); hudTick(1 / 30);
    }
    // 预热完冻住**进度**：战况定在这一刻，而火力、弹幕、粒子照跑 —— 截图要的
    // 是"打到这个比分时画面是活的什么样"，不是一张静止的死图
    if (Q.get('liveFreeze') === '1') freeze = true;
    // liveStop 把整个世界停在预热结束那一帧：要看清"处决落地的瞬间"只能这样，
    // 它只存在零点几秒，主循环再跑一下就过去了
    if (Q.get('liveStop') === '1') { stopAll = true; live = false; }
  }
  if (Q.has('p')) { S.p = clamp(+Q.get('p'), 0, 100); S.auto = false; }
  // ?pos=<米> 直接把两个人摆到某个位置（正 = 往左、进女生卧室），截各房间的样子用
  if (Q.has('pos')) S.pos = clamp(+Q.get('pos'), -NUM.END, NUM.END);
  /* 自动演示默认就是关的（见 S.auto），?auto=1 才打开 —— 展示时它会自己来回
     拽手机，观众分不清哪一下是刷礼物推的。?auto=0 保留着，写脚本时不用管
     默认值是什么。 */
  if (Q.get('auto') === '0') S.auto = false;
  if (Q.get('auto') === '1') S.auto = true;
  /* X / M / V_Z 三个数就地试：?x=30&m=1000&vz=1.5。V_Z 决定局长 —— 1.5 是从
     需求例子"差 1000 每秒扣 5%"换算来的（约 70 秒一局）；?end= 改终点多远。 */
  if (Q.has('x')) NUM.PULL_X = Math.max(0, +Q.get('x'));
  if (Q.has('m')) NUM.PULL_M = Math.max(1, +Q.get('m'));
  if (Q.has('vz')) NUM.V_Z = Math.max(0, +Q.get('vz'));
  if (Q.has('end')) NUM.END = clamp(+Q.get('end'), 5, 30);
  if (Q.has('linefull')) NUM.LINE_FULL = Math.max(1, +Q.get('linefull'));
  /* 钉住闪光。两个都在这里**当场写一次值**，不能只设 pin 等 hudTick 去写 ——
     ?liveStop 把主循环停在 `render(); return`，hudTick 一次都不会跑，
     只设 pin 的话截出来的永远是没闪光的那一帧（踩过）。 */
  // ?hudflash=0..1 钉住拉力的注入闪光，专门用来截"礼物砸进来那一下"的形态
  if (Q.has('hudflash')) { HUD.pin = clamp(+Q.get('hudflash'), 0, 1); HUD.lfA = HUD.lfB = HUD.pin; }
  if (Q.has('overt')) Result.setPin(Math.max(0, +Q.get('overt')));   // 结算定帧
  // ?zoom=1 用画布原生尺寸铺开，截图时才看得清脸和手的实际画法
  if (Q.get('zoom') === '1') document.getElementById('stage').style.width = W + 'px';
  document.getElementById('pv').value = S.p;
  document.getElementById('auto').checked = S.auto;
  for (let i = 0; i < 90; i++) derive(1 / 60);   // 预热，让指数趋近收敛到位

  /* 震动只作用在"正在发生冲突的东西"上 —— 角色、弹幕、粒子。背景不震（见
     drawWorld），HUD 也不震，它不在场景里。
     拆成三段是因为它本来就是三张画布、三种代价：背景每帧画一两张房间图，
     角色每帧画一张贴图，特效层则随着场上有多少东西线性涨。"哪一层在拖后腿"
     只有分开计时才答得出，而合在一个函数里就只能猜。 */
  function renderBg() {
    bctx.clearRect(0, 0, W, H);
    drawWorld(bctx, rooms);
  }

  function renderActors() {
    const ox = Particles.off.x, oy = Particles.off.y;
    cctx.clearRect(0, 0, W, H);
    cctx.save(); cctx.translate(ox, oy);
    actors.draw(cctx, FX.frame, FX.pairX + FX.hitX, GROUND + FX.bob, FX.punch, FX.tint, FX.tintA);
    cctx.restore();
  }

  function renderFx() {
    const ox = Particles.off.x, oy = Particles.off.y;
    fctx.clearRect(0, 0, W, H);
    fctx.save(); fctx.translate(ox, oy);
    // 气泡在弹幕之下：它贴在后面那堵墙上，弹幕是前景，飞过时该压过去
    Bubble.draw(fctx);
    /* 弹幕在角色之上、粒子之下：它飞向两个人中间，画在角色底下的话命中前
       最后那段就被身体挡掉了；而粒子是命中的爆炸，该盖在弹幕上面。 */
    Ammo.draw(fctx);
    Particles.draw(fctx);
    fctx.restore();
    /* 结算全屏接管：演出图铺满整幅，距离条不再画。结果已经写在画面里
       （谁在抡枕头、谁跪着哭），再摆一遍是重复。 */
    if (S.phase === 'over') Result.draw(fctx);
    else drawHUD(fctx);
    Particles.drawFlash(fctx, W, H);
  }

  function render() { renderBg(); renderActors(); renderFx(); }

  /* 并排出胶片的公共部分：n 格，每格先跑 setup(i) 再渲染，左上角写 label(i)。 */
  function filmstrip(n, setup, label) {
    const sc = 0.5, out = document.createElement('canvas');
    out.width = n * W * sc; out.height = H * sc;
    const o = out.getContext('2d');
    o.fillStyle = '#0c0e12'; o.fillRect(0, 0, out.width, out.height);
    for (let i = 0; i < n; i++) {
      setup(i);
      render();
      const dx = i * W * sc;
      for (const c of [cvBg, cvCh, cvFx]) o.drawImage(c, dx, 0, W * sc, H * sc);
      const t = label(i);
      o.font = '600 15px system-ui';
      o.fillStyle = 'rgba(0,0,0,.66)'; o.fillRect(dx, 0, o.measureText(t).width + 16, 26);
      o.fillStyle = '#fff'; o.fillText(t, dx + 8, 18);
    }
    const stage = document.getElementById('stage');
    stage.style.width = out.width + 'px';
    stage.style.aspectRatio = `${out.width}/${out.height}`;
    stage.innerHTML = '';
    out.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    stage.appendChild(out);
  }

  /* ?strip=1 七种动作 × 各自该在的房间并排摆：一次看清动作、背景、距离条、
     手机位置四样东西对不对得上。p 定动作、pos 定卷到哪 —— 两者本来由同一个
     拉力差推出来，这里分开给是为了每格都落在一个有代表性的位置上。 */
  if (Q.has('strip')) {
    const cells = [[50, 0], [68, 4], [81, 12], [95, 24], [32, -4], [19, -12], [5, -24]];
    filmstrip(cells.length, (i) => {
      [S.p, S.pos] = cells[i]; S.vel = (S.p - 50) / 50 * NUM.V_Z; S.t = 3.0;
      FX.pose = 'n'; FX.poseT = 0;
      for (let k = 0; k < 240; k++) derive(1 / 60);   // 逐档每档停 stageHold，要走够
    }, (i) => `p=${cells[i][0]} pos=${cells[i][1]}m  ${FX.pose}/${FX.frame}`);
    return;
  }

  /* ?loopstrip=1 僵持循环的 8 格按播放顺序并排 —— 循环帧之间抖不抖、手机
     是不是在来回走，只有摊开才看得出来。 */
  if (Q.has('loopstrip')) {
    filmstrip(LOOP_N.length, (i) => {
      S.p = 50; S.pos = 0; S.vel = 0; FX.pose = 'n';
      FX.poseT = (i + 0.5) / P.loopFps;
      derive(0);
    }, (i) => `${i} ${FX.frame}  手机 x=${FX.phoneX.toFixed(0)}`);
    return;
  }

  /* ?gaitstrip=aK 把某一档的步态循环按顺序摊开：两条腿是不是交替往后、上半身
     有没有跟着跳。 */
  if (Q.has('gaitstrip')) {
    const g = WORLD.gaits[Q.get('gaitstrip') || 'aK'].frames;
    const p = { a: 81, b: 19 }[g[0][0]];
    filmstrip(g.length, (i) => {
      S.p = p; S.pos = 0; S.vel = 0; FX.pose = g[0]; FX.poseT = 0;
      FX.gaitPh = (i + 0.5) / g.length;
      derive(0);
    }, (i) => `${FX.frame}`);
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
        o.fillText(`${Q.get('fxrecipe') || 'thud'} p${power}`, dx + 8, 42);
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
    const k = { p: S.p, pos: S.pos, vel: S.vel, clock: S.clock, phase: S.phase,
                big: S.big, sudden: S.sudden, stand: S.stand, winner: S.winner };
    battle(dt);
    if (freeze) Object.assign(S, k);
    if (S.auto && S.phase === 'idle') {
      S.p += dir * dt * 9 * (0.35 + Math.abs(Math.sin(S.t * .27)) * 1.5);
      if (S.p > 97) { S.p = 97; dir = -1; } if (S.p < 3) { S.p = 3; dir = 1; }
    }
    if (S.phase === 'idle') drift(dt);
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
        ? `p=${S.p.toFixed(1)}  位置${S.pos.toFixed(1)}m  手机x=${FX.phoneX.toFixed(0)}  ${actors.shown}  `
        : `位置 ${S.pos.toFixed(1)}m ${S.vel.toFixed(2)}m/s  拉力 ${S.fA.toFixed(0)}:${S.fB.toFixed(0)}  `
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
    else { S.phase = 'idle'; S.fA = S.fB = 0; S.p = 50; S.pos = 0; S.clock = NUM.MATCH; Ammo.clear(); document.getElementById('start').textContent = '开始对局'; }
  };
})();
