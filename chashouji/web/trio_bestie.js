/* trio_bestie.js —— 闺蜜侧（左，查岗党，打男生）三人组的角色数据 + 10 组搭配。**美术维护**，引擎在 trio.js。
 * 怎么出一个人、每个字段什么意思：docs/三人组角色规范.md。名单与分组：docs/三人组30人名单.md。
 * 坐标约定同 trio_buddy.js 开头。
 */
'use strict';

const TRIO_BESTIE = {
  /* 后排地面的人 = crew.js Bestie 的第几个形象（MIST.skins 的下标）：G1 墨镜短发 src3 / G2 蓝发发明家 src7 / G3 月光水手 src8 */
  ground: { G1: 0, G2: 1, G3: 2 },

  cast: {
    /* ---- 帧序列（新标准） ---- */
    G11: {      // 花饰格格：秋千从左上画外荡进来（往前荡伸腿、往后荡收腿），荡到最前面抛绣球砸他的头
      face: +1,
      sheet: { src: 'assets/trio/G11_gege.webp', cell: [315, 343], cols: 4, names: ['idle', 'raise', 'throw', 'follow', 'wind', 'tuck', 'kick', 'idle2'] },
      anchor: [128, 212.3], at: [170, 640, 1], pivot: [128, -530], leanK: 0.5,
      depth: 0.5, recipe: 'bloom',
      /* 进场：0.4 秒从左上画外露面时收着腿俯冲（tuck），0.6 秒荡到最低点（摆角过零）伸腿（kick）往前荡，0.75 秒接出手 */
      enter: { kind: 'swing', seq: [['tuck', 0.6], ['kick', 9]] },
      /* 绳子、座板由引擎画（帧里的座板已抠掉）：ends 座板两头、grip 这一帧哪只手握着绳 [左手, 右手]、board 座板的框 */
      ropes: { ...ROPE, ends: [[50, 207], [208, 207]], board: [44, 205, 214, 222], flowers: '#f59ab8',
               grip: { idle: [[49, 63]], raise: [[44, 63]], throw: [[69, 76]], follow: [[57, 60]], wind: [[25, 72]],
                       tuck: [[98, 60], [227, 63]], kick: [[47, 66], [176, 60]] } },
      swing: { a0: 1.3, a: 0.13, tau: 0.45, w: 2.6, pump: { fwd: 'kick', back: 'tuck', min: 0.3 } },
      exit: { frame: 'tuck' },
      idle: { frame: 'idle', breathe: [0.014, 0.45] },
      /* 帽子后面那根流苏：下端贴着肩膀，画不出三边透明的 flex 框，拆成挂件层（frames.json 的 lift，帧里原位置已补画）。
         顶上的结挂住，自己慢慢晃（0.08 rad，尖上 ±4 px），秋千摆的时候往后拖（跟摆 0.25 × 摆的角速度） */
      parts: [{ src: 'assets/trio/G11_tassel.webp', pivot: [7, 0], z: 1, sway: [0.08, 0.8, 0.25],
                at: { idle: [80, 30, 0], raise: [84.5, 24, 0], throw: [107, 43, 0], follow: [81, 30, 0], wind: [54.5, 39, 0], tuck: [135, 34, 0], kick: [58.5, 39, 0], idle2: [79, 34, 0] } }],
      atk: { kind: 'throw', item: 'ball', prop: 'assets/world/trio_prop_ball.webp', scale: 0.5,
             seq: [['raise', 0.12], ['wind', 0.24], ['throw', 0.1, 'fire'], ['follow', 0.3]],
             hold: { idle: [176, 172], raise: [63, 26], wind: [14, 146], throw: [277, 38] },
             T: 0.5, arc: 0.25, spin: 5, idleSpin: 0.8, stretch: 0.04, onHit: 'bounce' },
    },

    G23: {      // 客栈女侠（郭芙蓉式）：马步从左下角滑进来、跺地站定，排山倒海 —— 双掌齐推，一道气浪轰他的脸
      face: +1,
      sheet: { src: 'assets/trio/G23_furong.webp', cell: [394, 307], cols: 4, names: ['idle', 'raise', 'throw', 'follow', 'slide', 'land', 'wind', 'idle2'] },
      anchor: [213.1, 305.4], at: [175, 1330, 1], pivot: [213, 305],
      leanK: 0,   // 马步两只靴子离锚点各 150px：整体前后倾会把靴子一上一下翘起来，蓄力 / 出手全靠帧
      depth: 1.3, recipe: 'thud',
      /* slide 帧（弓步滑）人一露面就在画 → land（跺进马步，压扁）→ idle。wind / idle2 是第二张条里的，马步画宽了一截，不上场 */
      enter: { kind: 'slide', seq: [['slide', 0.5], ['land', 0.14, 'land'], ['idle', 9]], sq: 0.12 },
      exit: { frame: 'slide' },
      idle: { frame: 'idle', breathe: [0.018, 0.75, 0] },   // 站马步：只竖向起伏（绕两靴之间的地面），横向不补 —— 不然两只靴子左右挪
      /* 发带下面那截飘带：上沿钉住，下端左右甩（框只有上沿压着飘带，其余三边透明） */
      flex: { idle: [[100, 62, 150, 86, 't', 8, 1.2]] },
      atk: { kind: 'beam', seq: [['raise', 0.34], ['throw', 0.4, 'fire'], ['follow', 0.3]],
             hold: { raise: [145, 125], throw: [350, 80] }, stretch: 0.03, gap: [1.0, 1.4],   // raise：两只手掌收在腰侧之间那一点（蓄力球画在这）
             /* 气浪：比悟空的光线粗一倍（排山倒海是一堵墙推过去，不是一根线）；最外一层暗红给它在暖色客厅上描个边 */
             beam: { fire: 0.38, drip: 0.1, ball: 40, glow: [255, 170, 70], edge: [220, 60, 30],
                     layers: [[84, [170, 30, 20], 0.3], [64, [255, 90, 40], 0.6], [42, [255, 160, 70], 0.85], [20, [255, 230, 160], 1], [7, [255, 255, 255], 1]] } },
    },

    G21: {      // 忍者扇娘（不知火舞式）：左下角翻滚进来（团身滚 → 落地蹲 → 半跪），胸罩当手里剑甩出去，打中挂在他头上
      face: +1,
      sheet: { src: 'assets/trio/G21_mai.webp', cell: [297, 284], cols: 4, names: ['idle', 'wind0', 'throw', 'follow', 'roll', 'land', 'wind', 'idle2'] },
      anchor: [142.6, 278.4], at: [150, 1330, 1], pivot: [142, 278],
      leanK: 0,   // 半跪：绕地面转会把着地的膝盖和前脚翘起来
      depth: 1.3, recipe: 'rouge',
      enter: { kind: 'roll', seq: [['roll', 0.5], ['land', 0.14, 'land'], ['idle', 9]], sq: 0.1 },
      exit: { frame: 'roll' },
      idle: { frame: 'idle', breathe: [0.016, 0.7, 0] },
      /* 前脚脚尖不耐烦地点地：脚踝钉住（'l'），脚尖上下点（框上、右、下三边透明） */
      flex: { idle: [[238, 257, 262, 283, 'l', 6, 0.9]] },
      /* wind0（第一张条的蓄力，手只到肩后）当蓄力前段，wind（第二张条的强蓄力，手甩到身后）接着 */
      atk: { kind: 'throw', item: 'bra', prop: 'assets/world/trio_prop_bra.webp', scale: 0.55,
             seq: [['wind0', 0.1], ['wind', 0.22], ['throw', 0.1, 'fire'], ['follow', 0.3]],
             hold: { idle: [116, 157], wind0: [42, 77], wind: [36, 123], throw: [285, 77] },
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
      /* 翘起来的两条小腿 + 靴子是挂件层（bestie/G22_explorer/legs.py 从 idle 拆出来，四个在场帧里原处已清掉）：
         绕小腿中段的切口来回晃 = 趴着懒洋洋晃脚。爬的帧（腿平放）不画。切口两层重叠 4 行、重叠处硬边（不然叠出一道 1 px 暗线） */
      parts: [{ src: 'assets/trio/G22_legs.webp', pivot: [61.5, 96], z: 1, sway: [0.06, 0.6, 0],
                at: { idle: [99.5, 100, 0], wind: [99.5, 100, 0], throw: [99.5, 100, 0], follow: [99.5, 100, 0] } }],
      atk: { kind: 'camera', seq: [['wind', 0.3], ['throw', 0.12, 'fire'], ['follow', 0.35]],
             hold: { throw: [424, 50] }, stretch: 0, gap: [1.0, 1.4] },
    },

    G24: {      // 宫斗贵妃（华妃式）：侧卧着从左下角滑进来、撑肘起身扶正旗头，弹出一枚金护甲砸他 —— 赏"一丈红"（打中炸红粉）
      face: +1,
      sheet: { src: 'assets/trio/G24_huafei.webp', cell: [490, 193], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'slide', 'land', 'wind2', 'idle2'] },
      anchor: [353.1, 181.8], at: [240, 1325, 1], pivot: [353, 181],
      leanK: 0,   // 侧卧：整体前后倾会把贴地的腿翘起来
      depth: 1.3, recipe: 'rouge',
      enter: { kind: 'slide', seq: [['slide', 0.45], ['land', 0.16, 'land'], ['idle', 9]], sq: 0.1 },
      exit: { frame: 'slide' },
      idle: { frame: 'idle', breathe: [0.016, 0.7, 0] },   // 躺着：只竖向起伏，不横向补（贴地的脚不左右挪）
      /* 两只脚尖懒洋洋地翘：小腿钉住（'l'），往右越翘越高（框上、右、下三边透明） */
      flex: { idle: [[448, 125, 489, 192, 'l', 7, 0.8]] },
      /* 金护甲：bestie/tools/prop_nailguard.py 程序画的（她手指上的护甲跟手指叠着，抠不出来） */
      atk: { kind: 'throw', item: 'nailguard', prop: 'assets/world/trio_g24_nailguard.webp', scale: 0.45,
             seq: [['wind', 0.28], ['throw', 0.1, 'fire'], ['follow', 0.3]],
             hold: { wind: [127, 34], throw: [421, 59] },
             T: 0.5, arc: 0.2, spin: 12, stretch: 0, gap: [1.0, 1.4], onHit: 'bounce' },
    },
    G25: {      // 大针筒护士：踩着输液架轮座从左下角滑进来、跳下来半跪扶着输液架，甩一支巨型针筒飞镖，扎在他头上
      face: +1,
      sheet: { src: 'assets/trio/G25_nurse.webp', cell: [314, 352], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'ride', 'hop', 'wind2', 'idle2'] },
      anchor: [192.3, 348.5], at: [185, 1330, 1], pivot: [192, 348],
      leanK: 0,   // 半跪：整体前后倾会把着地的膝盖和脚带起来
      depth: 1.3, recipe: 'rouge',
      /* 输液架画在帧里（她一直扶着）：进场踩在轮座上滑、跳下来落成半跪 */
      enter: { kind: 'slide', seq: [['ride', 0.42], ['hop', 0.14], ['idle', 9, 'land']], sq: 0.1 },
      exit: { frame: 'ride' },
      idle: { frame: 'idle', breathe: [0.016, 0.8, 0] },
      /* 前脚鞋尖点地：脚踝钉住（'l'），往右越翘越高（框上、右、下三边透明） */
      flex: { idle: [[228, 315, 258, 351, 'l', 7, 1.0]] },
      /* 巨型针筒：tools/3d/syringe.py 3D 转盘；扎在头上那一支用平面图（onHit 'wear' 只画 prop） */
      atk: { kind: 'throw', item: 'syringe', r: 36, atlas: { src: 'assets/trio/prop_syringe.webp', n: 36, cols: 6, cell: 128, scale: 1.10 },
             prop: 'assets/world/trio_g25_syringe.webp',
             seq: [['wind', 0.28], ['throw', 0.1, 'fire'], ['follow', 0.3]],
             hold: { idle: [118, 100], wind: [100, 82], throw: [297, 119] },
             T: 0.5, arc: 0.15, spin: 6.3, idleSpin: 0.6, stretch: 0.03, gap: [1.0, 1.4], onHit: 'wear' },
    },
    G30: {      // 葫芦山蛇精式妖女：像蛇一样左右扭着从左下角滑进来、斜倚坐起，举如意放一道绿光吸住他
      face: +1,
      sheet: { src: 'assets/trio/G30_snake.webp', cell: [497, 275], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'slither1', 'slither2', 'wind2', 'idle2'] },
      anchor: [228.2, 276.8], at: [160, 1332, 1], pivot: [228, 276],
      leanK: 0,   // 斜倚在地上：整体前后倾会把贴地的蛇尾裙摆翘起来
      depth: 1.3, recipe: 'star',
      /* 进场：贴地 S 形扭滑，两帧左右扭交替；待机用 follow（如意横在膝前）——
         动作条左上那格 idle（如意扛肩）的头比其余几格画大了 6%（frames.json 缩放锁 1，按身子对齐），不上场 */
      enter: { kind: 'slide', seq: [['slither1', 0.13], ['slither2', 0.13], ['slither1', 0.13], ['slither2', 0.13], ['follow', 9, 'land']], sq: 0.08 },
      exit: { frame: 'slither2' },
      idle: { frame: 'follow', breathe: [0.016, 0.7, 0] },
      /* 发髻上垂下的翠玉流苏：顶钉住（'t'），框左、右、下三边透明 */
      flex: { follow: [[250, 113, 260, 138, 't', 6, 1.1]] },
      /* 如意画在帧里：往后抡（wind2）→ 举过头顶（wind）→ 指向他放光（throw）→ 收回膝前（follow = 待机） */
      atk: { kind: 'beam', seq: [['wind2', 0.18], ['wind', 0.2], ['throw', 0.5, 'fire'], ['follow', 0.3]],
             hold: { wind2: [214, 117], wind: [240, 14], throw: [482, 124] }, stretch: 0, gap: [1.0, 1.4],
             beam: { fire: 0.45, drip: 0.1, ball: 30, glow: [120, 255, 150], edge: [20, 120, 60],
                     layers: [[40, [20, 120, 60], 0.3], [28, [60, 200, 100], 0.6], [16, [140, 255, 170], 0.9], [6, [240, 255, 240], 1]] } },
    },
    G26: {      // 蝴蝶发饰剑士（蝴蝶忍式）：从左上轻轻一跃、张开蝴蝶羽织落地蹲下，挥袖放出一群毒蝴蝶扑过去
      face: +1,
      sheet: { src: 'assets/trio/G26_shinobu.webp', cell: [333, 316], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'leap', 'land', 'wind2', 'idle2'] },
      anchor: [179.0, 311.1], at: [175, 1330, 1], pivot: [179, 311],
      leanK: 0,   // 蹲着：整体前后倾会把着地的木屐带起来
      depth: 1.3, recipe: 'petal',
      /* 轻跳落地：h 小（身形轻），腾空张开羽织 → 脚尖点地 → 蹲下 */
      enter: { kind: 'leap', h: 70, air: 0.45, sq: 0.1, seq: [['leap', 0.45], ['land', 0.14, 'land'], ['idle', 9]] },
      exit: { frame: 'leap' },
      idle: { frame: 'idle', breathe: [0.018, 0.75, 0] },
      /* 羽织袖子垂下的那一角（蝴蝶翅尖）：顶钉住（'t'），框左、右、下三边透明 */
      flex: { idle: [[78, 210, 120, 257, 't', 7, 0.9]] },
      /* 毒蝴蝶：tools/3d/butterfly.py 3D 转盘齐射件，一次放 5 只；待机时指尖停着一只 */
      atk: { kind: 'throw', item: 'butterfly', r: 22, n: 5, atlas: { src: 'assets/trio/prop_butterfly.webp', n: 36, cols: 6, cell: 76, scale: 1.13 },
             seq: [['wind2', 0.28], ['throw', 0.1, 'fire'], ['follow', 0.3]],
             hold: { idle: [153, 62], wind2: [53, 67], throw: [326, 50] },
             T: 0.6, arc: 0.3, spin: 5.2, idleSpin: 0.5, stretch: 0.03, gap: [1.0, 1.4] },
    },
    G27: {      // 暴脾气平民女孩（杉菜式）：从左下角冲过来一记滑铲、撑地起身半跪，抡起书包砸过去
      face: +1,
      sheet: { src: 'assets/trio/G27_shancai.webp', cell: [332, 314], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'tackle', 'rise', 'wind2', 'idle2'] },
      anchor: [134.0, 308.1], at: [170, 1330, 1], pivot: [134, 308],
      leanK: 0,   // 半跪：整体前后倾会把跪地的膝盖带起来
      depth: 1.3, recipe: 'thud',
      /* 滑铲进来（前脚鞋底朝前）→ 刹住撑地起身 → 半跪；wind / follow 两帧的前腿按 idle 挪正过（G27_shancai/fixleg.py，build 后必跑） */
      enter: { kind: 'slide', seq: [['tackle', 0.46], ['rise', 0.14, 'land'], ['idle', 9]], sq: 0.1 },
      exit: { frame: 'tackle' },
      idle: { frame: 'idle', breathe: [0.018, 0.8, 0] },
      /* 书包：引擎 3D 转盘（tools/3d/schoolbag.py，道具表 r 30 cell 115 scale 1.37）；待机拎着书包带在手里晃（idleSpin） */
      atk: { kind: 'throw', item: 'schoolbag', r: 30, atlas: { src: 'assets/trio/prop_schoolbag.webp', n: 36, cols: 6, cell: 115, scale: 1.37 },
             seq: [['wind', 0.28], ['throw', 0.1, 'fire'], ['follow', 0.3]],
             hold: { idle: [116, 118], wind: [10, 152], throw: [266, 20] },
             T: 0.5, arc: 0.22, spin: 6.3, idleSpin: 0.9, stretch: 0.03, gap: [1.0, 1.4], onHit: 'bounce' },
    },
    G28: {      // 80 年代健美操女：从左边一路开合跳进来，指尖转着呼啦圈，甩出去套在他头上
      face: +1,
      sheet: { src: 'assets/trio/G28_aerobics.webp', cell: [301, 417], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'jump1', 'jump2', 'jump3', 'jump4'] },
      anchor: [138.9, 396.5], at: [175, 1330, 1], pivot: [138, 396],
      leanK: 0,   // 两脚大开站定：整体前后倾绕两脚中点转，离中点 120 px 的脚会上下挪 7 px（量出来的）
      depth: 1.3, recipe: 'star',
      /* 开合跳：jump1 并腿落地 → jump2 腾空张开 → jump3 开腿落地、双臂举成 V → jump4 腾空合拢（偶数帧接地、奇数帧 bob 抬起，规范第九节 G28）。
         stride = 每跳前进的距离（格内像素）：接地 → 腾空 → 接地换两次帧，每次前进 stride / 2 */
      enter: { kind: 'walk', fps: 6, bob: 40, stride: 110, seq: [[['jump1', 'jump2', 'jump3', 'jump4'], 9]] },
      exit: { frame: ['jump1', 'jump2', 'jump3', 'jump4'], fps: 8, flip: true, T: 0.8 },
      idle: { frame: 'idle', breathe: [0.014, 0.9] },
      /* 呼啦圈：引擎 3D 转盘（道具表 r 36 cell 108 scale 1.07），待机顶在指尖上转；套在他头上那只用图集第 4 格（压扁的椭圆）当平面图。
         收势用 jump3（双臂举成 V 欢呼）：A 条的 follow 那格头画小了 9%，按头缩放后脚踩到地板下 17 px，不上场 */
      atk: { kind: 'throw', item: 'hoop', r: 36, atlas: { src: 'assets/trio/prop_hoop.webp', n: 36, cols: 6, cell: 108, scale: 1.07 },
             prop: 'assets/world/trio_g28_hoop.webp',
             seq: [['wind', 0.28], ['throw', 0.1, 'fire'], ['jump3', 0.35]],
             hold: { idle: [84, 40], wind: [27, 196], throw: [295, 114] },
             T: 0.55, arc: 0.25, spin: 5.7, idleSpin: 2.5, stretch: 0.03, gap: [1.0, 1.4], onHit: 'wear' },
    },
    G29: {      // 打狗棒女侠（黄蓉式）：撑着打狗棒从左上一跃、棒子点地荡进来落成蹲，竹棒伸缩着捅过去
      face: +1,
      sheet: { src: 'assets/trio/G29_huangrong.webp', cell: [309, 339], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'vault', 'swing', 'land', 'idle2'] },
      anchor: [188.4, 331.7], at: [180, 1328, 1], pivot: [188, 331],
      leanK: 0,   // 蹲着、一只手撑地：整体前后倾会把撑地的手和靴子带起来
      depth: 1.3, recipe: 'thud',
      /* 撑棒跃进：双手握棒顶腾空（vault）→ 收腿荡过去（swing）→ 落地蹲下单手撑地（land）→ 待机 */
      enter: { kind: 'leap', h: 120, air: 0.45, sq: 0.1, seq: [['vault', 0.25], ['swing', 0.2], ['land', 0.14, 'land'], ['idle', 9]] },
      exit: { frame: 'vault' },
      idle: { frame: 'idle', breathe: [0.018, 0.75, 0] },
      /* 打狗棒：定妆拆好的挂件层（bestie/ref/G29_staff.png → tools/part.py h 281），挂点 = 握棒处（棒长 80% 那一点）。
         待机 / 落地：握在举起的左拳里、斜靠在背后；腾空两帧：双手握棒顶、棒子往下（转 π，荡的那帧更竖）；
         wind / throw / follow 不画（这几帧手里画着一截短竹棒，捅出去的就是它） */
      parts: [{ src: 'assets/trio/G29_staff.webp', pivot: [107, 222], z: -1, sway: [0.04, 0.7, 0],
                at: { idle: [120, 117, 0], land: [111, 195, 0], vault: [182, 12, 3.1416], swing: [170, 80, 3.44] } }],
      /* 伸缩棒（帧序列 punch）：棒头从 throw 帧里抠，伸出去的"管子"填竹子色；收势 = 收棒回腰（用 wind 帧）——
         A 条 follow（棒扛肩）那格两腿站位画得不一样（配准残差 6.7 px），不上场 */
      atk: { kind: 'punch', seq: [['wind', 0.3], ['throw', 0.55, 'fire'], ['wind', 0.25]],
             fist: [270, 145, 308, 163], fistC: [290, 154], wrist: [262, 157], armW: 8,
             skin: '#6cbf45', skinShade: 'rgba(40,110,30,.55)', skinEdge: '#1f3d12', fistZ: 1.3, phases: [0.16, 0.12, 0.22],
             stretch: 0, gap: [1.0, 1.4] },
    },
    /* ---- 后排地面（站在女生身后左边、画在主角之后；样板 B5，规范 4.3 / 6.4 后排出手翻过自己主角头顶） ---- */
    G4: {       // 丸子头旗袍格斗家（春丽式）：倒立劈叉旋转踢从左边转进来、落地一蹲、站成格斗架；百裂脚 —— 右腿高踢连踢，一串腿影从女生头顶翻过去砸他
      face: +1,
      sheet: { src: 'assets/trio/G4_chunli.webp', cell: [533, 498], cols: 4, names: ['idle', 'wind', 'hitA', 'hitB', 'spin1', 'spin2', 'land', 'follow'] },
      /* 锚点 = 前脚（右脚）鞋底：踢腿是后腿踢、站在前脚上，出手四帧按这只靴子配准（残差 0.38 px）。
         后排：脚底 y 1040（同组地板 G21 头顶 1052，不叠），x 250 在女生身后左边，站姿高约 350 px */
      anchor: [287.5, 478.5], at: [250, 1040, 0.9], pivot: [287, 478], leanK: 0,
      depth: 0.8, recipe: 'star',
      /* 翻滚进来：整张图转一圈（引擎 roll）的同时帧在换 —— 倒立劈叉 → 斜劈叉 → 倒立劈叉 → 落地一蹲（压扁）→ 格斗架 */
      enter: { kind: 'roll', T: 0.9, seq: [['spin1', 0.2], ['spin2', 0.2], ['spin1', 0.3], ['land', 0.2, 'land'], ['idle', 9]], sq: 0.1 },
      exit: { frame: 'spin2' },
      idle: { frame: 'idle', breathe: [0.014, 0.8, 0] },   // 两脚站定：只竖向起伏，后脚不左右挪
      /* 包子套上的白飘带往后（左）飘：根在右边（钉右），其余三边透明 */
      flex: { idle: [[88, 110, 129, 176, 'r', 10, 1.1]] },
      /* 百裂脚：抬膝蓄力 → 高踢 / 平踢每秒 10 帧交替 0.6 秒、每 0.1 秒一道腿影飞过去 → 比 V 收势。
         出手点 = hitA 踢过头顶的那只靴子（后排：腿影从女生头顶翻过去） */
      atk: { kind: 'rush', seq: [['wind', 0.3], [['hitA', 'hitB'], 0.6, 'fire'], ['follow', 0.5]], fps: 10, from: [415, 40],
             rush: { n: 6, every: 0.1, T: 0.1, line: '#bfe0ff',
                     ghost: [{ frame: 'hitA', box: [350, 0, 450, 130] }, { frame: 'hitB', box: [410, 120, 533, 205] }] },
             gap: [0.8, 1.2], stretch: 0.03 },
    },

    G5: {       // 客栈老板娘（佟湘玉式）：腰侧挂着大算盘、叉着腰扭着走进来，惊呼"额滴神"；摘下算盘举过头顶，一把 3D 算盘甩出去砸他
      face: +1,
      sheet: { src: 'assets/trio/G5_tong.webp', cell: [319, 440], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'walk1', 'walk2', 'walk3', 'walk4'] },
      /* 锚点 = 前脚（右脚）鞋底：出手四帧按这只鞋配准（残差 0.23 px）。脚底 y 1020（同组地板 G23 头顶 1028，不叠），站姿高约 350 px */
      anchor: [190.4, 434.3], at: [230, 1020, 0.88], pivot: [190, 434], leanK: 0,
      depth: 0.8, recipe: 'debris',
      /* 扭腰走：走路条四帧出自同一张底图（raw/act_b1.png），walk1 / walk3 接地（两腿对调）、walk2 / walk4 过渡；左手一直叉腰，右手 后 → 中 → 前 → 中。
         stride 119 = 相邻两帧着地那只鞋的鞋跟距离（61 / 58 / 59 / 58）× 2 的平均：每次换帧前进 59.5，同一只脚前后差 ≤ 1.5（格内像素） */
      enter: { kind: 'walk', fps: 6, bob: 6, stride: 119, seq: [[['walk1', 'walk2', 'walk3', 'walk4'], 9]] },
      exit: { frame: ['walk1', 'walk2', 'walk3', 'walk4'], fps: 8, flip: true, T: 0.8 },
      idle: { frame: 'idle', breathe: [0.014, 0.8, 0] },
      /* 算盘是挂件层（定妆拆层 ref/G5_abacus.png，part.py w 90）：红绳吊在左胯，绕绳头晃；举过头顶 / 甩出去那两帧不画（在手里的是 3D 算盘） */
      parts: [{ src: 'assets/trio/G5_abacus.webp', pivot: [41, 1], z: 1, sway: [0.1, 0.9, 0],
                at: { idle: [78, 214, 0], follow: [78, 222, 0], walk1: [84, 226, 0], walk2: [78, 226, 0], walk3: [84, 226, 0], walk4: [78, 226, 0] } }],
      /* 两手举过头顶（后排：出手点在女生头顶以上）→ 往前甩出 → 捂胸叹气。3D 算盘照道具表 r 40 cell 115 scale 1.35，转速 π / T */
      atk: { kind: 'throw', item: 'abacus', r: 40, atlas: { src: 'assets/trio/prop_abacus.webp', n: 36, cols: 6, cell: 115, scale: 1.35 },
             seq: [['wind', 0.32], ['throw', 0.1, 'fire'], ['follow', 0.35]],
             hold: { wind: [188, 32], throw: [300, 72] },
             T: 0.55, arc: 0.25, spin: 5.7, idleSpin: 0.6, stretch: 0.03, gap: [1.0, 1.4], onHit: 'bounce' },
    },

    G6: {       // 平底锅主妇（蜡笔小新妈式）：额头冒青筋、围裙拖鞋气冲冲跑进来，攥着平底锅；把锅举过头顶抡出去，3D 平底锅"当"地砸在他头上
      face: +1,
      sheet: { src: 'assets/trio/G6_misae.webp', cell: [316, 403], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'walk1', 'walk2', 'walk3', 'walk4'] },
      /* 锚点 = 前脚拖鞋鞋底：出手四帧按这只拖鞋配准（残差 0.31 px）。脚底 y 1040（同组地板 G30 头顶 1057），站姿高约 350 px */
      anchor: [220.6, 397.1], at: [250, 1040, 0.88], pivot: [220, 397], leanK: 0,
      depth: 0.8, recipe: 'thud',
      /* 气冲冲跑进来：跑步条四帧出自同一张底图（raw/walk_base.png；walk3 的两臂用蒙版重绘成和 walk1 反过来：近手往前捶、远手甩到背后，raw/act_b1.png）。
         每秒 12 帧、一步一伏 10 px。stride 175：相邻两帧着地那只拖鞋的鞋跟前进 82 / 92 / 86 / 90（格内像素），取平均 87.5 × 2；同一只脚换帧差 ≤ 5.5 格内（≤ 4.8 屏幕 px） */
      enter: { kind: 'walk', fps: 12, bob: 10, stride: 175, seq: [[['walk1', 'walk2', 'walk3', 'walk4'], 9]] },
      exit: { frame: ['walk1', 'walk2', 'walk3', 'walk4'], fps: 12, flip: true, T: 0.6 },
      idle: { frame: 'idle', breathe: [0.016, 0.9, 0] },
      /* 后脑勺那一撮卷发往后（左）甩：根在右边（钉右），框上、下、左三边透明 */
      flex: { idle: [[108, 34, 128, 88, 'r', 9, 1.0]] },
      /* 平底锅照道具表 3D：r 30 cell 91 scale 1.08，转速 π / T。待机攥在右拳里（慢慢晃着转），蓄力举过头顶（后排：出手点在女生头顶以上），出手后叉腰喘粗气 */
      atk: { kind: 'throw', item: 'pan', r: 30, atlas: { src: 'assets/trio/prop_pan.webp', n: 36, cols: 6, cell: 91, scale: 1.08 },
             seq: [['wind', 0.3], ['throw', 0.1, 'fire'], ['follow', 0.35]],
             hold: { idle: [218, 212], wind: [120, 6], throw: [296, 72] },
             T: 0.55, arc: 0.3, spin: 5.7, idleSpin: 0.5, stretch: 0.03, gap: [1.0, 1.4], onHit: 'bounce' },
    },

    G7: {       // 黑裙荆棘杀手（约尔式）：一团暗紫黑烟里蹲着现身、起身撩发，温柔地笑；手指夹着玫瑰护手的细刺刀举过头顶甩出去
      face: +1,
      sheet: { src: 'assets/trio/G7_yor.webp', cell: [330, 411], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'crouch', 'rise', 'emerge', 'idle2'] },
      /* 锚点 = 前脚高跟靴：出手四帧按这只靴子配准（残差 0.19 px）。脚底 y 1000（同组地板 G26 头顶 1021，最低点 1018 不叠），站姿高约 290 px */
      anchor: [247.7, 385.4], at: [260, 1000, 0.88], pivot: [247, 385], leanK: 0,
      depth: 0.8, recipe: 'petal',
      /* 阴影一闪：淡入（0.35 秒）时蹲着低头，淡入完起身撩发 → 站起张手 → 待机（淡入结束后换了两次帧） */
      enter: { kind: 'appear', fx: 'smoke', color: [60, 20, 70], seq: [['crouch', 0.35], ['rise', 0.18], ['emerge', 0.14, 'land'], ['idle', 9]], sq: 0.05 },
      exit: { frame: 'crouch' },
      idle: { frame: 'idle', breathe: [0.014, 0.8, 0] },
      /* 身后的长发梢连同垂着的后手一起慢慢晃（根在右边钉住；框上、下、左三边透明） */
      flex: { idle: [[9, 98, 66, 212, 'r', 5, 0.8]] },
      /* 细刺刀是平面图（bestie/G7_yor/raw/knife_src.png 抠出来，180 px 长 × 0.5）：手指夹着举过头顶（后排：出手点在女生头顶以上）→ 甩出去打着转飞 */
      atk: { kind: 'throw', item: 'knife', prop: 'assets/world/trio_g7_knife.webp', scale: 0.5,
             seq: [['wind', 0.28], ['throw', 0.1, 'fire'], ['follow', 0.35]],
             hold: { wind: [84, 16], throw: [316, 86] },
             T: 0.4, arc: 0.12, spin: 14, stretch: 0.03, gap: [0.9, 1.3], onHit: 'bounce' },
    },

    /* ---- 上方（左上，男女主头顶以下；样板 G11） ---- */
    G15: {      // 船头红发少女（泰坦尼克 Rose 式）：站在一截白色船头上从左边平着滑出来，捂着心口 → 张开双臂"飞"；举起心形蓝宝石项链一抛（3D）砸他
      face: +1,
      sheet: { src: 'assets/trio/G15_rose.webp', cell: [362, 435], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'grip', 'step', 'open', 'idle2'] },
      /* 船头画在每一帧里（动作条每格同一截船头，人站在同一处），锚点 = 两只高跟鞋之间的船头甲板；按两只鞋配准（残差 0.22 px）。
         grip / step 两帧模型多画了一根竖栏杆（船头变形），不上场。大小：人（不算船头）剪影 × 0.75² ≈ 2.34 万（上方样板 G11 2.06 万，+14%，蓬裙占得多）。
         站位：同组后排 G5 头顶 671、蓄力举过头的算盘顶到 626，船头最低点 616 让开 */
      anchor: [212.4, 367.4], at: [190, 565, 0.75], pivot: [212, 367], leanK: 0,
      depth: 0.5, recipe: 'bloom',
      /* 船头从左边画外平着滑进来（fly，from 在同一高度偏左、dy 小），减速到位；滑行时捂着心口 → 双臂半张 → 到位张开双臂（露面后换两次帧，最后标 land） */
      enter: { kind: 'fly', from: [-420, -30], air: 0.75, tilt: 0.04, seq: [['follow', 0.35], ['open', 0.3], ['idle', 9, 'land']], sq: 0.05 },
      exit: { frame: 'follow' },
      idle: { frame: 'idle', breathe: [0.014, 0.6, 0] },
      /* 往后飘的长卷发：根在右边钉住，框上、下、左三边透明 */
      flex: { idle: [[42, 45, 140, 152, 'r', 6, 0.8]] },   // 框里连着张开的左手：飘发和手一起随风轻晃
      /* 心形蓝宝石项链照道具表 3D：r 26 cell 79 scale 1.39，转速 π / T */
      atk: { kind: 'throw', item: 'necklace', r: 26, atlas: { src: 'assets/trio/prop_necklace.webp', n: 36, cols: 6, cell: 79, scale: 1.39 },
             seq: [['wind', 0.3], ['throw', 0.1, 'fire'], ['follow', 0.35]],
             hold: { wind: [250, 14], throw: [352, 52] },
             T: 0.55, arc: 0.2, spin: 5.7, idleSpin: 1.2, stretch: 0.03, gap: [1.0, 1.4], onHit: 'bounce' },
    },

    /* ---- 单张立绘（旧，等按规范重做成帧序列） ---- */
    G12: {      // 紫衣仙子：秋千从左上画外荡进来，飞吻，爱心打到他脸上留下口红印（查岗证据）
      face: +1, src: 'assets/world/trio_fairy.webp', at: [165, 230, 1],   /* 2026-10-01 自由组合：原 y 360 秋千荡下来压后排地面的头，抬 130（组合遮挡矩阵_bestie 建议站位） */
      anchor: [145, 0], pivot: [145, -480], hand: [238, 115],
      depth: 0.5, enter: 'swing', recipe: 'rouge', ropes: { ...ROPE, x: [100, 190], fill: '#a7864f' },
      swing: { a0: 1.3, a: 0.12, tau: 0.5, w: 2.4 },
      atk: { kind: 'throw', item: 'heart', n: 2, color: [255, 70, 130], T: 0.55, arc: 0.1, spin: 0, onHit: 'lips' },
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
