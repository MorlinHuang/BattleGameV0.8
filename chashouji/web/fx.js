/* fx.js —— 粒子与打击感
 *
 * 全部特效走同一个粒子池 + 预渲染贴图。这台机器没有 GPU（软渲染），所以
 * 避开 shadowBlur / filter / 每帧 createRadialGradient —— 光斑一次性烘到离屏
 * canvas，之后只 drawImage。
 *
 * 这里只有"怎么画"，没有"画什么"：具体某件礼物炸出羽毛还是星星，由 main.js
 * 的配方表决定。粒子形态刻意留成通用的六种，换题材皮不用动这个文件。
 *
 * 打击感的四个手段都不需要改角色帧素材 —— 角色是预渲染帧，做不了受击变形，
 * 但顿帧、震屏、白闪、角色被推开与染色都作用在贴图之外（受击不缩放人，见 main.js PoseView）：
 *   hitStop  命中瞬间冻住整个世界几十毫秒，打击感有一半来自这个
 *   shake    屏幕震动
 *   flash    全屏白闪
 */
'use strict';

/* FxShape —— 去几何图元的矢量画法（精特3，2026-10-01）。
   用户看正式页："光晕的圆圈、弧形的特效，太规整不自然，一看就是代码的产物"。正圆 / 正椭圆描边、等宽直线、规整弧带
   都换成同一套思路（精特1b A 方案的矢量版，不要贴图，随 fx.js 一起到、首帧就能用）：
     · 轮廓用几道不公约的谐波扰动（角向 / 沿长度），谐波的相位按种子定、随时间慢慢漂 —— 不圆、不直、每一下都不一样，动起来不重复；
     · 宽度也按谐波起伏，越老越多地方宽度掉到 0 = 断成一截截两头收尖的弧段（"笔触"，不是描边）；
     · 冲击波两道波前错开（主波 + 内侧一道细的余波）。
   种子由调用方给（同一下炸出来的"深色托底 + 亮色"两圈要同形，见 Particles ring 的 shapeSeed）。全部只填充多边形，不用 shadow / filter。 */
const FxShape = (() => {
  const TAU = 6.283185307179586;
  function rng(seed) {                                    // mulberry32
    let a = seed >>> 0;
    return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  const hash = (...v) => { let h = 2166136261; for (const x of v) { h ^= Math.round(x) | 0; h = Math.imul(h, 16777619); } return h >>> 0; };
  /* 一组谐波：[频率, 振幅, 相位, 漂移速度] × 4。角向用整数频率（绕一圈首尾接得上），沿长度的用非整数 */
  function harm(seed, ks = [2, 3, 5, 8]) {
    const r = rng(seed), H = [];
    for (let i = 0; i < ks.length; i++) H.push(ks[i], [1, 0.6, 0.42, 0.28][i], r() * TAU, (r() - 0.5) * 3.2);
    H.rot = r() * TAU;
    return H;
  }
  const n = (H, x, t, sh = 0) => {                          // −1..1
    let v = 0;
    for (let i = 0; i < H.length; i += 4) v += H[i + 1] * Math.sin(H[i] * x + H[i + 2] + sh * (i + 1) + H[i + 3] * t);
    return v / 2.3;
  };
  const sstep = (e0, e1, x) => { const k = Math.min(1, Math.max(0, (x - e0) / (e1 - e0))); return k * k * (3 - 2 * k); };

  /* 一道波前：半径 R（y 压 sq）、最宽 w；thr 越大断得越多（≤ −0.2 基本不断），null = 一整圈不断（只起伏）。宽度 = w × 包络，包络在断口两侧平滑收到 0 */
  function front(ctx, x, y, R, sq, w, thr, t, H, sh, wob = 0.11) {
    const N = Math.max(28, Math.min(84, Math.round(R * 0.45)));
    const ox = new Float32Array(N), oy = new Float32Array(N), ix = new Float32Array(N), iy = new Float32Array(N), on = new Uint8Array(N);
    let any = 0, gap = -1;
    for (let i = 0; i < N; i++) {
      const a = i / N * TAU, th = a + H.rot;
      const rr = R * (1 + wob * n(H, a, t, sh)), m = 0.5 + 0.5 * n(H, a, t * 0.7, sh + 1.9);
      const k = thr == null ? 1 : sstep(thr, thr + 0.22, m), hw = w * 0.5 * k * (0.55 + 0.9 * m);
      on[i] = hw > 0.25; if (on[i]) any = 1; else if (gap < 0) gap = i;
      const c = Math.cos(th), s = Math.sin(th);
      ox[i] = x + c * (rr + hw); oy[i] = y + s * (rr + hw) * sq; ix[i] = x + c * (rr - hw); iy[i] = y + s * (rr - hw) * sq;
    }
    if (!any) return;
    ctx.beginPath();
    if (gap < 0) {                                         // 一整圈没断：外圈 + 内圈反向，evenodd 掏空
      for (let i = 0; i < N; i++) i ? ctx.lineTo(ox[i], oy[i]) : ctx.moveTo(ox[i], oy[i]);
      ctx.closePath();
      ctx.moveTo(ix[N - 1], iy[N - 1]); for (let i = N - 2; i >= 0; i--) ctx.lineTo(ix[i], iy[i]);
      ctx.closePath(); ctx.fill('evenodd'); return;
    }
    for (let j = 1, run = []; j <= N; j++) {               // 从一个断口开始绕一圈，按连续的"有"切成段
      const i = (gap + j) % N;
      if (on[i]) run.push(i);
      if ((!on[i] || j === N) && run.length) {
        if (run.length > 1) {
          ctx.moveTo(ox[run[0]], oy[run[0]]);
          for (const q of run) ctx.lineTo(ox[q], oy[q]);
          for (let q = run.length - 1; q >= 0; q--) ctx.lineTo(ix[run[q]], iy[run[q]]);
          ctx.closePath();
        }
        run = [];
      }
    }
    ctx.fill();
  }
  /* 冲击波：主波 + 内侧余波（0.78 R、细一半、断得更早）。u 0..1 = 年龄（越老断得越多），t 秒（谐波漂移） */
  function ring(ctx, x, y, r, sq, w, u, t, H) {
    front(ctx, x, y, r, sq, w, 0.75 * u - 0.12, t, H, 0);   // 前三成寿命基本连着（命中那一下要读得出"一圈"），之后越来越碎
    const A = ctx.globalAlpha;
    ctx.globalAlpha = A * 0.6;
    front(ctx, x, y, r * 0.78, sq, w * 0.55, 0.1 + 0.7 * u, t, H, 2.7);
    ctx.globalAlpha = A;
  }
  /* 速度线 / 火花：尾 (x0, y0) 收尖 → 头 (x1, y1) 圆头宽 w。替换 lineCap round 的等宽直线 */
  function streak(ctx, x0, y0, x1, y1, w) {
    const dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy) || 1, nx = -dy / L * w / 2, ny = dx / L * w / 2, a = Math.atan2(dy, dx);
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1 + nx, y1 + ny); ctx.arc(x1, y1, w / 2, a + Math.PI / 2, a - Math.PI / 2, true); ctx.closePath(); ctx.fill();
  }
  /* 不规则斑块路径（调用方 fill / stroke）：10 个顶点按谐波推拉、二次曲线连 */
  function blob(ctx, x, y, r, seed) {
    const H = harm(seed, [2, 3, 4, 7]), K = 10, P = [];
    for (let i = 0; i < K; i++) { const a = i / K * TAU; P.push([x + Math.cos(a + H.rot) * r * (1 + 0.22 * n(H, a, 0)), y + Math.sin(a + H.rot) * r * (1 + 0.22 * n(H, a, 0))]); }
    ctx.beginPath();
    for (let i = 0; i <= K; i++) {
      const p = P[i % K], q = P[(i + 1) % K], mx = (p[0] + q[0]) / 2, my = (p[1] + q[1]) / 2;
      i ? ctx.quadraticCurveTo(p[0], p[1], mx, my) : ctx.moveTo(mx, my);
    }
    ctx.closePath();
  }
  /* 弧形刀光（替换 trio.js drawSlash）：s { t, p, ang, flip }、Q = A.slash { len, w, color, life }。
     同旧的接口和节奏：0.07 s 从弦的一头划到另一头、后半寿命淡出；层次同旧（深色托底 → 外晕 → 本色 → 白芯）。
     改的是形：中线半径沿弧起伏、宽度两头收尖且沿弧鼓瘪不匀、划过去的前沿是一条更尖的舌头；后半寿命从两头往中间断成碎段（碎散），
     外侧多拖两缕细丝（拉丝）。种子取 s.ang（每道随机），同一道每帧同形 */
  const SLASH_L = (c) => [[1.35, 'rgba(15,30,70,.55)'], [2.2, `rgba(${c[0]},${c[1]},${c[2]},.35)`], [1, `rgba(${c[0]},${c[1]},${c[2]},.95)`], [0.35, 'rgba(255,255,255,1)']];
  function slash(ctx, s, Q) {
    if (s.t < 0 || !s.p) return;
    const c = Q.color, R = Q.len / 2, life = Q.life || 0.45, dr = Math.min(1, s.t / 0.07), fade = Math.min(1, (life - s.t) / (life * 0.5));
    if (fade <= 0) return;
    const H = harm(hash(s.ang * 1e4, 7), [1.7, 2.9, 4.3, 7.1]), u = s.t / life, brk = Math.max(0, (u - 0.45) / 0.55);
    const a0 = -0.9, span = 1.8, M = 26;
    ctx.save(); ctx.translate(s.p[0], s.p[1]); ctx.rotate(s.ang); ctx.scale(1, s.flip || 1); ctx.globalAlpha *= fade;   // 乘调用方的透明度（剑气飞行段的残影要淡）
    const cy = R * 0.4, pt = (f, off) => { const a = a0 + span * f - Math.PI / 2, rr = R * (1 + 0.07 * n(H, f * 3, s.t * 2)) + off; return [Math.cos(a) * rr, cy + Math.sin(a) * rr]; };
    for (const [wk, col] of SLASH_L(c)) {
      ctx.fillStyle = col; ctx.beginPath();
      let open = false; const inner = [];
      const flush = () => { if (open) { for (let q = inner.length - 1; q >= 0; q--) ctx.lineTo(inner[q][0], inner[q][1]); ctx.closePath(); } open = false; inner.length = 0; };
      for (let i = 0; i <= M; i++) {
        const f = i / M * dr;
        /* 宽：两头收尖（sin^0.7）× 沿弧鼓瘪 × 前沿舌头（离划到的那一点越近越尖）× 碎散（谐波低于阈值的地方断开，从两头先断） */
        const env = Math.pow(Math.sin(Math.PI * f), 0.7) * (dr >= 1 ? 1 : Math.min(1, (dr - f) / 0.12));
        const m = 0.5 + 0.5 * n(H, f * 5, 0, 1.3), cut = brk > 0 ? sstep(brk * 0.9 + Math.abs(f - 0.5) * brk, brk * 0.9 + Math.abs(f - 0.5) * brk + 0.18, m) : 1;
        const hw = Q.w * wk * 0.62 * env * (0.7 + 0.6 * m) * cut;
        if (hw < 0.3) { flush(); continue; }
        const o = pt(f, hw), q = pt(f, -hw * 0.6);             // 月牙：往外鼓得多、内沿收得少（同旧"内弧往里收"）
        if (!open) { ctx.moveTo(o[0], o[1]); open = true; } else ctx.lineTo(o[0], o[1]);
        inner.push(q);
      }
      flush(); ctx.fill();
    }
    /* 拉丝：外侧两缕细丝，比刀光晚一点划到、先断 */
    ctx.fillStyle = `rgba(${c[0]},${c[1]},${c[2]},.8)`;
    for (const k of [1, 2]) {
      const off = Q.w * (0.75 + 0.55 * k), f0 = 0.15 * k, f1 = Math.min(dr, 1) * (1 - 0.1 * k) - brk * 0.5;
      if (f1 - f0 < 0.05) continue;
      ctx.beginPath();
      const L = [];
      for (let i = 0; i <= 12; i++) { const f = f0 + (f1 - f0) * i / 12, hw = Q.w * 0.09 * Math.sin(Math.PI * i / 12) * (1 + 0.5 * n(H, f * 7, s.t, k)); L.push([pt(f, off + hw), pt(f, off - hw)]); }
      L.forEach(([o], i) => (i ? ctx.lineTo(o[0], o[1]) : ctx.moveTo(o[0], o[1])));
      for (let i = L.length - 1; i >= 0; i--) ctx.lineTo(L[i][1][0], L[i][1][1]);
      ctx.closePath(); ctx.fill();
    }
    ctx.restore();
  }
  /* 波动的光带（替换"四层同宽直线"的光束）：O → E，每层 [宽倍数, rgb, 不透明度]，中线横向三频波往前传（两头钉住）、宽度沿长度脉动、
     出口胀一点；每层相位错开（不同心）。env 0..1 整体粗细 */
  function wavyBand(ctx, O, E, W, layers, t, seed) {
    const dx = E[0] - O[0], dy = E[1] - O[1], L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L, N = Math.max(6, Math.ceil(L / 28));
    const H = harm(seed, [1.3, 2.7, 4.9, 8.3]), amp = Math.min(22, W * 0.35 + 3);
    layers.forEach(([k, rgb, a], li) => {
      const up = [], dn = [];
      for (let i = 0; i <= N; i++) {
        const f = i / N, d = f * L, env = Math.sin(Math.PI * Math.min(1, f * 1.6)) ** 0.5 * (1 - 0.4 * f);
        const o = amp * env * n(H, f * 4, t * 9, li * 0.7), hw = W * k * 0.5 * (1 + 0.35 * Math.exp(-d / 50)) * (1 + 0.14 * n(H, f * 9, t * 14, li + 2));
        const cx = O[0] + ux * d - uy * o, cy = O[1] + uy * d + ux * o;
        up.push([cx - uy * hw, cy + ux * hw]); dn.push([cx + uy * hw, cy - ux * hw]);
      }
      ctx.fillStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`; ctx.beginPath();
      up.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
      for (let i = dn.length - 1; i >= 0; i--) ctx.lineTo(dn[i][0], dn[i][1]);
      ctx.closePath(); ctx.fill();
    });
  }
  /* —— 档 4 的光（精特4，2026-10-04，用户："4 档除视频之外的特效，周围的光晕、天使的头环、光环这类代码做的特效都比较粗糙，
     不要那么硬的直线或者标准的圆，要更像设定中的效果"）—— */
  const HC = new Map();
  const harmOf = (seed) => { let H = HC.get(seed); if (!H) { H = harm(seed); HC.set(seed, H); } return H; };
  const rgba = (c, a) => `rgba(${c[0]},${c[1]},${c[2]},${Math.max(0, a).toFixed(3)})`;
  /* 身后的一团光（替换"一个正圆径向渐变"）：三团错开的光叠成一片，各自绕中心慢慢漂、胀缩、拉长转向 —— 等亮线不是同心圆，
     读成一团在呼吸的云气。core 亮芯色、rgb 光色、a 中心不透明度（三团叠起来约等于原来一团的 a）；sq 纵向压扁；
     lobes 几片（本身就是一大片里的一小团的，如恶魔身后九团烟里的一团，给 1：一片拉长、慢慢转的光，已经不圆，填充只要三分之一） */
  function glow(ctx, x, y, R, core, rgb, a, t, seed, sq = 1, lobes = 3) {
    const H = harmOf(seed);
    for (let i = 0; i < lobes; i++) {
      const ph = i * 2.1, wgt = lobes === 1 ? 0.9 : [0.55, 0.38, 0.3][i];
      const ox = R * 0.14 * n(H, ph, t * 0.35), oy = R * 0.11 * n(H, ph + 1.3, t * 0.3);
      const r = R * (0.62 + 0.12 * i + 0.08 * n(H, ph + 2.6, t * 0.5)), st = 1 + 0.2 * n(H, ph + 3.1, t * 0.25);
      ctx.save();
      ctx.translate(x + ox, y + oy); ctx.rotate(H.rot + i * 1.1 + 0.3 * n(H, ph + 4, t * 0.2)); ctx.scale(st, sq / st);
      const g = ctx.createRadialGradient(0, 0, 0, 0, 0, r);
      g.addColorStop(0, rgba(core, a * wgt)); g.addColorStop(0.4, rgba(rgb, a * wgt * 0.55)); g.addColorStop(1, rgba(rgb, 0));
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.fill();   // 只填圆：外接方框的四角全透明，软渲染下白填 27% 像素
      ctx.restore();
    }
  }
  /* 放射的光芒（替换"一圈等宽直三角"）：每道是一束从根往外张开、微微弯、长短粗细各自一闪一闪的光；角度不等分（出生时各抖一点）、
     各自慢慢漂。三遍由宽到窄、由淡到亮叠出来 —— 边是软的，不是一刀切的三角；末端不收尖，靠渐变淡出去
     （第一版两头收尖，一道道细针，用户要的"不硬"反而更像直线）。
     n 几道、r0 → r1 从多远到多远、w 每道半张角（rad）、spin 整体转速 */
  const RAYS = new Map();
  function rays(ctx, x, y, nn, r0, r1, w, rgb, a, t, spin, seed) {
    const H = harmOf(seed);
    let P = RAYS.get(seed + ':' + nn);
    if (!P) {
      const r = rng(seed * 7 + 1); P = [];
      for (let i = 0; i < nn; i++) P.push({ a: (i + (r() - 0.5) * 0.7) / nn * TAU, w: 0.55 + 0.9 * r(), L: 0.78 + 0.22 * r(), f: 1.2 + 2.2 * r(), ph: r() * TAU, c: (r() - 0.5) * 0.5 });
      RAYS.set(seed + ':' + nn, P);
    }
    const M = 7;
    /* 亮度：三层叠起来，伸出人身外那一段（半径 0.4~0.8）跟原来一整块三角差不多亮 —— 第一版每层 0.22 / 0.4 / 0.7、渐变 0.45 处就掉一半，
       光柱又只伸到 0.6~1 倍，露在人外面的部分只剩一成多，整圈光芒等于没了 */
    for (const [wk, ak] of [[1.7, 0.3], [1.0, 0.5], [0.45, 0.8]]) {
      const g = ctx.createRadialGradient(x, y, r0 * 0.5, x, y, r1);
      g.addColorStop(0, rgba(rgb, a * ak)); g.addColorStop(0.6, rgba(rgb, a * ak * 0.55)); g.addColorStop(1, rgba(rgb, 0));
      ctx.fillStyle = g; ctx.beginPath();
      P.forEach((p, i) => {
        const fl = 0.5 + 0.5 * Math.sin(t * p.f + p.ph), a0 = p.a + t * spin + 0.06 * n(H, i * 1.7, t * 0.4);
        const L = r0 + (r1 - r0) * p.L * (0.85 + 0.15 * fl), hw = w * p.w * wk * (0.65 + 0.35 * fl);
        const side = (sg) => {
          const pts = [];
          for (let j = 0; j <= M; j++) {
            const f = j / M, d = r0 + (L - r0) * f, env = 0.3 + 0.7 * Math.sqrt(f);       // 根窄、往外张开
            const ang = a0 + p.c * f * f * w * 3 + sg * hw * env;
            pts.push([x + Math.cos(ang) * d, y + Math.sin(ang) * d]);
          }
          return pts;
        };
        const A = side(1), B = side(-1);
        ctx.moveTo(A[0][0], A[0][1]); for (const q of A) ctx.lineTo(q[0], q[1]);
        for (let j = B.length - 1; j >= 0; j--) ctx.lineTo(B[j][0], B[j][1]);
        ctx.closePath();
      });
      ctx.fill();
    }
  }
  /* 光环（替换"一条正圆 / 正椭圆描边"）：笔触式的一圈 —— 粗细沿圈起伏、轮廓轻轻颤（wob 3%）；外一层宽而淡的柔光、
     中间一层本色、最里一道细亮芯（芯会断开几处，像高光不是描边）；两颗闪光沿着环绕圈走。sq 纵向压扁（头顶的天使环 ≈ 0.26，头后光轮 1） */
  function halo(ctx, x, y, R, sq, lw, edge, rgb, core, a, t, seed) {
    const H = harmOf(seed);
    ctx.fillStyle = rgba(rgb, 0.22 * a); front(ctx, x, y, R, sq, lw * 3.2, null, t * 0.5, H, 0, 0.03);
    ctx.fillStyle = rgba(edge, 0.62 * a); front(ctx, x, y, R, sq, lw * 1.6, null, t * 0.5, H, 0, 0.03);
    ctx.fillStyle = rgba(rgb, 0.95 * a); front(ctx, x, y, R, sq, lw * 1.05, null, t * 0.5, H, 0, 0.03);
    ctx.fillStyle = rgba(core, 0.95 * a); front(ctx, x, y, R, sq, lw * 0.5, -0.05, t * 0.8, H, 1.7, 0.03);
    for (let k = 0; k < 2; k++) {
      const th = t * (0.7 + 0.25 * k) + k * Math.PI + H.rot, px = x + Math.cos(th) * R, py = y + Math.sin(th) * R * sq;
      const tw = 0.55 + 0.45 * Math.sin(t * 5.3 + k * 2), L = lw * (2.2 + 1.2 * tw);
      ctx.fillStyle = rgba(core, a * tw);
      for (let q = 0; q < 4; q++) {
        const aa = q * Math.PI / 2 + 0.4, ll = L * (q % 2 ? 0.6 : 1);
        streak(ctx, px + Math.cos(aa) * ll, py + Math.sin(aa) * ll, px, py, lw * 0.7);
      }
    }
  }
  /* 一道裂光 / 电弧（替换"等宽折线"）：从 (x0, y0) 沿 ang 往外 len，折点按 seed 抖、每 1/8 秒重新抖一次（劈啪地闪），
     宽 w 从根到尖收细；返回路径由调用方 fill（两遍：宽的暗托底、细的亮芯） */
  function bolt(ctx, x0, y0, ang, len, w, seed, t) {
    const r = rng(hash(seed, Math.floor(t * 8))), K = 6, L = [], Rr = [];
    let px = x0, py = y0, a = ang;
    for (let i = 0; i <= K; i++) {
      const f = i / K, hw = w * 0.5 * (1 - f * 0.85), nx = -Math.sin(a), ny = Math.cos(a);
      L.push([px + nx * hw, py + ny * hw]); Rr.push([px - nx * hw, py - ny * hw]);
      a = ang + (r() - 0.5) * 1.1; const d = len / K * (0.7 + 0.6 * r());   // 每一折都相对总方向偏（不累积），整道不会弯出去
      px += Math.cos(a) * d; py += Math.sin(a) * d;
    }
    ctx.beginPath(); ctx.moveTo(L[0][0], L[0][1]);
    for (const q of L) ctx.lineTo(q[0], q[1]);
    ctx.lineTo(px, py);
    for (let i = Rr.length - 1; i >= 0; i--) ctx.lineTo(Rr[i][0], Rr[i][1]);
    ctx.closePath();
  }
  /* 喷口焰 / 爆光（替换"规整的 16 角星"）：长短不一的尖芒（每帧长短都跳）+ 不规则的亮芯斑块 */
  function burst(ctx, x, y, r, t, seed, spikes = 7) {
    const H = harmOf(seed);
    for (let i = 0; i < spikes; i++) {
      const a = (i + 0.35 * n(H, i * 2.3, 0)) / spikes * TAU + t * 0.8, L = r * (0.55 + 0.45 * (0.5 + 0.5 * n(H, i * 1.9, t * 9)));
      streak(ctx, x + Math.cos(a) * L, y + Math.sin(a) * L, x, y, r * 0.32);
    }
    blob(ctx, x, y, r * 0.42, hash(seed, Math.floor(t * 18))); ctx.fill();
  }
  /* 一团雾（替换雾锥里每颗粒子的正圆，精特4）：16 种预先算好的不规则轮廓（10 个顶点按谐波推拉、二次曲线连），按 k 取、转 rot —— 每帧不分配。
     雾锥几百团叠在一起，正圆的话边上是一圈圈规整的弧，读成"一堆圆"；换成团状轮廓、随寿命慢慢翻转，读成一股往外翻滚的雾 */
  const PUFF = Array.from({ length: 16 }, (_, k) => {
    const H = harm(9000 + k, [2, 3, 4, 7]), P = [];
    for (let i = 0; i < 10; i++) { const a = i / 10 * TAU, rr = 1 + 0.2 * n(H, a, 0); P.push([Math.cos(a) * rr, Math.sin(a) * rr]); }
    return P;
  });
  function puff(ctx, x, y, r, k, rot) {
    const P = PUFF[k & 15], c = Math.cos(rot) * r, sn = Math.sin(rot) * r;
    const X = (p) => x + p[0] * c - p[1] * sn, Y = (p) => y + p[0] * sn + p[1] * c;
    ctx.beginPath();
    for (let i = 0; i <= 10; i++) {
      const p = P[i % 10], q = P[(i + 1) % 10], mx = (X(p) + X(q)) / 2, my = (Y(p) + Y(q)) / 2;
      i ? ctx.quadraticCurveTo(X(p), Y(p), mx, my) : ctx.moveTo(mx, my);
    }
    ctx.closePath();
  }
  return { rng, hash, harm, n, ring, front, streak, blob, slash, wavyBand, glow, rays, halo, bolt, burst, puff };
})();

/* 聊天气泡图标（真相喷雾：雾里飘的、命中时从男生脸上蹦出来的"被翻出来的聊天记录"）。
   以 (0,0) 为中心、半宽 r：圆角框 + 左下一个小尾巴 + 三个点。粒子（kind 'chat'）和 crew.js 的雾共用这一个画法。
   描边是实体靠轮廓那条规矩：白框在浅绿墙上不描边就化掉。 */
function drawChatIcon(ctx, r, fill, line, lw, dot) {
  const w = r * 2, h = r * 1.4, x = -r, y = -h / 2, c = h * 0.42;
  ctx.beginPath();
  ctx.moveTo(x + c, y); ctx.lineTo(x + w - c, y); ctx.quadraticCurveTo(x + w, y, x + w, y + c);
  ctx.lineTo(x + w, y + h - c); ctx.quadraticCurveTo(x + w, y + h, x + w - c, y + h);
  ctx.lineTo(x + r * 0.62, y + h); ctx.lineTo(x + r * 0.18, y + h + r * 0.5); ctx.lineTo(x + r * 0.34, y + h);   // 尾巴
  ctx.lineTo(x + c, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - c);
  ctx.lineTo(x, y + c); ctx.quadraticCurveTo(x, y, x + c, y);
  ctx.closePath();
  ctx.fillStyle = fill; ctx.fill();
  if (line) { ctx.lineWidth = lw; ctx.strokeStyle = line; ctx.stroke(); }
  ctx.fillStyle = dot;
  for (let i = -1; i <= 1; i++) { ctx.beginPath(); ctx.arc(i * r * 0.5, 0, r * 0.16, 0, 6.283); ctx.fill(); }
}

const Particles = (function () {
  const MAX = 1200;
  const act = [];            // 活跃粒子
  const pool = [];           // 回收池，避免每帧 new

  let shake = 0;             // 屏幕震动强度（像素）
  let flash = 0;             // 全屏白闪 0..1
  let stop = 0;              // 顿帧剩余时长（秒）
  let cool = 0;              // 顿帧不应期剩余：这段时间里只接受更重的一击
  let lvl = 0;               // 正在演的这次顿帧有多重，用来判断谁能打断谁
  const off = { x: 0, y: 0 };   // 当前震动偏移，main.js 读它来平移整个画面

  /* ---------- 预渲染贴图 ---------- */

  const glowCache = new Map();
  function glow(rgb) {
    const key = rgb[0] + ',' + rgb[1] + ',' + rgb[2];
    let c = glowCache.get(key);
    if (c) return c;
    const S = 128;
    c = document.createElement('canvas');
    c.width = c.height = S;
    const g = c.getContext('2d');
    const rg = g.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S / 2);
    rg.addColorStop(0.00, 'rgba(255,255,255,1)');
    rg.addColorStop(0.22, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0.95)`);
    rg.addColorStop(0.55, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0.35)`);
    rg.addColorStop(1.00, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
    g.fillStyle = rg;
    g.fillRect(0, 0, S, S);
    glowCache.set(key, c);
    return c;
  }

  /* 绒絮用普通混合、先于亮部画。全走 lighter 会让它显得飘、没有体积 ——
     羽毛和灰尘是实体，不是光。 */
  const softCache = new Map();
  function soft(rgb) {
    const key = rgb[0] + ',' + rgb[1] + ',' + rgb[2];
    let c = softCache.get(key);
    if (c) return c;
    const S = 96;
    c = document.createElement('canvas');
    c.width = c.height = S;
    const g = c.getContext('2d');
    const rg = g.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S / 2);
    rg.addColorStop(0.0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0.9)`);
    rg.addColorStop(0.5, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0.42)`);
    rg.addColorStop(1.0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
    g.fillStyle = rg;
    g.fillRect(0, 0, S, S);
    softCache.set(key, c);
    return c;
  }

  /* ---------- 3D 渲出来的实体粒子贴图 ---------- */

  /* 实体粒子原先是现场画的几何：圆角胶囊当碎片、五角星路径、矩形当照片。
     它们在画面上就是一个纯色形状在平移 —— 没有厚度，光影也无从谈起。
     换成 Blender 渲的转盘之后，每一颗都带硬边二分的明暗和自己的描边，
     翻滚时能看到正面转到侧面再转到背面。"有体积感"就是这个差别。

     **贴图一律渲成白色。** 粒子颜色是配方在 spawn 时逐颗定的（羽毛五颗里有
     一颗偏粉、碎片按 `dark` 分两种深浅），烧死在贴图里配方就没法再调色了。
     运行时用 multiply 把目标色乘上去：亮面变成目标色本身，暗面变成它的暗调，
     二分光影原样保留。描边也因此不能用角色线稿那个暖黑 —— 乘完会黑死，
     素材那边已经改成浅两档的 5a4a42。

     `scale` 补偿裁剪留白（图集按所有角度的并集裁，单帧填不满一格），
     跟 ammo.js 的 SPRITE 是同一套账。这些数字由 tools/3d/pack_atlas.py 打印。 */
  /* scale 这里是**实测调出来的绘制倍率**，跟 ammo.js 那边不一样。
     物品的模型都按"主体直径 2.0 单位"建，pack_atlas 算出来的 scale 直接能用；
     粒子里有细长件（羽毛长宽 1:2.2），它在正方形格子里只占一半宽度，
     照算出来的倍率画就比矢量版细一圈、在画面上碎成一片瓜子壳。
     所以细长的那几个手工放大过，末尾标了算出来的原值。 */
  const SHAPE = {
    petal:   { src: 'assets/fx/petal_atlas.webp',   n: 12, cols: 6, cell: 80, scale: 1.15 },
    feather: { src: 'assets/fx/feather_atlas.webp', n: 12, cols: 6, cell: 80, scale: 1.40 },  // 算出来 1.03
    debris:  { src: 'assets/fx/debris_atlas.webp',  n: 12, cols: 6, cell: 80, scale: 1.00 },  // 算出来 0.83
    star:    { src: 'assets/fx/star_atlas.webp',    n: 12, cols: 6, cell: 80, scale: 1.22 },
    heart:   { src: 'assets/fx/heart_atlas.webp',   n: 12, cols: 6, cell: 80, scale: 1.24 },
    card:    { src: 'assets/fx/card_atlas.webp',    n: 12, cols: 6, cell: 80, scale: 1.31 },
    // 珍珠是个球，绕哪个轴转轮廓都一样，4 帧只是让明暗交界有一点挪动
    pearl:   { src: 'assets/fx/pearl_atlas.webp',   n: 4,  cols: 6, cell: 80, scale: 1.09 },
  };

  /* ?nosprite=1 连粒子贴图一起关掉，退回矢量画法。两条路都要留着：
     加载失败要能退，跟转盘版并排对比也要能退。 */
  function loadShapes(ver, off) {
    if (off) return Promise.resolve([]);
    const q = ver ? '?v=' + encodeURIComponent(ver) : '';
    return Promise.all(Object.keys(SHAPE).map((k) => new Promise((done) => {
      const sp = SHAPE[k], im = new Image();
      sp.key = k;
      im.onload = () => { sp.img = im; done(true); };
      im.onerror = () => done(false);     // 缺素材不阻塞，退回矢量画法
      im.src = sp.src + q;
    })));
  }

  const tintCache = new Map();
  function tinted(sp, rgb) {
    const key = sp.key + '|' + rgb[0] + ',' + rgb[1] + ',' + rgb[2];
    let c = tintCache.get(key);
    if (c) return c;
    c = document.createElement('canvas');
    c.width = sp.img.width; c.height = sp.img.height;
    const g = c.getContext('2d');
    g.drawImage(sp.img, 0, 0);
    g.globalCompositeOperation = 'multiply';
    g.fillStyle = `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
    g.fillRect(0, 0, c.width, c.height);
    /* multiply 把整块矩形都涂了，透明区的 alpha 也被抬成 1。
       再用 destination-in 拿原图的 alpha 把轮廓切回来。 */
    g.globalCompositeOperation = 'destination-in';
    g.drawImage(sp.img, 0, 0);
    /* 配方给的颜色是离散的（`i % 5 ? A : B` 这种写法），缓存条目本来就只有
       十来条。设个上限是防将来有人写连续随机色，别让离屏 canvas 无限长下去。 */
    if (tintCache.size > 48) tintCache.clear();
    tintCache.set(key, c);
    return c;
  }

  // 当前朝向对应转盘的哪一格
  function shapeCell(sp, rot) {
    let k = Math.floor(rot / 6.2832 * sp.n) % sp.n;
    if (k < 0) k += sp.n;
    return k;
  }

  /* ---------- 粒子 ---------- */

  /* kind 只有六种，都是形态而非题材：
       dot   光斑，会从 r 涨到 r1
       spark 沿速度方向的短亮线，速度越快拉得越长
       ring  扩散的涟漪（贴地看所以压扁；FxShape.ring：不圆、粗细不匀、越老断得越多、带一道余波）
       chip  翻滚的小片，羽毛/塑料碎/纸屑都用它
       star  五角星，会旋转、会缩小
       soft  绒絮，普通混合，用作灰尘与绒毛

     chip、star 和 heart 都吃 edge（描边色）。底图是明亮客厅，实体不描边就糊
     在浅绿墙和米色地板里 —— 这跟角色睡衣有线稿是同一个道理，赛璐璐风格
     里"看得见"靠的是轮廓不是亮度。发光那三种（dot/spark/ring）没有描边，
     它们本来就该是光。 */
  function spawn(o) {
    if (act.length >= MAX) return null;
    const p = pool.pop() || {};
    p.kind = o.kind; p.x = o.x; p.y = o.y;
    p.vx = o.vx || 0; p.vy = o.vy || 0;
    p.g = o.g || 0; p.drag = o.drag != null ? o.drag : 1;
    p.life = p.maxLife = o.life;
    p.r = o.r || 4; p.r1 = o.r1 != null ? o.r1 : p.r;
    p.rgb = o.rgb || [255, 255, 255];
    p.a = o.a != null ? o.a : 1;
    p.rot = o.rot || 0; p.vrot = o.vrot || 0;
    p.w = o.w || 0; p.h = o.h || 0;
    p.lw = o.lw || 3;
    p.edge = o.edge || null;   // 实体描边色，明亮底图上靠它把碎片从背景里拔出来
    p.spin = o.spin || 0;      // 绕出生点公转的半径，星星绕头转用
    p.sway = o.sway || 0;      // 横向摆幅，羽毛飘落用
    p.text = o.text || '';     // tag 上写的字
    p.seed = Math.random() * 6.283;
    /* ring 的形状种子：位置 + 半径 + 出生那一帧。配方里"深色托底一圈 + 亮色一圈"是同一帧在同一点 spawn 的两颗（半径差几 px），
       种子相同 → 两圈同形，托底才托得住；随机种子的话两圈各扭各的，读成两个乱圈 */
    p.H = p.kind === 'ring' ? FxShape.harm(FxShape.hash(o.x * 2, o.y * 2, (o.r || 4) * 4, frameNo)) : null;
    /* 颜色串和贴图在出生时就定下来。它们整个生命周期都不变，而写在 draw 里
       就是每帧、每颗粒子都重新拼一次字符串、让浏览器重新解析一次颜色 ——
       场上常有三五百颗粒子，这笔账一秒钟要算上万次。 */
    p.fill = `rgb(${p.rgb[0]},${p.rgb[1]},${p.rgb[2]})`;
    p.line = p.edge ? `rgb(${p.edge[0]},${p.edge[1]},${p.edge[2]})` : null;
    p.tex = p.kind === 'soft' ? soft(p.rgb) : p.kind === 'dot' ? glow(p.rgb) : null;
    /* shape 指这颗粒子用哪张 3D 转盘。它跟 kind 是两件事：kind 是**画法**
       （实体还是光、吃不吃描边），shape 是**题材**（羽毛还是花瓣还是碎片）。
       同一个 chip 被五个配方复用，各自要的东西完全不一样 —— 枕头炸出羽毛、
       花束炸出花瓣、奶茶炸出珍珠，所以选图得看配方而不是看 kind。
       没给 shape、或素材没加载上，p.sp 为空，draw 自动退回矢量画法。 */
    p.sp = (o.shape && SHAPE[o.shape] && SHAPE[o.shape].img) ? SHAPE[o.shape] : null;
    p.stex = p.sp ? tinted(p.sp, p.rgb) : null;
    act.push(p);
    return p;
  }

  let frameNo = 0;                                       // 第几次 update（ring 种子用：同一帧出生的算同一下）
  function update(dt) {
    frameNo++;
    for (let i = act.length - 1; i >= 0; i--) {
      const p = act[i];
      p.life -= dt;
      if (p.life <= 0) { act.splice(i, 1); pool.push(p); continue; }
      p.vy += p.g * dt;
      if (p.drag !== 1) { const d = Math.pow(p.drag, dt * 60); p.vx *= d; p.vy *= d; }
      p.x += (p.vx + (p.sway ? Math.cos(p.seed + p.life * 3.1) * p.sway : 0)) * dt;
      p.y += p.vy * dt;
      p.rot += p.vrot * dt;
    }
    /* 衰减都写成 pow(k, dt*60) 而不是 k*dt：后者会让节奏随帧率漂移，
       这个坑在对抗线那边已经踩过一次。 */
    shake *= Math.pow(0.86, dt * 60);
    if (shake < 0.15) shake = 0;
    flash *= Math.pow(0.80, dt * 60);
    if (flash < 0.004) flash = 0;

    const a = Math.random() * 6.283;
    off.x = Math.cos(a) * shake;
    off.y = Math.sin(a) * shake * 0.6;   // 竖屏，横向震得多一点更像撞击
  }

  /* 淡入是绝对时间，淡出才按寿命比例。
     原来两头都按比例（前 15% 淡入），短命的火花看不出问题，但羽毛活 2 秒，
     15% 就是 300 毫秒 —— 枕头炸开之后要等三分之一秒羽毛才显形，命中最该看
     见东西的那一刻画面是空的。"入场"是一个固定的瞬间，与这个粒子打算活多久
     没有任何关系。 */
  const FADE_IN = 0.045;
  function fade(p) {
    const inn = Math.min(1, (p.maxLife - p.life) / FADE_IN);
    const out = Math.min(1, p.life / (p.maxLife * 0.34));
    return inn * out;
  }

  /* 五角星路径。半径 r，内凹到 0.42 —— 再瘦就变成海星，再胖就读成花。 */
  /* 爱心。用两段三次贝塞尔拼出来，比心形参数方程便宜得多，形状也更"图标"
     一点 —— 这里要的是观众一眼认出的那个符号，不是数学上正确的心脏线。
     顶点在 -r*0.62 而不是 -r，因为爱心的视觉重心明显偏下，按外接盒居中的话
     一堆爱心飘起来会整体显得往上飘了半个身位。 */
  function heartPath(ctx, r) {
    ctx.beginPath();
    ctx.moveTo(0, r * 0.92);
    ctx.bezierCurveTo(-r * 1.08, r * 0.10, -r * 0.62, -r * 1.02, 0, -r * 0.34);
    ctx.bezierCurveTo(r * 0.62, -r * 1.02, r * 1.08, r * 0.10, 0, r * 0.92);
    ctx.closePath();
  }

  function starPath(ctx, r) {
    ctx.beginPath();
    for (let i = 0; i < 10; i++) {
      const a = -1.5708 + i * 0.6283, rr = i % 2 ? r * 0.42 : r;
      const x = Math.cos(a) * rr, y = Math.sin(a) * rr;
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    }
    ctx.closePath();
  }

  /* 实体（普通混合、吃描边）的 kind；其余 dot / spark / ring 是光，走第二趟 lighter */
  const SOLID = new Set(['soft', 'chip', 'star', 'heart', 'card', 'chat', 'tag', 'glyph']);


  function draw(ctx) {
    // 第一趟：绒絮、碎片、星星，普通混合，它们是实体
    ctx.save();
    ctx.lineJoin = 'round';
    for (let i = 0; i < act.length; i++) {
      const p = act[i];
      if (!SOLID.has(p.kind)) continue;
      const k = p.life / p.maxLife;
      const alpha = p.a * fade(p);
      if (alpha <= 0.01) continue;
      ctx.globalAlpha = alpha;
      if (p.kind === 'soft') {
        const r = p.r + (p.r1 - p.r) * (1 - k);
        ctx.drawImage(p.tex, p.x - r, p.y - r, r * 2, r * 2);

      } else if (p.stex) {
        /* 3D 转盘版。五种实体形态共用这一段 —— 它们的差别已经全在贴图里了。

           尺寸取**正方形**：贴图格子是按所有角度的并集正方形裁的，物体在格子
           里保持自己的长宽比（羽毛就是细长的、照片就是竖的）。再按 w×h 去拉伸
           等于把形状的比例乘两遍，羽毛会被拉成一根面条。

           朝向分两份：转盘格子走 p.rot 全速（那是物体在**翻面**），canvas 只
           跟着转四分之一（那是它在画面里**打旋**）。不转 canvas 会僵、全速转
           canvas 又等于把渲好的光影一起转走 —— 那正是换 3D 要解决的问题。 */
        const r = p.r + (p.r1 - p.r) * (1 - k);
        const sz = ((p.kind === 'star' || p.kind === 'heart') ? r * 2 : Math.max(p.w, p.h)) * p.sp.scale;
        const ph = p.seed + (1 - k) * 7.4;
        const c = shapeCell(p.sp, p.rot), e = p.sp.cell;
        ctx.save();
        ctx.translate(p.x + (p.spin ? Math.cos(ph) * p.spin : 0),
                      p.y + (p.spin ? Math.sin(ph) * p.spin * 0.42 : 0));
        ctx.rotate(p.seed + p.rot * 0.25);
        ctx.drawImage(p.stex, (c % p.sp.cols) * e, ((c / p.sp.cols) | 0) * e, e, e,
                      -sz / 2, -sz / 2, sz, sz);
        ctx.restore();

      } else if (p.kind === 'star' || p.kind === 'heart') {
        const r = p.r + (p.r1 - p.r) * (1 - k);
        const ph = p.seed + (1 - k) * 7.4;
        ctx.save();
        ctx.translate(p.x + (p.spin ? Math.cos(ph) * p.spin : 0),
                      p.y + (p.spin ? Math.sin(ph) * p.spin * 0.42 : 0));
        ctx.rotate(p.rot);
        (p.kind === 'heart' ? heartPath : starPath)(ctx, r);
        ctx.fillStyle = p.fill;
        ctx.fill();
        if (p.line) { ctx.lineWidth = p.lw; ctx.strokeStyle = p.line; ctx.stroke(); }
        ctx.restore();
      } else if (p.kind === 'chat') {
        /* 聊天气泡：从脸上蹦出来的"翻出来的聊天记录"。r → r1 胀开，轻轻摆（rot 来回，不打转 —— 转起来就不像消息了）。
           edge 当描边，rgb 当框色，三个点用描边色。 */
        const r = p.r + (p.r1 - p.r) * (1 - k);
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(Math.sin(p.seed + (1 - k) * 6) * 0.22);
        drawChatIcon(ctx, r, p.fill, p.line, p.lw, p.line || '#3a8a30');
        ctx.restore();
      } else if (p.kind === 'tag') {
        /* 系统提示小标签（灭迹恶魔打中女生脸：「已撤回」「记录已清空」）：灰色圆角条 + 白字 + 深色描边，
           跟聊天软件里那条灰色的"对方撤回了一条消息"一个样子。r → r1 是字号，一出来先弹大一点再回落。 */
        const u = 1 - k, sz = p.r1 * (u < 0.12 ? 0.6 + 0.4 * u / 0.12 * 1.25 : 1);
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.font = `800 ${sz.toFixed(1)}px system-ui,"PingFang SC","Microsoft YaHei",sans-serif`;
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        const tw = ctx.measureText(p.text).width, hw = tw / 2 + sz * 0.6, hh = sz * 0.8;
        ctx.beginPath(); ctx.roundRect(-hw, -hh, hw * 2, hh * 2, hh);
        ctx.fillStyle = p.fill; ctx.fill();
        if (p.line) { ctx.lineWidth = p.lw; ctx.strokeStyle = p.line; ctx.stroke(); }
        ctx.fillStyle = '#ffffff'; ctx.fillText(p.text, 0, 1);
        ctx.restore();
      } else if (p.kind === 'glyph') {
        /* 一个金字（法海的咒语打中女生：「卍」「唵」「吽」这些字从她身上迸出来）：金芯 + 深褐粗描边，r → r1 是字号，
           先弹大一点再回落，边飞边慢慢转。金字在浅色底图上不描边就化掉。 */
        const u = 1 - k, sz = p.r1 * (u < 0.12 ? 0.6 + 0.4 * u / 0.12 * 1.3 : 1);
        ctx.save();
        ctx.translate(p.x, p.y); ctx.rotate(p.rot);
        ctx.font = `900 ${sz.toFixed(1)}px "Noto Serif CJK SC","Songti SC","STSong","SimSun",serif`;
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.lineWidth = p.lw; ctx.strokeStyle = p.line || '#5a2a08'; ctx.strokeText(p.text, 0, 0);
        ctx.fillStyle = p.fill; ctx.fillText(p.text, 0, 0);
        ctx.restore();
      } else if (p.kind === 'card') {
        /* 卡片：一张照片。它跟 chip 的区别不是参数而是**语义** —— chip 是
           "空中翻滚的薄片"，带描边时圆角被拉到半高满值、短边收成半圆，
           再配合按 cos(rot) 的压扁，无论怎么调参数都只会读成一颗胶囊。
           而照片必须始终是个有直角的矩形，否则"是不是照片"就没了，那正是
           这个粒子全部的意义。所以它不压扁、不圆角，只是斜着飘。
           内芯那一块是相纸中间的画面：没有它就只是一张白纸。 */
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        const hw = p.w / 2, hh2 = p.h / 2;
        ctx.fillStyle = p.fill;
        ctx.fillRect(-hw, -hh2, p.w, p.h);
        if (p.line) {
          ctx.lineWidth = p.lw; ctx.strokeStyle = p.line;
          ctx.strokeRect(-hw, -hh2, p.w, p.h);
          ctx.globalAlpha = alpha * 0.5;
          ctx.fillStyle = p.line;
          ctx.fillRect(-hw * 0.74, -hh2 * 0.82, p.w * 0.74, p.h * 0.58);
        }
        ctx.restore();

      } else {
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        // 翻滚时按 cos 压扁，读起来是一片薄东西在空中打转
        const hh = p.h / 2 * Math.abs(Math.cos(p.rot * 1.7));
        ctx.fillStyle = p.fill;
        if (p.line) {
          // 胶囊形：羽毛和碎屑都不是方砖，描边一上去直角就很扎眼。圆角给到
          // 半高的满值，短边直接收成半圆 —— 长宽比大的时候读成羽毛，接近
          // 正方的时候读成碎片，一个形状覆盖两种题材。
          ctx.beginPath();
          const rr = Math.min(p.w, hh * 2) * 0.5;
          ctx.roundRect(-p.w / 2, -hh, p.w, hh * 2, rr);
          ctx.fill();
          ctx.lineWidth = p.lw; ctx.strokeStyle = p.line;
          ctx.stroke();
        } else {
          ctx.fillRect(-p.w / 2, -hh, p.w, hh * 2);
        }
        ctx.restore();
      }
    }
    ctx.restore();

    // 第二趟：发光部分
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    for (let i = 0; i < act.length; i++) {
      const p = act[i];
      if (SOLID.has(p.kind)) continue;
      const k = p.life / p.maxLife;
      const alpha = p.a * fade(p);
      if (alpha <= 0.01) continue;
      ctx.globalAlpha = alpha;

      if (p.kind === 'dot') {
        const r = p.r + (p.r1 - p.r) * (1 - k);
        ctx.drawImage(p.tex, p.x - r, p.y - r, r * 2, r * 2);

      } else if (p.kind === 'spark') {                    // 头圆尾尖的一笔（原来是等宽圆头直线）
        const sp = Math.hypot(p.vx, p.vy);
        /* 长短、粗细每颗各不一样（seed 定）：配方 sweep 一圈等速甩出去的火花，长度一样时排成一圈整齐的虚线（用户截图一里那圈短线） */
        const j = p.seed / 6.283, len = Math.min(26, 4 + sp * 0.028) * (0.55 + 0.9 * j);
        const nx = sp ? p.vx / sp : 1, ny = sp ? p.vy / sp : 0;
        ctx.fillStyle = p.fill;
        FxShape.streak(ctx, p.x - nx * len * 1.3, p.y - ny * len * 1.3, p.x, p.y, p.lw * (0.8 + 0.8 * ((j * 7.3) % 1)));

      } else if (p.kind === 'ring') {                     // 涟漪（原来是 ctx.ellipse 描边的正椭圆）：半径 / 粗细 / 透明度的语义不变
        const r = p.r + (p.r1 - p.r) * (1 - k);
        ctx.fillStyle = p.fill;
        FxShape.ring(ctx, p.x, p.y, r, 0.5, (p.lw * k + 0.6) * 1.6, 1 - k, p.maxLife - p.life, p.H);
      }
    }
    ctx.restore();
  }

  /* 全屏白闪。画在最上层，连 HUD 一起罩住 —— 只罩画面的话会显得闪光是
     "场景里的光"，而它要的是"这一下很重"。
     用普通混合而不是 lighter：底图是明亮的客厅（浅绿墙、米色地板），lighter
     叠上去立刻过曝成一片白，人物全糊。可用的白闪强度是底图亮度定的，暗色
     战场能用 0.5，这里 0.22 就到顶了。 */
  function drawFlash(ctx, w, h) {
    if (flash <= 0.004) return;
    ctx.save();
    ctx.fillStyle = `rgba(255,252,246,${flash})`;
    ctx.fillRect(0, 0, w, h);
    ctx.restore();
  }

  /* 顿帧：返回本帧实际该走多少时间。命中瞬间把世界冻住，其余照常。
     注意冻的是游戏时间不是渲染 —— 画面照常刷新，只是一切都不动。 */
  function tick(dt) {
    if (cool > 0) { cool -= dt; if (cool <= 0) lvl = 0; }
    if (stop > 0) { stop -= dt; return 0; }
    return dt;
  }

  /* 顿帧必须有不应期。
     "冻住"之所以有力，是因为它打断了流动 —— 而连点时命中本来就是连续的，
     每一击都冻的话顿帧首尾相接，世界就长期停摆：帧率一点没掉，观众却读成
     "卡了"。实测连点时有 65% 的帧是冻住的，把礼物间隔放宽三倍还是 65%，
     说明撑起它的不是礼物密度，是"每一击都冻"这条规则本身。
     所以冻完之后，要让世界正常流动更长的一段时间。比例给到 1:2 而不是 1:1：
     命中越密集，顿帧越该退让 —— 每秒有九件礼物落地的时候根本没有"这一击"
     可言，观众要看的是整体的热闹，而一半时间不动的画面只会读成掉帧。
     更重的一击可以打断正在演的那一次 —— 大礼物压过点赞，这个优先级跟别处
     是一致的。 */
  function hitStop(sec) {
    if (sec <= 0) return;
    if (cool > 0 && sec <= lvl) return;
    stop = Math.max(stop, sec);
    lvl = sec;
    cool = sec * 3;          // 冻 sec，再流动 2*sec —— 占空比到顶三分之一
  }
  function addShake(v) { shake = Math.min(30, shake + v); }
  function addFlash(v) { flash = Math.max(flash, v); }
  function clear() { while (act.length) pool.push(act.pop()); shake = flash = stop = cool = lvl = 0; }

  return {
    spawn, update, draw, drawFlash, tick, loadShapes,
    hitStop, addShake, addFlash, clear,
    off, count: () => act.length,
  };
})();
