/* trio_fx.js —— 三人组攻击特效：烘焙贴图 + sprite 粒子（2026-10-01，美术打磨自检 P4 / P5 / P8）
 *
 * 把"canvas 平涂线条"换成游戏级效果：光束是多层贴图条（外晕 / 光身 / 中层 / 芯，噪声沿长度滚动）+ 出口四角星 +
 * 沿途甩光粒 + 末端溅开的冲击波；命中是统一的三层配方（瞬闪 → 主体碎片 → 余烬），碎片是带高光和描边的 sprite；
 * 落地 / 滑行有尘土。贴图由 tools/fx_bake.py 离线烘焙进 assets/fx/trio/，运行时按调色板映射一次（ramp），之后只 drawImage。
 *
 * 配色规矩跟 fx.js 一样，是这张明亮客厅底图逼出来的（skill chashouji-fx）：lighter 在亮底上加不出来，所以这里**全部普通混合**，
 * 发光靠色带"白芯 → 饱和本色 → 暗一档的边"自己撑对比，实体碎片一律带暗描边。贴图存的是色带位置 v（灰度）而不是颜色，
 * 同一张水滴能出水 / 焦糖 / 西瓜汁，同一条光束能出悟空的蓝和排山倒海的橙。
 *
 * ======================================================================================================================
 * 接口（引擎接入点）。全部坐标是画布坐标（960×1707），角度是弧度、y 朝下（Math.atan2(dy, dx) 那一套）。
 * ======================================================================================================================
 *
 * 0. 加载与每帧驱动（main.js）
 *      boot：    await TrioFX.load(ver)            // 与 Particles.loadShapes 并列；ver 同 ?v=，返回 Promise<boolean>（缺素材 false，不抛）
 *      update：  TrioFX.update(dt)                  // 用 Particles.tick(dt) 之后的 dt —— 顿帧冻住时粒子一起冻
 *      renderFx：TrioFX.draw(ctx)                   // 紧跟 Particles.draw(ctx) 之后（同一层：弹幕 → 粒子 → HUD）
 *      clear：   TrioFX.clear()                     // 跟 Particles.clear() 一起（重开一局）
 *
 * 1. 命中配方（main.js RECIPE / trio.js TRIO_RECIPE）
 *      TrioFX.RECIPE 的每一项和旧 RECIPE 同签名：{ tint, burst(x, y, side, s), drip?(x, y, side) }，impact() 不用改。
 *      接法：Object.assign(RECIPE, TrioFX.RECIPE) 放在 Object.assign(RECIPE, TRIO_RECIPE) 之后（同名覆盖旧的）；
 *      只想先换三人组：三人组 cfg.recipe 改写成 'fx_' 前缀另挂一份也行 —— 名字表见 TrioFX.RECIPE 的 key：
 *        thud star splash feather melon slash petal debris hollow water ball rouge（12 种，tint 与旧配方逐字一致）；之后加的 pepper jab 等同理
 *      每项还带 layers: { flash, body, ember } 三个函数，可单独调某一层（比如 drip 只放余烬）。
 *      side / s 语义同 impact：side +1 打向左（女方），-1 打向右；s 0.55 / 1.0 / 1.7 / 2.8。尺寸内部按 min(s, 1.8) 封顶
 *      （skill：密度靠数量不靠单颗更大），数量按 s 线性。
 *
 * 2. 光束（trio.js stepBeam / beamTick / drawBeam / orb，B19 B22 G23 G30）
 *      const fx = TrioFX.beam(A.beam)               // 每个角色一次（建 Act 时），A.beam 原样传：读 glow / edge / layers / ball
 *      蓄力（stepBeam 'charge' 分支 / 帧序列蓄力帧）：fx.charge(dt, x, y, r)    // (x, y) = holdPt(P)，r = 原 drawBeam 算的球半径
 *      开轰（'fire' 分支，每个逻辑帧）：  fx.fire(dt, from, dir, to, e, k)
 *          from  出口点 handPt(P)
 *          dir   出口方向（弧度）—— **光束第一段的切线 = dir**。引擎负责人那边 P1 做出口方向：出手帧的 nozzle / hold 第三项
 *                给出手臂指向，传进来即可；传 null 表示还没有出口方向，退回直线 from → to（等于现在的画法）。
 *                dir 与 from→to 不一致时光束走二次贝塞尔：控制点 = from + dir × 0.42·|to − from|，所以出手那一段沿手臂出去、
 *                再弯到落点。（后排出手要翻过主角头顶的那条 over() 路径：把 over() 的控制点方向当 dir 传即可，同一条曲线。）
 *          to    落点 o.aim(S.u)
 *          e     光头伸出去多少 0..1 = min(1, S.t / beamReach())（与 beamTick 判打中用同一个数，伸到 1 那一刻打中）
 *          k     收束 0..1 = min(1, (B.fire − S.t) / 0.15)
 *      歇（'rest'）：fx.rest()                       // 不画；已经甩出去的光粒照常飞完
 *      画：fx.draw(ctx)                               // 放在 drawOver 里原 drawBeam(ctx) 的位置
 *      末端溅开（冲击波 + 反溅火花）由 fx 自己在 e ≥ 1 时持续放；beamTick 每 drip 秒的 onSplash 照旧（那是配方的 drip）。
 *
 * 3. 斩痕（trio.js drawSlash，B23 G?）
 *      shots 里 'slash' 那一项开始划（s.t 从 < 0 跨到 ≥ 0、s.p 有了）的那一帧调一次：
 *        TrioFX.slash(s.p[0], s.p[1], s.ang, A.slash.len, A.slash.color, A.slash.life)
 *      之后 drawShot 里 'slash' 分支不再画（刀光序列帧在 TrioFX 的粒子池里，自己播完）。
 *
 * 4. 尘土（P8，main.js / trio.js 进场）
 *      落地：enter seq 里标 'land' 的那一刻：TrioFX.land(x, y, s)          // (x, y) 脚下接地点；s 体型（P.s，默认 1）
 *      滑行 / 冲刺 / 骑：在场这段每个逻辑帧：TrioFX.skid(st, x, y, vx, dt, s)  // st = 调用方自己持有的一个对象（b 就行，
 *                        TrioFX 在上面记累加器 st._fxSkid）；vx 接触点水平速度（px/s，正 = 往右），|vx| < 40 不出尘
 *      拖痕沿用 main.js 的 Scuff。
 *
 * 性能：贴图 6 张 + atlas.json 共 70 KB，load 一次；ramp（灰度 → 调色板）每种 (贴图格, 调色板) 只算一次进 rampCache；运行时每颗粒子
 *      一次 drawImage（圆团不转，走快路径），光束每层每段一次 fillRect（直线 1 段，弯的 24 段，4 层）。池上限 MAX = 900，满了回收最老的。
 *      实测（fx_lab.html ?bench=1，桌面容器 GUI Chrome + SwiftShader 软渲染，600 帧；负载 = 同屏 6 人 + 主角：两道光束 B22 + G23
 *      轮流蓄 / 轰、每 0.25 s 一次首击级命中（s 1.7，12 配方轮换）、每 0.1 s 一次 water.drip、两条 600 px/s 的滑行尘）：
 *        只算特效（生成 + 更新 + 绘制，不含底图）   旧 均 8.2 ms / p95 12.8      新 均 13.2 ms / p95 20.2，粒子 均 263 峰 378
 *        差值分账：新·不画光束 9.2 ms → 两道光束 ≈ 4.0 ms；新·都不画 0.08 ms（生成 + 更新几乎不花钱，钱全在填像素）
 *        对等比（去掉旧版没有的滑行尘 &benchskid=0）：新·只画粒子 8.5 ms ≈ 旧·粒子 + 平涂光束 8.1 ms
 *      软渲染下绝对值偏大、填充率是瓶颈（skill chashouji-verify：这台机器绝对帧时间不可信，相对比可信）；手机 GPU 上 drawImage
 *      ~260 次 / 帧不是负担。真机帧时间未测。
 *
 * ======================================================================================================================
 * 精特1b：去规则（2026-10-01 用户："光束圈太规范的圆，很代码很死板；直线光束太直太死板"）。接口不变，内部按方案出图：
 *   TrioFX.setScheme('jp1' | 'A' | 'B' | 'AB')，TrioFX.scheme()。**默认 'AB'**；引擎不用调（fx_lab.html 的"方案"下拉用它并排比）。
 *   jp1 精特1：冲击波 = 一张规整圆环贴图放大；光束 = 四层直贴图条
 *   A   程序化：冲击波 = 涟漪序列帧（tools/fx_bake.py bake_rip：极坐标噪声位移 → 外缘不圆、粗细不匀、随时间断成弧段，两道波前错时扩散，
 *       外沿甩游丝，早期中心一点能量雾；两套噪声随机挑 + 随机镜像，往受击方向漂一成半径）；
 *       光束 = 沿路铺的网格（drawWavy）：三道不公约的横向波往前传（出口从 0 长起、中段最大、落点收到四成），每层相位错开不同心；
 *       出口胀 1.4 倍、落点前收、宽度沿长度脉动；外晕 / 光身边缘被噪声啃毛（beam2 haloE / bodyE）；芯亮度沿长度不匀（coreE）；
 *       两股游丝绕中线螺旋（虚线描边，偏移随时间滚）、偶发细电弧（每秒 ~9 道、0.07 s）
 *   B   生图：generate_image 出的冲击波两张、光束能量流两张（tools/fx_src/gen_*.png，抠像转色带位置 v），形状仍是 jp1 的（圆环放大、直条）
 *   AB  A 的形状和动 + B 的质感：涟漪序列帧的波带里按极坐标贴 B 冲击波的纹理；光束 A 的网格，光身 / 中层换 B 的能量流贴图
 * 结论（胶片 shots/polish/精特1b_*：同场景同时刻定种子，雷雨夜 / 白天 / 电竞房三种底）：
 *   · jp1 一眼是圆规画的同心圆 + 管子；B 质感好但轮廓还是正圆 / 直条（用户嫌的正是轮廓和运动，不是质感）—— 不选。
 *   · A 轮廓、运动都去掉了几何感：圆断成漂移的弧段、几道波前错时，光束在扭、在胀缩、边缘冒火苗；但纹理偏"程序味"（干净的噪声），
 *     光身按 52 px 一段铺，宽光束（G23）边上看得出折角。
 *   · AB 选这个：A 解决形状和动，B 的手绘能量纹把网格折角和程序噪声都盖掉；三种底上都靠暗边立得住（电竞房蓝底上蓝光束对比比 jp1 弱一档，仍清楚）。
 *   性能（fx_lab.html ?bench=1&schemes=jp1,A,B,AB，同第一批的压测场景，GUI Chrome + SwiftShader，600 帧，只计特效）：
 *     旧 8.2 / p95 13.0 · jp1 12.9 / 19.9 · A 16.5 / 27.6 · B 13.2 / 20.6 · AB 16.9 / 28.0 ms（均值 / p95；同一页同一次跑完四个方案）
 *     AB 比 jp1 多 ~4 ms：冲击波序列帧 ~+1.1（&benchoff=beam 分账）、两道网格光束 ~+2.5（每段一次路径填充；第一版 14 px 一段时 +8）。
 *     软渲染下绝对值不可信、相对比可信；真机未测。
 *     贴图：beam2.webp 47 KB + rip.webp 229 KB（有损，42 格序列帧）—— 不在首屏关键路径上，建议引擎放预取队列里 TrioFX.load。
 *
 * ======================================================================================================================
 * 第二批（精特2，2026-10-01，自检 P4②③④ / P10 / P11）：沿用精特1b 的手法 —— 形状和运动程序化去规则（wob：三道不公约的波，
 * 宽窄 / 横向位移 / 甩影），质感用烘焙 / 生图贴图（band.webp 条带 + beam2 的生图能量流）。胶片 shots/polish/精特2_*（老上新下，同种子同时刻）。
 *   带状物  绸 / 鞭剑：大波 + 布颤（wob）、扭转最窄 0.36（第一版 0.16 侧身成一根线）、宽窄抖、甩影（最近 0.05 s 的形状淡铺在下面）
 *           橡皮臂：整条弓起来回甩 + 往拳头走的肉浪鼓包；竹棒：捅出去被甩弯、回弹几下（第一版两者都是笔直等粗的一根）
 *   水柱    每滴自带粗细（鼓包随水走）+ 横向松散；sheen 高光丝随水流；折射暗边（第一版是一根淡色等粗管子，比旧版还弱）
 *   剑气    月牙身后一条生图能量尾（beam2 bodyB / midB，宽窄横向都抖），月牙胀缩、微抖着转
 *   拖尾    越老越往两边飘、宽窄抖、外圈软光；狐火本体换生图能量流
 *   喷雾 / 喷、秋千绳、花瓣：第一版胶片过（雾团是有体积的噪声团，绳是麻绳纹带 + 甩弯），未再改
 *   剑气月牙：FxShape.slash 现画（原 slash.webp slash1 是圆规弧，精特3 同一条意见）
 *
 *   性能（精特2 收口，fx_lab.html ?bench=1&noold=1&ab2=7：同一页里"不加 / 加第二批"交替 7 轮取增量中位数 —— 桌面负载 40~50，
 *   单独两次跑同一配置就差 ±0.7 ms，必须配对；分账用 &b2off=件 关掉一件看差值、&b2rep=件,5 一件画 5 遍放大）：
 *     第二批增量（一条水柱 + 一条绸 + 一记橡皮臂 + 狐火带尾 + 三道剑气 + 水柱落点溅射）：10.8 ms → 3.65 ms（7 轮 3.60~3.95）
 *     改前分账（ca56965）：水柱 2.6、绸 1.9、臂 1.4、狐火尾 1.0、第二批放的粒子 1.7、水柱落点溅射 1.7（逐件 flush 计时，含 flush 开销）
 *     改后分账（配对差值）：水柱 1.1、剑气 1.0、绸 0.4（放大 5 倍测）、臂 0.35、狐火尾 0.3、溅射 ≈ 0
 *     做了什么（贵在哪 → 怎么省）：
 *       逐像素双线性采样（SwiftShader 下带状物开销的大头，实心填色只剩零头）→ 第二批带子 pattern 最近点采样（band 注释）
 *       每件一张离屏层（换画布 + 整块搬运）→ 去掉：水柱 / 拖尾直接画，绸改不透明（原 0.85）
 *       多遍叠铺（绸三遍、水柱两遍、拖尾三遍、剑气尾两遍）→ comp() 合成一张条一遍铺；绸的扭转按相位 16 档各一张
 *       甩影逐段贴图 × 4 帧 → 每帧一整块渐变（只铺靠梢 55 %、最多 2 块）；臂 / 棒不画甩影（顺着自己的轴伸缩，叠在本体上看不出）
 *       粒子（一颗约 37 µs）：水柱落点 drip 按模拟时间限流（DRIP_GAP）、狐火火星 70 → 30 / s、剑气沿路光粒 16 → 6、水柱出口尘团 1/3 → 1/4、水沫 j ≤ 0.2
 *       段数：水柱每三滴一个点、绸 / 臂按弧长抽点（thin）—— 合计约 0.25 ms
 *   精特2b（折角 / 臂直，用户："路飞的手臂拐弯了…不符合真实物理"）：臂 / 棒直；绸 / 剑节点钉在路上、链只管横向 + 张力、按长度缩形、
 *     出手段沿出口；所有带子过样条 smooth（按转角取点）。bands.py 中线最大转角 绸 / 剑 149~172° → 13~14°、臂 0°。
 *     增量同时段背靠背：HEAD 3.81 ms / 精特2b 3.79 ms（负载 60~85，比 3.65 那次高；读数与做法见 shots/polish/精特2b_压测与折角.txt）
 *     软渲染下绝对值不可信、相对比可信；真机未测。第一批光束（两道 6.5 ms）仍双线性，没动（不在本轮判据里，记 docs/待办.md）
 *
 * ---------- 接入清单（给引擎；行号 = 工作区 trio.js / main.js 2026-10-01 精特2 收口时复核，引擎改动未提交，会漂，以函数名为准）----------
 *   dir 一律可以传三种：弧度 / null（直线）/ 控制点 [cx, cy] —— 引擎已有 dirAt(P, frameName()) 和 rayC(p0, p2, d, lam)：
 *   传 rayC 的结果最省事，件的路线和引擎判打中的那条逐点一致。
 *
 * 5. 带状物 TrioFX.ribbon(Q, style)（建 Act 时一个句柄 h）
 *      G9 G13 红 / 白绸  style 'silk'，Q = A.whip     替换 drawWhip（trio.js:1344）整个函数体的画法：
 *                         h.draw(ctx, handPt(P), c, tg, e, W.t, P.s)  —— e 照 drawWhip 第 3 行算，c = W.way ? rayC(h, tg, d, W.way.lam) : null
 *      G17 鞭剑          style 'blade'，同上
 *      B12 橡皮臂        style 'arm'，Q = A            替换 drawArm（trio.js:1503）里画手臂那一段：h.draw(ctx, wr, d, [fx, fy], 1, b.pk.t, s)（d = drawArm 第 2 行的 dirAt）；
 *                         拳头按 h.tip()[2] 转（替换 drawArm 里的 ang），拳头仍由引擎画
 *      G29 打狗棒        style 'bamboo'，同上
 *      调用点不变：drawOver（trio.js:1331）里 1337 drawArm / 1339 drawWhip
 * 6. 秋千绳 TrioFX.rope(ctx, pts, w, fill, edge, bend)
 *      drawSwing（trio.js:1286）/ drawRopes（1321）/ drawLine（1136）里每根绳原来的 stroke 换成 rope(ctx, pts, R.w * P.s, R.fill, R.edge, bend)；
 *      bend = −摆角速度 × 14（不荡传 0）。调用点 1056 / 1057 / 1096 不变；座板、绳上的花照旧
 * 7. 水柱 / 喷雾（B1~B4 stream，G1~G3 mist）
 *      drawJets（trio.js:969）第 971 行 drawStream / drawMist 换成：
 *        h = J.draw === 'mist' ? TrioFX.mist({ life: J.life }) : TrioFX.stream()     // 建 Act 时一次
 *        h.draw(ctx, jets, b && b.jm, F > 0 ? -b.ja : Math.PI + b.ja)                 // 第 4 参 = 枪口此刻的屏幕角
 *      crew.js drawStream（580）/ drawMist（634）原样留给男女主自己的水枪；落点 main.js:2505 / 2506 / 2512 的 RECIPE.water / pepper.drip
 *      在 Object.assign(RECIPE, TrioFX.RECIPE)（main.js:2630 预取回调里，引擎已接）之后自动是新的（pepper 是新配方）；
 *      water.drip 按 TrioFX.update(dt) 的模拟时钟限流，引擎每帧照常调 TrioFX.update 即可
 * 8. 喷（B20 酒雾，atk.kind 'spray'）h = TrioFX.spray(A.spray)
 *      stepFx（trio.js:825）第 856 行 shots.push({ kind: 'puff', ... }) 之后：h.emit(h0, a)；
 *      drawShot（1399）第 1402 行 'puff' 分支整段换成 h.puff(ctx, s)。路照旧（puff 的 c 已经由引擎按出口方向算）
 * 9. 剑气飞行段（B23 G14，atk.kind 'slash'）
 *      fire()（trio.js:683）slash 分支（707 行 shots.push）每道 t 起点再往前挪 FLY = 0.12；stepShot（721）'slash' 分支（737）
 *      s.t 跨过 −FLY 的那一帧：TrioFX.qi(handPt(P), dir, o.aim(s.u), A.slash.color, { T: FLY, len: A.slash.len, ang: s.ang, life: A.slash.life })；
 *      drawShot 1401 行 'slash' 分支不再画（刀光由 qi 到点自己放）。打中时刻不变（刀光开始后 0.05 s）
 * 10. 飞行物拖尾（G16 狐火 fox、G15 项链 gem、G20 月牙 moon；其他小件 trailLook(rgb, 'fire' | 'glint')）
 *      h = TrioFX.trail(TrioFX.TRAIL.fox)（cfg 里加一项 trail: 'fox' 之类，建 Act 时取）
 *      stepShot（721）飞行段算完 s.x / s.y 之后（第 769 行 s.x = nx 之后；打中弹开的 s.fall 分支 723 行也调，尾巴淡完）：h.track(s, dt)
 *      drawShot（1399）画物件之前（'puff' 分支之后、画物件那段之前）：h.draw(ctx, s)
 * 11. 花瓣上限（P11）：TrioFX.RECIPE.petal 已是 petals() 默认（主体 ≤ 14 片、半径 200 px、寿命 0.55~0.8 s），Object.assign 后自动生效；
 *      按人换颜色：petals({ pal: [...] }) 另挂一个名字
 *
 * 12. 精特3 去几何图元（2026-10-01，用户："光晕的圆圈、弧形的特效太规整"）：画法在 **fx.js FxShape**（正式页已加载，不依赖 trio_fx），
 *      引擎只换调用 —— 全表与胶片见 docs/美术打磨自检.md 第 5 节「几何图元盘点」：
 *        trio.js drawSlash（截图二的金色弧带）函数体 → FxShape.slash(ctx, s, A.slash)   （工作区 trio.js:1498 引擎已换，未提交）
 *        trio.js drawGhost 速度线三根直线 → FxShape.streak（头圆尾尖）
 *        main.js drawStains 的 ctx.arc → FxShape.blob(ctx, x, y, d.r, seed)
 *      fx.js Particles 'ring'（截图一的金色椭圆环，全站 ~70 处）/ 'spark' 已在 fx.js 里换掉，引擎不用动。
 *      TrioFX.slash 本身也改成 FxShape.slash 现画（不再用 slash.webp 序列帧）
 *
 * 预取（main.js:2627 Preload.add('items', ...) 之后另登记一项，不要放进 boot 首帧关键路径）—— 工作区 main.js:2630 引擎已登记：
 *      Preload.add('trio_fx', () => TrioFX.load(V).then(ok => { if (ok) Object.assign(RECIPE, TrioFX.RECIPE); }))
 *      assets/fx/trio/ 九张 + atlas.json，共 397 KB：rip.webp 234 KB · beam2.webp 47 KB · band.webp 18 KB · frag 14 · ring 12 · beam 12 ·
 *      slash 11 · glow 9 · dust 7 KB · atlas.json 6 KB。第二批只用 band + beam2（+ 第一批的 frag / glow / dust）；
 *      slash.webp 精特3 起已没有调用（斩痕、剑气月牙都改 FxShape.slash 现画），仍在 atlas.json 里随包加载（11 KB，记 docs/待办.md）；
 *      没加载完时所有件 ready() 为假直接不画（引擎照旧画的那一份就别删，按 TrioFX.ready() 二选一）
 * ====================================================================================================================== */
'use strict';

const TrioFX = (function () {
  const MAX = 900;
  let META = null;
  const IMG = {};

  function load(ver) {
    const q = ver ? '?v=' + encodeURIComponent(ver) : '';
    return fetch('assets/fx/trio/atlas.json' + q).then(r => r.json()).then(m => {
      META = m;
      return Promise.all(Object.keys(m).map(k => new Promise((done) => {
        const im = new Image();
        im.onload = () => { IMG[k] = im; done(true); };
        im.onerror = () => { console.error(`trio_fx: ${m[k].src} 加载失败`); done(false); };
        im.src = m[k].src + q;
      })));
    }).then(ok => ok.every(Boolean));
  }
  const ready = () => !!META && Object.keys(META).every(k => IMG[k]);

  /* ---------- 调色板 ---------- */
  /* 色带四个点：v = 0 暗边 / 描边、0.45 本色、0.8 亮色、1 高光（tools/fx_bake.py 头注释） */
  const STOPS = [0, 0.45, 0.8, 1];
  const mix = (a, b, k) => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k].map(Math.round);
  const WHITE = [255, 255, 255], BLACK = [0, 0, 0];
  /* 由一个本色推出整条色带：暗边是本色压暗 + 往暖黑（角色线稿 INK）偏，亮色往白推 */
  const INK = [58, 44, 38];
  const palOf = (c, dk = 0.55, lt = 0.55) => [mix(mix(c, INK, 0.35), BLACK, dk * 0.6), c, mix(c, WHITE, lt), mix(c, WHITE, 0.92)];

  const PAL = {
    ember: [[150, 60, 10], [255, 140, 30], [255, 214, 120], [255, 250, 230]],
    gold: [[110, 60, 10], [255, 190, 40], [255, 236, 140], [255, 255, 240]],
    water: [[20, 58, 128], [70, 160, 240], [180, 226, 255], [255, 255, 255]],
    caramel: [[70, 38, 16], [176, 112, 52], [232, 186, 128], [255, 244, 222]],
    pearl: [[18, 10, 6], [56, 36, 22], [120, 86, 60], [250, 236, 220]],
    melon: [[110, 10, 20], [226, 40, 56], [255, 130, 130], [255, 236, 236]],
    seed: [[8, 6, 6], [34, 26, 24], [90, 80, 76], [240, 240, 240]],
    rind: [[20, 60, 24], [50, 140, 56], [200, 236, 190], [250, 255, 246]],
    wood: [[58, 40, 28], [150, 100, 58], [214, 170, 118], [250, 230, 200]],
    plastic: [[40, 44, 52], [96, 106, 120], [170, 180, 192], [240, 244, 250]],
    petal: [[110, 24, 52], [236, 72, 116], [255, 160, 186], [255, 236, 242]],
    petalDeep: [[80, 12, 34], [190, 34, 72], [244, 110, 140], [255, 220, 230]],
    feather: [[120, 104, 112], [228, 222, 226], [250, 248, 250], [255, 255, 255]],
    fluff: [[150, 136, 142], [214, 202, 208], [238, 232, 236], [255, 255, 255]],
    dust: [[104, 90, 78], [190, 174, 154], [228, 218, 202], [248, 242, 232]],
    grit: [[34, 26, 20], [90, 72, 58], [150, 128, 108], [220, 206, 190]],
    purple: [[40, 8, 70], [150, 60, 255], [214, 170, 255], [255, 246, 255]],
    red: [[90, 10, 30], [255, 70, 110], [255, 170, 190], [255, 245, 248]],
    blue: [[16, 30, 110], [80, 120, 255], [170, 200, 255], [245, 248, 255]],
    orange: [[100, 40, 10], [236, 110, 30], [255, 190, 110], [255, 246, 230]],
    rouge: [[110, 20, 70], [255, 92, 160], [255, 176, 212], [255, 240, 248]],
  };

  /* 贴图格 + 调色板 → 一张染好的小 canvas。getImageData 一次、逐像素查色带；按 key 缓存，之后只 drawImage */
  const rampCache = new Map();
  function ramp(sheet, cell, pal) {
    const key = sheet + '|' + cell + '|' + pal.join(';');
    let c = rampCache.get(key);
    if (c) return c;
    const [sx, sy, w, h] = META[sheet].cells[cell];
    /* 读像素在一张临时画布上做，结果 putImageData 进另一张普通画布：willReadFrequently 的画布是内存里的位图，
       拿它当 drawImage 的源每画一次都要重新上传一遍 —— 第一版直接用它当贴图，压测里粒子绘制比旧版慢两倍多 */
    const tmp = document.createElement('canvas');
    tmp.width = w; tmp.height = h;
    const tg = tmp.getContext('2d', { willReadFrequently: true });
    tg.drawImage(IMG[sheet], sx, sy, w, h, 0, 0, w, h);
    const im = tg.getImageData(0, 0, w, h), d = im.data;
    const lut = new Uint8ClampedArray(256 * 3);
    for (let i = 0; i < 256; i++) {
      const v = i / 255;
      let j = 0;
      while (j < 2 && v > STOPS[j + 1]) j++;
      const k = (v - STOPS[j]) / (STOPS[j + 1] - STOPS[j]);
      for (let ch = 0; ch < 3; ch++) lut[i * 3 + ch] = pal[j][ch] + (pal[j + 1][ch] - pal[j][ch]) * k;
    }
    for (let i = 0; i < d.length; i += 4) {
      const v = d[i];
      d[i] = lut[v * 3]; d[i + 1] = lut[v * 3 + 1]; d[i + 2] = lut[v * 3 + 2];
    }
    c = document.createElement('canvas');
    c.width = w; c.height = h;
    c.getContext('2d').putImageData(im, 0, 0);
    c._k = key;                                          // comp() 拿它拼合成贴图的 key
    if (rampCache.size > 1600) rampCache.clear();       // 配方里颜色是离散的，正常几十条 × 冲击波序列帧 10 帧；上限防将来有人写连续随机色
    rampCache.set(key, c);
    return c;
  }

  /* ---------- 粒子 ---------- */
  /* 一种粒子结构，几种画法（p.m）：
       'spr'    贴图，绕自身转（rot），可"翻面"（flip：按 cos 压扁一个轴，读成薄片在空中翻）
       'vel'    贴图顺着速度方向画（水滴 / 籽 / 锥形火花），速度越快拉得越长（stretch）
       'ring'   冲击波：半径 r0 → r1（easeOut），透明度 a → 0，可压扁（sq）
       'flip'   涟漪序列帧（frames 按年龄均分）；'fly' 剑气沿路飞；'fxs' 斩痕（fx.js FxShape.slash 现画，w = 弦长、h = 宽、rgb）
     age 从 -delay 起算：错开出场用模拟时间，不用 setTimeout（墙钟，顿帧冻住时它照走 —— trio.js sweep 那条注释） */
  const act = [], pool = [];
  const FADE_IN = 0.03;                                  // 淡入用绝对时间（skill：按寿命比例会让长寿命粒子迟到）
  function spawn(o) {
    if (act.length >= MAX) pool.push(act.shift());       // 满了回收最老的（同 ammo.js：新发射的才是观众正在看的）
    const p = pool.pop() || {};
    p.m = o.m || 'spr'; p.img = o.img || null; p.tex = o.tex || null; p.tex2 = o.tex2 || null; p.rgb = o.rgb || null; p.frames = o.frames || null;
    p.x = o.x; p.y = o.y; p.vx = o.vx || 0; p.vy = o.vy || 0;
    p.g = o.g || 0; p.drag = o.drag != null ? o.drag : 1;
    p.life = o.life; p.age = -(o.delay || 0);
    p.w = o.w; p.h = o.h != null ? o.h : o.w;
    p.s0 = o.s0 != null ? o.s0 : 1; p.s1 = o.s1 != null ? o.s1 : p.s0;
    p.rot = o.rot || 0; p.vrot = o.vrot || 0;
    p.flip = o.flip || 0; p.fph = Math.random() * 6.283;
    p.a = o.a != null ? o.a : 1; p.fo = o.fo != null ? o.fo : 0.35; p.fi = o.fi != null ? o.fi : FADE_IN;
    p.z = o.z || 0; p.sq = o.sq || 1; p.sway = o.sway || 0; p.stretch = o.stretch || 0;
    p.orb = o.orb || 0; p.ox = o.x; p.oy = o.y;           // orb：绕出生点公转的半径（星星绕头转）
    p.mx = o.mx || 1; p.my = o.my || 1;                   // 镜像（冲击波每次随机翻一翻，不用转 —— 转会走慢路径）
    p.lim = o.lim || 0;                                   // lim：离出生点最远多少 px（P11 范围上限）：最后四分之一淡出，出界即收
    p.path = o.path || null; p.T = o.T || 0;             // 'fly'：沿二次贝塞尔 path [x0, y0, cx, cy, x1, y1] 走 T 秒（剑气）
    act.push(p);
    return p;
  }

  let clock = 0, dripAt = -1;                            // 模拟时钟（顿帧时 update 不走，它也不走）；dripAt：water.drip 上一次的时刻
  const DRIP_GAP = 0.07;
  function update(dt) {
    clock += dt;
    for (let i = act.length - 1; i >= 0; i--) {
      const p = act[i];
      p.age += dt;
      if (p.age < 0) continue;
      if (p.age >= p.life) { act.splice(i, 1); pool.push(p); continue; }
      p.vy += p.g * dt;
      if (p.drag !== 1) { const d = Math.pow(p.drag, dt * 60); p.vx *= d; p.vy *= d; }   // pow(k, dt*60)：不随帧率漂移
      p.x += (p.vx + (p.sway ? Math.cos(p.fph + p.age * 3.1) * p.sway : 0)) * dt;
      p.y += p.vy * dt;
      p.rot += p.vrot * dt;
      if (p.orb) { p.ox += p.vx * dt; p.oy += p.vy * dt; }
      if (p.path) { const q = flyAt(p, p.age); p.x = q[0]; p.y = q[1]; }
      if (p.lim && Math.hypot(p.x - p.ox, p.y - p.oy) >= p.lim) { act.splice(i, 1); pool.push(p); }
    }
  }

  const easeOut = (u) => 1 - Math.pow(1 - u, 3);
  /* 圆团（尘、浆、光粒、冲击波、闪光）一律不转：rot 0 时只平移缩放，Skia 走不带旋转的快路径。软渲染压测里大贴图带旋转
     是粒子绘制的大头（第一版 14 ms，见 fx_lab.html ?bench=1&benchoff=beam），而圆团转不转肉眼看不出 */
  function draw(ctx) {
    if (!act.length) return;
    ctx.save();
    const T = ctx.getTransform();
    /* 两趟：z 0 碎片 / 余烬，z 1 瞬闪（闪光、冲击波）—— 闪光先 spawn，按出生顺序画会被同一下炸出来的碎片盖住 */
    for (let i = 0, z = 0; z < 2; i++) {
      if (i >= act.length) { i = -1; z++; continue; }
      const p = act[i];
      if (p.age < 0 || p.z !== z) continue;
      const u = p.age / p.life;
      let al;
      if (p.m === 'ring') al = p.a * Math.pow(1 - u, 1.3);
      else if (p.m === 'flip') al = p.a * Math.pow(1 - u, 0.6);
      else al = p.a * (p.fi > 0 ? Math.min(1, p.age / p.fi) : 1) * Math.min(1, (p.life - p.age) / (p.life * p.fo));
      if (p.lim) al *= Math.min(1, (p.lim - Math.hypot(p.x - p.ox, p.y - p.oy)) / (p.lim * 0.25));
      if (al <= 0.01) continue;
      ctx.globalAlpha = al;
      let x = p.x, y = p.y;
      if (p.orb) { const ph = p.fph + p.age * 7.4; x = p.ox + Math.cos(ph) * p.orb; y = p.oy + Math.sin(ph) * p.orb * 0.42; }
      ctx.setTransform(T);
      ctx.translate(x, y);
      if (p.m === 'fly') { drawFly(ctx, p, T, al); continue; }
      if (p.m === 'fxs') { FxShape.slash(ctx, { t: p.age, p: [0, 0], ang: p.rot, flip: 1 }, { len: p.w, w: p.h, color: p.rgb, life: p.life }); continue; }
      if (p.m === 'ring') {
        const r = p.s0 + (p.s1 - p.s0) * easeOut(u);
        ctx.scale(p.mx, p.my);
        ctx.drawImage(p.img, -r, -r * p.sq, r * 2, r * 2 * p.sq);
        continue;
      }
      if (p.m === 'flip') {                               // 涟漪序列帧：帧里的波前自己在扩（半径 RIP_R(τ)），按 s0 → s1 定这一帧画多大
        const f = Math.min(p.frames.length - 1, (u * p.frames.length) | 0), tau = (f + 0.5) / p.frames.length;
        const r = p.s0 + (p.s1 - p.s0) * easeOut(u), H = r / RIP_R(p.s1 < p.s0 ? 1 - tau : tau);
        ctx.scale(p.mx, p.my);
        ctx.drawImage(p.frames[p.s1 < p.s0 ? p.frames.length - 1 - f : f], -H, -H * p.sq, H * 2, H * 2 * p.sq);
        continue;
      }
      const sc = p.s0 + (p.s1 - p.s0) * u;
      let w = p.w * sc, h = p.h * sc;
      if (p.m === 'vel') {
        const sp = Math.hypot(p.vx, p.vy);
        ctx.rotate(Math.atan2(p.vy, p.vx));
        w *= 1 + Math.min(1.6, sp * p.stretch);
        ctx.drawImage(p.img, -w * 0.75, -h / 2, w, h);   // 头在粒子位置前面一点，尾巴拖在后面
        continue;
      }
      if (p.rot) ctx.rotate(p.rot);
      if (p.flip) h *= 0.25 + 0.75 * Math.abs(Math.cos(p.fph + p.age * p.flip));
      ctx.drawImage(p.img, -w / 2, -h / 2, w, h);
    }
    ctx.restore();
  }
  /* 'fly'（剑气）：t 秒时在路上哪、朝哪。走法 easeIn 一点（刚甩出去最慢、越飞越快：读出"甩"） */
  function flyAt(p, t) {
    const e = Math.min(1, Math.max(0, t / p.T)), k = e * (0.6 + 0.4 * e), [x0, y0, cx, cy, x1, y1] = p.path, q = 1 - k;
    return [q * q * x0 + 2 * q * k * cx + k * k * x1, q * q * y0 + 2 * q * k * cy + k * k * y1,
            Math.atan2(q * (cy - y0) + k * (y1 - cy), q * (cx - x0) + k * (x1 - cx))];
  }
  /* 剑气本体 + 身后两道残影（同一道月牙，越往后越淡越小）；月牙凸面朝前：FxShape.slash 的弧鼓向 −y，转 ang + π/2。
     月牙是 FxShape.slash 停在"满弧、还没碎"那一段（t 0.08 ~ 0.13）现画 —— 原来是 slash.webp 的 slash1 格，圆规画的弧（精特3 用户：弧形太规整）；
     形状种子按 fph 变，三道剑气各不一样，飞的时候半径沿弧起伏跟着 t 动 */
  function drawFly(ctx, p, T, al) {
    if (p.tex) {                                          // 能量尾：身后 0.075 s 飞过的路铺一条生图能量流（beam2 bodyB / midB），宽窄、横向都按 wob 抖，越往后越细
      const t1 = p.age, t0 = Math.max(0, t1 - 0.075), M = 8, pts = [], hw = [], u = [];
      for (let j = 0; j <= M; j++) {
        /* 横摆 / 宽窄抖的 wob 自变量每点只走 14 / 11（原来 70 / 55：wob 主频 0.051，一点跳 3.6 rad = 采样不到，尾巴抖成之字）；再过样条 */
        const tt = t0 + (t1 - t0) * j / M, [x, y, a] = flyAt(p, tt), f = j / M, o = p.w * 0.16 * wob(j * 14, t1, p.fph) * (1 - f);
        pts.push([x - Math.sin(a) * o, y + Math.cos(a) * o]); hw.push(p.h * 0.28 * Math.pow(f, 1.3) * (1 + 0.4 * wob(j * 11, t1, 1 + p.fph)) + 1); u.push(-tt * 2400);
      }
      ctx.setTransform(T); ctx.globalAlpha = al * 0.9;
      band(ctx, ...smooth(pts, [hw, u], 40, 0.25), [{ tex: comp([[p.tex, 1], [p.tex2, 1]]), smooth: true }]);   // 双线性：生图能量流宽、颗粒细，最近点在胶片上起毛；只活 0.12 s，开销零头
    }
    for (let k = 2; k >= 0; k--) {                       // 两道残影（原来三道贴图；现画的月牙一道 6 次 fill，三道剑气同飞时压测多 0.2 ms）
      const t = p.age - k * 0.03;
      if (t < 0) continue;
      const [x, y, a] = flyAt(p, t), sc = (0.7 + 0.3 * Math.min(1, t / p.T)) * (1 - k * 0.12);
      const fl = 1 + 0.09 * Math.sin(t * 61 + p.fph);       // 月牙一胀一缩、微微抖着转（一张贴图平移过去读成贴纸）
      ctx.setTransform(T); ctx.translate(x, y); ctx.rotate(a + Math.PI / 2 + 0.07 * Math.sin(t * 43 + p.fph));
      ctx.globalAlpha = al * (k ? 0.42 / k : 1); ctx.scale(sc * fl, sc / fl); ctx.rotate(-p.fph);
      FxShape.slash(ctx, { t: 0.08 + 0.4 * t, p: [0, 0], ang: p.fph, flip: 1 }, { len: p.w * 1.27, w: p.w * 0.11, color: p.rgb, life: 1 });
    }
  }

  /* ---------- 小工具（配方用）---------- */
  const R = Math.random;
  const rr = (a, b) => a + R() * (b - a);
  const frag = (name, pal) => ramp('frag', name, pal);
  const glow = (name, pal) => ramp('glow', name, pal);
  const ringImg = (pal) => ramp('ring', 'ring', pal);
  /* 朝场内的扇形：side +1 打向左边的人，碎片往左飞（-side），a0 中心角、spread 张角 */
  function fan(side, spread, sp0, sp1, up) {
    const a = (R() - 0.5) * spread, sp = rr(sp0, sp1);
    return [-side * Math.cos(a) * sp, Math.sin(a) * sp - up];
  }

  /* ---------- 方案（精特1b：去规则）----------
     'jp1' 精特1（规整的圆环 + 直的贴图条）/ 'A' 程序化（涟漪序列帧、光束横向波动 + 毛边 + 游丝 + 电弧）/ 'B' 生图贴图（形状同 jp1）/
     'AB' A 的形状和动 + B 的质感。默认见文件头；fx_lab.html 的"方案"下拉用 setScheme 切 */
  let SCHEME = 'AB';
  const setScheme = (k) => { if (!['jp1', 'A', 'B', 'AB'].includes(k)) throw new Error('trio_fx: 未知方案 ' + k); SCHEME = k; };
  /* 涟漪帧里主波前的半径（格子半宽为 1）：tools/fx_bake.py bake_rip 的 R1 = 0.26 + 0.6 × (1 − (1 − τ)^2.4) */
  const RIP_R = (tau) => 0.26 + 0.6 * (1 - Math.pow(1 - tau, 2.4));
  const ripFrames = new Map();
  function ripOf(mode, v, pal) {
    const key = mode + v + pal.join(';');
    let f = ripFrames.get(key);
    if (!f) { f = []; for (let i = 0; i < 10; i++) f.push(ramp('rip', `rip${mode}${v}_${i}`, pal)); if (ripFrames.size > 150) ripFrames.clear(); ripFrames.set(key, f); }
    return f;
  }
  /* 冲击波：o 同 'ring' 粒子（x, y, s0, s1, life, a, sq, delay, z）+ side（打向哪边：波往受击方向漂一点）。按方案出不同的东西：
     jp1 规整圆环贴图；B 生图冲击波一张（随机两张之一、随机镜像）；A / AB 涟漪序列帧（两套噪声之一、随机镜像） */
  function wave(pal, o) {
    const mx = R() < 0.5 ? -1 : 1, my = R() < 0.5 ? -1 : 1, v = (R() * 2) | 0;
    const drift = o.side ? { vx: -o.side * 0.1 * Math.abs(o.s1 - o.s0) / o.life } : {};   // 扩一圈的工夫往受击方向漂出约一成半径
    if (SCHEME === 'jp1') return spawn({ m: 'ring', img: ringImg(pal), ...o });
    if (SCHEME === 'B') return spawn({ m: 'ring', img: ramp('rip', 'ringB' + v, pal), mx, my, ...drift, ...o });
    return spawn({ m: 'flip', frames: ripOf(SCHEME, v, pal), mx, my, ...drift, ...o, a: Math.min(1, (o.a || 1) * 1.15) });
  }

  /* 第一层：瞬闪（≤ 0.06 s）+ 冲击波。四角星闪一下就收、一团光，冲击波 0.18 s 从 0.3 扩到 1.2、透明度 1 → 0，
     外圈晚 0.03 s 再荡一道更淡更大的。全部普通混合：色带自己从白到暗边，亮底图上也立得住 */
  function flash(x, y, s, pal, o = {}) {
    const k = Math.min(s, 1.8), Rr = (o.R || 64) * k;
    spawn({ m: 'spr', img: glow('flare', pal), x, y, w: 170 * k, s0: 1.25, s1: 0.5, life: 0.07, a: 1, fo: 0.6, fi: 0, z: 1 });
    spawn({ m: 'spr', img: glow('mote', pal), x, y, w: 90 * k, s0: 0.8, s1: 1.3, life: 0.06, a: 0.95, fo: 0.7, fi: 0, z: 1 });
    wave(pal, { x, y, s0: Rr * 0.3, s1: Rr * 1.2, life: 0.18, a: 1, sq: o.sq || 0.78, z: 1, side: o.side });
    wave(pal, { x, y, s0: Rr * 0.5, s1: Rr * 1.65, life: 0.26, a: 0.45, sq: o.sq || 0.78, delay: 0.03, z: 1, side: o.side });
  }
  /* 锥形火花：头宽尾尖、顺速度拉长 */
  function sparks(x, y, side, s, n, pal, o = {}) {
    const k = Math.min(s, 1.8);
    for (let i = 0; i < n; i++) {
      const [vx, vy] = o.all ? (() => { const a = R() * 6.283, sp = rr(o.sp0 || 260, o.sp1 || 640) * k; return [Math.cos(a) * sp, Math.sin(a) * sp]; })()
        : fan(side, o.spread || 2.3, (o.sp0 || 260) * k, (o.sp1 || 700) * k, o.up != null ? o.up : 120);
      const j = rr(4, 16) * k, sp = Math.hypot(vx, vy) || 1;   // 出生点沿飞行方向错开一点：同一帧从一个点射出来读成一把扫帚
      spawn({ m: 'vel', img: glow('spark', pal), x: x + vx / sp * j, y: y + vy / sp * j, vx, vy, g: o.g != null ? o.g : 900, drag: 0.985,
              w: rr(20, 30) * k, h: rr(6, 9) * k, stretch: 0.0011, life: rr(0.18, 0.38), fo: 0.5, delay: rr(0, 0.03) });
    }
  }
  /* 实体碎片：sprite 带高光描边、转、翻、受重力。w0 / w1 写的是**碎片本身**多大（px）；frag 格子 64 里物体只占六七成、四周留空，
     画的时候按 CELL 放大到格子尺寸 —— 不然按格子写数，碎片比旧的矢量版小一圈（第一版胶片实测：木屑、花瓣、水珠都看不清） */
  const CELL = 1 / 0.68;
  function chips(x, y, side, n, names, pal, o) {
    for (let i = 0; i < n; i++) {
      const [vx, vy] = o.all ? (() => { const a = R() * 6.283, sp = rr(o.sp0, o.sp1); return [Math.cos(a) * sp, Math.sin(a) * sp - (o.up || 0)]; })()
        : fan(side, o.spread || 2.5, o.sp0, o.sp1, o.up || 200);
      const pl = Array.isArray(pal[0][0]) ? pal[i % pal.length] : pal;
      const sz = rr(o.w0, o.w1) * CELL;
      spawn({ m: o.vel ? 'vel' : 'spr', img: frag(names[i % names.length], pl), x: x + rr(-1, 1) * (o.jx || 0), y: y + rr(-1, 1) * (o.jy || 0),
              vx, vy, g: o.g, drag: o.drag || 0.99, w: sz, life: rr(o.l0, o.l1), rot: R() * 6.283, vrot: rr(-1, 1) * (o.vrot || 12),
              flip: o.flip || 0, sway: o.sway ? rr(o.sway * 0.6, o.sway) : 0, stretch: o.stretch || 0, a: 1, fo: o.fo || 0.3 });
    }
  }
  /* 软团（尘、浆、绒）：dust 贴图染色，胀开、慢下来 */
  function puffs(x, y, side, n, pal, o) {
    for (let i = 0; i < n; i++) {
      const [vx, vy] = fan(side, o.spread || 2.4, o.sp0, o.sp1, o.up || 40);
      spawn({ m: 'spr', img: ramp('dust', 'dust' + (i % 4), pal), x: x + rr(-1, 1) * (o.jx || 20), y: y + rr(-1, 1) * (o.jy || 14),
              vx, vy, g: o.g || 0, drag: o.drag || 0.92, w: rr(o.w0, o.w1), s0: o.s0 || 0.6, s1: o.s1 || 1.3,
              life: rr(o.l0, o.l1), a: o.a || 0.8, fo: 0.55, delay: o.delay ? rr(o.delay * 0.6, o.delay) : 0 });
    }
  }
  /* 第三层：余烬 —— 小光粒慢慢飘落 / 飘起、一闪一闪（flip 当闪烁），活得比碎片久 */
  function embers(x, y, s, n, pal, o = {}) {
    const k = Math.min(s, 1.8);
    for (let i = 0; i < n; i++) {
      const a = R() * 6.283, sp = rr(40, 170) * k;
      spawn({ m: 'spr', img: glow(o.flare ? 'flare' : 'mote', pal), x: x + rr(-30, 30) * k, y: y + rr(-30, 20) * k,
              vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - (o.up || 30), g: o.g != null ? o.g : 120, drag: 0.95, sway: rr(10, 30),
              w: rr(10, 18) * (o.big || 1), life: rr(0.55, 1.1), flip: o.flare ? 9 : 0, rot: o.flare ? R() : 0, vrot: o.flare ? rr(-3, 3) : 0, delay: rr(0.04, 0.12), a: 0.95, fo: 0.5 });
    }
  }

  /* ---------- 12 个命中配方（瞬闪 → 主体 → 余烬）。tint 与 main.js 同名配方逐字一致（impact 拿它给挨打的人染色）---------- */
  function layered(def) {
    const L = { flash: def.flash, body: def.body, ember: def.ember };
    return { tint: def.tint, layers: L, drip: def.drip,
             burst(x, y, side, s) { L.flash(x, y, side, s); L.body(x, y, side, s); L.ember(x, y, side, s); } };
  }
  const n = (c, s) => Math.max(1, Math.round(c * s));
  const kk = (s) => Math.min(s, 1.8);

  const RECIPE = {
    /* 通用撞击：橙闪 + 冲击波；暖橙锥形火花 + 灰褐碎块 + 一撮灰；余烬是落下来的橙色小光粒 */
    thud: layered({
      tint: [255, 224, 186],
      flash: (x, y, side, s) => flash(x, y, s, PAL.ember, { side }),
      body(x, y, side, s) {
        sparks(x, y, side, s, n(18, s), PAL.ember);
        chips(x, y, side, n(8, s), ['shard0', 'shard1', 'chip0'], PAL.grit, { sp0: 170 * kk(s), sp1: 460 * kk(s), g: 980, w0: 14, w1: 24, l0: 0.6, l1: 1.0, flip: 8, vrot: 14 });
      },
      ember(x, y, side, s) {
        embers(x, y, s, n(7, s), PAL.ember);
        puffs(x, y, side, n(3, s), PAL.dust, { sp0: 60, sp1: 180, w0: 46 * kk(s), w1: 70 * kk(s), l0: 0.5, l1: 0.8, a: 0.4, delay: 0.1 });
      },
    }),
    /* 打懵：金闪；大金星绕头公转（orb）+ 小金星飞散 + 金色火花；余烬是一闪一闪的小四角星 */
    star: layered({
      tint: [255, 242, 196],
      flash: (x, y, side, s) => flash(x, y, s, PAL.gold, { side }),
      body(x, y, side, s) {
        const k = kk(s);
        for (let i = 0; i < n(5, s); i++)
          spawn({ m: 'spr', img: frag('star' + (i % 2), PAL.gold), x: x - side * 18, y: y - rr(40, 90), vx: -side * rr(10, 60), vy: rr(-70, -30), g: 60, drag: 0.94,
                  orb: rr(26, 44) * k, w: rr(34, 46) * k, life: rr(0.8, 1.2), rot: R() * 6.28, vrot: rr(-4, 4), flip: 5, fo: 0.3 });
        chips(x, y, side, n(9, s), ['star0', 'star1'], PAL.gold, { sp0: 200 * k, sp1: 520 * k, g: 700, w0: 18, w1: 28, l0: 0.5, l1: 0.9, vrot: 10, flip: 7 });
        sparks(x, y, side, s, n(10, s), PAL.gold);
      },
      ember: (x, y, side, s) => embers(x, y, s, n(6, s), PAL.gold, { flare: true, big: 1.6, g: 60 }),
    }),
    /* 奶茶：焦糖闪；焦糖液滴（顺速度拉长）+ 深褐珍珠弹开 + 几团浆糊住（drag 大，停在身上）；余烬是往下滴的小滴 */
    splash: layered({
      tint: [246, 226, 198],
      flash: (x, y, side, s) => flash(x, y, s, PAL.caramel, { side, R: 58 }),
      body(x, y, side, s) {
        const k = kk(s);
        puffs(x, y, side, n(5, s), PAL.caramel, { sp0: 90 * k, sp1: 260 * k, drag: 0.86, w0: 40 * k, w1: 64 * k, l0: 1.0, l1: 1.5, a: 0.7, s0: 0.5, s1: 1.1 });
        chips(x, y, side, n(16, s), ['drop0', 'drop1'], PAL.caramel, { sp0: 240 * k, sp1: 640 * k, g: 1150, w0: 22, w1: 34, l0: 0.5, l1: 0.9, vel: true, stretch: 0.0009 });
        chips(x, y, side, n(12, s), ['pearl'], PAL.pearl, { sp0: 220 * k, sp1: 520 * k, up: 300, g: 1180, w0: 18, w1: 26, l0: 1.0, l1: 1.6, vrot: 12 });
      },
      ember(x, y, side, s) {
        chips(x, y + 10, side, n(6, s), ['drop1'], PAL.caramel, { sp0: 20, sp1: 90, up: 0, g: 700, w0: 12, w1: 18, l0: 0.6, l1: 1.0, vel: true, stretch: 0.002, jx: 40, jy: 30 });
      },
    }),
    /* 枕头：浅粉一闪（小）；羽毛打着旋翻着往下飘（flip + sway，重力小）+ 几团绒；余烬是更小的绒羽慢落 */
    feather: layered({
      tint: [255, 238, 240],
      flash: (x, y, side, s) => flash(x, y, s, PAL.fluff, { side, R: 50 }),
      body(x, y, side, s) {
        const k = kk(s);
        puffs(x, y, side, n(4, s), PAL.fluff, { sp0: 60 * k, sp1: 220 * k, w0: 50 * k, w1: 80 * k, l0: 0.5, l1: 0.9, a: 0.55 });
        chips(x, y, side, n(20, s), ['feather0', 'feather1'], PAL.feather, { sp0: 180 * k, sp1: 560 * k, up: 170, g: 150, drag: 0.987, sway: 70,
              w0: 38, w1: 54, l0: 1.4, l1: 2.6, vrot: 4, flip: 3.2, jx: 30, jy: 40 });
      },
      ember(x, y, side, s) {
        chips(x, y, side, n(8, s), ['feather0', 'feather1'], PAL.feather, { all: true, sp0: 40, sp1: 160, up: 60, g: 60, drag: 0.98, sway: 40,
              w0: 22, w1: 28, l0: 1.6, l1: 2.6, vrot: 3, flip: 2.5, jx: 50, jy: 40 });
      },
    }),
    /* 西瓜：红闪；红瓤液滴 + 黑籽（水滴形，顺速度）+ 几片弯的绿皮 + 两团瓤糊住；余烬是往下滴的红汁和两三颗籽 */
    melon: layered({
      tint: [255, 214, 206],
      flash: (x, y, side, s) => flash(x, y, s, PAL.melon, { side }),
      body(x, y, side, s) {
        const k = kk(s);
        puffs(x, y, side, n(4, s), PAL.melon, { sp0: 90 * k, sp1: 240 * k, drag: 0.86, w0: 40 * k, w1: 60 * k, l0: 0.9, l1: 1.4, a: 0.7, s0: 0.5, s1: 1.05 });
        chips(x, y, side, n(12, s), ['drop0', 'drop1'], PAL.melon, { sp0: 240 * k, sp1: 600 * k, g: 1150, w0: 22, w1: 32, l0: 0.5, l1: 0.9, vel: true, stretch: 0.0009 });
        chips(x, y, side, n(16, s), ['seed0', 'seed1'], PAL.seed, { sp0: 260 * k, sp1: 560 * k, up: 300, g: 1180, w0: 14, w1: 20, l0: 0.9, l1: 1.5, vel: true, stretch: 0.0005 });
        chips(x, y, side, n(4, s), ['rind0', 'rind1'], PAL.rind, { sp0: 200 * k, sp1: 420 * k, up: 260, g: 1250, w0: 34, w1: 46, l0: 0.8, l1: 1.2, vrot: 10, flip: 6 });
      },
      ember(x, y, side, s) {
        chips(x, y + 10, side, n(5, s), ['drop1'], PAL.melon, { sp0: 20, sp1: 90, up: 0, g: 700, w0: 12, w1: 18, l0: 0.6, l1: 1.0, vel: true, stretch: 0.002, jx: 40, jy: 30 });
      },
    }),
    /* 斩：本色闪；两道交叉刀光（序列帧）+ 沿刀口飞的锥形火花；余烬是本色小光粒。颜色取 B23 斩痕的绿 */
    slash: layered({
      tint: [255, 242, 196],
      flash: (x, y, side, s) => flash(x, y, s, palOf([90, 230, 110]), { side, R: 52 }),
      body(x, y, side, s) {
        slash(x, y, -0.5, 230, [90, 230, 110], 0.5);
        slash(x, y, 0.75, 200, [90, 230, 110], 0.5, 0.06);
        sparks(x, y, side, s, n(6, s), palOf([90, 230, 110]), { all: true, g: 300, sp0: 200, sp1: 420 });
      },
      ember: (x, y, side, s) => embers(x, y, s, n(6, s), palOf([90, 230, 110])),
    }),
    /* 花束：粉闪；花瓣打着旋飘（深浅两种）+ 金色火花（包装纸反光）；余烬是慢落的小花瓣。
       第二批 P11：数量 / 范围 / 寿命有上限（默认 14 片、200 px、0.55~0.8 s），见 petals() —— 第一批 22 × s 片飞 1.3~2.4 s，s 1.7 时铺满半屏 */
    petal: petals(),
    /* 硬东西崩碎（松果、木头）：橙闪；三角木屑（两面一明一暗，翻转）+ 橙色锥形火花 + 一撮灰；余烬是细木渣和灰 */
    debris: layered({
      tint: [226, 238, 255],
      flash: (x, y, side, s) => flash(x, y, s, PAL.ember, { side, R: 70 }),
      body(x, y, side, s) {
        const k = kk(s);
        chips(x, y, side, n(18, s), ['chip0', 'chip1', 'chip2'], PAL.wood, { sp0: 300 * k, sp1: 700 * k, up: 300, g: 1450, drag: 0.995, w0: 18, w1: 32, l0: 0.55, l1: 1.0, vrot: 20, flip: 10 });
        sparks(x, y, side, s, n(16, s), PAL.ember);
      },
      ember(x, y, side, s) {
        chips(x, y, side, n(10, s), ['chip1', 'chip2'], PAL.wood, { sp0: 60, sp1: 220, up: 120, g: 900, w0: 12, w1: 17, l0: 0.8, l1: 1.3, vrot: 16, flip: 9, jx: 20, jy: 20 });
        puffs(x, y, side, n(3, s), PAL.dust, { sp0: 60, sp1: 180, w0: 46 * kk(s), w1: 70 * kk(s), l0: 0.6, l1: 1.0, a: 0.45, delay: 0.1 });
      },
    }),
    /* 紫色光球（"茈"）：一圈紫冲击波先**往里收**（0.12 s）再往外炸；红、蓝锥形火花对着甩；余烬是往命中点吸的紫光粒 */
    hollow: layered({
      tint: [226, 196, 255],
      flash(x, y, side, s) {
        const k = kk(s);
        wave(PAL.purple, { x, y, s0: 150 * k, s1: 10 * k, life: 0.12, a: 0.9, sq: 0.85 });
        flash(x, y, s, PAL.purple, { side, R: 76 });
      },
      body(x, y, side, s) {
        sparks(x, y, side, s, n(8, s), PAL.red, { all: true, g: 120 });
        sparks(x, y, side, s, n(8, s), PAL.blue, { all: true, g: 120 });
      },
      ember(x, y, side, s) {
        const k = kk(s);
        for (let i = 0; i < n(12, s); i++) {                // 吸：出生在一圈上，速度指向命中点，活到正好飞到
          const a = R() * 6.283, d = rr(90, 150) * k, life = rr(0.3, 0.5);
          spawn({ m: 'spr', img: glow('mote', PAL.purple), x: x + Math.cos(a) * d, y: y + Math.sin(a) * d * 0.8, vx: -Math.cos(a) * d / life, vy: -Math.sin(a) * d * 0.8 / life,
                  w: rr(16, 26), s0: 1, s1: 0.4, life, delay: rr(0.1, 0.35), a: 1, fo: 0.3 });
        }
      },
    }),
    /* 水：水蓝闪 + 冲击波；带高光的透明水滴（顺速度拉长）+ 一层水雾；余烬是往下滴的小水珠。drip：每滴打上去溅两三颗 + 偶尔一圈小水环 */
    water: layered({
      tint: [196, 228, 255],
      flash: (x, y, side, s) => flash(x, y, s, PAL.water, { side }),
      body(x, y, side, s) {
        const k = kk(s);
        chips(x, y, side, n(16, s), ['drop0', 'drop1'], PAL.water, { sp0: 220 * k, sp1: 620 * k, up: 220, g: 1100, w0: 20, w1: 32, l0: 0.45, l1: 0.8, vel: true, stretch: 0.0009 });
        puffs(x, y, side, n(3, s), PAL.water, { sp0: 60, sp1: 180, w0: 40 * k, w1: 64 * k, l0: 0.4, l1: 0.6, a: 0.35 });
      },
      ember(x, y, side, s) {
        chips(x, y + 10, side, n(6, s), ['drop1'], PAL.water, { sp0: 20, sp1: 90, up: 0, g: 800, w0: 12, w1: 16, l0: 0.5, l1: 0.9, vel: true, stretch: 0.002, jx: 40, jy: 30 });
      },
      /* 溅两颗 + 三成一圈小水环；按模拟时间限流：离上一次 drip 不到 DRIP_GAP 秒就按比例少溅（水柱每滴都调，B1 一秒 55 滴 →
         原来一秒 110 颗水珠、同屏多四十几颗，压测里占第二批增量的两成；光束 beamTick 0.1 s 一次的不受影响） */
      drip(x, y, side) {
        const k = Math.min(1, (clock - dripAt) / DRIP_GAP);
        dripAt = clock;
        const m = 2 * k, cnt = Math.floor(m) + (R() < m % 1 ? 1 : 0);
        if (cnt) chips(x, y, side, cnt, ['drop1'], PAL.water, { sp0: 120, sp1: 300, up: 160, g: 1100, w0: 13, w1: 18, l0: 0.3, l1: 0.5, vel: true, stretch: 0.0012 });
        if (R() < 0.3 * k) wave(PAL.water, { x, y, s0: 8, s1: 34, life: 0.16, a: 0.8, sq: 0.78 });
      },
    }),
    /* 篮球砸中（不碎）：橙闪 + 一道大冲击波（弹的那一下）+ 速度线式的锥形火花 + 落灰；余烬是灰 */
    ball: layered({
      tint: [255, 255, 255],
      flash: (x, y, side, s) => flash(x, y, s, PAL.orange, { side, R: 80 }),
      body(x, y, side, s) {
        sparks(x, y, side, s, n(14, s), PAL.orange, { all: true, g: 200, sp0: 380, sp1: 760 });
        puffs(x, y, side, n(5, s), PAL.dust, { sp0: 60, sp1: 200, w0: 50 * kk(s), w1: 84 * kk(s), l0: 0.5, l1: 0.9, a: 0.5 });
      },
      ember: (x, y, side, s) => embers(x, y, s, n(5, s), PAL.orange),
    }),
    /* 口红：玫红闪；玫红液滴 + 粉色珠子；余烬是一闪一闪的粉色小星芒 */
    rouge: layered({
      tint: [255, 170, 210],
      flash: (x, y, side, s) => flash(x, y, s, PAL.rouge, { side, R: 54 }),
      body(x, y, side, s) {
        const k = 0.5 + s;                                // 同 main.js rouge：档 1 尺寸给足
        chips(x, y, side, n(8, k), ['drop0', 'drop1'], PAL.rouge, { sp0: 200, sp1: 480, up: 200, g: 1000, w0: 18, w1: 28, l0: 0.45, l1: 0.8, vel: true, stretch: 0.0009 });
        chips(x, y, side, n(6, k), ['pearl'], PAL.rouge, { sp0: 180, sp1: 400, up: 200, g: 900, w0: 14, w1: 20, l0: 0.45, l1: 0.8, vrot: 6 });
        sparks(x, y, side, s, n(6, k), PAL.rouge);
      },
      ember: (x, y, side, s) => embers(x, y, s, n(5, 0.5 + s), PAL.rouge, { flare: true, big: 1.4, g: 40 }),
    }),
    /* 针扎（G25 护士的巨型针筒飞镖，扎中后插在头上）：10-03 用户「命中特效有点太大太胡」—— 原来借口红的 rouge，首击 s 1.7
       时是 290 px 的光芒 + 两道冲击波 + 18 颗液滴 + 13 颗珠子 + 13 道火花 + 11 颗星芒，把脸整个糊住，读不出"扎了一针"。
       针扎进去是一个点：白芯小闪 0.06 s + 一道贴着针头的小环；几道细火花顺着扎的方向迸开；两三颗药水珠往下滴；不放余烬。
       尺寸按 min(s, 1.2) 封顶，数量照 s 线性（首击 5 道火花 3 滴，后面每下 2 道 1 滴） */
    jab: layered({
      tint: [255, 196, 226],
      flash(x, y, side, s) {
        const k = Math.min(s, 1.2);
        spawn({ m: 'spr', img: glow('flare', PAL.rouge), x, y, w: 96 * k, s0: 1.1, s1: 0.4, life: 0.06, a: 1, fo: 0.6, fi: 0, z: 1 });
        wave(PAL.rouge, { x, y, s0: 10 * k, s1: 40 * k, life: 0.14, a: 0.8, sq: 0.78, z: 1, side });
      },
      body(x, y, side, s) {
        sparks(x, y, side, Math.min(s, 1.2), n(3, s), PAL.rouge, { sp0: 200, sp1: 420, spread: 1.4 });
        chips(x, y, side, n(1.5, s), ['drop0', 'drop1'], PAL.rouge, { sp0: 60, sp1: 160, up: 40, g: 1100, w0: 10, w1: 14, l0: 0.4, l1: 0.6, vel: true, stretch: 0.0009, spread: 1.2 });
      },
      ember() {},
    }),
    /* 防狼喷雾（第二批，G1~G3 的落点溅射）：橙一闪 + 一道橙冲击波；几团有体积的辣椒雾往四周胀开 + 一撮橙色水珠；余烬是慢慢升走的小雾团。
       drip（每个雾团碰到脸）：一团雾 + 偶尔一颗水珠 —— 软的，不像水那样甩一把水珠（同 main.js pepper 的口径） */
    pepper: layered({
      tint: [255, 196, 150],
      flash: (x, y, side, s) => flash(x, y, s, PEPPER, { side, R: 46 }),
      body(x, y, side, s) {
        const k = kk(s);
        puffs(x, y, side, n(5, s), PEPPER, { sp0: 60 * k, sp1: 200 * k, w0: 50 * k, w1: 80 * k, l0: 0.45, l1: 0.75, a: 0.55, spread: 3.4, up: 20 });
        chips(x, y, side, n(6, s), ['drop1'], PEPPER, { sp0: 160 * k, sp1: 380 * k, up: 120, g: 900, w0: 12, w1: 18, l0: 0.35, l1: 0.6, vel: true, stretch: 0.0012 });
      },
      ember: (x, y, side, s) => puffs(x, y - 20, side, n(2, s), PEPPER, { sp0: 30, sp1: 90, up: 90, w0: 40, w1: 60, l0: 0.5, l1: 0.8, a: 0.35, delay: 0.1 }),
      drip(x, y, side) {
        puffs(x, y, side, 1, PEPPER, { sp0: 60, sp1: 180, w0: 34, w1: 56, l0: 0.4, l1: 0.65, a: 0.45, spread: 2.6, up: 20, jx: 8, jy: 8 });
        if (R() < 0.3) chips(x, y, side, 1, ['drop1'], PEPPER, { sp0: 120, sp1: 260, up: 100, g: 900, w0: 10, w1: 14, l0: 0.3, l1: 0.45, vel: true, stretch: 0.0012 });
      },
    }),
  };

  /* ---------- 斩痕 ----------
     精特3：原来是 slash.webp 四格序列帧（划开 → 满弧 → 拉丝 → 碎散），帧里的弧是圆规画的月牙 —— 用户："弧形的特效太规整"。
     换成 fx.js FxShape.slash（与正式页 trio.js drawSlash 的替换同一个画法）：中线半径沿弧起伏、宽度两头收尖且鼓瘪不匀、前沿舌头、
     后半寿命从两头往中间断成碎段、外侧两缕细丝。宽 = len × 0.08（B23 230 / 18、G14 240 / 20 的比例） */
  function slash(x, y, ang, len, rgb, life = 0.45, delay = 0) {
    spawn({ m: 'fxs', x, y, rot: ang, w: len, h: len * 0.08, rgb, life, delay, a: 1, fi: 0, fo: 1e-3 });   // 淡出由 FxShape.slash 自己管（它乘 globalAlpha）
  }

  /* ---------- 光束 ---------- */
  /* 每人一个句柄：按 cfg.beam 把贴图条染好（外晕 / 暗轮廓 / 中层 / 芯各一张调色板），宽度从 layers 里取 */
  function beam(B) {
    const L = B.layers, inner = L[L.length - 1][1], hiC = L.length > 2 ? L[L.length - 2][1] : inner;
    const edge = B.edge, glowC = B.glow;
    const pals = {
      halo: [mix(edge, INK, 0.2), mix(edge, glowC, 0.35), glowC, hiC],
      body: [mix(edge, INK, 0.55), edge, glowC, hiC],
      mid: [edge, mix(edge, glowC, 0.5), glowC, hiC],
      core: [glowC, hiC, mix(hiC, WHITE, 0.6), WHITE],
      spark: [mix(edge, INK, 0.3), glowC, hiC, WHITE],
    };
    /* 宽度：外晕按最外层、光身和中层按第二层、芯按倒数第二层（最内一层是白芯线，贴图条芯本来就白）。外晕 / 中层 / 芯的横截面
       是高斯，可见宽度只有条高的四成上下，所以放大；光身是平顶管，条高九成都实，按 1.15 */
    const L1 = (L[1] || L[0])[0];
    const Wh = L[0][0] * 2.2, Wb = L1 * 1.15, Wm = L1 * 1.5, Wc = Math.max(9, (L.length > 2 ? L[L.length - 2] : L[0])[0] * 1.7);
    /* 出口 / 光头闪光的尺度：按外晕宽但封顶 —— G23 外晕 218 px，照比例画出口四角星是半径三百多的一团，把发波的人整个盖掉 */
    const Wf = Math.min(Wh, 70);
    /* 名、用哪条贴图、宽、alpha、滚动 px/s、贴图横向拉伸。从外往里：外晕（一缕缕的软光）→ 光身（平顶管，带 2~3 px 暗边）→
       中层（亮纹，流得更快）→ 芯。光身是第三版加的：只有高斯三层时 G23 的气浪读成一团半透明的雾，旧的平涂反而因为最外一层
       暗红立得住 —— 亮底图上光束也要靠轮廓（skill chashouji-fx） */
    const layers = [['halo', 'halo', Wh, 0.85, 240, 1.6], ['body', 'body', Wb, 1, 380, 1.2], ['mid', 'mid', Wm, 0.7, 560, 1.0], ['core', 'core', Wc, 1, 900, 0.8]];
    /* 每个方案四层各用哪条贴图（beam = 精特1 的高斯条 / 平顶光身；beam2 = 精特1b：E 被噪声啃毛的、B 生图的） */
    const TEX = { jp1: [['beam', 'halo'], ['beam', 'body'], ['beam', 'mid'], ['beam', 'core']],
                  B: [['beam', 'halo'], ['beam2', 'bodyB'], ['beam2', 'midB'], ['beam', 'core']],
                  A: [['beam2', 'haloE'], ['beam2', 'bodyE'], ['beam2', 'midE'], ['beam2', 'coreE']],
                  AB: [['beam2', 'haloE'], ['beam2', 'bodyB'], ['beam2', 'midB'], ['beam2', 'coreE']] };
    const strips = {}, pats = new WeakMap();
    function prep() { return strips[SCHEME] || (strips[SCHEME] = layers.map(([n], i) => ramp(TEX[SCHEME][i][0], TEX[SCHEME][i][1], pals[n]))); }
    const S = { ph: 'rest', t: 0, from: null, dir: null, to: null, e: 0, k: 1, x: 0, y: 0, r: 0, acc: 0, accSp: 0, accRing: 0, hit: false, arcs: [] };
    function patsFor(ctx) {
      let m = pats.get(ctx);
      if (!m) pats.set(ctx, (m = {}));
      return m[SCHEME] || (m[SCHEME] = prep().map(c => ctx.createPattern(c, 'repeat')));
    }
    /* 路径：from 沿 dir 出去、弯到 to 的二次贝塞尔（dir null 或与 from→to 差不到 2° 就是直线）。返回采样点与累计弧长 */
    function path() {
      const [x0, y0] = S.from, [x1, y1] = S.to, [cx, cy, curved] = ctrl(S.from, S.dir, S.to);
      const N = curved ? 24 : 1, pts = [], len = [0];
      for (let i = 0; i <= N; i++) {
        const t = i / N, q = 1 - t;
        pts.push([q * q * x0 + 2 * q * t * cx + t * t * x1, q * q * y0 + 2 * q * t * cy + t * t * y1]);
        if (i) len.push(len[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
      }
      return { pts, len, total: len[N] };
    }
    function along(P, d) {                                 // 弧长 d 处的点和切向
      let i = 1;
      while (i < P.len.length - 1 && P.len[i] < d) i++;
      const a = P.pts[i - 1], b = P.pts[i], seg = P.len[i] - P.len[i - 1] || 1, u = Math.min(1, Math.max(0, (d - P.len[i - 1]) / seg));
      return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, Math.atan2(b[1] - a[1], b[0] - a[0])];
    }

    return {
      look: pals, widths: [Wh, Wb, Wm, Wc],
      charge(dt, x, y, r) {
        if (!ready()) return;
        S.ph = 'charge'; S.x = x; S.y = y; S.r = r; S.t += dt;
        S.acc += dt * 34;                                  // 往手心吸的光粒：出生在 3r 外一圈，活到正好飞到
        while (S.acc >= 1) {
          S.acc -= 1;
          const a = R() * 6.283, d = r * rr(2.2, 3.4) + 20, life = rr(0.22, 0.36);
          spawn({ m: 'spr', img: glow('mote', pals.spark), x: x + Math.cos(a) * d, y: y + Math.sin(a) * d, vx: -Math.cos(a) * d / life, vy: -Math.sin(a) * d / life,
                  w: rr(8, 14), s0: 1, s1: 0.35, life, a: 1, fo: 0.25 });
        }
      },
      fire(dt, from, dir, to, e, k) {
        if (!ready()) return;
        if (S.ph !== 'fire') {                             // 开轰那一下：出口大闪 + 一圈冲击波
          S.t = 0; S.acc = S.accSp = S.accRing = 0; S.hit = false;
          spawn({ m: 'spr', img: glow('flare', pals.spark), x: from[0], y: from[1], w: Wf * 4, s0: 1.3, s1: 0.6, life: 0.12, rot: R(), a: 1, fo: 0.6 });
          wave(pals.spark, { x: from[0], y: from[1], s0: Wf * 0.4, s1: Wf * 1.6, life: 0.2, a: 0.9, sq: 0.8 });
        }
        S.ph = 'fire'; S.from = from; S.dir = dir; S.to = to; S.e = e; S.k = k; S.t += dt;
        const P = path(), Ld = P.total * e, ang0 = along(P, 0)[2];
        /* A / AB：束身上偶发的细电弧（每秒约 9 道，活 0.07 s）：从光身边上往外跳出去的一截折线，形状生下来就定（每帧不重抖 = 不闪成噪点） */
        if (SCHEME === 'A' || SCHEME === 'AB') {
          for (let i = S.arcs.length - 1; i >= 0; i--) if (S.t - S.arcs[i].t0 > 0.07) S.arcs.splice(i, 1);
          if (Ld > 60 && R() < dt * 9 * k && S.arcs.length < 4)
            S.arcs.push({ t0: S.t, u: rr(0.12, 0.92), side: R() < 0.5 ? -1 : 1, j: [0, 1, 2, 3, 4].map(() => [rr(-1, 1), rr(0.6, 1.2)]) });
        }
        /* 出口散射：沿出口方向 ±0.9 rad 的锥形火花 */
        S.accSp += dt * 36 * k;
        while (S.accSp >= 1) {
          S.accSp -= 1;
          const a = ang0 + rr(-0.9, 0.9), sp = rr(180, 420);
          spawn({ m: 'vel', img: glow('spark', pals.spark), x: from[0], y: from[1], vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, g: 300, drag: 0.96,
                  w: rr(16, 26), h: rr(5, 8), stretch: 0.0015, life: rr(0.14, 0.26), a: 1, fo: 0.5 });
        }
        /* 沿途甩光粒：每 40 px 一格，每格每秒约 7 颗，往两侧飘（略往前冲） */
        S.acc += dt * 7 * k * Ld / 40;
        while (S.acc >= 1) {
          S.acc -= 1;
          const [px, py, a] = along(P, rr(20, Math.max(21, Ld - 10))), side = R() < 0.5 ? -1 : 1, sp = rr(30, 110);
          spawn({ m: 'spr', img: glow('mote', R() < 0.5 ? pals.spark : pals.mid), x: px + Math.cos(a + 1.571) * side * Wm * 0.3, y: py + Math.sin(a + 1.571) * side * Wm * 0.3,
                  vx: Math.cos(a + 1.571) * side * sp + Math.cos(a) * 60, vy: Math.sin(a + 1.571) * side * sp + Math.sin(a) * 60 - 20, g: -30, drag: 0.95,
                  w: rr(8, 15), s0: 1, s1: 0.3, life: rr(0.3, 0.5), a: 1, fo: 0.4 });
        }
        /* 末端：伸到了（e = 1）才溅 —— 反溅的锥形火花 + 每 0.11 s 一圈冲击波 */
        if (e >= 1) {
          const [hx, hy, a] = along(P, Ld);
          if (!S.hit) { S.hit = true; S.accRing = 0.11; }   // 伸到的那一帧先溅一圈
          S.accRing += dt;
          if (S.accRing >= 0.11) { S.accRing -= 0.11; wave(pals.spark, { x: hx, y: hy, s0: Wf * 0.35, s1: Wf * 1.5, life: 0.2, a: 0.85 * k, sq: 0.8 }); }
          for (let i = 0; i < 2; i++) if (R() < dt * 26 * k) {
            const b = a + Math.PI + rr(-1.3, 1.3), sp = rr(220, 520);
            spawn({ m: 'vel', img: glow('spark', pals.spark), x: hx, y: hy, vx: Math.cos(b) * sp, vy: Math.sin(b) * sp, g: 650, drag: 0.98,
                    w: rr(18, 28), h: rr(6, 9), stretch: 0.0015, life: rr(0.18, 0.32), a: 1, fo: 0.5 });
          }
        }
      },
      rest() { S.ph = 'rest'; },
      draw(ctx) {
        if (!ready() || S.ph === 'rest') return;
        if (S.ph === 'charge') { drawCharge(ctx); return; }
        if (SCHEME === 'A' || SCHEME === 'AB') { drawWavy(ctx); return; }
        const P = path(), Ld = P.total * S.e;
        if (Ld < 2) return;
        const pt = patsFor(ctx), t = S.t, k = S.k;
        ctx.save();
        /* 三层：外晕 → 中层 → 芯，各自滚动（越往里越快：读出"芯在冲、晕在拖"） */
        for (let li = 0; li < layers.length; li++) {
          const [, , W0, al, spd, sx] = layers[li], pat = pt[li];
          ctx.globalAlpha = al * k;
          ctx.fillStyle = pat;
          let d = 0;
          for (let i = 1; i < P.pts.length && d < Ld; i++) {
            const a = P.pts[i - 1], b = P.pts[i], seg = P.len[i] - P.len[i - 1];
            const segL = Math.min(seg, Ld - d);
            const mid = d + segL / 2;
            /* 粗细：出口 28 px 内从 0.55 胀满，光头前 20 px 收到 0.8；一道往前走的波纹（同一处粗细随时间起伏 = 在流） */
            const w = W0 * (0.6 + 0.4 * k) * (0.55 + 0.45 * Math.min(1, mid / 28)) * (Ld - mid < 20 ? 0.8 + 0.2 * (Ld - mid) / 20 : 1)
              * (1 + 0.08 * Math.sin(mid * 0.045 - t * 30) * (li === 0 ? 1.6 : 1));
            const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
            ctx.save();
            ctx.translate(a[0], a[1]);
            ctx.rotate(ang);
            ctx.scale(sx, w / 64);
            /* 贴图坐标：沿弧长 d、减去滚动量 —— 噪声往光头那边流 */
            ctx.translate(-((d - t * spd) / sx % 256), -32);
            ctx.fillRect(((d - t * spd) / sx % 256), 0, (segL + (P.pts.length > 2 ? 0.6 : 0)) / sx, 64);
            ctx.restore();
            d += seg;
          }
        }
        /* 光头：一团光 + 小四角星；出口：四角星闪光（转、跳） */
        const [hx, hy] = along(P, Ld), [fx, fy, a0] = along(P, 0);
        ctx.globalAlpha = k;
        const head = ramp('glow', 'mote', pals.mid), fl = ramp('glow', 'flare', pals.spark);
        const hr = Math.max(Wf, Wb * 0.8) * (1.1 + 0.1 * Math.sin(t * 47));
        ctx.drawImage(head, hx - hr, hy - hr, hr * 2, hr * 2);
        const fr = Wf * (1.5 + 0.25 * Math.sin(t * 37)) * (t < 0.1 ? 1.6 - 6 * t : 1);
        ctx.translate(fx, fy); ctx.rotate(a0 + t * 3);
        ctx.drawImage(fl, -fr, -fr, fr * 2, fr * 2);
        ctx.restore();
      },
    };
    /* 精特1b A / AB：束身是沿路铺的网格（band），不是直条 ——
       · 横向波动：中线按两道往前传的正弦摆（出口 60 px 内从 0 长起、中段最大、最后四分之一收到四成），每层相位错开 → 几层不再同心，像一股在扭的能量；
       · 宽度：出口胀 1.4 倍、落点前 24 px 收、沿长度一道往前走的脉动；
       · 边缘：毛边贴图（haloE / bodyE 的 alpha 被噪声啃过；AB 的光身 / 中层是生图的能量流）随滚动一直在变；
       · 外绕两股游丝（细亮线绕着中线螺旋，速度比束身快）+ 偶发细电弧（fire 里生、这里画）；
       · 芯亮度沿长度不匀（coreE）。 */
    function drawWavy(ctx) {
      const P = path(), Ld = P.total * S.e;
      if (Ld < 2) return;
      const t = S.t, k = S.k, tex = prep(), N = 2 * Math.max(3, Math.ceil(Ld / 52));   // 一段约 26 px：软渲染下钱花在每段一次的路径填充上（14 px 时两道光束 12 ms），波长最短 120 px，26 px 还看不出折角
      const base = [];
      for (let i = 0; i <= N; i++) { const d = Ld * i / N, [x, y, a] = along(P, d); base.push([x, y, a, d]); }
      const env = (d) => Math.min(1, d / 60) * (1 - 0.6 * Math.max(0, (d - Ld * 0.75) / (Ld * 0.25)));
      const off = (d, ph, am) => env(d) * am * (Math.sin(d * 0.022 - t * 15 + ph) + 0.55 * Math.sin(d * 0.051 - t * 26 + ph * 2) + 0.35 * Math.sin(d * 0.0093 - t * 7 + ph * 3));   // 三道不公约的波：不重复成一节节
      const amp = Math.min(26, Wb * 0.2 + 3);
      ctx.save();
      const A0 = ctx.globalAlpha;
      const strand = (ph, am, wOf, uOf, step = 1) => {
        const pts = [], hw = [], u = [];
        for (let i = 0; i <= N; i += step) {
          const [x, y, a, d] = base[i];
          const o = off(d, ph, am);
          pts.push([x - Math.sin(a) * o, y + Math.cos(a) * o]); hw.push(wOf(d)); u.push(uOf(d));
        }
        return [pts, hw, u];
      };
      for (let li = 0; li < layers.length; li++) {
        const [, , W0, al, spd, sx] = layers[li];
        const [pts, hw, u] = strand(li * 0.9, amp * (li === 0 ? 1.35 : 1), (d) => W0 / 2 * (0.6 + 0.4 * k) * (1 + 0.4 * Math.exp(-d / 45))
          * (Ld - d < 24 ? 0.7 + 0.3 * (Ld - d) / 24 : 1) * (1 + 0.06 * Math.sin(d * 0.031 - t * 19 + li) + 0.05 * Math.sin(d * 0.073 - t * 31 + 2.1 * li) + 0.04 * Math.sin(d * 0.013 - t * 9)), (d) => (d - t * spd) / sx,
          li < 3 ? 2 : 1);                                // 外晕 / 光身 / 中层隔一个点取（段长约 52 px，宽、软，折角看不出）；芯细，按 26 px
        ctx.globalAlpha = A0 * al * k;
        band(ctx, pts, hw, u, [{ tex: tex[li], ext: al < 1 ? 0 : 0.6, smooth: true }]);
        if (li === 2) {                                   // 游丝：两股绕中线螺旋，压在中层之上、芯之下。一股 = 暗边 + 亮芯两笔虚线描边，虚线偏移随时间滚（断续、往前流）——
          ctx.lineCap = 'round'; ctx.lineJoin = 'round';  // 第一版每股按段铺贴图，两道光束多出 ~100 次填充；描边一股两次调用
          const fw = Math.max(1.3, Math.min(2.6, Wm * 0.03));
          for (const q of [0, Math.PI]) {
            ctx.beginPath();
            for (let i = 0; i <= N; i++) {
              const [x, y, a, d] = base[i], o = off(d, 1.8, amp) + Wm * 0.48 * Math.sin(d * 0.032 - t * 13 + q) * Math.min(1, d / 40);
              if (i) ctx.lineTo(x - Math.sin(a) * o, y + Math.cos(a) * o); else ctx.moveTo(x - Math.sin(a) * o, y + Math.cos(a) * o);
            }
            ctx.setLineDash([46 + 20 * Math.sin(q + 1), 22]); ctx.lineDashOffset = -t * 900 - q * 30;
            ctx.globalAlpha = A0 * 0.75 * k;
            ctx.strokeStyle = `rgb(${pals.body[0].join(',')})`; ctx.lineWidth = fw + 2; ctx.stroke();
            ctx.strokeStyle = `rgb(${pals.core[2].join(',')})`; ctx.lineWidth = fw; ctx.stroke();
          }
          ctx.setLineDash([]);
        }
      }
      /* 电弧：光身边上一截往外跳的折线，暗边 + 亮芯两笔 */
      ctx.globalAlpha = A0 * k;
      ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      for (const c of S.arcs) {
        const d = c.u * Ld, [x, y, a] = along(P, d), o = off(d, 0.9, amp), nx = -Math.sin(a) * c.side, ny = Math.cos(a) * c.side;
        const pts = c.j.map(([jt, jn], i) => { const r = Wb * 0.42 + i * Wb * 0.16 * jn; return [x - Math.sin(a) * o + nx * r + Math.cos(a) * (i * 7 + jt * 6), y + Math.cos(a) * o + ny * r + Math.sin(a) * (i * 7 + jt * 6)]; });
        for (const [w, col] of [[3.2, `rgb(${pals.body[0].join(',')})`], [1.4, `rgb(${pals.core[2].join(',')})`]]) {
          ctx.strokeStyle = col; ctx.lineWidth = w; ctx.beginPath(); pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.stroke();
        }
      }
      /* 光头一团光、出口四角星（同 jp1，光头跟着波动后的中线） */
      const [hx, hy, ha] = along(P, Ld), ho = off(Ld, 0, amp), [fx, fy, a0] = along(P, 0);
      const head = ramp('glow', 'mote', pals.mid), fl = ramp('glow', 'flare', pals.spark);
      const hr = Math.max(Wf, Wb * 0.8) * (1.1 + 0.1 * Math.sin(t * 47));
      ctx.globalAlpha = A0 * k;
      ctx.drawImage(head, hx - Math.sin(ha) * ho - hr, hy + Math.cos(ha) * ho - hr, hr * 2, hr * 2);
      const fr = Wf * (1.5 + 0.25 * Math.sin(t * 37)) * (t < 0.1 ? 1.6 - 6 * t : 1);
      ctx.translate(fx, fy); ctx.rotate(a0 + t * 3);
      ctx.drawImage(fl, -fr, -fr, fr * 2, fr * 2);
      ctx.restore();
    }
    function drawCharge(ctx) {
      const r = S.r, t = S.t;
      const orb = ramp('glow', 'mote', pals.mid), fl = ramp('glow', 'flare', pals.spark);
      ctx.save();
      const R0 = r * 1.6 * (1 + 0.08 * Math.sin(t * 40));
      ctx.drawImage(orb, S.x - R0, S.y - R0, R0 * 2, R0 * 2);
      ctx.translate(S.x, S.y); ctx.rotate(t * 4);
      const F = r * 2.2 * (0.85 + 0.15 * Math.sin(t * 23));
      ctx.globalAlpha = 0.9;
      ctx.drawImage(fl, -F, -F, F * 2, F * 2);
      ctx.restore();
    }
  }

  /* ====================================================================================================================
     第二批（2026-10-01，自检 P4②③④ / P10 / P11）：带状物、水柱 / 喷雾、剑气飞行段、飞行物拖尾、花瓣上限。接入点见文件头第 5~11 节
     ==================================================================================================================== */

  /* ---------- 出口方向 → 路径控制点（P1 共用）----------
     所有从手里出去的件走同一条路：from 沿 dir 出去、弯到 to 的二次贝塞尔，控制点 = from + dir × 0.42·|to − from|。
     dir null 或与 from→to 差不到 2° → 控制点在中点（直线）。dir 也可以直接给控制点 [cx, cy]。返回 [cx, cy, 弯不弯] */
  function ctrl(from, dir, to) {
    if (Array.isArray(dir)) return [dir[0], dir[1], true];   // 调用方已经有自己的控制点（引擎 rayC / over 的结果）：原样用，路线与引擎判打中的那条逐点一致
    const dx = to[0] - from[0], dy = to[1] - from[1], D = Math.hypot(dx, dy) || 1;
    if (dir != null) {
      const da = Math.atan2(Math.sin(dir - Math.atan2(dy, dx)), Math.cos(dir - Math.atan2(dy, dx)));
      if (Math.abs(da) > 0.035) return [from[0] + Math.cos(dir) * D * 0.42, from[1] + Math.sin(dir) * D * 0.42, true];
    }
    return [(from[0] + to[0]) / 2, (from[1] + to[1]) / 2, false];
  }
  const bz = (p0, c, p2, t) => { const q = 1 - t; return [q * q * p0[0] + 2 * q * t * c[0] + t * t * p2[0], q * q * p0[1] + 2 * q * t * c[1] + t * t * p2[1]]; };
  /* 三道不公约的波（同 beam drawWavy 的 off）：沿长度 x（px）、时间 t 往前传，ph 错开股 / 层。值域约 −1..1，不重复成一节节 —— 第二批所有"去规则"共用 */
  const wob = (x, t, ph = 0) => (Math.sin(x * 0.022 - t * 15 + ph) + 0.55 * Math.sin(x * 0.051 - t * 26 + ph * 2) + 0.35 * Math.sin(x * 0.0093 - t * 7 + ph * 3)) / 1.9;
  const rgbOf = (c) => {                                 // '#rrggbb' / 'rgba(r,g,b,a)' / [r, g, b] → [r, g, b]
    if (Array.isArray(c)) return c;
    if (c[0] === '#') return [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16));
    return c.match(/[\d.]+/g).slice(0, 3).map(Number);
  };

  /* ---------- 贴图带：沿折线按段铺一条贴图条 ----------
     每段是一个四边形（两头用顶点法线 × 半宽，邻段共用顶点 → 边是连续的，宽度可以逐点变：绸子扭转、末梢渐细），
     四边形里按这段的局部坐标系铺 pattern：贴图 x = 沿长度的 u（调用方给每个点的 u，弧长 / 水滴序号 / 从末端量），
     贴图 y = 横截面（行 32 = 中线）。带子细到几 px 时 pattern 缩小采样会闪 —— 按屏幕宽度挑 1 / ½ / ¼ 的预缩版（mip）。
     段与段之间往前多铺 0.6 px（ext），盖掉抗锯齿接缝（所以整条带子不能再整体降透明度：0.6 px 的重叠会叠出一道道深线 —— 第二批的带子一律
     不透明或靠贴图自带的透明度；原来绸 0.85 / 水柱 0.95 是画到离屏层再贴回，每件多一次换画布 + 整块搬运，精特2 压测时去掉）。
     采样：第二批的带子 pattern 用最近点采样（imageSmoothingEnabled = false，passes[0].smooth 例外：第一批光束、剑气能量尾仍双线性）——
     SwiftShader 软渲染里带状物的开销几乎全是逐像素的双线性采样（fx_lab ?bench=1&ab2=3&b2rep=stream,5 放大分账：水柱带身一帧
     0.95 ms，改实心填色只剩零头；段数是次要的，见 thin）；贴图都是软渐变 + mip 选到接近 1:1，最近点在胶片上看不出颗粒 */
  const patCache = new WeakMap();
  /* 合成贴图条：几张 256 × 64 的条按 [贴图, 透明度, 纵向占比 f（居中，1 = 满高）] 叠成一张，离屏一次、按 key 缓存。
     一条带子原来要沿路铺几遍（本体 + 高光、外晕 + 芯 + 亮丝），每遍把整条带子的面积采样一次；合成后每段只铺一次，
     观感同叠铺（叠的是同一套 u / 半宽） */
  const compCache = new Map();
  function comp(layers) {
    const key = layers.map(([t, a, f = 1]) => t._k + '@' + a.toFixed(3) + '@' + f).join('|');
    let c = compCache.get(key);
    if (c) return c;
    c = document.createElement('canvas'); c.width = 256; c.height = 64;
    const g = c.getContext('2d');
    for (const [t, a, f = 1] of layers) { if (a <= 0.004) continue; g.globalAlpha = a; g.drawImage(t, 0, 0, 256, 64, 0, 32 - 32 * f, 256, 64 * f); }
    c._k = key;
    if (compCache.size > 400) compCache.clear();
    compCache.set(key, c);
    return c;
  }
  /* 折线每点的法线（相邻两段法线的平均） */
  function normals(pts) {
    const n = pts.length, nx = new Float64Array(n), ny = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      let sx = 0, sy = 0;
      for (const j of [i - 1, i]) {
        if (j < 0 || j >= n - 1) continue;
        const dx = pts[j + 1][0] - pts[j][0], dy = pts[j + 1][1] - pts[j][1], L = Math.hypot(dx, dy);
        if (L > 1e-6) { sx += -dy / L; sy += dx / L; }
      }
      const L = Math.hypot(sx, sy) || 1; nx[i] = sx / L; ny[i] = sy / L;
    }
    return [nx, ny];
  }
  /* 甩影片：一帧形状铺成一整块（一次 fill，纯色），代替逐段贴图 —— 它压在本体下面、淡、只活 0.05 s，贴图的横向软边看不出来 */
  function sheet(ctx, pts, hw, color) {
    const n = pts.length;
    if (n < 2) return;
    const [nx, ny] = normals(pts);
    ctx.beginPath();
    for (let i = 0; i < n; i++) { const x = pts[i][0] + nx[i] * hw[i], y = pts[i][1] + ny[i] * hw[i]; if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); }
    for (let i = n - 1; i >= 0; i--) ctx.lineTo(pts[i][0] - nx[i] * hw[i], pts[i][1] - ny[i] * hw[i]);
    ctx.fillStyle = color; ctx.fill();
  }
  function mipOf(tex, lv) {
    if (!lv) return tex;
    tex._mip = tex._mip || [];
    if (!tex._mip[lv]) {
      const f = 1 / (1 << lv), c = document.createElement('canvas');
      c.width = Math.max(1, Math.round(tex.width * f)); c.height = Math.max(1, Math.round(tex.height * f));
      const g = c.getContext('2d'); g.imageSmoothingQuality = 'high'; g.drawImage(lv > 1 ? mipOf(tex, lv - 1) : tex, 0, 0, c.width, c.height);
      tex._mip[lv] = c;
    }
    return tex._mip[lv];
  }
  function patOf(ctx, tex, lv) {
    let m = patCache.get(ctx);
    if (!m) patCache.set(ctx, (m = new Map()));
    const src = mipOf(tex, lv);
    let p = m.get(src);
    if (!p) { p = ctx.createPattern(src, 'repeat-x'); if (lv) p.setTransform(new DOMMatrix().scale(1 << lv)); m.set(src, p); }
    return p;
  }
  /* pts [[x, y]...]、hw 每点半宽、u 每点贴图横坐标（贴图 px）。passes：[{ tex（canvas 或 i → canvas）, alpha?(i), ext? }]，依次叠；
     ink：沿两条边各描一笔（贴图里不烧描边：段宽各不相同，烧进去的边对不上）；cap：末端也封口 */
  function band(ctx, pts, hw, u, passes, ink, inkW = 1.2, cap = true) {
    const n = pts.length;
    if (n < 2) return;
    const [nx, ny] = normals(pts);
    const T = ctx.getTransform(), A0 = ctx.globalAlpha, SM = ctx.imageSmoothingEnabled;
    ctx.imageSmoothingEnabled = !!passes[0].smooth;
    for (const ps of passes) {
      for (let i = 0; i < n - 1; i++) {
        const al = ps.alpha ? ps.alpha(i) : 1;
        if (al <= 0.01) continue;
        const a = pts[i], b = pts[i + 1], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
        if (L < 1e-3) continue;
        const cx = dx / L, cy = dy / L, ext = ps.ext === 0 || i === n - 2 ? 0 : 0.6;
        const hm = Math.max(hw[i], hw[i + 1], 0.5), su = (u[i + 1] - u[i]) / L || 1e-3, u0 = ((u[i] % 256) + 256) % 256;
        const lv = hm * 2 < 12 ? 2 : hm * 2 < 28 ? 1 : 0;
        const tex = typeof ps.tex === 'function' ? ps.tex(i) : ps.tex;
        const C = [[a[0] + nx[i] * hw[i], a[1] + ny[i] * hw[i]], [b[0] + nx[i + 1] * hw[i + 1] + cx * ext, b[1] + ny[i + 1] * hw[i + 1] + cy * ext],
                   [b[0] - nx[i + 1] * hw[i + 1] + cx * ext, b[1] - ny[i + 1] * hw[i + 1] + cy * ext], [a[0] - nx[i] * hw[i], a[1] - ny[i] * hw[i]]];
        ctx.setTransform(T); ctx.translate(a[0], a[1]); ctx.rotate(Math.atan2(cy, cx)); ctx.scale(1 / su, hm / 32); ctx.translate(-u0, -32);
        ctx.beginPath();
        for (let k = 0; k < 4; k++) {
          const px = C[k][0] - a[0], py = C[k][1] - a[1], s = px * cx + py * cy, t = -px * cy + py * cx;
          const X = u0 + s * su, Y = 32 + t * 32 / hm;
          if (k) ctx.lineTo(X, Y); else ctx.moveTo(X, Y);
        }
        ctx.globalAlpha = A0 * al; ctx.fillStyle = patOf(ctx, tex, lv); ctx.fill();
      }
    }
    ctx.setTransform(T); ctx.globalAlpha = A0; ctx.imageSmoothingEnabled = SM;
    if (ink) {
      ctx.strokeStyle = ink; ctx.lineWidth = inkW; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      ctx.beginPath();
      for (let i = 0; i < n; i++) { const x = pts[i][0] + nx[i] * hw[i], y = pts[i][1] + ny[i] * hw[i]; if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); }
      if (cap) for (let i = n - 1; i >= 0; i--) ctx.lineTo(pts[i][0] - nx[i] * hw[i], pts[i][1] - ny[i] * hw[i]);
      else { ctx.moveTo(pts[0][0] - nx[0] * hw[0], pts[0][1] - ny[0] * hw[0]); for (let i = 1; i < n; i++) ctx.lineTo(pts[i][0] - nx[i] * hw[i], pts[i][1] - ny[i] * hw[i]); }
      ctx.stroke();
    }
  }
  /* 抽点：沿弧长每隔至少 minSeg px 留一个点（头尾必留）。只给直的臂 / 棒用（段只带粗细变化）；弯的带子走 smooth（按转角取点） */
  const thin = (L, minSeg) => { const k = [0]; for (let i = 1; i < L.length - 1; i++) if (L[i] - L[k[k.length - 1]] >= minSeg) k.push(i); k.push(L.length - 1); return k; };
  const arcLen = (pts) => { const L = [0]; for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])); return L; };
  /* 顺滑：把控制点（弹簧链节点 / 水滴 / 飞过的点）当成一条向心 Catmull-Rom 样条的过点，按弯的程度重新取点再交给 band。
     直接把控制点连成折线（精特2 收口时绸按弧长抽到 ≥ 20 px 一段、水柱三滴一个点）在波峰处折成可见的尖角（用户：不符合真实物理）；
     样条曲率连续，取点规则：切向比上一个留下的点将要转过 maxTurn（默认 7°：一圈 52 边，圆看着就是圆；留转过之前那个采样点）或弧长到 maxSeg 才留 ——
     直的地方段长、弯的地方自动加密，段数（每段一次 fill）和原来抽点差不多。
     attrs：每个控制点的一组标量 [[hw…], [u…], …]，按同一个参数插值（第一组 = 半宽：Catmull-Rom 同样顺滑、下限 0.3；其余线性，u 保持单调）；
     宽度变化超过 25 % 也留点（扭转的窄处不被一段直线抹平）。返回 [pts, ...attrs] */
  function smooth(P, attrs, maxSeg = 28, maxTurn = 0.12, maxDw = 0.25) {
    const n = P.length;
    if (n < 3) return [P, ...attrs];
    const at = (i) => P[Math.max(0, Math.min(n - 1, i))];
    const dense = [[P[0][0], P[0][1]]], A = attrs.map(a => [a[0]]);
    for (let i = 0; i < n - 1; i++) {
      const p0 = i ? at(i - 1) : [2 * P[0][0] - P[1][0], 2 * P[0][1] - P[1][1]], p1 = P[i], p2 = P[i + 1],
            p3 = i + 2 < n ? P[i + 2] : [2 * P[n - 1][0] - P[n - 2][0], 2 * P[n - 1][1] - P[n - 2][1]];
      const d01 = Math.max(1e-3, Math.hypot(p1[0] - p0[0], p1[1] - p0[1]) ** 0.5), d12 = Math.max(1e-3, Math.hypot(p2[0] - p1[0], p2[1] - p1[1]) ** 0.5),
            d23 = Math.max(1e-3, Math.hypot(p3[0] - p2[0], p3[1] - p2[1]) ** 0.5);
      /* 向心参数化的切向（Barry–Goldman 化成 Hermite）：不会在点挤在一起的地方打圈 / 出尖 */
      const m1 = [0, 1].map(k => (p1[k] - p0[k]) / d01 - (p2[k] - p0[k]) / (d01 + d12) + (p2[k] - p1[k]) / d12).map(v => v * d12),
            m2 = [0, 1].map(k => (p2[k] - p1[k]) / d12 - (p3[k] - p1[k]) / (d12 + d23) + (p3[k] - p2[k]) / d23).map(v => v * d12);
      const m = Math.max(1, Math.ceil(d12 * d12 / 3));
      for (let j = 1; j <= m; j++) {
        const t = j / m, t2 = t * t, t3 = t2 * t, h00 = 2 * t3 - 3 * t2 + 1, h10 = t3 - 2 * t2 + t, h01 = -2 * t3 + 3 * t2, h11 = t3 - t2;
        dense.push([h00 * p1[0] + h10 * m1[0] + h01 * p2[0] + h11 * m2[0], h00 * p1[1] + h10 * m1[1] + h01 * p2[1] + h11 * m2[1]]);
        attrs.forEach((a, k) => {
          if (k) { A[k].push(a[i] + (a[i + 1] - a[i]) * t); return; }
          const a0 = a[Math.max(0, i - 1)], a3 = a[Math.min(n - 1, i + 2)];      // 均匀 Catmull-Rom
          A[0].push(Math.max(0.3, 0.5 * (2 * a[i] + (a[i + 1] - a0) * t + (2 * a0 - 5 * a[i] + 4 * a[i + 1] - a3) * t2 + (3 * a[i] - a0 - 3 * a[i + 1] + a3) * t3)));
        });
      }
    }
    const D = dense.length, out = [dense[0]], O = A.map(a => [a[0]]);
    let li = 0, run = 0;
    const dirAt = (j) => { const a = dense[Math.max(0, j - 1)], b = dense[Math.min(D - 1, j + 1)]; return Math.atan2(b[1] - a[1], b[0] - a[0]); };
    let d0 = dirAt(0);
    const keep = (j) => { out.push(dense[j]); A.forEach((a, k) => O[k].push(a[j])); li = j; d0 = dirAt(j); };
    const turnAt = (j) => { const dj = dirAt(j); return Math.abs(Math.atan2(Math.sin(dj - d0), Math.cos(dj - d0))); };
    for (let j = 1; j < D; j++) {
      const sj = Math.hypot(dense[j][0] - dense[j - 1][0], dense[j][1] - dense[j - 1][1]);
      run += sj;
      if (j === D - 1) { keep(j); break; }
      /* 转过 maxTurn 时留的是上一个采样点（转到这一点之前）：留这一点的话急弯处每个顶点多转一整步（3 px 一步，半径 25 px 的弯一步就 7°） */
      if (turnAt(j) > maxTurn && j - 1 > li) { keep(j - 1); run = sj; }
      const wl = A[0][li];
      if (run >= maxSeg || turnAt(j) > maxTurn || Math.abs(A[0][j] - wl) > maxDw * Math.max(wl, 2)) { keep(j); run = 0; }
    }
    return [out, ...O];
  }

  /* ---------- 弹簧链：带状物的惯性 ----------
     N + 1 个节点，两头钉死（0 = 手，N = 梢 / 拳头：梢按调用方给的路径走，打中的时刻不变），中间各自被弹簧拉向"该在的位置" D[i]，
     越靠中段弹簧越软（K × (1 − mid·sin πf)）→ 甩出去时中段落在后面、到点时中段冲过头再弹回来，收回时带一道波。
     ribbon 只拿它算横向偏移（D[i] = [w, 0]，x = 沿法线的偏移）：节点本身钉在路上，见 ribbon 里"节点钉在路上"一段
     ten：相邻节点之间的张力（拉普拉斯项 + 同样形式的阻尼）—— 没有它每个节点是一只各自固有频率的独立振子，摆上几百 ms 相位就散开，
     相邻节点一上一下 = 手边一截细碎的锯齿（bands.py：收回末段中线 30~40° 的拐都是这个）；有张力才是一根绳，高频的节点间模态被压住。
     推进按调用方这一下的时钟 t 的差（抽打 W.t / 出拳 b.pk.t）：顿帧时 t 不动、链也不动；t 变小 = 新的一下，链从 D 重新开始 */
  function chain(N) {
    const x = new Float64Array(N + 1), y = new Float64Array(N + 1), vx = new Float64Array(N + 1), vy = new Float64Array(N + 1);
    let t0 = null;
    return {
      x, y,
      step(t, D, K, mid, zeta, g, ten = 0) {
        if (t0 == null || t < t0 - 1e-6) {
          for (let i = 0; i <= N; i++) { x[i] = D[i][0]; y[i] = D[i][1]; vx[i] = vy[i] = 0; }
          t0 = t; return;
        }
        let left = Math.min(0.1, t - t0); t0 = t;
        x[0] = D[0][0]; y[0] = D[0][1]; x[N] = D[N][0]; y[N] = D[N][1];
        const td = 0.15 * Math.sqrt(ten);
        while (left > 1e-7) {
          const h = Math.min(1 / 240, left); left -= h;
          for (let i = 1; i < N; i++) {
            const f = i / N, k = K * (1 - mid * Math.sin(Math.PI * f)), c = 2 * zeta * Math.sqrt(k);
            const lx = ten * (x[i - 1] - 2 * x[i] + x[i + 1]) + td * (vx[i - 1] - 2 * vx[i] + vx[i + 1]), ly = ten * (y[i - 1] - 2 * y[i] + y[i + 1]) + td * (vy[i - 1] - 2 * vy[i] + vy[i + 1]);
            vx[i] += (k * (D[i][0] - x[i]) - c * vx[i] + lx) * h;
            vy[i] += (k * (D[i][1] - y[i]) - c * vy[i] + g * Math.sin(Math.PI * f) + ly) * h;
            x[i] += vx[i] * h; y[i] += vy[i] * h;
          }
        }
        x[0] = D[0][0]; y[0] = D[0][1]; x[N] = D[N][0]; y[N] = D[N][1];
      },
    };
  }

  /* ---------- 带状物（P10 / P4③）：绸、鞭剑、橡皮臂、伸缩棒 ----------
     TrioFX.ribbon(Q, style)：每个角色一个句柄（建 Act 时）。style：
       'silk'   绸（G9 红绸、G13 白绸）：Q = A.whip { w, taper, amp, waves, hz, color, edge, tip? }。带宽 = w × 1.6，沿长度扭转
                （半宽 × |cos φ|，φ 沿长度转一圈多、随时间慢慢拧），翻到背面换反面色（红绸暗红、白绸淡灰蓝），受光面叠一条软光泽；
                不透明（原来整条 0.85，要离屏层，见 band 注释）；有 tip 的梢上挂一只金铃 sprite（G13，原 tip 是一截 12 × 9 px 的金线）
       'blade'  软鞭剑（G17，金属）：Q = A.whip。剑身贴图（暗边 / 斜面 / 血槽 / 一条白刃光），螺旋甩出（中线绕一圈圈的螺旋偏移，
                宽窄跟着螺旋相位翻），tip = 一截收尖的剑尖
       'arm'    橡皮臂（B12）：Q = A（atk 原样：armW / skin / skinShade / skinEdge）。肉色圆柱 + 褶纹（拉得越长褶越稀 = 拉伸纹），
                前臂粗 → 中段拉细 → 拳前鼓；路径沿 from → to 直（精特2b：伸长肢体不弯，见 draw 里的注释）
       'bamboo' 伸缩棒（G29 打狗棒）：Q = A（同上，skin 当竹色）。竹节贴图，节从梢那头量 —— 伸出去时一节节从手里冒出来
     每帧：h.draw(ctx, from, dir, to, e, t, s)
       from  根（抽打 = handPt(P)；出拳 = 手腕 pt(P, A.wrist)）
       dir   出口方向（弧度）：第一段切线 = dir（P1）；null = 直线 from → to
       to    梢的落点（抽打 = o.aim(W.u)；出拳 = 拳头此刻的位置 [fx, fy]）
       e     伸出去多少 0..1（抽打 = drawWhip 的 e；出拳传 1：拳头位置已经含伸缩）
       t     这一下的时钟（抽打 W.t；出拳 b.pk.t）—— 弹簧链按它推进
       s     体型 P.s
     h.tip() → [x, y, ang]：梢此刻在哪、朝哪（出拳：拳头按它转，替换 drawArm 里的 ang） */
  const PHB = 16;
  /* 顺滑的 |x|（0..1 → 0..1）：|cos φ| 在侧身那一刻导数跳变，宽度在那里折一下 = 带子边上一个尖角 */
  const sabs = (x) => (Math.sqrt(x * x + 0.03) - 0.1732) / 0.8417;
  function ribbon(Q, style = 'silk') {
    const N = 20, C = chain(N), TUBE = style === 'arm' || style === 'bamboo';
    let pals, texName, tipImg = null;
    if (TUBE) {
      const sk = rgbOf(Q.skin), sh = rgbOf(Q.skinShade), ed = rgbOf(Q.skinEdge);
      pals = { body: [ed, mix(sh, sk, 0.35), sk, mix(sk, WHITE, 0.7)] };
      texName = style === 'arm' ? 'skin' : 'bamboo';
    } else {
      const c = rgbOf(Q.color), lum = (c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11) / 255;
      const back = lum > 0.85 ? [196, 204, 226] : mix(c, INK, 0.38);
      pals = { front: palOf(c, 0.5, 0.5), back: palOf(back, 0.5, 0.35), dark: [INK, INK, INK, mix(INK, c, 0.3)], sheen: [WHITE, WHITE, WHITE, WHITE] };
      if (style === 'blade') pals.front = [mix(rgbOf(Q.edge), INK, 0.2), c, mix(c, WHITE, 0.55), WHITE];
      texName = style === 'blade' ? 'blade' : 'silk';
    }
    const ink = TUBE ? Q.skinEdge : Q.edge || 'rgba(40,20,10,.85)';
    /* 甩影（去规则：快的时候一条带子读成"一片扫过去的面"，不是一根线）：调用方时钟 t 的最近 SMEAR 秒里的几帧形状，淡淡地铺在本体下面 */
    const SMEAR = TUBE ? 0 : 0.05, hist = [];            // 臂 / 棒是顺着自己的轴伸缩，甩影叠在本体上看不出来（压测里却是整块面积）—— 只有绸 / 鞭剑横着扫
    const smearC = (TUBE ? mix(rgbOf(Q.skin), WHITE, 0.3) : mix(rgbOf(Q.color), WHITE, style === 'blade' ? 0.55 : 0.2)).join(',');
    let last = null;
    const faces = [];                                    // 扭转相位每档一张合成条（本句柄的颜色固定，算一次）
    const D = Array.from({ length: N + 1 }, () => [0, 0]);
    return {
      draw(ctx, from, dir, to, e, t, s = 1) {
        if (!ready()) return;
        /* 臂 / 棒是伸长的肢体 / 硬杆（精引2 物理口径）：一律沿 from → to 直着出去，不走出口方向的弯（拳头本来就在前臂延长线上：drawArm 把它放在
           "落点在前臂线上的投影"），也不加横向波 —— 精特2 收口版臂上叠了"整条弓 + 往拳头走的小波"，胶片上是一根之字折线（用户：路飞的手臂拐弯了）。
           去几何感改靠粗细（前臂 → 中段收细 → 拳头前鼓）、皮肤贴图的明暗和随拉长放稀的拉伸褶 */
        const c = TUBE ? [(from[0] + to[0]) / 2, (from[1] + to[1]) / 2, false] : ctrl(from, dir, to), tot0 = Math.hypot(to[0] - from[0], to[1] - from[1]);
        /* 该在的位置：沿路 0 → e，再加横向位移（加在 D 上，弹簧把它滤顺）：
             绸 / 剑  一道往前走的大波（甩出去时大、到点后收）+ 一层碎的三频抖（布被风吹的颤，不是一条正弦）
             竹棒     捅出去的反冲让整根轻轻弯一下（一个整体的弧，最多 1.5 % 长度、12 px），很快收直
             橡皮臂   不加 */
        /* 节点钉在路上（沿路弧长 f·e 处），弹簧链只管横向偏移 w（沿该点法线）：原来链节点在平面里各自追目标点，伸缩快时靠梢的节点
           顺着路冲过钉死的梢 → 折回成钩、收回时打结（bands.py 读数：绸 / 剑中线最大转角 149~172°，都在 81~91 % 处）。只剩横向 → 沿路的次序不会乱。
           横波的包络：根上 smoothstep（斜率 0 → 首段切线 = 出口方向；原来 sin πf 在根上斜率最大，首段偏 dir 51~60°），
           幅度再按 grow = g² 收（见下 Lsc）；
           碎抖 wob 的自变量用弧长 px（原来 f × 620：带子短时波长跟着缩到 20 多 px = 之字）。下垂：链的重力改成静态的 droop × 法线的竖直分量 */
        const amp = TUBE ? 0 : (Q.amp || 24) * (style === 'blade' ? 1.0 : 0.8), fw0 = (Q.w || 8) * s;
        const droop = style === 'silk' ? 6 : style === 'blade' ? 2 : 0;
        /* 链里存的是"横向偏移 / (此刻伸出去的长度 × g)"，g = min(1, 长度 / 300)：收回时带子变短，链上挂着的形状跟着缩（存 px 的话偏移还在、
           节点间距先缩了 → 之字），而且多缩一个 g —— 波长 ∝ 长度、幅度 ∝ 长度²，曲率与长度无关（只按长度等比缩的话，收到 120 px 时整条的波
           挤成手边半径 15 px 的弯）。短的带子近乎直 = 被拽回手里绷紧 */
        const Lsc = Math.max(1, e * tot0), g = Math.min(1, Lsc / 300), grow = g * g, B = [], NX = [], NY = [];
        for (let i = 0; i <= N; i++) {
          const f = i / N, p = bz(from, c, to, f * e), q = bz(from, c, to, Math.min(1, f * e + 0.01)), pr = bz(from, c, to, Math.max(0, f * e - 0.01));
          const dx = q[0] - pr[0], dy = q[1] - pr[1], L = Math.hypot(dx, dy) || 1;
          B.push(p); NX.push(-dy / L); NY.push(dx / L);
          let w = 0;
          if (i > 0 && i < N && style !== 'arm') {
            const sn = Math.sin(Math.PI * f), r = Math.min(1, f / 0.22), env = sn * r * r * (3 - 2 * r);
            if (style === 'bamboo') w = env * Math.min(12, tot0 * 0.015) * Math.sin(t * 30 + 0.6) * Math.exp(-t * 6);
            else w = env * grow * (amp * (1.2 - e * 0.7) * Math.sin(6.2832 * (f * (Q.waves || 1.5) - t * (Q.hz || 4))) + fw0 * (style === 'blade' ? 0.4 : 0.7) * wob(f * Lsc, t, 1.1))
                     + env * grow * droop * NY[i];
          }
          D[i][0] = w / (Lsc * g); D[i][1] = 0;
        }
        if (style === 'bamboo') C.step(t, D, 4200, 0.6, 0.7, 0);
        else if (style !== 'arm') C.step(t, D, 900, 0.82, 0.32, 0, 4000);
        const pts = [];
        /* 出手那一截：横向偏移再乘一个按弧长的 smoothstep（0 → max(40 px, 两成长度)：节点 25 px 一个，只铺 40 px 的话只盖住一个节点）—— 张力会把弯一路传到根上，乘上它根上偏移和斜率都是 0（首段沿出口方向），
           且导数连续（钉死节点的话钉住段和自由段之间是个折角） */
        for (let i = 0; i <= N; i++) { const r = Math.min(1, i / N / Math.max(40 * s / Lsc, 0.2)), w = style === 'arm' ? 0 : C.x[i] * Lsc * g * r * r * (3 - 2 * r); pts.push([B[i][0] + NX[i] * w, B[i][1] + NY[i] * w]); }
        const L = arcLen(pts), tot = L[N] || 1;
        const hw = [], phi = [];
        let W0;
        if (TUBE) {
          W0 = Q.armW * s * (1 - 0.25 * Math.min(1, tot / 500)) / 2;                     // 拉得越长越细（同旧 drawArm）
          for (let i = 0; i <= N; i++) {
            const f = i / N;
            /* 臂：前臂端粗 → 中段被拉细 → 近拳头鼓回来（肌肉被拽长的样子）+ 一道往拳头走的轻微肉浪（只动粗细、不动路径）；
               棒：竹节处略粗、整根粗细不匀一点 */
            hw.push(W0 * (style === 'arm' ? (1.05 - 0.17 * Math.sin(Math.PI * Math.min(1, f / 0.85)) + 0.2 * Math.max(0, (f - 0.8) / 0.2) ** 2)
                                            * (1 + 0.08 * Math.sin(L[i] * 0.05 - t * 26) * Math.sin(Math.PI * f))
                                          : 1 + 0.08 * wob(L[i] * 2, 0, 2.2)));
          }
        } else {
          W0 = fw0 * (style === 'silk' ? 0.8 : 0.5);
          const tp = Q.taper != null ? Q.taper : 0.5;
          for (let i = 0; i <= N; i++) {
            const f = i / N;
            /* 扭转：silk φ 每 px 转 0.014 rad（按伸出去的布量：500 px 转 1.1 圈；原来按 f 量，刚甩出去的短带子也挤满 1.1 圈，侧身处边线折得很急）、随时间拧；blade 跟着螺旋相位（宽面转到侧面时窄）。侧过去最窄只到 0.36（第一版 0.16，
               胶片上一侧身就是一根线）；沿长度的宽窄抖在样条取点之后按弧长加（波长 90 px，节点 30 px 一个采不住，会抖成锯齿） */
            const ph = style === 'blade' ? 6.2832 * (f * (Q.waves || 2) - t * (Q.hz || 4)) : 1.1 + L[i] * 0.014 + t * 2.4;
            phi.push(ph);
            hw.push(W0 * (1 - (1 - tp) * f) * (style === 'blade' ? 0.45 + 0.55 * sabs(Math.cos(ph)) : 0.36 + 0.64 * sabs(Math.cos(ph)))
                    * (i === N && !Q.tip ? 0.3 : 1));
          }
        }
        /* u：绸 / 剑从根量（纹路钉在布上）；臂从拳头量、褶距随拉长放稀；棒从梢量（节从手里冒出来） */
        const u = [];
        for (let i = 0; i <= N; i++) {
          if (style === 'arm') u.push((tot - L[i]) * 64 / (13 * s * Math.max(1, tot / 110)));
          else if (style === 'bamboo') u.push((tot - L[i]) * 64 / (30 * s));
          else u.push(L[i] * 64 / (W0 * 2.6));
        }
        /* 剑尖：顺最后一段方向多接一截收尖 */
        const tipA = Math.atan2(pts[N][1] - pts[N - 2][1], pts[N][0] - pts[N - 2][0]);
        if (style === 'blade' && Q.tip) {
          const tl = Q.tip[0] * s, tw = Q.tip[1] * s / 2;
          for (const [k, w] of [[0.5, tw * 0.85], [1, 0.4]]) { pts.push([pts[N][0] + Math.cos(tipA) * tl * k, pts[N][1] + Math.sin(tipA) * tl * k]); hw.push(w); phi.push(0); u.push(u[u.length - 1] + tl * k * 64 / (W0 * 2.6)); }
        }
        last = [pts[N][0], pts[N][1], tipA];
        /* 绸 / 剑：弹簧链节点当样条过点重新取点（smooth）—— 节点间 25~30 px，直接连是折线，波峰处折成尖角 */
        let SP = pts, SW = hw, SU = u, SF = phi;
        if (!TUBE) {
          [SP, SW, SU, SF] = smooth(pts, [hw, u, phi], 40, 0.12, 0.4);
          const SL = arcLen(SP);
          SW = SW.map((w, j) => w * (1 + 0.2 * wob(SL[j] * 1.4, t, 2.0)));
        }
        /* 甩影：先画（压在本体下面）。只画梢比这一帧挪开 6 px 以上的那几帧（停住时不花钱）。每帧一整块（sheet），只铺靠梢的 55 %
           （根几乎不动，那半截的甩影本来就看不见），沿长度由透明渐到实。每 0.03 s 记一帧、留 0.05 s = 最多 2 块（原来逐段贴图 × 4 帧 = 40 次 fill；
           整块渐变的面积开销仍不小：压测配对差值里甩影约 0.75 ms，砍掉根那半截和第 4 块） */
        if (hist.length && t < hist[hist.length - 1].t - 1e-6) hist.length = 0;
        while (hist.length && t - hist[0].t > SMEAR) hist.shift();
        for (const g of hist) {
          const ag = (t - g.t) / SMEAR, gp = g.pts, e = gp[gp.length - 1];
          if (ag <= 0 || Math.hypot(e[0] - pts[N][0], e[1] - pts[N][1]) < 6) continue;
          const gr = ctx.createLinearGradient(gp[0][0], gp[0][1], e[0], e[1]), a = (style === 'silk' ? 0.3 : 0.25) * (1 - ag);
          gr.addColorStop(0, `rgba(${smearC},0)`); gr.addColorStop(1, `rgba(${smearC},${a.toFixed(3)})`);
          sheet(ctx, gp, g.hw, gr);
        }
        if (SMEAR && (!hist.length || t - hist[hist.length - 1].t >= 0.03)) {
          const gp = [], gh = [];
          const SL = arcLen(SP), from45 = SL[SL.length - 1] * 0.45;
          for (let i = 0; i < SP.length; i++) if (SL[i] >= from45) { gp.push(SP[i]); gh.push(Math.max(SW[i] * 1.05, 2)); }
          hist.push({ t, pts: gp, hw: gh });
        }
        const body = ramp('band', texName, TUBE ? pals.body : pals.front);
        if (TUBE) { const k = thin(L, 48 * s);            // 臂 / 棒是直的（棒至多一道 12 px 的整体弯），段只用来带粗细变化
           band(ctx, k.map(i => pts[i]), k.map(i => hw[i]), k.map(i => u[i]), [{ tex: body }], ink, 1.4); return; }
        const backT = ramp('band', texName, pals.back), darkT = ramp('band', texName, pals.dark), sheenT = ramp('band', 'sheen', pals.sheen);
        /* 每段按扭转相位 φ（取两端平均）挑一张合成条：正 / 反面本体 + 侧过去压暗 + 正对光亮一条。φ 量化成 PHB 档（每档 22.5°，
           原来三遍逐段 alpha 连续变、每段 3 次 fill；现在 1 次，档间差一点点亮度，段本来就是逐段一个值） */
        const shine = style === 'blade' ? 0.5 : 0.85;
        const faceTex = (i, i1) => {
          const b = ((Math.round((SF[i] + SF[i1]) / 2 / 6.2832 * PHB) % PHB) + PHB) % PHB;
          if (!faces[b]) { const p = b * 6.2832 / PHB, f = Math.cos(p);
            faces[b] = comp([[f >= 0 ? body : backT, 1], [darkT, 0.55 * (1 - Math.abs(f)) ** 2], [sheenT, shine * Math.max(0, Math.cos(p - 0.5)) ** 3]]); }
          return faces[b];
        };
        band(ctx, SP, SW, SU, [{ tex: (j) => faceTex(j, j + 1) }], ink, 1);
        if (style === 'silk' && Q.tip) {                       // 金铃：挂在梢上、口朝下摆（顺最后一段方向 + 往下坠一点）
          tipImg = tipImg || ramp('band', 'bell', palOf(rgbOf(Q.tip[2]), 0.55, 0.6));
          const sz = Math.max(26, Q.tip[0] * s * 1.8), a = Math.atan2(Math.sin(tipA) + 1.2, Math.cos(tipA)) - Math.PI / 2;
          ctx.save(); ctx.translate(pts[N][0], pts[N][1]); ctx.rotate(a + 0.25 * Math.sin(t * 22)); ctx.drawImage(tipImg, -sz / 2, -sz * 0.22, sz, sz); ctx.restore();
        }
      },
      tip: () => last,
    };
  }

  /* ---------- 秋千绳 / 倒挂绳（P10⑤）：麻绳纹贴图带 + 一点弯 ----------
     TrioFX.rope(ctx, pts, w, fill, edge, bend)：pts 绳上的几个点（座板头 → 握绳的手 → 转轴高度，同 drawSwing / drawRopes / drawLine 的 pts），
     w 绳粗（R.w × P.s）、fill / edge 同 cfg.ropes；bend：最长那一段中点往法线方向弯多少 px（荡的时候绳子被甩弯：调用方传 −摆角速度 × 几 px，
     不传 = 直的）。纹路按弧长从第一个点量，绳子动纹路跟着动，不在绳上滑 */
  function rope(ctx, pts, w, fill, edge, bend = 0) {
    if (!ready() || pts.length < 2) return;
    let li = 0, lm = 0;
    for (let i = 0; i + 1 < pts.length; i++) { const d = Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]); if (d > lm) { lm = d; li = i; } }
    const P = [pts[0]];
    for (let i = 0; i + 1 < pts.length; i++) {
      const a = pts[i], b = pts[i + 1], n = i === li ? 10 : 1, dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1;
      for (let k = 1; k <= n; k++) { const f = k / n, o = i === li ? bend * 4 * f * (1 - f) : 0; P.push([a[0] + dx * f - dy / L * o, a[1] + dy * f + dx / L * o]); }
    }
    const L = arcLen(P), hw = P.map(() => w * 0.55), u = L.map(d => d * 64 / (w * 2.2));
    band(ctx, P, hw, u, [{ tex: ramp('band', 'rope', palOf(rgbOf(fill), 0.5, 0.45)) }], edge, 1.2, false);
  }

  /* ---------- 水柱（P4②，B1~B4 atk.jet draw 'stream'）----------
     水滴还是引擎的（trio.js stepJet / stepDrops：出口、仰角、断开、打中全照旧），这里只换画法 —— 替换 crew.js drawStream：
     连着的水滴连成一条贴图带（半透明水身 + 折射暗边 + 断续高光），贴图横坐标按水滴序号走（u = seq × 45）→ 纹路跟着水往前流；
     断开的水滴画成带高光的水珠 sprite（顺速度拉长），水沫是小水珠；出口：每三滴一小团水雾、偶尔一颗甩出去的水珠和一点闪光。
     宽度 / 断开 / 水沫三条规则与 crew.js WATER 逐字相同（只换画法，命中手感不变）。落点溅射走 onDrip（RECIPE.water.drip，第一批已换）。
     h = TrioFX.stream()；drawJets 里 J.draw === 'stream' 分支：h.draw(ctx, jets, b && b.jm, dir)
       dir：出口方向（弧度，= 枪口此刻的仰角换成屏幕角 F > 0 ? −b.ja : π + b.ja）。给了就让喷口 → 第一滴那一段先沿 dir 出去（P1） */
  const MIST = 0.2;
  const WATER = { w0: 7, w1: 20, grow: 0.3, a1: 0.55, breakT: 0.14, brk: 0.16, mist: 0.35 };
  function stream(o = {}) {
    const pal = o.pal || PAL.water;
    let seen = -1;
    const wOf = (d) => WATER.w0 + (WATER.w1 - WATER.w0) * Math.min(1, d.t / WATER.grow);
    const aOf = (d) => 1 - (1 - WATER.a1) * Math.min(1, d.t / WATER.grow);
    return {
      draw(ctx, ps, m, dir) {
        if (!ready()) return;
        const n = ps.length, link = (p, d) => d.seq === p.seq + 1 && Math.hypot(d.x - p.x, d.y - p.y) <= 60 && !(d.t > WATER.breakT && d.j < WATER.brk);
        const tex = ramp('band', 'water', pal), hl = ramp('band', 'sheen', [pal[3], pal[3], pal[3], pal[3]]), linked = new Set(), runs = [];
        let run = n ? [ps[n - 1]] : [];
        for (let i = n - 1; i >= 1; i--) {
          if (link(ps[i - 1], ps[i])) run.push(ps[i - 1]);
          else { runs.push(run); run = [ps[i - 1]]; }
        }
        if (run.length) runs.push(run);
        const head = n && m && Math.hypot(ps[n - 1].x - m[0], ps[n - 1].y - m[1]) < 60 ? ps[n - 1] : null;
        const lines = [];
        for (const r of runs) {
          /* 去规则：每滴水自带一个粗细（鼓包随水往前走，不是一根等粗的管子）和一点横向偏移（越老越大：水柱在空中松开、抖）。
             每三滴取一个点：水滴间距约 23 px，一段 69 px 的直段贴在抛物线上（顶点曲率半径 V² / G ≈ 1700 px）弓高不到 0.4 px，看不出折；
             段数是逐滴的三分之一（压测配对差值里约 0.25 ms：每段一次 fill 的固定开销）。
             所以鼓包 / 横摆的频率按三滴一个采样定：主鼓包 0.55 rad / 滴（11 滴一个，每个鼓包约 4 个点），原来 1.31（4.8 滴）隔点取是一胖一瘦的锯齿 */
          const k = r.filter((d, i) => i % 3 === 0 || i === r.length - 1);
          const pts = k.map(d => { const v = Math.hypot(d.vx, d.vy) || 1, o = wOf(d) * 0.22 * Math.sin(d.seq * 0.4 + 0.4) * Math.min(1, d.t / 0.15);
                                   return [d.x - d.vy / v * o, d.y + d.vx / v * o]; });
          const hw = k.map(d => wOf(d) * 0.58 * (1 + 0.24 * Math.sin(d.seq * 0.55) + 0.12 * Math.sin(d.seq * 0.23 + 1.7))), u = k.map(d => -d.seq * 45);
          if (r[0] === head) {                                 // 接到喷口；给了 dir 就先沿 dir 出去一小段
            const d0 = Math.hypot(head.x - m[0], head.y - m[1]);
            if (dir != null && d0 > 6) { pts.unshift([m[0] + Math.cos(dir) * d0 * 0.45, m[1] + Math.sin(dir) * d0 * 0.45]); hw.unshift(WATER.w0 * 0.55); u.unshift(-(head.seq + 0.55) * 45); }
            pts.unshift([m[0], m[1]]); hw.unshift(WATER.w0 * 0.5); u.unshift(-(head.seq + 1) * 45);
          }
          if (pts.length < 2) continue;
          for (const d of r) linked.add(d);
          lines.push(smooth(pts, [hw, u], 70));            // 三滴一个点 + 横摆：直接连在横摆处折角，过样条
        }
        if (lines.length) {
          /* 水身 + 一条断续的白高光（sheen 条的亮丝沿 u 走 = 跟着水流）合成一张条，每段铺一次 + 折射暗边（实体靠轮廓：第一版没边，
             亮地板上是一根淡管子）。水身贴图本身半透明，直接画在 ctx 上（原来先画离屏层再 0.95 贴回：层只多一次整块搬运，接缝一样） */
          const edge = `rgba(${pal[0].join(',')},.6)`, wt = comp([[tex, 1], [hl, 0.7]]);
          for (const [pts, hw, u] of lines) band(ctx, pts, hw, u, [{ tex: wt }], edge, 1.3);
        }
        /* 断开的水珠、水沫：贴图水滴，顺速度画（头在前） */
        const dropA = ramp('frag', 'drop0', pal), dropB = ramp('frag', 'drop1', pal);
        ctx.save();
        const T = ctx.getTransform();
        for (const d of ps) {
          const sp = Math.atan2(d.vy, d.vx);
          if (!linked.has(d) || d.j < WATER.brk) {
            const w = wOf(d) * (1.5 + 0.6 * ((d.j * 7) % 1)) * CELL;
            ctx.setTransform(T); ctx.translate(d.x, d.y); ctx.rotate(sp); ctx.globalAlpha = aOf(d);
            ctx.drawImage(dropA, -w * 0.6, -w / 2, w, w);
          }
          if (d.t >= WATER.breakT && d.j <= MIST) {          // 水沫只画 j ≤ 0.2 的（crew.js 是 0.35：每颗一次 drawImage，水柱的水滴 sprite 一帧 0.4 ms）
            const k = d.j / MIST, off = (k - 0.5) * 2 * wOf(d) * 1.3, w = (5 + 6 * k) * CELL, vl = Math.hypot(d.vx, d.vy) || 1;
            ctx.setTransform(T); ctx.translate(d.x - d.vy / vl * off, d.y + d.vx / vl * off); ctx.rotate(sp); ctx.globalAlpha = 0.9;
            ctx.drawImage(dropB, -w * 0.6, -w / 2, w, w);
          }
        }
        ctx.restore();
        /* 出口：按新出来的水滴序号放（引擎每帧出几滴就放几次，顿帧时不出水也就不放） */
        if (m && n) {
          const nw = ps[n - 1];
          if (nw.seq < seen) seen = -1;                        // 换了一个人 / 重开：序号从头
          for (const d of ps) {
            if (d.seq <= seen) continue;
            const a = dir != null ? dir : Math.atan2(d.vy, d.vx);
            if (d.seq % 4 === 0) spawn({ m: 'spr', img: ramp('dust', 'dust' + (d.seq % 4), pal), x: m[0] + Math.cos(a) * 8, y: m[1] + Math.sin(a) * 8,
              vx: Math.cos(a) * 160 + rr(-30, 30), vy: Math.sin(a) * 160 - 20, drag: 0.9, w: rr(26, 40), s0: 0.5, s1: 1.2, life: 0.28, a: 0.35, fo: 0.6 });
            if (d.j > 0.86) { const b = a + rr(-0.35, 0.35), sp = rr(300, 520);
              spawn({ m: 'vel', img: dropB, x: m[0], y: m[1], vx: Math.cos(b) * sp, vy: Math.sin(b) * sp, g: 1100, drag: 0.99, w: rr(9, 13) * CELL, h: rr(9, 13) * CELL * 0.62,
                      stretch: 0.0012, life: rr(0.25, 0.4), fo: 0.3 }); }
            if (d.seq % 7 === 0) spawn({ m: 'spr', img: glow('flare', pal), x: m[0], y: m[1], w: 34, s0: 1, s1: 0.5, life: 0.06, fi: 0, a: 0.9, fo: 0.6 });
          }
          seen = nw.seq;
        }
      },
    };
  }

  /* ---------- 喷雾（G1~G3 防狼喷雾 atk.jet draw 'mist'）：替换 crew.js drawMist ----------
     每个雾团画一张尘团贴图（上亮下暗、边被噪声啃软 = 有体积，不是平涂圆）、出口小、越飞越胀越淡；出口每四团甩几颗辣椒水珠、一点闪光。
     h = TrioFX.mist({ life: J.life })；h.draw(ctx, jets, b && b.jm, dir)。落点溅射：RECIPE.pepper.drip（下面新配方，onDrip 已经调它） */
  const PEPPER = [[150, 46, 16], [255, 140, 70], [255, 200, 150], [255, 242, 226]];
  function mist(o = {}) {
    const L = o.life || 0.8, pal = o.pal || PEPPER;
    let seen = -1;
    return {
      draw(ctx, ps, m, dir) {
        if (!ready()) return;
        ctx.save();
        for (const d of ps) {
          const u = Math.min(1, d.t / L), r = (7 + 22 * Math.sqrt(u)) * 2.3, a = (1 - u * u) * 0.3;
          if (a <= 0.01) continue;
          ctx.globalAlpha = a;
          ctx.drawImage(ramp('dust', 'dust' + (d.seq % 4), pal), d.x - r, d.y - r, r * 2, r * 2);
        }
        ctx.restore();
        if (m && ps.length) {
          const nw = ps[ps.length - 1];
          if (nw.seq < seen) seen = -1;
          for (const d of ps) {
            if (d.seq <= seen) continue;
            const a = dir != null ? dir : Math.atan2(d.vy, d.vx);
            if (d.seq % 4 === 0) { const b = a + rr(-0.3, 0.3), sp = rr(380, 620);
              spawn({ m: 'vel', img: frag('drop1', pal), x: m[0], y: m[1], vx: Math.cos(b) * sp, vy: Math.sin(b) * sp, g: 500, drag: 0.97, w: rr(8, 11) * CELL, h: rr(8, 11) * CELL * 0.62,
                      stretch: 0.0012, life: rr(0.2, 0.32), fo: 0.4 }); }
            if (d.seq % 9 === 0) spawn({ m: 'spr', img: glow('flare', pal), x: m[0], y: m[1], w: 30, s0: 1, s1: 0.5, life: 0.06, fi: 0, a: 0.85, fo: 0.6 });
          }
          seen = nw.seq;
        }
      },
    };
  }

  /* ---------- 喷（B20 酒雾，atk.kind 'spray'：一团团 puff 沿路飞）：替换 drawShot 的 'puff' 分支 ----------
     h = TrioFX.spray(A.spray)
     出一团（stepFx 里 shots.push 'puff' 那一刻）：h.emit(h0, a)   h0 出口点、a 这一团的出口方向（弧度）→ 嘴边一点酒沫、偶尔一颗酒珠
     画（drawShot 'puff'）：h.puff(ctx, s)                       s 原样（x, y, t, life, vx, vy, j）
     路：puff 的控制点 c 用 TrioFX.ctrl(h0, dir, p2)（dir = 出口方向）即首段切线 = dir（P1）；后排要翻头顶的仍用 over() */
  function spray(Q) {
    const c = Q.color || [235, 195, 110], pal = palOf(c, 0.55, 0.55), R0 = Q.r || 14;
    return {
      emit(h0, a) {
        if (!ready()) return;
        if (R() < 0.35) { const b = a + rr(-0.25, 0.25), sp = rr(420, 700);
          spawn({ m: 'vel', img: frag('drop1', pal), x: h0[0], y: h0[1], vx: Math.cos(b) * sp, vy: Math.sin(b) * sp, g: 700, drag: 0.98, w: rr(10, 14) * CELL, h: rr(10, 14) * CELL * 0.62,
                  stretch: 0.0012, life: rr(0.25, 0.4), fo: 0.4 }); }
        if (R() < 0.25) spawn({ m: 'spr', img: ramp('dust', 'dust' + ((R() * 4) | 0), pal), x: h0[0], y: h0[1], vx: Math.cos(a) * 90, vy: Math.sin(a) * 90 - 20, drag: 0.9,
                                w: rr(30, 44), s0: 0.5, s1: 1.1, life: 0.25, a: 0.4, fo: 0.6 });
      },
      puff(ctx, s) {
        if (!ready()) return;
        const u = s.t / s.life, r = R0 * (0.8 + 2.6 * u) * 2.2, a = 0.78 * Math.pow(1 - u, 1.2);
        if (a <= 0.01) return;
        ctx.save();
        ctx.globalAlpha = a;
        ctx.drawImage(ramp('dust', 'dust' + ((s.j * 4) | 0), pal), s.x - r, s.y - r, r * 2, r * 2);
        if (u < 0.5) {                                        // 团里裹着两颗酒珠，顺着飞的方向
          const sp = Math.atan2(s.vy || 0, s.vx || 1), w = 11 * CELL, img = frag('drop0', pal);
          ctx.globalAlpha = 1 - 2 * u;
          for (const k of [-1, 1]) {
            ctx.save(); ctx.translate(s.x - Math.sin(sp) * k * r * 0.25 * (s.j + 0.3), s.y + Math.cos(sp) * k * r * 0.25 * (s.j + 0.3)); ctx.rotate(sp);
            ctx.drawImage(img, -w * 0.6, -w / 2, w, w * 0.62); ctx.restore();
          }
        }
        ctx.restore();
      },
    };
  }

  /* ---------- 剑气飞行段（P4④，B23 G14 atk.kind 'slash'）----------
     TrioFX.qi(from, dir, to, rgb, o) → 飞行秒数 T。从 from（刀尖 / 剑尖）沿 dir 甩出一道月牙剑气（凸面朝前、身后三道残影 + 沿路光粒和火花），
     T 秒（默认 0.12）飞到 to，到了就地展开刀光序列帧（第一批的 slash()，o.ang / o.len / o.life 原样给它）。
     o: { T, len（A.slash.len）, ang（s.ang）, life（A.slash.life）, delay（第几道：i × gap）, slash: false = 只飞不展开 }
     引擎：fire() 里 slash 分支每道照旧 push，但 s.t 起点再往前挪 T（打中仍在"刀光开始 0.05 s 后"= 剑气到了之后）；
     那一道 s.t 跨过 −T 的那一帧调 qi（from = handPt(P)，to = o.aim(s.u)）—— 刀光由 qi 到点自己放，drawShot 'slash' 不再画 */
  function qi(from, dir, to, rgb, o = {}) {
    if (!ready()) return 0;
    const T = o.T || 0.12, pal = palOf(rgb, 0.7, 0.6), c = ctrl(from, dir, to), len = o.len || 230, w = len * 0.78, h = w * 160 / 256, dl = o.delay || 0;
    spawn({ m: 'fly', rgb, tex: ramp('beam2', 'bodyB', pal), tex2: ramp('beam2', 'midB', pal), path: [from[0], from[1], c[0], c[1], to[0], to[1]], T, x: from[0], y: from[1], w, h, life: T, a: 1, fi: 0, fo: 0.01, delay: dl });
    spawn({ m: 'spr', img: glow('flare', pal), x: from[0], y: from[1], w: 90, s0: 1.2, s1: 0.5, life: 0.08, fi: 0, a: 1, fo: 0.6, delay: dl, z: 1 });   // 出刀一闪
    for (let j = 1; j <= 6; j++) {                       // 沿路：按剑气经过的时刻错开出生，留在身后往两侧散
      const e = j / 7, k = e * (0.6 + 0.4 * e), p = bz(from, c, to, k), q = bz(from, c, to, Math.min(1, k + 0.02)), a = Math.atan2(q[1] - p[1], q[0] - p[0]);
      for (const sd of [j % 2 ? -1 : 1]) {                // 每步一颗、左右交替（原来 8 步 × 两侧：三道剑气同屏 48 颗光粒，压测里粒子是第二批增量的大头）
        const sp = rr(40, 120);
        spawn({ m: 'spr', img: glow('mote', pal), x: p[0], y: p[1], vx: Math.cos(a + sd * 1.571) * sp - Math.cos(a) * 40, vy: Math.sin(a + sd * 1.571) * sp - Math.sin(a) * 40, drag: 0.93,
                w: rr(12, 20), s0: 1, s1: 0.3, life: rr(0.22, 0.34), a: 1, fo: 0.4, delay: dl + e * T });
      }
      if (j % 3 === 1) spawn({ m: 'vel', img: glow('spark', pal), x: p[0], y: p[1], vx: -Math.cos(a) * rr(120, 260), vy: -Math.sin(a) * rr(120, 260), drag: 0.95, g: 200,
                         w: rr(16, 24), h: rr(5, 7), stretch: 0.0015, life: rr(0.12, 0.2), fo: 0.5, delay: dl + e * T });
    }
    if (o.slash !== false) slash(to[0], to[1], o.ang != null ? o.ang : Math.atan2(to[1] - c[1], to[0] - c[0]) + Math.PI / 2, len, rgb, o.life || 0.45, dl + T);
    return T;
  }

  /* ---------- 飞行物拖尾（G16 狐火火尾、G15 项链 / G20 月牙等小件拖光）----------
     h = TrioFX.trail(TrioFX.TRAIL.fox | gem | moon | TrioFX.trailLook(rgb, 'fire' | 'glint'))
     stepShot 里飞行那段算完 s.x / s.y 之后（含打中弹开、钉住之后，用来让尾巴淡完）：h.track(s, dt)
     drawShot 里画这件东西**之前**：h.draw(ctx, s)          —— 尾巴压在物件下面
     记录挂在 s._fxTr 上（引擎不用管）。尾巴沿实际飞过的点画，首段切线就是飞行方向（P1 的 dir 由路径本身决定：throw 的控制点用 TrioFX.ctrl） */
  const TRAIL = {
    fox: { pal: [[16, 34, 120], [40, 140, 255], [140, 226, 255], [236, 252, 255]], w: 34, len: 0.17, fire: true },          // 青蓝狐火：火舌往上窜
    gem: { pal: [[14, 30, 110], [60, 120, 255], [170, 210, 255], [255, 255, 255]], w: 18, len: 0.14, fire: false },          // 心形蓝宝石项链
    moon: { pal: [[110, 60, 10], [255, 190, 40], [255, 236, 140], [255, 255, 240]], w: 20, len: 0.14, fire: false },         // 金月牙镖
  };
  const trailLook = (rgb, kind = 'glint', w) => ({ pal: palOf(rgb, 0.6, 0.6), w: w || (kind === 'fire' ? 30 : 14), len: kind === 'fire' ? 0.17 : 0.14, fire: kind === 'fire' });
  function trail(look) {
    return {
      track(s, dt) {
        if (!ready()) return;
        const H = s._fxTr || (s._fxTr = { pts: [], t: 0, acc: 0 });
        H.t += dt;
        const flying = s.fall == null && s.stuck == null;
        if (flying) {
          H.pts.push([s.x, s.y, H.t]);
          H.acc += dt * (look.fire ? 30 : 16);         // 每秒几颗火星 / 闪光（原来 70 / 20：一颗粒子软渲染约 37 µs，狐火一飞同屏多二十颗）
          while (H.acc >= 1) {
            H.acc -= 1;
            if (look.fire) spawn({ m: 'spr', img: glow('mote', look.pal), x: s.x + rr(-6, 6), y: s.y + rr(-6, 6), vx: -(s.vx || 0) * 0.08 + rr(-30, 30), vy: -(s.vy || 0) * 0.08 - rr(60, 150),
                                   g: -160, drag: 0.94, w: rr(17, 30), s0: 1, s1: 0.2, life: rr(0.22, 0.38), a: 1, fo: 0.5 });
            else spawn({ m: 'spr', img: glow('flare', look.pal), x: s.x + rr(-8, 8), y: s.y + rr(-8, 8), vx: rr(-20, 20), vy: rr(-20, 20), drag: 0.9,
                         w: rr(14, 22), s0: 1, s1: 0.3, life: rr(0.22, 0.34), flip: 14, rot: R(), a: 1, fo: 0.5 });
          }
        }
        while (H.pts.length && H.t - H.pts[0][2] > look.len) H.pts.shift();
      },
      draw(ctx, s) {
        const H = s._fxTr;
        if (!H || H.pts.length < 2 || !ready()) return;
        const pts = [], hw = [], ag = [];
        for (let i = H.pts.length - 1; i >= 0; i--) {
          const k = 1 - (H.t - H.pts[i][2]) / look.len;
          if (k <= 0) break;
          pts.push([H.pts[i][0], H.pts[i][1]]); hw.push(look.w / 2 * Math.pow(k, 0.8)); ag.push(1 - k);
        }
        if (pts.length < 2) return;
        /* 去规则：尾巴越老越往两边飘（wob 横向位移 × 年龄）、宽窄沿长度抖 —— 第一版是一根等宽渐细的光管，胶片上读成"画了条线" */
        const L = arcLen(pts), n = pts.length, P = [];
        for (let i = 0; i < n; i++) {
          const j0 = Math.max(0, i - 1), j1 = Math.min(n - 1, i + 1), dx = pts[j1][0] - pts[j0][0], dy = pts[j1][1] - pts[j0][1], dl = Math.hypot(dx, dy) || 1;
          const o = look.w * (look.fire ? 0.7 : 0.45) * ag[i] * wob(L[i] * 2.2, H.t, 0.5);
          P.push([pts[i][0] - dy / dl * o, pts[i][1] + dx / dl * o]);
          hw[i] *= 1 + (look.fire ? 0.45 : 0.3) * wob(L[i] * 3, H.t, 2.4);
        }
        const u0 = L.map(d => d * 1.6 + H.t * (look.fire ? 700 : 300));
        const [SP, halo, u] = smooth(P, [hw.map(w => w * 1.6), u0], 40, 0.25);      // 一帧一个点 + 横飘：低帧率 / 飞得快时点稀，直接连有折角。软光带、没有墨线：14° 一折看不出
        const tex = ramp('band', 'trail', look.pal), flow = ramp('beam2', look.fire ? 'bodyB' : 'midB', look.pal);
        /* 外面一圈软光（0.4）+ 本体（生图能量流 + 一缕亮丝，占中间 1 / 1.6）合成一张条，按外晕的宽铺一次（原来三遍 + 离屏层；
           外晕原来 1.9 倍宽，最外一圈贴图本来就近乎透明，收到 1.6 少铺三成面积） */
        ctx.save(); ctx.globalAlpha *= look.fire ? 1 : 0.9;
        band(ctx, SP, halo, u, [{ tex: comp([[tex, 0.4], [flow, 1, 1 / 1.6], [tex, 1, 1 / 1.6]]) }]);
        ctx.restore();
      },
    };
  }

  /* ---------- P11 花瓣：密度 / 范围上限 ----------
     TrioFX.petals({ max, R, life, ...}) → 一份 petal 配方（同签名）。
       max   主体花瓣最多几片（默认 14；余烬另算，最多 max / 3）—— 旧的 22 × s，s 1.7 时 37 片
       R     离命中点最远几 px（默认 200）：最后四分之一淡出、出界即收（粒子的 lim）—— 旧的飞到 HUD、窗户、画外
       life  [短, 长] 秒（默认 [0.55, 0.8]）—— 旧的 1.3 ~ 2.4 s
       pal   [主色, 深色]（默认粉 / 深粉）；shapes 用哪几张花瓣格
     TrioFX.RECIPE.petal 就是默认值那一份；要按人换（G18 红缨一朵花、G26 蝴蝶翅）再 petals({ pal: ... }) 另挂一个名字 */
  function petals(o = {}) {
    const max = o.max || 14, Rm = o.R || 200, lf = o.life || [0.55, 0.8], P1 = (o.pal || [PAL.petal, PAL.petalDeep]);
    const shapes = o.shapes || ['petal0', 'petal1', 'petal2'];
    const pal3 = [P1[0], P1[0], P1[1]];
    return layered({
      tint: o.tint || [255, 214, 226],
      flash: (x, y, side, s) => flash(x, y, s, P1[0], { side }),
      body(x, y, side, s) {
        const k = kk(s), nb = Math.min(max, n(11, s));
        for (let i = 0; i < nb; i++) {
          const [vx, vy] = fan(side, 2.5, 160 * k, 380 * k, 140);
          spawn({ m: 'spr', img: frag(shapes[i % shapes.length], pal3[i % 3]), x: x + rr(-1, 1) * 24, y: y + rr(-1, 1) * 30, vx, vy, g: 160, drag: 0.975, sway: rr(30, 50),
                  w: rr(30, 42) * CELL, life: rr(lf[0], lf[1]), rot: R() * 6.283, vrot: rr(-3.5, 3.5), flip: 3.2, a: 1, fo: 0.35, lim: Rm });
        }
        sparks(x, y, side, s, Math.min(6, n(5, s)), PAL.gold);
      },
      ember(x, y, side, s) {
        const ne = Math.min(Math.ceil(max / 3), n(3, s));
        for (let i = 0; i < ne; i++) {
          const a = R() * 6.283, sp = rr(40, 120);
          spawn({ m: 'spr', img: frag(shapes[1 + (i % 2)], i % 2 ? P1[1] : P1[0]), x: x + rr(-40, 40), y: y + rr(-30, 30), vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 30, g: 70, drag: 0.97,
                  sway: rr(20, 35), w: rr(18, 24) * CELL, life: rr(lf[0], lf[1]) * 1.1, rot: R() * 6.283, vrot: rr(-2.5, 2.5), flip: 2.5, delay: rr(0.04, 0.12), a: 1, fo: 0.4, lim: Rm * 0.8 });
        }
      },
    });
  }

  /* ---------- 尘土（P8）---------- */
  /* 落地：左右两团往外散（0.35 s 主体，尾巴再拖一点），中间一圈贴地的尘环、几颗小石子蹦一下。
     尘团贴图 128 格里烟只占中间六成，尺寸按格子写（第一版按烟本身写 46~74，胶片上是脚边两小撮，读不出"砸地"） */
  function land(x, y, s = 1) {
    if (!ready()) return;
    const k = Math.min(1.6, s);
    for (const d of [-1, 1]) {
      for (let i = 0; i < 6; i++) {
        const sp = rr(90, 300) * k;
        spawn({ m: 'spr', img: ramp('dust', 'dust' + (i % 4), PAL.dust), x: x + d * rr(8, 30) * k, y: y - rr(4, 18) * k,
                vx: d * sp, vy: -rr(20, 90) * k, g: 30, drag: 0.9, w: rr(90, 150) * k, s0: 0.5, s1: 1.3,
                life: rr(0.38, 0.6), a: 0.9, fo: 0.6 });
      }
    }
    wave(PAL.dust, { x, y, s0: 30 * k, s1: 170 * k, life: 0.32, a: 0.7, sq: 0.22 });
    for (let i = 0; i < 6; i++) {
      const d = R() < 0.5 ? -1 : 1;
      spawn({ m: 'spr', img: frag('shard' + (i % 2), PAL.grit), x: x + rr(-20, 20), y: y - 4, vx: d * rr(60, 200), vy: -rr(140, 300), g: 1400, drag: 0.99,
              w: rr(10, 15) * CELL, life: rr(0.3, 0.45), rot: R() * 6.28, vrot: rr(-15, 15), a: 1, fo: 0.3 });
    }
  }
  /* 滑行 / 冲刺 / 骑：接触点每秒 |vx|/40 团尘（封顶 16）往身后翻起、一半带一颗砂粒，速度越快越密。
     尘团是这里最大的贴图，第一版 |vx|/18（600 px/s 时每秒 33 团、一条滑行同时挂 15 团）在压测里是粒子绘制最贵的一项；
     一团活 0.45 s、胀到 1.4 倍，每秒十几团已经连成一条 */
  function skid(st, x, y, vx, dt, s = 1) {
    if (!ready()) return;
    const sp = Math.abs(vx);
    if (sp < 40) return;
    const k = Math.min(1.6, s), back = vx > 0 ? -1 : 1;
    st._fxSkid = (st._fxSkid || 0) + dt * Math.min(16, sp / 40);
    while (st._fxSkid >= 1) {
      st._fxSkid -= 1;
      spawn({ m: 'spr', img: ramp('dust', 'dust' + ((R() * 4) | 0), PAL.dust), x: x + rr(-10, 10), y: y - rr(2, 10),
              vx: back * rr(20, 90) + vx * 0.15, vy: -rr(20, 70), g: -10, drag: 0.92, w: rr(60, 100) * k, s0: 0.5, s1: 1.4,
              life: rr(0.35, 0.55), a: 0.8, fo: 0.6 });
      if (R() < 0.5) spawn({ m: 'spr', img: frag('shard' + ((R() * 2) | 0), PAL.grit), x, y: y - 3, vx: back * rr(40, 160), vy: -rr(80, 200), g: 1300,
                             w: rr(7, 10) * CELL, life: rr(0.25, 0.4), rot: R() * 6.28, vrot: rr(-15, 15), a: 1, fo: 0.3 });
    }
  }

  function clear() { while (act.length) pool.push(act.pop()); }

  return { load, ready, update, draw, clear, count: () => act.length, RECIPE, beam, slash, land, skid, PAL, palOf, ramp, setScheme, scheme: () => SCHEME,
           ctrl, ribbon, rope, stream, mist, spray, qi, trail, TRAIL, trailLook, petals };
})();
