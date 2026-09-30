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

    /* B5 是后排地面的样板（引擎负责人 2026-09-30 临时写在这里，哥们美术接手后照规范维护）。素材：v14/trio/tools/samples/B5_jkd */
    B5: {       // 截拳道：从右边画外晃着双节棍走进来，站定摆格斗架；连打——双节棍左右抡，一串棍影砸到她身上，"啊哒"
      face: -1,
      sheet: { src: 'assets/trio/B5_jkd.webp', cell: [423, 482], cols: 4, names: ['idle', 'wind', 'hitA', 'hitB', 'walk1', 'walk2', 'walk3', 'taunt'] },
      anchor: [260.7, 478.1], at: [800, 1158, 0.85], pivot: [260, 478], leanK: 0,   // 站在男生身后右边：脚底 = 地面往上 350 × (1 − 0.9)、比主角小一圈（同 crew.js 后排的透视）
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

    /* ---- 单张立绘（旧，等按规范重做成帧序列） ---- */
    B11: {      // 假面绅士：扒在右边屏幕壁上，甩玫瑰飞镖；打偏的钉在她脚边，打中她头上冒爱心（灭迹党靠分散注意力）
      face: -1, src: 'assets/world/trio_mask.webp', at: [958, 620, 1], anchor: [265, 175], pivot: [262, 175], hand: [30, 205],
      depth: 0.5, enter: 'crawl', recipe: 'petal',
      atk: { kind: 'throw', item: 'rose', prop: 'assets/world/trio_prop_rose.webp', scale: 0.55, T: 0.42, arc: 0.12, spin: 0,
             wind: 0.22, gap: [0.45, 0.7], miss: 0.35, stick: 2.2, onHit: 'heart' },
    },
    B12: {      // 草帽船长：扒在右边屏幕壁上，橡皮手臂伸长弹她脑门
      face: -1, src: 'assets/world/trio_straw.webp', at: [960, 620, 1], anchor: [300, 180], pivot: [298, 180], hand: [15, 70],
      depth: 0.5, enter: 'spring', recipe: 'star',
      atk: { kind: 'punch', fist: [0, 44, 36, 96], fistC: [16, 70], wrist: [36, 70], armW: 16, skin: '#f7cba0', skinShade: 'rgba(214,146,96,.5)', skinEdge: '#5a3420', fistZ: 1.35,
             phases: [0.16, 0.1, 0.34], wind: 0.3, gap: [0.55, 0.9] },
    },
    B22: {      // 悟空：从右下角斜冲上来半跪，推出水版龟派气功
      face: -1, src: 'assets/world/trio_goku.webp', at: [832, 1330, 1.05], anchor: [140, 297], pivot: [200, 285], hand: [8, 72],
      depth: 1.3, enter: 'dash', recipe: 'water',
      atk: { kind: 'beam', beam: { charge: 0.45, fire: 0.6, rest: 0.45, drip: 0.1, ball: 26, glow: [120, 210, 255], edge: [30, 90, 200],
             layers: [[34, [30, 90, 200], 0.35], [22, [90, 180, 255], 0.8], [11, [210, 240, 255], 0.95], [4, [255, 255, 255], 1]] } },
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
