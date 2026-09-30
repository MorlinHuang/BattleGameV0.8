/* trio_buddy.js —— 哥们侧（右，灭迹党，打女生）三人组的角色数据 + 10 组搭配。**美术维护**，引擎在 trio.js。
 * 怎么出一个人、每个字段什么意思：docs/三人组角色规范.md。名单与分组：docs/三人组30人名单.md。
 * 坐标：at 是 960×1334 版面上的屏幕像素（GROUND 1195 = 男女主脚底，1334 以下直播时被评论区盖着）；
 * 贴图点（anchor / pivot / hold / flex …）是图集里一格的像素（v14/trio/preview/<名>_frames.png 上量，旧的单张立绘是 <名>_grid.png）。
 */
'use strict';

const TRIO_BUDDY = {
  cast: {
    /* ---- 后排地面：原 crew.js 的老角色（2026-10-01 迁成帧序列，引擎负责人维护这几条） ---- */
    B1: {      // 冲浪男（棕发护目镜、花短裤、红滑板）：原 crew.js 滑板哥们（v14/buddy/skate1.png），2026-10-01 迁成帧序列（引擎负责人）
      face: -1,
      /* crewframes.py：crew.js 在用的分层原图按 crew.js 的转轴合成（外形、配色、脸不变）；at.s 0.83 时和 crew.js 原来一样大 */
      sheet: { src: 'assets/trio/B1_surfer.webp', cell: [434, 421], cols: 4, names: ['idle', 'wind', 'follow', 'ride', 'brake', 'aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10'] },
      anchor: [265.3, 415.6], at: [820, 1040, 0.83], pivot: [265.3, 415.6], leanK: 0,   // 锚点 = 滑板着地那一点
      depth: 0.8, recipe: 'water',
      /* 踩着滑板从画外滑进来（ride：减速停住、身子往来的方向仰），刹住那一下枪往上一扬（brake）；离场往后溜出去 */
      enter: { kind: 'ride', T: 0.55, tilt: 0.06, roll: [7.7, 1.9, 1.15], seq: [['ride', 0.42], ['brake', 0.13, 'land'], ['idle', 9]], sq: 0.05 },
      exit: { frame: 'ride', T: 0.5 },
      idle: { frame: 'idle', breathe: [0.012, 0.9, 0.4] },
      /* 水枪（crew.js Buddy.fluid 原样）：举枪（wind）→ 按瞄准角挑 aim0~10 那一帧、水柱沿枪口仰角射出去一直扫她（aim 段 2.2 秒）→ 枪口往下一甩收（follow） */
      atk: { kind: 'jet', seq: [['wind', 0.22], ['aim', 2.2, 'fire'], ['follow', 0.3]], gap: [0.2, 0.45], stretch: 0,
             aim: { frames: ['aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10'], rate: 2.4, follow: 10, sweep: { a: [0.32, 0.2], w: [1.2, 2.8] },
                    nozzle: { aim0: [6.9, 219.1, -0.52], aim1: [5.3, 199.8, -0.447], aim2: [5.1, 180.4, -0.374], aim3: [6.4, 161.1, -0.301], aim4: [9.0, 141.8, -0.228], aim5: [13.1, 122.9, -0.155], aim6: [18.5, 104.2, -0.082], aim7: [25.2, 86.1, -0.009], aim8: [33.3, 68.4, 0.064], aim9: [42.6, 51.4, 0.137], aim10: [53.2, 35.1, 0.21] } },
             jet: { draw: 'stream', V: 1250, G: 900, rate: 55, life: 1.6, miss: 90, hitEvery: 0.3, floor: true } },
    },
    B2: {      // 金箍浪子（至尊宝式）：原 crew.js 滑板哥们（v14/buddy/skate4.png），2026-10-01 迁成帧序列（引擎负责人）
      face: -1,
      /* crewframes.py：crew.js 在用的分层原图按 crew.js 的转轴合成（外形、配色、脸不变）；at.s 0.83 时和 crew.js 原来一样大 */
      sheet: { src: 'assets/trio/B2_zhizunbao.webp', cell: [434, 424], cols: 4, names: ['idle', 'wind', 'follow', 'ride', 'brake', 'aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10'] },
      anchor: [265.3, 418.6], at: [820, 1040, 0.83], pivot: [265.3, 418.6], leanK: 0,   // 锚点 = 滑板着地那一点
      depth: 0.8, recipe: 'water',
      /* 踩着滑板从画外滑进来（ride：减速停住、身子往来的方向仰），刹住那一下枪往上一扬（brake）；离场往后溜出去 */
      enter: { kind: 'ride', T: 0.55, tilt: 0.06, roll: [7.7, 1.9, 1.15], seq: [['ride', 0.42], ['brake', 0.13, 'land'], ['idle', 9]], sq: 0.05 },
      exit: { frame: 'ride', T: 0.5 },
      idle: { frame: 'idle', breathe: [0.012, 0.9, 0.4] },
      /* 水枪（crew.js Buddy.fluid 原样）：举枪（wind）→ 按瞄准角挑 aim0~10 那一帧、水柱沿枪口仰角射出去一直扫她（aim 段 2.2 秒）→ 枪口往下一甩收（follow） */
      atk: { kind: 'jet', seq: [['wind', 0.22], ['aim', 2.2, 'fire'], ['follow', 0.3]], gap: [0.2, 0.45], stretch: 0,
             aim: { frames: ['aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10'], rate: 2.4, follow: 10, sweep: { a: [0.32, 0.2], w: [1.2, 2.8] },
                    nozzle: { aim0: [6.9, 222.1, -0.52], aim1: [5.3, 202.8, -0.447], aim2: [5.1, 183.4, -0.374], aim3: [6.4, 164.1, -0.301], aim4: [9.0, 144.8, -0.228], aim5: [13.1, 125.9, -0.155], aim6: [18.5, 107.2, -0.082], aim7: [25.2, 89.1, -0.009], aim8: [33.3, 71.4, 0.064], aim9: [42.6, 54.4, 0.137], aim10: [53.2, 38.1, 0.21] } },
             jet: { draw: 'stream', V: 1250, G: 900, rate: 55, life: 1.6, miss: 90, hitEvery: 0.3, floor: true } },
    },
    B3: {      // 格格府贝勒（五阿哥式）：原 crew.js 滑板哥们（v14/buddy/skate5.png），2026-10-01 迁成帧序列（引擎负责人）
      face: -1,
      /* crewframes.py：crew.js 在用的分层原图按 crew.js 的转轴合成（外形、配色、脸不变）；at.s 0.83 时和 crew.js 原来一样大 */
      sheet: { src: 'assets/trio/B3_beile.webp', cell: [434, 419], cols: 4, names: ['idle', 'wind', 'follow', 'ride', 'brake', 'aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10'] },
      anchor: [265.3, 413.6], at: [820, 1040, 0.83], pivot: [265.3, 413.6], leanK: 0,   // 锚点 = 滑板着地那一点
      depth: 0.8, recipe: 'water',
      /* 踩着滑板从画外滑进来（ride：减速停住、身子往来的方向仰），刹住那一下枪往上一扬（brake）；离场往后溜出去 */
      enter: { kind: 'ride', T: 0.55, tilt: 0.06, roll: [7.7, 1.9, 1.15], seq: [['ride', 0.42], ['brake', 0.13, 'land'], ['idle', 9]], sq: 0.05 },
      exit: { frame: 'ride', T: 0.5 },
      idle: { frame: 'idle', breathe: [0.012, 0.9, 0.4] },
      /* 水枪（crew.js Buddy.fluid 原样）：举枪（wind）→ 按瞄准角挑 aim0~10 那一帧、水柱沿枪口仰角射出去一直扫她（aim 段 2.2 秒）→ 枪口往下一甩收（follow） */
      atk: { kind: 'jet', seq: [['wind', 0.22], ['aim', 2.2, 'fire'], ['follow', 0.3]], gap: [0.2, 0.45], stretch: 0,
             aim: { frames: ['aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10'], rate: 2.4, follow: 10, sweep: { a: [0.32, 0.2], w: [1.2, 2.8] },
                    nozzle: { aim0: [6.9, 217.1, -0.52], aim1: [5.3, 197.8, -0.447], aim2: [5.1, 178.4, -0.374], aim3: [6.4, 159.1, -0.301], aim4: [9.0, 139.8, -0.228], aim5: [13.1, 120.9, -0.155], aim6: [18.5, 102.2, -0.082], aim7: [25.2, 84.1, -0.009], aim8: [33.3, 66.4, 0.064], aim9: [42.6, 49.4, 0.137], aim10: [53.2, 33.1, 0.21] } },
             jet: { draw: 'stream', V: 1250, G: 900, rate: 55, life: 1.6, miss: 90, hitEvery: 0.3, floor: true } },
    },
    B4: {      // 红发宿敌（八神庵式）：原 crew.js 滑板哥们（v14/buddy/skate7.png），2026-10-01 迁成帧序列（引擎负责人）
      face: -1,
      /* crewframes.py：crew.js 在用的分层原图按 crew.js 的转轴合成（外形、配色、脸不变）；at.s 0.83 时和 crew.js 原来一样大 */
      sheet: { src: 'assets/trio/B4_yagami.webp', cell: [442, 458], cols: 4, names: ['idle', 'wind', 'follow', 'ride', 'brake', 'aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10'] },
      anchor: [273.3, 452.6], at: [820, 1040, 0.83], pivot: [273.3, 452.6], leanK: 0,   // 锚点 = 滑板着地那一点
      depth: 0.8, recipe: 'water',
      /* 踩着滑板从画外滑进来（ride：减速停住、身子往来的方向仰），刹住那一下枪往上一扬（brake）；离场往后溜出去 */
      enter: { kind: 'ride', T: 0.55, tilt: 0.06, roll: [7.7, 1.9, 1.15], seq: [['ride', 0.42], ['brake', 0.13, 'land'], ['idle', 9]], sq: 0.05 },
      exit: { frame: 'ride', T: 0.5 },
      idle: { frame: 'idle', breathe: [0.012, 0.9, 0.4] },
      /* 水枪（crew.js Buddy.fluid 原样）：举枪（wind）→ 按瞄准角挑 aim0~10 那一帧、水柱沿枪口仰角射出去一直扫她（aim 段 2.2 秒）→ 枪口往下一甩收（follow） */
      atk: { kind: 'jet', seq: [['wind', 0.22], ['aim', 2.2, 'fire'], ['follow', 0.3]], gap: [0.2, 0.45], stretch: 0,
             aim: { frames: ['aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10'], rate: 2.4, follow: 10, sweep: { a: [0.32, 0.2], w: [1.2, 2.8] },
                    nozzle: { aim0: [14.9, 256.1, -0.52], aim1: [13.3, 236.8, -0.447], aim2: [13.1, 217.4, -0.374], aim3: [14.4, 198.1, -0.301], aim4: [17.0, 178.8, -0.228], aim5: [21.1, 159.9, -0.155], aim6: [26.5, 141.2, -0.082], aim7: [33.2, 123.1, -0.009], aim8: [41.3, 105.4, 0.064], aim9: [50.6, 88.4, 0.137], aim10: [61.2, 72.1, 0.21] } },
             jet: { draw: 'stream', V: 1250, G: 900, rate: 55, life: 1.6, miss: 90, hitEvery: 0.3, floor: true } },
    },
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
      sheet: { src: 'assets/trio/B5_jkd.webp', cell: [494, 482], cols: 4, names: ['idle', 'wind', 'hitA', 'hitB', 'walk1', 'walk4', 'walk3', 'walk2', 'taunt', 'idle2'] },
      anchor: [260.7, 478.1], at: [740, 1070, 0.83], pivot: [260, 478], leanK: 0,   // 站在男生身后右边、比主角小一圈（同 crew.js 后排的透视）
      /* 原 [800, 1158, 0.85]：同组 B24 坐在右下角，头顶和举起的磁带到 y 1038，比 B5 的脚底还高，横着挪到 x 650 也分不开（剪影重叠 ≥ 600px）。
         改成往左 60、往后排退 88（脚底 1070，仍在地板上），缩一点点：B5 在场五帧（含复审重出的宽马步 taunt）× B24 在场六帧 + 手里的磁带，剪影外扩 4px 逐对相交为 0 */
      depth: 0.8, recipe: 'thud',
      /* 走进来：四帧一个循环（两步），每秒 7 帧，换帧那一刻才前进 stride/2（钉脚）；一步一伏 7 px。离场掉头（flip）走回右边画外。
         走路条（第三次，审查_样板 7.2）：四帧同一张底图——第一次生图的 walk1 / walk4，蒙版只重绘腿和手臂（raw/walk_inp1.png）。
         walk1 近侧腿（带黑条）在前、walk2 近侧腿撑地、walk3 远侧腿（纯黄）在前、walk4 远侧腿撑地；棍四帧都在近侧手：后 → 胯边 → 前 → 胯边。
         stride 209.5 = 一圈四次换帧"继续着地那只脚"的格内位移之和 / 2（walkfix.py edge pivot：前脚落地→支撑钉鞋跟、支撑→后脚踮起钉鞋尖；
         各帧横移后四次都是 105）；dist = 5 步 × 86.94，最后一步落在 walk1（walkfix 的 ref，走完换待机不跳） */
      enter: { kind: 'walk', fps: 7, bob: 7, stride: 209.5, dist: 434.7, seq: [[['walk1', 'walk2', 'walk3', 'walk4'], 9]] },
      exit: { frame: ['walk1', 'walk2', 'walk3', 'walk4'], fps: 9, flip: true, T: 0.8 },
      idle: { frame: 'idle', breathe: [0.012, 0.8] },
      /* 连打：蓄力（棍举过头）0.3 秒 → 左右抡 0.6 秒（hitA / hitB 每秒 10 帧交替），每 0.1 秒一道棍影飞过去打一下 → 收势摸鼻子 */
      atk: { kind: 'rush', seq: [['wind', 0.3], [['hitA', 'hitB'], 0.6, 'fire'], ['taunt', 0.5]], fps: 10, from: [270, 28],   // 出手点 = wind 帧举过头顶的那只拳头：后排的出手从男生头顶翻过去，原 [80, 104] 在男生脸旁
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
      flex: { idle: [[186, 70, 220, 120, 'l', 5, 1.4]], follow: [[195, 40, 264, 115, 'l', 5, 1.4]] },   // 头巾结的两条飘带：结那头钉住，梢往外甩
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
      atk: { kind: 'throw', item: 'dumbbell', r: 28, atlas: { src: 'assets/trio/prop_dumbbell.webp', n: 36, cols: 6, cell: 75, scale: 1.06 },
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
      flex: { idle: [[212, 180, 245, 224, 'l', 5, 1.2]], follow: [[200, 150, 260, 242, 'l', 5, 1.2]] },   // 腰带的两条尾巴：结那头钉住
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
      sheet: { src: 'assets/trio/B23_zoro.webp', cell: [391, 284], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'skid', 'slide', 'set', 'idle2'] },
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
      atk: { kind: 'throw', item: 'mouse', r: 22, atlas: { src: 'assets/trio/prop_mouse.webp', n: 36, cols: 6, cell: 88, scale: 1.46 },
             seq: [['wind', 0.3], ['throw', 0.1, 'fire'], ['follow', 0.35]],
             hold: { idle: [66, 168], wind: [76, 12], throw: [28, 88], follow: [80, 92] },
             tether: { w: 2.5, color: '#2a2d33' },
             T: 0.45, arc: 0.2, spin: 7, idleSpin: 1.6, stretch: 0, gap: [0.5, 0.9], onHit: 'bounce' },
    },
    B6: {       // 上海滩（礼帽长风衣白围巾）：竖着衣领、一手插兜慢步走进来；站定捏着一枚 3D 银元把玩，手举过头顶一弹，银元翻着飞过去
      face: -1,
      sheet: { src: 'assets/trio/B6_shanghai.webp', cell: [394, 521], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'walk1', 'walk2', 'walk3', 'walk4', 'stop', 'idle2'] },
      /* 后排地面：站在男生身后右边。原想用 B5 的 [740, 1070]，同组 B27 蹲滑的头和锅铲会碰上（外扩 4px 相交 851px），退到 1040 后在场四帧 × B27 在场五帧相交 0 */
      anchor: [152.8, 506.2], at: [740, 1040, 0.83], pivot: [153, 506], leanK: 0,
      depth: 0.8, recipe: 'star',
      /* 慢步走：两腿都是黑西裤，生图两次、改图一次都没把接地腿换过来（颜色一样也看不出换没换），四张取同一张生图里的四格。
         钉脚：buddy/walkfix.py 按"继续着地那只脚"把四帧横向对齐（-25 / +6 / -24 / 0 → 以 walk1 为 0），stride = 一个循环四次换帧鞋位差之和 / 2。
         dist 必须是步长（stride / 2 × s）的整数倍：引擎每步走 dist / 步数，默认距离 357 / 5 步 = 71.4 ≠ 78.2，换帧时脚滑 6.8px（胶片实测 +6.9 / +7.7） */
      enter: { kind: 'walk', fps: 5, bob: 4, stride: 188.5, dist: 391.2, seq: [[['walk1', 'walk2', 'walk3', 'walk4'], 9]] },
      exit: { frame: ['walk1', 'walk2', 'walk3', 'walk4'], fps: 7, flip: true, T: 0.8 },
      idle: { frame: 'idle', breathe: [0.012, 0.8] },
      flex: { idle: [[253, 215, 330, 323, 'l', 5, 1.0]] },   // 围巾尾：靠身子那头钉住、梢往后飘
      /* 手举过头顶弹：出手点 [28, 15] 在帽顶以上（后排出手从男生头顶翻过去，规范 6.4） */
      atk: { kind: 'throw', item: 'coin', r: 20, atlas: { src: 'assets/trio/prop_coin.webp', n: 36, cols: 6, cell: 63, scale: 1.13 },
             seq: [['wind', 0.3], ['throw', 0.1, 'fire'], ['follow', 0.4]], hold: { wind: [56, 300], throw: [28, 15] },   // 待机不拿：3D 银元侧着转到 90° 时是一块黑盘子，比捏着的手指还大
             T: 0.5, arc: 0.3, spin: 6.3, stretch: 0.03, gap: [0.6, 1.0] },
    },

    B7: {       // 卷发大少：踩着电动平衡车滑进来、甩头发、急刹后仰，站在车上伸手指人；把一张红纸条举过头顶一甩，贴在她身上
      face: -1,
      sheet: { src: 'assets/trio/B7_f4.webp', cell: [332, 461], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'cruise', 'swerve', 'brake', 'idle2'] },
      /* 后排地面；平衡车画在帧里，锚点 = 车底中点。[740, 1040]：同组 B25 在场四帧相交 0（1070 时 234px） */
      anchor: [168.8, 453.1], at: [740, 1040, 0.83], pivot: [169, 453], leanK: 0,
      depth: 0.8, recipe: 'feather',
      enter: { kind: 'ride', T: 1.0, tilt: 0.1, seq: [['cruise', 0.4], ['swerve', 0.3], ['brake', 9, 'land']], sq: 0.08 },   // 插兜滑行 → 甩头发拐弯 → 急刹后仰
      exit: { frame: 'cruise', flip: true },
      idle: { frame: 'idle', breathe: [0.012, 0.8] },
      flex: { idle: [[118, 8, 210, 55, 'b', 4, 0.8]] },   // 爆炸卷发顶：底边（头皮）钉住，发顶颤
      /* 纸条在 wind 帧举过头顶那一刻离手（fire 段仍是 wind 帧，出手点 [97, 14] 在头顶以上），throw 帧是甩完的手 */
      atk: { kind: 'throw', item: 'paper', prop: 'assets/trio/B7_redslip.webp', scale: 0.45,
             seq: [['wind', 0.3], ['wind', 0.06, 'fire'], ['throw', 0.14], ['follow', 0.4]], hold: { wind: [97, 14] },
             T: 0.5, arc: 0.25, spin: 5, gap: [0.6, 1.0], onHit: 'wear' },
    },

    B9: {       // 外卖小哥：骑蓝色小电驴飞驰进来、一个漂移甩尾、急刹，坐在车上竖大拇指；把外卖盒托过头顶一甩，3D 外卖盒翻着砸过去、汤汁溅开
      face: -1,
      sheet: { src: 'assets/trio/B9_rider.webp', cell: [438, 504], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'cruise', 'drift', 'brake', 'idle2'] },
      /* 后排地面；电驴画在帧里（两张条都按车身 + 后轮配准、scale_by fixed），锚点 = 两轮着地中点 */
      anchor: [197.4, 489.6], at: [625, 1062, 0.83], pivot: [197, 490], leanK: 0,
      depth: 0.8, recipe: 'splash',
      enter: { kind: 'ride', T: 1.0, tilt: 0.15, seq: [['cruise', 0.4], ['drift', 0.3], ['brake', 9, 'land']], sq: 0.08 },   // 伏低飞驰 → 漂移甩尾、一脚点地 → 急刹两脚落地
      exit: { frame: 'cruise', flip: true },
      idle: { frame: 'idle', breathe: [0.012, 0.8] },
      /* wind 帧手掌托过头顶（掌心顶 y 4，头顶 y 71），外卖盒托在掌上、在那一刻离手；throw 帧是甩完往前下的手 */
      atk: { kind: 'throw', item: 'takeout', r: 26, atlas: { src: 'assets/trio/prop_takeout.webp', n: 36, cols: 6, cell: 96, scale: 1.32 },
             seq: [['wind', 0.3], ['wind', 0.06, 'fire'], ['throw', 0.14], ['follow', 0.4]], hold: { wind: [343, -20] },
             T: 0.5, arc: 0.35, spin: 6.3, stretch: 0.02, gap: [0.6, 1.0] },
    },

    B8: {       // 光头伐木工：被身后看不见的熊追着倒退跑进来、猛回头急刹；攥着松果举过头顶狠狠砸过去
      face: -1,
      sheet: { src: 'assets/trio/B8_logger.webp', cell: [463, 479], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'walk1', 'walk2', 'walk3', 'walk4', 'skid', 'idle2'] },
      /* 后排地面。[740, 1040]：同组 B26 在场四帧相交 0（1070 时 542px）。格子 463 宽是急刹那格两臂张开撑出来的，人本身 ~250 */
      anchor: [265.3, 466.8], at: [740, 1040, 0.83], pivot: [265, 467], leanK: 0,
      depth: 0.8, recipe: 'debris',
      /* 倒退跑：身子朝右（看着追来的熊）、腿往左倒着蹬；最后一步换成急刹回头（skid 落地压一下）。
         跑：过渡帧腾空，没有哪只脚跨着换帧一直着地，不做钉脚平移（硬对齐要来回平移 ±97px，人一抽一抽）；stride = walk1 两只靴前沿横距（规范第九节 G6 跑步的取法） */
      enter: { kind: 'walk', fps: 12, bob: 10, stride: 188, dist: 624.2, seq: [[['walk1', 'walk2', 'walk3', 'walk4'], 0.5], ['skid', 9, 'land']], sq: 0.08 },
      exit: { frame: ['walk1', 'walk2', 'walk3', 'walk4'], fps: 12, flip: true, T: 0.6 },
      idle: { frame: 'idle', breathe: [0.014, 1.1] },
      /* 3D 松果（500273c 返工：上尖下圆 + 人字齿鳞片），r / cell / scale 照 docs/待办.md 的返工交接。
         松果在 wind 帧举过头顶那一刻离手（fire 段仍是 wind 帧，出手点 [184, 22] 在头顶以上），throw 帧是砸完的手。
         arc 0.45：高高抛过去、最后一段近乎竖着砸下来 —— arc 0.22 时拔河拉近那几格，落点前最后一段斜着擦过男生脸框左沿（probescan 192 格里 3 格 61~199px） */
      atk: { kind: 'throw', item: 'pinecone', r: 26, atlas: { src: 'assets/trio/prop_pinecone.webp', n: 36, cols: 6, cell: 76, scale: 1.25 },
             seq: [['wind', 0.3], ['wind', 0.06, 'fire'], ['throw', 0.14], ['follow', 0.4]], hold: { idle: [177, 160], wind: [184, 22] },
             T: 0.5, arc: 0.45, spin: 6.3, idleSpin: 1.5, gap: [0.5, 0.9] },   // 不写 bounce：弹开是往回蹦，会擦过男生的脸（组 2 B27 实测 149px）
    },

    B10: {      // 麻将大叔：拎着折起来的小马扎晃着肚子走进来，把马扎一撑一屁股坐下；捏两张麻将举过头顶一甩，3D 麻将翻着砸过去，喊"胡了"
      face: -1,
      sheet: { src: 'assets/trio/B10_mahjong.webp', cell: [473, 425], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'walk1', 'walk2', 'walk3', 'walk4', 'plop', 'idle2'] },
      /* 后排地面，锚点 = 两只人字拖中间的地面。坐在马扎上待机、出手（条 1 按马扎配准）。[740, 1020]：同组 B29 在场各帧外扩 4px 相交 0（1040 时 wind 371 px） */
      anchor: [277.0, 419.4], at: [740, 1020, 0.83], pivot: [277, 419], leanK: 0,
      depth: 0.8, recipe: 'thud',
      /* 走进来：四帧同一张底图（walk1 / walk2 生图，walk3 / walk4 蒙版重绘腿和手臂），马扎四帧都在近侧手：后 → 胯边 → 前 → 胯边。
         stride 159.5（walkfix pivot，蓝人字拖；walk1 / walk3 鞋尖距 158 / 161），5 步 × 66.19 = 330.96；第 5 步换成一屁股坐下（plop），
         plop 在图集里已经往前挪了一步（cellshift −80），坐下那一刻马扎就落在站位上，换待机不跳 */
      enter: { kind: 'walk', fps: 6, bob: 6, stride: 159.5, dist: 330.96, seq: [[['walk1', 'walk2', 'walk3', 'walk4'], 0.66667], ['plop', 9, 'land']], sq: 0.12 },
      exit: { frame: ['walk1', 'walk2', 'walk3', 'walk4'], fps: 7, flip: true, T: 0.8 },
      idle: { frame: 'idle', breathe: [0.016, 0.8] },
      /* wind 帧捏着牌的拳头举过头顶（拳顶 y 3，头顶 y 62），两张一起离手 */
      atk: { kind: 'throw', item: 'mahjong', n: 2, r: 20, atlas: { src: 'assets/trio/prop_mahjong.webp', n: 36, cols: 6, cell: 77, scale: 1.37 },
             seq: [['wind', 0.3], ['wind', 0.06, 'fire'], ['throw', 0.14], ['follow', 0.45]], hold: { wind: [201, 8] },
             T: 0.5, arc: 0.35, spin: 6.3, stretch: 0.03, gap: [0.6, 1.0] },
    },

    B13: {      // 仙剑少年：踩着飞剑从右上斜着俯冲下来、后仰刹住、站稳悬停；剑指举过头顶召出一把蓝光飞剑，剑指一点，飞剑拖着蓝光射过去
      face: -1,
      sheet: { src: 'assets/trio/B13_sword.webp', cell: [257, 333], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'swoop', 'brake', 'settle', 'idle2', 'sword'] },
      /* 上方；锚点 = 两脚鞋底中点（踩在剑上）。剪影面积 2.12 万（上方槽位对格格 2.09 万）。画布宽 960：人最右伸出锚点 98 px；
         [850, 680]：同组 B7 在场帧外扩 4px 相交 0（730 时 throw 前伸的手压到 B7 头 556 px） */
      anchor: [155.2, 317.3], at: [850, 680, 1], pivot: [155, 317], leanK: 0.3,
      depth: 0.5, recipe: 'thud',
      /* 脚下的剑是挂件层（raw/sword_plain.png，part.py w 240），画在人后、鞋底压在剑身上；每帧按两只鞋底连线摆（角度 = 连线斜率） */
      parts: [{ src: 'assets/trio/B13_sword_ride.webp', pivot: [120, 10], z: -1, sway: [0.02, 0.7, 0],
                at: { idle: [157, 316, 0.12], wind: [157, 316, 0.116], throw: [159, 319, 0.139], follow: [167, 316, 0.153],
                      swoop: [171, 320, 0.077], brake: [148, 319, 0.093], settle: [141, 322, 0.071], idle2: [160, 316, 0.085] } },
              /* 召剑：wind 帧飞剑悬在举起的剑指上方（同一张飞剑贴图，出手那帧就不画了，由 rush 残影接着飞出去） */
              { src: 'assets/trio/B13_sword_fly.webp', pivot: [165, 24], z: 1, sway: [0.04, 2.2, 0], at: { wind: [120, -14, 0] } }],
      enter: { kind: 'fly', from: [420, -420], T: 0.8, air: 0.8, tilt: 0.12, seq: [['swoop', 0.4], ['brake', 0.25], ['settle', 0.15, 'land'], ['idle', 9]], sq: 0.06 },   // 俯冲 → 后仰刹住 → 站稳
      exit: { frame: 'swoop' },
      idle: { frame: 'idle', breathe: [0.014, 0.9, 0.4] },
      /* 飞剑（raw/sword_fly.png，蓝光拖尾画在贴图里、剑尖朝左）走 rush 残影：图集末尾那格 'sword'（add_sword_cell.py），残影按图原样水平画，剑尖一直朝前。
         throw 的平面道具朝向是随机的（b.hang），拖尾会横着 / 倒着飞，所以不用 throw。剑指点出去那一刻（throw 帧指尖 [4, 96]）射出 */
      atk: { kind: 'rush', seq: [['wind', 0.35], ['throw', 0.3, 'fire'], ['follow', 0.4]], from: [4, 96],
             rush: { n: 1, every: 0.1, T: 0.26, line: '#9ef', ghost: { frame: 'sword', box: [3, 148, 254, 185], z: 1.4 } },
             gap: [0.6, 1.0], stretch: 0.03 },
    },

    B14: {      // 方块头矿工：从右上墙里一拳一拳挖出来、跨出来落地；托起一块泥土方块举过头顶甩出去，3D 方块翻着砸过去
      face: -1,
      sheet: { src: 'assets/trio/B14_miner.webp', cell: [240, 286], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'dig', 'step', 'land', 'idle2'] },
      /* 上方；锚点 = 两脚中间的地面。剪影面积 s 1 时 2.52 万，s 0.91 → 2.09 万（上方对格格）。画布宽 960：最右伸出锚点 97 px，x 855 */
      anchor: [130.9, 275.0], at: [855, 740, 0.91], pivot: [131, 275], leanK: 0.2,
      depth: 0.5, recipe: 'debris',
      /* 挖墙钻出：从脚底那条线后面升上来 + 灰土烟；升的时候是挖墙的一拳（dig），升到位跨出来（step）、落地（land） */
      enter: { kind: 'appear', rise: 200, fx: 'smoke', color: [150, 125, 95], T: 0.8, seq: [['dig', 0.35], ['step', 0.25], ['land', 0.15, 'land'], ['idle', 9]], sq: 0.08 },
      exit: { frame: 'dig' },
      idle: { frame: 'idle', breathe: [0.012, 0.9, 0.4] },
      /* 泥土方块（3D，道具表 r 30 cell 125 scale 1.49）：待机拿在身前的拳头里、wind 托过头顶、throw 帧甩出去那一刻离手 */
      atk: { kind: 'throw', item: 'dirtblock', r: 30, atlas: { src: 'assets/trio/prop_dirtblock.webp', n: 36, cols: 6, cell: 125, scale: 1.49 },
             seq: [['wind', 0.3], ['throw', 0.1, 'fire'], ['follow', 0.4]], hold: { idle: [44, 72], wind: [84, -22], throw: [10, 150] },
             T: 0.5, arc: 0.3, spin: 6.3, idleSpin: 0.5, stretch: 0.03, gap: [0.6, 1.0] },
    },

    B15: {      // 白发蒙眼最强：右上一道紫白闪光凭空浮现，盘腿悬浮、手插兜；手指举过头顶聚起一颗紫色光球，往前一弹射过去，收势勾起眼罩露一只蓝眼
      face: -1,
      sheet: { src: 'assets/trio/B15_gojo.webp', cell: [235, 319], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'fold', 'reveal', 'settle', 'idle2'] },
      /* 上方；悬浮，锚点 = 盘着的腿最低处。剪影面积 2.20 万（上方对格格 2.09 万）。[880, 730]：同组 B8 在场帧外扩 4px 相交 0 */
      anchor: [137.3, 318.9], at: [880, 730, 1], pivot: [137, 319], leanK: 0.2,
      depth: 0.5, recipe: 'bloom',
      /* 凭空浮现：紫白闪光里淡入（抱臂低头）→ 抬头张开双手 → 手插兜落定 */
      enter: { kind: 'appear', fx: 'flash', color: [200, 160, 255], fade: 0.3, T: 0.8, seq: [['fold', 0.35], ['reveal', 0.3], ['settle', 0.15, 'land'], ['idle', 9]], sq: 0.05 },
      exit: { frame: 'fold' },
      idle: { frame: 'idle', breathe: [0.012, 0.8, 0.4] },
      flex: { idle: [[160, 5, 290, 45, 'b', 3, 0.8]] },   // 冲天白发顶：底边钉住，发梢颤
      /* 紫色光球（raw/orb_src.png，part.py w 140；平面贴图，圆的，转着飞）：wind 帧聚在举起的指尖上方，throw 帧指尖一弹射出去 */
      atk: { kind: 'throw', item: 'orb', prop: 'assets/trio/B15_orb.webp', scale: 0.5,
             seq: [['wind', 0.35], ['throw', 0.1, 'fire'], ['follow', 0.45]], hold: { wind: [86, -20], throw: [0, 90] },
             T: 0.4, arc: 0.1, spin: 8, stretch: 0.03, gap: [0.6, 1.0] },
    },

    B16: {      // 黄金圣衣战士：右上金光一闪、圣衣合身张开双臂，单膝落地、起身举拳；收拳蓄力，一串金色光速拳影砸过去
      face: -1,
      sheet: { src: 'assets/trio/B16_gold.webp', cell: [287, 341], cols: 4, names: ['idle', 'wind', 'hitA', 'hitB', 'assemble', 'land', 'victory', 'idle2'] },
      /* 上方；锚点 = 两脚中间的地面（站在墙沿）。剪影面积 s 1 时 2.92 万，s 0.85 → 2.11 万（上方对格格）。
         画布宽 960：披风最右伸出锚点 133 px，x ≤ 822。[820, 670]：同组 B5 在场帧外扩 4px 相交 0（740 时 B5 wind 举棍过头相交 1039 px），同组 B24 相交 0 */
      anchor: [127.2, 337.5], at: [820, 670, 0.85], pivot: [127, 337], leanK: 0.2,
      depth: 0.5, recipe: 'star',
      /* 圣衣拼身：金光里淡入（张开双臂、圣衣刚合上）→ 单膝落在墙沿（land 压扁）→ 起身举拳 */
      enter: { kind: 'appear', fx: 'flash', color: [255, 210, 80], fade: 0.3, T: 0.9, seq: [['assemble', 0.35], ['land', 0.25, 'land'], ['victory', 0.3], ['idle', 9]], sq: 0.08 },
      exit: { frame: 'assemble' },
      idle: { frame: 'idle', breathe: [0.012, 0.8, 0.4] },
      /* 光速拳：收拳蓄力 0.3 秒 → 两拳交替 0.6 秒，每 0.1 秒一道拳影（hitA / hitB 前伸那只拳头）飞过去、金色速度线 → 举拳 */
      atk: { kind: 'rush', seq: [['wind', 0.3], [['hitA', 'hitB'], 0.6, 'fire'], ['victory', 0.4]], fps: 10, from: [14, 110],
             rush: { n: 6, every: 0.1, T: 0.1, line: '#ffd84a',
                     ghost: [{ frame: 'hitA', box: [12, 96, 75, 124] }, { frame: 'hitB', box: [14, 121, 77, 149] }] },
             gap: [0.7, 1.1], stretch: 0.03 },
    },

    B17: {      // 补丁帽灰狼：脚踝拴着绳从右上倒挂着掉下来、蹦两下，挂着抱臂坏笑露尖牙；抡起捕羊网兜一甩，罩在她头上
      face: -1,
      sheet: { src: 'assets/trio/B17_wolf.webp', cell: [232, 324], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'plunge', 'bounce', 'settle', 'idle2'] },
      /* 上方；倒挂，锚点 = 两只脚踝（绳子拴的那一点）。剪影面积 s 1 时 1.72 万，s 1.05 → 1.89 万（上方对格格 −10%）。
         [830, 370]：同组 B10 收势双手举过头顶，y 470 时相交 5223 px；370 时在场帧外扩 4px 相交 0。画布宽 960：人最右伸出锚点 119 px */
      anchor: [116.3, 6.5], at: [830, 370, 1.05], pivot: [116, -660], leanK: 0,
      depth: 0.5, recipe: 'thud',
      /* 倒挂垂下：顺着绳从上面掉下来（伸直俯冲）→ 冲过头弹回（张开手脚）→ 稳住；绳子引擎画，拴在脚踝 line */
      enter: { kind: 'drop', len: 700, line: [116, 6], T: 0.8, w: 3, fill: '#8a6a44', edge: 'rgba(60,40,20,.9)',
               seq: [['plunge', 0.35], ['bounce', 0.25], ['settle', 0.2, 'land'], ['idle', 9]], sq: 0.06 },
      exit: { frame: 'plunge' },
      idle: { frame: 'idle', breathe: [0.014, 0.9, 0.3] },
      flex: { idle: [[150, 110, 208, 198, 'l', 5, 0.9]] },   // 大尾巴：贴屁股那边（左）钉住，尾梢甩
      /* 捕羊网兜（raw/net_src.png，part.py w 200）：wind 抡到身后，throw 帧爪子甩出去那一刻离手，打中罩在头上（onHit net） */
      atk: { kind: 'throw', item: 'net', prop: 'assets/trio/B17_net.webp', scale: 0.7,
             seq: [['wind', 0.3], ['throw', 0.1, 'fire'], ['follow', 0.45]], hold: { throw: [14, 198] },
             T: 0.5, arc: 0.2, spin: 1.5, stretch: 0.02, onHit: 'net', gap: [0.6, 1.0] },
    },

    B19: {      // 光之巨人 cos 大叔：右上一道白光变身冲天、落地一蹲、起身双手叉腰挺肚子；胸口计时器蓄光，十字手打出一道白蓝光线
      face: -1,
      sheet: { src: 'assets/trio/B19_ultra.webp', cell: [225, 318], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'transform', 'land', 'rise', 'idle2'] },
      /* 上方；锚点 = 两脚中间的地面。剪影面积 s 1 时 1.85 万，s 1.06 → 2.08 万（上方对格格）。
         [850, 700]：同组 B3（820, 1040）在场帧（含 aim0~10）、B30 外扩 4px 相交 0；720 时 follow 举拳 × B3 wind 相交 398 px。画布宽 960：最右伸出锚点 93 px */
      anchor: [99.1, 311.8], at: [850, 700, 1.06], pivot: [99, 312], leanK: 0.2,
      depth: 0.5, recipe: 'water',
      /* 变身闪光：白光里淡入（冲天拳）→ 落地一蹲 → 起身 */
      enter: { kind: 'appear', fx: 'flash', color: [230, 240, 255], fade: 0.3, T: 0.9, seq: [['transform', 0.35], ['land', 0.25, 'land'], ['rise', 0.2], ['idle', 9]], sq: 0.08 },
      exit: { frame: 'transform' },
      idle: { frame: 'idle', breathe: [0.018, 0.8, 0.3] },
      /* 十字光线：wind 两臂张开蓄力，蓄力球在胸口计时器上；throw 帧十字手，光从竖着那条前臂的左沿射出去（beam.fire 0.6 秒） */
      atk: { kind: 'beam', seq: [['wind', 0.45], ['throw', 0.6, 'fire'], ['follow', 0.35]],
             hold: { wind: [87, 128], throw: [40, 86] }, gap: [0.45, 0.8], stretch: 0.03,
             beam: { fire: 0.6, drip: 0.1, ball: 16, glow: [180, 230, 255], edge: [40, 110, 220],
                     layers: [[26, [40, 110, 220], 0.35], [16, [140, 210, 255], 0.8], [8, [225, 245, 255], 0.95], [3, [255, 255, 255], 1]] } },
    },

    B20: {      // 济公式疯和尚：坐在一只大酒坛上从右上飘下来、晃一下抓住坛盖、坐稳；仰头灌一口酒葫芦，鼓着腮往前一喷，一股酒雾喷到她脸上
      face: -1,
      sheet: { src: 'assets/trio/B20_monk.webp', cell: [259, 316], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'drift', 'wobble', 'settle', 'idle2'] },
      /* 上方；酒坛画在帧里（两张条都按酒坛配准），锚点 = 坛底中点。剪影面积 s 1 时 3.24 万（含酒坛），s 0.8 → 2.07 万（上方对格格）。
         [860, 680]：同组 B2（820, 1040，含 aim 帧）、B28 在场帧外扩 4px 相交 0（700 时 settle × B2 wind 36 px）。画布宽 960：最右伸出锚点 83 px */
      anchor: [120.6, 310.9], at: [860, 680, 0.8], pivot: [121, 311], leanK: 0.2,
      depth: 0.5, recipe: 'splash',
      /* 坐酒坛飘下来：从右上斜着飘（坛前倾、两腿翘起）→ 坛往后一晃抓住坛盖 → 坐稳 */
      enter: { kind: 'fly', from: [380, -420], T: 0.9, air: 0.9, tilt: 0.1, seq: [['drift', 0.4], ['wobble', 0.3], ['settle', 0.2, 'land'], ['idle', 9]], sq: 0.06 },
      exit: { frame: 'drift' },
      idle: { frame: 'idle', breathe: [0.016, 0.8, 0.3] },
      /* 喷酒雾（spray，名单二选一取喷）：wind 仰头灌酒、throw 鼓腮从嘴里喷（from = throw 帧嘴），琥珀色酒雾 */
      atk: { kind: 'spray', seq: [['wind', 0.35], ['throw', 0.7, 'fire'], ['follow', 0.35]], from: [30, 106],
             spray: { dur: 0.6, rate: 90, T: 0.3, tick: 0.15, color: [235, 195, 110], r: 18, spread: 0.14 }, gap: [0.6, 1.0], stretch: 0.02 },   // 出手挤压小一点：坛子是硬的
    },

    B18: {      // 摇扇才子：从右上墙头后面一蹿翻上来、坐定；背后插着题诗折扇，伸手抽出来一甩，3D 折扇旋着飞过去
      face: -1,
      sheet: { src: 'assets/trio/B18_tangbohu.webp', cell: [279, 375], cols: 4, names: ['idle', 'raise', 'wind', 'throw', 'follow', 'leap', 'land', 'idle2'] },
      /* 锚点 = 撑在墙头上的那只手 = 墙头那一行。上方槽位：剪影面积 3.94 万 × 0.72² = 2.04 万（格格 2.09 万 −2%）。
         [890, 630]：和别的上方角色（B11 y 620）同一高度，把 y 400 一带留给叠第二组时的上方备用位（SLOT2 = 往上 210）；原来放 y 520 正好占了它。
         背后的扇子右沿到 x 958 不出画；和同组 B6 在场四帧 × B18 在场六帧剪影外扩 4px 相交 0 */
      anchor: [194.8, 211.6], at: [890, 630, 0.72], pivot: [195, 212], leanK: 0.3,
      depth: 0.5, recipe: 'feather',
      /* 从墙头那一行后面升上来（线以下剪掉），蹿上来 → 落座（压一下）→ 坐定；淡入 0.35 秒内是 leap，之后换 land */
      enter: { kind: 'appear', rise: 220, cut: 212, T: 0.8, seq: [['leap', 0.4], ['land', 0.2, 'land'], ['idle', 9]], sq: 0.08 },
      exit: { frame: 'leap' },
      idle: { frame: 'idle', breathe: [0.016, 0.9, 0.4] },
      /* 挂件层：墙头瓦檐（buddy/B18_tangbohu/raw/wall.png，下接一截渐隐白墙）垫在人后面；背后斜插的折扇（定妆拆的那一层 ref/B18_fan.png）跟着轻晃，
         抽出来以后（wind 起手里是 3D 扇、throw / follow 扔出去了）不画 */
      parts: [
        { src: 'assets/trio/B18_wall.webp', pivot: [165, 14], z: -1, fixed: true, at: { idle: [195, 212, 0], raise: [195, 212, 0], wind: [195, 212, 0], throw: [195, 212, 0], follow: [195, 212, 0], leap: [195, 212, 0], land: [195, 212, 0], idle2: [195, 212, 0] } },   // 场景层（引擎负责人 2026-10-01）：墙头钉在世界里，人从它后面升上来
        { src: 'assets/trio/B18_fan.webp', pivot: [38, 87], z: -1, at: { idle: [202, 133, 0], raise: [202, 133, 0], leap: [207, 172, 0], land: [209, 144, 0], idle2: [202, 133, 0] }, sway: [0.05, 0.7, 0] },
      ],
      atk: { kind: 'throw', item: 'fan', r: 45, atlas: { src: 'assets/trio/prop_fan.webp', n: 36, cols: 6, cell: 126, scale: 1.06 },   // 3D 扇返工（引擎负责人 2026-10-01）：白纸水墨 + 红穗，长边 73~94px ≈ 背后那把
             seq: [['raise', 0.2], ['wind', 0.25], ['throw', 0.1, 'fire'], ['follow', 0.35]], hold: { wind: [191, 29], throw: [8, 78] },
             T: 0.5, arc: 0.15, spin: 6.3, gap: [0.6, 1.0] },
    },

    B28: {      // 西游胖和尚（八戒式）：背着九齿钉耙蹲着一扭一扭挪进来，一屁股坐下；抱着 3D 西瓜腆肚子，举过头顶砸过去，砸中红瓤带籽溅开
      face: -1,
      sheet: { src: 'assets/trio/B28_pig.webp', cell: [256, 268], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'walk1', 'walk2', 'walk3', 'walk4', 'plop', 'idle2'] },
      /* 地板前排，锚点 = 屁股着地那一点。剪影面积 2.71 万（樱木 +2%）；各帧剪影最低一行屏幕 y 最大 1325 */
      anchor: [113.3, 265.0], at: [830, 1325, 1], pivot: [113, 265], leanK: 0,
      depth: 1.3, recipe: 'melon',
      /* 蹲着挪：步子小、慢（fps 5）；最后一步换成一屁股坐下（plop 落地压扁），坐定 = idle。钉脚：walkfix.py 横向对齐（平移 -3 / 0 / -4 / 0），stride = 四次换帧鞋位差之和 / 2。
         两条腿都是黑灯笼裤白袜，接地帧换没换腿看不出，四张取同一张生图里的四格 */
      enter: { kind: 'walk', fps: 5, bob: 5, stride: 129.5, dist: 324, seq: [[['walk1', 'walk2', 'walk3', 'walk4'], 0.8], ['plop', 9, 'land']], sq: 0.14 },   // dist = 5 步：前 4 步走完一个循环，第 5 步是一屁股坐下
      exit: { frame: ['walk1', 'walk2', 'walk3', 'walk4'], fps: 6, flip: true, T: 0.8 },
      idle: { frame: 'idle', breathe: [0.02, 0.9, 0] },
      atk: { kind: 'throw', item: 'watermelon', r: 30, atlas: { src: 'assets/trio/prop_watermelon.webp', n: 36, cols: 6, cell: 98, scale: 1.17 },
             seq: [['wind', 0.35], ['throw', 0.1, 'fire'], ['follow', 0.4]], hold: { idle: [112, 150], wind: [135, 15], throw: [35, 105] },
             T: 0.5, arc: 0.25, spin: 6.3, idleSpin: 0.6, stretch: 0, gap: [0.6, 1.0] },
    },

    B29: {      // 东北卖拐大叔：军大衣雷锋帽，拄着拐一瘸一拐挪进来，举着拐吆喝推销；抡起拐杖甩过去，3D 拐杖翻着飞
      face: -1,
      sheet: { src: 'assets/trio/B29_crutch.webp', cell: [302, 331], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'walk1', 'walk2', 'walk3', 'walk4', 'stop', 'idle2'] },
      /* 地板前排（站着弓腰），锚点 = 两脚之间的地面。剪影面积 2.85 万（樱木 +8%，含帧里的拐）。at.y 1326：各帧剪影最低一行屏幕 y 最大 1333.2（1328 时 1335.2，超 1.2）。
         拐杖在 idle / wind / 走路帧里画着（拄着、推销、抡起来），throw 帧手空了、飞出去的是 3D 拐杖 */
      anchor: [192.3, 320.8], at: [830, 1326, 1], pivot: [192, 321], leanK: 0,
      depth: 1.3, recipe: 'thud',
      /* 瘸：步长恒定（引擎一帧一步），瘸靠 walk3 伤腿着地时身子下沉、压着拐（审查第三轮第 4 条）；bob 跟帧。
         拄拐的过渡帧也是一前一后两脚着地（后脚撑着），钉脚按手写的换帧链对齐（walkfix.py，平移 +18 / -12 / -9 / -48）；dist = 6 步 × 59.25 */
      enter: { kind: 'walk', fps: 5, bob: 12, stride: 118.5, dist: 355.5, seq: [[['walk1', 'walk2', 'walk3', 'walk4'], 9]] },
      exit: { frame: ['walk1', 'walk2', 'walk3', 'walk4'], fps: 6, flip: true, T: 0.8 },
      idle: { frame: 'idle', breathe: [0.014, 0.8, 0] },
      flex: { idle: [[100, 33, 180, 68, 'b', 3, 0.8]] },   // 雷锋帽顶的毛：底边钉住，帽顶颤
      atk: { kind: 'throw', item: 'crutch', r: 86, atlas: { src: 'assets/trio/prop_crutch.webp', n: 36, cols: 6, cell: 190, scale: 1.07 },   // 3D 拐返工（引擎负责人 2026-10-01）：浅木双杆长拐，长边 163~183px ≈ 帧里那根
             seq: [['wind', 0.35], ['throw', 0.1, 'fire'], ['follow', 0.4]], hold: { throw: [18, 75] },
             T: 0.5, arc: 0.2, spin: 6.3, stretch: 0.02, gap: [0.6, 1.0] },
    },

    /* ---- 单张立绘（旧，等按规范重做成帧序列） ---- */
    B12: {      // 草帽船长：扒在右边屏幕壁上，橡皮手臂伸长弹她脑门
      /* 2026-10-01 迁成帧序列（引擎负责人）：idle = 原单张立绘（拳头伸出去），wind = 同一张画布上只局部重绘右臂（拳头收到胸前蓄力，
         v14/trio/buddy/B12_straw/inp/，inpaint_paste.py：框外是原图像素）。锚点、手、拳头框都和原立绘同一个像素，原来调好的数值照搬。
         出手：收拳蓄力 → 换回伸拳那一帧、橡皮手臂从手腕伸出去弹她脑门（punch：拳头那一块画在伸出去的地方）→ 缩回来 */
      face: -1,
      sheet: { src: 'assets/trio/B12_straw.webp', cell: [305, 360], cols: 2, names: ['idle', 'wind'] },
      anchor: [300, 180], at: [960, 620, 1], pivot: [298, 180], leanK: 0.6,   // 绕扒墙的那只手前后倾：蓄力往后、出拳往前甩
      depth: 0.5, enter: 'spring', recipe: 'star',
      idle: { frame: 'idle', breathe: [0.014, 0.9, 0.4] },
      atk: { kind: 'punch', seq: [['wind', 0.3], ['idle', 0.62, 'fire']],
             fist: [0, 44, 36, 96], fistC: [16, 70], wrist: [36, 70], armW: 16, skin: '#f7cba0', skinShade: 'rgba(214,146,96,.5)', skinEdge: '#5a3420', fistZ: 1.35,
             phases: [0.16, 0.1, 0.34], gap: [0.55, 0.9], stretch: 0.03 },
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
