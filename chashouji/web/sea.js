/* sea.js —— 白娘子的水（2026-09-28）：底部海水 Sea、水花 Splashes、掌心水柱 / 水花的 3D 序列帧贴图 WaterArt（水柱在 crew.js drawJet 里画）。
 * 用户："整个屏幕的底部，从下边缘到男女生下方，用海水汹涌填充（代表白娘子的水法术），海水也需要持续的动画，
 *        海里可以有些虾兵蟹将。白娘子持续 15s，海水也一样。当白娘子消失的时候，海水也消散。"
 * 海面三版：
 *   ① canvas 现画的四条正弦色带 + 白线 —— 用户："太 Q 了，要更写实"；
 *   ② Blender 3 渲 2 的周期 Gerstner 海面（硬切明暗 + 描边）—— 用户："水波纹体积感还是做得太假，水波纹不适合做体积感，
 *      还是回到 2D 的感觉，但不要太 Q，需要写实些表现"；
 *   ③ 现在：动画电影背景那种手绘写实海浪（生图 → 抠像 → 横向无缝长条，v14/sea2/make.py），远 / 中 / 近三层贴图，
 *      动起来靠：各层往相反方向平移（远慢近快）+ 按列上下起伏（一道道涌浪从画面里走过去）+ 浪尖甩出的飞沫。
 *   掌心水柱、打中的水花仍是 3 渲 2（tools/3d/water/jet.py、splash.py），用户这次只否了海面。
 *
 * 海：跟着她走，不自己计时 —— main.js 每帧告诉 update 她在不在施法（on）。在 → 水位 lv 从 0 涨到 1（RISE 秒，整片从屏幕下沿涌上来）；
 * 不在（飞走了）→ 退回 0（FALL 秒：往下沉、越沉越透）。续送她多待一段，海水也就多待一段。
 * 按 远 → 第一排虾兵蟹将 → 中 → 第二排 → 近 叠：兵的下半截被它前面那层海盖住，泡在水里；
 * 兵跟着那层海的浪上沿起伏、按坡度歪 —— 浪上沿是加载时从贴图 alpha 量出来的（每列一个数），再加上当时的平移和起伏。
 *
 * 层级：main.js 画在人物之前（最底下、背景之上）—— 海面顶到男女生脚下，不盖人；档 4 出场压暗照样压它（只有白娘子本人是亮的）。
 */
'use strict';

/* 两套 3D 贴图的参数（tools/3d/water/pack_water.py 打印的，重渲后重填）。
   jet：16 帧、4 列，x0 = 掌心在格子里的 x、cy = 中轴的 y；loop = 引擎里多少秒转一圈（jet.py 按整周期渲，首尾相接）。
   splash：10 帧、5 列，(ox, oy) = 撞击点在格子里的位置；life = 播一遍多少秒。 */
const WaterArt = {
  jet: { src: 'assets/fx/jet.webp', n: 16, cols: 4, w: 712, h: 171, x0: 4, cy: 92, loop: 0.5 },
  splash: { src: 'assets/fx/splash.webp', n: 10, cols: 5, w: 320, h: 239, ox: 160, oy: 151, life: 0.45 },
  load(v, off) {
    if (off) return Promise.resolve(false);
    const one = (o) => new Promise((ok) => {
      const i = new Image();
      i.onload = () => { o.img = i; ok(true); }; i.onerror = () => ok(false);
      i.src = o.src + (v ? '?v=' + encodeURIComponent(v) : '');
    });
    return Promise.all([one(this.jet), one(this.splash)]).then(r => r.every(Boolean));
  },
};
/* 图集里第 i 帧的源矩形 [sx, sy, sw, sh] */
const atlasCell = (A, o, i) => [(i % A.cols) * o.w, ((i / A.cols) | 0) * o.h, o.w, o.h];

/* 水花：一朵 3D 水冠在 (x, y) 播一遍（WaterArt.splash），s = 缩放。白娘子打中男生（main.js 在特效层画）。 */
function Splashes() {
  const list = [];
  return {
    spawn(x, y, s) { list.push({ x, y, s, t: 0 }); },
    update(dt) { for (let i = list.length - 1; i >= 0; i--) if ((list[i].t += dt) >= WaterArt.splash.life) list.splice(i, 1); },
    draw(ctx, alpha = 1) {
      const S = WaterArt.splash;
      if (!S.img) return;
      ctx.save();
      for (const p of list) {
        const u = p.t / S.life, i = Math.min(S.n - 1, Math.floor(u * S.n)), [sx, sy, sw, sh] = atlasCell(S, S, i);
        /* 后五成淡掉：水冠最后收成一圈带刺的环，放大到 1.3 倍（第一下）时整圈清清楚楚，像个救生圈 */
        ctx.globalAlpha = alpha * Math.min(1, (1 - u) / 0.5);
        ctx.drawImage(S.img, sx, sy, sw, sh, p.x - S.ox * p.s, p.y - S.oy * p.s, sw * p.s, sh * p.s);
      }
      ctx.restore();
    },
    reset() { list.length = 0; },
  };
}
const HitSplash = Splashes();      // 白娘子水柱打中男生：main.js 在特效层画


const Sea = (() => {
  const SEA_TOP = 1190;      // 三层贴图的 y 以这里为 0（远层浪尖 ≈ 1203，两人脚底 GROUND 1195）
  const RISE = 1.2, FALL = 1.6;   // 涨满、退干各几秒
  /* 三层（远 → 近），贴图 v14/sea2/make.py 出（尺寸是它打印的；已按屏幕大小缩好，引擎不再缩放）：
     y：贴图上沿在 SEA_TOP 下多少；v：平移速度（像素/秒，正 = 往右），相邻两层反向、越近越快（远近错开，不是整块挪）；
     swell：一道道涌浪从画面里走过去 [起伏幅度 A（像素）, 涌浪长 L（像素）, 走速 c（像素/秒）]，按列算（每 SL 像素一条竖条）；
     bob：整层上下晃 [幅度, 角频率]。
     直播画面下半截压着礼物面板（画布 y ≈ 1373 以下看不见）：三层浪尖都摆在面板之上 —— 远 ≈ 1203~1261、中 ≈ 1242~1328、近 ≈ 1312~1399。 */
  const LAYERS = [
    { src: 'assets/world/sea2_far.webp',  w: 536, h: 276, y: 0,   v: -14, swell: [4, 520, 30],  bob: [2, 0.9] },
    { src: 'assets/world/sea2_mid.webp',  w: 696, h: 356, y: 52,  v: 26,  swell: [7, 640, -45], bob: [3, 1.1] },
    { src: 'assets/world/sea2_near.webp', w: 884, h: 439, y: 112, v: -44, swell: [10, 780, 70], bob: [4, 1.3] },
  ];
  const SL = 8;              // 按列起伏的竖条宽（像素）：相邻两条的高差 ≤ A·2π/L·SL ≈ 0.65 像素，看不出台阶
  const LIP = 10;            // 量浪上沿：从上往下第一个"下面连着 LIP 个不透明像素"的点（浪尖上方飞着的水沫不算）
  /* 飞沫：浪尖（这一层浪上沿最高的那四分之一）随机甩出的水点，软边白点，带重力落回去。中、近两层才甩（远层的太小看不见）。
     每颗画在它那层海之后、下一层之前（近层的飞沫盖住中层，不会反过来）。 */
  const SPRAY = { every: 0.035, crest: 0.25, V: [120, 260], spread: 1.1, G: 700, life: [0.45, 0.8], r: [2.5, 6], a: 0.85 };
  /* 虾兵蟹将：贴图（v14/sea/make.py，都朝右）、走速。row 0 泡在中层海里（画在远层之后、中层之前），row 1 泡在近层里。
     2026-09-28 用户："往上挪挪，但不要盖住男女生"：两排都摆在礼物面板之上；兵都画在人物之前的那一趟，蹦起来也只在人身后。
     缩放按透视：中层远（~0.75）、近层近（1.0）。 */
  const KINDS = [
    { src: 'assets/world/sea_shrimp1.webp', v: 60 }, { src: 'assets/world/sea_shrimp2.webp', v: 70 },
    { src: 'assets/world/sea_crab1.webp', v: 45 },   { src: 'assets/world/sea_crab2.webp', v: 50 },
  ];
  const MOBS = [            // 开场摆好的位置（x 占屏宽的几成）、哪一排、第几种、缩放
    { x: 0.08, row: 0, k: 2, s: 0.75 }, { x: 0.42, row: 0, k: 0, s: 0.75 }, { x: 0.76, row: 0, k: 3, s: 0.75 },
    { x: 0.22, row: 1, k: 1, s: 1.0 }, { x: 0.58, row: 1, k: 2, s: 1.0 }, { x: 0.92, row: 1, k: 0, s: 1.0 },
  ];
  const SINK = 0.3;               // 泡在水里：贴图下沿压到浪上沿以下 30% 的高度（被那一层海盖住）
  const HOP = { every: [2.2, 4.0], T: 0.7, h: 70, splash: 16 };   // 蹦出水面：隔多久一次、在空中多久、多高、落水溅几颗飞沫

  let W = 960, H = 1707;
  let lv = 0, t = 0, imgs = [], mobs = [], hopT = 3, sprays = [], sprayT = 0, dot = null;

  function init(w, h) { W = w; H = h; reset(); }

  /* 贴图 → 横向多接 SL 像素的画布（竖条取到末尾不用拆两段）、每列浪上沿 top、浪尖门槛 crest（上沿最高那 SPRAY.crest 的分位） */
  function prep(L, im) {
    const c = document.createElement('canvas');
    c.width = L.w + SL + 1; c.height = L.h;
    const g = c.getContext('2d', { willReadFrequently: true });
    g.drawImage(im, 0, 0); g.drawImage(im, L.w, 0);
    const d = g.getImageData(0, 0, L.w, L.h).data, top = new Float32Array(L.w);
    for (let x = 0; x < L.w; x++) {
      let run = 0, y = 0;
      for (; y < L.h && run < LIP; y++) run = d[(y * L.w + x) * 4 + 3] > 128 ? run + 1 : 0;
      top[x] = y - LIP;
    }
    const sm = top.map((_, x) => { let s = 0; for (let k = -4; k <= 4; k++) s += top[(x + k + L.w) % L.w]; return s / 9; });   // 抹平一点：兵不跟着浪尖上的碎沫一抖一抖
    L.ext = c; L.top = sm;
    L.crest = [...sm].sort((a, b) => a - b)[Math.floor(L.w * SPRAY.crest)];
  }

  function load(v, off) {
    if (off) return Promise.resolve(false);
    const img = (src) => new Promise((ok) => {
      const i = new Image();
      i.onload = () => ok(i); i.onerror = () => ok(null);
      i.src = src + (v ? '?v=' + encodeURIComponent(v) : '');
    });
    /* 飞沫的软边白点：画一次，之后按大小缩放贴 */
    dot = document.createElement('canvas'); dot.width = dot.height = 32;
    const g = dot.getContext('2d'), rg = g.createRadialGradient(16, 16, 0, 16, 16, 16);
    rg.addColorStop(0, 'rgba(255,255,255,1)'); rg.addColorStop(0.45, 'rgba(235,248,255,0.85)'); rg.addColorStop(1, 'rgba(200,232,255,0)');
    g.fillStyle = rg; g.fillRect(0, 0, 32, 32);
    return Promise.all([
      Promise.all(LAYERS.map(L => img(L.src).then(i => { if (i) prep(L, i); return !!i; }))),
      Promise.all(KINDS.map(K => img(K.src))).then(r => { imgs = r; return r.every(Boolean); }),
    ]).then(([a, b]) => a.every(Boolean) && b);
  }

  function reset() {
    lv = 0; t = 0; hopT = 3; sprays = []; sprayT = 0;
    mobs = MOBS.map(m => ({ ...m, x: m.x * W, ph: Math.random() * 6, hop: -1 }));
  }

  /* 水位：lv 0~1，按缓动映射成整片海往下沉多少（没涨满时整片在屏幕下沿以下） */
  const ease = (u) => u * u * (3 - 2 * u);
  const sinkOf = () => (1 - ease(lv)) * (H - SEA_TOP + 40);
  const mod = (a, n) => ((a % n) + n) % n;
  /* 第 k 层贴图上沿在屏幕 x 处的 y（不含浪形，只含整层位置 + 起伏） */
  function baseY(k, x) {
    const L = LAYERS[k];
    return SEA_TOP + L.y + sinkOf() + L.bob[0] * Math.sin(t * L.bob[1] + k * 1.7)
      + L.swell[0] * Math.sin(6.2832 * (x - L.swell[2] * t) / L.swell[1]);
  }
  /* 第 k 层在屏幕 x 处的浪上沿（屏幕 y） */
  function surfY(k, x) {
    const L = LAYERS[k];
    return baseY(k, x) + L.top[Math.floor(mod(x - L.v * t, L.w))];
  }

  function spray(k, x, y, n, up) {
    for (let i = 0; i < n; i++) {
      const a = -Math.PI / 2 + (Math.random() - 0.5) * SPRAY.spread * (up ? 1.6 : 1) + (up ? 0 : Math.sign(LAYERS[k].v) * 0.35);
      const v = SPRAY.V[0] + Math.random() * (SPRAY.V[1] - SPRAY.V[0]);
      sprays.push({ k, x, y, vx: Math.cos(a) * v + LAYERS[k].v, vy: Math.sin(a) * v, t: 0,
                    life: SPRAY.life[0] + Math.random() * (SPRAY.life[1] - SPRAY.life[0]),
                    r: (SPRAY.r[0] + Math.random() * (SPRAY.r[1] - SPRAY.r[0])) * (k === 1 ? 0.8 : 1) });
    }
  }

  function update(dt, on) {
    lv = Math.max(0, Math.min(1, lv + (on ? dt / RISE : -dt / FALL)));
    for (let i = sprays.length - 1; i >= 0; i--) {
      const p = sprays[i];
      p.vy += SPRAY.G * dt; p.x += p.vx * dt; p.y += p.vy * dt;
      if ((p.t += dt) > p.life) sprays.splice(i, 1);
    }
    if (lv <= 0) return;
    t += dt;
    if (!LAYERS[2].top) return;
    /* 虾兵蟹将往右冲，出了右边从左边再进来；隔几秒挑一只蹦出水面，落回去溅一圈飞沫 */
    for (const m of mobs) {
      m.x += KINDS[m.k].v * m.s * dt;
      const w = imgs[m.k] ? imgs[m.k].width * m.s : 150;
      if (m.x - w / 2 > W) m.x = -w / 2;
      if (m.hop >= 0 && (m.hop += dt) > HOP.T) { m.hop = -1; spray(m.row + 1, m.x, surfY(m.row + 1, m.x), HOP.splash, true); }
    }
    if (on && (hopT -= dt) <= 0) {
      const idle = mobs.filter(m => m.hop < 0 && m.x > 40 && m.x < W - 40);
      if (idle.length) idle[Math.floor(Math.random() * idle.length)].hop = 0;
      hopT = HOP.every[0] + Math.random() * (HOP.every[1] - HOP.every[0]);
    }
    /* 浪尖飞沫：随机挑中 / 近层、一个 x，那里的浪上沿够高（贴图里最高那四分之一）才甩；退潮时不甩 */
    if (on) for (sprayT += dt; sprayT >= SPRAY.every; sprayT -= SPRAY.every) {
      const k = 1 + (Math.random() < 0.6 ? 1 : 0), L = LAYERS[k], x = Math.random() * W;
      if (L.top[Math.floor(mod(x - L.v * t, L.w))] <= L.crest) spray(k, x, surfY(k, x) + 4, 1 + (Math.random() < 0.4 ? 1 : 0), false);
    }
  }

  function drawLayer(ctx, k) {
    const L = LAYERS[k];
    if (!L.ext || baseY(k, 0) - 20 > H) return;
    const off = mod(-L.v * t, L.w), fx = off - Math.floor(off);   // 屏幕 x 处取贴图第 (x + off) 列；整数列取、小数部分挪到落点上
    for (let x = 0; x < W + SL; x += SL) {
      const u = Math.floor(mod(x + off, L.w));
      ctx.drawImage(L.ext, u, 0, SL + 1, L.h, x - fx, baseY(k, x + SL / 2), SL + 1, L.h);   // 多画 1 像素：竖条之间不漏缝
    }
  }

  function drawSprays(ctx, k, a) {
    for (const p of sprays) {
      if (p.k !== k) continue;
      const u = p.t / p.life;
      ctx.globalAlpha = a * SPRAY.a * (u < 0.15 ? u / 0.15 : 1 - (u - 0.15) / 0.85);
      const r = p.r * (1 + 0.6 * u);                 // 越飞越散
      ctx.drawImage(dot, p.x - r, p.y - r, 2 * r, 2 * r);
    }
  }

  function drawMob(ctx, m) {
    const im = imgs[m.k];
    if (!im) return;
    const w = im.width * m.s, h = im.height * m.s, k = m.row + 1;
    const wy = surfY(k, m.x), slope = (surfY(k, m.x + 18) - surfY(k, m.x - 18)) / 36;
    let y = wy + h * SINK + Math.sin(t * 3 + m.ph) * 3, rot = Math.atan(slope) * 0.6;
    if (m.hop >= 0) {                                 // 蹦出水面：抛物线，空中打个前滚半圈
      const u = m.hop / HOP.T;
      y -= HOP.h * 4 * u * (1 - u);
      rot += Math.sin(u * Math.PI) * 0.5;
    }
    ctx.save(); ctx.translate(m.x, y); ctx.rotate(rot);
    ctx.drawImage(im, -w / 2, -h, w, h);
    ctx.restore();
  }

  function draw(ctx) {
    if (!LAYERS[2].top || (lv <= 0 && !sprays.length)) return;
    const a = Math.min(1, lv * 1.6);                 // 退潮后段整片淡掉（涨潮时很快不透明）
    ctx.save();
    for (let k = 0; k < 3; k++) {
      ctx.globalAlpha = a;
      if (lv > 0) drawLayer(ctx, k);
      drawSprays(ctx, k, 1);
      ctx.globalAlpha = a;
      if (k < 2 && lv > 0) for (const m of mobs) if (m.row === k) drawMob(ctx, m);
    }
    ctx.restore();
  }

  const active = () => lv > 0;
  return { init, load, update, draw, reset, active };
})();
