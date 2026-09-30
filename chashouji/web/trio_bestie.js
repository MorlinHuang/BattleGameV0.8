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
             hold: { throw: [350, 80] }, stretch: 0.03, gap: [1.0, 1.4],
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
      sheet: { src: 'assets/trio/G22_explorer.webp', cell: [467, 185], cols: 4, names: ['idle', 'wind', 'throw', 'follow', 'crawl1', 'crawl2', 'land', 'idle2'] },
      anchor: [228.8, 152.6], at: [200, 1314, 1], pivot: [228, 152],
      leanK: 0,   // 趴着的人不整体前后倾（同樱木）
      depth: 1.3, recipe: 'star',
      enter: { kind: 'creep', seq: [['crawl1', 0.14], ['crawl2', 0.14], ['crawl1', 0.14], ['crawl2', 0.14], ['land', 0.1, 'land'], ['idle', 9]], sq: 0.08 },
      exit: { frame: 'crawl2' },
      idle: { frame: 'idle', breathe: [0.02, 0.7, 0] },   // 趴着：只竖向起伏
      /* 翘起来的两条小腿 + 靴子是挂件层（bestie/G22_explorer/legs.py 从 idle 拆出来，四个在场帧里原处已清掉）：
         绕小腿中段的切口来回晃 = 趴着懒洋洋晃脚。爬的帧（腿平放）不画 */
      parts: [{ src: 'assets/trio/G22_legs.webp', pivot: [62, 96], z: 1, sway: [0.06, 0.6, 0],
                at: { idle: [105, 100, 0], wind: [105, 100, 0], throw: [105, 100, 0], follow: [105, 100, 0] } }],
      atk: { kind: 'camera', seq: [['wind', 0.3], ['throw', 0.12, 'fire'], ['follow', 0.35]],
             hold: { throw: [430, 50] }, stretch: 0, gap: [1.0, 1.4] },
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
    /* ---- 单张立绘（旧，等按规范重做成帧序列） ---- */
    G12: {      // 紫衣仙子：秋千从左上画外荡进来，飞吻，爱心打到他脸上留下口红印（查岗证据）
      face: +1, src: 'assets/world/trio_fairy.webp', at: [165, 360, 1], anchor: [145, 0], pivot: [145, -480], hand: [238, 115],
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
