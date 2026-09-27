# 真相喷雾妹子（commit 752300b）对抗式审查 · 第 1 轮

审查对象：`web/crew.js`（TRUTH / drawTruth / hoverPose / CrewGroup）、`web/main.js`（Truth.init / RECIPE.truth）、`web/fx.js`（kind `chat`）。
桌面容器上部署的 crew.js / main.js / fx.js 与本机 md5 一致（f13b83db… / 23fa4da8… / 47cd7c63…），审的就是线上这份。
**没有改任何代码或素材。**

## 总表

| 条 | 判定 | 问题（严重度） |
|---|---|---|
| A 看点 | **合格** | A1 后腿被屏幕左沿切掉（次要）；A2 刹停冲击环盖住她的身子 0.36s（次要） |
| B 猎奇/炫酷 | **不合格** | B1 喷流本身几乎看不到：喷口离脸只有约 110px，一半被喷口焰盖住（**重要**）；B2 bubble.js 的消息气泡几乎一直压在喷口上（**重要**） |
| C 流畅 | **不合格** | C1 人一动，尾焰就散成一串孤立的淡绿圆球（进场、离场都这样）（**重要**）；C2 瞄准角速度瞬间反转 / 瞬间起转（次要）；C3 刹停和第一喷挤在同一帧（次要） |
| D 遮挡与层次 | **合格** | D1 三人同时在场时，她的靴子盖住平衡车闺蜜的脸（次要）；D2 p=95 时瞄准角钉死在下限 −0.8，扫动没了（次要） |
| E 正确性 | **不合格** | E1 第 4 次召唤约 49% 会多出第 4 个人，而且是重复形象（**重要**）；E2 离场途中被召唤会瞬间消失、再从头进场（次要）；E3 `?bestie=2` 会抛 TypeError（次要，只影响诊断参数） |
| 控制台 | **无相关报错** | 唯一一条是 `favicon.ico` 404（页面没声明 icon，改动前就有），原文见 E 节 |

## 证据怎么拿的

- 胶片：`ssh kf-deployment '/tmp/shot.sh <名字> "4800,900" "ammostrip=10&ammoms=400&ammogift=bestie&bestie=1&v=<新值>"'`
  （窗口高度用 900 不用 670：670 会把一格 853px 高的画面下半截裁掉）。→ `truth_ammostrip_400ms.png`
- **逐帧整帧取样（本轮主力）**：胶片最多 12 格、每次都从 t=0 起拍、只有半分辨率，拍不到离场段 33ms 间隔的画面。
  所以写了一个 Playwright 脚本 `tools/h.py`：接管页面的 `requestAnimationFrame`，用固定 16.667ms 步长驱动**真实主循环 `frame()`**（走的是 live 路径，不是胶片路径），
  在指定毫秒抓 960×1707 的整帧（bg/ch/fx 三层合成），同时每帧记录 `Truth.peek()` / `Bestie.peek()` 的 t / aim / want / kick / lean / m。
  用法：`scp tools/h.py cN.json kf-deployment:/tmp/rv/ && ssh kf-deployment 'cd /tmp/rv && python3 h.py cN.json'`，
  cN.json 形如 `{"q":"p=50&auto=0&v=x","out":"/tmp/rv/c1","act":"Truth.summon()","total":3900,"caps":[0,100,...]}`。
  `act` 的调用都等价于正式路径：`Truth.summon()` 等于 `?bestie=1`，`BestieGroup.summon()` 等于 `CREW.bestie.summon()`，`giveGift(1,'boom')` 就是真实送礼。
- 运动学：`tools/kin.py` 按 crew.js 的 hoverPose / carried 公式，从每帧日志算出靴尖、喷口、罐尾的屏幕轨迹，再求逐帧速度差（结果在 `truth_C_kinematics_log.json` 基础上算出）。
- 调度统计：`tools/sched.py` 在页面里对 `BestieGroup.summon()` 做 3000 / 2000 次蒙特卡洛统计。

下文 "c1 1000ms" 指 c1 这组（`p=50&auto=0`，`Truth.summon()`）召唤后第 1000ms 的整帧。注意：第一击的 0.11s 顿帧会冻住 crew 的时钟，所以墙钟毫秒比她自己的 b.t 多 110ms。

---

## A. 看点 —— 合格

**证据** `truth_A_girl_fullres.png`（c1 1000 / 2000ms 全分辨率）、`truth_A_hover_4frames.png`（550/1000/1600/2500ms）、`truth_C_kick_waist.png`（1467~1600ms 腰部特写）
- 脸：悬停全程露在罐尾左下方，没被罐子、HUD 或尾焰挡住（尾焰从罐尾往左上喷，贴着她头顶出去，挡不到脸）。胸前、短裙、前腿的白色过膝靴完整可见。
- 大小：从头到鞋跟约 550px，占屏高 32%；罐子横跨约 520px，是画面左半边最大、最亮的物体。
- HUD：悬停时罐顶最高在 y≈590，血条/距离条下沿在 y≈200，不冲突。只有进场那 0.1s 罐子从 HUD 背后穿过（`truth_C_drop_33-200.png`，117~133ms），这是合理的出场方式。
- 腰部分层接缝：后坐时上身绕腰转 ±0.03 rad，短裙把接缝盖住了，逐帧看不出撕裂（`truth_C_kick_waist.png`）。

**A1 后腿被屏幕左沿切掉 — 次要**
- 复现：`p=50`，c1 1000~3300ms 任意一帧；`truth_A_rearleg_cut.png`
- 现象：往后甩的那条腿从膝盖往下出了画，小腿和靴子全没了。"长腿"是验收点之一，现在只有前腿是完整的。
- 已排除一个方向：在页面里把 perch 临时改成 `[215, GROUND−175]`、s 改成 0.9 试过（`truth_A_perch_variants.png` 第 2 格），后腿**照样出画**，人还小了一圈。原因是整个人绕肩转约 −0.38 rad，这条腿本来就朝左下方甩，**靠挪悬停点修不好**。
- 建议：改素材层，不改参数。`v14/truth/make.py` 切层时把后腿单独切成一层，挂在 `whole` 下面，再额外往上收约 0.35 rad（跟 arm 层的做法一样），或者让这条腿弯膝收回来。如果不打算改图，就接受现状：前腿完整，后腿出画读起来也像"从画外飞进来"。

**A2 刹停冲击环正好套在她身上 — 次要**
- 复现：c2 567~700ms，`truth_C_arrive_533-700.png`
- 现象：`RECIPE.truth.arrive` 的两道 ring（`main.js:868-869`）以腰为圆心，而 ring 这个 kind 画出来是压扁一半的椭圆（`fx.js:409` `r*0.5`），读成一个呼啦圈套在腰上，0.36s 里横切过她的身体和裙子，这正是最想让人看的那段。
- 建议：环心下移到脚底（`onArrive` 里 `y + 180*s`），或者改用不压扁的圆环。后一种要在 fx.js 新开一个 kind（比如 `shock`），`ring` 本身不要动，因为命中环是按"地面上的环"设计的。

---

## B. 猎奇 / 炫酷 —— 不合格

**合格的部分**
- 罐子：体量感足，黄黑警示条、"真相喷雾"四个字、红色喷嘴在浅绿墙和米色地板上都清楚（所有帧）。
- 悬停时的尾焰：罐尾往左上喷出一股青柠色烟柱，因为人不动、雾团叠得起来，读得出是"喷气"（`truth_A_girl_fullres.png`）。
- 命中爆点：青柠雾团糊满男生的脸，白底深绿描边的聊天图标往上蹦，星星四溅。一眼能读出"脸被喷了，冒出消息"（`truth_B_hits_850-2000.png`）。深绿描边在卧室粉墙、电竞房暗色墙上都看得见（`truth_D_pos+20_-20.png`）。
- 星星：暖黄白底加深绿描边，在各个房间都看得清。

**B1 看不到喷流，只看到"喷口一朵星 + 脸上一团雾" — 重要**
- 复现：`p=50`，c2 567~700ms 全分辨率 `truth_B_firsthit_567-700.png`；c1 850~2000ms `truth_B_hits_850-2000.png`
- 数据：日志里喷口 m≈(541,797)，瞄点 tg≈(640,840)，**喷口到脸只有约 110px**。喷口焰半径 34~52（`crew.js:493` flare），一个喷口焰就把这段距离盖掉一半。雾以 V 1250 的速度出去，0.09s 就飞到脸上，同一时刻在路上的雾团只有约 10 个，看到的是两三团小绿圆。
- 为什么不合格：用户要的是"大型喷雾有看点"。现在罐子大，但"喷"这个动作在画面上只有 50px 左右的一截，读成罐子顶着他的脸冒了一下，看不到"一股雾冲出去"。平衡车闺蜜离得远，喷流反而比她长（`truth_D_crowd.png` 里的橙色喷锥）。
- 建议（`crew.js` TRUTH / TRUTH_FX）：
  1. `fluid.V` 1250 → 600~700：路上的雾团翻倍、连成一个锥。G 只有 40，瞄准几乎不受影响；
  2. `TRUTH_FX.r0` 10 → 20：一出口就是大团，读成高压喷出来的；
  3. `TRUTH_FX.flare` [34,52] → [20,32]：喷口焰退回"点火"的角色，不要盖住喷流；
  4. 如果还是嫌短，就学 WATER 的做法，从喷口到最新一团画一条渐粗的青柠锥形带（深绿描边），保证每帧都有一条完整的"喷流"。

**B2 游戏本身的消息气泡几乎一直压在喷口和罐头上 — 重要**
- 复现：`p=50`，c1 850 / 1000 / 1300 / 1600 / 2000 / 2500 / 3000 / 3300 / 3400 / 3500ms，这 10 帧里全部都有 bubble.js 的消息（"我好想你""怎么不回我""今天梦到你了"等）盖在喷口或罐子前半截上（`truth_B_hits_850-2000.png`、`truth_C_exit_3000-3800.png`、`truth_D_p95_zoom.png`）。
- 原因：bubble.js 从手机上方 44px 出生，往上升 140px 再往上顶（`bubble.js:108`），升的那条走廊正是罐子前半截和喷口所在的 x≈400~600、y≈700~850。气泡画在特效层（`main.js:2000`），会盖住喷口焰和喷流。
- 建议：她在场时把气泡出生点往男生那边挪。改 `main.js:1779` 的 `phoneAt`，套一层 `() => { const [x, y] = phonePos(); return Truth.active() ? [x + 150, y] : [x, y]; }`；或者让她在场期间 Bubble 的 RISE 减半，让气泡停在罐子下方。两种都不会碰到气泡给脸让路的原规则。

---

## C. 流畅 —— 不合格

**合格的部分**
- 进场位置连续：easeOut 刹停在 t=0.55 时速度为 0，之后晃动在 0.3s 里从 0 长满，位置没有跳变（`truth_C_enter_0-600.png`，100ms 一格；`truth_C_drop_33-200.png`，17ms 一格）。先露靴子，再露罐子，150ms 时全身入画，读得出"从上面冲下来"。
- 悬停：瞄准平滑跟随。1.0~3.3s 之间 aim 只在 −0.37 ~ −0.45 之间缓慢变化，**没有跳变**（`kinematics_log`）。
- 后坐：每次按下，喷口在一帧里上跳约 25px，然后按 e^−9t 衰减（运动学：喷口 Δv≈1650px/s，只出现在 bt=0.55 / 1.40 / 2.28 / 3.13 这四个按下的时刻）。这是刻意做的一下"震"，腰部没有撕裂，算合格。
- 离场：位置按 u² 从静止开始加速，连续；离场后雾照样飞完、照样命中（c1 3700/3800ms 男生脸上仍有雾团，`truth_C_exit_3000-3800.png`）。

**C1 人一动，尾焰就断成一串孤立的淡绿圆球 — 重要**
- 复现：c2 400/467/533ms、c1 3700ms，`truth_C_exhaust_beads.png`；400ms 胶片 `truth_ammostrip_400ms.png` 第 2 格也看得到
- 现象：进场那 0.55s 里，从她罐尾一直到屏幕顶端是一串间距约 60px、互不相连的淡绿圆片。离场时这串珠子留在她身后，压在她靴子上，而罐尾那边反而没东西。
- 原因：尾焰按时间匀速出（`crew.js:567` rate 40/s，喷的时候 ×2），每团都从**当帧**的罐尾位置出生（`crew.js:267-276`）。人静止时它们叠成烟柱；进场时人以 3000~8000px/s 往下冲，两团之间差出几十上百 px，就断开了。
- 另外，离场时 aim 被放平到 0，尾焰朝**正左方**喷（`dir = angles(b, th)[1]`）。她是往上冲的，尾焰却不往下喷，"是它把她顶上去的"这层意思没了。
- 建议：
  1. 出生点做子帧插值：记下上一帧的罐尾位置 `b.exP`，同一帧里出的 n 团沿 `exP → r` 均匀摆开（跟雾的 `age` 补飞是同一个思路）。再加一条按距离补发：`b.ex += dt*X.rate + 移动距离/14`，保证两团间距不超过 14px；
  2. 离场段尾焰方向改成朝下（`dir` 在 t>se 时往 −π/2 插值），她冲出去时底下拖一条向下的焰。

**C2 瞄准角速度瞬间反转 / 瞬间起转 — 次要**
- 复现：c2 300~533ms（`truth_C_aimrev_300-533.png`）；日志 bt=0.367：aim −0.560 → −0.572 → −0.552，角速度在一帧里从 −1.6 rad/s 变成 +1.2 rad/s，靴尖的横向速度在一帧里从 −241 变成 +403px/s。bt=3.35 离场起步：want 从 −0.43 一帧跳到 0，靴尖速度在一帧里从 (−145,−51) 变成 (555,273)px/s。
- 为什么是次要：两处都叠在大位移上（进场下落、离场上升），33ms 胶片里不显眼，但在 60 帧设备上腿会"咔"地换一下方向。
- 建议：`crew.js:252` 的限速跟随改成带角速度的临界阻尼：`b.av += ((want-b.aim)*K - b.av*2*Math.sqrt(K))*dt; b.av = clamp(b.av, ±AIM.rate); b.aim += b.av*dt`，K≈40。只给 `cfg.whole` 用，哥们和平衡车闺蜜不受影响。

**C3 刹停和第一喷在同一帧 — 次要**
- 复现：c2 533~700ms（`truth_C_arrive_533-700.png`）：冲击环、喷口焰、第一击的爆点、全屏白闪、震屏全挤在 0.55~0.63s 之间。
- 为什么：`spraying = b.t >= T.enter`（`crew.js:255`），落地那一帧就开喷，"刹住"和"开火"两个节拍混成一个。
- 建议：开喷条件改成 `b.t >= T.enter + 0.18`（给 TRUTH 加一个 `T.fire` 字段，其余角色取 0），先"嘭"地停住，再"呲——"。

---

## D. 遮挡与层次 —— 合格

**证据**
- 女主：p=50 时罐子从女主头顶上方压过去，前腿靴子只擦过女主长发的外沿，女主的**脸在所有帧里都露着**（`truth_A_rearleg_cut.png`、`truth_A_hover_4frames.png`）。p=95 时罐子最低，从女主头右侧斜着过去，脸依然没被挡（`truth_D_p95_zoom.png`）。手机（黑色）在所有取样帧里都看得见。
- 罐子会不会捅进人：喷口与男生脸的最近距离，p=50 约 110px，p=95 约 120px（日志 m=(443,926)、tg=(534,1044)），**没有穿模**。
- p=5（女主被拖倒趴地、男生站着）：aim −0.30，雾打到男生脸，喷流反而最长、最好看（`truth_D_p5.png`）。
- p=95（男生被拖倒趴地）：aim 钉在 −0.800，雾照样命中男生脸，靠 miss 70 的判定窗口吃到（`truth_D_p95.png`）。
- pos=+20（卧室粉墙）/ pos=−20（电竞房暗色墙）：站位成立，青柠和深绿描边在两种底色上都看得见，雾命中脸（`truth_D_pos+20_-20.png`；aim −0.73 / −0.29）。
- 三人同时在场（B0+B1+T0，BestieGroup.summon×3）：三股喷流各走各的，没有打架（`truth_D_crowd.png`）。

**D1 三人同时在场时，她的前腿靴子盖住最远那个平衡车闺蜜的脸 — 次要**
- 复现：c4 1500ms，`truth_D_crowd_zoom.png` 左格：红比基尼那位的头正好在白色过膝靴后面。
- 建议：MIST.rows 最远那排（`[0.58,0.63]`）在她在场时不用，或者在 `Bestie.summon` 的 pickR 里避开 x<160 这一段。代价小，不急。

**D2 p=95 时瞄准角钉死在下限 — 次要**
- 复现：`p=95`，c7 日志 aim 全程 −0.800 / want −0.800（`truth_D_p95.png`）。
- 后果：整个人一动不动（只剩 bob），扫动没了；而且全靠 miss 窗口命中，男生再往右一点雾就会从他头上飞过去。
- 建议：`crew.js:575` `aim.lo` −0.8 → −0.95；或者 perch 跟着瞄点下移：`perch: () => [195, GROUND − HOVER + clamp((tgY−840)*0.5, 0, 90)]`。

---

## E. 正确性 —— 不合格

**合格的部分**
- 随机调度（不传 bestie）：第一次召唤 3000 次，平衡车 0 号 982 / 1 号 958 / 真相喷雾 1060，基本各 1/3，均匀（`tools/sched.py`）。
- 连续召唤 3 次：2000 次里 2000 次都是三个不同形象同时在场（B0,B1,T0）。
- 真相喷雾满员续时间：在场时再召唤，spray 2.8 → 5.6，人数仍是 1。live 实测被续到 8.4s（`truth_E_live_log.json`）。
- 离场后雾继续飞：c1 3700/3800ms，人已经出画，脸上的雾还在（`truth_C_exit_3000-3800.png`）。
- `startMatch` 会重置 Truth（`main.js:318`）；主循环、ammostrip、fxstrip 三处都调用了 Truth.update。

**E1 第 4 次召唤约 49% 会多出第 4 个人，而且形象重复 — 重要**
- 复现（统计）：连续召唤 4 次，2000 次里 {B0,B1,T0} 1029 次，**{B0,B1,B1,T0} 492 次、{B0,B0,B1,T0} 479 次**。
- 复现（真实对局）：`?live=1&liveA=0&liveB=0`，每 0.7s `giveGift(1,'boom')` 一次。2116ms 时场上是 `T0, B1, B1, B0`，**四个人、两个一模一样的粉平衡车条纹比基尼**（`truth_E_live_4onscreen.png`、`truth_E_live_log.json`）。直播里大哥连刷几个闺蜜，3.5 秒内刷满 4 个就会出现。
- 根因：平衡车闺蜜的形象从 3 个减到 2 个（`skins: [1, 2]`），但 `MIST.max` 还是 3（`crew.js:473`）。CrewGroup 在三个形象都占满以后，随机挑一个在场的成员去 `summon()`；挑中 Bestie 时，它 2<3 没满，于是**加人**而不是续时间，形象再从已经用过的两个里随机挑。
- 建议：`crew.js:473` 的 `max: 3` 改成 `max: 2`（等于它的形象数）。这样满员时 Bestie.summon 自己会去续时间，组合总人数封顶在 3，"同时在场各不相同"这条又成立了。顺带把 `crew.js:81` 注释里的"三个形象、最多三个人"改成按组来说。

**E2 离场途中被召唤：旧的那个瞬间消失，新的从头再进场 — 次要**
- 复现：`Truth.summon()`，推进到 bt=3.45（离场 0.1s，人还在画面里），再 `Truth.summon()` → peek 只剩一个 t=0 的新人（`tools/sched.py` 的 exitResummon 输出 `{oldT:3.45, now:[0]}`）。正式路径下，Truth 正在离场、平衡车形象又都在场时刷闺蜜就会走到这里。
- 根因：`crew.js:76` "全在离场：顶掉走得最远的"是给站地角色设计的（她们往画外溜，被顶掉也看不出来）；悬停的人离场前 0.2s 还在画面正中。
- 建议：TRUTH 离场中被召唤时把她"拉回来"：`b.spray = b.t - T.enter + T.spray`，让 t 仍然 ≤ se，hoverPose 会从当前高度继续悬停。或者离场中不顶掉，直接返回（这一件礼物就不出人了）。前者更好看。

**E3 `?bestie=2`（或任何越界下标）抛 TypeError — 次要，只影响诊断参数**
- `crew.js:341` `members[pick].summon()`，pick 越界时 members[pick] 是 undefined。建议 `members[Math.min(pick, members.length-1)]`，或者忽略越界值。

**控制台报错检查：无相关报错**
- 用 `--enable-logging=stderr --dump-dom` 跑了以下 5 条，抓 `CONSOLE|Uncaught|Error`，除 crewlog 外**0 行**：
  `live=1&liveGift=boom&liveAt=0.5&livet=1&liveSide=1` / `live=1&liveEvery=4&liveGA=boom&liveGB=mic&livet=40` / `live=1&liveGift=bestie&liveEvery=4&livet=20` /
  `ammostrip=12&ammoms=330&ammogift=bestie&buddyn=3&crewlog=1` / `ammostrip=12&ammoms=330&ammogift=bestie&bestie=1&p=95&crewlog=1`
  （抓取方法本身有效：同样的命令抓到了 crewlog 行，例如 `INFO:CONSOLE:2119] "crewlog t=0.63 aim=-0.413 want=-0.413 tg=628,841 m=538,784"`）
- Playwright 驱动的真实主循环跑了 12 组、累计约 40s（含 7 次 giveGift、4 人同屏），pageerror 为 0。唯一一条 console：
  `error: Failed to load resource: the server responded with a status of 404 (File not found)`，是 `/favicon.ico`（`curl` 返回 404，index.html 里没有 icon 声明），跟本次改动无关。
- 提醒：`liveGift=bestie` 是空操作。`giveGift` 查的是 SHOP 表的 key，闺蜜对应的是档 3 左的 `boom`，要验闺蜜得用 `liveGift=boom` / `liveGA=boom`。

---

## 范围外的发现（不影响本轮判据，没有展开）

1. `?live` 的预热循环（`main.js` 约 1920~1935 行）只推进 `battle / Ammo / Particles`，不推进 Buddy / Bestie / Truth / Rain。于是 `liveEvery` 在预热期间送出的档 3 礼物全部卡在 t=0 叠加：Truth 被连续续时间，平衡车闺蜜被叫满。这是改动前就有的问题，跟"预热里 hudTick 也要跟着快进"是同一类，要补的话在那一行加上 crew / rain 的 update。
2. 页面没有 favicon，每次加载 console 都有一条 404，会干扰"控制台零报错"的判断。加一行 `<link rel="icon" href="data:,">` 就能消掉。
