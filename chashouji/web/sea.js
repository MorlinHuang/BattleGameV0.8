/* sea.js —— 白娘子的水法术：整个屏幕底部涌起海水（2026-09-28）。
 * 用户："整个屏幕的底部，从下边缘到男女生下方，用海水汹涌填充（代表白娘子的水法术），海水也需要持续的动画，
 *        海里可以有些虾兵蟹将。白娘子持续 15s，海水也一样。当白娘子消失的时候，海水也消散。"
 *
 * 跟着她走，不自己计时：main.js 每帧告诉 update 她在不在施法（on）。在 → 水位 lv 从 0 涨到 1（RISE 秒，从屏幕下沿涌上来）；
 * 不在（飞走了）→ 退回 0（FALL 秒：往下沉、越沉越透、浪头的白沫先散）。续送她多待一段，海水也就多待一段。
 *
 * 画法（从远到近，都在 draw 里现算，没有贴图）：
 *   几层浪（LAYERS），每层上沿是两个正弦叠出来的尖顶浪 —— 浪尖削尖、浪谷拉平，读成"汹涌"而不是水波纹；
 *   越靠前越深、浪越高、走得越快，相邻两层往相反方向走（远近错开，不是整块平移）；
 *   每层浪尖一条断断续续的白沫线 + 浪身上几道横的高光；浪尖高过一定程度就甩出水花（sprays）。
 *   虾兵蟹将（MOBS）夹在浪层之间：跟着所在那层的浪上下起伏、按浪的坡度歪，下半截被前一层浪盖住（像泡在水里）；
 *   一律朝右冲（冲着男生那边：她的兵），出了右边从左边再进来；隔几秒有一只蹦出水面、落回去溅一圈水。
 *
 * 层级：main.js 画在人物之前（最底下、背景之上）—— 海面顶到男女生脚下（TOP），不盖人；
 * 档 4 出场压暗照样压它（只有白娘子本人是亮的）。
 * 配色按明亮底图：水身不透明的饱和蓝（半透明的浅蓝在米色地板上是一片灰），浪尖白沫带深蓝托底。
 */
'use strict';

const Sea = (() => {
  const TOP = 1222;          // 海面（第一层浪的平均高度）：男女生脚底（GROUND 1195）往下一点 —— 浪尖顶到脚下，不淹脚。
                             // 第一版 1272：脚下空出 80 像素地板，读成"海在远处"不是"涌到脚下"
  const RISE = 1.2, FALL = 1.6;   // 涨满、退干各几秒
  /* 浪层（远 → 近）：y 相对 TOP 的平均高度、浪高 A、波长 L、走速 v（像素/秒，正 = 往右）、颜色 [上, 下]、白沫线宽 */
  /* 第一版浪高 10~28、相邻层颜色只差一点：整片读成一块平的蓝布，白沫是飘在上面的细线。
     现在浪高翻倍、相邻层明暗拉开（远的浅青、近的深蓝），每层上沿一道亮边、浪尖一顶按高度变粗的白沫帽。 */
  const LAYERS = [
    { y: 0,   A: 18, L: 280, v: -50, col: [[132, 206, 246], [88, 166, 232]],  foam: 7 },
    { y: 75,  A: 28, L: 360, v: 80,  col: [[74, 152, 232], [42, 112, 206]],   foam: 9 },
    { y: 180, A: 36, L: 440, v: -110, col: [[38, 102, 206], [22, 70, 172]],   foam: 11 },
    { y: 320, A: 44, L: 540, v: 150, col: [[22, 64, 162], [10, 36, 112]],     foam: 13 },
  ];
  const SURGE = [0.3, 0.7];       // 浪高随时间涨落：± 几成、角频率（一阵大一阵小，"汹涌"不是匀速的正弦）
  const INK = [16, 50, 120];      // 白沫、水花的深蓝托底
  const SWELL = [7, 1.1];         // 整层随涌浪上下起伏 [幅度, 角频率]
  const SPRAY = { every: 0.07, crest: 0.8, V: [180, 320], G: 900, life: 0.7, r: [3, 7] };   // 浪尖水花：多久一颗、浪尖高过几成才甩、初速、重力、寿命、颗粒半径
  /* 虾兵蟹将：贴图（v14/sea/make.py，都朝右）、走速。MOBS 的 row = 画在第几层浪之后：它泡在下一层浪（row + 1）里，
     跟着那一层的浪线起伏、下半截被那一层盖住 —— 按自己这层的浪线摆的话，下半截画在水面上，读成站在水上。 */
  const KINDS = [
    { src: 'assets/world/sea_shrimp1.webp', v: 60 }, { src: 'assets/world/sea_shrimp2.webp', v: 70 },
    { src: 'assets/world/sea_crab1.webp', v: 45 },   { src: 'assets/world/sea_crab2.webp', v: 50 },
  ];
  const MOBS = [            // 开场摆好的位置（x 占屏宽的几成）、哪一行、第几种、缩放
    { x: 0.08, row: 1, k: 2, s: 0.95 }, { x: 0.42, row: 1, k: 0, s: 0.95 }, { x: 0.76, row: 1, k: 3, s: 0.95 },
    { x: 0.22, row: 2, k: 1, s: 1.2 }, { x: 0.58, row: 2, k: 2, s: 1.2 }, { x: 0.92, row: 2, k: 0, s: 1.2 },
  ];
  const SINK = 0.3;               // 泡在水里：贴图下沿压到浪线以下 30% 的高度（被前一层浪盖住）
  const HOP = { every: [2.2, 4.0], T: 0.75, h: 110 };   // 蹦出水面：隔多久一次、在空中多久、多高

  let W = 960, H = 1707;
  let lv = 0, t = 0, imgs = [], mobs = [], sprays = [], sprayT = 0, hopT = 3;

  function init(w, h) { W = w; H = h; reset(); }

  function load(v, off) {
    if (off) return Promise.resolve(false);
    return Promise.all(KINDS.map(K => new Promise((ok) => {
      const i = new Image();
      i.onload = () => ok(i); i.onerror = () => ok(null);
      i.src = K.src + (v ? '?v=' + encodeURIComponent(v) : '');
    }))).then(r => { imgs = r; return r.every(Boolean); });
  }

  function reset() {
    lv = 0; t = 0; sprays = []; sprayT = 0; hopT = 3;
    mobs = MOBS.map(m => ({ ...m, x: m.x * W, ph: Math.random() * 6, hop: -1 }));
  }

  /* 水位：lv 0~1，按缓动映射成整片海往下沉多少（没涨满时整片在屏幕下沿以下） */
  const ease = (u) => u * u * (3 - 2 * u);
  const sinkOf = () => (1 - ease(lv)) * (H - TOP + 60);

  /* 第 i 层浪在 x 处的上沿 y（屏幕像素）。尖顶浪：两个正弦叠加后按 |·|^1.5 把正半周削尖、负半周拉平 */
  function waveY(i, x) {
    const Lr = LAYERS[i], k = 6.2832 / Lr.L;
    const a = Math.sin(k * (x - Lr.v * t) + i * 1.7), b = Math.sin(k * 2.3 * (x + Lr.v * 0.6 * t) + i * 0.9);
    const w = 0.7 * a + 0.3 * b, crest = w > 0 ? Math.pow(w, 1.8) : w * 0.4;
    const A = Lr.A * (1 + SURGE[0] * Math.sin(t * SURGE[1] + i * 2.1 + x * 0.004));
    return TOP + Lr.y - A * lv * crest * 2 + Math.sin(t * SWELL[1] + i * 1.3) * SWELL[0] + sinkOf();
  }

  function update(dt, on) {
    lv = Math.max(0, Math.min(1, lv + (on ? dt / RISE : -dt / FALL)));
    if (lv <= 0) { if (sprays.length) sprays = []; return; }
    t += dt;
    /* 虾兵蟹将往右冲，出了右边从左边再进来；隔几秒挑一只蹦出水面 */
    for (const m of mobs) {
      m.x += KINDS[m.k].v * m.s * dt;
      const w = imgs[m.k] ? imgs[m.k].width * m.s : 150;
      if (m.x - w / 2 > W) m.x = -w / 2;
      if (m.hop >= 0 && (m.hop += dt) > HOP.T) { m.hop = -1; splash(m.x, waveY(m.row + 1, m.x), 10); }
    }
    if (on && (hopT -= dt) <= 0) {
      const idle = mobs.filter(m => m.hop < 0 && m.x > 40 && m.x < W - 40);
      if (idle.length) idle[Math.floor(Math.random() * idle.length)].hop = 0;
      hopT = HOP.every[0] + Math.random() * (HOP.every[1] - HOP.every[0]);
    }
    /* 浪尖水花：随机挑一层、一个 x，浪尖够高就甩一颗（退潮时不甩） */
    if (on) for (sprayT += dt; sprayT >= SPRAY.every; sprayT -= SPRAY.every) {
      const i = 1 + Math.floor(Math.random() * (LAYERS.length - 1)), x = Math.random() * W, y = waveY(i, x);
      if (TOP + LAYERS[i].y + sinkOf() - y > LAYERS[i].A * SPRAY.crest * 2) splash(x, y, 1);
    }
    for (let i = sprays.length - 1; i >= 0; i--) {
      const p = sprays[i];
      p.vy += SPRAY.G * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.t += dt;
      if (p.t > SPRAY.life) sprays.splice(i, 1);
    }
  }

  function splash(x, y, n) {
    for (let k = 0; k < n; k++) {
      const a = -Math.PI / 2 + (Math.random() - 0.5) * 1.4, v = SPRAY.V[0] + Math.random() * (SPRAY.V[1] - SPRAY.V[0]);
      sprays.push({ x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, t: 0, r: SPRAY.r[0] + Math.random() * (SPRAY.r[1] - SPRAY.r[0]) });
    }
  }

  const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${a.toFixed(3)})`;
  const STEP = 16;                // 浪线每隔几像素取一个点

  function drawLayer(ctx, i, a) {
    const Lr = LAYERS[i], y0 = TOP + Lr.y + sinkOf();
    if (y0 - Lr.A * 2 > H) return;
    const pts = [];
    for (let x = -STEP; x <= W + STEP; x += STEP) pts.push([x, waveY(i, x)]);
    /* 水身：上沿浪线 → 屏幕下沿，竖直渐变 */
    const g = ctx.createLinearGradient(0, y0 - Lr.A * 2, 0, y0 + 220);
    g.addColorStop(0, rgba(Lr.col[0], a)); g.addColorStop(1, rgba(Lr.col[1], a));
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.moveTo(pts[0][0], H + 10);
    for (const [x, y] of pts) ctx.lineTo(x, y);
    ctx.lineTo(pts[pts.length - 1][0], H + 10); ctx.closePath(); ctx.fill();
    /* 上沿亮边：浪线往下一道宽的浅色带（水面反光），让每层浪的轮廓从后一层里跳出来 */
    const hi = Lr.col[0].map(c => Math.round(c + (255 - c) * 0.45));
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    ctx.lineWidth = 12; ctx.strokeStyle = rgba(hi, 0.8 * a);
    ctx.beginPath(); pts.forEach(([x, y], n) => n ? ctx.lineTo(x, y + 7) : ctx.moveTo(x, y + 7)); ctx.stroke();
    /* 浪身上的横高光：几道短白线，跟着这层的走速漂 */
    ctx.lineWidth = 3; ctx.strokeStyle = rgba([220, 240, 255], 0.4 * a);
    ctx.beginPath();
    for (let j = 0; j < 7; j++) {
      const x = ((j * 157 + i * 71 + Lr.v * t * 0.8) % (W + 120) + W + 120) % (W + 120) - 60, y = waveY(i, x) + 30 + ((j * 37) % 60);
      const len = 26 + (j * 13) % 30;
      ctx.moveTo(x, y); ctx.lineTo(x + len, y);
    }
    ctx.stroke();
    /* 浪尖白沫帽：只在高过平均线的那几段描，越靠浪尖越粗（lw = foam × (0.4 + 1.2·high)）—— 读成浪头翻起的白沫，不是一根白线。
       先描深蓝托底再描白。退潮时先散（× lv²） */
    const fa = a * lv * lv;
    if (fa < 0.02) return;
    const segs = [];
    for (let n = 1; n < pts.length; n++) {
      const [x0, yA] = pts[n - 1], [x1, yB] = pts[n];
      const high = (y0 + Math.sin(t * SWELL[1] + i * 1.3) * SWELL[0] - (yA + yB) / 2) / (Lr.A * 2 * lv + 1e-3);   // 这一段多靠近浪尖（0 平均线 … 1 浪尖）
      if (high > 0.08) segs.push([x0, yA, x1, yB, Math.min(1, high)]);
    }
    for (const [pad, c, al] of [[4, INK, 0.45], [0, [255, 255, 255], 0.95]]) {
      ctx.strokeStyle = rgba(c, al * fa);
      for (const [x0, yA, x1, yB, h] of segs) {
        ctx.lineWidth = Lr.foam * (0.4 + 1.2 * h) + pad;
        ctx.beginPath(); ctx.moveTo(x0, yA + 2); ctx.lineTo(x1, yB + 2); ctx.stroke();
      }
    }
    /* 浪头后面拖的碎沫：浪尖以下几颗小白点，跟着浪走 */
    ctx.fillStyle = rgba([255, 255, 255], 0.8 * fa);
    for (const [x0, yA, , , h] of segs) {
      if (h < 0.5) continue;
      const q = Math.sin(x0 * 12.9898 + i * 78.233) * 43758.5453, j = q - Math.floor(q);
      ctx.beginPath(); ctx.arc(x0 + j * STEP, yA + 14 + j * 16, 2 + j * 3, 0, 6.283); ctx.fill();
    }
  }

  function drawMob(ctx, m) {
    const im = imgs[m.k];
    if (!im) return;
    const w = im.width * m.s, h = im.height * m.s;
    const L = m.row + 1, wy = waveY(L, m.x), slope = (waveY(L, m.x + 12) - waveY(L, m.x - 12)) / 24;
    let y = wy + h * SINK + Math.sin(t * 3 + m.ph) * 4, rot = Math.atan(slope) * 0.8;
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
    if (lv <= 0) return;
    const a = Math.min(1, lv * 1.6);                 // 退潮后段整片淡掉（涨潮时很快不透明）
    ctx.save();
    for (let i = 0; i < LAYERS.length; i++) {
      drawLayer(ctx, i, a);
      ctx.globalAlpha = a;
      for (const m of mobs) if (m.row === i) drawMob(ctx, m);   // 这一行的兵画在这层浪之后、下一层浪之前：下半截被下一层盖住
      ctx.globalAlpha = 1;
    }
    for (const p of sprays) {
      const k = 1 - p.t / SPRAY.life;
      ctx.fillStyle = rgba(INK, 0.5 * k * a); ctx.beginPath(); ctx.arc(p.x, p.y, p.r + 2, 0, 6.283); ctx.fill();
      ctx.fillStyle = rgba([240, 250, 255], 0.95 * k * a); ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.283); ctx.fill();
    }
    ctx.restore();
  }

  const active = () => lv > 0;
  return { init, load, update, draw, reset, active };
})();
