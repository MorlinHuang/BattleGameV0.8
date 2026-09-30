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
      depth: 0.5, enter: 'swing', recipe: 'bloom',
      /* 绳子、座板由引擎画（帧里的座板已抠掉）：ends 座板两头、grip 这一帧哪只手握着绳 [左手, 右手]、board 座板的框 */
      ropes: { ...ROPE, ends: [[50, 207], [208, 207]], board: [44, 205, 214, 222], flowers: '#f59ab8',
               grip: { idle: [[49, 63]], raise: [[44, 63]], throw: [[69, 76]], follow: [[57, 60]], wind: [[25, 72]],
                       tuck: [[98, 60], [227, 63]], kick: [[47, 66], [176, 60]] } },
      swing: { a0: 1.3, a: 0.13, tau: 0.45, w: 2.6, pump: { fwd: 'kick', back: 'tuck', min: 0.3 } },
      exit: { frame: 'tuck' },
      idle: { frame: 'idle', breathe: [0.014, 0.45] },
      /* 帽子后面那根流苏：顶上钉住（'t'），跟着秋千的摆往后甩（最后一项 = 跟摆多少） */
      flex: { idle: [[71, 38, 89, 84, 't', 2.2, 0.8, 5]], tuck: [[130, 38, 145, 84, 't', 2.2, 0.8, 5]], kick: [[50, 36, 66, 88, 't', 2.2, 0.8, 5]] },
      atk: { kind: 'throw', item: 'ball', prop: 'assets/world/trio_prop_ball.webp', scale: 0.5,
             seq: [['raise', 0.12], ['wind', 0.24], ['throw', 0.1, 'fire'], ['follow', 0.3]],
             hold: { idle: [176, 172], raise: [63, 26], wind: [14, 146], throw: [277, 38] },
             T: 0.5, arc: 0.25, spin: 5, idleSpin: 0.8, stretch: 0.04, onHit: 'bounce' },
    },

    /* ---- 单张立绘（旧，等按规范重做成帧序列） ---- */
    G12: {      // 紫衣仙子：秋千从左上画外荡进来，飞吻，爱心打到他脸上留下口红印（查岗证据）
      face: +1, src: 'assets/world/trio_fairy.webp', at: [165, 360, 1], anchor: [145, 0], pivot: [145, -480], hand: [238, 115],
      depth: 0.5, enter: 'swing', recipe: 'rouge', ropes: { ...ROPE, x: [100, 190], fill: '#a7864f' },
      swing: { a0: 1.3, a: 0.12, tau: 0.5, w: 2.4 },
      atk: { kind: 'throw', item: 'heart', n: 2, color: [255, 70, 130], T: 0.55, arc: 0.1, spin: 0, onHit: 'lips' },
    },
    G21: {      // 忍者扇娘：从左下角翻滚进来半跪，胸罩当手里剑甩出去，打中挂在他头上
      face: +1, src: 'assets/world/trio_ninja.webp', at: [140, 1330, 1.05], anchor: [160, 288], pivot: [150, 280], hand: [305, 92],
      depth: 1.3, enter: 'roll', recipe: 'rouge',
      atk: { kind: 'throw', item: 'bra', prop: 'assets/world/trio_prop_bra.webp', scale: 0.55, T: 0.45, arc: 0.18, spin: 16,
             wind: 0.2, gap: [0.7, 1.0], onHit: 'wear' },
    },
    G22: {      // 探险家：从左下角匍匐爬进来，举相机拍照取证，闪光晃他的眼，照片飞出来
      face: +1, src: 'assets/world/trio_explorer.webp', at: [150, 1345, 1.05], anchor: [215, 208], pivot: [330, 200], hand: [415, 48],
      depth: 1.3, enter: 'creep', recipe: 'star',
      atk: { kind: 'camera', wind: 0.18, gap: [0.75, 1.1] },
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
