---
name: chashouji-web
description: 《查手机》网页版的代码结构与改法——文件分工、长卷世界与姿势贴图、参数表 P、状态 S、派生 FX、距离条 HUD、礼物表 GIFT、URL 诊断参数、部署命令。用于"改网页""加一件礼物""调数值""动作切换不对""背景卷得不对""手机位置不对""加个诊断参数""部署上去"这类请求。网页版是这个项目的单一真源，Godot 逐字对照搬。
---

# 《查手机》网页版

`/workspace/art/chashouji/web/`，部署在 **http://1.14.252.30:40235/index.html**。
**这里是单一真源**：所有数值和手感在这里调定，Godot 只做呈现。

## 开工前必须问清

1. **改的是数值还是结构？** 数值一律进 `P` 表或 `GIFT`/`RECIPE` 表，不要散落到
   函数里——用户会自己手动改参数，找不到就等于没有。
2. **改完要不要同步 Godot？** 默认**不同步**，等用户说"这个特效没问题"。
3. **怎么验证？** 见 `chashouji-verify`。改完至少 `node --check` 过一遍。

## 文件分工

```
index.html   画布 + 礼物按钮 + 调试面板 + script 引入顺序 + 说明文字
main.js      常量 / P / S / FX / derive / impact / RECIPE / GIFT / 各层绘制 / 主循环 / URL 分支
fx.js        Particles —— 粒子、屏幕震动、全屏闪、顿帧
ammo.js      Ammo —— 飞行物与弹道（色晕/拖尾/残影/本体）
bubble.js    Bubble —— 手机上方的聊天气泡
result.js    Result —— 结算画面（演出图 + 判词 + 台词 + 数据带），全屏接管
```

引入顺序 `fx → ammo → bubble → result → main`，改 index.html 时别打乱。

## 世界与贴图（v14，2026-09-24 起；此前是固定客厅 + 89 张每 1% 一帧）

```js
const W = 960, H = 1334, MID = 480;
const GROUND = 1195;          // 两个人的脚底线
```

素材全在 `web/assets/world/`，**由 `chashouji/v14/build.py` 生成，别手改**：

```
room0/1/2.webp   女生卧室 | 客厅 | 电竞房，高 1334，宽 2334/2229/2137（共 6700）
pose_*.webp      9 张抠好的姿势贴图，裁到外框
world.json       rooms 各宽 · center 客厅正中的世界 x（=0 米，3396）·
                 poses{名: w,h, ax,ay 锚点, phone 手机点}
```

- 世界坐标 → 屏幕：`wx = center − S.pos × P.pxPerM`，镜头 `camX = clamp(wx, 480, total−480)`，
  人物锚点在屏幕 `pairX = 480 + (wx − camX)`。走到世界边上镜头停、人往边上走。
- 贴图锚点 `(ax, ay)` 对到 `(pairX, GROUND)`。**僵持循环帧按脚那一截的质心对齐**
  （脚钉在地上，按全身对齐会让上身前后倾带着脚滑）；其余按**外框中点**（拖地姿势
  宽约 1000，按质心会让一侧出画 100 多像素）。
- **手机点是自动找的**（近黑连通块里挑"填充率高的横向长条"），每次 build 都会出
  `v14/preview/phone_check.jpg`，**必须看一眼再部署**。弹幕打它、气泡从它冒。
- 房间拼接：每张房间图接缝那侧都画了一扇被边缘切开的门，**一扇门取两张图各一半**，
  接缝落在门洞里。切点 `CUT_LIVING_L=75 / CUT_BOY_L=140` 是对着原图量的，换图重量。
- 弹幕发射高度带由 main.js 按 `GROUND` 传给 `Ammo.init({band})`，ammo.js 不写死几何。

## 三张表：改数值只改这里

**`P` —— 参数表**（表现手感）：`pxPerM=82` 米→世界像素（±30 米正好停在两头房间深处、
镜头不露边）/ `kneelAt=0.25` `fallAt=0.50` `lieAt=0.75` `hys=0.05` 选动作的门槛与回差 / `stageHold=0.6` 一次只走一档、每档至少停这么久。**两把尺取更狼狈的**：拉力 |S.p−50|/50 与距离 |S.pos|/END；被拖远的一方在往回拽（拉力反号且 ≥kneelAt）时只看拉力。只看拉力时 2:1 对刷 94 秒全是僵持（人站着被平移 30 米），这是加距离尺的原因；`LINE_FULL` 试过 2000 同样太钝，保持 1000/
`loopFps=8` 僵持循环格速 / `bobHz` `bobPx` 单张动作的颠步（**占位**，循环帧画出来就删）/
`hitK` `hitDamp` 角色被推开的弹力与阻尼 / `tintDecay` 染色衰减。**受击不缩放人**（2026-09-26 删了 punch：胀一下再缩回读成"人变小"，用户要求大小不变、只留闪色）。

**`GIFT` —— 礼物表**（加/改礼物只动这张）：

```js
hairpin: { from:+1, style:'volley', item:'hairpin', r:22, n:8, power:1, recipe:'star',    push:1   }
pillow:  { from:+1, style:'single', item:'pillow',  r:56,      power:2, recipe:'feather', push:20  }
bouquet: { from:+1, style:'heavy',  item:'bouquet', r:76,      power:3, recipe:'petal',   push:230 }
ringbox: { from:+1, style:'heavy',  item:'ringbox', r:64,      power:4, recipe:'bloom',   push:600 }
seed:    { from:-1, style:'volley', item:'seed',    r:21, n:8, power:1, recipe:'star',    push:1   }
gamepad: { from:-1, style:'single', item:'gamepad', r:52,      power:2, recipe:'debris',  push:20  }
milktea: { from:-1, style:'heavy',  item:'milktea', r:72,      power:3, recipe:'splash',  push:230 }
photo:   { from:-1, style:'heavy',  item:'photo',   r:68,      power:4, recipe:'memory',  push:600 }
```

`from`：+1 查岗党（左）/ -1 灭迹党（右）。三种 `style` 的速度在 `ammo.js` 的
`SPEED = { volley:1400, single:900, heavy:850 }`。档 4 另外由 `exec` 把 `r` 乘 1.8、
速度减半——它买的是一段没人打断的时间，飞快就把这段时间还回去了。

`quilt` / `box`（棉被、外卖箱）留在 `ammo.js` 的 `ITEM`/`SILH` 里作**备选池**，
当前未启用；换回档 3 只需改 `ITEM_OF` 一行。弃用原因：两件剪影只差 1.03 倍。

**`RECIPE` —— 特效配方表**：`thud` / `feather` / `star` / `debris` /
`petal` / `splash` / `bloom` / `memory` 八种，礼物只引用配方名，不各写各的。

**同档两件的剪影长宽比至少要差 1.4 倍。** 飞在半空观众只看得到纯色剪影（`SILH` 层），
形状太像就会出现"屏幕上在对撞，但我不知道谁占上风"。挑物品时先算这个比值。

加一件新礼物要动的全部地方：`GIFT` 一行 + `ammo.js` 的 `ITEM`/`SILH`/`AURA`/`TAIL`
各一行 + `index.html` 一个按钮。**引擎本体一行都不该改。**
换某一档飞什么东西：只改 `main.js` 的 `ITEM_OF` 一行，数值表 `SHOP` 一个字都不用动。

## 状态与派生：渲染只读不写

```js
const S = { p: 50, pos: 0, vel: 0, fA: 0, fB: 0, t: 0, auto: false, ... };
// pos 是胜负真源（米，正 = 往左拖进女生卧室）；vel 是 battle 顺手写出的读数（米/秒，带符号）
const FX = { pose, poseT, frame, camX, pairX, bob, phoneX, phoneY, struggle,
             hitX, hitV, tint, tintA };   // 全部由 derive(dt) 算出
```

**三个数，别混**（2026-09-24 起）：
- `S.pos` **胜负真源**。拉力差每秒把两个人往拉力大的一边拖，到 ±`NUM.END`（30 米）赢。
  它是**积分量**但能拖回来 —— 对面追上来拉力差反号，背景倒着卷。
- `S.p`（0~100）**拉力差的当前读数**，只管**摆哪套动作**（`pickPose`）。不积分。
- `S.vel` 读数：HUD 的方向箭头、头像被拖脉动、颠步开不开都读它。
  **颠步必须看 vel**：速度为 0（抓门框顶住、调试台刚过门槛）时背景不卷，人还在颠就是滑冰。

动作七档：`n` 僵持（8 格循环 `LOOP_N`，5 张来回用）/ `aK` `aF` `aL` 查岗党占优、男方
跪·扑倒·趴 / `bK` `bF` `bL` 反之（`pickPose` 按 `STAGES='KFL'` 逐档比门槛）。
**步态**：被拉倒六档（aK aF aL bK bF bL）都有 `WORLD.gaits[pose] = {frames: [8 张], cycle: 像素}`，相位 `FX.gaitPh += vel·朝向·dt·pxPerM·P.gaitSlip / gait.cycle`（按位移不按时间：背景不动脚不动，拽回来倒着播）。`cycle` 是 build.py 按原图两脚间距量的步幅×2（400~650），`gaitSlip=1` 时站地的脚跟地板同速、不打滑；以前固定 `gaitCycle=100`，步频是地板的五倍，读成"冰上倒腾"。`?gaitstrip=aK` 摊开看（窗口要 3600×760 才装得下八格）。僵持档 n 挪动时还没有步态。
**人物大小**：被拉倒各档是各自生图的，扑倒/趴画小了 5~9%，build.py 用赢方的头做多尺度匹配（`head_scale`，框对着 pose_n0 量）逐档补缩放；用户看到的症状是"被礼物砸中后人物变小很长时间"（掉进这几档又因回差停很久）。

**空闲拉锯（`P.sway` / `FX.pDraw` / `FX.busy`）和对抗线形变（`rowOff/rowImp/frontAt(y)`）
已随 v14 删除**：前者是为了"僵在同一帧"加的，现在僵持本身就是循环；后者画在地毯上，
地毯会被卷走。

**镜头远近 `ZOOM`（2026-09-25 起 = 2/3）**：用户嫌人太大，要"人变成现在的 2/3"，选了"整个镜头拉远"
（人和房间一起缩，不只缩人 —— 只缩人沙发会比人大一圈）。build.py `SCALE = 0.66×2/3 = 0.44`，房间改用
`v14/bg/*_ext.png`（原图上补画 424 行墙到天花板顶角线、下补 49 行地板，宽度不变故 CUT_* 不变）。
main.js 里"跟人一样大"的像素数都写成原值 × ZOOM：`pxPerM`（82→54.7，世界 6700→4470 宽，±30 米仍停在两头房间深处）、
弹幕高度带 band、挨打推开的 hitV。改镜头只动 ZOOM + build.py 的 SCALE 两处并重跑 build。
礼物/粒子尺寸**没缩**（用户只说了人），现在相对人偏大，待用户定。

**礼物命中 = 碰到挨打那个人的轮廓**（2026-09-25 用户定）：`frontAt(y, from)` 返回挨打那个人在这个高度上
朝这边的轮廓 x（from=+1 打男生，-1 打女生；路过自己那方的人不算）。轮廓由 build.py `edges()` 按行量好存在
`poses[帧].edge = {step, a: 女生右沿, b: 男生左沿}`（-1 = 这行没人）；分人按连通块（先挖掉手机周围），
不按手机竖线一刀切 —— 男生跪/扑时前脚会伸过手机线。运行时叠 pairX/hitX/bob。
这一行没人就找上下 80px 内最近的一行，再没有返回 null、那发飞出画面；`targetSpan(from)` 在**出手那一刻**
把高度压进对方身体范围（对方趴下时不会从头顶飞过）。对冲的仍在 `midAt()`（手机 x）前撞掉。
验证：`?ammostrip=10&ammoms=150&ammogift=pillow&ammoy=640`（头）/ `ammoy=1010`（腿），加 `p=95` 看趴档。

## HUD：距离条一根 + 名字行 + 拉力牌

```js
const UI = { avR:30, avCX:44, avCY:35, barX:18, barY:68, barH:44, clkCY:33, pwCY:158, sk:12 };
const HUD = { avA, avB, lfA, lfB, pfA, pfB, mf, pm, t, pin };
```

- **距离条是一根，不是左右两条**：位置是一个数，劈两条读起来像各有一份血（那是旧模型）。
  横向顶满 18~942，`barAt(m)` 把米换成 x（正往左）。
- 条上按三间房铺淡底色 = **小地图**，门的米数由 `world.json` 现算。从正中到手机图标
  涂领先方颜色（四段渐变 + 高光 + 底暗，血条时代定的"管"形制）。
- 填充里一串箭头朝拖的方向流，流速跟 `S.vel` —— 条长答"拖了多远"，箭头答"还在拖吗"。
- **手机图标**当滑块：每跨过一整米亮一下（`HUD.mf`，按整点跨越判，衰减 7/秒 ——
  按"在动就亮"判会常亮）。离终点剩不到 25% 时那一端透红呼吸。
- 名字行：队名 + **这一方拽过来的米数**（对面领先时是 0.0m —— 哪边的数在跳哪边在赢）。
- 时钟牌跨在名字行正中，旁边写 `◀ 1.5米/秒` / `僵 持`。拉力牌在条下方，没改。

沿用下来的四条规矩（都踩过）：
- **数字不能放进条里** —— 填充末端迟早扫过整条，条里没有安全位置。
- **排竖向要连描边一起算**（lineWidth 5 往外扩 2.5px）。
- **时钟牌按内容伸缩，拉力牌写死 660 宽**（数字宽窄变牌子会抖，读成卡顿）。
- **`liveFreeze` 连阶段和计时器一起冻**（现在冻 `p/pos/vel/clock/phase/big/sudden/stand/winner`）。
  只冻位置的话绝杀累计照走，截一张图能等出个"查岗党胜"来。

## 帧率无关插值（三个项目里各踩过一次）

```js
const approach = (dt, k) => 1 - Math.exp(-k * dt);
```
**绝对不要写 `Math.min(1, dt*k)`**——它让节奏随帧率漂移，而低帧率测试机会掩盖
高帧率才暴露的缺陷。`proto/index.html` 里还剩两处没改，是已知待办。

## 渲染分层

```
renderBg      drawWorld：只画镜头里那一两间房（背景不震）
renderActors  PoseView.draw(FX.frame) 按锚点贴 + 缩放脉冲 + 染色（跟着震）
renderFx      气泡 → 弹幕 → 粒子 → HUD（结算时换成 Result.draw）→ 全屏闪
```

**拆成三段是为了能分层计时**（`?bench` 靠它分账），合在一个函数里只能猜哪层慢。

气泡在弹幕**之下**：它贴在后面那堵墙上，弹幕是前景。

## 结算画面（`result.js`，全屏接管不是弹窗）

`S.phase === 'over'` 时 `renderFx` 里 **`Result.draw` 顶掉 `drawHUD`** —— 结算把整屏
接管，血条队名全撤。它存在的理由是**情绪展示**：赢家的戏、输家的脸、一句台词。
不是"显示比分"，数据只配当底下那条带子。

版式四段（960×1334）：判词 `0~210` / 台词气泡 `214~390` / 演出区 `390~1040` /
数据带 `1058~1300`。演出图是**底图**，铺满全屏，UI 压在它上面。

```
assets/ui/win_a1.webp  查岗党胜·蓄力（女生举枕头）      960×1334
assets/ui/win_a2.webp  查岗党胜·命中（砸下去）
assets/ui/win_b1.webp  灭迹党胜·蓄力（手机举胸前）
assets/ui/win_b2.webp  灭迹党胜·命中（怼到她面前）
```

- **两帧硬切，间隔不能等长**。蓄力 `HOLD=0.45` / 命中 `HIT=0.18`。等频（试过 0.22/0.22）
  读成机械闪烁，不像人在打——抡东西本来就是举起来慢、砸下去快。这个节奏还顺带压住了
  生成帧之间的人物位移：两张图里连跪着不动的人也会挪几十 px，等频快切会把它放大成
  "人在左右跳"，慢蓄力+快命中则读成"扑上去"。
- **命中那 0.18 秒整幅下震 6px，只震演出图不震 UI**。字跟着抖就读不下去了。
  震屏下移会让顶边露出底下没被盖住的东西 → `drawImage(im, -8, sh-8, W+16, H+16)`，
  四边各留 8px 余量。
- **生图必须先按界面画幅构图，不能生完再裁**。第一批生的方图/9:16 裁进 0.72:1 时
  人物被推到下半屏，数据卡直接盖在两张脸上——情绪展示的主体被 UI 埋了。提示词里
  写死"上五分之一留墙、下四分之一留地板、人物在正中偏下占一半高"才落得对。
  挑图也要**裁到 960×1334 之后再挑**。
- **背景对齐 ≠ 人物对齐**。量第二帧与第一帧的背景 MAE（上墙/地板都 <5）说明镜头没动，
  但人物仍会漂。要按质心单独量人物（粉色睡衣 / 暗色头发 / 手机亮屏各算一个）。
- **台词气泡的尾巴要按每套素材单调，不能镜像套用**。A 案女生在左下，尾巴朝左下；
  B 案照镜像出来的长尾巴尖端正好戳在男生举着的手机屏上，读成手机在说话——缩到刚
  探出气泡、从手机顶边上方过去。尾巴本来也不必够到嘴，拉长只会变成一大块白三角。
- **`▸`（U+25B8）在 Noto Sans CJK 里是空码位**，渲染成豆腐块。倒计时那个箭头是
  `beginPath` 画的三角。
- **贴纸描边的 lineWidth 是居中的**（一半描在字外），PIL 的 `stroke_width` 是全外。
  离线试版定的 27/17/9 搬到 canvas 要写 **54/34/18**。
- **战斗画面是写实的、结算是 Q 版**，中间靠 `0~0.18s` 的白闪 + 硬切转场掩盖。
  白闪那 0.18 秒底下仍是战斗画面，别在这段提前画结算。

两条流程上的规矩（都踩过）：

- **`derive` 不做流程控制**。把"到点开下一局"写进 `derive` 一定出事：`?live` 的预热
  是靠反复调 `derive(1/30)` 快进的，预热跑到结算就会在循环内部把这一局重置掉。
  开新局属于对局流程，放在主循环 `frame()` 里：
  `if (S.phase === 'over' && Result.pin < 0 && S.overT >= Result.NEXT) startMatch()`。
  `derive` 里只推进 `S.overT`。
- **`over` 之后必须停掉注入和送礼**，预热循环和主循环两条路径都要加 `if (S.phase !== 'over')`。
  漏了就会截出"本局时长 0:26 / 礼物 12:12 / 拉力 5747"这种自相矛盾的面板——
  局在 26 秒打完，后面 44 秒的注入还在往一个已经结束的局里加。

`S.board` 是送礼榜，形如 `[{name, side, amt}]` 按 amt 倒序，**网页版恒为空**，
接直播时由外部填。空的时候面板自己写"接入直播后显示前三名"——**不造假数据**。
榜只能横排三格（竖排三行在 1334 高里装不下，第三行顶到底边），代价是昵称按格宽截断。


## URL 诊断参数（全表）

| 参数 | 作用 |
|---|---|
| `?p=<0-100>` | 强制姿态读数（只在 idle 下有效）。idle 下位置按同一把尺子从 p 积分，拖滑块背景也会卷 |
| `?pos=<米>` | 直接把两个人摆到某个位置（正 = 进女生卧室），截各房间用 |
| `?auto=1` | **打开**自动演示（默认已关） |
| `?x=` `?m=` `?vz=` `?end=` `?linefull=` | 就地改 X / M / V_Z、终点米数、姿态满幅刻度 |
| `?hudflash=0..1` | 钉住拉力数字的注入闪光。它只亮半秒，不钉住截图永远抓不到 |
| `?zoom=1` | 画布按原始宽度显示（截图用） |
| `?strip=1` | 七种动作 × 各自该在的房间并排：动作/背景/距离条/手机位置一次对 |
| `?loopstrip=1` | 僵持循环 8 格按播放顺序并排，每格标手机 x |
| `?fxstrip=N&fxms=M&fxpower=1..3&fxrecipe=thud\|feather\|star\|debris` | 粒子配方胶片 |
| `?ammostrip=N&ammoms=M&ammogift=<礼物名>&ammoy=<高度>` | 弹道胶片 |
| `?bubblestrip=N&bubblems=M` | 气泡胶片，四种消息轮流强制推 |
| `?bench=1&benchframes=N&benchrate=M` | 连点压测 |
| `?benchoff=ammo\|part\|both` | 关掉某层做差值分账 |

**新加诊断模式时照这个套路**：每格强制指定内容，不要碰运气等随机——
气泡按一两秒随机冒，混在别的胶片里拍不到语音条和撤回提示。

**钉住类参数（`?hudflash`）要在 URL 解析处当场把值写进状态**，不能
只设 `pin` 等每帧的 tick 去写：`?liveStop` 把主循环停在 `render(); return`，
`hudTick` 一次都不会跑，只设 pin 截出来永远是"没闪光"的那一帧。踩过一次。

**`?live` 的预热循环里，表现层的 tick 也要跟着快进**（`hudTick(1/30)` 和
`derive(1/30)` 并排）。漏掉的话预热结束那一帧的 HUD 永远是"刚开局、什么都
没闪过"的样子，`livet` 微调也扫不到闪光 —— 而 `livet` 每 0.05 秒扫一格正是
验证短动效真的在跑的办法（量一块填充区的通道均值，比肉眼可靠）。

## 数值层（三层模型；2026-09-24 胜负层从血量换成位置）

**礼物既不直接拖人也不直接换动作。** 礼物注入拉力，只有**拉力差**起作用：

```js
FA += push;                                 // 礼物注入拉力（giveGift）
const burn = NUM.BURN * Math.min(FA, FB);   // 对冲，由拉力少的一方定速
FA -= (burn + NUM.LOSS * FA) * dt;          // FB 同
const diff = FA - FB;

// 姿态读数：拉力差的当前值，不积分 → 选动作
S.p += (50 + 50 * clamp(diff / NUM.LINE_FULL, -1, 1) - S.p) * approach(dt, NUM.LINE_RATE);

// 胜负层：差过了死区 X，每 M 点差每秒拖 V_Z 米，封顶 V_MAX；到 ±END 赢
if (Math.abs(diff) > NUM.PULL_X) {
  const v = Math.min(NUM.V_MAX, Math.abs(diff) / NUM.PULL_M * NUM.V_Z);
  S.pos += Math.sign(diff) * v * dt;
}
```

`X = 30 / M = 1000 / V_Z = 1.5 / V_MAX = 3 / END = 30`。V_Z 与 V_MAX 是从血量制
**原样换算**的（旧 Z=5%/秒、HP_MAX=10%/秒 × END），所以局长没变：`?sim` 实测
单边猛刷 23:0 → 0:57、2:1 对刷 → 1:36（左右对称）。**Z 的 5% 不是《螂人杀》文档里的**
（文档没写速率），取自需求例子"差 1000 每秒扣 5%"，别再去翻文档找它。

**`BURN / LOSS / V_Z` 是同一根时间轴上的刻度，改一个必须三个一起按同样倍数改。**
- **兑现速度** = `1/LOSS`（时间常数 25 秒）。三个一起乘 k 平衡不动，只有快慢变。
- **局长** = `V_Z / LOSS`。想拉长对局就等比调小 `V_Z` 与 `V_MAX`（`?vz=` 现场试）。

绝杀 / 反击 / 抓门框三条都从"血量"换成了"位置占 END 的比例"：
`SUDDEN_LEAD=0.35`（被拖出 35% 持续 60 秒进绝杀）/ `STAND_AT=0.08` / `SHIELD_AT=0.10`。
时间到：被拖向谁那边谁赢，离正中不到 1 米判平。

`battle(dt)` 算 `S.pos` 与 `S.p`，`derive(dt)` 由它们算画面。idle 下 `battle` 不跑，
主循环改调 `drift(dt)`：位置按同一把尺子从滑块给的 `S.p` 积分。

四条不能动的规矩：
- `onHit` 只演出、**不拖人**。让命中再推一次等于同一份力算两遍。
- **抓门框只能按比例减速，不能扣拉力存量**（扣存量 → 对冲变弱 → 差值反而扩大的正反馈，
  血量制时实测净差冲到理论值 2.4 倍）。
- **拖动速度要有上限**（`V_MAX`）。极端投入下差值能到四万，不封顶就是一眨眼到头。
- **别拿 `S.p` 判胜负**：它是瞬时读数，一件空投④就能把人拽倒一下。

礼物是**两张表**：`SHOP`（九件平台礼物，管数值）× `GIFT`（八件物品，管表现），
用 `tier` 和 `ITEM_OF` 连接。加礼物改 `SHOP` 一行。
物品方案是**档 1~2 客厅现场 + 档 3~4 甜蜜反击**（发卡瓜子/抱枕手柄 → 玫瑰奶茶 →
戒指盒相框），依据与备选池见 `docs/礼物设计.md`。

## 新增诊断参数

| 参数 | 作用 |
|---|---|
| `?sim=1&simA=&simB=&simT=` | 纯数值快进，不渲染。两秒跑完一局，调参不用看画面 |
| `?live=1&liveA=&liveB=&livet=` | 真实对局，按给定注入率快进到指定秒数 |
| `&liveGift=drop&liveAt=&liveSide=` | 指定时刻送一件礼物 |
| `&liveFreeze=1` | 冻住**整个战况**（姿态/位置/阶段/三个计时器），拉力与弹幕照跑 |
| `&liveStop=1` | 冻住整个世界（截处决这种只存在零点几秒的东西） |
| `&liveEvery=<秒>&liveGA=&liveGB=` | 每隔几秒给两边各送一件，用来把礼物数堆到能看的量 |
| `?overt=<秒>` | **结算定帧**：把 `S.overT` 钉死在指定秒。入场动画和两帧循环都读它，不钉住截不到 |
| `&v=<任意值>` | 绕过 js 的磁盘缓存，见 chashouji-verify |

## 部署

```bash
for f in main ammo fx bubble result; do node --check $f.js; done
timeout 100 scp -q main.js fx.js ammo.js bubble.js result.js index.html kf-deployment:/home/op/chashouji/web/
# 素材有变时（v14/build.py 重跑过）：
timeout 150 scp -q assets/world/* kf-deployment:/home/op/chashouji/web/assets/world/
```
⚠️ `scp -r assets/world kf-deployment:.../web/` 会落到 `web/world` 而不是 `web/assets/world`（踩过），
按上面那样拷**文件**到已存在的目录。
桌面容器上 `python3 -m http.server 40235` 常驻在 `/home/op/chashouji/web`。

## 改完别忘

- `index.html` 底部那段**说明文字要跟着改**——它是给用户看的，代码改了文字没改
  就是错的（已发生过：改成按距离回溯 16 帧后，说明里还写着"记了八帧轨迹"）。


## 画布 960×1707（2026-09-26，最终 1080×1920 竖屏）
- `main.js` `H = 1707`，`build.py` `H = 1707`。玩法版式（HUD、`GROUND=1195`、礼物弹道、结算 UI 卡片 1058~1300）仍按原 960×1334 排，
  **1334 以下 373px 是背景往下补画的地板**（`v14/bg/*_ext.png` 高 1818，补画过程在 `v14/bg/ext2/`），直播时被平台评论区盖着。
- `index.html`：舞台按窗口高度放满（9:16），调试面板 `.panel` 挪进 `#stage`、`top:78.2%` 叠在补出的地板上，字号用 `cqw` 随舞台缩放。
  strip 类诊断会 `stage.innerHTML=''`，面板随之消失，不影响截图。
- 结算图 `assets/ui/win_*.webp` 也是 960×1707（上面 1334 构图不变，下面是地板）；头像 `av_*.webp` 从新 `loop/n0.png` 裁。
- 看结算：`?live=1&liveA=200&liveB=0&livet=120&overt=3`（灭迹党胜把 A/B 对调）。

## 瞄部位的档 1：香蕉 / 口红（2026-09-26，替换瓜子 / 发卡）
- `GIFT.banana`（灭迹党）：`r:40, n:3, gap:0.5, aim:'face', stain:true, recipe:'cream'`（白爆点 + 女生脸上白点）。
- `GIFT.lipstick`（查岗党）：`r:28, n:3, gap:0.5, aim:'hip', stain:true, recipe:'rouge'`（粉爆点 + 男生短裤上粉点），淡红管身。
- **碰撞点是部位，不是外轮廓**：ammo.js 出手时 `p.aimKey = Math.random()`，每帧 `aimAt(g, key)` 重取 [碰撞 x, y]，
  高度按 `1-exp(-12dt)` 追过去、x 到了就爆（人倒下/迈步部位跟着挪）。没有 aimKey 的照旧走 `frontAt`。
- main.js `aimAt`：face = 脸朝对方那半边（`f[0] - from*0.5r`）、上下 ±0.2r；hip = `hipOf().pts` 第 key 行的左沿 +5。
- 留点 `stainAt(part, x, y)`：只有瞄准命中（aimKey）才留；存部位归一化坐标（脸：以脸半径为单位；短裤：外框 0~1），
  每部位最多 14 个、9 秒、`STAIN_LOOK` 管颜色。
- 常规火力（emitFire）左飞口红、右飞香蕉，走 `one` → `free`：不瞄、不留点。
- 部位数据：build.py `head_find` → `face:{a,b}:[x,y,r]`（步态帧沿用 base）；`hip_find` → `hip:{box,pts}`，按**藏青色相**抠男生短裤，
  每张图（含步态格）各量一次，pts 是 9 行 `[左沿, y, 右沿]`。换男生裤子颜色必须改 hip_find 的色阈。
- 看效果：`?ammostrip=6&ammoms=260&ammogift=lipstick&ammoy=aim`（`ammoy=aim` 不钉高度，走真实瞄准）。
- 贴图 `tools/3d/banana.py` / `lipstick.py`：lean=20；**view_transform=Standard**（AgX 把黄压成芥末、把淡红压成豆沙粉）。
  发卡、瓜子的贴图和矢量画法仍留在 ammo.js 当备选。

## 哥们（2026-09-26 替换奶茶，灭迹党档 3）
- `GIFT.buddy`：`style:'buddy'` → giveGift / ammostrip 走 `Buddy.summon()`（buddy.js），不走 Ammo。奶茶那行留作备选。
- buddy.js：角色层画人（男生**之前**画，被挡住），特效层画水柱。每人 `T` 滑进 0.55 → 滋 2.5 → 溜出 0.5；同时最多 `MAX=3` 个，满了再刷 = 给剩余时间最短的那个 `spray += T.spray`。
- 立绘两层 `assets/world/buddy_up.webp`（头躯干双臂水枪）/`buddy_lo.webp`（裤腿滑板）：`v14/buddy/make.py`（skate1.png 踩滑板，×0.37）在裤腰 `CUT=186` 切开、肚皮往下补 `BELLY` 行，打印 `SPR.foot/muzzle/pivot`。上半身绕 pivot（裤腰正中）转，下层后画压住接缝。滑板替掉走路动作。
- 站位**按枪口排**：`sprayZone()`=[枪口最左 min(phoneX+100, W-420), 人右沿最多 W+90]，横向 r 随机；远近分 `ROWS` 三排（每人占一排，远排小、高 LIFT 140）—— 横向只剩 ~140 像素，靠远近把几股水的起点上下错开，否则从同一点分叉读成"7"字。
- **由落点反推枪**：瞄点平滑跟随（`AIM.follow`，步态硬切帧会抖）→ 按固定 `V=1250` 反解仰角（与枪口位置互相依赖，迭代 6 次）→ 上半身按 `AIM.rate` 转过去、夹在 `AIM.lo~hi`；水**永远沿枪管以 V 射出**（每滴反解初速试过：前后两滴速度差大，水柱成锯齿）。打偏：离落点 `MISS` 内算中，否则碰 `girlFront`（轮廓、跳过手机那行 `BUDDY_ARM_GAP`）溅开。
- **女生倒地**（`girlDown()` = 帧名 bF/bL 开头）：`girlTarget` 沿身体从头到脚取上沿上的点（`girlTop(x)` 查 world.json `edge.top`，build.py 按列量的女生上沿），返回第三项 `'top'`；buddy.js 每人每 `ZONE.every` 秒随机挑一个部位（u∈`ZONE.lo~hi`，背/屁股/腿）小幅扫；碰撞按"落到这一列上沿以下"，**不看前沿**（横躺时每行前沿都是手臂和头，浇背的水会全碎在头上）。落空的水在地板上溅开。扫动 `SWEEP=[1.2,2.8]` rad/s —— 快了（2.3/5.3）前后水滴落点差太远折成"7"。瞄点 u 从脸到大腿上段（`sp[1]-0.35h`）。水柱线宽 `STROKE` 26/19/6。连线按人找上一滴（几个人的水滴在 drops 里交错）。
- 看效果：`?ammostrip=6&ammoms=450&ammogift=buddy&buddyn=3`（buddyn 一次叫几个；可加 `pos=-29` 看女生趴地）。
