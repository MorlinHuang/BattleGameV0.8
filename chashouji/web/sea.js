/* sea.js —— 档 4 六个人各自铺在屏幕底部的"法术潮"（2026-09-28 起）+ 白娘子的掌心水柱贴图 WaterArt、命中的爆水泡沫 Foam。
 *
 * 六片：白娘子 海 Sea / 法海 经卷 Scroll（下面细说）；2026-09-29 加真相女神 真相云海 TruthTide / 灭迹恶魔 碎纸黑烟 DemonTide /
 * 嫦娥 明月银河 MoonSky / 后羿 烈日火空 SunSky（文件末尾，同一个 Sky，不是层层浪；贴图 v14/tides/make.py、v14/moonsky、v14/sunsky）。
 * 左边三片从左推进、右边三片从右。
 *
 * 白娘子（女生侧）→ 海水 Sea。用户："整个屏幕的底部，从下边缘到男女生下方，用海水汹涌填充（代表白娘子的水法术），
 *   海水也需要持续的动画，海里可以有些虾兵蟹将。白娘子持续 15s，海水也一样。当白娘子消失的时候，海水也消散。"
 *   海面三版：① canvas 现画的正弦色带 —— "太 Q"；② Blender 3 渲 2 的 Gerstner 海面 —— "水波纹不适合做体积感，回到 2D 但不要太 Q，
 *   要写实"；③ 现在：手绘写实海浪（生图 → 抠像 → 横向无缝长条，v14/sea2/make.py），远 / 中 / 近三层。
 * 法海（男生侧）→ 金光经卷 Scroll。用户："同样也需要跟白娘子海面的动效，可能是在金光虚化的佛经卷轴，也会和海平面一样波动，
 *   虾兵蟹将可以对应神兽小佛"。三条金色《心经》卷轴（v14/scroll/make.py 程序画的，经文是真字）一层层起伏，
 *   底下一片金色光雾，卷轴上骑着神兽小佛（v14/scroll/beasts.py：小沙弥、麒麟崽、小石狮、小白象）。
 *
 * 海、经卷、真相云海、碎纸黑烟四片是同一套东西（Tide）：三层横向无缝长条贴图，
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
 * 两边同时有人：各推到两边进度的分界，交界处两边的飞沫对撞（Clash）。
 *
 * 层级（main.js renderActors）：画在男女主之上（用户："水面和卷轴是在男女主的上层"）—— 潮漫过两人的脚和小腿。
 * 层数不定（C.layers 远 → 近，最后一层最近、最低）：经卷为了铺满到屏幕下沿比海多两条。
 */
'use strict';

/* 掌心水柱的 3D 贴图（tools/3d/water/pack_water.py 打印的，重渲后重填）。
   16 帧、4 列，x0 = 掌心在格子里的 x、cy = 中轴的 y；loop = 引擎里多少秒转一圈（jet.py 按整周期渲，首尾相接）。 */
const WaterArt = {
  jet: { src: 'assets/fx/jet.webp', n: 16, cols: 4, w: 709, h: 166, x0: 1, cy: 90, loop: 0.5 },
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
   spray：上沿甩出的东西 { every（多久试一次）, crest（上沿最高那几成才甩）, V, spread, G（正 = 往下掉，负 = 往上飘）, life, r, a, dot（软点三色）, layers（哪几层甩），
          shape（可无）：[形状, 占几成, 大小倍数, ...颜色] —— 'chat' 聊天气泡 [.., 填色, 描边]、'paper' 碎纸条 [.., 纸色]，其余几成照样是软点 }；
   kinds：小兵贴图、走速；dir：小兵往哪走（+1 右 / −1 左，贴图朝向要跟它一致）；mobs：开场位置；sink：贴图下沿压到上沿以下几成；
   hop：蹦起来 { every, T, h, splash（落回去甩几颗）}。 */
/* 一片潮只画 [x0, x1)，两头各羽化 FEATHER 像素（贴着屏幕边的那头不羽化）：第一版硬裁一刀，海和经卷之间一条笔直的竖线，
   像两张图拼起来的。先画进自己的离屏画布（begin 给它），end 按横向渐变抠掉交界那一段再贴回去 ——
   两边在交界处互相淡进淡出（小兵走过交界也是慢慢淡掉，不是被一刀切掉）。 */
function SpanBuf() {
  const FEATHER = 70;
  let buf = null;
  return {
    begin(W, H) {
      if (!buf) { buf = document.createElement('canvas'); buf.width = W; buf.height = H; }
      const c = buf.getContext('2d');
      c.setTransform(1, 0, 0, 1, 0, 0); c.clearRect(0, 0, W, H);
      return c;
    },
    end(out, x0, x1) {
      const c = buf.getContext('2d'), W = buf.width, H = buf.height;
      if (x0 > 0 || x1 < W) {
        const g = c.createLinearGradient(x0 - FEATHER, 0, x1 + FEATHER, 0), L = x1 - x0 + 2 * FEATHER;
        const edge = (x, on) => [(x - (x0 - FEATHER)) / L, on];
        for (const [u, on] of [edge(x0 - FEATHER, x0 <= 0 ? 1 : 0), edge(x0 + FEATHER, 1), edge(x1 - FEATHER, 1), edge(x1 + FEATHER, x1 >= W ? 1 : 0)])
          g.addColorStop(Math.max(0, Math.min(1, u)), `rgba(0,0,0,${on})`);
        c.globalCompositeOperation = 'destination-in';
        c.fillStyle = g; c.fillRect(0, 0, W, H);
        c.globalCompositeOperation = 'source-over';
      }
      out.drawImage(buf, 0, 0);
    },
  };
}

function Tide(C) {
  const SL = 8;              // 按列起伏的竖条宽（像素）：相邻两条的高差 ≤ A·2π/L·SL，1 像素以内看不出台阶
  const LIP = 10;            // 量上沿：从上往下第一个"下面连着 LIP 个不透明像素"的点（浪尖上方飞着的水沫不算）
  const S = C.spray;
  let W = 960, H = 1707;
  const N = C.layers.length, LAST = C.layers[N - 1];
  let lv = 0, t = 0, imgs = [], mobs = [], hopT = 3, sprays = [], sprayT = 0, frontT = 0, dot = null;
  /* 从出场视频接过来（handoff）：整片先抬 / 压到视频里海面的高度，SETTLE 秒里落回自己的位置 */
  const SETTLE = 1.2, EMERGE = [0.25, 0.22];     // 回位几秒；小兵第一只几秒后蹦出来、之后每隔几秒一只
  let lift = 0, liftT = -1;

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
    lv = 0; t = 0; hopT = 3; sprays = []; sprayT = 0; frontT = 0; lift = 0; liftT = -1;
    mobs = C.mobs.map(m => ({ ...m, x: m.x * W, ph: Math.random() * 6, hop: -1, wait: 0, em: false }));
  }

  const ease = (u) => u * u * (3 - 2 * u);
  const mod = (a, n) => ((a % n) + n) % n;
  /* 第 k 层贴图上沿在屏幕 x 处的 y（不含浪形，只含整层位置 + 起伏） */
  const liftNow = () => liftT < 0 ? 0 : lift * (1 - ease(Math.min(1, liftT / SETTLE)));
  function baseY(k, x) {
    const L = C.layers[k];
    return C.top + liftNow() + L.y + L.bob[0] * Math.sin(t * L.bob[1] + k * 1.7)
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
      sprays.push({ k, x, y, vx: Math.cos(a) * v + C.layers[k].v, vy: Math.sin(a) * v, t: 0, j: Math.random(), vr: (Math.random() - 0.5) * 12,
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
    if (liftT >= 0 && (liftT += dt) >= SETTLE) liftT = -1;
    if (!LAST.top) return;
    /* 小兵往 dir 那边冲，出了画从另一边再进来；隔几秒挑一只蹦起来，落回去甩一圈 */
    for (const m of mobs) {
      m.x += C.dir * C.kinds[m.k].v * m.s * dt;
      const w = imgs[m.k] ? imgs[m.k].width * m.s : 150;
      if (C.dir > 0 && m.x - w / 2 > W) m.x = -w / 2;
      if (C.dir < 0 && m.x + w / 2 < 0) m.x = W + w / 2;
      if (m.wait > 0 && (m.wait -= dt) <= 0) { m.hop = 0; m.em = true; spray(m.row + 1, m.x, surfY(m.row + 1, m.x), C.hop.splash, true); }
      if (m.hop >= 0 && (m.hop += dt) > C.hop.T) { m.hop = -1; m.em = false; spray(m.row + 1, m.x, surfY(m.row + 1, m.x), C.hop.splash, true); }
    }
    if (on && (hopT -= dt) <= 0) {
      const idle = mobs.filter(m => m.hop < 0 && !(m.wait > 0) && m.x > 40 && m.x < W - 40);
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

  /* 有形状的飞沫：真相云海往上冒聊天气泡（被翻出来的聊天记录）、灭迹黑烟里翻飞碎纸条（被撕掉的证据） */
  function drawShape(ctx, p, r) {
    const [kind, , , c0, c1] = S.shape;
    ctx.save(); ctx.translate(p.x, p.y);
    if (kind === 'chat') { ctx.rotate(Math.sin(p.t * 3 + p.j * 20) * 0.2); drawChatIcon(ctx, r, c0, c1, 2, c1); }
    else { ctx.rotate(p.vr * p.t + p.j * 6); ctx.fillStyle = c0; ctx.fillRect(-r, -r * 0.3, 2 * r, r * 0.6); }
    ctx.restore();
  }

  function drawSprays(ctx, k) {
    for (const p of sprays) {
      if (p.k !== k) continue;
      const u = p.t / p.life;
      ctx.globalAlpha = S.a * (u < 0.15 ? u / 0.15 : 1 - (u - 0.15) / 0.85);
      const r = p.r * (1 + 0.6 * u);                 // 越飞越散
      if (S.shape && p.j < S.shape[1]) drawShape(ctx, p, r * S.shape[2]);
      else ctx.drawImage(dot, p.x - r, p.y - r, 2 * r, 2 * r);
    }
    ctx.globalAlpha = 1;
  }

  function drawMob(ctx, m) {
    const im = imgs[m.k];
    if (!im || m.wait > 0) return;                    // 还潜在水里（handoff 后还没轮到它蹦出来）
    const w = im.width * m.s, h = im.height * m.s, k = m.row + 1;
    const wy = surfY(k, m.x), slope = (surfY(k, m.x + 18) - surfY(k, m.x - 18)) / 36;
    let y = wy + h * C.sink + Math.sin(t * 3 + m.ph) * 3, rot = Math.atan(slope) * 0.6;
    if (m.hop >= 0) {                                 // 蹦起来：抛物线，空中朝前打半个滚
      const u = m.hop / C.hop.T;
      y -= C.hop.h * 4 * u * (1 - u);
      if (m.em) y += h * 0.8 * Math.max(0, 1 - u * 2.5);   // 第一次是从水底下蹦出来：起跳时整只还在水面以下
      rot += C.dir * Math.sin(u * Math.PI) * 0.5;
    }
    ctx.save(); ctx.translate(m.x, y); ctx.rotate(rot);
    ctx.drawImage(im, -w / 2, -h, w, h);
    ctx.restore();
  }

  /* 只画 [x0, x1) 这一段（推进到哪 / 两个人同时在场时各占一边，main.js tideSpan），两头羽化（featherSpan）。
     飞沫 / 光点不裁：前沿甩出来的正好在羽化带上，裁了就只剩一半；它们飞到对面那片上头也是对撞的一部分。 */
  const span = SpanBuf();
  function draw(ctx, x0 = 0, x1 = W) {
    if (!LAST.top || (lv <= 0 && !sprays.length)) return;
    const full = x0 <= 0 && x1 >= W, out = ctx;
    if (!full) ctx = span.begin(W, H);
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
    span.end(out, x0, x1);
    for (let k = 0; k < N; k++) drawSprays(out, k);
  }

  /* 出场视频放完（intro.js → main.js）：视频底部带着同一片海，视频淡掉时这片海要已经原位铺满 ——
     不从画外推进来，直接满；整片从视频里海面的高度 y（画布）落回自己的位置；视频结尾虾兵蟹将潜回水里了，
     这边的小兵先藏着，隔一会儿一只只从海里蹦出来（读成从视频的海里冲进游戏）。
     "海面高度"两边按同一个量法：每列最上沿取中位数（vframes layer.sea_line / 这里第 0 层上沿）。 */
  function handoff(y) {
    if (!LAST.top) return;
    lv = 1; liftT = -1;
    const tops = [];
    for (let x = 0; x < W; x += SL) tops.push(surfY(0, x));
    tops.sort((a, b) => a - b);
    lift = y - tops[tops.length >> 1]; liftT = 0;
    const order = mobs.map((_, i) => i).sort(() => Math.random() - 0.5);
    order.forEach((i, n) => { mobs[i].wait = EMERGE[0] + n * EMERGE[1]; mobs[i].hop = -1; });
  }

  const active = () => lv > 0;
  const level = () => ease(lv);
  const dotImg = () => dot;              // 交界对撞（Clash）用这片潮自己的飞沫颜色
  /* 上沿（给交界处的对撞找高度）：最远那层在 x 处的上沿 */
  const edgeY = (x) => C.layers[0].top ? surfY(0, x) : H;
  return { init, load, update, draw, reset, handoff, active, level, edgeY, dotImg, side: C.side };
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

/* 两片潮同时在场：交界处（main.js tideSpan）一直往上迸两边各自的飞沫（水花和金光、月光和火星……），读成两股法力顶在一起。
   update 给交界 x、高度 y、强度 k（两边进度的较小者；没顶在一起时 0，不迸）、左右两片潮（取它们的飞沫贴图，Tide.dotImg）。 */
const Clash = (() => {
  const E = { rate: 90, V: [220, 560], G: 900, life: [0.45, 0.9], r: [4, 10] };   // 每秒几颗、初速、重力、寿命、大小
  const list = [];
  let acc = 0;
  return {
    update(dt, x, y, k, L, R) {
      for (let i = list.length - 1; i >= 0; i--) {
        const p = list[i];
        p.vy += E.G * dt; p.x += p.vx * dt; p.y += p.vy * dt;
        if ((p.t += dt) > p.life) list.splice(i, 1);
      }
      if (k <= 0) { acc = 0; return; }
      for (acc += dt * E.rate * k; acc >= 1; acc -= 1) {
        const right = Math.random() < 0.5, a = -Math.PI / 2 + (right ? 0.5 : -0.5) * Math.random();   // 右边那片的往右偏、左边的往左偏
        const v = E.V[0] + Math.random() * (E.V[1] - E.V[0]);
        list.push({ img: (right ? R : L).dotImg(), x: x + (Math.random() - 0.5) * 16, y: y + Math.random() * 40, vx: Math.cos(a) * v, vy: Math.sin(a) * v, t: 0,
                    life: E.life[0] + Math.random() * (E.life[1] - E.life[0]), r: E.r[0] + Math.random() * (E.r[1] - E.r[0]) });
      }
    },
    draw(ctx) {
      if (!list.length) return;
      ctx.save();
      for (const p of list) {
        if (!p.img) continue;
        const u = p.t / p.life, r = p.r * (1 + 0.5 * u);
        ctx.globalAlpha = 1 - u; ctx.drawImage(p.img, p.x - r, p.y - r, 2 * r, 2 * r);
      }
      ctx.restore();
    },
    reset() { list.length = 0; acc = 0; },
  };
})();

/* ---- 真相女神、灭迹恶魔的两片潮（2026-09-29；嫦娥、后羿原来的月夜银云海 / 太阳火云海换成了 MoonSky / SunSky）----
   用户："给真相女神和恶魔添加类似水面和卷轴的效果"；"新增一对嫦娥 vs 后羿，制作规格和白娘子法海一致"。
   贴图 v14/tides/make.py 出（尺寸是它打印的）：每片一张生图，远 / 中 / 近三层（中层水平翻），小兵是 2×2 一张切的。
   摆位同海：三层浪上沿的中位数各对齐海那一层（远 1246、中 1311、近 1366，y = 1246 − 1190 − 贴图里上沿中位数），近层都高到出屏。
   平移、起伏同海（各层反向走、远慢近快）；左边的往右冲、从左进场，右边的往左冲、从右进场。 */
const TIDE_SWELL = [[-14, [4, 520, 30], [2, 0.9]], [26, [7, 640, -45], [3, 1.1]], [-44, [10, 780, 70], [4, 1.3]]];   // 三层的 [v, swell, bob]（同海）
/* 三层：[名, w, h, y]（make.py 打印），dir：左边的潮 +1（层的平移方向跟海一致）、右边的 −1（镜像过来） */
const tideLayers = (name, sizes, dir) => sizes.map(([ln, w, h, y], k) => {
  const [v, sw, bob] = TIDE_SWELL[k];
  return { src: `assets/world/tide_${name}_${ln}.webp`, w, h, y, v: v * dir, swell: [sw[0], sw[1], sw[2] * dir], bob };
});
const tideKinds = (name, list) => list.map(([k, v]) => ({ src: `assets/world/tide_${name}_${k}.webp`, v }));
const TIDE_MOBS = [                    // 开场位置（同海）：row 0 骑中层（缩放 0.75）、row 1 骑近层（0.95）
  { x: 0.08, row: 0, k: 2, s: 0.75 }, { x: 0.42, row: 0, k: 0, s: 0.75 }, { x: 0.76, row: 0, k: 3, s: 0.75 },
  { x: 0.22, row: 1, k: 1, s: 0.95 }, { x: 0.58, row: 1, k: 2, s: 0.95 }, { x: 0.92, row: 1, k: 0, s: 0.95 },
];

/* 真相云海：翠绿发光云浪，往上冒聊天气泡（被翻出来的聊天记录）和绿色光点；放大镜、带翅膀的手机、聊天气泡、相机小精灵往右冲 */
const TruthTide = Tide({
  top: 1190, rise: 1.4, fall: 1.4, side: -1, front: { every: 0.014 },
  layers: tideLayers('truth', [['far', 535, 319, 13], ['mid', 693, 413, 65], ['near', 888, 529, 105]], +1),
  spray: { every: 0.04, crest: 0.4, V: [40, 120], spread: 1.2, G: -70, life: [0.9, 1.5], r: [3, 6], a: 0.95, layers: [0, 1, 2],
           dot: ['rgba(240,255,230,1)', 'rgba(150,255,150,0.85)', 'rgba(40,200,80,0)'],
           shape: ['chat', 0.3, 2.6, 'rgba(255,255,255,0.95)', 'rgb(40,140,60)'] },
  kinds: tideKinds('truth', [['magnifier', 60], ['phone', 70], ['bubble', 50], ['camera', 55]]),
  dir: +1, mobs: TIDE_MOBS,
  sink: 0.22,                    // 小精灵下半截没在云里
  hop: { every: [2.0, 3.6], T: 0.7, h: 80, splash: 12 },
});

/* 灭迹黑烟：紫黑浓烟浪，碎纸条从浪尖翻飞出来再落回去（被撕掉的证据），夹着紫色火星；小恶魔、吃纸垃圾桶、碎纸机、橡皮擦往左冲 */
const DemonTide = Tide({
  top: 1190, rise: 1.4, fall: 1.4, side: +1, front: { every: 0.014 },
  layers: tideLayers('demon', [['far', 535, 301, 30], ['mid', 693, 390, 87], ['near', 888, 499, 133]], -1),
  spray: { every: 0.03, crest: 0.35, V: [140, 300], spread: 1.1, G: 520, life: [0.7, 1.1], r: [3, 6], a: 0.95, layers: [1, 2, 2],
           dot: ['rgba(255,220,255,1)', 'rgba(200,90,240,0.85)', 'rgba(90,20,120,0)'],
           shape: ['paper', 0.55, 1.6, 'rgba(246,244,250,0.95)'] },
  kinds: tideKinds('demon', [['imp', 70], ['bin', 55], ['shredder', 50], ['eraser', 62]]),
  dir: -1, mobs: TIDE_MOBS,
  sink: 0.22,
  hop: { every: [2.0, 3.6], T: 0.7, h: 80, splash: 14 },
});

/* ---- 嫦娥的明月银河 MoonSky / 后羿的烈日火空 SunSky（2026-09-29，替掉月夜银云海、太阳火云海）----
   嫦娥（用户："太像水面了，跟白娘子的重复而且与嫦娥设定不搭。屏幕下方的特效，可以做一轮明月 + 银河星带，里面再漂些兔子和薄纱就行"，方案 A）：
     深蓝夜空，左下角半轮大明月从下沿升起；银河星带从明月往右上铺开、星尘往右流、星星一闪一闪；玉兔失重般翻着往右漂；几条淡紫薄纱飘。
   后羿（用户："后羿的元素是对比嫦娥的。屏幕下方的特效，可以做一轮烈日 + 火花飞溅，里面有小陨石和三足金乌飞行"，方案 A）：
     暗红到橙金的火空，右下角半轮烈日从下沿升起、日冕一道道转着翻腾；火焰云带从烈日往左上铺开、往左流；火花一直往上溅；
     小陨石拖着火尾从右上往左下坠、落到底炸一小团火星；三足金乌（v14/tides 的 tide_sun_crow1~4）往左飞、翅膀一扇一扇（身子上下颤）。
   两片左右镜像，同一个 Sky(C)：不是层层浪（Tide），没有"上沿"可骑，对外接口跟 Tide 一样（main.js TIDE_OF 照常推进 / 退场 / 两边对顶 / 羽化）。
   进场：[x0, x1) 从自己那边铺开（main.js tideSpan），明月 / 烈日同时从下沿升起（sink × (1 − 进度)），前沿一路迸光点。
   贴图 v14/moonsky/make.py、v14/sunsky/make.py；夜空、星星、星尘、薄纱、日冕、火花、陨石现画。
   画法：天空 + 星带 + 星星 + 星尘先画进离屏画布、按竖向渐变把上沿抠成渐隐（一起淡进客厅），再画日月、纱、兔 / 金乌、陨石、火花（不淡）。
   C 里哪样没有就不画：stars / dust / ribbons 只有嫦娥，corona / embers / meteors 只有后羿。 */
function Sky(C) {
  let W = 960, H = 1707, lv = 0, t = 0, frontT = 0, band = null, orb = null, mobImgs = [], stars = [], dust = [], sparks = [], embers = [], meteors = [];
  let emberT = 0, meteorT = 1;
  const dot = softDot(...C.dot);
  const span = SpanBuf();
  const ease = (u) => u * u * (3 - 2 * u), mod = (a, n) => ((a % n) + n) % n, rnd = (a, b) => a + Math.random() * (b - a);
  const G = C.band, bandY = (x) => G.y + (x - W / 2) * Math.tan(G.tilt);

  function init(w, h) { W = w; H = h; reset(); }
  function load(v, off) {
    if (off) return Promise.resolve(false);
    const img = (src) => new Promise((ok) => {
      const i = new Image();
      i.onload = () => ok(i); i.onerror = () => ok(null);
      i.src = src + (v ? '?v=' + encodeURIComponent(v) : '');
    });
    return Promise.all([img(G.src), img(C.orb.src), ...C.mobs.list.map(m => img(C.mobs.src(m.k)))]).then(([g, m, ...ms]) => {
      band = g; orb = m; mobImgs = ms;
      return !!g && !!m && ms.every(Boolean);
    });
  }
  function reset() {
    lv = 0; t = 0; frontT = 0; sparks = []; embers = []; meteors = []; emberT = 0; meteorT = 1;
    const S = C.sky;
    stars = C.stars ? Array.from({ length: C.stars.n }, (_, i) => ({ x: Math.random() * W, y: rnd(S.y1 - 10, H), r: rnd(0.8, 2.2), big: i < C.stars.big,
                                                                     w: rnd(1.5, 4), ph: Math.random() * 6.3 })) : [];
    dust = C.dust ? Array.from({ length: C.dust.n }, () => newDust(Math.random() * W)) : [];
  }
  function newDust(x) {
    const D = C.dust;
    return { x, off: (Math.random() + Math.random() - 1) * D.band, v: rnd(D.v[0], D.v[1]), r: rnd(D.r[0], D.r[1]), ph: Math.random() * 6.3 };
  }

  function update(dt, on, front) {
    const lv0 = lv, S = C.sky;
    lv = Math.max(0, Math.min(1, lv + (on ? dt / C.rise : -dt / C.fall)));
    if (front != null && lv !== lv0) for (frontT += dt; frontT >= C.front.every; frontT -= C.front.every)
      sparks.push({ x: front + rnd(-20, 20), y: rnd(S.y1, 1400), vx: -C.side * rnd(-40, 120), vy: rnd(-130, -30), t: 0, life: rnd(0.6, 1.0), r: rnd(3, 7) });
    for (const list of [sparks, embers]) for (let i = list.length - 1; i >= 0; i--) {
      const p = list[i];
      p.vy += (p.g ?? -30) * dt; p.x += p.vx * dt; p.y += p.vy * dt;
      if ((p.t += dt) > p.life) list.splice(i, 1);
    }
    for (let i = meteors.length - 1; i >= 0; i--) {
      const m = meteors[i];
      m.x += m.vx * dt; m.y += m.vy * dt;
      if (m.y > C.meteors.floor) {                    // 落到底：炸一小团火星
        for (let k = 0; k < C.meteors.burst; k++) {
          const a = -Math.PI / 2 + rnd(-1.3, 1.3), v = rnd(80, 260);
          embers.push({ x: m.x, y: m.y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, g: 400, t: 0, life: rnd(0.3, 0.6), r: rnd(2.5, 5) });
        }
        meteors.splice(i, 1);
      }
    }
    if (lv <= 0) return;
    t += dt;
    for (const d of dust) if ((d.x += d.v * dt) > W + 10) Object.assign(d, newDust(-10));
    if (!on) return;
    /* 火花：从下沿（偏向烈日那边）往上溅，飘出上沿、飞进客厅一截再熄 */
    const E = C.embers;
    if (E) for (emberT += dt * E.rate; emberT >= 1; emberT--) {
      const x = Math.random() < E.nearOrb ? C.orb.x + rnd(-1, 1) * C.orb.D * 0.5 : Math.random() * W;
      embers.push({ x, y: rnd(E.y[0], E.y[1]), vx: rnd(-30, 30), vy: -rnd(E.v[0], E.v[1]), g: -20, t: 0, life: rnd(E.life[0], E.life[1]), r: rnd(E.r[0], E.r[1]) });
    }
    /* 陨石：隔几秒一颗，从上沿外面沿 ang 斜着坠下来 */
    const M = C.meteors;
    if (M && (meteorT -= dt) <= 0) {
      meteorT = rnd(M.every[0], M.every[1]);
      const v = rnd(M.v[0], M.v[1]);
      meteors.push({ x: rnd(W * 0.15, W + 120), y: C.sky.y0 + rnd(-10, 40), vx: Math.cos(M.ang) * v, vy: Math.sin(M.ang) * v, r: rnd(M.r[0], M.r[1]) });
    }
  }

  /* 十字芒：两道细光交叉 + 一颗亮点 */
  function cross(ctx, x, y, R, a) {
    ctx.globalAlpha = a;
    ctx.fillStyle = 'rgba(235,242,255,1)';
    ctx.fillRect(x - R, y - 0.8, 2 * R, 1.6); ctx.fillRect(x - 0.8, y - R, 1.6, 2 * R);
    ctx.drawImage(dot, x - R * 0.45, y - R * 0.45, R * 0.9, R * 0.9);
  }

  /* 一条纱：头在 hx，身子往左拖 len；中线是往右走的正弦，宽度两头收尖、按 tw 周期"翻面"（窄 → 宽 → 窄，读成绸子在转） */
  function ribbon(ctx, R, i) {
    const hx = mod(R.x * (W + R.len + 200) + R.v * t, W + R.len + 200) - 100;
    const up = [], dn = [], n = 40;
    for (let k = 0; k <= n; k++) {
      const u = k / n, x = hx - R.len * u;
      const yc = R.y + R.A * Math.sin(6.2832 * (x - 1.6 * R.v * t) / R.L + i * 2.1) + 5 * Math.sin(t * 0.8 + i);
      const hw = R.w / 2 * Math.pow(Math.sin(Math.PI * u), 0.6) * (0.25 + 0.75 * Math.abs(Math.cos(6.2832 * (x - 0.7 * R.v * t) / R.tw + i)));
      up.push([x, yc - hw]); dn.push([x, yc + hw]);
    }
    ctx.globalAlpha = 1;
    ctx.beginPath(); ctx.moveTo(...up[0]);
    for (const q of up) ctx.lineTo(...q);
    for (let k = dn.length - 1; k >= 0; k--) ctx.lineTo(...dn[k]);
    ctx.closePath();
    ctx.fillStyle = `rgba(${R.rgb},${R.a})`; ctx.fill();
    ctx.beginPath(); ctx.moveTo(...up[0]);
    for (const q of up) ctx.lineTo(...q);
    ctx.lineWidth = 1.5; ctx.strokeStyle = `rgba(248,244,255,${(R.a * 1.6).toFixed(2)})`; ctx.stroke();
  }

  /* 漂着的小东西（玉兔 / 金乌）：沿 v 横着走、出画从另一边再来；spin 整圈慢慢翻（0 = 只左右摆）；flap 扇翅：身子上下颤 + 竖着一伸一缩 */
  function mob(ctx, R, i) {
    const im = mobImgs[i];
    if (!im) return;
    const w = im.width * R.s, h = im.height * R.s, x = mod(R.x * (W + 260) + R.v * t, W + 260) - 130;
    let y = R.y + 12 * Math.sin(t * 0.9 + i * 1.7), rot = R.spin ? t * R.spin + i : 0.3 * Math.sin(t * 0.6 + i * 2.3), sy = 1;
    if (R.flap) { const f = Math.sin(t * R.flap + i * 2); y += 5 * f; sy = 1 + 0.08 * f; rot *= 0.4; }
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(1, sy); ctx.globalAlpha = 1;
    ctx.drawImage(im, -w / 2, -h / 2, w, h);
    ctx.restore();
  }

  /* 日冕：一道道细长的扇形光从日面往外伸，慢慢转、一明一暗（同 crew.js drawGodAura 的放射光） */
  function corona(ctx, x, y) {
    const K = C.orb.corona;
    for (let i = 0; i < K.n; i++) {
      const a = i / K.n * 6.2832 + t * K.spin, fl = 0.55 + 0.45 * Math.sin(t * 2.7 + i * 1.9);
      const r0 = C.orb.D * 0.42, r1 = C.orb.D * 0.5 + K.len * (0.6 + 0.4 * Math.sin(t * 1.3 + i * 2.7));
      const g = ctx.createRadialGradient(x, y, r0, x, y, r1);
      g.addColorStop(0, `rgba(${K.rgb},${(K.a * fl).toFixed(3)})`); g.addColorStop(1, `rgba(${K.rgb},0)`);
      ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(x, y); ctx.arc(x, y, r1, a - K.w, a + K.w); ctx.closePath(); ctx.fill();
    }
  }

  function meteor(ctx, m) {
    const M = C.meteors, sp = Math.hypot(m.vx, m.vy), ux = m.vx / sp, uy = m.vy / sp, L = M.tail * m.r;
    ctx.globalAlpha = 1; ctx.lineCap = 'round';
    for (const [w, c, a] of M.trail) {
      const g = ctx.createLinearGradient(m.x, m.y, m.x - ux * L, m.y - uy * L);
      g.addColorStop(0, `rgba(${c},${a})`); g.addColorStop(1, `rgba(${c},0)`);
      ctx.lineWidth = m.r * w; ctx.strokeStyle = g;
      ctx.beginPath(); ctx.moveTo(m.x, m.y); ctx.lineTo(m.x - ux * L, m.y - uy * L); ctx.stroke();
    }
    ctx.fillStyle = `rgb(${M.rock})`; ctx.beginPath(); ctx.arc(m.x, m.y, m.r, 0, 6.2832); ctx.fill();
    ctx.lineWidth = m.r * 0.35; ctx.strokeStyle = `rgba(${M.rim},0.95)`; ctx.stroke();
  }

  function draw(out, x0 = 0, x1 = W) {
    if (!band || (lv <= 0 && !sparks.length && !embers.length)) return;
    if (lv > 0 && x1 > x0) {
      const ctx = span.begin(W, H), S = C.sky;
      ctx.save();
      /* 天空 */
      const g = ctx.createLinearGradient(0, S.y0, 0, H);
      g.addColorStop(0, `rgba(${S.top},${S.a})`); g.addColorStop(1, `rgba(${S.bot},${S.a})`);
      ctx.fillStyle = g; ctx.fillRect(x0, S.y0, x1 - x0, H - S.y0);
      /* 星带 / 火焰云带：斜着铺、横着流（贴图横向无缝，接着画） */
      const tw = band.width * G.k, th = band.height * G.k, off = mod(G.v * t, tw);
      ctx.save(); ctx.translate(W / 2, G.y); ctx.rotate(G.tilt); ctx.globalAlpha = G.a ?? 1;
      for (let x = -W / 2 - 160 - tw + off; x < W / 2 + 160; x += tw) ctx.drawImage(band, x, -th / 2, tw + 1, th);
      ctx.restore();
      /* 星星：一闪一闪；带芒的几颗大一点 */
      for (const p of stars) {
        const a = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * p.w + p.ph));
        if (p.big) cross(ctx, p.x, p.y, 7 + 5 * a, a);
        else { ctx.globalAlpha = a; ctx.drawImage(dot, p.x - p.r * 1.6, p.y - p.r * 1.6, p.r * 3.2, p.r * 3.2); }
      }
      /* 星尘：沿星带流 */
      for (const d of dust) {
        ctx.globalAlpha = 0.5 + 0.5 * Math.sin(t * 3 + d.ph);
        ctx.drawImage(dot, d.x - d.r * 1.6, bandY(d.x) + d.off - d.r * 1.6, d.r * 3.2, d.r * 3.2);
      }
      /* 上沿渐隐：y0 全透 → y1 */
      ctx.globalAlpha = 1;
      const m = ctx.createLinearGradient(0, S.y0, 0, S.y1);
      m.addColorStop(0, 'rgba(0,0,0,0)'); m.addColorStop(1, 'rgba(0,0,0,1)');
      ctx.globalCompositeOperation = 'destination-in';
      ctx.fillStyle = m; ctx.fillRect(0, 0, W, H);
      ctx.globalCompositeOperation = 'source-over';
      /* 日月：晕 +（日冕）+ 本体，跟着进度从下沿升起 */
      const O = C.orb, cy = O.y + O.sink * (1 - ease(lv)), hl = O.halo;
      const hg = ctx.createRadialGradient(O.x, cy, O.D * 0.45, O.x, cy, hl.R);
      hg.addColorStop(0, `rgba(${hl.rgb},${hl.a})`); hg.addColorStop(1, `rgba(${hl.rgb},0)`);
      ctx.fillStyle = hg; ctx.beginPath(); ctx.arc(O.x, cy, hl.R, 0, 6.2832); ctx.fill();
      if (O.corona) corona(ctx, O.x, cy);
      const pulse = O.pulse ? 1 + O.pulse * Math.sin(t * 2.2) : 1, D = O.D * pulse;
      ctx.drawImage(orb, O.x - D / 2, cy - D / 2, D, D);
      /* 纱和兔 / 金乌穿插：第 0 条纱在它们后面，其余在前面 */
      const RB = C.ribbons || [];
      if (RB[0]) ribbon(ctx, RB[0], 0);
      C.mobs.list.forEach((R, i) => mob(ctx, R, i));
      for (let i = 1; i < RB.length; i++) ribbon(ctx, RB[i], i);
      for (const mt of meteors) meteor(ctx, mt);
      ctx.restore();
      span.end(out, x0, x1);
    }
    /* 前沿迸的光点、火花不裁（同 Tide 的飞沫）：飞到对面那片上头、飘进客厅也是它的一部分 */
    for (const list of [sparks, embers]) for (const p of list) {
      const u = p.t / p.life, r = p.r * (1 + 0.5 * u);
      out.globalAlpha = u < 0.15 ? u / 0.15 : 1 - (u - 0.15) / 0.85;
      out.drawImage(dot, p.x - r, p.y - r, 2 * r, 2 * r);
    }
    out.globalAlpha = 1;
  }

  /* 出场视频放完（intro.js → main.js）：直接铺满、日月已升起（视频底部那片接过来） */
  function handoff() { lv = 1; }
  return { init, load, update, draw, reset, handoff, active: () => lv > 0, level: () => ease(lv), edgeY: () => C.sky.y1, dotImg: () => dot, side: C.side };
}

const MoonSky = Sky({
  side: -1, rise: 1.4, fall: 1.4,
  dot: ['rgba(255,255,255,1)', 'rgba(215,228,255,0.85)', 'rgba(150,170,255,0)'],
  /* 夜空：y0 全透 → y1 不透明，往下 top 色渐到 bot 色（竖向渐隐也管星带和星星） */
  sky: { y0: 1175, y1: 1238, top: [14, 18, 58], bot: [38, 22, 78], a: 0.93 },
  /* 星带：贴图缩放 k，中线在屏幕正中过 y，斜 tilt（负 = 往右上抬），往右流 v px/s */
  band: { src: 'assets/world/moonsky_galaxy.webp', k: 0.8, y: 1300, tilt: -0.07, v: 22 },
  /* 明月：直径 D，圆心 (x, y)，没升起时往下沉 sink；月晕半径 R、颜色、不透明度 */
  orb: { src: 'assets/world/moonsky_moon.webp', D: 300, x: 125, y: 1338, sink: 300, halo: { R: 270, rgb: [200, 214, 255], a: 0.5 } },
  stars: { n: 90, big: 9 },                          // 满天小星几颗、其中带十字芒的几颗
  dust: { n: 80, v: [25, 80], band: 60, r: [1.5, 3.5] },   // 星尘：沿星带往右流，离中线 ±band
  /* 薄纱：一条条有头有尾的纱往右飘（头走到 W + len 再从左边画外重来）；y 中线、A 波幅、L 波长、v 走速、len 长、w 宽、tw 翻面周期、颜色、亮边 */
  ribbons: [
    { y: 1262, A: 16, L: 460, v: 46, len: 620, w: 30, tw: 210, x: 0.2, rgb: [196, 178, 255], a: 0.34 },
    { y: 1318, A: 22, L: 560, v: 34, len: 760, w: 38, tw: 260, x: 0.75, rgb: [176, 196, 255], a: 0.3 },
    { y: 1290, A: 14, L: 400, v: 58, len: 520, w: 24, tw: 180, x: 0.45, rgb: [226, 194, 255], a: 0.32 },
  ],
  /* 玉兔：贴图 k（0 抱药杵 / 1 提灯笼 / 2 蜷着睡 / 3 张开手脚）、开场 x（屏宽几成）、y、往右漂 v、缩放 s、spin（整圈慢慢翻 rad/s，0 = 只左右摆） */
  mobs: {
    src: (k) => `assets/world/moonsky_rabbit${k + 1}.webp`,
    list: [
      { k: 0, x: 0.12, y: 1262, v: 30, s: 0.72, spin: 0 },
      { k: 1, x: 0.4, y: 1300, v: 24, s: 0.8, spin: 0 },
      { k: 2, x: 0.66, y: 1250, v: 36, s: 0.62, spin: 0.5 },
      { k: 3, x: 0.9, y: 1292, v: 28, s: 0.76, spin: -0.35 },
    ],
  },
  front: { every: 0.014 },                           // 推进 / 退回时前沿每隔几秒迸一颗星光
});

/* 烈日火空：嫦娥那片左右镜像 —— 烈日在右下、火焰云带往左上抬（tilt 正）、往左流（v 负）、金乌往左飞 */
const SunSky = Sky({
  side: +1, rise: 1.4, fall: 1.4,
  dot: ['rgba(255,255,225,1)', 'rgba(255,190,60,0.9)', 'rgba(255,80,10,0)'],
  sky: { y0: 1175, y1: 1238, top: [70, 12, 8], bot: [120, 36, 6], a: 0.93 },
  /* 火焰云带：很满、很亮，压到 0.8 */
  band: { src: 'assets/world/sunsky_fire.webp', k: 0.72, y: 1305, tilt: 0.07, v: -26, a: 0.8 },
  /* 烈日：同明月的摆法（右下角）；corona 日冕 n 道、伸出 len、张角 w、转速；pulse 日面一胀一缩 */
  orb: { src: 'assets/world/sunsky_sun.webp', D: 330, x: 835, y: 1340, sink: 320, pulse: 0.02,
         halo: { R: 300, rgb: [255, 170, 60], a: 0.55 },
         corona: { n: 18, len: 110, w: 0.07, spin: 0.12, rgb: [255, 196, 80], a: 0.45 } },
  /* 火花：每秒 rate 颗，nearOrb 成从烈日附近冒，其余满屏；从 y 区间往上 v 飞 */
  embers: { rate: 34, nearOrb: 0.45, y: [1260, 1420], v: [90, 240], life: [0.8, 1.6], r: [2, 4.5] },
  /* 陨石：隔 every 秒一颗，速度 v、方向 ang（从右上往左下）、石头半径 r、火尾长 tail × r、落到 floor 炸 burst 颗火星 */
  meteors: { every: [0.5, 1.2], v: [380, 560], ang: Math.PI * 0.8, r: [7, 12], tail: 14, floor: 1400, burst: 8,
             rock: [70, 30, 20], rim: [255, 170, 60], trail: [[3.2, [255, 90, 20], 0.5], [1.8, [255, 200, 80], 0.7], [0.8, [255, 250, 220], 0.9]] },
  /* 三足金乌：v14/tides 的四只（朝左），往左飞；flap 扇翅频率 */
  mobs: {
    src: (k) => `assets/world/tide_sun_crow${k + 1}.webp`,
    list: [
      { k: 0, x: 0.1, y: 1255, v: -48, s: 0.62, spin: 0, flap: 9 },
      { k: 1, x: 0.38, y: 1300, v: -40, s: 0.72, spin: 0, flap: 8 },
      { k: 2, x: 0.62, y: 1248, v: -56, s: 0.55, spin: 0, flap: 10 },
      { k: 3, x: 0.88, y: 1295, v: -44, s: 0.68, spin: 0, flap: 8.5 },
    ],
  },
  front: { every: 0.012 },
});
