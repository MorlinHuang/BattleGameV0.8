/* bgmotion.js —— 长卷背景里会动的东西（v15 雷雨夜，2026-09-29）。
 *
 * 用户："背景要活起来，但不能喧宾夺主，礼物特效出来时不能乱""画龙点睛，不要什么都动"。两类：
 *
 * ① 视频动区（assets/world/v15/anim/）：即梦图生视频，离线由 v14/bg/v15/video/anim.py 处理成一块块小视频 ——
 *    配准到底图、逐帧配色、羽化边缘（边缘像素就是底图本身）、常驻的接成无缝循环、偶发的首尾淡回底图。
 *    这里把每块按世界坐标**整块盖在房间图上**，不用遮罩，也不用管接缝。
 *      loop  常驻（鱼缸、三扇窗的雨、黑猫、床幔）：在镜头里就播，出了镜头就暂停（不占解码）。
 *      event 写真相框里的人眨眼浅笑：每 PHOTO_GAP 秒演一次，不参与让位（用户："档 4 在场时不影响写真"）。
 *
 * ② 程序光效（assets/world/v15/fx/，位置和贴图由 v14/bg/v15/lights.py 从底图量出来）：
 *      常驻：串灯 / 镜灯顺着灯串慢慢"呼吸"（光晕叠加，灯泡本身在底图里）、蜡烛火苗抖、机箱风扇慢慢换色、显卡彩虹流光；
 *      联动：送礼时电竞房聊天屏冒一条新消息，旧的往上顶；
 *      偶发（EVENT_GAP 秒一件，同一时刻只一件）：闪电（三扇窗同时白闪两下、窗里各劈一道 + 冷光从窗口洒进屋，霓虹手柄跟着接触不良）、
 *            床上手机亮屏震两下、霓虹手柄自己接触不良一下。
 * 让位（全盘规划.md 第 5 节）：档 3/4 帮手在场时，常驻的退三成（CALM），偶发的不开演；写真、聊天屏照常。
 * 按真实时间走（performance.now），跟对局的顿帧、慢放无关 —— 背景不参与打击感。
 */
'use strict';

const BgMotion = (() => {
  const PHOTO_GAP = [6, 12];   // 写真眨眼间隔（秒）
  const EVENT_GAP = [10, 20];  // 偶发事件间隔（秒）（20~40 用户看不出来）
  const CALM = 0.7;            // 让位时常驻动效剩几成
  const EASE = 2.5;            // 让位进出的快慢（每秒走多少）
  const rnd = (a, b) => a + Math.random() * (b - a);
  let zones = [], fx = null, calmK = 0, last = 0, t0 = 0;
  const img = {};

  /* ---------- 加载 ---------- */
  async function json(url) { const r = await fetch(url); return r.ok ? r.json() : null; }
  const image = (src) => new Promise((ok, no) => { const im = new Image(); im.onload = () => ok(im); im.onerror = no; im.src = src; });

  /* dir：这套房间的目录（assets/world/v15/）。没有 anim/ 或 fx/ 就是没有这一类，返回加载到的动区 + 光效组数 */
  async function load(dir, q) {
    const [anim, f] = await Promise.all([json(dir + 'anim/anim.json' + q), json(dir + 'fx/fx.json' + q)]);
    const now = performance.now() / 1000; t0 = now;
    zones = (anim || []).map(z => {
      const v = document.createElement('video');
      v.muted = true; v.setAttribute('muted', ''); v.setAttribute('playsinline', ''); v.playsInline = true;
      v.loop = z.kind === 'loop'; v.preload = 'auto';
      v.src = dir + 'anim/' + z.src + q;
      v.defaultPlaybackRate = v.playbackRate = z.rate || 1;
      return { ...z, v, next: now + rnd(...PHOTO_GAP) };
    });
    if (f) {
      const srcs = [f.fans.src, f.gpu.src, f.neon.src, f.phone.off, f.phone.body, f.chat.mask, ...Object.values(f.windows).map(w => w.src)];
      await Promise.all(srcs.map(s => image(dir + 'fx/' + s + q).then(im => { img[s] = im; })));
      fx = f; initFx(now);
    }
    return zones.length + (fx ? fx.bulbs.length + 5 : 0);
  }

  /* ---------- 光效的状态 ---------- */
  const glowCache = new Map();
  /* 灯泡光晕：暖色径向渐变，中心不到全亮（灯泡本身底图里已经是白的，这里只让周围那圈光一呼一吸） */
  function glow(c, r) {
    const k = c.join() + r;
    if (!glowCache.has(k)) {
      const cv = document.createElement('canvas'); cv.width = cv.height = r * 2;
      const g = cv.getContext('2d'), gr = g.createRadialGradient(r, r, 0, r, r, r);
      gr.addColorStop(0, `rgba(${c},0.95)`); gr.addColorStop(0.15, `rgba(${c},0.6)`); gr.addColorStop(0.45, `rgba(${c},0.2)`); gr.addColorStop(1, `rgba(${c},0)`);
      g.fillStyle = gr; g.fillRect(0, 0, r * 2, r * 2); glowCache.set(k, cv);
    }
    return glowCache.get(k);
  }
  let off = null;                           // 风扇换色、聊天屏用的离屏画布
  const buf = (w, h) => { if (!off) off = document.createElement('canvas'); off.width = w; off.height = h; const c = off.getContext('2d'); c.clearRect(0, 0, w, h); return c; };

  let ev = null, evNext = 0;                // 偶发事件：{kind, t0}
  const chat = { rows: [], scroll: 0, hi: 0, queue: 0, nextAt: 0 };
  const CHAT_COLORS = ['rgb(110,205,245)', 'rgb(245,150,115)', 'rgb(245,120,170)', 'rgb(250,200,110)', 'rgb(160,140,255)'];
  const chatRow = () => ({ c: CHAT_COLORS[Math.floor(Math.random() * CHAT_COLORS.length)], n: rnd(12, 24), w: rnd(22, 52) });
  function initFx(now) {
    evNext = now + rnd(4, 8);               // 进场后先稍等，第一件别一开局就来
    chat.rows = ['rgb(110,205,245)', 'rgb(245,150,115)', 'rgb(245,120,170)', 'rgb(245,150,115)', 'rgb(245,120,170)', 'rgb(110,205,245)']
      .map(c => ({ ...chatRow(), c }));     // 开局跟底图里那几条的头像颜色一样
  }

  /* 送礼 → 聊天屏冒一条。点赞刷得快，排队、最快 0.45 秒一条，最多攒 3 条 */
  function chatPush() { chat.queue = Math.min(3, chat.queue + 1); }

  /* ---------- 画 ---------- */
  /* x0：房间图第 0 张画在屏幕上的 x（drawWorld 用的同一个取整值），全部东西跟着房间逐像素对齐 */
  function draw(ctx, x0, W, H, calm) {
    const now = performance.now() / 1000, dt = Math.min(0.1, now - (last || now)); last = now;
    calmK = Math.min(1, Math.max(0, calmK + (calm ? EASE : -EASE) * dt));
    const k = 1 - (1 - CALM) * calmK;       // 常驻动效还剩几成
    const seen = (x, w) => x0 + x + w > 0 && x0 + x < W;
    drawZones(ctx, x0, seen, now, k);
    if (!fx) return;
    const t = now - t0;
    if (!ev && now >= evNext && !calm) ev = pickEvent(now, seen);
    if (ev && now - ev.t0 > ev.dur) { ev = null; evNext = now + rnd(...EVENT_GAP); }
    const et = ev ? now - ev.t0 : -1;
    const flash = ev && ev.kind === 'lightning' ? lightning(et) : 0;
    drawBulbs(ctx, x0, W, t, k);
    drawFans(ctx, x0, seen, t, k);
    drawGpu(ctx, x0, seen, t, k);
    drawNeon(ctx, x0, seen, ev, et);
    drawChat(ctx, x0, seen, now, dt);
    drawPhone(ctx, x0, seen, ev && ev.kind === 'phone' ? et : -1);
    if (flash > 0) drawLightning(ctx, x0, W, H, seen, flash);
  }

  function drawZones(ctx, x0, seen, now, k) {
    for (const z of zones) {
      const v = z.v, vis = seen(z.x, z.w);
      if (z.kind === 'loop') {
        if (!vis) { if (!v.paused) v.pause(); continue; }
        if (v.paused) play(v);
      } else {
        if (z.on && v.ended) { z.on = false; z.next = now + rnd(...PHOTO_GAP); }
        if (!z.on) {
          if (!vis || now < z.next) continue;
          z.on = true; v.currentTime = 0; play(v);
        }
        if (!vis) continue;
      }
      if (v.readyState < 2) continue;
      ctx.globalAlpha = z.kind === 'loop' ? k : 1;
      ctx.drawImage(v, x0 + z.x, z.y, z.w, z.h);
    }
    ctx.globalAlpha = 1;
  }
  /* 浏览器拒绝播放（省电模式、后台标签页）时视频停在原地：画面就是静止的底图，不影响对局 */
  function play(v) { v.play().catch(() => {}); }

  /* 串灯：顺着灯串一波一波地亮（相位按 x 走），一颗颗各自再带一点点抖；镜灯一起慢呼吸；蜡烛火苗抖 */
  function drawBulbs(ctx, x0, W, t, k) {
    ctx.globalCompositeOperation = 'lighter';
    for (const b of fx.bulbs) {
      const g = glow(b.color, b.r);
      for (let i = 0; i < b.pts.length; i++) {
        const [x, y] = b.pts[i], sx = x0 + x;
        if (sx + b.r < 0 || sx - b.r > W) continue;
        let a;
        /* 串灯：一道亮波顺着灯串走过去（平方让波峰窄、灯与灯之间明暗拉得开），用户第一版："效果不明显，看不出来" */
        if (b.mode === 'wave') { const w = 0.5 + 0.5 * Math.sin(t * 1.6 - x * 0.025); a = 0.08 + 0.85 * w * w + 0.05 * Math.sin(t * 5.1 + i * 2.3); }
        else if (b.mode === 'mirror') a = 0.18 + 0.55 * (0.5 + 0.5 * Math.sin(t * 1.1));
        else a = 0.55 + 0.25 * Math.sin(t * 9.7) * Math.sin(t * 5.3 + 1) + 0.1 * Math.sin(t * 23);
        ctx.globalAlpha = Math.max(0, a) * k;
        ctx.drawImage(g, sx - b.r, y - b.r);
      }
    }
    ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  }

  /* 机箱风扇：色相在青 → 蓝 → 紫 → 粉之间来回慢慢走（20 秒一个来回），亮度结构用原图的（'hue' 混合只换色相） */
  function drawFans(ctx, x0, seen, t, k) {
    const f = fx.fans, im = img[f.src];
    if (!seen(f.x, im.width)) return;
    const h = 195 + 125 * (0.5 - 0.5 * Math.cos(t * Math.PI * 2 / 20));
    const c = buf(im.width, im.height);
    c.drawImage(im, 0, 0);
    c.globalCompositeOperation = 'hue'; c.fillStyle = `hsl(${h},100%,50%)`; c.fillRect(0, 0, im.width, im.height);
    c.globalCompositeOperation = 'destination-in'; c.drawImage(im, 0, 0);
    c.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = k; ctx.drawImage(off, x0 + f.x, f.y);
    /* 同色的光晕往外晕一圈，一呼一吸：光换了颜色，映在机箱和墙上的也跟着换 */
    ctx.globalCompositeOperation = 'lighter';
    for (const [cx, cy] of f.centers) {
      const r = 34, gr = ctx.createRadialGradient(x0 + cx, cy, 0, x0 + cx, cy, r), a = (0.3 + 0.15 * Math.sin(t * 2.2)) * k;
      gr.addColorStop(0, `hsla(${h},100%,60%,${a.toFixed(3)})`); gr.addColorStop(1, `hsla(${h},100%,60%,0)`);
      ctx.fillStyle = gr; ctx.fillRect(x0 + cx - r, cy - r, r * 2, r * 2);
    }
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
  }

  /* 显卡彩虹流光（用户："和真实炫彩显卡效果类似"）：ARGB 显卡的彩虹波 —— 一整条彩虹沿灯条往一个方向流，
     2.4 秒流过一圈。三层：显卡那团光换成流动的彩虹色相、灯条本身一道更亮的彩虹线、同色的光洒满机箱侧透玻璃里 */
  const GPU_PERIOD = 2.4, GPU_SPAN = 40;      // 流一圈几秒、一整条彩虹在画面上铺多宽（像素）
  function rainbow(c, xa, ya, xb, yb, t, a, l = 55) {
    const g = c.createLinearGradient(xa, ya, xb, yb), ph = (t / GPU_PERIOD) % 1;
    for (let i = 0; i <= 6; i++) g.addColorStop(i / 6, `hsla(${((i / 6 - ph) * 360 * (Math.hypot(xb - xa, yb - ya) / GPU_SPAN) + 3600) % 360},100%,${l}%,${a})`);
    return g;
  }
  function drawGpu(ctx, x0, seen, t, k) {
    const p = fx.gpu, im = img[p.src];
    if (!seen(p.x, im.width)) return;
    const gx = x0 + p.x, [[ax, ay], [bx, by]] = p.bar;
    // ① 那团光：色相换成沿灯条方向流动的彩虹（'hue' 保留原图的明暗结构）
    const c = buf(im.width, im.height);
    c.drawImage(im, 0, 0);
    c.globalCompositeOperation = 'hue'; c.fillStyle = rainbow(c, ax - p.x - 12, 0, bx - p.x + 12, 0, t, 1); c.fillRect(0, 0, im.width, im.height);
    c.globalCompositeOperation = 'destination-in'; c.drawImage(im, 0, 0);
    c.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = k; ctx.drawImage(off, gx, p.y);
    // ② 机箱玻璃里洒一层同色的光（跟着灯条中段此刻的颜色走），③ 灯条本身：宽的光晕 + 细的亮芯
    ctx.globalCompositeOperation = 'lighter';
    const [q0, q1, q2, q3] = p.glass, mx = (ax + bx) / 2, my = (ay + by) / 2, hMid = ((0.5 - (t / GPU_PERIOD) % 1) * 360 * ((bx - ax) / GPU_SPAN) + 3600) % 360;
    ctx.save(); ctx.beginPath(); ctx.rect(x0 + q0, q1, q2 - q0, q3 - q1); ctx.clip();
    const gr = ctx.createRadialGradient(x0 + mx, my, 0, x0 + mx, my, 48);
    gr.addColorStop(0, `hsla(${hMid},100%,60%,${(0.5 * k).toFixed(3)})`); gr.addColorStop(1, `hsla(${hMid},100%,60%,0)`);
    ctx.fillStyle = gr; ctx.fillRect(x0 + q0, q1, q2 - q0, q3 - q1);
    ctx.restore();
    ctx.lineCap = 'round';
    for (const [lw, a, l] of [[7, 0.35, 55], [2.4, 0.95, 68]]) {
      ctx.strokeStyle = rainbow(ctx, x0 + ax, ay, x0 + bx, by, t, (a * k).toFixed(3), l); ctx.lineWidth = lw;
      ctx.beginPath(); ctx.moveTo(x0 + ax, ay); ctx.lineTo(x0 + bx, by); ctx.stroke();
    }
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
  }

  /* 霓虹手柄接触不良：一串长短不一的灭 / 半亮（[起始秒, 灭了几成]），闪电后和它自己偶发时都用这一串 */
  const GLITCH = [[0, 1], [0.05, 0], [0.12, 1], [0.17, 0.35], [0.24, 1], [0.42, 0], [0.47, 0.8], [0.53, 0]];
  function drawNeon(ctx, x0, seen, ev, et) {
    const n = fx.neon, im = img[n.src];
    if (!ev || !seen(n.x, im.width)) return;
    const s = ev.kind === 'neon' ? et : ev.kind === 'lightning' ? et - 0.35 : -1;   // 闪电劈下来之后才跳
    if (s < 0 || s > 0.6) return;
    let a = 0; for (const [ts, v] of GLITCH) if (s >= ts) a = v;
    if (a > 0) { ctx.globalAlpha = a; ctx.drawImage(im, x0 + n.x, n.y); ctx.globalAlpha = 1; }
  }

  /* 聊天屏：新消息从底下冒出来，整列往上顶一行；新的那条底下亮一下再暗回去 */
  const CHAT_DY = 14;
  function drawChat(ctx, x0, seen, now, dt) {
    const c = fx.chat, [bx0, by0, bx1, by1] = c.box, bw = bx1 - bx0, bh = by1 - by0;
    if (chat.queue > 0 && now >= chat.nextAt) {
      chat.queue--; chat.nextAt = now + 0.45;
      chat.rows.push(chatRow()); if (chat.rows.length > c.rows.length + 1) chat.rows.shift();
      chat.scroll = 1; chat.hi = 1;
    }
    chat.scroll = Math.max(0, chat.scroll - dt / 0.28); chat.hi = Math.max(0, chat.hi - dt / 1.6);
    if (!seen(bx0, bw)) return;
    const g = buf(bw, bh), ax = c.x - bx0, top = c.rows[0] - 8 - by0;
    g.fillStyle = `rgb(${c.bg})`; g.fillRect(ax - 7, top, bw - (ax - 7) - 6, bh - top);
    const e = chat.scroll * chat.scroll * (3 - 2 * chat.scroll);          // 顶上去的缓动
    const n = chat.rows.length, lastY = c.rows[c.rows.length - 1] - by0;
    for (let i = 0; i < n; i++) {
      const r = chat.rows[i], y = lastY - (n - 1 - i) * CHAT_DY + e * CHAT_DY;
      if (y < top + 4) continue;
      if (i === n - 1 && chat.hi > 0) { g.fillStyle = `rgba(170,200,255,${(0.75 * chat.hi).toFixed(3)})`; g.fillRect(ax - 7, y - 7, bw - (ax - 7) - 6, CHAT_DY); }
      g.fillStyle = r.c; g.beginPath(); g.arc(ax, y, 4.2, 0, Math.PI * 2); g.fill();
      g.fillStyle = 'rgba(220,232,255,0.92)'; g.fillRect(ax + 8, y - 4, r.n, 2.2);
      g.fillStyle = 'rgba(165,188,248,0.85)'; g.fillRect(ax + 8, y + 1, r.w, 2);
    }
    g.globalCompositeOperation = 'destination-in'; g.drawImage(img[c.mask], 0, 0); g.globalCompositeOperation = 'source-over';
    ctx.drawImage(off, x0 + bx0, by0);
  }

  /* 床上手机：平时黑屏（盖 screen_off）；来消息时亮屏、震两下（整只手机左右错 1px），屏幕的蓝光映在被子上 */
  function drawPhone(ctx, x0, seen, et) {
    const p = fx.phone, so = img[p.off], body = img[p.body];
    if (!seen(p.x, body.width)) return;
    const on = et < 0 ? 0 : et < 0.12 ? et / 0.12 : et < 2.9 ? 1 : Math.max(0, 1 - (et - 2.9) / 0.4);
    const buzz = (et > 0.2 && et < 0.5) || (et > 0.75 && et < 1.05);
    if (buzz) ctx.drawImage(body, x0 + p.x + (Math.sin(et * 110) > 0 ? 1 : -1), p.y);
    if (on < 1) { ctx.globalAlpha = 1 - on; ctx.drawImage(so, x0 + p.x, p.y); ctx.globalAlpha = 1; }
    if (on > 0) {
      const cx = x0 + p.cx, cy = p.cy, r = 130, gr = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
      gr.addColorStop(0, `rgba(100,160,255,${(0.6 * on).toFixed(3)})`); gr.addColorStop(0.3, `rgba(90,150,255,${(0.22 * on).toFixed(3)})`); gr.addColorStop(1, 'rgba(90,150,255,0)');
      ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = gr; ctx.fillRect(cx - r, cy - r, r * 2, r * 2);
      ctx.globalCompositeOperation = 'source-over';
    }
  }

  /* 闪电：白闪两下（第一下短而亮，第二下稍弱、拖得长一点）。三扇窗同时，全屋跟着一层冷光 */
  function lightning(t) {
    const pulse = (t0, a, rise, fall) => t < t0 ? 0 : t < t0 + rise ? a * (t - t0) / rise : a * Math.exp(-(t - t0 - rise) / fall);
    return Math.min(1, pulse(0, 1, 0.03, 0.07) + pulse(0.2, 0.8, 0.04, 0.16));
  }
  /* 窗里的闪电本体：每扇窗每次各劈一道（开演时随机生成），从窗顶往下折，到窗高六七成（楼后面）为止，带两根分叉 */
  function bolt(w, h) {
    const main = [[w * rnd(0.2, 0.8), 0]];
    const stop = h * rnd(0.5, 0.7);
    while (main[main.length - 1][1] < stop) { const [x, y] = main[main.length - 1]; main.push([Math.min(w - 4, Math.max(4, x + rnd(-14, 14))), y + rnd(10, 22)]); }
    const paths = [main];
    for (let b = 0; b < 2; b++) {
      let [x, y] = main[2 + Math.floor(Math.random() * (main.length - 4))]; const dir = Math.random() < 0.5 ? -1 : 1, br = [[x, y]];
      for (let s = 0; s < 4; s++) { x += dir * rnd(4, 14); y += rnd(8, 16); br.push([x, y]); }
      paths.push(br);
    }
    return paths;
  }
  function strokeBolt(ctx, paths, ox, oy, a) {
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    for (const [lw, col] of [[9, `rgba(150,170,255,${(0.35 * a).toFixed(3)})`], [3.5, `rgba(210,220,255,${(0.8 * a).toFixed(3)})`], [1.5, `rgba(255,255,255,${a.toFixed(3)})`]]) {
      ctx.strokeStyle = col;
      paths.forEach((p, i) => {
        ctx.lineWidth = i ? lw * 0.55 : lw; ctx.beginPath();
        p.forEach(([x, y], j) => (j ? ctx.lineTo : ctx.moveTo).call(ctx, ox + x, oy + y)); ctx.stroke();
      });
    }
  }
  function drawLightning(ctx, x0, W, H, seen, f) {
    ctx.globalCompositeOperation = 'lighter';
    for (const [k, w] of Object.entries(fx.windows)) {
      const im = img[w.src];
      if (!seen(w.x, im.width)) continue;
      ctx.globalAlpha = f; ctx.drawImage(im, x0 + w.x, w.y); ctx.globalAlpha = 1;
      if (!ev.bolts) ev.bolts = {};
      if (!ev.bolts[k]) ev.bolts[k] = bolt(im.width, im.height);
      ctx.save(); ctx.beginPath(); ctx.rect(x0 + w.x + 6, w.y + 6, im.width - 12, im.height - 12); ctx.clip();
      strokeBolt(ctx, ev.bolts[k], x0 + w.x, w.y, Math.min(1, f * 1.3));
      ctx.restore();
    }
    /* 屋里的冷光从窗口照进来：以窗为心往屋里衰减（整屏均匀一层读成起雾），全屋只留很淡一层底 */
    ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'screen';
    for (const w of Object.values(fx.windows)) {
      const im = img[w.src], cx = x0 + w.x + im.width / 2, cy = w.y + im.height * 0.55, r = 760;
      if (cx + r < 0 || cx - r > W) continue;
      const gr = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
      gr.addColorStop(0, `rgba(180,200,255,${(0.42 * f).toFixed(3)})`); gr.addColorStop(1, 'rgba(175,195,255,0)');
      ctx.fillStyle = gr; ctx.fillRect(cx - r, cy - r, r * 2, r * 2);
    }
    ctx.fillStyle = `rgba(180,200,255,${(0.09 * f).toFixed(3)})`; ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'source-over';
  }

  /* 下一件偶发：闪电哪儿都能演（全屋同步），手机、霓虹只在镜头里看得见时才轮得到 */
  function pickEvent(now, seen) {
    const c = [['lightning', 1.5, 1.2]];
    const p = fx.phone, n = fx.neon;
    if (seen(p.x, img[p.body].width)) c.push(['phone', 1, 3.3]);
    if (seen(n.x, img[n.src].width)) c.push(['neon', 0.6, 0.7]);
    let r = Math.random() * c.reduce((s, e) => s + e[1], 0);
    for (const [kind, w, dur] of c) { if ((r -= w) <= 0) return { kind, dur, t0: now }; }
    return { kind: 'lightning', dur: 1.2, t0: now };
  }

  return { load, draw, chatPush, zones: () => zones, fire: (kind) => { ev = { kind, dur: { lightning: 1.2, phone: 3.3, neon: 0.7 }[kind], t0: performance.now() / 1000 }; } };
})();
