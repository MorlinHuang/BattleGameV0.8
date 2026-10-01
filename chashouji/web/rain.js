/* rain.js —— 档 2 的两场"天上掉东西"（2026-09-27）：
 *   查岗党「榴莲鞋雨」（替换抱枕）：男生头顶上方画外掉下 2~3 个榴莲、4 只高跟鞋（红 / 粉 / 黑），砸男生；
 *   灭迹党「臭袜子足球」（替换手柄）：女生头顶上方掉下 2~3 个足球、4 只臭袜子，砸女生。
 * 同一套逻辑两份配置（Drops 工厂），跟 crew.js 的哥们 / 闺蜜一个做法。
 *
 * 不是弹幕（ammo.js 的东西是从一侧平飞过去的），是**天上掉下来的**：竖直方向是真重力（G），
 * 横向每帧按落下的进度把 x 拉到落点 —— 挨砸的人在动（步态、被拖倒趴地），落点每帧重取，东西追着他掉。
 * 落点是他身上随机一处（出手时抽 u，o.target(u) = 他身上第 u 那一列的上沿）：站着砸头、肩、胳膊，
 * 倒地砸背、屁股、腿（第二版只砸脸，他倒地后一串东西全往一个点上落 —— 用户：随机一点，砸到人就行）。
 * 落到所在那一列他的上沿（o.top）就爆（o.onHit，带颜色）并**当场消失**
 * （第一版砸中后弹飞、三成落空掉在地板上弹一下 —— 用户：砸到身上直接爆掉消失，不用落地）。
 *
 * **贴图是 3D 转盘图集**（tools/3d/durian.py、heel.py、football.py、sock.py，跟口红、香蕉同一条管线）：
 * 按转角取那一格画，**不转 canvas** —— 格子里本来就是那个角度渲好的，再叠 2D 旋转光影会跟着转走
 * （生图平面贴纸在画面里打转那一版，用户："参考口红、香蕉做成有体积感的"）。
 * 转速按"落下途中转半圈左右"（~0.8 秒），从第 0 格（建模正面）起步、抖 ±PHASE（danmu-3d-sprite 坑 6）。
 * 画在特效层（人物之前）：东西从镜头这一侧掉在人身上，挡住他是对的。
 * 数值不在这里（送礼的战力走 SHOP.push），这里只负责演出。
 */
'use strict';

function Drops(cfg) {
  const KINDS = cfg.kinds, SEQ = cfg.seq;
  const JIT_T = 0.04;      // 每一项出手时刻抖 ±JIT_T 秒
  const G = 2600;          // 重力（像素/秒²）
  const V0 = 250;          // 出手时往下的初速
  const TOP = -160;        // 从画面上沿以上多高出手
  const DRIFT = 70;        // 出手点离落点横向最多偏多少（斜着掉，不是一根竖线）
  const PHASE = 0.35;      // 起始转角抖多少（rad）
  const LOW = 0.35;        // 碰撞：东西中心往下 LOW × r 落到那一列的上沿就算砸中（按外框算会隔空爆）
  const N = 36, COLS = 6;  // 图集：36 格、6 列

  let o = {};
  const ps = [];           // 在掉的
  let queue = [];          // 还没出手的 [时刻, 什么]
  let clock = 0;

  function init(opt) { o = opt; }

  function load(v, off) {
    if (off) return Promise.resolve(false);
    const one = (a) => new Promise((ok) => {
      const i = new Image();
      i.onload = () => { a.img = i; ok(true); };
      i.onerror = () => ok(false);
      i.src = a.src + (v ? '?v=' + encodeURIComponent(v) : '');
    });
    return Promise.all(Object.values(KINDS).flatMap(K => K.atlas.map(one))).then(r => r.every(Boolean));
  }

  function summon() {
    const seq = Math.random() < cfg.extra[1] ? [...SEQ, cfg.extra[0]] : SEQ;
    for (const [k, t] of seq) queue.push([clock + t + (Math.random() - 0.5) * 2 * JIT_T, k]);
  }

  function drop(kind) {
    const u = Math.random(), f = o.target(u);
    if (!f) return;
    const K = KINDS[kind], a = K.atlas[Math.floor(Math.random() * K.atlas.length)];
    const x0 = f[0] + (Math.random() - 0.5) * 2 * DRIFT;
    ps.push({ kind, a, r: K.r * (0.92 + Math.random() * 0.16), u, x0, x: x0, y: TOP, y0: TOP, vy: V0,
              rot: (Math.random() - 0.5) * 2 * PHASE, vrot: (Math.random() < 0.5 ? -1 : 1) * K.spin * (0.8 + Math.random() * 0.4) });
  }

  function update(dt) {
    clock += dt;
    for (let i = queue.length - 1; i >= 0; i--) if (queue[i][0] <= clock) { drop(queue[i][1]); queue.splice(i, 1); }
    for (let i = ps.length - 1; i >= 0; i--) {
      const p = ps[i];
      p.rot += p.vrot * dt;
      p.vy += G * dt; p.y += p.vy * dt;
      const f = o.target(p.u);
      if (!f) continue;
      /* 横向按落下的进度从出手点拉到落点；落到落点那一列的上沿就爆。o.top 取不到（这一帧他换了姿势，
         那一列正好空了）就按落点的高度算 —— 不能让它穿过人掉下去。 */
      const k = Math.min(1, Math.max(0, (p.y - p.y0) / Math.max(1, f[1] - p.y0)));
      p.x = p.x0 + (f[0] - p.x0) * k;
      const top = o.top(p.x) ?? f[1];
      if (p.y + LOW * p.r >= top) {
        o.onHit(p.kind, p.a.col, p.x, top, KINDS[p.kind].power);
        ps.splice(i, 1);                             // 砸中就没了，爆点接替它
      }
    }
  }

  function draw(ctx) {
    for (const p of ps) {
      const a = p.a;
      /* 图集还没加载到（首帧之后预取队列在排，首帧刚出来就送了档 2，docs/首屏加载诊断.md）：矢量画法，砸照样砸 */
      if (!a.img) { ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot); VEC[p.kind](ctx, p.r, a.col); ctx.restore(); continue; }
      let c = Math.floor(p.rot / 6.2832 * N) % N;
      if (c < 0) c += N;
      const d = p.r * a.scale * 2, e = a.cell;
      ctx.drawImage(a.img, (c % COLS) * e, ((c / COLS) | 0) * e, e, e, p.x - d / 2, p.y - d / 2, d, d);
    }
  }

  const active = () => ps.length > 0 || queue.length > 0;
  function reset() { ps.length = 0; queue = []; }

  return { init, load, summon, update, draw, active, reset };
}

/* 矢量画法（图集没到时用）：形状读得出是什么、颜色跟图集那一份（col）一样；深色描边（浅绿墙上浅色不描边就化掉） */
const VEC_INK = 'rgba(40,30,24,.9)';
const VEC_COL = { white: '#a7b04a', red: '#d8283a', pink: '#f07aa8', black: '#2a2a30', ball: '#f4f4f0', stink: '#d9d2b0' };
const VEC = {
  durian(ctx, r, col) {                       // 榴莲：一圈尖刺的椭圆
    ctx.beginPath();
    for (let i = 0; i < 28; i++) {
      const a = i / 28 * 6.2832, k = i % 2 ? 0.82 : 1;
      ctx.lineTo(Math.cos(a) * r * k, Math.sin(a) * r * 0.86 * k);
    }
    ctx.closePath(); ctx.fillStyle = VEC_COL[col]; ctx.fill();
    ctx.lineWidth = 3; ctx.strokeStyle = VEC_INK; ctx.stroke();
  },
  heel(ctx, r, col) {                         // 高跟鞋：鞋身 + 细跟
    ctx.beginPath();
    ctx.moveTo(-r, r * 0.15); ctx.quadraticCurveTo(-r * 0.2, -r * 0.1, r * 0.25, -r * 0.55);
    ctx.lineTo(r * 0.8, -r * 0.6); ctx.lineTo(r * 0.85, r * 0.6); ctx.lineTo(r * 0.7, r * 0.6); ctx.lineTo(r * 0.62, -r * 0.05);
    ctx.quadraticCurveTo(-r * 0.1, r * 0.4, -r, r * 0.45); ctx.closePath();
    ctx.fillStyle = VEC_COL[col]; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = VEC_INK; ctx.stroke();
  },
  football(ctx, r, col) {                     // 足球：白球 + 中间黑五边形
    ctx.beginPath(); ctx.arc(0, 0, r * 0.9, 0, 6.2832); ctx.fillStyle = VEC_COL[col]; ctx.fill();
    ctx.lineWidth = 3; ctx.strokeStyle = VEC_INK; ctx.stroke();
    ctx.beginPath();
    for (let i = 0; i < 5; i++) { const a = -1.5708 + i * 1.2566; ctx.lineTo(Math.cos(a) * r * 0.32, Math.sin(a) * r * 0.32); }
    ctx.closePath(); ctx.fillStyle = '#222'; ctx.fill();
  },
  sock(ctx, r, col) {                         // 臭袜子：L 形，袜口一道条纹
    ctx.beginPath();
    ctx.moveTo(-r * 0.35, -r); ctx.lineTo(r * 0.2, -r); ctx.lineTo(r * 0.2, r * 0.25);
    ctx.quadraticCurveTo(r * 0.95, r * 0.25, r * 0.95, r * 0.65); ctx.quadraticCurveTo(r * 0.95, r, r * 0.4, r);
    ctx.lineTo(-r * 0.15, r); ctx.quadraticCurveTo(-r * 0.35, r, -r * 0.35, r * 0.7); ctx.closePath();
    ctx.fillStyle = VEC_COL[col]; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = VEC_INK; ctx.stroke();
    ctx.fillStyle = '#5b8c3a'; ctx.fillRect(-r * 0.35, -r * 0.8, r * 0.55, r * 0.14);
  },
};

/* 图集参数照 tools/3d/pack_atlas.py 打印的那行填（cell、scale），每次重渲都要重填。
   r 是引擎里的半径（渲染时的 screen_r，描边按它倒推成屏幕 2.8px）；col 是爆点颜色（main.js 按它挑配方）。
   高跟鞋只渲了红色，粉 / 黑是在图集上把鞋面红调色出来的（tools/3d/recolor_heel.py）。 */
const ATLAS = (name, cell, scale, col) => ({ src: `assets/items/${name}_atlas.webp`, cell, scale, col });

/* 榴莲鞋雨：鞋开头 —— 先下一只把人的眼睛拉到男生头顶，榴莲和鞋交替着砸；
   第三个榴莲（extra，一半概率有）压在最后，是收尾那一下。 */
const DurianRain = Drops({
  kinds: {
    durian: { atlas: [ATLAS('durian', 220, 1.06, 'white')], r: 52, spin: 3.5, power: 2 },
    heel:   { atlas: [ATLAS('heel', 208, 1.22, 'red'), ATLAS('heel_pink', 208, 1.22, 'pink'), ATLAS('heel_black', 208, 1.22, 'black')],
              r: 42, spin: 4.5, power: 1 },
  },
  seq: [['heel', 0], ['durian', 0.16], ['heel', 0.32], ['heel', 0.46], ['durian', 0.6], ['heel', 0.76]],
  extra: [['durian', 0.94], 0.5],
});

/* 臭袜子足球（跟榴莲鞋雨对称）：袜子大小参考高跟鞋（同 r 42）、足球参考榴莲（同 r 52）。 */
const SockRain = Drops({
  kinds: {
    football: { atlas: [ATLAS('football', 220, 1.05, 'ball')], r: 52, spin: 3.5, power: 2 },
    sock:     { atlas: [ATLAS('sock', 220, 1.35, 'stink')], r: 42, spin: 4.5, power: 1 },
  },
  seq: [['sock', 0], ['football', 0.16], ['sock', 0.32], ['sock', 0.46], ['football', 0.6], ['sock', 0.76]],
  extra: [['football', 0.94], 0.5],
});
