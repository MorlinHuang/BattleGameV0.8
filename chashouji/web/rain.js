/* rain.js —— 女生档 2「榴莲鞋雨」（2026-09-27 替换抱枕）：男生头顶上方画外掉下一阵东西 ——
 * 一个榴莲、七只高跟鞋（红 / 粉 / 黑），前后 ~1 秒掉完。
 *
 * 不是弹幕（ammo.js 的东西是从一侧平飞过去的），是**天上掉下来的**：竖直方向是真重力（G），
 * 横向每帧按落下的进度把 x 拉到落点 —— 男生在动（步态、被拖倒脸贴地），落点每帧重取，东西追着他的头掉。
 *   · 砸头的（hit）：落点在他脸上 ±jit 个半径，碰到脸那一圈就爆（o.onHit），然后从头上弹飞出去；
 *   · 落空的（miss，只有鞋）：落点在他身边 MISS 像素开外的地板上，落地弹一下 —— 全砸头读成"瞄准射击"，
 *     掉几只在旁边才是"下雨"。
 * 砸中 / 落地之后都变成"碎物"：不再碰撞，弹一下、转得更快、淡掉。
 * 画在特效层（人物之前）：东西从镜头这一侧掉在他头上，挡住他是对的。
 * 数值不在这里（送礼的战力走 SHOP.push），这里只负责演出。
 */
'use strict';

const Rain = (() => {
  /* 贴图：v14/rain/make.py 出的，按画面尺寸的 2 倍，画的时候按 w（画面像素宽）缩 */
  const KINDS = {
    durian: { src: ['assets/items/rain_durian.webp'], w: 118, spin: 3, power: 2 },
    heel:   { src: ['assets/items/rain_heel_red.webp', 'assets/items/rain_heel_pink.webp', 'assets/items/rain_heel_black.webp'],
              w: 92, spin: 8, power: 1 },
  };
  /* 一阵雨的编排：[什么, 第几秒出手]。榴莲放在中间 —— 先下几只鞋把人的眼睛拉到男生头顶，
     重的那一下再砸下来；放第一个的话后面的鞋全是余韵。每一项出手时刻再抖 ±JIT_T 秒。 */
  const SEQ = [['heel', 0], ['heel', 0.12], ['heel', 0.24], ['durian', 0.38], ['heel', 0.55],
               ['heel', 0.68], ['heel', 0.82], ['heel', 0.96]];
  const JIT_T = 0.04;
  const G = 2600;          // 重力（像素/秒²）
  const V0 = 250;          // 出手时往下的初速
  const TOP = -160;        // 从画面上沿以上多高出手
  const DRIFT = 70;        // 出手点离落点横向最多偏多少（斜着掉，不是一根竖线）
  const JIT = 0.55;        // 砸头的落点：脸心左右 ±JIT 个脸半径
  const MISS_P = 0.3;      // 鞋落空的概率
  const MISS = [60, 220];  // 落空的落在他脸心往**右**（他身后那侧）多远的地板上 —— 两边都掉的话，
                           // 他被拖倒时脸已经挨到女生那边，往左掉的鞋落在女生脚边，读成砸女生
  const BOUNCE = { vy: [380, 620], vx: [120, 320], spin: 2.2, damp: 0.35, fade: 0.45 };  // 弹飞：往上多快、横向多快、转速翻几倍、落地剩几成速度、淡出几秒

  let img = {}, o = {};
  const ps = [];           // 在掉的 + 碎物
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
    for (const [k, t] of SEQ) queue.push([clock + t + (Math.random() - 0.5) * 2 * JIT_T, k]);
  }

  const rnd = (a) => a[0] + Math.random() * (a[1] - a[0]);

  function drop(kind) {
    const f = o.head();
    if (!f) return;
    const miss = kind === 'heel' && Math.random() < MISS_P;
    const off = miss ? rnd(MISS) : (Math.random() - 0.5) * 2 * JIT * f[2];
    const K = KINDS[kind], im = img[kind][Math.floor(Math.random() * img[kind].length)];
    ps.push({ kind, im, w: K.w * (0.9 + Math.random() * 0.2), miss, off, x0: f[0] + off + (Math.random() - 0.5) * 2 * DRIFT,
              x: 0, y: TOP, y0: TOP, vy: V0, vx: 0, rot: Math.random() * 6.28,
              vrot: (Math.random() < 0.5 ? -1 : 1) * K.spin * (0.7 + Math.random() * 0.6), dead: false, a: 1, t: 0 });
    ps[ps.length - 1].x = ps[ps.length - 1].x0;
  }

  /* 碰撞半径：贴图宽的 0.35（高跟鞋细长、榴莲带刺，按外框算会隔空爆） */
  const rad = (p) => p.w * 0.35;

  function update(dt) {
    clock += dt;
    for (let i = queue.length - 1; i >= 0; i--) if (queue[i][0] <= clock) { drop(queue[i][1]); queue.splice(i, 1); }
    const ground = o.ground();
    for (let i = ps.length - 1; i >= 0; i--) {
      const p = ps[i];
      p.t += dt; p.rot += p.vrot * dt;
      p.vy += G * dt; p.y += p.vy * dt;
      if (p.dead) {                                  // 碎物：弹一下、淡掉
        p.x += p.vx * dt;
        if (p.y > ground - rad(p) * 0.6 && p.vy > 0) {
          p.y = ground - rad(p) * 0.6; p.vy *= -BOUNCE.damp; p.vx *= 0.6; p.vrot *= 0.6;
          if (p.fadeT == null) p.fadeT = p.t;
        }
        if (p.fadeT != null) p.a = 1 - (p.t - p.fadeT) / BOUNCE.fade;
        if (p.a <= 0 || p.y > o.H + 200) ps.splice(i, 1);
        continue;
      }
      const f = o.head();
      if (!f) continue;
      /* 落点：砸头的是脸心（+off）那一点，落空的是地板；横向按落下的进度从出手点拉过去 */
      const gx = f[0] + p.off, gy = p.miss ? ground : f[1];
      const k = Math.min(1, Math.max(0, (p.y - p.y0) / Math.max(1, gy - p.y0)));
      p.x = p.x0 + (gx - p.x0) * k;
      if (!p.miss && (Math.hypot(p.x - f[0], p.y - f[1]) < f[2] + rad(p) || p.y >= f[1])) {
        o.onHit(p.kind, p.x, Math.min(p.y, f[1]), KINDS[p.kind].power);
        knock(p, f[0]);
      } else if (p.miss && p.y >= ground - rad(p) * 0.6) {
        p.y = ground - rad(p) * 0.6;
        o.onLand(p.kind, p.x, ground);
        knock(p, p.x - Math.sign(p.off));
        p.vy *= 0.45;                                // 落地只弹一小下
      }
    }
  }

  /* 砸中 / 落地：变碎物，往上弹、往远离 cx 的那边飞，转速翻倍 */
  function knock(p, cx) {
    p.dead = true;
    const side = p.x >= cx ? 1 : -1;
    p.vy = -rnd(BOUNCE.vy); p.vx = side * rnd(BOUNCE.vx); p.vrot *= BOUNCE.spin;
  }

  function draw(ctx) {
    for (const p of ps) {
      const h = p.w * p.im.height / p.im.width;
      ctx.save();
      ctx.globalAlpha = Math.max(0, p.a);
      ctx.translate(p.x, p.y); ctx.rotate(p.rot);
      ctx.drawImage(p.im, -p.w / 2, -h / 2, p.w, h);
      ctx.restore();
    }
  }

  const active = () => ps.length > 0 || queue.length > 0;
  function reset() { ps.length = 0; queue = []; }

  return { init, load, summon, update, draw, active, reset };
})();
