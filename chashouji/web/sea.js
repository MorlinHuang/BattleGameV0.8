/* sea.js —— 档 4 两位神仙铺在屏幕底部的"法术潮"（2026-09-28）+ 白娘子的掌心水柱贴图 WaterArt、命中的爆水泡沫 Foam。
 *
 * 白娘子（女生侧）→ 海水 Sea。用户："整个屏幕的底部，从下边缘到男女生下方，用海水汹涌填充（代表白娘子的水法术），
 *   海水也需要持续的动画，海里可以有些虾兵蟹将。白娘子持续 15s，海水也一样。当白娘子消失的时候，海水也消散。"
 *   海面三版：① canvas 现画的正弦色带 —— "太 Q"；② Blender 3 渲 2 的 Gerstner 海面 —— "水波纹不适合做体积感，回到 2D 但不要太 Q，
 *   要写实"；③ 现在：手绘写实海浪（生图 → 抠像 → 横向无缝长条，v14/sea2/make.py），远 / 中 / 近三层。
 * 法海（男生侧）→ 金光经卷 Scroll。用户："同样也需要跟白娘子海面的动效，可能是在金光虚化的佛经卷轴，也会和海平面一样波动，
 *   虾兵蟹将可以对应神兽小佛"。三条金色《心经》卷轴（v14/scroll/make.py 程序画的，经文是真字）一层层起伏，
 *   底下一片金色光雾，卷轴上骑着神兽小佛（v14/scroll/beasts.py：小沙弥、麒麟崽、小石狮、小白象）。
 *
 * 两样是同一套东西（Tide）：三层横向无缝长条贴图，
 *   · 各层往相反方向平移（远慢近快，远近错开不是整块挪）；
 *   · 按列上下起伏（每 SL 像素一条竖条各自上下挪：一道道涌浪从画面里走过去，卷轴像绸带一样飘）；
 *   · 浪尖 / 卷轴上沿随机甩出东西（海：白色飞沫往上溅、落回去；经卷：金色光点往上飘）；
 *   · 小兵（虾兵蟹将 / 神兽小佛）夹在层与层之间：跟着它那一层的上沿起伏、按坡度歪，隔几秒蹦起来一次。
 *   上沿是加载时从贴图 alpha 量出来的（每列一个数），再加上当时的平移和起伏。
 * 跟着人走，不自己计时：main.js 每帧告诉 update 这个人在不在施法（on）。在 → 进度 lv 从 0 涨到 1（rise 秒），不在（飞走了）→ 退回 0（fall 秒）。
 * 续送多待一段，潮也就多待一段。
 * 进场是横着推进来的（2026-09-28 用户："水面和卷轴改成分别从左右进场，这样同时播放"）：海从左边屏幕外推进来、经卷从右边，
 *   lv 是推进了几成（main.js tideSpan 换成这一片占的 [x0, x1)），前沿一路甩飞沫 / 金光点（update 的 front）；退场原路退回去。
 *   第一版是整片从屏幕下沿涌上来，两片同时在场只能一起涨、一起落，看不出是两股法力各从一边压过来。
 * 两个人同时在场：各推到两边进度的分界（左海右经），交界处水花和金光对撞（Clash）。
 *
 * 层级（main.js renderActors）：画在男女主之上（用户："水面和卷轴是在男女主的上层"）—— 潮漫过两人的脚和小腿。
 * 层数不定（C.layers 远 → 近，最后一层最近、最低）：经卷为了铺满到屏幕下沿比海多两条。
 */
'use strict';

/* 掌心水柱的 3D 贴图（tools/3d/water/pack_water.py 打印的，重渲后重填）。
   16 帧、4 列，x0 = 掌心在格子里的 x、cy = 中轴的 y；loop = 引擎里多少秒转一圈（jet.py 按整周期渲，首尾相接）。 */
const WaterArt = {
  jet: { src: 'assets/fx/jet.webp', n: 16, cols: 4, w: 712, h: 171, x0: 4, cy: 92, loop: 0.5 },
  load(v, off) {
    if (off) return Promise.resolve(false);
    const o = this.jet;
    return new Promise((ok) => {
      const i = new Image();
      i.onload = () => { o.img = i; ok(true); }; i.onerror = () => ok(false);
      i.src = o.src + (v ? '?v=' + encodeURIComponent(v) : '');
    });
  },
};
/* 图集里第 i 帧的源矩形 [sx, sy, sw, sh] */
const atlasCell = (A, o, i) => [(i % A.cols) * o.w, ((i / A.cols) | 0) * o.h, o.w, o.h];

/* 软边圆点贴图（画一次，按大小缩放贴）：c0 芯、c1 中圈、c2 外沿（外沿 alpha 0） */
function softDot(c0, c1, c2) {
  const d = document.createElement('canvas'); d.width = d.height = 32;
  const g = d.getContext('2d'), rg = g.createRadialGradient(16, 16, 0, 16, 16, 16);
  rg.addColorStop(0, c0); rg.addColorStop(0.45, c1); rg.addColorStop(1, c2);
  g.fillStyle = rg; g.fillRect(0, 0, 32, 32);
  return d;
}

/* ---- 白娘子水柱打中男生：爆一团水泡沫（2026-09-28 第三版） ----
   用户："打中后的水花特效明显不合适，直接爆水泡沫就行"。第二版是 Blender 渲的 3D 水冠（一圈往上张的水膜 + 水指），
   放大后收成一圈带刺的环，像个救生圈；第一版是冷白闪 + 深蓝环 + 描边水珠（太 Q）。
   现在：一团往外炸开的泡泡（透明泡身、深蓝细边、左上一点高光，飞一会儿"啵"地胀一下破掉）+ 几团白色泡沫往外鼓 + 几颗水珠带重力落。
   泡泡边一律深蓝：浅蓝 / 白在浅绿墙上不描边就化掉（chashouji-fx 明亮底图配色）。
   spawn(x, y, s)：s = 力度（首击 2.8、之后 1；水滴一路打在身上 drip 走 bubble 零星冒几颗）。 */
const Foam = (() => {
  const B = { n: [6, 9], V: [120, 360], drag: 3.2, lift: 90, r: [4, 13], life: [0.45, 0.85], pop: 0.14,
              body: 'rgba(214,240,255,0.28)', rim: 'rgba(30,100,190,0.85)', hi: 'rgba(255,255,255,0.95)' };
  const P = { n: [3, 3], V: [40, 140], r: [10, 18], r1: 2.4, life: [0.35, 0.55] };    // 白泡沫团：往外鼓到 r1 倍、淡掉
  const D = { n: [4, 4], V: [220, 480], G: 1400, r: [2.5, 5], life: [0.35, 0.6] };   // 水珠
  const MAX = 420;               // 最多同时几颗（她每 0.3 秒一次命中，首击 s 2.8 一下出 ~60 颗）
  const list = [];
  let puff = null;
  const rnd = (a) => a[0] + Math.random() * (a[1] - a[0]);
  function add(o) { if (list.length < MAX) list.push(o); }
  function spray(kind, x, y, s, n, C) {
    for (let i = 0; i < n; i++) {
      const a = Math.random() * 6.283, v = rnd(C.V) * Math.sqrt(s);
      add({ kind, x: x + (Math.random() - 0.5) * 20 * s, y: y + (Math.random() - 0.5) * 20 * s, vx: Math.cos(a) * v, vy: Math.sin(a) * v - (kind === 'drop' ? 200 : 0),
            r: rnd(C.r) * (kind === 'drop' ? 1 : Math.sqrt(s)), t: 0, life: rnd(C.life) });
    }
  }
  return {
    spawn(x, y, s) {
      spray('bub', x, y, s, Math.round(B.n[0] + B.n[1] * s), B);
      spray('puff', x, y, s, Math.round(P.n[0] + P.n[1] * s), P);
      spray('drop', x, y, s, Math.round(D.n[0] + D.n[1] * s), D);
    },
    bubble(x, y) { spray('bub', x, y, 0.6, 1 + (Math.random() < 0.4 ? 1 : 0), B); },
    update(dt) {
      for (let i = list.length - 1; i >= 0; i--) {
        const p = list[i];
        if ((p.t += dt) >= p.life) { list.splice(i, 1); continue; }
        if (p.kind === 'drop') p.vy += D.G * dt;
        else { const k = Math.exp(-B.drag * dt); p.vx *= k; p.vy = p.vy * k - B.lift * dt; }   // 泡泡、泡沫：很快刹住、慢慢往上浮
        p.x += p.vx * dt; p.y += p.vy * dt;
      }
    },
    draw(ctx) {
      if (!list.length) return;
      if (!puff) puff = softDot('rgba(255,255,255,0.95)', 'rgba(232,246,255,0.8)', 'rgba(150,200,245,0)');
      ctx.save(); ctx.lineWidth = 1.8;
      for (const p of list) {
        const u = p.t / p.life;
        if (p.kind === 'puff') {
          const r = p.r * (1 + (P.r1 - 1) * Math.sqrt(u));
          ctx.globalAlpha = (1 - u) * 0.9; ctx.drawImage(puff, p.x - r, p.y - r, 2 * r, 2 * r);
        } else if (p.kind === 'drop') {
          ctx.globalAlpha = Math.min(1, (1 - u) * 3);
          ctx.fillStyle = 'rgba(150,212,255,1)'; ctx.strokeStyle = B.rim;
          ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.283); ctx.fill(); ctx.stroke();
        } else {
          /* 泡泡：最后 B.pop 的时间里胀大 1.5 倍、边变细变淡 —— "啵"地破掉 */
          const e = Math.max(0, (u - (1 - B.pop)) / B.pop), r = p.r * (Math.min(1, u * 6) * 0.4 + 0.6) * (1 + 0.5 * e);
          ctx.globalAlpha = 1 - e;
          ctx.fillStyle = B.body; ctx.strokeStyle = B.rim;
          ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, 6.283); ctx.fill(); ctx.stroke();
          ctx.strokeStyle = B.hi; ctx.lineWidth = Math.max(1.2, r * 0.18);
          ctx.beginPath(); ctx.arc(p.x, p.y, r * 0.62, 3.6, 4.6); ctx.stroke();
          ctx.lineWidth = 1.8;
        }
      }
      ctx.restore();
    },
    reset() { list.length = 0; },
  };
})();

/* 一片法术潮。C：
   top：各层贴图的 y 以这里为 0；rise / fall：推满、退空各几秒；side：从哪边进场（−1 左 / +1 右）；
   layers：远 → 近（层数不定，小兵骑在第 1、2 层），每层 { src, w, h（贴图尺寸，make.py 打印）, y（贴图上沿在 top 下多少）, v（平移，像素/秒，正 = 往右）,
           swell [起伏幅度, 涌浪长, 走速]（按列起伏）, bob [幅度, 角频率]（整层上下晃） }；
   haze（可无）：画在三层之下的一片竖向渐变 [颜色, 上沿不透明度, 下沿不透明度]，从 top + haze[3] 到屏幕下沿；
   spray：上沿甩出的东西 { every（多久试一次）, crest（上沿最高那几成才甩）, V, spread, G（正 = 往下掉，负 = 往上飘）, life, r, a, dot（软点三色）, layers（哪几层甩）}；
   kinds：小兵贴图、走速；dir：小兵往哪走（+1 右 / −1 左，贴图朝向要跟它一致）；mobs：开场位置；sink：贴图下沿压到上沿以下几成；
   hop：蹦起来 { every, T, h, splash（落回去甩几颗）}。 */
function Tide(C) {
  const SL = 8;              // 按列起伏的竖条宽（像素）：相邻两条的高差 ≤ A·2π/L·SL，1 像素以内看不出台阶
  const LIP = 10;            // 量上沿：从上往下第一个"下面连着 LIP 个不透明像素"的点（浪尖上方飞着的水沫不算）
  const S = C.spray;
  let W = 960, H = 1707;
  const N = C.layers.length, LAST = C.layers[N - 1];
  let lv = 0, t = 0, imgs = [], mobs = [], hopT = 3, sprays = [], sprayT = 0, frontT = 0, dot = null;

  function init(w, h) { W = w; H = h; reset(); }

  /* 贴图 → 横向多接 SL 像素的画布（竖条取到末尾不用拆两段）、每列上沿 top、甩东西的门槛 crest（上沿最高那 S.crest 的分位） */
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
    L.crest = [...sm].sort((a, b) => a - b)[Math.floor(L.w * S.crest)];
  }

  function load(v, off) {
    if (off) return Promise.resolve(false);
    const img = (src) => new Promise((ok) => {
      const i = new Image();
      i.onload = () => ok(i); i.onerror = () => ok(null);
      i.src = src + (v ? '?v=' + encodeURIComponent(v) : '');
    });
    dot = softDot(...S.dot);
    return Promise.all([
      Promise.all(C.layers.map(L => img(L.src).then(i => { if (i) prep(L, i); return !!i; }))),
      Promise.all(C.kinds.map(K => img(K.src))).then(r => { imgs = r; return r.every(Boolean); }),
    ]).then(([a, b]) => a.every(Boolean) && b);
  }

  function reset() {
    lv = 0; t = 0; hopT = 3; sprays = []; sprayT = 0; frontT = 0;
    mobs = C.mobs.map(m => ({ ...m, x: m.x * W, ph: Math.random() * 6, hop: -1 }));
  }

  const ease = (u) => u * u * (3 - 2 * u);
  const mod = (a, n) => ((a % n) + n) % n;
  /* 第 k 层贴图上沿在屏幕 x 处的 y（不含浪形，只含整层位置 + 起伏） */
  function baseY(k, x) {
    const L = C.layers[k];
    return C.top + L.y + L.bob[0] * Math.sin(t * L.bob[1] + k * 1.7)
      + L.swell[0] * Math.sin(6.2832 * (x - L.swell[2] * t) / L.swell[1]);
  }
  /* 第 k 层在屏幕 x 处的上沿（屏幕 y） */
  function surfY(k, x) {
    const L = C.layers[k];
    return baseY(k, x) + L.top[Math.floor(mod(x - L.v * t, L.w))];
  }

  function spray(k, x, y, n, up) {
    for (let i = 0; i < n; i++) {
      const a = -Math.PI / 2 + (Math.random() - 0.5) * S.spread * (up ? 1.6 : 1) + (up ? 0 : Math.sign(C.layers[k].v) * 0.35);
      const v = S.V[0] + Math.random() * (S.V[1] - S.V[0]);
      sprays.push({ k, x, y, vx: Math.cos(a) * v + C.layers[k].v, vy: Math.sin(a) * v, t: 0,
                    life: S.life[0] + Math.random() * (S.life[1] - S.life[0]),
                    r: (S.r[0] + Math.random() * (S.r[1] - S.r[0])) * (k === 1 ? 0.8 : 1) });
    }
  }

  /* front：前沿此刻在屏幕哪个 x（main.js tideSpan；贴着屏幕边 / 跟另一片顶在一起时给 null）。推进、退回的路上前沿一路甩东西，
     读成一道浪头 / 一道金光卷过来，而不是一块图淡进来 */
  function update(dt, on, front) {
    const lv0 = lv;
    lv = Math.max(0, Math.min(1, lv + (on ? dt / C.rise : -dt / C.fall)));
    if (front != null && lv !== lv0) for (frontT += dt; frontT >= C.front.every; frontT -= C.front.every) {
      const k = 1 + Math.floor(Math.random() * (N - 1));
      spray(k, front + (Math.random() - 0.5) * 40, surfY(k, front) + 6, 1, true);
    }
    for (let i = sprays.length - 1; i >= 0; i--) {
      const p = sprays[i];
      p.vy += S.G * dt; p.x += p.vx * dt; p.y += p.vy * dt;
      if ((p.t += dt) > p.life) sprays.splice(i, 1);
    }
    if (lv <= 0) return;
    t += dt;
    if (!LAST.top) return;
    /* 小兵往 dir 那边冲，出了画从另一边再进来；隔几秒挑一只蹦起来，落回去甩一圈 */
    for (const m of mobs) {
      m.x += C.dir * C.kinds[m.k].v * m.s * dt;
      const w = imgs[m.k] ? imgs[m.k].width * m.s : 150;
      if (C.dir > 0 && m.x - w / 2 > W) m.x = -w / 2;
      if (C.dir < 0 && m.x + w / 2 < 0) m.x = W + w / 2;
      if (m.hop >= 0 && (m.hop += dt) > C.hop.T) { m.hop = -1; spray(m.row + 1, m.x, surfY(m.row + 1, m.x), C.hop.splash, true); }
    }
    if (on && (hopT -= dt) <= 0) {
      const idle = mobs.filter(m => m.hop < 0 && m.x > 40 && m.x < W - 40);
      if (idle.length) idle[Math.floor(Math.random() * idle.length)].hop = 0;
      hopT = C.hop.every[0] + Math.random() * (C.hop.every[1] - C.hop.every[0]);
    }
    /* 上沿甩东西：随机挑一层（S.layers）、一个 x，那里的上沿够高（贴图里最高那几成）才甩；退潮时不甩 */
    if (on) for (sprayT += dt; sprayT >= S.every; sprayT -= S.every) {
      const k = S.layers[Math.floor(Math.random() * S.layers.length)], L = C.layers[k], x = Math.random() * W;
      if (L.top[Math.floor(mod(x - L.v * t, L.w))] <= L.crest) spray(k, x, surfY(k, x) + 4, 1 + (Math.random() < 0.4 ? 1 : 0), false);
    }
  }

  function drawLayer(ctx, k, x0, x1) {
    const L = C.layers[k];
    if (!L.ext) return;
    const off = mod(-L.v * t, L.w), fx = off - Math.floor(off);   // 屏幕 x 处取贴图第 (x + off) 列；整数列取、小数部分挪到落点上
    for (let x = Math.floor(x0 / SL) * SL; x < x1 + SL; x += SL) {
      const u = Math.floor(mod(x + off, L.w));
      ctx.drawImage(L.ext, u, 0, SL + 1, L.h, x - fx, baseY(k, x + SL / 2), SL + 1, L.h);   // 多画 1 像素：竖条之间不漏缝
    }
  }

  function drawSprays(ctx, k) {
    for (const p of sprays) {
      if (p.k !== k) continue;
      const u = p.t / p.life;
      ctx.globalAlpha = S.a * (u < 0.15 ? u / 0.15 : 1 - (u - 0.15) / 0.85);
      const r = p.r * (1 + 0.6 * u);                 // 越飞越散
      ctx.drawImage(dot, p.x - r, p.y - r, 2 * r, 2 * r);
    }
    ctx.globalAlpha = 1;
  }

  function drawMob(ctx, m) {
    const im = imgs[m.k];
    if (!im) return;
    const w = im.width * m.s, h = im.height * m.s, k = m.row + 1;
    const wy = surfY(k, m.x), slope = (surfY(k, m.x + 18) - surfY(k, m.x - 18)) / 36;
    let y = wy + h * C.sink + Math.sin(t * 3 + m.ph) * 3, rot = Math.atan(slope) * 0.6;
    if (m.hop >= 0) {                                 // 蹦起来：抛物线，空中朝前打半个滚
      const u = m.hop / C.hop.T;
      y -= C.hop.h * 4 * u * (1 - u);
      rot += C.dir * Math.sin(u * Math.PI) * 0.5;
    }
    ctx.save(); ctx.translate(m.x, y); ctx.rotate(rot);
    ctx.drawImage(im, -w / 2, -h, w, h);
    ctx.restore();
  }

  /* 只画 [x0, x1) 这一段（推进到哪 / 两个人同时在场时各占一边，main.js tideSpan）。两头各羽化 FEATHER 像素（贴着屏幕边的那头不羽化）：
     第一版硬裁一刀，海和经卷之间一条笔直的竖线，像两张图拼起来的。现在先画进自己的离屏画布，再按横向渐变抠掉交界那一段，
     两边在交界处互相淡进淡出（小兵走过交界也是慢慢淡掉，不是被一刀切掉）。
     飞沫 / 光点不裁：前沿甩出来的正好在羽化带上，裁了就只剩一半；它们飞到对面那片上头也是对撞的一部分。 */
  const FEATHER = 70;
  let buf = null;
  function draw(ctx, x0 = 0, x1 = W) {
    if (!LAST.top || (lv <= 0 && !sprays.length)) return;
    const full = x0 <= 0 && x1 >= W, out = ctx;
    if (!full) {
      if (!buf) { buf = document.createElement('canvas'); buf.width = W; buf.height = H; }
      ctx = buf.getContext('2d');
      ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, W, H);
    }
    const on = lv > 0 && x1 > x0;                    // 退空了只剩飞在半空的飞沫 / 光点
    ctx.save();
    if (C.haze && on) {
      const [c, a0, a1, dy] = C.haze, y0 = C.top + dy, g = ctx.createLinearGradient(0, y0, 0, H);
      g.addColorStop(0, `rgba(${c},${a0})`); g.addColorStop(1, `rgba(${c},${a1})`);
      ctx.fillStyle = g; ctx.fillRect(x0, y0, x1 - x0, H - y0);
    }
    for (let k = 0; k < N; k++) {
      if (on) drawLayer(ctx, k, x0, x1);
      if (full) drawSprays(ctx, k);
      if (k < 2 && on) for (const m of mobs) if (m.row === k) drawMob(ctx, m);
    }
    ctx.restore();
    if (full) return;
    const g = ctx.createLinearGradient(x0 - FEATHER, 0, x1 + FEATHER, 0), L = x1 - x0 + 2 * FEATHER;
    const edge = (x, on) => [(x - (x0 - FEATHER)) / L, on];
    for (const [u, on] of [edge(x0 - FEATHER, x0 <= 0 ? 1 : 0), edge(x0 + FEATHER, 1), edge(x1 - FEATHER, 1), edge(x1 + FEATHER, x1 >= W ? 1 : 0)])
      g.addColorStop(Math.max(0, Math.min(1, u)), `rgba(0,0,0,${on})`);
    ctx.globalCompositeOperation = 'destination-in';
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'source-over';
    out.drawImage(buf, 0, 0);
    for (let k = 0; k < N; k++) drawSprays(out, k);
  }

  const active = () => lv > 0;
  const level = () => ease(lv);
  /* 上沿（给交界处的对撞找高度）：最远那层在 x 处的上沿 */
  const edgeY = (x) => C.layers[0].top ? surfY(0, x) : H;
  return { init, load, update, draw, reset, active, level, edgeY };
}

/* ---- 白娘子的海 ----
   三层贴图 v14/sea2/make.py 出（尺寸是它打印的；已按屏幕大小缩好，引擎不再缩放）。
   直播画面下半截压着礼物面板（画布 y ≈ 1373 以下看不见）：三层浪尖都摆在面板之上 —— 远 ≈ 1203~1261、中 ≈ 1242~1328、近 ≈ 1312~1399。
   虾兵蟹将（v14/sea/make.py，都朝右）往右冲（冲男生那边：她的兵）；row 0 泡在中层（缩放 0.75，远）、row 1 泡在近层（1.0）。
   2026-09-28 用户先说"往上挪挪，但不要盖住男女生"，后来又定"水面和卷轴是在男女主的上层"：整片潮连兵一起画在男女主之后（盖在脚上）。 */
const Sea = Tide({
  top: 1190, rise: 1.4, fall: 1.4, side: -1,
  front: { every: 0.012 },       // 推进 / 退回时前沿每隔几秒甩一颗（浪头的飞沫）
  layers: [
    { src: 'assets/world/sea2_far.webp',  w: 536, h: 276, y: 0,   v: -14, swell: [4, 520, 30],  bob: [2, 0.9] },
    { src: 'assets/world/sea2_mid.webp',  w: 696, h: 356, y: 52,  v: 26,  swell: [7, 640, -45], bob: [3, 1.1] },
    { src: 'assets/world/sea2_near.webp', w: 884, h: 439, y: 112, v: -44, swell: [10, 780, 70], bob: [4, 1.3] },
  ],
  /* 浪尖飞沫：软边白点往上溅、带重力落回去；中、近两层才甩（远层的太小看不见） */
  spray: { every: 0.035, crest: 0.25, V: [120, 260], spread: 1.1, G: 700, life: [0.45, 0.8], r: [2.5, 6], a: 0.85, layers: [1, 2, 2],
           dot: ['rgba(255,255,255,1)', 'rgba(235,248,255,0.85)', 'rgba(200,232,255,0)'] },
  kinds: [
    { src: 'assets/world/sea_shrimp1.webp', v: 60 }, { src: 'assets/world/sea_shrimp2.webp', v: 70 },
    { src: 'assets/world/sea_crab1.webp', v: 45 },   { src: 'assets/world/sea_crab2.webp', v: 50 },
  ],
  dir: +1,
  mobs: [
    { x: 0.08, row: 0, k: 2, s: 0.75 }, { x: 0.42, row: 0, k: 0, s: 0.75 }, { x: 0.76, row: 0, k: 3, s: 0.75 },
    { x: 0.22, row: 1, k: 1, s: 1.0 }, { x: 0.58, row: 1, k: 2, s: 1.0 }, { x: 0.92, row: 1, k: 0, s: 1.0 },
  ],
  sink: 0.3,                     // 泡在水里：贴图下沿压到浪上沿以下 30% 的高度（被那一层海盖住）
  hop: { every: [2.2, 4.0], T: 0.7, h: 70, splash: 16 },
});

/* ---- 法海的金光经卷 ----
   三条卷轴 v14/scroll/make.py 出（程序画的，尺寸是它打印的；贴图上下各有一圈金光留边：远 14、中 20、近 26）。
   绢面摆位（屏幕 y）：远 ≈ 1246~1311、中 ≈ 1311~1403、近 ≈ 1366~1484、deep1 ≈ 1470~1600、deep2 ≈ 1585~1727（出屏）。
   2026-09-28 用户："卷轴下半部分是空的，应该和水面一样，补齐。卷轴的上边缘略高，应该与水面齐平"：
   原来三条摆在 1204~1436，近层以下只剩一层金雾；现在远 / 中 / 近三条的绢面上沿各对齐海那一层浪上沿的中位数
   （海：远 1246、中 1311、近 1366，量贴图 alpha），近层下面再铺 deep1、deep2 两条更大的（v14/scroll/make.py），铺到屏幕下沿。
   比海起伏得大、涌浪短（swell）：卷轴是绸子，要读成"飘"；底下铺一片金色光雾（haze）当"海水"。
   神兽小佛（v14/scroll/beasts.py，都朝左）往左冲（冲女生那边），骑在卷轴上（sink 小：站在绢面上，不是泡在里面）。 */
const Scroll = Tide({
  top: 1190, rise: 1.4, fall: 1.4, side: +1,
  front: { every: 0.018 },
  layers: [
    { src: 'assets/world/scroll_far.webp',   w: 800,  h: 93,  y: 42,  v: 18,  swell: [8, 380, -40], bob: [3, 0.9] },
    { src: 'assets/world/scroll_mid.webp',   w: 952,  h: 132, y: 101, v: -30, swell: [12, 460, 55], bob: [4, 1.1] },
    { src: 'assets/world/scroll_near.webp',  w: 1080, h: 170, y: 150, v: 46,  swell: [16, 560, -70], bob: [5, 1.3] },
    { src: 'assets/world/scroll_deep1.webp', w: 1120, h: 188, y: 251, v: -38, swell: [16, 620, 60], bob: [5, 1.2] },
    { src: 'assets/world/scroll_deep2.webp', w: 1118, h: 204, y: 364, v: 52,  swell: [18, 700, -80], bob: [6, 1.4] },
  ],
  haze: ['255,196,70', 0.18, 0.55, 60],
  /* 卷轴上沿飘起的金色光点：往上飘（G 负）、慢、寿命长 */
  spray: { every: 0.05, crest: 0.5, V: [30, 90], spread: 1.4, G: -60, life: [0.8, 1.4], r: [2.5, 5.5], a: 0.95, layers: [0, 1, 2],
           dot: ['rgba(255,252,220,1)', 'rgba(255,214,90,0.85)', 'rgba(255,170,30,0)'] },
  kinds: [
    { src: 'assets/world/scroll_monk.webp', v: 55 }, { src: 'assets/world/scroll_qilin.webp', v: 70 },
    { src: 'assets/world/scroll_lion.webp', v: 62 }, { src: 'assets/world/scroll_elephant.webp', v: 45 },
  ],
  dir: -1,
  mobs: [
    { x: 0.12, row: 0, k: 1, s: 0.75 }, { x: 0.47, row: 0, k: 3, s: 0.75 }, { x: 0.83, row: 0, k: 0, s: 0.75 },
    { x: 0.28, row: 1, k: 2, s: 0.95 }, { x: 0.64, row: 1, k: 0, s: 0.95 }, { x: 0.96, row: 1, k: 3, s: 0.95 },
  ],
  sink: 0.16,                    // 贴图下沿留了 18 像素的金光边（beasts.py PAD），压 16% ≈ 脚踩在绢面上
  hop: { every: [2.0, 3.6], T: 0.7, h: 80, splash: 14 },
});

/* 两片潮同时在场：交界处（main.js tideSplit）一直往上迸水花和金光，读成两股法力顶在一起。
   update 给交界 x 和两边的强度 k（两边水位的较小者：只有一边时 0，不迸）。 */
const Clash = (() => {
  const E = { rate: 90, V: [220, 560], G: 900, life: [0.45, 0.9], r: [4, 10] };   // 每秒几颗、初速、重力、寿命、大小
  const list = [];
  let acc = 0, dots = null;
  return {
    update(dt, x, y, k) {
      for (let i = list.length - 1; i >= 0; i--) {
        const p = list[i];
        p.vy += E.G * dt; p.x += p.vx * dt; p.y += p.vy * dt;
        if ((p.t += dt) > p.life) list.splice(i, 1);
      }
      if (k <= 0) { acc = 0; return; }
      for (acc += dt * E.rate * k; acc >= 1; acc -= 1) {
        const gold = Math.random() < 0.5, a = -Math.PI / 2 + (gold ? 0.5 : -0.5) * Math.random();   // 金光往右（法海那边）偏、水往左偏
        const v = E.V[0] + Math.random() * (E.V[1] - E.V[0]);
        list.push({ gold, x: x + (Math.random() - 0.5) * 16, y: y + Math.random() * 40, vx: Math.cos(a) * v, vy: Math.sin(a) * v, t: 0,
                    life: E.life[0] + Math.random() * (E.life[1] - E.life[0]), r: E.r[0] + Math.random() * (E.r[1] - E.r[0]) });
      }
    },
    draw(ctx) {
      if (!list.length) return;
      if (!dots) dots = [softDot('rgba(255,255,255,1)', 'rgba(225,244,255,0.9)', 'rgba(120,190,250,0)'),
                         softDot('rgba(255,252,220,1)', 'rgba(255,210,80,0.9)', 'rgba(255,160,20,0)')];
      ctx.save();
      for (const p of list) {
        const u = p.t / p.life, r = p.r * (1 + 0.5 * u);
        ctx.globalAlpha = 1 - u; ctx.drawImage(dots[p.gold ? 1 : 0], p.x - r, p.y - r, 2 * r, 2 * r);
      }
      ctx.restore();
    },
    reset() { list.length = 0; acc = 0; },
  };
})();
