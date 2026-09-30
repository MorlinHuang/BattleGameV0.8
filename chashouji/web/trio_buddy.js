/* trio_buddy.js —— 哥们侧（右，灭迹党，打女生）三人组的角色数据 + 10 组搭配。**美术维护**，引擎在 trio.js。
 * 怎么出一个人、每个字段什么意思：docs/三人组角色规范.md。名单与分组：docs/三人组30人名单.md。
 * 坐标：at 是 960×1334 版面上的屏幕像素（GROUND 1195 = 男女主脚底，1334 以下直播时被评论区盖着）；
 * 贴图点（anchor / pivot / hold / flex …）是图集里一格的像素（v14/trio/preview/<名>_frames.png 上量，旧的单张立绘是 <名>_grid.png）。
 */
'use strict';

const TRIO_BUDDY = {
  /* 后排地面的人 = crew.js Buddy 的第几个形象（Buddy.skins 的下标）：B1 冲浪男 skate1 / B2 金箍浪子 skate4 / B3 贝勒 skate5 / B4 八神 skate7 */
  ground: { B1: 0, B2: 1, B3: 2, B4: 3 },

  cast: {
    /* ---- 帧序列（新标准） ---- */
    B21: {      // 樱木（红发篮球少年）：右下角腾空扑地 → 砸地 → 贴地滑进来，趴着甩 3D 篮球，砸中弹开
      face: -1,
      sheet: { src: 'assets/trio/B21_sakura.webp', cell: [555, 208], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'dive', 'flop', 'slide', 'idle2'] },
      anchor: [300.1, 199.2], at: [712, 1328, 0.95], pivot: [300, 199],   // 整个人在画面里：脚尖到 x 955、手到 428、最低点（follow 帧第 205 行）1333.6（旧立绘 812 × 1.05 脚伸出右沿 ~100px，脚翘看不见）
      leanK: 0,   // 趴着的人不整体前后倾：绕肚皮转会把贴地的腿翘起来，读成一张图在转；蓄力 / 出手全靠帧
      depth: 1.3, recipe: 'thud',
      enter: { kind: 'dive', seq: [['dive', 0.3], ['flop', 0.1, 'land'], ['slide', 9]], h: 150, air: 0.3, sq: 0.12 },
      exit: { frame: 'slide' },
      idle: { frame: 'idle', breathe: [0.022, 0.9, 0] },   // 趴着：只竖向起伏（背一起一伏），不横向补；0.9 次/秒 = 两次出手之间（gap 0.45~0.8 秒 + 收势）做完一口气
      /* 两只脚懒洋洋地一翘一翘：小腿中段钉住（'l' 左边），往右越翘越高 */
      flex: { idle: [[395, 100, 555, 205, 'l', 6, 0.7]], wind: [[395, 100, 555, 205, 'l', 6, 0.7]], follow: [[395, 100, 555, 205, 'l', 6, 0.7]] },
      atk: { kind: 'throw', item: 'bball', r: 34, atlas: { src: 'assets/trio/prop_basketball.webp', n: 36, cols: 6, cell: 104, scale: 1.07 },
             seq: [['wind', 0.28], ['throw', 0.1, 'fire'], ['follow', 0.26]],
             hold: { idle: [86, 146], wind: [178, 18], throw: [30, 84] },
             T: 0.5, arc: 0.3, spin: 6.3, idleSpin: 1.6, stretch: 0, gap: [0.45, 0.8], onHit: 'bounce' },
    },
    B27: {      // 食神大厨：从右下角蹲着滑出来刹住，弓步蹲着把"濑尿牛丸"一弹，砸中弹开、爆一滩肉汁（splash）
      face: -1,
      sheet: { src: 'assets/trio/B27_chef.webp', cell: [420, 281], cols: 4, names: ['idle', 'wind1', 'throw', 'follow', 'slide', 'skid', 'wind', 'idle2'] },
      /* 锚点 = 两脚中间的地面。整个人在 x 543~957；最低点（throw / wind 帧第 277 行）屏幕 y 1333.5。
         剪影面积 2.97 万（樱木 2.65 万 +12%，同槽位 ±15% 以内） */
      anchor: [210.2, 268.5], at: [750, 1325, 1], pivot: [210, 268],
      leanK: 0,     // 弓步两脚都踩着地，不能整体前后倾：绕两脚中间转 0.045 rad，前脚（离转轴 160px）就翘起 5.6px（drift.py 实测）
      depth: 1.3, recipe: 'splash',
      enter: { kind: 'slide', seq: [['slide', 0.5], ['skid', 0.15, 'land'], ['idle', 9]], sq: 0.1 },   // 张开双臂贴地滑 → 手拍地刹住（压扁）→ 待机
      exit: { frame: 'slide' },
      idle: { frame: 'idle', breathe: [0.018, 0.9, 0] },   // 弓步两脚隔得远：横向补偿给 0，不然脚跟着左右挪
      /* 腰上那串 5 颗牛丸（定妆图上的认人点）：单独一层挂在腰带上，人前（z 1）晃。动作条里特意没画它 */
      parts: [{ src: 'assets/trio/B27_skewer.webp', pivot: [7, 2], z: 1,
                at: { idle: [194, 163, 0], wind1: [194, 163, 0], throw: [196, 160, 0.25], follow: [194, 163, 0], slide: [196, 163, 0.5],
                      skid: [196, 163, 0.3], wind: [192, 163, -0.1], idle2: [194, 163, 0] },
                sway: [0.16, 1.1, 0] }],
      atk: { kind: 'throw', item: 'meatball', r: 18, atlas: { src: 'assets/trio/prop_meatball.webp', n: 36, cols: 6, cell: 68, scale: 1.27 },
             seq: [['wind', 0.3], ['throw', 0.1, 'fire'], ['follow', 0.3]],
             hold: { idle: [80, 76], wind: [120, 52], throw: [12, 82] },
             T: 0.5, arc: 0.35, spin: 6.3, idleSpin: 1.6, stretch: 0.03, gap: [0.5, 0.9], onHit: 'bounce' },
    },

    /* B5 是后排地面的样板（引擎负责人 2026-09-30 临时写在这里，哥们美术接手后照规范维护）。素材：v14/trio/tools/samples/B5_jkd */
    B5: {       // 截拳道：从右边画外晃着双节棍走进来，站定摆格斗架；连打——双节棍左右抡，一串棍影砸到她身上，"啊哒"
      face: -1,
      sheet: { src: 'assets/trio/B5_jkd.webp', cell: [423, 482], cols: 4, names: ['idle', 'wind', 'hitA', 'hitB', 'walk1', 'walk2', 'walk3', 'taunt'] },
      anchor: [260.7, 478.1], at: [740, 1086, 0.83], pivot: [260, 478], leanK: 0,   // 站在男生身后右边、比主角小一圈（同 crew.js 后排的透视）
      /* 原 [800, 1158, 0.85]：同组 B24 坐在右下角，头顶和举起的磁带到 y 1038，比 B5 的脚底还高，横着挪到 x 650 也分不开（剪影重叠 ≥ 600px）。
         改成往左 60、往后排退 72（脚底 1086，仍在地板上），缩一点点：B5 在场五帧 × B24 在场六帧 + 手里的磁带，剪影逐对相交为 0 */
      depth: 0.8, recipe: 'thud',
      /* 走进来 1.3 秒：四帧一个循环（两步），每秒 7 帧；一步一伏 7 px。离场掉头（flip）走回右边画外 */
      enter: { kind: 'walk', T: 1.3, fps: 7, bob: 7, seq: [[['walk1', 'walk2', 'walk3', 'walk2'], 9]] },
      exit: { frame: ['walk1', 'walk2', 'walk3', 'walk2'], fps: 9, flip: true, T: 0.8 },
      idle: { frame: 'idle', breathe: [0.012, 0.8] },
      /* 连打：蓄力（棍举过头）0.3 秒 → 左右抡 0.6 秒（hitA / hitB 每秒 10 帧交替），每 0.1 秒一道棍影飞过去打一下 → 收势摸鼻子 */
      atk: { kind: 'rush', seq: [['wind', 0.3], [['hitA', 'hitB'], 0.6, 'fire'], ['taunt', 0.5]], fps: 10, from: [80, 104],
             rush: { n: 6, every: 0.1, T: 0.1, text: '啊哒',
                     ghost: [{ frame: 'hitA', box: [0, 85, 125, 122] }, { frame: 'hitB', box: [75, 195, 190, 232] }] },
             gap: [0.7, 1.1], stretch: 0.03 },
    },

    B24: {      // 霹雳舞小子：从右下角头转 → 风车 → 落成定格翻滚进来，坐地 b-boy，把一盘 3D 磁带像飞盘一样甩出去
      face: -1,
      sheet: { src: 'assets/trio/B24_bboy.webp', cell: [297, 324], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'headspin', 'windmill', 'freeze', 'idle2'] },
      /* 锚点 = 撑地的手和两脚之间的地面。在场帧最低点（freeze 第 321 行）屏幕 y 1334；人在 x 662~958。剪影面积 2.90 万（樱木 +10%） */
      anchor: [149.8, 307.5], at: [810, 1320, 1], pivot: [150, 307],
      leanK: 0,   // 坐在地上撑着手：整体前后倾会把撑地的手和脚翘起来
      depth: 1.3, recipe: 'thud',
      enter: { kind: 'roll', seq: [['headspin', 0.3], ['windmill', 0.25], ['freeze', 9, 'land']], sq: 0.1 },   // 翻滚进场时帧也在换：头转 → 风车 → 落地定格（压扁）
      exit: { frame: 'windmill' },
      idle: { frame: 'idle', breathe: [0.018, 0.9, 0] },
      flex: { idle: [[186, 70, 220, 120, 'l', 5, 1.4]], follow: [[186, 70, 220, 120, 'l', 5, 1.4]] },   // 头巾结的两条飘带：结那头钉住，梢往外甩
      atk: { kind: 'throw', item: 'cassette', r: 22, atlas: { src: 'assets/trio/prop_cassette.webp', n: 36, cols: 6, cell: 84, scale: 1.31 },
             seq: [['wind', 0.3], ['throw', 0.1, 'fire'], ['follow', 0.3]],
             hold: { idle: [232, 118], wind: [248, 72], throw: [28, 128] },
             T: 0.5, arc: 0.25, spin: 6.3, idleSpin: 1.6, stretch: 0, gap: [0.5, 0.9], onHit: 'bounce' },
    },
    B25: {      // 健身教练：俯卧撑姿势从右下角滑进来、一撑弹起单膝跪秀双臂，抡起 3D 哑铃砸过去
      face: -1,
      sheet: { src: 'assets/trio/B25_coach.webp', cell: [278, 349], cols: 4, names: ['idle', 'raise', 'throw', 'follow', 'plank', 'pushup', 'pop', 'idle2'] },
      /* 待机用 pop（单膝跪、正面秀双臂）：原来的 idle 帧扭头朝右秀单臂，朝向不够干脆，改当收势（curl）；
         原 follow 帧模型把腿画挪了（配准残差 5.7px），不用。锚点 = 前脚和跪地膝之间的地面；在场帧最低点屏幕 y 1332.5 */
      anchor: [149.4, 307.5], at: [840, 1330, 1], pivot: [149, 307],
      leanK: 0,
      depth: 1.3, recipe: 'thud',
      enter: { kind: 'slide', seq: [['plank', 0.25], ['pushup', 0.2], ['plank', 0.15], ['pop', 9, 'land']], sq: 0.12 },   // 俯卧撑平板滑 → 压下去 → 撑起 → 弹起秀肌肉
      exit: { frame: 'plank' },
      idle: { frame: 'pop', breathe: [0.02, 0.9, 0] },
      atk: { kind: 'throw', item: 'dumbbell', r: 24, atlas: { src: 'assets/trio/prop_dumbbell.webp', n: 36, cols: 6, cell: 75, scale: 1.08 },
             seq: [['raise', 0.3], ['throw', 0.1, 'fire'], ['idle', 0.3]],
             hold: { pop: [54, 61], raise: [192, 15], throw: [9, 80] },
             T: 0.5, arc: 0.3, spin: 6.3, idleSpin: 1.6, stretch: 0, gap: [0.55, 0.95], onHit: 'bounce' },
    },
    B30: {      // 杀马特：跪着往后仰滑进来、指天定格，跪地捂脸，指间转着一把蓝梳子，甩飞过去
      face: -1,
      sheet: { src: 'assets/trio/B30_smart.webp', cell: [287, 345], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'kneeslide', 'arrive', 'stop', 'idle2'] },
      /* 锚点 = 两膝和靴尖之间的地面；在场帧最低点屏幕 y 1333.3。名单里的发胶喷雾引擎还没有 spray，这一版只有飞梳子 */
      anchor: [147.3, 338.7], at: [835, 1330, 1], pivot: [147, 338],
      leanK: 0,   // 跪在地上：整体前后倾会把膝盖翘起来
      depth: 1.3, recipe: 'star',
      enter: { kind: 'slide', seq: [['kneeslide', 0.4], ['arrive', 0.2], ['stop', 9, 'land']], sq: 0.1 },
      exit: { frame: 'kneeslide' },
      idle: { frame: 'idle', breathe: [0.018, 0.9, 0] },
      /* 次级摆动：梳子在指间一直转（idleSpin 大，平面道具按 hang × 0.2 转） */
      atk: { kind: 'throw', item: 'comb', prop: 'assets/trio/prop_comb.webp', scale: 1.4,   // 1 倍（64px 长）飞起来太小，看不出是梳子
             seq: [['wind', 0.3], ['throw', 0.1, 'fire'], ['follow', 0.3]],
             hold: { idle: [95, 215], wind: [68, 45], throw: [8, 95] },
             T: 0.42, arc: 0.15, spin: 16, idleSpin: 12, stretch: 0.03, gap: [0.5, 0.9], onHit: 'bounce' },
    },
    B22: {      // 悟空：从右下角低身冲刺、一滑落成半跪，双手在腰侧蓄气 → 往前推出水版气功波
      face: -1,
      sheet: { src: 'assets/trio/B22_goku.webp', cell: [262, 328], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'dash', 'skid', 'guard', 'idle2'] },
      /* 锚点 = 前脚和跪地膝之间的地面；在场帧最低点屏幕 y 1332.9。剪影面积 2.90 万 */
      anchor: [138.1, 291.2], at: [835, 1330, 1], pivot: [138, 291],
      leanK: 0,   // 半跪两点着地：整体前后倾会把前脚翘起来
      depth: 1.3, recipe: 'water',
      enter: { kind: 'dash', seq: [['dash', 0.45], ['skid', 0.15, 'land'], ['guard', 9]], sq: 0.1 },
      exit: { frame: 'dash' },
      idle: { frame: 'idle', breathe: [0.02, 0.9, 0] },
      flex: { idle: [[212, 180, 245, 224, 'l', 5, 1.2]], follow: [[212, 180, 245, 224, 'l', 5, 1.2]] },   // 腰带的两条尾巴：结那头钉住
      /* 出手帧（throw）的时长 = beam.fire：波轰满 0.6 秒才收 */
      atk: { kind: 'beam', seq: [['wind', 0.45], ['throw', 0.6, 'fire'], ['follow', 0.3]],
             hold: { wind: [215, 160], throw: [38, 85] }, gap: [0.45, 0.8], stretch: 0.03,
             beam: { fire: 0.6, drip: 0.1, ball: 26, glow: [120, 210, 255], edge: [30, 90, 200],
                     layers: [[34, [30, 90, 200], 0.35], [22, [90, 180, 255], 0.8], [11, [210, 240, 255], 0.95], [4, [255, 255, 255], 1]] } },
    },
    B11: {      // 假面绅士：从右屏边扒着墙爬进来，挂在墙上甩玫瑰飞镖；打偏的钉在她脚边，打中她头上冒爱心（灭迹党靠分散注意力）
      face: -1,
      sheet: { src: 'assets/trio/B11_mask.webp', cell: [215, 301], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'crawl1', 'crawl2', 'arrive', 'idle2'] },
      /* 锚点 = 贴墙的那只鞋（右屏边）；剪影面积 2.31 万（格格 2.09 万 +10%） */
      anchor: [203.9, 167.8], at: [952, 620, 1], pivot: [204, 168],
      leanK: 0.4,   // 挂在墙上的人前后倾打折：转轴就是贴墙那一点，幅度大了手脚离墙
      depth: 0.5, recipe: 'petal',
      enter: { kind: 'crawl', seq: [['crawl1', 0.15], ['crawl2', 0.15], ['crawl1', 0.15], ['crawl2', 0.15], ['arrive', 9]] },   // 一步一耸爬进来（crawl 的耸动 5 个半周期，换帧跟着它）→ 压帽檐到位
      exit: { frame: 'crawl1' },
      idle: { frame: 'idle', breathe: [0.016, 0.9, 0.4] },
      flex: { idle: [[60, 206, 138, 274, 't', 14, 0.9]], follow: [[60, 206, 138, 274, 't', 14, 0.9]] },   // 披风下摆：顶边钉住，下摆晃（幅度 6 时胶片上整块只动 1.8px，不到 3px）
      atk: { kind: 'throw', item: 'rose', prop: 'assets/world/trio_prop_rose.webp', scale: 0.5,
             seq: [['wind', 0.28], ['throw', 0.1, 'fire'], ['follow', 0.3]],
             hold: { wind: [85, 105], throw: [15, 85] },
             T: 0.42, arc: 0.12, spin: 0, gap: [0.45, 0.7], miss: 0.35, stick: 2.2, onHit: 'heart' },
    },

    B23: {      // 三刀剑客（索隆式）：三刀在手从右下角一个滑步压低、刹住落成单膝跪三刀流架势，向左一记横斩，三道绿色斩痕交叉劈在她身上
      face: -1,
      sheet: { src: 'assets/trio/B23_zoro.webp', cell: [361, 368], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'skid', 'slide', 'set', 'idle2'] },
      /* 锚点 = 前脚和跪地膝之间的地面；在场帧最低点屏幕 y 1332。剪影面积 2.89 万（樱木 +9%，刀算在剪影里） */
      anchor: [160.4, 279.1], at: [820, 1330, 1], pivot: [160, 279],
      leanK: 0,   // 单膝跪地：整体前后倾会把跪地的膝盖翘起来
      depth: 1.3, recipe: 'star',
      /* 滑步（刀往后拖）→ 刹住后仰 → 落膝（压扁）→ 三刀架势。进场条上排两格头后多一小截黑结（模型画的），只在前 0.3 秒 */
      enter: { kind: 'slide', seq: [['slide', 0.3], ['skid', 0.15], ['set', 0.15, 'land'], ['idle', 9]], sq: 0.1 },
      exit: { frame: 'slide' },
      idle: { frame: 'idle', breathe: [0.018, 0.9, 0] },
      flex: { idle: [[215, 93, 233, 120, 'l', 5, 1.3]] },   // 左臂头巾结的两条尾巴：结那头钉住，尾梢甩
      /* 斩痕画在她身上（引擎 slash），出手那一段 0.35 秒盖住三道（gap 0.08 × 2 + 划出 0.07） */
      atk: { kind: 'slash', seq: [['wind', 0.3], ['throw', 0.35, 'fire'], ['follow', 0.3]],
             slash: { n: 3, gap: 0.08, len: 230, w: 18, life: 0.5, color: [90, 230, 110], ang: -0.5, spread: 0.25 },
             gap: [0.6, 1.0] },
    },
    B26: {      // 电竞宅男：趴在橙色懒人沙发上被（画外的人）推进来，趴着攥住鼠标线抡圈，把 3D 有线鼠标当流星锤甩出去，线连着手
      face: -1,
      sheet: { src: 'assets/trio/B26_gamer.webp', cell: [253, 274], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'pushed', 'skid', 'settle', 'idle2'] },
      /* 锚点 = 懒人沙发底的中点；在场帧最低点（拖鞋）屏幕 y 1333。剪影面积按"人 + 沙发"对齐樱木：约 3.0 万（+13%），所以人比别的地板角色小一圈。
         skid 格模型多画了一双拖鞋（四只），不用 */
      anchor: [132.7, 254.2], at: [830, 1316, 1], pivot: [133, 254],
      leanK: 0,   // 趴在沙发上：整体前后倾会把沙发底翘起来
      depth: 1.3, recipe: 'thud',
      enter: { kind: 'slide', seq: [['pushed', 0.45], ['settle', 0.2, 'land'], ['idle', 9]], sq: 0.12 },   // 被推着滑 → 瘫下去伸懒腰（压扁）→ 撑脸待机
      exit: { frame: 'pushed' },
      idle: { frame: 'idle', breathe: [0.02, 0.9, 0] },
      /* 次级摆动：手里的鼠标一直慢慢转（3D 图集） */
      atk: { kind: 'throw', item: 'mouse', r: 22, atlas: { src: 'assets/trio/prop_mouse.webp', n: 36, cols: 6, cell: 88, scale: 1.37 },
             seq: [['wind', 0.3], ['throw', 0.1, 'fire'], ['follow', 0.35]],
             hold: { idle: [66, 168], wind: [76, 12], throw: [28, 88], follow: [80, 92] },
             tether: { w: 2.5, color: '#2a2d33' },
             T: 0.45, arc: 0.2, spin: 7, idleSpin: 1.6, stretch: 0, gap: [0.5, 0.9], onHit: 'bounce' },
    },
    /* ---- 单张立绘（旧，等按规范重做成帧序列） ---- */
    B12: {      // 草帽船长：扒在右边屏幕壁上，橡皮手臂伸长弹她脑门
      face: -1, src: 'assets/world/trio_straw.webp', at: [960, 620, 1], anchor: [300, 180], pivot: [298, 180], hand: [15, 70],
      depth: 0.5, enter: 'spring', recipe: 'star',
      atk: { kind: 'punch', fist: [0, 44, 36, 96], fistC: [16, 70], wrist: [36, 70], armW: 16, skin: '#f7cba0', skinShade: 'rgba(214,146,96,.5)', skinEdge: '#5a3420', fistZ: 1.35,
             phases: [0.16, 0.1, 0.34], wind: 0.3, gap: [0.55, 0.9] },
    },
  },

  /* 10 组（地面 + 上方 + 地板），docs/三人组30人名单.md。cast / ground 里还没有的编号 = 还没做，那个槽位空着；整组都没有就跳过 */
  groups: [
    { name: '热血格斗', ground: 'B4', top: 'B12', floor: 'B22' },
    { name: '港片', ground: 'B6', top: 'B18', floor: 'B27' },
    { name: '功夫', ground: 'B5', top: 'B16', floor: 'B24' },
    { name: '西游', ground: 'B2', top: 'B20', floor: 'B28' },
    { name: '冒险', ground: 'B1', top: 'B14', floor: 'B23' },
    { name: '球场', ground: 'B9', top: 'B11', floor: 'B21' },
    { name: '富少', ground: 'B7', top: 'B13', floor: 'B25' },
    { name: '最强', ground: 'B8', top: 'B15', floor: 'B26' },
    { name: '街坊', ground: 'B10', top: 'B17', floor: 'B29' },
    { name: '特摄', ground: 'B3', top: 'B19', floor: 'B30' },
  ],
};
