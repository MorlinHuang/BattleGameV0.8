/* trio_tune.js —— 引擎负责人量好、还没抄进角色数据的逐人数值（精引2，2026-10-01）。**引擎负责人维护**。
 *
 * 为什么单独一个文件：两位美术正在改 trio_buddy.js / trio_bestie.js（改了还没提交，还部署了中间版），引擎这边同时去改会互相覆盖。
 * 这里的值按 docs/三人组角色规范.md「出手方向」「待机轮换与换帧淡入」的交接表一条条抄进角色数据即可；trio.js tuned() 合并时
 * **角色数据里写了的一律以角色数据为准**，抄过去以后这里那一条自动不起作用，引擎负责人再删掉。
 *
 *   dir      → atk.dir       { 帧: 仰角° }：出手那一帧手臂 / 道具 / 嘴朝哪（人朝对手那边 0°，往上正、往下负），在图集那一格上量
 *   atlasAim → atk.atlas.aim { cell, tip }：3D 转盘道具朝前飞时定格在第几格、这一格里尖头朝哪（弧度，图上量）
 *   alt      → idle.alt      { frame, every: [秒, 秒], hold: [秒, 秒] }：待机轮换
 *   at.arm   → atk.arm       { box, pivot, max }：伸缩臂出拳时整条手臂绕肩转过去对准落点（box 框里只能有手臂和拳头）
 *   band     → atk.band  精引3 带状物 / 伸缩臂的画法（trio_fx.js 第 5 节）：抽打默认 'silk'，G17 'blade'（软鞭剑）；伸缩臂默认 'arm'，G29 'bamboo'（打狗棒）
 *   trail    → atk.trail 精引3 飞行物拖尾（trio_fx.js 第 10 节）：TrioFX.TRAIL 的名字 'fox' / 'gem' / 'moon'，或 [[r, g, b], 'fire' | 'glint']
 *   at       → 贴图坐标的点（alt 帧手里东西拿在哪 hold、挂件挂在哪 parts.<挂件图名>）；cell 是量的那一版图集的格子大小，
 *              美术重排图集以后（cell 变了）整块作废，连同 alt 一起不用（trio.js tuned）。地板 G21 G25~G27 G29 按 6038a76 加边（+40, +40~60）重算过
 *
 * 读数（量法、改前 / 改后角度差）：docs/三人组角色规范.md「出手方向」；胶片 shots/polish2/。
 */
'use strict';

const ALT = { frame: 'idle2', every: [0.5, 1.2], hold: [0.6, 1.0] };   // 攒够 0.5~1.2 秒待机时间换一次（出手时暂停，trio.js stepAlt），停 0.6~1.0 秒：在场的人七成时间在出手，每段待机只有 1~1.3 秒，[1.2, 2.2] 时 5 秒里我接的 14 人有 4 个一次都没换（精引2 读数）

const TRIO_TUNE = {
  /* ---- 哥们 ---- */
  /* dir 的数值取 docs/美术打磨自检.md 第 4 节（物理一致性复核，4.2 / 4.3「参照方向」列）换成仰角：
     丢东西 = 出手前一帧 → 出手帧的手位移方向（出手那一下手往哪走）；光束 / 指尖发射 = 手臂、掌的指向；残影 = 图块里肢体的轴向；绸鞭 = 手臂轴；斩痕 = 挥向。
     复核里没有的（B23、G14 斩痕的挥向）按复核 4.6 第 5 条写 */
  B5: { dir: { hitA: 0, hitB: 0 } },
  B6: { dir: { throw: 47.7 } },
  B7: { dir: { swing: -45 } },
  B8: { dir: { swing: 38.4 } },
  B9: { dir: { swing: -12.3 } },
  B10: { dir: { swing: -70.5 }, at: { cell: [480, 425], hold: { throw: [108, 224] } } },   // 线上图集出手帧（throw）张开的手掌；ce7d459 起 hold 只写了 wind / swing，出手点读空抛错停主循环
  /* 上方 / 地板 */
  B11: { dir: { throw: 16 } },
  B23: { dir: { throw: 60 }, at: { cell: [510, 294], hold: { throw: [124, 41] } } },   // 三刀往左上扫（复核 4.6-5：刀尖往左上 ≈ 60°）；剑气从上面那把刀的刀尖出（throw 格量）
  B14: { dir: { throw: -67 } },
  // B15：指尖弹出的光球是能量（走直线、不受重力），不写 dir；throw 手臂已往下转 38° 对准落点（2026-10-02，buddy/B15_gojo/armswing.py）
  B17: { dir: { throw: 0 } },
  B18: { dir: { throw: -15 } },
  B21: { dir: { throw: -52.3 } },
  B24: { dir: { throw: -4.4 } },
  B25: { dir: { throw: -19.6 } },
  B27: { dir: { throw: 2 } },
  B28: { dir: { throw: -65.1 } },
  B30: { dir: { throw: -40 } },
  /* 伸缩臂（punch）的前臂方向就是 atk.wrist → atk.fistC，不用 dir；arm = 出拳时整条手臂绕肩转过去对准落点（trio.js armNeed） */
  B13: { dir: { throw: 0, sword: 0 } },
  B16: { dir: { hitA: 0, hitB: 0 } },
  B19: { dir: { throw: 0 } },
  B20: { dir: { throw: 0 } },
  B22: { dir: { throw: 5 } },
  B26: { dir: { throw: -58.7 } },
  B29: { dir: { throw: 0 } },

  /* ---- 闺蜜 ---- */
  /* G4~G7、G9、G10 的 dir / idle.alt 美术已写进 trio_bestie.js（6038a76 精闺1 第 1 批），这里的删了 */
  G8: { dir: { wind: -42 } },                       // idle2 美术正在重画（16:36 新图：手收回、没地方放冰锥），等定稿再接 alt
  G11: { dir: { throw: 22.3 }, alt: ALT, at: { cell: [315, 343], hold: { idle2: [176, 172] } } },
  G12: { dir: { idle: 0 } },
  G13: { dir: { throw: 18 } },
  G14: { dir: { throw: -45 } },   // 剑尖 hold.throw 已写进角色数据（trio_bestie.js）
  G15: { dir: { throw: -20.4 }, alt: ALT, trail: 'gem' },
  G16: { dir: { throw: -53 }, alt: ALT, trail: 'fox', at: { cell: [288, 401], hold: { idle2: [263, 89] } } },
  G17: { dir: { throw: -45 }, alt: ALT, band: 'blade' },
  G18: { dir: { throw: -16.8 }, atlasAim: { cell: 33, tip: 0.18 } },   // 长枪定格在侧面最长那一格、枪尖顺着飞；idle2 落脚区被 G4 挡 5 px（combo_scan），先不接 alt
  G19: { dir: { throw: -20.4 }, atlasAim: { cell: 33, tip: -1.66 }, alt: ALT },       // 火箭定格在侧面带舷窗那一格（图上尖头朝上）
  G20: { dir: { throw: -41.7 }, alt: ALT, trail: 'moon', at: { cell: [234, 338], hold: { idle2: [228, 72] } } },
  G21: { dir: { throw: 10.5 }, alt: ALT, at: { cell: [377, 344], hold: { idle2: [156, 217] } } },
  // G22：idle2 底边到 y 1342（地板最低 1334，combo_scan 出画 9 px）：美术把 at.y 上移或重切 idle2 后再接 alt
  G23: { dir: { throw: 1.5 }, alt: ALT },
  G24: { dir: { throw: -4.9 }, alt: ALT },
  G25: { dir: { throw: -10.6 }, alt: ALT, at: { cell: [394, 402], hold: { idle2: [158, 150] } } },
  G26: { dir: { throw: 3.6 }, alt: ALT, at: { cell: [413, 376], hold: { idle2: [193, 122] } } },
  G27: { dir: { throw: 27.3 }, alt: ALT, at: { cell: [412, 354], hold: { idle2: [156, 158] } } },
  G28: { dir: { throw: 17 } },
  G29: { band: 'bamboo', alt: ALT, at: { cell: [389, 379], parts: { G29_staff: { idle2: [160, 157, 0] } },
                        arm: { box: [276, 176, 349, 212], pivot: [274, 197] } } },   // 袖口以外的前臂 + 打狗棒，绕袖口（肘在袖子里）转
  G30: { dir: { throw: 20 }, alt: ALT },
};
