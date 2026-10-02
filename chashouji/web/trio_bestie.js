/* trio_bestie.js —— 闺蜜侧（左，查岗党，打男生）三人组的角色数据 + 10 组搭配。**美术维护**，引擎在 trio.js。
 * 怎么出一个人、每个字段什么意思：docs/三人组角色规范.md。名单与分组：docs/三人组30人名单.md。
 * 坐标约定同 trio_buddy.js 开头。
 */
'use strict';

const TRIO_BESTIE = {
  cast: {
    /* ---- 后排地面：原 crew.js 的老角色（2026-10-01 迁成帧序列，引擎负责人维护这几条） ---- */
    G1: {      // 墨镜短发（头顶墨镜、条纹比基尼、粉平衡车）：原 crew.js 平衡车闺蜜（v14/bestie/src3.png），2026-10-01 迁成帧序列（引擎负责人）
      face: 1,
      /* crewframes.py：crew.js 在用的分层原图按 crew.js 的转轴合成（外形、配色、脸不变）；at.s 0.88 时和 crew.js 原来一样大 */
      sheet: { src: 'assets/trio/G1_shades.webp', cell: [234, 380], cols: 4, names: ['idle', 'wind', 'follow', 'ride', 'brake', 'aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10', 'kick0', 'kick1', 'kick2', 'kick3', 'kick4', 'kick5', 'kick6', 'kick7', 'kick8', 'kick9', 'kick10'] },
      anchor: [74.9, 374.3], at: [110, 940, 0.92], pivot: [74.9, 374.3], leanK: 0,   // 锚点 = 平衡车着地那一点；站位按遮挡判据第二版（主角算遮挡物）往左挪、离开女主身后（combo_scan.py，2026-10-01）
      depth: 0.8, recipe: 'pepper',
      /* 踩着平衡车从画外滑进来（ride：减速停住、身子往来的方向仰），刹住那一下罐子往上一扬（brake）；离场往后溜出去 */
      enter: { kind: 'ride', T: 0.55, tilt: 0.06, roll: [6, 1.9, 0.9], bob: [1.8, 2.6], seq: [['ride', 0.42], ['brake', 0.13, 'land'], ['idle', 9]], sq: 0.05 },
      exit: { frame: 'ride', T: 0.5 },
      idle: { frame: 'idle', breathe: [0.012, 0.9, 0.4] },
      /* 防狼喷雾（crew.js MIST 原样）：摇罐举起（wind）→ 按瞄准角挑 aim0~10、每按一下后坐换 kick0~10（"呲—呲—"），雾冲男生的脸 → 收罐（follow） */
      atk: { kind: 'jet', seq: [['wind', 0.22], ['aim', 2.2, 'fire'], ['follow', 0.3]], gap: [0.2, 0.45], stretch: 0,
             aim: { frames: ['aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10'],
                    kick: ['kick0', 'kick1', 'kick2', 'kick3', 'kick4', 'kick5', 'kick6', 'kick7', 'kick8', 'kick9', 'kick10'], rate: 2.4, follow: 10, sweep: { a: [0.3, 0.15], w: [1.3, 3.1] },
                    nozzle: { aim0: [225.9, 148.6, -0.7], aim1: [226.2, 134.5, -0.595], aim2: [225.1, 120.3, -0.49], aim3: [222.6, 106.2, -0.385], aim4: [218.7, 92.2, -0.28], aim5: [213.4, 78.6, -0.175], aim6: [206.7, 65.4, -0.07], aim7: [198.8, 52.9, 0.035], aim8: [189.6, 41.1, 0.14], aim9: [179.3, 30.2, 0.245], aim10: [167.9, 20.3, 0.35], kick0: [225.3, 132.1, -0.58], kick1: [224.0, 117.9, -0.475], kick2: [221.3, 103.7, -0.37], kick3: [217.1, 89.8, -0.265], kick4: [211.6, 76.3, -0.16], kick5: [204.8, 63.3, -0.055], kick6: [196.6, 50.9, 0.05], kick7: [187.3, 39.2, 0.155], kick8: [176.8, 28.5, 0.26], kick9: [165.2, 18.7, 0.365], kick10: [152.7, 10.1, 0.47] } },
             jet: { draw: 'mist', V: 1100, G: 60, drag: 1.0, rate: 90, spread: 0.1, vJit: 0.15, life: 0.8, miss: 60, snap: 12, hitEvery: 0.3,
                    pulse: [0.42, 0.14], kickDecay: 10 } },
    },
    G2: {      // 蓝发发明家（自制喷雾器）：原 crew.js 平衡车闺蜜（v14/bestie/src7.png），2026-10-01 迁成帧序列（引擎负责人）
      face: 1,
      /* crewframes.py：crew.js 在用的分层原图按 crew.js 的转轴合成（外形、配色、脸不变）；at.s 0.88 时和 crew.js 原来一样大 */
      sheet: { src: 'assets/trio/G2_bulma.webp', cell: [245, 380], cols: 4, names: ['idle', 'wind', 'follow', 'ride', 'brake', 'aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10', 'kick0', 'kick1', 'kick2', 'kick3', 'kick4', 'kick5', 'kick6', 'kick7', 'kick8', 'kick9', 'kick10'] },
      anchor: [85.9, 374.3], at: [110, 940, 0.91], pivot: [85.9, 374.3], leanK: 0,   // 锚点 = 平衡车着地那一点；站位按遮挡判据第二版（主角算遮挡物）往左挪、离开女主身后（combo_scan.py，2026-10-01）
      depth: 0.8, recipe: 'pepper',
      /* 踩着平衡车从画外滑进来（ride：减速停住、身子往来的方向仰），刹住那一下罐子往上一扬（brake）；离场往后溜出去 */
      enter: { kind: 'ride', T: 0.55, tilt: 0.06, roll: [6, 1.9, 0.9], bob: [1.8, 2.6], seq: [['ride', 0.42], ['brake', 0.13, 'land'], ['idle', 9]], sq: 0.05 },
      exit: { frame: 'ride', T: 0.5 },
      idle: { frame: 'idle', breathe: [0.012, 0.9, 0.4] },
      /* 防狼喷雾（crew.js MIST 原样）：摇罐举起（wind）→ 按瞄准角挑 aim0~10、每按一下后坐换 kick0~10（"呲—呲—"），雾冲男生的脸 → 收罐（follow） */
      atk: { kind: 'jet', seq: [['wind', 0.22], ['aim', 2.2, 'fire'], ['follow', 0.3]], gap: [0.2, 0.45], stretch: 0,
             aim: { frames: ['aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10'],
                    kick: ['kick0', 'kick1', 'kick2', 'kick3', 'kick4', 'kick5', 'kick6', 'kick7', 'kick8', 'kick9', 'kick10'], rate: 2.4, follow: 10, sweep: { a: [0.3, 0.15], w: [1.3, 3.1] },
                    nozzle: { aim0: [236.9, 148.6, -0.7], aim1: [237.2, 134.5, -0.595], aim2: [236.1, 120.3, -0.49], aim3: [233.6, 106.2, -0.385], aim4: [229.7, 92.2, -0.28], aim5: [224.4, 78.6, -0.175], aim6: [217.7, 65.4, -0.07], aim7: [209.8, 52.9, 0.035], aim8: [200.6, 41.1, 0.14], aim9: [190.3, 30.2, 0.245], aim10: [178.9, 20.3, 0.35], kick0: [236.3, 132.1, -0.58], kick1: [235.0, 117.9, -0.475], kick2: [232.3, 103.7, -0.37], kick3: [228.1, 89.8, -0.265], kick4: [222.6, 76.3, -0.16], kick5: [215.8, 63.3, -0.055], kick6: [207.6, 50.9, 0.05], kick7: [198.3, 39.2, 0.155], kick8: [187.8, 28.5, 0.26], kick9: [176.2, 18.7, 0.365], kick10: [163.7, 10.1, 0.47] } },
             jet: { draw: 'mist', V: 1100, G: 60, drag: 1.0, rate: 90, spread: 0.1, vJit: 0.15, life: 0.8, miss: 60, snap: 12, hitEvery: 0.3,
                    pulse: [0.42, 0.14], kickDecay: 10 } },
    },
    G3: {      // 月光水手少女：原 crew.js 平衡车闺蜜（v14/bestie/src8.png），2026-10-01 迁成帧序列（引擎负责人）
      face: 1,
      /* crewframes.py：crew.js 在用的分层原图按 crew.js 的转轴合成（外形、配色、脸不变）；at.s 0.88 时和 crew.js 原来一样大 */
      sheet: { src: 'assets/trio/G3_sailor.webp', cell: [250, 380], cols: 4, names: ['idle', 'wind', 'follow', 'ride', 'brake', 'aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10', 'kick0', 'kick1', 'kick2', 'kick3', 'kick4', 'kick5', 'kick6', 'kick7', 'kick8', 'kick9', 'kick10'] },
      anchor: [90.9, 374.3], at: [100, 920, 0.88], pivot: [90.9, 374.3], leanK: 0,   // 锚点 = 平衡车着地那一点；站位按遮挡判据第二版（主角算遮挡物）往左挪、离开女主身后（combo_scan.py，2026-10-01）
      depth: 0.8, recipe: 'pepper',
      /* 踩着平衡车从画外滑进来（ride：减速停住、身子往来的方向仰），刹住那一下罐子往上一扬（brake）；离场往后溜出去 */
      enter: { kind: 'ride', T: 0.55, tilt: 0.06, roll: [6, 1.9, 0.9], bob: [1.8, 2.6], seq: [['ride', 0.42], ['brake', 0.13, 'land'], ['idle', 9]], sq: 0.05 },
      exit: { frame: 'ride', T: 0.5 },
      idle: { frame: 'idle', breathe: [0.012, 0.9, 0.4] },
      /* 防狼喷雾（crew.js MIST 原样）：摇罐举起（wind）→ 按瞄准角挑 aim0~10、每按一下后坐换 kick0~10（"呲—呲—"），雾冲男生的脸 → 收罐（follow） */
      atk: { kind: 'jet', seq: [['wind', 0.22], ['aim', 2.2, 'fire'], ['follow', 0.3]], gap: [0.2, 0.45], stretch: 0,
             aim: { frames: ['aim0', 'aim1', 'aim2', 'aim3', 'aim4', 'aim5', 'aim6', 'aim7', 'aim8', 'aim9', 'aim10'],
                    kick: ['kick0', 'kick1', 'kick2', 'kick3', 'kick4', 'kick5', 'kick6', 'kick7', 'kick8', 'kick9', 'kick10'], rate: 2.4, follow: 10, sweep: { a: [0.3, 0.15], w: [1.3, 3.1] },
                    nozzle: { aim0: [241.9, 148.6, -0.7], aim1: [242.2, 134.5, -0.595], aim2: [241.1, 120.3, -0.49], aim3: [238.6, 106.2, -0.385], aim4: [234.7, 92.2, -0.28], aim5: [229.4, 78.6, -0.175], aim6: [222.7, 65.4, -0.07], aim7: [214.8, 52.9, 0.035], aim8: [205.6, 41.1, 0.14], aim9: [195.3, 30.2, 0.245], aim10: [183.9, 20.3, 0.35], kick0: [241.3, 132.1, -0.58], kick1: [240.0, 117.9, -0.475], kick2: [237.3, 103.7, -0.37], kick3: [233.1, 89.8, -0.265], kick4: [227.6, 76.3, -0.16], kick5: [220.8, 63.3, -0.055], kick6: [212.6, 50.9, 0.05], kick7: [203.3, 39.2, 0.155], kick8: [192.8, 28.5, 0.26], kick9: [181.2, 18.7, 0.365], kick10: [168.7, 10.1, 0.47] } },
             jet: { draw: 'mist', V: 1100, G: 60, drag: 1.0, rate: 90, spread: 0.1, vJit: 0.15, life: 0.8, miss: 60, snap: 12, hitEvery: 0.3,
                    pulse: [0.42, 0.14], kickDecay: 10 } },
    },
    /* ---- 帧序列（新标准） ---- */
    G11: {      // 花饰格格：秋千从左上画外荡进来（往前荡伸腿、往后荡收腿），荡到最前面抛绣球砸他的头
      face: +1,
      sheet: { src: 'assets/trio/G11_gege.webp', cell: [315, 343], cols: 4, names: ['idle', 'raise', 'throw', 'follow', 'wind', 'tuck', 'kick', 'idle2', 'release', 'through'] },
      anchor: [128, 212.3], at: [170, 480, 1], pivot: [128, -530], leanK: 0.5,   // y 640 → 540 → 500（引擎负责人 2026-10-01，遮挡判据第二版：后排 G5 挪到 [230, 960] 以后 540 时她被挡 15.5%）
      depth: 0.5, recipe: 'petal',
      /* 进场：0.4 秒从左上画外露面时收着腿俯冲（tuck），0.6 秒荡到最低点（摆角过零）伸腿（kick）往前荡，0.75 秒接出手 */
      enter: { kind: 'swing', seq: [['tuck', 0.6], ['kick', 9]] },
      /* 绳子、座板由引擎画（帧里的座板已抠掉）：ends 座板两头、grip 这一帧哪只手握着绳 [左手, 右手]、board 座板的框 */
      ropes: { ...ROPE, ends: [[50, 207], [208, 207]], board: [44, 205, 214, 222], flowers: '#f59ab8',
               grip: { idle: [[49, 63]], raise: [[44, 63]], throw: [[69, 76]], release: [[69, 76]], through: [[69, 76]], follow: [[57, 60]], wind: [[25, 72]],
                       tuck: [[98, 60], [227, 63]], kick: [[47, 66], [176, 60]] } },
      swing: { a0: 1.3, a: 0.13, tau: 0.45, w: 2.6, pump: { fwd: 'kick', back: 'tuck', min: 0.3 } },
      exit: { frame: 'tuck' },
      idle: { frame: 'idle', breathe: [0.014, 0.45] },
      /* 帽子后面那根流苏：下端贴着肩膀，画不出三边透明的 flex 框，拆成挂件层（frames.json 的 lift，帧里原位置已补画）。
         顶上的结挂住，自己慢慢晃（0.08 rad，尖上 ±4 px），秋千摆的时候往后拖（跟摆 0.25 × 摆的角速度） */
      parts: [{ src: 'assets/trio/G11_tassel.webp', pivot: [7, 0], z: 1, sway: [0.08, 0.8, 0.25],
                at: { idle: [80, 30, 0], raise: [84.5, 24, 0], throw: [107, 43, 0], release: [107, 43, 0], through: [107, 43, 0], follow: [81, 30, 0], wind: [54.5, 39, 0], tuck: [135, 34, 0], kick: [58.5, 39, 0], idle2: [79, 34, 0] } }],
      atk: { kind: 'throw', item: 'ball', prop: 'assets/world/trio_prop_ball.webp', scale: 0.5,
             seq: [['raise', 0.12], ['wind', 0.24], ['release', 0.06, 'fire'], ['throw', 0.1], ['through', 0.12], ['follow', 0.25]],   // 精闺1 P6：release 手臂伸到最远离手，through 手腕下垂（只重画右臂，头身 = throw）
             hold: { idle: [176, 172], raise: [63, 26], wind: [14, 146], release: [292, 48], throw: [277, 38] }, dir: { release: 19.4 },   // wind → release 手位移 19.4°（引擎原量 throw 22.3°）
             T: 0.5, arc: 0.25, spin: 5, idleSpin: 0.8, stretch: 0.04, onHit: 'bounce' },
    },

    G23: {      // 客栈女侠（郭芙蓉式）：马步从左下角滑进来、跺地站定，排山倒海 —— 双掌齐推，一道气浪轰他的脸
      face: +1,
      sheet: { src: 'assets/trio/G23_furong.webp', cell: [474, 347], cols: 4, names: ['idle', 'raise', 'throw', 'follow', 'slide', 'land', 'wind', 'idle2', 'release'] },
      anchor: [253.1, 345.4], at: [175, 1330, 1], pivot: [253, 345],
      leanK: 0,   // 马步两只靴子离锚点各 150px：整体前后倾会把靴子一上一下翘起来，蓄力 / 出手全靠帧
      depth: 1.3, recipe: 'thud',
      /* slide 帧（弓步滑）人一露面就在画 → land（跺进马步，压扁）→ idle。wind / idle2 是第二张条里的，马步画宽了一截，不上场 */
      enter: { kind: 'slide', seq: [['slide', 0.5], ['land', 0.14, 'land'], ['idle', 9]], sq: 0.12 },
      exit: { frame: 'slide' },
      idle: { frame: 'idle', breathe: [0.018, 0.75, 0] },   // 站马步：只竖向起伏（绕两靴之间的地面），横向不补 —— 不然两只靴子左右挪
      /* 发带下面那截飘带：上沿钉住，下端左右甩（框只有上沿压着飘带，其余三边透明） */
      flex: { idle: [[140, 102, 190, 126, 't', 8, 1.2]] },
      atk: { kind: 'beam', seq: [['raise', 0.34], ['release', 0.4, 'fire'], ['follow', 0.3]], dir: { release: 48 },   // 精闺1：双掌往前上推 48°（所需 39°），光束从掌心直出
             hold: { raise: [185, 165], throw: [390, 120], release: [345, 22] }, stretch: 0.03, gap: [1.0, 1.4],   // raise：两只手掌收在腰侧之间那一点（蓄力球画在这）
             /* 气浪：比悟空的光线粗一倍（排山倒海是一堵墙推过去，不是一根线）；最外一层暗红给它在暖色客厅上描个边 */
             beam: { fire: 0.38, drip: 0.1, ball: 40, glow: [255, 170, 70], edge: [220, 60, 30],
                     layers: [[84, [170, 30, 20], 0.3], [64, [255, 90, 40], 0.6], [42, [255, 160, 70], 0.85], [20, [255, 230, 160], 1], [7, [255, 255, 255], 1]] } },
    },

    G21: {      // 忍者扇娘（不知火舞式）：左下角翻滚进来（团身滚 → 落地蹲 → 半跪），胸罩当手里剑甩出去，打中挂在他头上
      face: +1,
      sheet: { src: 'assets/trio/G21_mai.webp', cell: [385, 384], cols: 4, names: ['idle', 'wind0', 'throw', 'follow', 'roll', 'land', 'wind', 'idle2', 'release'] },
      anchor: [190.6, 378.4], at: [150, 1310, 1], pivot: [190, 378],
      leanK: 0,   // 半跪：绕地面转会把着地的膝盖和前脚翘起来
      depth: 1.3, recipe: 'rouge',
      enter: { kind: 'roll', seq: [['roll', 0.5], ['land', 0.14, 'land'], ['idle', 9]], sq: 0.1 },
      exit: { frame: 'roll' },
      idle: { frame: 'idle', breathe: [0.016, 0.7, 0] },
      /* 前脚脚尖不耐烦地点地：脚踝钉住（'l'），脚尖上下点（框上、右、下三边透明） */
      flex: { idle: [[286, 357, 310, 383, 'l', 6, 0.9]] },
      /* wind0（第一张条的蓄力，手只到肩后）当蓄力前段，wind（第二张条的强蓄力，手甩到身后）接着 */
      atk: { kind: 'throw', item: 'bra', prop: 'assets/world/trio_prop_bra.webp', scale: 0.55,
             seq: [['wind0', 0.1], ['wind', 0.2], ['release', 0.06, 'fire'], ['throw', 0.12], ['follow', 0.28]], dir: { release: 57 },   // 精闺1：release 出手瞬间（手臂甩到最前上方、手在最远点，自检 4.4 所需角度）→ 原 throw 帧接着当跟随；dir = 肩 → 手（图集上量）
             hold: { idle: [164, 257], wind0: [90, 177], wind: [84, 223], throw: [333, 177], release: [343, 12] },
             T: 0.45, arc: 0.18, spin: 16, idleSpin: 0.8, stretch: 0.03, gap: [1.0, 1.4], onHit: 'wear' },
    },
    G22: {      // 麻花辫探险家（劳拉式）：左下角匍匐爬进来（左右肘交替）趴定，举相机拍照取证，闪光晃他的眼，照片飞出来
      face: +1,
      sheet: { src: 'assets/trio/G22_explorer.webp', cell: [466, 183], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'crawl1', 'crawl2', 'land', 'idle2'] },
      anchor: [223.0, 152.6], at: [200, 1314, 1], pivot: [223, 152],
      leanK: 0,   // 趴着的人不整体前后倾（同樱木）
      depth: 1.3, recipe: 'star',
      enter: { kind: 'creep', seq: [['crawl1', 0.14], ['crawl2', 0.14], ['crawl1', 0.14], ['crawl2', 0.14], ['land', 0.1, 'land'], ['idle', 9]], sq: 0.08 },
      exit: { frame: 'crawl2' },
      idle: { frame: 'idle', breathe: [0.02, 0.7, 0] },   // 趴着：只竖向起伏
      /* 垂到地上的麻花辫梢：顶边钉住，辫梢轻晃（框左、右、下三边透明，flexfind） */
      flex: { idle: [[300, 150, 344, 174, 't', 3, 0.9]] },
      /* 翘起来的两条小腿 + 靴子是挂件层（bestie/G22_explorer/legs.py 从 idle 拆出来，四个在场帧里原处已清掉）：
         绕小腿中段的切口来回晃 = 趴着懒洋洋晃脚。爬的帧（腿平放）不画。切口两层重叠 4 行、重叠处硬边（不然叠出一道 1 px 暗线） */
      parts: [{ src: 'assets/trio/G22_legs.webp', pivot: [61.5, 96], z: 1, sway: [0.06, 0.6, 0],
                at: { idle: [99.5, 100, 0], wind: [99.5, 100, 0], throw: [99.5, 100, 0], follow: [99.5, 100, 0] } }],
      atk: { kind: 'camera', seq: [['wind', 0.3], ['throw', 0.12, 'fire'], ['follow', 0.35]],
             hold: { throw: [424, 50] }, stretch: 0, gap: [1.0, 1.4] },
    },

    G24: {      // 宫斗贵妃（华妃式）：侧卧着从左下角滑进来、撑肘起身扶正旗头，弹出一枚金护甲砸他 —— 赏"一丈红"（打中炸红粉）
      face: +1,
      sheet: { src: 'assets/trio/G24_huafei.webp', cell: [570, 303], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'slide', 'land', 'wind2', 'idle2', 'release'] },
      anchor: [393.1, 291.8], at: [280, 1325, 1], pivot: [393, 291],
      leanK: 0,   // 侧卧：整体前后倾会把贴地的腿翘起来
      depth: 1.3, recipe: 'rouge',
      enter: { kind: 'slide', seq: [['slide', 0.45], ['land', 0.16, 'land'], ['idle', 9]], sq: 0.1 },
      exit: { frame: 'slide' },
      idle: { frame: 'idle', breathe: [0.016, 0.7, 0] },   // 躺着：只竖向起伏，不横向补（贴地的脚不左右挪）
      /* 两只脚尖懒洋洋地翘：小腿钉住（'l'），往右越翘越高（框上、右、下三边透明） */
      flex: { idle: [[488, 235, 529, 302, 'l', 7, 0.8]] },
      /* 金护甲：bestie/tools/prop_nailguard.py 程序画的（她手指上的护甲跟手指叠着，抠不出来） */
      atk: { kind: 'throw', item: 'nailguard', prop: 'assets/world/trio_g24_nailguard.webp', scale: 0.45,
             seq: [['wind', 0.26], ['release', 0.06, 'fire'], ['throw', 0.12], ['follow', 0.26]], dir: { release: 60 },   // 精闺1：release 出手瞬间（手臂甩到最前上方、手在最远点，自检 4.4 所需角度）→ 原 throw 帧接着当跟随；dir = 肩 → 手（图集上量）
             hold: { wind: [167, 144], throw: [461, 169], release: [428, 20] },
             T: 0.5, arc: 0.2, spin: 12, stretch: 0, gap: [1.0, 1.4], onHit: 'bounce' },
    },
    G25: {      // 大针筒护士：踩着输液架轮座从左下角滑进来、跳下来半跪扶着输液架，甩一支巨型针筒飞镖，扎在他头上
      face: +1,
      sheet: { src: 'assets/trio/G25_nurse.webp', cell: [394, 402], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'ride', 'hop', 'wind2', 'idle2', 'release'] },
      anchor: [232.3, 398.5], at: [185, 1330, 1], pivot: [232, 398],
      leanK: 0,   // 半跪：整体前后倾会把着地的膝盖和脚带起来
      depth: 1.3, recipe: 'rouge',
      /* 输液架画在帧里（她一直扶着）：进场踩在轮座上滑、跳下来落成半跪 */
      enter: { kind: 'slide', seq: [['ride', 0.42], ['hop', 0.14], ['idle', 9, 'land']], sq: 0.1 },
      exit: { frame: 'ride' },
      idle: { frame: 'idle', breathe: [0.016, 0.8, 0] },
      /* 前脚鞋尖点地：脚踝钉住（'l'），往右越翘越高（框上、右、下三边透明） */
      flex: { idle: [[268, 365, 298, 401, 'l', 7, 1.0]] },
      /* 巨型针筒：tools/3d/syringe.py 3D 转盘；扎在头上那一支用平面图（onHit 'wear' 只画 prop） */
      atk: { kind: 'throw', item: 'syringe', r: 36, atlas: { src: 'assets/trio/prop_syringe.webp', n: 36, cols: 6, cell: 128, scale: 1.10 },
             prop: 'assets/world/trio_g25_syringe.webp',
             seq: [['wind', 0.26], ['release', 0.06, 'fire'], ['throw', 0.12], ['follow', 0.26]], dir: { release: 47 },   // 精闺1：release 出手瞬间（手臂甩到最前上方、手在最远点，所需 47°）→ 原 throw 帧接着当跟随；dir = 肩 → 手（图集上量）
             hold: { idle: [158, 150], wind: [140, 132], throw: [337, 169], release: [262, 42] },
             T: 0.5, arc: 0.15, spin: 6.3, idleSpin: 0.6, stretch: 0.03, gap: [1.0, 1.4], onHit: 'wear' },
    },
    G30: {      // 葫芦山蛇精式妖女：像蛇一样左右扭着从左下角滑进来、斜倚坐起，举如意放一道绿光吸住他
      face: +1,
      sheet: { src: 'assets/trio/G30_snake.webp', cell: [577, 385], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'slither1', 'slither2', 'wind2', 'idle2', 'release'] },
      anchor: [268.2, 386.8], at: [200, 1332, 1], pivot: [268, 386],
      leanK: 0,   // 斜倚在地上：整体前后倾会把贴地的蛇尾裙摆翘起来
      depth: 1.3, recipe: 'star',
      /* 进场：贴地 S 形扭滑，两帧左右扭交替；待机用 follow（如意横在膝前）——
         动作条左上那格 idle（如意扛肩）的头比其余几格画大了 6%（frames.json 缩放锁 1，按身子对齐），不上场 */
      enter: { kind: 'slide', seq: [['slither1', 0.13], ['slither2', 0.13], ['slither1', 0.13], ['slither2', 0.13], ['follow', 9, 'land']], sq: 0.08 },
      exit: { frame: 'slither2' },
      idle: { frame: 'follow', breathe: [0.016, 0.7, 0] },
      /* 发髻上垂下的翠玉流苏：顶钉住（'t'），框左、右、下三边透明 */
      flex: { follow: [[290, 223, 300, 248, 't', 6, 1.1]] },
      /* 如意画在帧里：往后抡（wind2）→ 举过头顶（wind）→ 指向他放光（throw）→ 收回膝前（follow = 待机） */
      atk: { kind: 'beam', seq: [['wind2', 0.18], ['wind', 0.2], ['release', 0.5, 'fire'], ['follow', 0.3]], dir: { release: 59 },   // release = throw 手臂连如意绕肩上举 50°（切件，bestie/G30_snake/armrelease.py；原局部重绘帧上半身比例不对、缺一条），手臂 59°（所需 69°，差 10°），光从如意头直出
             hold: { wind2: [254, 227], wind: [280, 124], throw: [522, 234], release: [449.3, 126.1] }, stretch: 0, gap: [1.0, 1.4],
             beam: { fire: 0.45, drip: 0.1, ball: 30, glow: [120, 255, 150], edge: [20, 120, 60],
                     layers: [[40, [20, 120, 60], 0.3], [28, [60, 200, 100], 0.6], [16, [140, 255, 170], 0.9], [6, [240, 255, 240], 1]] } },
    },
    G26: {      // 蝴蝶发饰剑士（蝴蝶忍式）：从左上轻轻一跃、张开蝴蝶羽织落地蹲下，挥袖放出一群毒蝴蝶扑过去
      face: +1,
      sheet: { src: 'assets/trio/G26_shinobu.webp', cell: [423, 391], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'leap', 'land', 'wind2', 'idle2', 'release'] },
      anchor: [219, 386.1], at: [175, 1330, 1], pivot: [219, 386],
      leanK: 0,   // 蹲着：整体前后倾会把着地的木屐带起来
      depth: 1.3, recipe: 'petal',
      /* 轻跳落地：h 小（身形轻），腾空张开羽织 → 脚尖点地 → 蹲下 */
      enter: { kind: 'leap', h: 70, air: 0.45, sq: 0.1, seq: [['leap', 0.45], ['land', 0.14, 'land'], ['idle', 9]] },
      exit: { frame: 'leap' },
      idle: { frame: 'idle', breathe: [0.018, 0.75, 0] },
      /* 羽织袖子垂下的那一角（蝴蝶翅尖）：顶钉住（'t'），框左、右、下三边透明 */
      flex: { idle: [[118, 285, 160, 332, 't', 7, 0.9]] },
      /* 毒蝴蝶：tools/3d/butterfly.py 3D 转盘齐射件，一次放 5 只；待机时指尖停着一只 */
      atk: { kind: 'throw', item: 'butterfly', r: 22, n: 5, atlas: { src: 'assets/trio/prop_butterfly.webp', n: 36, cols: 6, cell: 76, scale: 1.13 },
             seq: [['wind2', 0.26], ['release', 0.06, 'fire'], ['throw', 0.12], ['follow', 0.26]], dir: { release: 40 },   // 精闺1：release 出手瞬间（手臂甩到最前上方、手在最远点，自检 4.4 所需角度）→ 原 throw 帧接着当跟随；dir = 肩 → 手（图集上量）
             hold: { idle: [193, 137], wind2: [93, 142], throw: [366, 125], release: [395, 20] },
             T: 0.6, arc: 0.3, spin: 5.2, idleSpin: 0.5, stretch: 0.03, gap: [1.0, 1.4] },
    },
    G27: {      // 暴脾气平民女孩（杉菜式）：从左下角冲过来一记滑铲、撑地起身半跪，抡起书包砸过去
      face: +1,
      sheet: { src: 'assets/trio/G27_shancai.webp', cell: [417, 404], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'tackle', 'rise', 'wind2', 'idle2', 'release'] },
      anchor: [174, 398.1], at: [170, 1330, 1], pivot: [174, 398],
      leanK: 0,   // 半跪：整体前后倾会把跪地的膝盖带起来
      depth: 1.3, recipe: 'thud',
      /* 滑铲进来（前脚鞋底朝前）→ 刹住撑地起身 → 半跪；wind / follow 两帧的前腿按 idle 挪正过（G27_shancai/fixleg.py，build 后必跑） */
      enter: { kind: 'slide', seq: [['tackle', 0.46], ['rise', 0.14, 'land'], ['idle', 9]], sq: 0.1 },
      exit: { frame: 'tackle' },
      idle: { frame: 'idle', breathe: [0.018, 0.8, 0] },
      /* 脑后翘起的短发梢：根在右边钉住（框上、下、左三边透明，flexfind） */
      flex: { idle: [[138, 112, 158, 160, 'r', 4, 0.9]] },
      /* 书包：引擎 3D 转盘（tools/3d/schoolbag.py，道具表 r 30 cell 115 scale 1.37）；待机拎着书包带在手里晃（idleSpin） */
      atk: { kind: 'throw', item: 'schoolbag', r: 30, atlas: { src: 'assets/trio/prop_schoolbag.webp', n: 36, cols: 6, cell: 115, scale: 1.37 },
             seq: [['wind', 0.26], ['release', 0.06, 'fire'], ['throw', 0.12], ['follow', 0.26]], dir: { release: 37.5 },   // 精闺1：release 出手瞬间（手臂甩到最前上方、手在最远点，自检 4.4 所需角度）→ 原 throw 帧接着当跟随；dir = 肩 → 手（图集上量）
             hold: { idle: [156, 208], wind: [50, 242], throw: [306, 110], release: [400, 25] },
             T: 0.5, arc: 0.22, spin: 6.3, idleSpin: 0.9, stretch: 0.03, gap: [1.0, 1.4], onHit: 'bounce' },
    },
    G28: {      // 80 年代健美操女：从左边一路开合跳进来，指尖转着呼啦圈，甩出去套在他头上
      face: +1,
      sheet: { src: 'assets/trio/G28_aerobics.webp', cell: [381, 457], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'jump1', 'jump2', 'jump3', 'jump4', 'release'] },
      anchor: [178.9, 436.5], at: [155, 1330, 0.9], pivot: [178, 436],
      leanK: 0,   // 两脚大开站定：整体前后倾绕两脚中点转，离中点 120 px 的脚会上下挪 7 px（量出来的）
      depth: 1.3, recipe: 'star',
      /* 开合跳：jump1 并腿落地 → jump2 腾空张开 → jump3 开腿落地、双臂举成 V → jump4 腾空合拢（偶数帧接地、奇数帧 bob 抬起，规范第九节 G28）。
         stride = 每跳前进的距离（格内像素）：接地 → 腾空 → 接地换两次帧，每次前进 stride / 2 */
      enter: { kind: 'walk', fps: 6, bob: 40, stride: 110, dist: 346.5, seq: [[['jump1', 'jump2', 'jump3', 'jump4'], 9]] },
      exit: { frame: ['jump1', 'jump2', 'jump3', 'jump4'], fps: 8, flip: true, T: 0.8 },
      idle: { frame: 'idle', breathe: [0.014, 0.9] },
      /* 呼啦圈：引擎 3D 转盘（道具表 r 36 cell 108 scale 1.07），待机顶在指尖上转；套在他头上那只用图集第 4 格（压扁的椭圆）当平面图。
         收势用 jump3（双臂举成 V 欢呼）：A 条的 follow 那格头画小了 9%，按头缩放后脚踩到地板下 17 px，不上场 */
      atk: { kind: 'throw', item: 'hoop', r: 36, atlas: { src: 'assets/trio/prop_hoop.webp', n: 36, cols: 6, cell: 108, scale: 1.07 },
             prop: 'assets/world/trio_g28_hoop.webp',
             seq: [['wind', 0.26], ['release', 0.06, 'fire'], ['throw', 0.12], ['jump3', 0.3]], dir: { release: 53.5 },   // 精闺1：release 出手瞬间（手臂甩到最前上方、手在最远点，自检 4.4 所需角度）→ 原 throw 帧接着当跟随；dir = 肩 → 手（图集上量）
             hold: { idle: [124, 80], wind: [67, 236], throw: [335, 154], release: [330, 65] },
             T: 0.55, arc: 0.25, spin: 5.7, idleSpin: 2.5, stretch: 0.03, gap: [1.0, 1.4], onHit: 'wear' },
    },
    G29: {      // 打狗棒女侠（黄蓉式）：撑着打狗棒从左上一跃、棒子点地荡进来落成蹲，竹棒伸缩着捅过去
      face: +1,
      sheet: { src: 'assets/trio/G29_huangrong.webp', cell: [444, 387], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'vault', 'swing', 'land', 'idle2', 'release'] },
      anchor: [228.4, 371.7], at: [180, 1328, 0.98], pivot: [228, 371],
      leanK: 0,   // 蹲着：整体前后倾会把撑地的手和靴子带起来
      depth: 1.3, recipe: 'thud',
      /* 撑棒跃进：双手握棒顶腾空（vault）→ 收腿荡过去（swing）→ 落地蹲下单手撑地（land）→ 待机 */
      enter: { kind: 'leap', h: 120, air: 0.45, sq: 0.1, seq: [['vault', 0.25], ['swing', 0.2], ['land', 0.14, 'land'], ['idle', 9]] },
      exit: { frame: 'vault' },
      idle: { frame: 'idle', breathe: [0.018, 0.75, 0] },
      /* idle / idle2 / wind / throw 原图两只手各有去处（举拳握棒 + 前伸 / 扶膝 / 握短棒）却还画着一只撑地的手 = 三只手（2026-10-02 用户指出）：
         撑地那条前臂局部重绘成膝盖和衣摆（bestie/G29_huangrong/nohand/：蒙版、生成图、reg.py 配回原格），land / release 只有一只手在别处，撑地手保留。
         release 原来只把上半身（格内 y < 172）贴回 throw 底格，拼缝横穿后面那只胳膊（上截新画、下截旧袖子、中间半透明过渡带）：10-02 改成整张用生图（addframes.json 去掉 paste: 'box'），出手手位 (+1, −5) 跟着平移 */
      /* 打狗棒：定妆拆好的挂件层（bestie/ref/G29_staff.png → tools/part.py h 281），挂点 = 握棒处（棒长 80% 那一点）。
         待机 / 落地：握在举起的左拳里、斜靠在背后；腾空两帧：双手握棒顶、棒子往下（转 π，荡的那帧更竖）；
         wind / throw / follow 不画（这几帧手里画着一截短竹棒，捅出去的就是它） */
      parts: [{ src: 'assets/trio/G29_staff.webp', pivot: [107, 222], z: -1, sway: [0.04, 0.7, 0],
                at: { idle: [160, 157, 0], land: [151, 235, 0], vault: [222, 52, 3.1416], swing: [210, 120, 3.44] } }],
      /* 伸缩棒（帧序列 punch）：手握着不动，棒头（release 帧画里竹棒的末端）沿竹棒轴线伸出去，中间的"管子"填竹子色；收势 = 收棒回腰（用 wind 帧）——
         A 条 follow（棒扛肩）那格两腿站位画得不一样（配准残差 6.7 px），不上场。
         10-02（用户：手臂还是不对）：原来 fist 框的是握棒的手，出手时手被抠走送到棒尖、胳膊上只剩空袖口，伸出去的管子还比画里的棒低 12~15 px、角度差 6°（读成两根棒）。
         现在 wrist = 棒从手里出来那一点、fistC / fist = 棒尖，两点都在画里竹棒的轴线上（release 帧 x > 345 的不透明像素拟合：34°，y = 300.8 − 0.679x），管子粗 ≈ 画里棒粗 7 */
      atk: { kind: 'punch', seq: [['wind', 0.3], ['release', 0.55, 'fire'], ['throw', 0.12], ['wind', 0.2]], dir: { release: 34 },   // 画里竹棒 34°（所需 33°），伸出去的棒沿 wrist → fistC
             fist: [400, 10, 420, 33], fistC: [410, 22.4], wrist: [346, 66], armW: 7,
             skin: '#6cbf45', skinShade: 'rgba(40,110,30,.55)', skinEdge: '#1f3d12', fistZ: 1, phases: [0.16, 0.12, 0.22],
             stretch: 0, gap: [1.0, 1.4] },
    },
    /* ---- 后排地面（站在女生身后左边、画在主角之后；样板 B5，规范 4.3 / 6.4 后排出手翻过自己主角头顶） ---- */
    G4: {       // 丸子头旗袍格斗家（春丽式）：倒立劈叉旋转踢从左边转进来、落地一蹲、站成格斗架；百裂脚 —— 右腿高踢连踢，一串腿影从女生头顶翻过去砸他
      face: +1,
      sheet: { src: 'assets/trio/G4_chunli.webp', cell: [613, 522], cols: 4, names: ['idle', 'wind', 'hitA', 'hitB', 'spin1', 'spin2', 'land', 'follow', 'hitC', 'hitD', 'idle2', 'hitE'] },
      /* 锚点 = 前脚（右脚）鞋底：踢腿是后腿踢、站在前脚上，出手四帧按这只靴子配准（残差 0.38 px）。
         后排：脚底 y 1040（同组地板 G21 头顶 1052，不叠），x 250 在女生身后左边，站姿高约 350 px */
      anchor: [327.5, 502.5], at: [190, 960, 0.82],   /* 精闺1：连踢改成往右下踢向男主后，脚压低、hitE 被地板 G21 挡 28.4% → combo_scan --only=G4 建议站位抬 20 */ pivot: [327, 502], leanK: 0,
      depth: 0.8, recipe: 'star',
      /* 翻滚进来：整张图转一圈（引擎 roll）的同时帧在换 —— 倒立劈叉 → 斜劈叉 → 倒立劈叉 → 落地一蹲（压扁）→ 格斗架 */
      enter: { kind: 'roll', T: 0.9, seq: [['spin1', 0.2], ['spin2', 0.2], ['spin1', 0.3], ['land', 0.2, 'land'], ['idle', 9]], sq: 0.1 },
      exit: { frame: 'spin2' },
      idle: { frame: 'idle', breathe: [0.014, 0.8, 0], alt: { frame: 'idle2', every: [2, 4], hold: [0.8, 1.2] } },   // 两脚站定：只竖向起伏，后脚不左右挪；idle2 = 眨眼、拇指擦鼻尖（精闺1 P7）
      /* 包子套上的白飘带往后（左）飘：根在右边（钉右），其余三边透明 */
      flex: { idle: [[128, 134, 169, 200, 'r', 10, 1.1]] },
      /* 百裂脚：抬膝蓄力 → 高踢 / 平踢每秒 10 帧交替 0.6 秒、每 0.1 秒一道腿影飞过去 → 比 V 收势。
         出手点 = hitA 踢过头顶的那只靴子（后排：腿影从女生头顶翻过去） */
      /* 精闺1 P6：连踢 4 帧循环 收腿 hitC → 侧踢 hitD → 收腿 hitC → 正蹬 hitE（都是 hitB 上身原样、只重画踢的那条腿：bestie/tools/addframes.py），每秒 12 帧；两脚踢都略往下、沿腿指向男主 */
      atk: { kind: 'rush', seq: [['wind', 0.3], [['hitC', 'hitD', 'hitC', 'hitE'], 0.6, 'fire'], ['follow', 0.5]], fps: 12, from: [588, 333], dir: { hitD: -17, hitE: -19 },   // 腿影沿腿飞向男主：髋（屏幕 ≈ (217, 753)）→ 男主 (616, 837) 是 −12°，hitD −17° / hitE −19°（髋 → 靴尖，图集上量），差 ≤ 7°；hitA 竖踢 / hitB 往上踢不进连踢（审查 −34° 是从旧 from 高踢靴尖算的）
             rush: { n: 6, every: 0.1, T: 0.1, line: '#bfe0ff',
                     ghost: [{ frame: 'hitD', box: [365, 235, 605, 345] }, { frame: 'hitE', box: [365, 235, 613, 362] }] },
             gap: [0.8, 1.2], stretch: 0.03 },
    },

    G5: {       // 客栈老板娘（佟湘玉式）：腰侧挂着大算盘、叉着腰扭着走进来，惊呼"额滴神"；摘下算盘举过头顶，一把 3D 算盘甩出去砸他
      face: +1,
      sheet: { src: 'assets/trio/G5_tong.webp', cell: [399, 464], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'walk1', 'walk2', 'walk3', 'walk4', 'release', 'through', 'idle2'] },
      /* 锚点 = 前脚（右脚）鞋底：出手四帧按这只鞋配准（残差 0.23 px）。站姿高约 350 px；站位按 shots/trio_std/建议站位_最终.md */
      anchor: [230.4, 458.3], at: [150, 980, 0.84], pivot: [230, 458], leanK: 0,
      depth: 0.8, recipe: 'debris',
      /* 扭腰走：走路条四帧出自同一张底图（raw/act_b1.png），walk1 / walk3 接地（两腿对调）、walk2 / walk4 过渡；左手一直叉腰，右手 后 → 中 → 前 → 中。
         stride 119 = 相邻两帧着地那只鞋的鞋跟距离（61 / 58 / 59 / 58）× 2 的平均：每次换帧前进 59.5，同一只脚前后差 ≤ 1.5（格内像素）。
         dist = 6 步 × 59.5 × s，写死：不写时引擎按 cell × s + 30 取整成 6 步、每步压短 0.3 px */
      enter: { kind: 'walk', fps: 6, bob: 6, stride: 119, dist: 299.9, seq: [[['walk1', 'walk2', 'walk3', 'walk4'], 9]] },
      exit: { frame: ['walk1', 'walk2', 'walk3', 'walk4'], fps: 8, flip: true, T: 0.8 },
      idle: { frame: 'idle', breathe: [0.014, 0.8, 0], alt: { frame: 'idle2', every: [1.2, 2.2], hold: [0.6, 1.0] } },   /* idle2 = 头绕脖子歪 9°（切件，bestie/G5_tong/headidle2.py，身子逐像素同 idle）；原整张重生的 idle2 头顶高 56 px，769478b 停用后换掉 */
      /* 算盘是挂件层，和甩出去的是同一把：3D 图集 prop_abacus 最正面那一格转正（bestie/G5_tong/abacus_part.py，屏幕长边 90 px，改 s 要重跑），
         上面一根红吊绳吊在左胯，绕绳结晃；举过头顶 / 甩出去那两帧不画（在手里的是 3D 算盘）。
         ammo: true = 胯上这把就是甩出去的那把：飞出去还没落完就不画（不然 follow 帧胯上一把、空中一把），落完从吊绳结长回来 */
      parts: [{ src: 'assets/trio/G5_abacus.webp', pivot: [55, 3], z: 1, sway: [0.1, 0.9, 0], ammo: true,
                at: { idle: [118, 238, 0], follow: [118, 246, 0], walk1: [124, 250, 0], walk2: [118, 250, 0], walk3: [124, 250, 0], walk4: [118, 250, 0], idle2: [118, 238, 0] } }],   // idle2 身子同 idle
      /* 两手举过头顶（后排：出手点在女生头顶以上）→ 往前甩出 → 捂胸叹气。3D 算盘照道具表 r 40 cell 115 scale 1.35，转速 π / T */
      atk: { kind: 'throw', item: 'abacus', r: 40, atlas: { src: 'assets/trio/prop_abacus.webp', n: 36, cols: 6, cell: 115, scale: 1.35 },
             seq: [['wind', 0.26], ['release', 0.06, 'fire'], ['throw', 0.1], ['through', 0.12], ['follow', 0.25]],   // 精闺1 P6：release 出手瞬间 / through 跟随（bestie/tools/addframes.py）
             hold: { wind: [228, 56], release: [368, 62], throw: [340, 96] }, dir: { release: -2.5 },   // dir = 出手瞬间手的运动方向（hold wind → release），v14/trio/bestie/tools/dircheck.py 验过能落到男主
             T: 0.55, arc: 0.25, spin: 5.7, idleSpin: 0.6, stretch: 0.03, gap: [1.0, 1.4], onHit: 'bounce' },
    },

    G6: {       // 平底锅主妇（蜡笔小新妈式）：额头冒青筋、围裙拖鞋气冲冲跑进来，攥着平底锅；把锅举过头顶抡出去，3D 平底锅"当"地砸在他头上
      face: +1,
      sheet: { src: 'assets/trio/G6_misae.webp', cell: [396, 427], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'walk1', 'walk2', 'walk3', 'walk4', 'release', 'through', 'idle2'] },
      /* 锚点 = 前脚拖鞋鞋底：出手四帧按这只拖鞋配准（残差 0.31 px）。脚底 y 1040（同组地板 G30 头顶 1057），站姿高约 350 px */
      anchor: [260.6, 421.1], at: [170, 980, 0.88], pivot: [260, 421], leanK: 0,
      depth: 0.8, recipe: 'thud',
      /* 气冲冲跑进来：跑步条四帧出自同一张底图（raw/walk_base.png；walk3 的两臂用蒙版重绘成和 walk1 反过来：近手往前捶、远手甩到背后，raw/act_b1.png）。
         每秒 12 帧、一步一伏 10 px。stride 175：相邻两帧着地那只拖鞋的鞋跟前进 82 / 92 / 86 / 90（格内像素），取平均 87.5 × 2；同一只脚换帧差 ≤ 5.5 格内（≤ 4.8 屏幕 px） */
      enter: { kind: 'walk', fps: 12, bob: 10, stride: 175, dist: 308, seq: [[['walk1', 'walk2', 'walk3', 'walk4'], 9]] },
      exit: { frame: ['walk1', 'walk2', 'walk3', 'walk4'], fps: 12, flip: true, T: 0.6 },
      idle: { frame: 'idle', breathe: [0.016, 0.9, 0], alt: { frame: 'idle2', every: [2, 4], hold: [0.9, 1.4] } },   // idle2 = 抱胳膊鼓腮生闷气（精闺1 P7）
      /* 后脑勺那一撮卷发往后（左）甩：根在右边（钉右），框上、下、左三边透明 */
      flex: { idle: [[148, 58, 168, 112, 'r', 9, 1.0]] },
      /* 平底锅照道具表 3D：r 30 cell 91 scale 1.08，转速 π / T。待机攥在右拳里（慢慢晃着转），蓄力举过头顶（后排：出手点在女生头顶以上），出手后叉腰喘粗气 */
      atk: { kind: 'throw', item: 'pan', r: 30, atlas: { src: 'assets/trio/prop_pan.webp', n: 36, cols: 6, cell: 91, scale: 1.08 },
             seq: [['wind', 0.24], ['release', 0.06, 'fire'], ['throw', 0.1], ['through', 0.12], ['follow', 0.25]],   // 精闺1 P6：release 出手瞬间 / through 跟随（bestie/tools/addframes.py）
             hold: { idle: [258, 236], idle2: [240, 155], wind: [160, 30], release: [352, 66], throw: [336, 96] }, dir: { release: -10.6 },   // dir = 手的运动方向（wind → release），dircheck 验过
             T: 0.55, arc: 0.3, spin: 5.7, idleSpin: 0.5, stretch: 0.03, gap: [1.0, 1.4], onHit: 'bounce' },
    },

    G7: {       // 黑裙荆棘杀手（约尔式）：一团暗紫黑烟里蹲着现身、起身撩发，温柔地笑；手指夹着玫瑰护手的细刺刀举过头顶甩出去
      face: +1,
      sheet: { src: 'assets/trio/G7_yor.webp', cell: [410, 435], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'crouch', 'rise', 'emerge', 'idle2', 'release', 'through'] },
      /* 锚点 = 前脚高跟靴：出手四帧按这只靴子配准（残差 0.19 px）。脚底 y 1000（同组地板 G26 头顶 1021，最低点 1018 不叠），站姿高约 290 px */
      anchor: [287.7, 409.4], at: [260, 960, 0.84],   /* 精闺1：补了 release 帧（头发往后甩）后 x 220 出画 33 px、手压 G18 落脚区 → combo_scan --only=G5,G7 建议站位 */ pivot: [287, 409], leanK: 0,
      depth: 0.8, recipe: 'petal',
      /* 阴影一闪：淡入（0.35 秒）时蹲着低头，淡入完起身撩发 → 站起张手 → 待机（淡入结束后换了两次帧） */
      enter: { kind: 'appear', fx: 'smoke', color: [60, 20, 70], seq: [['crouch', 0.35], ['rise', 0.18], ['emerge', 0.14, 'land'], ['idle', 9]], sq: 0.05 },
      exit: { frame: 'crouch' },
      idle: { frame: 'idle', breathe: [0.014, 0.8, 0], alt: { frame: 'idle2', every: [1.2, 2.2], hold: [0.6, 1.0] } },   /* idle2 = 前面那只小臂收到胸前（切件，bestie/G7_yor/armidle2.py，身子逐像素同 idle）；原整张重生的 idle2 头顶高 25 px，769478b 停用后换掉 */
      /* 身后的长发梢连同垂着的后手一起慢慢晃（根在右边钉住；框上、下、左三边透明） */
      flex: { idle: [[49, 122, 106, 236, 'r', 5, 0.8]] },
      /* 细刺刀是平面图（bestie/G7_yor/knife.py：原图 180 px 刀身提亮一档、加 3 px 深紫褐描边，186 px × 0.65 ≈ 屏幕 121 px，刀尖最细处连描边 ≈ 4.5 px）：
         手指夹着举过头顶（后排：出手点在女生头顶以上）→ 甩出去刀尖朝前直飞（aim：不自转，尖头顺着飞行方向，拿在手里也指着他） */
      atk: { kind: 'throw', item: 'knife', prop: 'assets/world/trio_g7_knife.webp', scale: 0.65,
             seq: [['wind', 0.22], ['release', 0.06, 'fire'], ['throw', 0.1], ['through', 0.12], ['follow', 0.25]],   /* through（2026-10-02 重做）：throw 帧手臂绕肩往下转 40°（bestie/G7_yor/armswing.py），身子逐像素同 throw */   // 精闺1 P6：release 出手瞬间 / through 跟随（bestie/tools/addframes.py）
             hold: { wind: [124, 40], release: [395, 72], throw: [356, 110] }, dir: { release: -6.7 },   // dir = 手的运动方向（wind → release），dircheck 验过
             T: 0.4, arc: 0.12, spin: 0, aim: true, stretch: 0.03, gap: [0.9, 1.3], onHit: 'bounce' },
    },
    G8: {       // 冰雪女王（艾莎式）：踮着脚一路滑冰滑进来（燕式滑行 → 踮脚转一圈 → 急停），掌心上浮着一根冰锥；把冰锥举过头顶一掷，打中他的头冻出一层冰壳
      face: +1,
      sheet: { src: 'assets/trio/G8_elsa.webp', cell: [644, 493], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'glide', 'twirl', 'stop', 'idle2', 'release'] },
      /* 锚点 = 前脚水晶鞋底：出手四帧按这只鞋配准（残差 0.46 px）；滑冰三帧 loose（横按头、竖按脚底） */
      anchor: [411.5, 483.1], at: [200, 960, 0.81], pivot: [411, 483], leanK: 0,
      depth: 0.8, recipe: 'water',
      /* 滑冰（ride）：燕式单脚滑行 → 踮脚转一圈 → 急停站稳（露面后换两次帧）；离场转身滑出去 */
      enter: { kind: 'ride', T: 1.0, tilt: 0.08, seq: [['glide', 0.4], ['twirl', 0.3], ['stop', 0.3, 'land'], ['idle', 9]], sq: 0.06 },
      exit: { frame: 'glide', flip: true },
      idle: { frame: 'idle', breathe: [0.014, 0.8, 0] },
      /* 次级摆动：垂着的左手指尖下吊着一片雪花（part.py 出图 40 px，挂点在上沿、像坠子一样来回摆 ±0.35 rad，下沿 ≈ 15 px） */
      parts: [{ src: 'assets/trio/G8_snowflake.webp', pivot: [20, 2], z: 1, sway: [0.35, 0.7, 0], at: { idle: [290, 304, 0], idle2: [290, 304, 0] } }],
      /* 冰锥是平面图（bestie/G8_elsa/raw/icicle_src.png 抠出来，150 px 长 × 0.6，尖朝右）：待机浮在伸出去的掌心上、尖指着他（aim）；
         wind 帧右手举过头顶、冰锥在掌心上方那一刻离手（后排：出手点在女生头顶以上），尖朝前直飞；throw 帧是甩出去的手 */
      atk: { kind: 'throw', item: 'icicle', prop: 'assets/world/trio_g8_icicle.webp', scale: 0.6,
             seq: [['wind', 0.3], ['release', 0.06, 'fire'], ['throw', 0.14], ['follow', 0.35]], dir: { release: -22.5 },   // 精闺1 / 自检 4.4（所需 ≈ −23°）：release = throw 帧手臂绕肩往上转 54°（G8_elsa/armswing.py），过顶往前抡、离手那一刻手速沿圆弧切线 = 手臂 67.5° − 90°
             hold: { idle: [495, 124], wind: [420, 20], release: [482, 72] },
             T: 0.45, arc: 0.15, spin: 0, aim: true, stretch: 0.03, gap: [0.9, 1.3], onHit: 'freeze' },
    },
    G9: {       // 广场舞大妈：腰挂小音箱、扭着秧歌步抬腿甩手走进来；一只手叉腰、一只手翘着兰花指打拍子；抡起一条红绸从头顶甩过去抽他
      face: +1,
      sheet: { src: 'assets/trio/G9_auntie.webp', cell: [357, 439], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'walk1', 'walk2', 'walk3', 'walk4', 'release', 'through', 'idle2'] },
      /* 锚点 = 两只布鞋鞋底中点：出手四帧按两只鞋配准（残差 0.64 px）；走路四帧 loose，出自同一张底图（蓝幕，layers.cut_blue） */
      anchor: [177.6, 434.8], at: [150, 970, 0.88], pivot: [177, 434], leanK: 0,   /* 精闺1：release 往上抡压 G18 落脚区 121 px → combo_scan --only=G9,G10,G27 建议站位 */
      depth: 0.8, recipe: 'rouge',
      /* 秧歌步（walk）：接地 A（右手甩到身前）→ 抬膝过渡 → 接地 B（右手甩到身后）→ 抬膝过渡。
         stride 136.5：着地鞋跟每次换帧前进 68 / 69 / 68 / 68 格内 px（walkshift.py 把 walk2~4 横移 −3 / +4 / −5 后），换帧同一只脚差 ≤ 0.75 格内 px */
      /* dist 300.3 = 5 步 × 60.06（stride / 2 × s）：默认 dist（格宽 × s + 30 = 273.8）÷ 60.06 取整 5 步、每步被匀成 54.8，换帧着地脚差 −5.4 px（W_g9_ms40 实测） */
      enter: { kind: 'walk', fps: 6, bob: 8, stride: 136.5, dist: 300.3, seq: [[['walk1', 'walk2', 'walk3', 'walk4'], 9]] },
      exit: { frame: ['walk1', 'walk2', 'walk3', 'walk4'], fps: 6, flip: true },
      idle: { frame: 'idle', breathe: [0.016, 0.9, 0], alt: { frame: 'idle2', every: [2, 4], hold: [0.9, 1.4] } },   // idle2 = 闭眼打响指跟着节拍（精闺1 P7）
      /* 翘着的兰花指打拍子：小臂那一行（框底）钉住，手掌左右晃（框上、左、右三边透明） */
      flex: { idle: [[232, 94, 292, 144, 'b', 5, 1.5]] },
      /* 红绸（whip，引擎画）：wind 手抡到脑后 → throw 手举到头顶最高点、红绸从那里甩出去（出手点 [258, 14] 在她自己头顶以上，也在女生头顶以上）→ follow 叉腰大笑 */
      atk: { kind: 'whip', seq: [['wind', 0.24], ['release', 0.06], ['throw', 0.44, 'fire'], ['through', 0.12], ['follow', 0.2]], from: [298, 38], dir: { throw: 52 },   // 精闺1 P6：release 往上抡 / through 跟随；dir = 举起的手臂轴（绸带第一节沿它甩出去）
             phases: [0.14, 0.08, 0.22],
             whip: { w: 14, taper: 0.35, amp: 30, waves: 1.3, hz: 3, color: '#e0303a', edge: 'rgba(110,10,20,.9)' }, gap: [0.9, 1.3] },
    },
    G10: {      // 粉蓝双马尾坏女孩（小丑女式）：踩着红蓝轮滑压低身子冲进来、单脚一转、横刹停住；球棒扛在肩上吐舌头，举过头顶抡出去（3D 棒球棍打着转飞）
      face: +1,
      sheet: { src: 'assets/trio/G10_harley.webp', cell: [396, 431], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'cruise', 'spin', 'stop', 'idle2', 'drop', 'through'] },
      /* 锚点 = 两只轮滑鞋轮子着地中点：按前脚红轮滑鞋配准、缩放也按它（scale_by fixed：wind 仰头时按头找缩放会缩成 0.87）；残差 0.14 px */
      anchor: [228.5, 425.4], at: [160, 980, 0.86], pivot: [228, 425], leanK: 0,   /* 精闺1：地板 G27 新出手帧手臂举高后挡 G10 drop 帧 18% → combo_scan --only=G9,G10,G27 建议站位 */
      depth: 0.8, recipe: 'star',
      /* 轮滑（ride）：压低冲刺 → 单脚转一圈 → 横刹后仰（露面后换两次帧）；离场转身滑走 */
      enter: { kind: 'ride', T: 1.0, tilt: 0.1, seq: [['cruise', 0.4], ['spin', 0.3], ['stop', 0.3, 'land'], ['idle', 9]], sq: 0.07 },
      exit: { frame: 'cruise', flip: true },
      idle: { frame: 'idle', breathe: [0.014, 0.8, 0], alt: { frame: 'idle2', every: [2, 4], hold: [0.8, 1.2] } },   // idle2 = 眨眼坏笑（只重画了头，拳头和球棒不动；精闺1 P7）
      /* 粉色那根马尾（头后、往左甩）：根在右边钉住，梢晃；框上、下、左三边透明（bestie/tools/flexfind.py） */
      flex: { idle: [[156, 46, 184, 130, 'r', 6, 0.9]] },
      /* 待机扛着的球棒（审查第八批打回：r 32 时只有 57 px、读成瓶子）：3D 球棒图集第 33 格的静帧做成挂件（bestie/G10_harley/bat_part.py，同 G5 算盘），
         和飞出去的 3D 球棒同一个造型、同一个长度（屏幕 142 px ≈ 人高 0.4）；pivot = 握把离尾端 13% 那一点，挂在 idle 举到下巴前的拳头上，
         z −1 画在人后面，拳头盖住握把 = 握在拳里。棍身竖着往前倒 16°、全长露在背景上（往后斜靠肩会大半藏在头和马尾后面，或者横过脸）。
         手里的 3D 道具引擎是居中画、按随机初始角挑格子转的，摆不出这个姿势，所以 idle 不写 hold。sway：拳头里轻轻晃（棍头峰峰约 10 px，待机次级摆动）。
         ammo: true = 手里有球棒才画（扔出去还在飞、还没落完的时候不画第二根；引擎 7c027a6 drawParts / reload 认这个字段） */
      parts: [{ src: 'assets/trio/G10_bat.webp', pivot: [19.2, 141.2], z: -1, sway: [0.04, 0.8, 0], ammo: true, at: { idle: [268, 112, 0], idle2: [268, 112, 0] } }],
      /* 3D 棒球棍（引擎 3566a8a 重渲 prop_bat_v2：r 68 cell 168 scale 1.05，外框长边中位 117 px）：wind 两拳举过头顶、棍在那一刻离手（后排：出手点在女生头顶以上），
         throw 帧是甩完张开的手 */
      atk: { kind: 'throw', item: 'bat', r: 68, atlas: { src: 'assets/trio/prop_bat_v2.webp', n: 36, cols: 6, cell: 168, scale: 1.05 },
             seq: [['wind', 0.32], ['throw', 0.08, 'fire'], ['drop', 0.08], ['through', 0.12], ['follow', 0.25]],   // 精闺1 P6：throw 双手送到最前上方 = 棍离手（手位移 wind→throw −9°，在直线角上方、物理可达）→ drop 双手往下甩 → through 跟随
             hold: { wind: [128, 28], throw: [330, 60] }, dir: { throw: -9 },   // dir = 手的运动方向（wind → throw），dircheck 验过
             T: 0.55, arc: 0.25, spin: 5.7, stretch: 0.03, gap: [0.9, 1.3], onHit: 'bounce' },
    },

    /* ---- 上方（左上，男女主头顶以下；样板 G11） ---- */
    G15: {      // 船头红发少女（泰坦尼克 Rose 式）：站在一截白色船头上从左边平着滑出来，捂着心口 → 张开双臂"飞"；举起心形蓝宝石项链一抛（3D）砸他
      face: +1,
      sheet: { src: 'assets/trio/G15_rose.webp', cell: [612, 435], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'grip', 'step', 'open', 'idle2', 'release', 'through'] },
      /* 船头画在帧里，在场六帧（idle / wind / throw / follow / open / idle2）都是 idle 那一份（bestie/G15_rose/bow.py 垫进去：蕾丝、小腿在栏杆后，鞋在栏杆前；
         frames.py build 之后要重跑），逐像素和 idle 一样（shots/trio_bestie/bow_G15.txt）。
         船尾往左接长 200（bow.py 顺着甲板斜度把栏杆、船体一列列接出去，立柱按间距复制，格加宽到 562、格内坐标 + 200）：船尾左端到屏幕 x −119，读成船从画外伸进来。锚点 = 两只高跟鞋之间的船头甲板；按两只鞋配准（残差 0.22 px）。
         grip / step 两帧模型多画了一根竖栏杆（船头变形），不上场。大小：人（不算船头）剪影 × 0.75² ≈ 2.34 万（上方样板 G11 2.06 万，+14%，蓬裙占得多）。
         站位：不在 shots/trio_std/建议站位_最终.md 的改动表里，保持原位（combo_scan 复扫见 shots/trio_bestie/combo_scan_站位改后.txt） */
      anchor: [412.4, 367.4], at: [190, 545, 0.75], pivot: [412, 367], leanK: 0,
      depth: 0.5, recipe: 'water',
      /* 船头从左边画外平着滑进来（fly，from 在同一高度偏左、dy 小），减速到位；滑行时捂着心口 → 双臂半张 → 到位张开双臂（露面后换两次帧，最后标 land） */
      enter: { kind: 'fly', from: [-420, -30], air: 0.75, tilt: 0.04, seq: [['follow', 0.35], ['open', 0.3], ['idle', 9, 'land']], sq: 0.05 },
      exit: { frame: 'follow' },
      idle: { frame: 'idle', breathe: [0.014, 0.6, 0], alt: { frame: 'idle2', every: [0.5, 1.2], hold: [0.6, 1.0] } },
      /* 往后飘的长卷发：根在右边钉住，框上、下、左三边透明 */
      flex: { idle: [[242, 45, 340, 152, 'r', 6, 0.8]] },   // 框里连着张开的左手：飘发和手一起随风轻晃
      /* 心形蓝宝石项链照道具表 3D：r 26 cell 79 scale 1.39，转速 π / T */
      atk: { kind: 'throw', item: 'necklace', r: 26, atlas: { src: 'assets/trio/prop_necklace.webp', n: 36, cols: 6, cell: 79, scale: 1.39 },
             seq: [['wind', 0.26], ['release', 0.06, 'fire'], ['throw', 0.1], ['through', 0.12], ['follow', 0.25]],   // 精闺1 P6：release 手臂平伸到最远、手指张开离手；throw 接着当跟随，through 手臂顺势落到右下 45°
             hold: { wind: [450, 14], release: [580, 80], throw: [552, 52] }, dir: { release: -26.9 },   // wind → release 手位移 −26.9°（引擎原量 throw −20.4°，差 6.5°）
             T: 0.55, arc: 0.2, spin: 5.7, idleSpin: 1.2, stretch: 0.03, gap: [1.0, 1.4], onHit: 'bounce' },
    },

    G18: {      // 挂帅女将（穆桂英式京剧武旦）：从左上一跃落下、单膝点地，起身亮相，翎子一甩；红缨枪举过头顶掷出去（3D）
      face: +1,
      sheet: { src: 'assets/trio/G18_mu.webp', cell: [365, 351], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'leap', 'land', 'rise', 'idle2', 'release', 'through'] },
      /* 锚点 = 前脚厚底靴鞋底：出手四帧按这只靴子配准（残差 0.17 px）。人那一层 idle 剪影 2.80 万 × 0.88² ≈ 2.17 万（上方样板 G11 2.06 万） */
      anchor: [273.7, 323.2], at: [496, 640, 0.88], pivot: [273, 323], leanK: 0,
      depth: 0.5, recipe: 'petal',
      /* 从左上画外抛物线跃下（腾空收腿张臂）→ 单膝落在墙沿上（压扁）→ 起身张臂 → 亮相待机 */
      enter: { kind: 'leap', from: [-320, -380], h: 120, air: 0.5, T: 0.9, seq: [['leap', 0.5], ['land', 0.2, 'land'], ['rise', 0.14], ['idle', 9]], sq: 0.1 },
      exit: { frame: 'leap' },
      idle: { frame: 'idle', breathe: [0.014, 0.7, 0], alt: { frame: 'idle2', every: [0.5, 1.2], hold: [0.6, 1.0] } },
      /* 墙沿场景层（bestie/G18_mu/ledge.py 程序画一截城墙顶：青砖墙顶面 + 错缝墙面、下半截渐隐），fixed 钉在世界里、左端出画。
         墙顶面是一条带（3/4 侧身，远脚 y 323、近脚 y 346）：前沿 = 格内 y 346 = land 单膝 / 脚尖、idle / rise 后脚的最低一行，后沿 314。
         左端格内 x −340：at x 260 → 380 后墙往左接长 136；修12 落脚区（G8 蓄力瞄男主的冰锥扫过左靴）人挪到 at x 496、墙再接长 134，左端仍在屏幕 x −44 出画 */
      parts: [{ src: 'assets/trio/G18_ledge.webp', pivot: [0, 0], z: -1, fixed: true, at: [-340, 314, 0] },
              /* 翎子、靠旗是定妆拆好的两层（ref/G18_feathers.png、G18_flags.png，part.py 按人那一层同一个比例 330/1424 缩）：都在人身后。
                 pivot：翎子 = 两根翎管插进盔头的那一点、靠旗 = 四根旗杆在背上并拢的插座。每帧的 at = idle 上的位置 + 这一帧的头相对 idle 的位移（头模板匹配） */
              { src: 'assets/trio/G18_flags.webp', pivot: [73.9, 118.5], z: -1, sway: [0.04, 0.7, 0],
                 at: { idle: [133.4, 65.4, 0], idle2: [136.4, 60.4, 0], wind: [144.4, 66.4, 0], throw: [155.4, 66.4, 0], release: [155.4, 66.4, 0], through: [155.4, 66.4, 0], follow: [128.4, 59.4, 0], leap: [133.4, 159.4, 0], land: [131.4, 130.4, 0], rise: [133.4, 72.4, 0] } },
              { src: 'assets/trio/G18_feathers.webp', pivot: [89.9, 169.0], z: -1, sway: [0.12, 0.9, 0],
                 at: { idle: [147.3, 20.2, 0], idle2: [150.3, 15.2, 0], wind: [158.3, 21.2, 0], throw: [169.3, 21.2, 0], release: [169.3, 21.2, 0], through: [169.3, 21.2, 0], follow: [142.3, 14.2, 0], leap: [147.3, 114.2, 0], land: [145.3, 85.2, 0], rise: [147.3, 27.2, 0] } }],
      /* 红缨枪照道具表 3D：r 95 cell 200 scale 1.02（审查第五批返工，引擎负责人：屏幕长 152~195 px，枪头始终朝右），转速 π / T；命中炸红（bloom） */
      atk: { kind: 'throw', item: 'spear', r: 95, atlas: { src: 'assets/trio/prop_spear.webp', n: 36, cols: 6, cell: 200, scale: 1.02 },
             seq: [['wind', 0.26], ['release', 0.06, 'fire'], ['throw', 0.1], ['through', 0.12], ['follow', 0.25]],   // 精闺1 P6：release 手臂平推到最远离手、through 手臂顺势落到右下 45°（release / through 只重画右臂，头身同 throw，翎子靠旗同 throw）
             hold: { wind: [132, 16], release: [338, 90], throw: [318, 72] }, dir: { release: -19.8 },   // wind → release 手位移 −19.8°（引擎原量 −16.8°）；idle2 翎子靠旗 = idle + 头位移 (+3, −5)（头模板匹配）
             T: 0.55, arc: 0.18, spin: 5.7, idleSpin: 0.6, stretch: 0.03, gap: [1.0, 1.4], onHit: 'bounce' },
    },
    G13: {      // 白衣古墓仙子（小龙女式）：躺在一根横拉的麻绳上从左边滑进来、随绳颠着荡；支起身子一甩白绸，绸梢金铃"叮当"抽过去
      face: +1,
      sheet: { src: 'assets/trio/G13_xiaolongnv.webp', cell: [421, 303], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'swing', 'through', 'idle2'] },
      /* 锚点 = 腰臀压在绳上那一点；按伸直的那条腿 + 脚配准（残差 ≤ 2.0 px）。绳子引擎画（rope，画在人之下），帧里不画绳。
         剪影（含垂下的长发、绸带）约 4.8 万格内像素 × 0.66² ≈ 2.1 万屏幕像素，同 G11 */
      anchor: [206.5, 166.1], at: [175, 500, 0.66], pivot: [206, 166], leanK: 0.3,
      depth: 0.5, recipe: 'star',
      /* 横绳（rope）：躺在绳上撩着头发滑进来 → 躺定一手枕头一手搭膝（露面后换一次帧，两个姿态）；绳是黄褐麻绳。
         ends 是屏幕点，跟着 at 走：at y 520 → 500 两头一起抬 20。右端拴在墙钉上（审查第九批打回：原 x 470 停在墙画右画框里、什么都没拴）：
         x 515 = 画框右沿 ≈ 487 和挂钟左沿 ≈ 543 之间的空墙；压绳点比两头连线低 6.9 px（往下坠） */
      enter: { kind: 'rope', ends: [[-80, 512], [515, 468]], touch: [206.5, 166.1], sag: 16, sway: 5, w: 6, fill: '#b98a4e', edge: '#5a3a1a',
               seq: [['follow', 0.45], ['idle', 9, 'land']], sq: 0.04 },
      exit: { frame: 'follow' },
      idle: { frame: 'idle', breathe: [0.012, 0.7, 0], alt: { frame: 'idle2', every: [0.5, 1.2], hold: [0.6, 1.0] } },   // 精闺1 idle2：搭在膝上的手顺着膝盖往前一伸、手腕耷拉
      /* 墙钉 + 绳结场景层（bestie/G13_xiaolongnv/peg.py 程序画：铁底板钉在墙上、下挂铁环，绳头穿环打结、垂一截绳尾）。
         fixed 钉在世界里，z −1 画在绳之后（引擎先画绳）、人之前；pivot = 绳结中心，at = 绳右端 [515, 468] 换成格内坐标。改 at / ends 要重跑 peg.py */
      parts: [{ src: 'assets/trio/G13_peg.webp', pivot: [18.2, 34.8], z: -1, fixed: true, at: [721.7, 117.6, 0] }],
      /* 垂下去的长发、身下垂着的裙摆绸带：上沿（压在身下那一行）钉住，梢晃（框左、右、下三边透明） */
      flex: { idle: [[0, 216, 165, 300, 't', 5, 0.8], [200, 210, 404, 300, 't', 5, 0.7]] },
      /* 金铃索（whip）：支起身子手举过头 → 往右一甩，白绸末端一对金铃抽过去。
         精闺1 P6：wind → swing（手臂扫到前上 40°，挥动中）→ throw（甩直，dir 18 沿手臂轴）→ through（手放平、手腕耷拉）→ follow */
      atk: { kind: 'whip', seq: [['wind', 0.24], ['swing', 0.06], ['throw', 0.44, 'fire'], ['through', 0.12], ['follow', 0.2]], from: [290, 45], phases: [0.14, 0.08, 0.22],
             whip: { w: 10, taper: 0.5, amp: 26, waves: 1.3, hz: 3, color: '#f6f4f8', edge: 'rgba(120,120,150,.9)', tip: [18, 13, '#e8b52c'] }, gap: [0.9, 1.3] },
    },
    G14: {      // 金发剑之公主（希瑞式）：左上一道蓝白闪光里举剑变身现身，剑指前方、扛剑站定；双手举剑过头一劈，金色剑光斩在他身上
      face: +1,
      sheet: { src: 'assets/trio/G14_shera.webp', cell: [395, 433], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'swing', 'through', 'idle2'] },
      /* 锚点 = 前脚金靴底：按这只靴子配准、缩放也按它（scale_by fixed：按头找时 idle 比其余三帧小一圈），残差 0.18 px。
         剑是她自己的（不飞出去），画在帧里；剪影约 3.5 万格内像素 × 0.77² ≈ 2.07 万屏幕像素，同 G11 */
      anchor: [222.4, 425.4], at: [170, 520, 0.7], pivot: [222, 425], leanK: 0.3,
      depth: 0.5, recipe: 'star',
      /* 闪电变身（appear 闪光，蓝白）：淡入时双手举剑指天（变身），淡入完剑指前方 → 扛剑站定（淡入后换两次帧） */
      enter: { kind: 'appear', fx: 'flash', color: [200, 230, 255], fade: 0.3, seq: [['wind', 0.35], ['follow', 0.3, 'land'], ['idle', 9]], sq: 0.05 },
      exit: { frame: 'wind' },
      idle: { frame: 'idle', breathe: [0.014, 0.8, 0], alt: { frame: 'idle2', every: [0.5, 1.2], hold: [0.6, 1.0] } },   // 精闺1 idle2：叉腰的左手抬起把金发拨到肩后
      /* 脚下的水晶城堡石台（审查第九批打回：两只金靴底悬在鱼缸玻璃中段）：bestie/G14_shera/ledge.py 程序画，fixed 钉在世界里、z −1、左端出画（屏幕 x −47）。
         不站鱼缸盖：鱼缸是长卷背景，镜头随拖拽卷动、三间房只有客厅有，人按屏幕 at 钉住，一拖鱼缸就滑走；场景层跟人走。
         顶面一条带：前沿 = 格内 y 429 = 后脚（左）靴底最低一行，前脚（右）靴底 425 落在带里，后沿 407 */
      parts: [{ src: 'assets/trio/G14_ledge.webp', pivot: [0, 0], z: -1, fixed: true, at: [-60, 407, 0] }],
      /* 身后飘着的长金发 + 红披风：身子那一侧（右边）钉住，往左飘（框上、下、左三边透明） */
      flex: { idle: [[0, 143, 106, 336, 'r', 12, 0.9]] },
      /* 剑光（slash，引擎画在他身上）：举剑过头 → 劈下，出手段 0.3 秒盖住两道（gap 0.12 + 划出） */
      atk: { kind: 'slash', seq: [['wind', 0.26], ['swing', 0.06], ['throw', 0.3, 'fire'], ['through', 0.12], ['follow', 0.25]],   // 精闺1 P6 / 审查 q9：举过头 → swing 剑在前上方约 55°（挥动中）→ 劈到右下 → through 剑尖顺势指地 → 收
             slash: { n: 2, gap: 0.12, len: 240, w: 20, life: 0.5, color: [255, 215, 110], ang: 0.79, spread: 0.2 },   // 精闺1 / 自检 4.6 第 5 条：弦线顺劈向往右下约 45°（原 −0.6 弦线往右上，和往右下劈的剑划向相反）
             hold: { throw: [297, 352] },   // 剑尖（throw 格量；剑气从这里飞出，精引3）
             gap: [0.9, 1.3] },
    },
    G16: {      // 狐尾妖姬（妲己式）：一团狐火橙烟里九条白尾巴裹着她现身，伸个懒腰、托腮一笑；掌心托一团青蓝狐火，举过头顶甩出去
      face: +1,
      sheet: { src: 'assets/trio/G16_daji.webp', cell: [328, 401], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'wrap', 'stretch', 'lean', 'idle2', 'through', 'release'] },
      /* 九尾宝座画在每一帧里：按交叠的大腿 + 臀配准（残差 0.27 px），scale_by sheet（wind 仰头按头找会放大到 1.15、stretch 缩到 0.85）。
         锚点 = 最低点（鞋 / 裙摆）。人（不算白尾巴）约 3.2 万格内像素 × 0.8² ≈ 2.05 万屏幕像素，同 G11 */
      anchor: [159.6, 383.7], at: [275, 550, 0.8], pivot: [159, 383], leanK: 0.3,
      depth: 0.5, recipe: 'foxfire',
      /* 九尾托着出现（appear 烟，狐火橙）：淡入时尾巴裹着身子只露眼睛 → 淡入完伸懒腰 → 托腮坐定 → 待机（淡入后换两次帧） */
      enter: { kind: 'appear', fx: 'smoke', color: [255, 140, 50], seq: [['wrap', 0.35], ['stretch', 0.25], ['lean', 0.2, 'land'], ['idle', 9]], sq: 0.04 },
      exit: { frame: 'wrap' },
      idle: { frame: 'idle', breathe: [0.014, 0.7, 0], alt: { frame: 'idle2', every: [0.5, 1.2], hold: [0.6, 1.0] } },
      /* 狐火是平面图（bestie/G16_daji/raw/foxfire_src.png 抠出来，100 px × 0.45）：待机浮在托起的掌心上打旋（次级摆动）；
         wind 举过头顶 → throw 甩出去、一路打着旋（道具表：狐火是光效，不做 3D） */
      atk: { kind: 'throw', item: 'foxfire', prop: 'assets/world/trio_g16_foxfire.webp', scale: 0.45,
             seq: [['wind', 0.26], ['release', 0.06, 'fire'], ['throw', 0.1], ['through', 0.14], ['follow', 0.2]],   // 精闺1 P6：release 手臂前上 25° 掌心推出离手   // 精闺1 / 自检 4.5：follow 和 throw 几乎同一张（剪影差 0.09）→ 补 through：甩完的手顺势落到膝上
             hold: { idle: [272, 92], idle2: [263, 89], wind: [207, 0], release: [292, 98], throw: [272, 86] }, dir: { release: -49 },   // wind → release 手位移 −49°（引擎原量 −53°）；idle2 掌心位置抄 trio_tune（格子只加了右边，坐标不变）
             T: 0.5, arc: 0.2, spin: 10, idleSpin: 6, stretch: 0.03, gap: [0.9, 1.3], onHit: 'bounce' },
    },
    G20: {      // 复古歌后（邓丽君式）：坐在一弯金月亮上从正上方缓缓降下来，挥手 → 张开双臂唱 → 坐定捂心口轻唱；指尖捏一枚月牙镖举过头顶一弹，打着转飞过去
      face: +1,
      sheet: { src: 'assets/trio/G20_teresa.webp', cell: [264, 338], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'wave', 'sing', 'bow', 'idle2', 'release', 'through'] },
      /* 月亮拆成挂件层（审查第八批打回：生图每帧重画的月亮不一样，月牙尖一换帧跳 6 px）：bestie/G20_teresa/moon.py 从每一帧里把月亮拿掉，
         挂件 = idle 那一份月亮（被人挡住的地方按月牙极坐标补），八帧同一张图、同一个位置，z −1 垫在人后面，照 G19 无人机。
         人按臀部 + 大腿（坐在月亮上的那一块）平移到和 idle 对齐（各帧原来差 0.4~7.6 格内 px），坐在同一张月亮上的接触线各帧一致。
         frames.py 按月亮背弧配准、缩放也按月亮（scale_by fixed），锚点 = 月亮弯里的中心。
         人（不算月亮）约 2.5 万格内像素 × 0.9² ≈ 2.06 万屏幕像素，同 G11 */
      anchor: [105.5, 181.5], at: [110, 480, 0.9], pivot: [105, 181], leanK: 0.3,
      depth: 0.5, recipe: 'crescent',
      /* 月亮降下（fly，从正上方）：一手扶月尖一手挥 → 张开双臂仰头唱 → 坐定（露面后换两次帧） */
      enter: { kind: 'fly', from: [0, -720], air: 0.9, tilt: 0.03, seq: [['wave', 0.45], ['sing', 0.35], ['idle', 9, 'land']], sq: 0.04 },
      exit: { frame: 'wave' },
      idle: { frame: 'idle', breathe: [0.014, 0.7, 0], alt: { frame: 'idle2', every: [0.5, 1.2], hold: [0.6, 1.0] } },
      /* 月亮：不甩（它是人坐着的东西，跟人一起降下来、一起呼吸）；pivot = 锚点在挂件图上的位置，八帧 at 都是锚点 */
      parts: [{ src: 'assets/trio/G20_moon.webp', pivot: [104.5, 177.5], z: -1,
                 at: { idle: [105.5, 181.5, 0], wind: [105.5, 181.5, 0], throw: [105.5, 181.5, 0], follow: [105.5, 181.5, 0], wave: [105.5, 181.5, 0], sing: [105.5, 181.5, 0], bow: [105.5, 181.5, 0], idle2: [105.5, 181.5, 0], release: [105.5, 181.5, 0], through: [105.5, 181.5, 0] } }],
      /* 月牙镖是平面图（bestie/G20_teresa/raw/crescent_src.png 抠出来，110 px 宽 × 0.5）：待机托在伸出去的掌心上慢慢转（次级摆动）；
         wind 捏着举过头顶 → throw 手腕一弹、从手里飞出去，平面内打着转飞（2D 转就是它本来的样子，道具表 7.1） */
      atk: { kind: 'throw', item: 'crescent', prop: 'assets/world/trio_g20_crescent.webp', scale: 0.5,
             seq: [['wind', 0.26], ['release', 0.06, 'fire'], ['throw', 0.1], ['through', 0.12], ['follow', 0.25]],   // 精闺1 P6：过顶甩，release 手臂从头顶甩到前上 35° 指尖一弹离手；through 手臂顺势落到右下 30°
             hold: { idle: [222, 80], idle2: [228, 72], wind: [167.2, 1.9], release: [215, 40], throw: [223.7, 52.2] }, dir: { release: -38.6 },   // wind → release 手位移 −38.6°（引擎原量 −41.7°）；idle2 抄 trio_tune   // wind / throw 跟着 moon.py 的平移（−2.84, −2.12 / −0.34, +0.21）
             T: 0.5, arc: 0.2, spin: 12, idleSpin: 3, stretch: 0.03, gap: [0.9, 1.3], onHit: 'bounce' },
    },

    G19: {      // 网红主播：戴猫耳耳机、举着手机直播，坐着白色四旋翼无人机从左边飞进来（前倾冲 → 后仰急刹 → 挥手打招呼）；甩出一枚打赏小火箭（3D）砸他
      face: +1,
      sheet: { src: 'assets/trio/G19_streamer.webp', cell: [345, 315], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'zoom', 'brake', 'wave', 'idle2', 'release', 'through'] },
      /* 人和无人机分开生（bestie/G19_streamer/raw/act_a1g / act_b1g 是"坐在看不见的座上"的人，drone.png 单独一张）：无人机做成挂件层垫在身后，
         每一帧同一张图、同一个位置（第七轮 G15 船头的要求）。人按屁股 + 大腿配准（残差 ≤ 0.40 px）；锚点 = 屁股坐在机身顶面的那一点。
         大小：人 idle 剪影 2.53 万格内像素 × 0.9² ≈ 2.05 万（上方样板 G11 2.06 万）；wind 头 0.92 是举过头顶的手压进了头框，同一张条缩放 1.00 */
      anchor: [108.3, 187.8], at: [160, 460, 0.9], pivot: [108, 188], leanK: 0.2,
      depth: 0.5, recipe: 'star',
      /* 从左边画外平着飞进来减速（fly，from 同一高度偏左）：前倾冲、头发往后拖 → 后仰急刹、两脚往前踢 → 到位挥手（露面后换两次帧，最后标 land） */
      enter: { kind: 'fly', from: [-460, -60], T: 1.0, air: 1.0, tilt: 0.08, seq: [['zoom', 0.45], ['brake', 0.25], ['wave', 9, 'land']], sq: 0.05 },
      exit: { frame: 'zoom' },
      idle: { frame: 'idle', breathe: [0.014, 0.8, 0], alt: { frame: 'idle2', every: [0.5, 1.2], hold: [0.6, 1.0] } },
      flex: { idle: [[38, 60, 72, 162, 'r', 5, 0.8]] },   // 身后垂着的长发：根在右边钉住，框上、下、左三边透明（flexcheck 0 / 0 / 0）
      /* 无人机：pivot = 机身顶面（她坐的地方），整机绕它轻轻晃（悬停），画在人后面 */
      parts: [{ src: 'assets/trio/G19_drone.webp', pivot: [150, 38], z: -1, sway: [0.03, 1.1, 0],
                 at: { idle: [140, 192, 0], wind: [140, 192, 0], throw: [140, 192, 0], follow: [140, 192, 0], zoom: [140, 192, 0], brake: [140, 192, 0], wave: [140, 192, 0], idle2: [140, 192, 0], release: [140, 192, 0], through: [140, 192, 0] } }],
      /* 打赏小火箭照道具表 3D：r 28 cell 106 scale 1.35。另一只手一直举着手机直播，扔火箭的是前侧那只手：举过头顶 → 往右甩出去 */
      atk: { kind: 'throw', item: 'rocket', r: 28, atlas: { src: 'assets/trio/prop_rocket.webp', n: 36, cols: 6, cell: 106, scale: 1.35 },
             seq: [['wind', 0.26], ['release', 0.06, 'fire'], ['throw', 0.1], ['through', 0.12], ['follow', 0.25]],   // 精闺1 P6：release 手臂平伸到最远、手指张开离手；through 手臂顺势落到右下 40°
             hold: { wind: [72, 14], release: [285, 113], throw: [292, 96] }, dir: { release: -24.9 },   // wind → release 手位移 −24.9°（引擎原量 −20.4°）
             T: 0.55, arc: 0.2, spin: 5.7, stretch: 0.03, gap: [0.9, 1.3], onHit: 'bounce' },
    },

    G17: {      // 恋柱（甘露寺式）：脚踝拴着绳从左上倒挂着掉下来、弹两下，捧着脸颊笑；握着剑柄一甩，粉色软鞭剑螺旋着抽过去，打中迸樱花瓣
      face: +1,
      sheet: { src: 'assets/trio/G17_mitsuri.webp', cell: [245, 349], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'plunge', 'bounce', 'settle', 'idle2', 'swing', 'through'] },
      /* 上方；倒挂，锚点 = 两只脚踝（绳子拴的那一点）。两条腿每帧都并拢伸直，缩放和配准都按腿（scale_by fixed，残差 ≤ 0.51 px）。
         蓝幕（身上粉 + 嫩绿，品红 / 绿幕都会吃掉头发），bestie/G17_mitsuri/bluekey.py 先抠成透明再进 frames.py。
         大小：idle 剪影 1.84 万 × 1.06² ≈ 2.07 万（上方样板 G11 2.06 万）。站位临时：脚踝 y 240 在 HUD（拉力行 ≤ 180）下面，辫梢最低 594 */
      anchor: [119.7, 15.3], at: [150, 240, 1.06], pivot: [120, -645], leanK: 0,
      depth: 0.5, recipe: 'petal',
      /* 倒挂垂下：伸直俯冲、辫子往上飞 → 冲过头弹回、张开双臂 → 捧脸稳住；绳子引擎画，拴在脚踝 line */
      enter: { kind: 'drop', len: 700, line: [120, 15], T: 0.8, w: 3, fill: '#8a6a44', edge: 'rgba(60,40,20,.9)',
               seq: [['plunge', 0.35], ['bounce', 0.25], ['settle', 0.2, 'land'], ['idle', 9]], sq: 0.06 },
      exit: { frame: 'plunge' },
      idle: { frame: 'idle', breathe: [0.014, 0.9, 0.3], alt: { frame: 'idle2', every: [0.5, 1.2], hold: [0.6, 1.0] } },
      flex: { idle: [[90, 280, 146, 338, 't', 5, 0.8]] },   // 垂着的两根麻花辫：顶边钉住，辫梢晃（flexcheck 下、左、右三边 0）
      /* 精闺1 P6：wind（抡到左后）→ swing（手臂垂直往下扫过）→ throw（甩到右下，dir −45）→ through（手臂顺势甩到右下 20°）→ follow。
         鞭剑（whip，引擎画）：手里只画剑柄（粉绿圆镡 + 白柄），wind 抡到身后 → throw 甩到右下、软剑从镡上螺旋抽出去（waves 2），末端一截剑尖 */
      atk: { kind: 'whip', seq: [['wind', 0.24], ['swing', 0.06], ['throw', 0.44, 'fire'], ['through', 0.12], ['follow', 0.2]], from: [236, 278], phases: [0.14, 0.08, 0.22],
             whip: { w: 7, taper: 0.55, amp: 26, waves: 2, hz: 4, color: '#f7a3c6', edge: 'rgba(120,30,70,.9)', tip: [30, 6, '#ffd6e6'] }, gap: [0.9, 1.3] },
    },

    /* ---- 单张立绘（旧，等按规范重做成帧序列） ---- */
    G12: {      // 紫衣仙子：秋千从左上画外荡进来，飞吻，爱心打到他脸上留下口红印（查岗证据）
      /* 2026-10-01 迁成帧序列（引擎负责人）：idle = 原单张立绘（手心朝上托着），kiss = 同一张画布上只局部重绘右臂（指尖送到唇边，
         v14/trio/bestie/G12_fairy/inp/，inpaint_paste.py：框外是原图像素，纱一点没动）。绳子、座板画在帧里（ropes.x：引擎只接帧顶往上那一截）。
         出手：荡到最前面之前 kiss（手送到唇边）→ 换回托掌那一帧、两颗爱心从掌心飞出去（飞吻） */
      face: +1,
      sheet: { src: 'assets/trio/G12_fairy.webp', cell: [280, 420], cols: 2, names: ['idle', 'kiss', 'through', 'blow', 'idle2'] },
      at: [165, 210, 1],   /* 2026-10-01 自由组合：原 y 360 秋千荡下来压后排地面的头，抬 130；7c027a6 蓄力道具计入遮挡后再抬 20（组合遮挡矩阵_bestie 建议站位） */
      anchor: [145, 0], pivot: [145, -480], leanK: 1,
      depth: 0.5, enter: 'swing', recipe: 'rouge', ropes: { ...ROPE, x: [100, 190], fill: '#a7864f' },
      swing: { a0: 1.3, a: 0.12, tau: 0.5, w: 2.4 },
      idle: { frame: 'idle', breathe: [0.012, 0.8, 0.4], alt: { frame: 'idle2', every: [0.5, 1.2], hold: [0.6, 1.0] } },
      atk: { kind: 'throw', item: 'heart', n: 2, color: [255, 70, 130], T: 0.55, arc: 0.1, spin: 0, onHit: 'lips',
             seq: [['kiss', 0.42], ['idle', 0.3, 'fire'], ['through', 0.14]], hold: { idle: [238, 115] } },   // 精闺1 P6：飞吻出手后手落到膝上（through，出手方向交接表 G12 引擎条目）
    },
  },

  /* 10 组（地面 + 上方 + 地板），docs/三人组30人名单.md。cast / ground 里还没有的编号 = 还没做，那个槽位空着；整组都没有就跳过 */
  groups: [
    { name: '格斗', ground: 'G4', top: 'G17', floor: 'G21' },
    { name: '客栈', ground: 'G5', top: 'G15', floor: 'G23' },
    { name: '妈妈辈', ground: 'G6', top: 'G20', floor: 'G30' },
    { name: '暗杀', ground: 'G7', top: 'G16', floor: 'G26' },
    { name: '女王', ground: 'G8', top: 'G18', floor: 'G25' },
    { name: '广场', ground: 'G9', top: 'G19', floor: 'G28' },
    { name: '古装', ground: 'G1', top: 'G11', floor: 'G24' },
    { name: '仙侠', ground: 'G2', top: 'G13', floor: 'G29' },
    { name: '女英雄', ground: 'G10', top: 'G14', floor: 'G22' },
    { name: '少女', ground: 'G3', top: 'G12', floor: 'G27' },
  ],
};
