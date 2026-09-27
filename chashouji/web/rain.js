/* rain.js —— 女生档 2「榴莲鞋雨」（2026-09-27 替换抱枕）：男生头顶上方画外掉下一阵东西 ——
 * 2~3 个榴莲、4 只高跟鞋（红 / 粉 / 黑，Q 版），前后 ~1 秒掉完。
 *
 * 不是弹幕（ammo.js 的东西是从一侧平飞过去的），是**天上掉下来的**：竖直方向是真重力（G），
 * 横向每帧按落下的进度把 x 拉到落点 —— 男生在动（步态、被拖倒脸贴地），落点每帧重取，东西追着他的头掉。
 * 落点在他脸上 ±JIT 个半径，碰到脸那一圈就爆（o.onHit，带颜色：榴莲白、鞋按自己的颜色）并**当场消失**。
 * （第一版砸中后弹飞、三成鞋落空掉在地板上弹一下 —— 用户：砸到身上直接爆掉消失，不用落地。）
 * 画在特效层（人物之前）：东西从镜头这一侧掉在他头上，挡住他是对的。
 * 数值不在这里（送礼的战力走 SHOP.push），这里只负责演出。
 */
'use strict';

const Rain = (() => {
  /* 贴图：v14/rain/make.py 出的，按画面尺寸的 2 倍，画的时候按 w（画面像素宽）缩 */
  const KINDS = {
    durian: { src: ['assets/items/rain_durian.webp'], col: ['white'], w: 104, spin: 3, power: 2 },
    heel:   { src: ['assets/items/rain_heel_red.webp', 'assets/items/rain_heel_pink.webp', 'assets/items/rain_heel_black.webp'],
              col: ['red', 'pink', 'black'], w: 84, spin: 8, power: 1 },
  };
  /* 一阵雨的编排：[什么, 第几秒出手]。鞋开头 —— 先下一只把人的眼睛拉到男生头顶，榴莲和鞋交替着砸；
     第三个榴莲（DURIAN3 的概率有）压在最后，是收尾那一下。每一项出手时刻再抖 ±JIT_T 秒。 */
  const SEQ = [['heel', 0], ['durian', 0.16], ['heel', 0.32], ['heel', 0.46], ['durian', 0.6], ['heel', 0.76]];
  const DURIAN3 = [['durian', 0.94], 0.5];
  const JIT_T = 0.04;
  const G = 2600;          // 重力（像素/秒²）
  const V0 = 250;          // 出手时往下的初速
  const TOP = -160;        // 从画面上沿以上多高出手
  const DRIFT = 70;        // 出手点离落点横向最多偏多少（斜着掉，不是一根竖线）
  const JIT = 0.55;        // 落点：脸心左右 ±JIT 个脸半径

  let img = {}, o = {};
  const ps = [];           // 在掉的
  let queue = [];          // 还没出手的 [时刻, 什么]
  let clock = 0;

  function init(opt) { o = opt; }

  function load(v, off) {
    if (off) return Promise.resolve(false);
    const one = (src) => new Promise((ok) => {
      const i = new Image();
      i.onload = () => ok(i);
      i.onerror = () => ok(null);
      i.src = src + (v ? '?v=' + encodeURIComponent(v) : '');
    });
    return Promise.all(Object.entries(KINDS).map(([k, K]) => Promise.all(K.src.map(one)).then((ims) => { img[k] = ims; })))
      .then(() => Object.values(img).every(a => a.every(Boolean)));
  }

  function summon() {
    const seq = Math.random() < DURIAN3[1] ? [...SEQ, DURIAN3[0]] : SEQ;
    for (const [k, t] of seq) queue.push([clock + t + (Math.random() - 0.5) * 2 * JIT_T, k]);
  }

  function drop(kind) {
    const f = o.head();
    if (!f) return;
    const off = (Math.random() - 0.5) * 2 * JIT * f[2], x0 = f[0] + off + (Math.random() - 0.5) * 2 * DRIFT;
    const K = KINDS[kind], j = Math.floor(Math.random() * img[kind].length);
    ps.push({ kind, im: img[kind][j], col: K.col[j], w: K.w * (0.9 + Math.random() * 0.2), off, x0, x: x0, y: TOP, y0: TOP, vy: V0,
              rot: Math.random() * 6.28, vrot: (Math.random() < 0.5 ? -1 : 1) * K.spin * (0.7 + Math.random() * 0.6) });
  }

  /* 碰撞半径：贴图宽的 0.35（高跟鞋细长、榴莲带刺，按外框算会隔空爆） */
  const rad = (p) => p.w * 0.35;

  function update(dt) {
    clock += dt;
    for (let i = queue.length - 1; i >= 0; i--) if (queue[i][0] <= clock) { drop(queue[i][1]); queue.splice(i, 1); }
    for (let i = ps.length - 1; i >= 0; i--) {
      const p = ps[i];
      p.rot += p.vrot * dt;
      p.vy += G * dt; p.y += p.vy * dt;
      const f = o.head();
      if (!f) continue;
      /* 落点是脸心（+off）那一点；横向按落下的进度从出手点拉过去 */
      const gx = f[0] + p.off, k = Math.min(1, Math.max(0, (p.y - p.y0) / Math.max(1, f[1] - p.y0)));
      p.x = p.x0 + (gx - p.x0) * k;
      if (Math.hypot(p.x - f[0], p.y - f[1]) < f[2] + rad(p) || p.y >= f[1]) {
        o.onHit(p.kind, p.col, p.x, Math.min(p.y, f[1]), KINDS[p.kind].power);
        ps.splice(i, 1);                             // 砸中就没了，爆点接替它
      }
    }
  }

  function draw(ctx) {
    for (const p of ps) {
      const h = p.w * p.im.height / p.im.width;
      ctx.save();
      ctx.translate(p.x, p.y); ctx.rotate(p.rot);
      ctx.drawImage(p.im, -p.w / 2, -h / 2, p.w, h);
      ctx.restore();
    }
  }

  const active = () => ps.length > 0 || queue.length > 0;
  function reset() { ps.length = 0; queue = []; }

  return { init, load, summon, update, draw, active, reset };
})();
