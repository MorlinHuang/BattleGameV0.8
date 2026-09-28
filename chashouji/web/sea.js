/* sea.js —— 白娘子的水（2026-09-28）：底部海水 Sea、水花 Splashes、以及三套 3D 序列帧贴图 WaterArt（掌心水柱在 crew.js drawJet 里画）。
 * 用户："整个屏幕的底部，从下边缘到男女生下方，用海水汹涌填充（代表白娘子的水法术），海水也需要持续的动画，
 *        海里可以有些虾兵蟹将。白娘子持续 15s，海水也一样。当白娘子消失的时候，海水也消散。"
 * 第二版（同日）用户："水流和海面美术风格实在是太 Q 了，需要更写实，参考之前的花束等礼物，做出类似 3 渲 2 的体积感"。
 * 第一版海面是 canvas 现画的四条正弦色带 + 白线；现在三样水全是 Blender 渲的 3 渲 2 序列帧（tools/3d/water/：
 * sea.py 周期 Gerstner 海面、jet.py 掌心水柱、splash.py 水花；打包 pack_water.py，下面的数照它打印的填）。
 *
 * 海：跟着她走，不自己计时 —— main.js 每帧告诉 update 她在不在施法（on）。在 → 水位 lv 从 0 涨到 1（RISE 秒，整片从屏幕下沿涌上来）；
 * 不在（飞走了）→ 退回 0（FALL 秒：往下沉、越沉越透）。续送她多待一段，海水也就多待一段。
 * 海面按远近渲成三层（SEA.bands），按 远 → 第一排虾兵蟹将 → 中 → 第二排 → 近 叠：兵的下半截被它前面那层海盖住，泡在水里。
 * 兵跟着前面那层海的浪上沿起伏、按坡度歪 —— 浪上沿是加载时从每一帧贴图里量出来的（heights）。
 * 帧与帧之间交叉淡化（36 帧 / 3 秒 = 12 帧每秒，不淡化看得出一跳一跳）。
 *
 * 层级：main.js 画在人物之前（最底下、背景之上）—— 海面顶到男女生脚下，不盖人；档 4 出场压暗照样压它（只有白娘子本人是亮的）。
 */
'use strict';

/* 三套贴图的参数（pack_water.py 打印的，重渲后重填）。
   sea：36 帧、6 列，存成 0.6 倍（全尺寸解码 ~120MB 手机扛不住），画的时候放大回 960 宽；top = 这一层在渲染图里的上沿 y。
   jet：16 帧、4 列，x0 = 掌心在格子里的 x、cy = 中轴的 y；loop = 引擎里多少秒转一圈（jet.py 按整周期渲，首尾相接）。
   splash：10 帧、5 列，(ox, oy) = 撞击点在格子里的位置；life = 播一遍多少秒。 */
const WaterArt = {
  sea: { n: 36, cols: 6, scale: 0.6, loop: 3.0,
         bands: [{ src: 'assets/fx/sea_far.webp', w: 576, h: 143, top: 9 },
                 { src: 'assets/fx/sea_mid.webp', w: 576, h: 220, top: 72 },
                 { src: 'assets/fx/sea_near.webp', w: 576, h: 230, top: 137 }] },
  jet: { src: 'assets/fx/jet.webp', n: 16, cols: 4, w: 712, h: 171, x0: 4, cy: 92, loop: 0.5 },
  splash: { src: 'assets/fx/splash.webp', n: 10, cols: 5, w: 320, h: 239, ox: 160, oy: 151, life: 0.45 },
  load(v, off) {
    if (off) return Promise.resolve(false);
    const one = (o) => new Promise((ok) => {
      const i = new Image();
      i.onload = () => { o.img = i; ok(true); }; i.onerror = () => ok(false);
      i.src = o.src + (v ? '?v=' + encodeURIComponent(v) : '');
    });
    return Promise.all([...this.sea.bands.map(one), one(this.jet), one(this.splash)]).then(r => r.every(Boolean));
  },
};
/* 图集里第 i 帧的源矩形 [sx, sy, sw, sh] */
const atlasCell = (A, o, i) => [(i % A.cols) * o.w, ((i / A.cols) | 0) * o.h, o.w, o.h];

/* 水花：一朵 3D 水冠在 (x, y) 播一遍（WaterArt.splash），s = 缩放。白娘子打中男生（main.js）、虾兵蟹将落回水里（Sea）各用一份。 */
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
  const SEA_TOP = 1190;      // 渲染图第 0 行摆在屏幕哪（最远的浪尖 top 9 → 1199，正好到两人脚底 GROUND 1195）
  const RISE = 1.2, FALL = 1.6;   // 涨满、退干各几秒
  /* 虾兵蟹将：贴图（v14/sea/make.py，都朝右）、走速。row 0 泡在中层海里（画在远层之后、中层之前），row 1 泡在近层里。
     2026-09-28 用户："往上挪挪，但不要盖住男女生"：直播画面下半截压着礼物面板（画布 y ≈ 1373 以下看不见），
     两排都摆在面板之上 —— 中层浪上沿 ≈ 1270~1300、近层 ≈ 1330~1370。兵都画在人物之前的那一趟，蹦起来也只在人身后。
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
  const HOP = { every: [2.2, 4.0], T: 0.7, h: 70, splash: 0.45 };   // 蹦出水面：隔多久一次、在空中多久、多高、落水水花多大

  let W = 960, H = 1707;
  let lv = 0, t = 0, imgs = [], mobs = [], hopT = 3, heights = null;
  const drops = Splashes();

  function init(w, h) { W = w; H = h; reset(); }

  /* 每层每帧每一列浪的上沿（格子像素，-1 = 这一列没有水）：从贴图 alpha 量。中、近两层要（兵泡在它们里面） */
  function measure(o) {
    const A = WaterArt.sea, c = document.createElement('canvas');
    c.width = o.img.width; c.height = o.img.height;
    const g = c.getContext('2d', { willReadFrequently: true });
    g.drawImage(o.img, 0, 0);
    const d = g.getImageData(0, 0, c.width, c.height).data, out = [];
    for (let i = 0; i < A.n; i++) {
      const [sx, sy] = atlasCell(A, o, i), col = new Int16Array(o.w).fill(-1);
      for (let x = 0; x < o.w; x++)
        for (let y = 0; y < o.h; y++) if (d[((sy + y) * c.width + sx + x) * 4 + 3] > 128) { col[x] = y; break; }
      out.push(col);
    }
    return out;
  }

  function load(v, off) {
    if (off) return Promise.resolve(false);
    const mob = Promise.all(KINDS.map(K => new Promise((ok) => {
      const i = new Image();
      i.onload = () => ok(i); i.onerror = () => ok(null);
      i.src = K.src + (v ? '?v=' + encodeURIComponent(v) : '');
    }))).then(r => { imgs = r; return r.every(Boolean); });
    /* WaterArt 由 main.js 另外加载（水柱、水花也要用），这里等它好了量浪上沿 */
    return mob;
  }
  function ready() {
    const B = WaterArt.sea.bands;
    if (!heights && B[1].img && B[2].img) heights = [measure(B[1]), measure(B[2])];
  }

  function reset() {
    lv = 0; t = 0; hopT = 3; drops.reset();
    mobs = MOBS.map(m => ({ ...m, x: m.x * W, ph: Math.random() * 6, hop: -1 }));
  }

  /* 水位：lv 0~1，按缓动映射成整片海往下沉多少（没涨满时整片在屏幕下沿以下） */
  const ease = (u) => u * u * (3 - 2 * u);
  const sinkOf = () => (1 - ease(lv)) * (H - SEA_TOP + 40);
  const frameOf = () => { const A = WaterArt.sea, f = (t / A.loop % 1) * A.n; return [Math.floor(f) % A.n, f - Math.floor(f)]; };

  /* 第 row 排兵所在那层海（中 / 近）在屏幕 x 处的浪上沿（屏幕 y），两帧之间插值 */
  function surfY(row, x) {
    const A = WaterArt.sea, o = A.bands[row + 1], [i, a] = frameOf();
    const cx = Math.max(0, Math.min(o.w - 1, Math.round(x * A.scale)));
    const h0 = heights[row][i][cx], h1 = heights[row][(i + 1) % A.n][cx];
    const h = h0 < 0 ? h1 : h1 < 0 ? h0 : h0 + (h1 - h0) * a;
    return SEA_TOP + o.top + Math.max(0, h) / A.scale + sinkOf();
  }

  function update(dt, on) {
    lv = Math.max(0, Math.min(1, lv + (on ? dt / RISE : -dt / FALL)));
    drops.update(dt);
    if (lv <= 0) return;
    t += dt;
    ready();
    if (!heights) return;
    /* 虾兵蟹将往右冲，出了右边从左边再进来；隔几秒挑一只蹦出水面，落回去溅一朵水花 */
    for (const m of mobs) {
      m.x += KINDS[m.k].v * m.s * dt;
      const w = imgs[m.k] ? imgs[m.k].width * m.s : 150;
      if (m.x - w / 2 > W) m.x = -w / 2;
      if (m.hop >= 0 && (m.hop += dt) > HOP.T) { m.hop = -1; drops.spawn(m.x, surfY(m.row, m.x), HOP.splash * m.s); }
    }
    if (on && (hopT -= dt) <= 0) {
      const idle = mobs.filter(m => m.hop < 0 && m.x > 40 && m.x < W - 40);
      if (idle.length) idle[Math.floor(Math.random() * idle.length)].hop = 0;
      hopT = HOP.every[0] + Math.random() * (HOP.every[1] - HOP.every[0]);
    }
  }

  function drawBand(ctx, k, a) {
    const A = WaterArt.sea, o = A.bands[k];
    if (!o.img) return;
    const [i, f] = frameOf(), y = SEA_TOP + o.top + sinkOf(), dh = o.h / A.scale;
    if (y > H) return;
    const put = (j, al) => { const [sx, sy, sw, sh] = atlasCell(A, o, j); ctx.globalAlpha = al; ctx.drawImage(o.img, sx, sy, sw, sh, 0, y, W, dh); };
    put(i, a);
    if (f > 0.02) put((i + 1) % A.n, a * f);           // 下一帧叠上来：12 帧每秒不淡化看得出一跳一跳
  }

  function drawMob(ctx, m) {
    const im = imgs[m.k];
    if (!im) return;
    const w = im.width * m.s, h = im.height * m.s;
    const wy = surfY(m.row, m.x), slope = (surfY(m.row, m.x + 14) - surfY(m.row, m.x - 14)) / 28;
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
    if (lv <= 0 || !heights) return;
    const a = Math.min(1, lv * 1.6);                 // 退潮后段整片淡掉（涨潮时很快不透明）
    ctx.save();
    for (let k = 0; k < 3; k++) {
      drawBand(ctx, k, a);
      if (k < 2) { ctx.globalAlpha = a; for (const m of mobs) if (m.row === k) drawMob(ctx, m); }
    }
    ctx.restore();
    drops.draw(ctx, a);
  }

  const active = () => lv > 0;
  return { init, load, update, draw, reset, active };
})();
