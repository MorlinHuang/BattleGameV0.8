/* trio_fx.js —— 三人组攻击特效：烘焙贴图 + sprite 粒子（2026-10-01，美术打磨自检 P4 / P5 / P8）
 *
 * 把"canvas 平涂线条"换成游戏级效果：光束是多层贴图条（外晕 / 光身 / 中层 / 芯，噪声沿长度滚动）+ 出口四角星 +
 * 沿途甩光粒 + 末端溅开的冲击波；命中是统一的三层配方（瞬闪 → 主体碎片 → 余烬），碎片是带高光和描边的 sprite；
 * 落地 / 滑行有尘土。贴图由 tools/fx_bake.py 离线烘焙进 assets/fx/trio/，运行时按调色板映射一次（ramp），之后只 drawImage。
 *
 * 配色规矩跟 fx.js 一样，是这张明亮客厅底图逼出来的（skill chashouji-fx）：lighter 在亮底上加不出来，所以这里**全部普通混合**，
 * 发光靠色带"白芯 → 饱和本色 → 暗一档的边"自己撑对比，实体碎片一律带暗描边。贴图存的是色带位置 v（灰度）而不是颜色，
 * 同一张水滴能出水 / 焦糖 / 西瓜汁，同一条光束能出悟空的蓝和排山倒海的橙。
 *
 * ======================================================================================================================
 * 接口（引擎接入点）。全部坐标是画布坐标（960×1707），角度是弧度、y 朝下（Math.atan2(dy, dx) 那一套）。
 * ======================================================================================================================
 *
 * 0. 加载与每帧驱动（main.js）
 *      boot：    await TrioFX.load(ver)            // 与 Particles.loadShapes 并列；ver 同 ?v=，返回 Promise<boolean>（缺素材 false，不抛）
 *      update：  TrioFX.update(dt)                  // 用 Particles.tick(dt) 之后的 dt —— 顿帧冻住时粒子一起冻
 *      renderFx：TrioFX.draw(ctx)                   // 紧跟 Particles.draw(ctx) 之后（同一层：弹幕 → 粒子 → HUD）
 *      clear：   TrioFX.clear()                     // 跟 Particles.clear() 一起（重开一局）
 *
 * 1. 命中配方（main.js RECIPE / trio.js TRIO_RECIPE）
 *      TrioFX.RECIPE 的每一项和旧 RECIPE 同签名：{ tint, burst(x, y, side, s), drip?(x, y, side) }，impact() 不用改。
 *      接法：Object.assign(RECIPE, TrioFX.RECIPE) 放在 Object.assign(RECIPE, TRIO_RECIPE) 之后（同名覆盖旧的）；
 *      只想先换三人组：三人组 cfg.recipe 改写成 'fx_' 前缀另挂一份也行 —— 名字表见 TrioFX.RECIPE 的 key：
 *        thud star splash feather melon slash petal debris hollow water ball rouge（12 种，tint 与旧配方逐字一致）
 *      每项还带 layers: { flash, body, ember } 三个函数，可单独调某一层（比如 drip 只放余烬）。
 *      side / s 语义同 impact：side +1 打向左（女方），-1 打向右；s 0.55 / 1.0 / 1.7 / 2.8。尺寸内部按 min(s, 1.8) 封顶
 *      （skill：密度靠数量不靠单颗更大），数量按 s 线性。
 *
 * 2. 光束（trio.js stepBeam / beamTick / drawBeam / orb，B19 B22 G23 G30）
 *      const fx = TrioFX.beam(A.beam)               // 每个角色一次（建 Act 时），A.beam 原样传：读 glow / edge / layers / ball
 *      蓄力（stepBeam 'charge' 分支 / 帧序列蓄力帧）：fx.charge(dt, x, y, r)    // (x, y) = holdPt(P)，r = 原 drawBeam 算的球半径
 *      开轰（'fire' 分支，每个逻辑帧）：  fx.fire(dt, from, dir, to, e, k)
 *          from  出口点 handPt(P)
 *          dir   出口方向（弧度）—— **光束第一段的切线 = dir**。引擎负责人那边 P1 做出口方向：出手帧的 nozzle / hold 第三项
 *                给出手臂指向，传进来即可；传 null 表示还没有出口方向，退回直线 from → to（等于现在的画法）。
 *                dir 与 from→to 不一致时光束走二次贝塞尔：控制点 = from + dir × 0.42·|to − from|，所以出手那一段沿手臂出去、
 *                再弯到落点。（后排出手要翻过主角头顶的那条 over() 路径：把 over() 的控制点方向当 dir 传即可，同一条曲线。）
 *          to    落点 o.aim(S.u)
 *          e     光头伸出去多少 0..1 = min(1, S.t / beamReach())（与 beamTick 判打中用同一个数，伸到 1 那一刻打中）
 *          k     收束 0..1 = min(1, (B.fire − S.t) / 0.15)
 *      歇（'rest'）：fx.rest()                       // 不画；已经甩出去的光粒照常飞完
 *      画：fx.draw(ctx)                               // 放在 drawOver 里原 drawBeam(ctx) 的位置
 *      末端溅开（冲击波 + 反溅火花）由 fx 自己在 e ≥ 1 时持续放；beamTick 每 drip 秒的 onSplash 照旧（那是配方的 drip）。
 *
 * 3. 斩痕（trio.js drawSlash，B23 G?）
 *      shots 里 'slash' 那一项开始划（s.t 从 < 0 跨到 ≥ 0、s.p 有了）的那一帧调一次：
 *        TrioFX.slash(s.p[0], s.p[1], s.ang, A.slash.len, A.slash.color, A.slash.life)
 *      之后 drawShot 里 'slash' 分支不再画（刀光序列帧在 TrioFX 的粒子池里，自己播完）。
 *
 * 4. 尘土（P8，main.js / trio.js 进场）
 *      落地：enter seq 里标 'land' 的那一刻：TrioFX.land(x, y, s)          // (x, y) 脚下接地点；s 体型（P.s，默认 1）
 *      滑行 / 冲刺 / 骑：在场这段每个逻辑帧：TrioFX.skid(st, x, y, vx, dt, s)  // st = 调用方自己持有的一个对象（b 就行，
 *                        TrioFX 在上面记累加器 st._fxSkid）；vx 接触点水平速度（px/s，正 = 往右），|vx| < 40 不出尘
 *      拖痕沿用 main.js 的 Scuff。
 *
 * 性能：贴图 6 张 + atlas.json 共 70 KB，load 一次；ramp（灰度 → 调色板）每种 (贴图格, 调色板) 只算一次进 rampCache；运行时每颗粒子
 *      一次 drawImage（圆团不转，走快路径），光束每层每段一次 fillRect（直线 1 段，弯的 24 段，4 层）。池上限 MAX = 900，满了回收最老的。
 *      实测（fx_lab.html ?bench=1，桌面容器 GUI Chrome + SwiftShader 软渲染，600 帧；负载 = 同屏 6 人 + 主角：两道光束 B22 + G23
 *      轮流蓄 / 轰、每 0.25 s 一次首击级命中（s 1.7，12 配方轮换）、每 0.1 s 一次 water.drip、两条 600 px/s 的滑行尘）：
 *        只算特效（生成 + 更新 + 绘制，不含底图）   旧 均 8.2 ms / p95 12.8      新 均 13.2 ms / p95 20.2，粒子 均 263 峰 378
 *        差值分账：新·不画光束 9.2 ms → 两道光束 ≈ 4.0 ms；新·都不画 0.08 ms（生成 + 更新几乎不花钱，钱全在填像素）
 *        对等比（去掉旧版没有的滑行尘 &benchskid=0）：新·只画粒子 8.5 ms ≈ 旧·粒子 + 平涂光束 8.1 ms
 *      软渲染下绝对值偏大、填充率是瓶颈（skill chashouji-verify：这台机器绝对帧时间不可信，相对比可信）；手机 GPU 上 drawImage
 *      ~260 次 / 帧不是负担。真机帧时间未测。
 * ====================================================================================================================== */
'use strict';

const TrioFX = (function () {
  const MAX = 900;
  let META = null;
  const IMG = {};

  function load(ver) {
    const q = ver ? '?v=' + encodeURIComponent(ver) : '';
    return fetch('assets/fx/trio/atlas.json' + q).then(r => r.json()).then(m => {
      META = m;
      return Promise.all(Object.keys(m).map(k => new Promise((done) => {
        const im = new Image();
        im.onload = () => { IMG[k] = im; done(true); };
        im.onerror = () => { console.error(`trio_fx: ${m[k].src} 加载失败`); done(false); };
        im.src = m[k].src + q;
      })));
    }).then(ok => ok.every(Boolean));
  }
  const ready = () => !!META && Object.keys(META).every(k => IMG[k]);

  /* ---------- 调色板 ---------- */
  /* 色带四个点：v = 0 暗边 / 描边、0.45 本色、0.8 亮色、1 高光（tools/fx_bake.py 头注释） */
  const STOPS = [0, 0.45, 0.8, 1];
  const mix = (a, b, k) => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k].map(Math.round);
  const WHITE = [255, 255, 255], BLACK = [0, 0, 0];
  /* 由一个本色推出整条色带：暗边是本色压暗 + 往暖黑（角色线稿 INK）偏，亮色往白推 */
  const INK = [58, 44, 38];
  const palOf = (c, dk = 0.55, lt = 0.55) => [mix(mix(c, INK, 0.35), BLACK, dk * 0.6), c, mix(c, WHITE, lt), mix(c, WHITE, 0.92)];

  const PAL = {
    ember: [[150, 60, 10], [255, 140, 30], [255, 214, 120], [255, 250, 230]],
    gold: [[110, 60, 10], [255, 190, 40], [255, 236, 140], [255, 255, 240]],
    water: [[20, 58, 128], [70, 160, 240], [180, 226, 255], [255, 255, 255]],
    caramel: [[70, 38, 16], [176, 112, 52], [232, 186, 128], [255, 244, 222]],
    pearl: [[18, 10, 6], [56, 36, 22], [120, 86, 60], [250, 236, 220]],
    melon: [[110, 10, 20], [226, 40, 56], [255, 130, 130], [255, 236, 236]],
    seed: [[8, 6, 6], [34, 26, 24], [90, 80, 76], [240, 240, 240]],
    rind: [[20, 60, 24], [50, 140, 56], [200, 236, 190], [250, 255, 246]],
    wood: [[58, 40, 28], [150, 100, 58], [214, 170, 118], [250, 230, 200]],
    plastic: [[40, 44, 52], [96, 106, 120], [170, 180, 192], [240, 244, 250]],
    petal: [[110, 24, 52], [236, 72, 116], [255, 160, 186], [255, 236, 242]],
    petalDeep: [[80, 12, 34], [190, 34, 72], [244, 110, 140], [255, 220, 230]],
    feather: [[120, 104, 112], [228, 222, 226], [250, 248, 250], [255, 255, 255]],
    fluff: [[150, 136, 142], [214, 202, 208], [238, 232, 236], [255, 255, 255]],
    dust: [[104, 90, 78], [190, 174, 154], [228, 218, 202], [248, 242, 232]],
    grit: [[34, 26, 20], [90, 72, 58], [150, 128, 108], [220, 206, 190]],
    purple: [[40, 8, 70], [150, 60, 255], [214, 170, 255], [255, 246, 255]],
    red: [[90, 10, 30], [255, 70, 110], [255, 170, 190], [255, 245, 248]],
    blue: [[16, 30, 110], [80, 120, 255], [170, 200, 255], [245, 248, 255]],
    orange: [[100, 40, 10], [236, 110, 30], [255, 190, 110], [255, 246, 230]],
    rouge: [[110, 20, 70], [255, 92, 160], [255, 176, 212], [255, 240, 248]],
  };

  /* 贴图格 + 调色板 → 一张染好的小 canvas。getImageData 一次、逐像素查色带；按 key 缓存，之后只 drawImage */
  const rampCache = new Map();
  function ramp(sheet, cell, pal) {
    const key = sheet + '|' + cell + '|' + pal.join(';');
    let c = rampCache.get(key);
    if (c) return c;
    const [sx, sy, w, h] = META[sheet].cells[cell];
    /* 读像素在一张临时画布上做，结果 putImageData 进另一张普通画布：willReadFrequently 的画布是内存里的位图，
       拿它当 drawImage 的源每画一次都要重新上传一遍 —— 第一版直接用它当贴图，压测里粒子绘制比旧版慢两倍多 */
    const tmp = document.createElement('canvas');
    tmp.width = w; tmp.height = h;
    const tg = tmp.getContext('2d', { willReadFrequently: true });
    tg.drawImage(IMG[sheet], sx, sy, w, h, 0, 0, w, h);
    const im = tg.getImageData(0, 0, w, h), d = im.data;
    const lut = new Uint8ClampedArray(256 * 3);
    for (let i = 0; i < 256; i++) {
      const v = i / 255;
      let j = 0;
      while (j < 2 && v > STOPS[j + 1]) j++;
      const k = (v - STOPS[j]) / (STOPS[j + 1] - STOPS[j]);
      for (let ch = 0; ch < 3; ch++) lut[i * 3 + ch] = pal[j][ch] + (pal[j + 1][ch] - pal[j][ch]) * k;
    }
    for (let i = 0; i < d.length; i += 4) {
      const v = d[i];
      d[i] = lut[v * 3]; d[i + 1] = lut[v * 3 + 1]; d[i + 2] = lut[v * 3 + 2];
    }
    c = document.createElement('canvas');
    c.width = w; c.height = h;
    c.getContext('2d').putImageData(im, 0, 0);
    if (rampCache.size > 400) rampCache.clear();        // 配方里颜色是离散的，正常几十条；上限防将来有人写连续随机色
    rampCache.set(key, c);
    return c;
  }

  /* ---------- 粒子 ---------- */
  /* 一种粒子结构，几种画法（p.m）：
       'spr'    贴图，绕自身转（rot），可"翻面"（flip：按 cos 压扁一个轴，读成薄片在空中翻）
       'vel'    贴图顺着速度方向画（水滴 / 籽 / 锥形火花），速度越快拉得越长（stretch）
       'ring'   冲击波：半径 r0 → r1（easeOut），透明度 a → 0，可压扁（sq）
       'seq'    序列帧（刀光）：frames 按 ft 时间点切换
     age 从 -delay 起算：错开出场用模拟时间，不用 setTimeout（墙钟，顿帧冻住时它照走 —— trio.js sweep 那条注释） */
  const act = [], pool = [];
  const FADE_IN = 0.03;                                  // 淡入用绝对时间（skill：按寿命比例会让长寿命粒子迟到）
  function spawn(o) {
    if (act.length >= MAX) pool.push(act.shift());       // 满了回收最老的（同 ammo.js：新发射的才是观众正在看的）
    const p = pool.pop() || {};
    p.m = o.m || 'spr'; p.img = o.img; p.frames = o.frames || null; p.ft = o.ft || null;
    p.x = o.x; p.y = o.y; p.vx = o.vx || 0; p.vy = o.vy || 0;
    p.g = o.g || 0; p.drag = o.drag != null ? o.drag : 1;
    p.life = o.life; p.age = -(o.delay || 0);
    p.w = o.w; p.h = o.h != null ? o.h : o.w;
    p.s0 = o.s0 != null ? o.s0 : 1; p.s1 = o.s1 != null ? o.s1 : p.s0;
    p.rot = o.rot || 0; p.vrot = o.vrot || 0;
    p.flip = o.flip || 0; p.fph = Math.random() * 6.283;
    p.a = o.a != null ? o.a : 1; p.fo = o.fo != null ? o.fo : 0.35; p.fi = o.fi != null ? o.fi : FADE_IN;
    p.z = o.z || 0; p.sq = o.sq || 1; p.sway = o.sway || 0; p.stretch = o.stretch || 0;
    p.orb = o.orb || 0; p.ox = o.x; p.oy = o.y;           // orb：绕出生点公转的半径（星星绕头转）
    act.push(p);
    return p;
  }

  function update(dt) {
    for (let i = act.length - 1; i >= 0; i--) {
      const p = act[i];
      p.age += dt;
      if (p.age < 0) continue;
      if (p.age >= p.life) { act.splice(i, 1); pool.push(p); continue; }
      p.vy += p.g * dt;
      if (p.drag !== 1) { const d = Math.pow(p.drag, dt * 60); p.vx *= d; p.vy *= d; }   // pow(k, dt*60)：不随帧率漂移
      p.x += (p.vx + (p.sway ? Math.cos(p.fph + p.age * 3.1) * p.sway : 0)) * dt;
      p.y += p.vy * dt;
      p.rot += p.vrot * dt;
      if (p.orb) { p.ox += p.vx * dt; p.oy += p.vy * dt; }
    }
  }

  const easeOut = (u) => 1 - Math.pow(1 - u, 3);
  /* 圆团（尘、浆、光粒、冲击波、闪光）一律不转：rot 0 时只平移缩放，Skia 走不带旋转的快路径。软渲染压测里大贴图带旋转
     是粒子绘制的大头（第一版 14 ms，见 fx_lab.html ?bench=1&benchoff=beam），而圆团转不转肉眼看不出 */
  function draw(ctx) {
    if (!act.length) return;
    ctx.save();
    const T = ctx.getTransform();
    /* 两趟：z 0 碎片 / 余烬，z 1 瞬闪（闪光、冲击波）—— 闪光先 spawn，按出生顺序画会被同一下炸出来的碎片盖住 */
    for (let i = 0, z = 0; z < 2; i++) {
      if (i >= act.length) { i = -1; z++; continue; }
      const p = act[i];
      if (p.age < 0 || p.z !== z) continue;
      const u = p.age / p.life;
      let al;
      if (p.m === 'ring') al = p.a * Math.pow(1 - u, 1.3);
      else al = p.a * (p.fi > 0 ? Math.min(1, p.age / p.fi) : 1) * Math.min(1, (p.life - p.age) / (p.life * p.fo));
      if (al <= 0.01) continue;
      ctx.globalAlpha = al;
      let x = p.x, y = p.y;
      if (p.orb) { const ph = p.fph + p.age * 7.4; x = p.ox + Math.cos(ph) * p.orb; y = p.oy + Math.sin(ph) * p.orb * 0.42; }
      ctx.setTransform(T);
      ctx.translate(x, y);
      if (p.m === 'ring') {
        const r = p.s0 + (p.s1 - p.s0) * easeOut(u);
        ctx.drawImage(p.img, -r, -r * p.sq, r * 2, r * 2 * p.sq);
        continue;
      }
      const sc = p.s0 + (p.s1 - p.s0) * u;
      let w = p.w * sc, h = p.h * sc;
      if (p.m === 'vel') {
        const sp = Math.hypot(p.vx, p.vy);
        ctx.rotate(Math.atan2(p.vy, p.vx));
        w *= 1 + Math.min(1.6, sp * p.stretch);
        ctx.drawImage(p.img, -w * 0.75, -h / 2, w, h);   // 头在粒子位置前面一点，尾巴拖在后面
        continue;
      }
      if (p.rot) ctx.rotate(p.rot);
      if (p.flip) h *= 0.25 + 0.75 * Math.abs(Math.cos(p.fph + p.age * p.flip));
      const img = p.m === 'seq' ? p.frames[frameAt(p.ft, p.age)] : p.img;
      ctx.drawImage(img, -w / 2, -h / 2, w, h);
    }
    ctx.restore();
  }
  function frameAt(ft, t) { let k = 0; while (k + 1 < ft.length && t >= ft[k + 1]) k++; return k; }

  /* ---------- 小工具（配方用）---------- */
  const R = Math.random;
  const rr = (a, b) => a + R() * (b - a);
  const frag = (name, pal) => ramp('frag', name, pal);
  const glow = (name, pal) => ramp('glow', name, pal);
  const ringImg = (pal) => ramp('ring', 'ring', pal);
  /* 朝场内的扇形：side +1 打向左边的人，碎片往左飞（-side），a0 中心角、spread 张角 */
  function fan(side, spread, sp0, sp1, up) {
    const a = (R() - 0.5) * spread, sp = rr(sp0, sp1);
    return [-side * Math.cos(a) * sp, Math.sin(a) * sp - up];
  }

  /* 第一层：瞬闪（≤ 0.06 s）+ 冲击波。四角星闪一下就收、一团光，冲击波 0.18 s 从 0.3 扩到 1.2、透明度 1 → 0，
     外圈晚 0.03 s 再荡一道更淡更大的。全部普通混合：色带自己从白到暗边，亮底图上也立得住 */
  function flash(x, y, s, pal, o = {}) {
    const k = Math.min(s, 1.8), Rr = (o.R || 64) * k;
    spawn({ m: 'spr', img: glow('flare', pal), x, y, w: 170 * k, s0: 1.25, s1: 0.5, life: 0.07, a: 1, fo: 0.6, fi: 0, z: 1 });
    spawn({ m: 'spr', img: glow('mote', pal), x, y, w: 90 * k, s0: 0.8, s1: 1.3, life: 0.06, a: 0.95, fo: 0.7, fi: 0, z: 1 });
    spawn({ m: 'ring', img: ringImg(pal), x, y, s0: Rr * 0.3, s1: Rr * 1.2, life: 0.18, a: 1, sq: o.sq || 0.78, z: 1 });
    spawn({ m: 'ring', img: ringImg(pal), x, y, s0: Rr * 0.5, s1: Rr * 1.65, life: 0.26, a: 0.45, sq: o.sq || 0.78, delay: 0.03, z: 1 });
  }
  /* 锥形火花：头宽尾尖、顺速度拉长 */
  function sparks(x, y, side, s, n, pal, o = {}) {
    const k = Math.min(s, 1.8);
    for (let i = 0; i < n; i++) {
      const [vx, vy] = o.all ? (() => { const a = R() * 6.283, sp = rr(o.sp0 || 260, o.sp1 || 640) * k; return [Math.cos(a) * sp, Math.sin(a) * sp]; })()
        : fan(side, o.spread || 2.3, (o.sp0 || 260) * k, (o.sp1 || 700) * k, o.up != null ? o.up : 120);
      const j = rr(4, 16) * k, sp = Math.hypot(vx, vy) || 1;   // 出生点沿飞行方向错开一点：同一帧从一个点射出来读成一把扫帚
      spawn({ m: 'vel', img: glow('spark', pal), x: x + vx / sp * j, y: y + vy / sp * j, vx, vy, g: o.g != null ? o.g : 900, drag: 0.985,
              w: rr(20, 30) * k, h: rr(6, 9) * k, stretch: 0.0011, life: rr(0.18, 0.38), fo: 0.5, delay: rr(0, 0.03) });
    }
  }
  /* 实体碎片：sprite 带高光描边、转、翻、受重力。w0 / w1 写的是**碎片本身**多大（px）；frag 格子 64 里物体只占六七成、四周留空，
     画的时候按 CELL 放大到格子尺寸 —— 不然按格子写数，碎片比旧的矢量版小一圈（第一版胶片实测：木屑、花瓣、水珠都看不清） */
  const CELL = 1 / 0.68;
  function chips(x, y, side, n, names, pal, o) {
    for (let i = 0; i < n; i++) {
      const [vx, vy] = o.all ? (() => { const a = R() * 6.283, sp = rr(o.sp0, o.sp1); return [Math.cos(a) * sp, Math.sin(a) * sp - (o.up || 0)]; })()
        : fan(side, o.spread || 2.5, o.sp0, o.sp1, o.up || 200);
      const pl = Array.isArray(pal[0][0]) ? pal[i % pal.length] : pal;
      const sz = rr(o.w0, o.w1) * CELL;
      spawn({ m: o.vel ? 'vel' : 'spr', img: frag(names[i % names.length], pl), x: x + rr(-1, 1) * (o.jx || 0), y: y + rr(-1, 1) * (o.jy || 0),
              vx, vy, g: o.g, drag: o.drag || 0.99, w: sz, life: rr(o.l0, o.l1), rot: R() * 6.283, vrot: rr(-1, 1) * (o.vrot || 12),
              flip: o.flip || 0, sway: o.sway ? rr(o.sway * 0.6, o.sway) : 0, stretch: o.stretch || 0, a: 1, fo: o.fo || 0.3 });
    }
  }
  /* 软团（尘、浆、绒）：dust 贴图染色，胀开、慢下来 */
  function puffs(x, y, side, n, pal, o) {
    for (let i = 0; i < n; i++) {
      const [vx, vy] = fan(side, o.spread || 2.4, o.sp0, o.sp1, o.up || 40);
      spawn({ m: 'spr', img: ramp('dust', 'dust' + (i % 4), pal), x: x + rr(-1, 1) * (o.jx || 20), y: y + rr(-1, 1) * (o.jy || 14),
              vx, vy, g: o.g || 0, drag: o.drag || 0.92, w: rr(o.w0, o.w1), s0: o.s0 || 0.6, s1: o.s1 || 1.3,
              life: rr(o.l0, o.l1), a: o.a || 0.8, fo: 0.55, delay: o.delay ? rr(o.delay * 0.6, o.delay) : 0 });
    }
  }
  /* 第三层：余烬 —— 小光粒慢慢飘落 / 飘起、一闪一闪（flip 当闪烁），活得比碎片久 */
  function embers(x, y, s, n, pal, o = {}) {
    const k = Math.min(s, 1.8);
    for (let i = 0; i < n; i++) {
      const a = R() * 6.283, sp = rr(40, 170) * k;
      spawn({ m: 'spr', img: glow(o.flare ? 'flare' : 'mote', pal), x: x + rr(-30, 30) * k, y: y + rr(-30, 20) * k,
              vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - (o.up || 30), g: o.g != null ? o.g : 120, drag: 0.95, sway: rr(10, 30),
              w: rr(10, 18) * (o.big || 1), life: rr(0.55, 1.1), flip: o.flare ? 9 : 0, rot: o.flare ? R() : 0, vrot: o.flare ? rr(-3, 3) : 0, delay: rr(0.04, 0.12), a: 0.95, fo: 0.5 });
    }
  }

  /* ---------- 12 个命中配方（瞬闪 → 主体 → 余烬）。tint 与 main.js 同名配方逐字一致（impact 拿它给挨打的人染色）---------- */
  function layered(def) {
    const L = { flash: def.flash, body: def.body, ember: def.ember };
    return { tint: def.tint, layers: L, drip: def.drip,
             burst(x, y, side, s) { L.flash(x, y, side, s); L.body(x, y, side, s); L.ember(x, y, side, s); } };
  }
  const n = (c, s) => Math.max(1, Math.round(c * s));
  const kk = (s) => Math.min(s, 1.8);

  const RECIPE = {
    /* 通用撞击：橙闪 + 冲击波；暖橙锥形火花 + 灰褐碎块 + 一撮灰；余烬是落下来的橙色小光粒 */
    thud: layered({
      tint: [255, 224, 186],
      flash: (x, y, side, s) => flash(x, y, s, PAL.ember),
      body(x, y, side, s) {
        sparks(x, y, side, s, n(18, s), PAL.ember);
        chips(x, y, side, n(8, s), ['shard0', 'shard1', 'chip0'], PAL.grit, { sp0: 170 * kk(s), sp1: 460 * kk(s), g: 980, w0: 14, w1: 24, l0: 0.6, l1: 1.0, flip: 8, vrot: 14 });
      },
      ember(x, y, side, s) {
        embers(x, y, s, n(7, s), PAL.ember);
        puffs(x, y, side, n(3, s), PAL.dust, { sp0: 60, sp1: 180, w0: 46 * kk(s), w1: 70 * kk(s), l0: 0.5, l1: 0.8, a: 0.4, delay: 0.1 });
      },
    }),
    /* 打懵：金闪；大金星绕头公转（orb）+ 小金星飞散 + 金色火花；余烬是一闪一闪的小四角星 */
    star: layered({
      tint: [255, 242, 196],
      flash: (x, y, side, s) => flash(x, y, s, PAL.gold),
      body(x, y, side, s) {
        const k = kk(s);
        for (let i = 0; i < n(5, s); i++)
          spawn({ m: 'spr', img: frag('star' + (i % 2), PAL.gold), x: x - side * 18, y: y - rr(40, 90), vx: -side * rr(10, 60), vy: rr(-70, -30), g: 60, drag: 0.94,
                  orb: rr(26, 44) * k, w: rr(34, 46) * k, life: rr(0.8, 1.2), rot: R() * 6.28, vrot: rr(-4, 4), flip: 5, fo: 0.3 });
        chips(x, y, side, n(9, s), ['star0', 'star1'], PAL.gold, { sp0: 200 * k, sp1: 520 * k, g: 700, w0: 18, w1: 28, l0: 0.5, l1: 0.9, vrot: 10, flip: 7 });
        sparks(x, y, side, s, n(10, s), PAL.gold);
      },
      ember: (x, y, side, s) => embers(x, y, s, n(6, s), PAL.gold, { flare: true, big: 1.6, g: 60 }),
    }),
    /* 奶茶：焦糖闪；焦糖液滴（顺速度拉长）+ 深褐珍珠弹开 + 几团浆糊住（drag 大，停在身上）；余烬是往下滴的小滴 */
    splash: layered({
      tint: [246, 226, 198],
      flash: (x, y, side, s) => flash(x, y, s, PAL.caramel, { R: 58 }),
      body(x, y, side, s) {
        const k = kk(s);
        puffs(x, y, side, n(5, s), PAL.caramel, { sp0: 90 * k, sp1: 260 * k, drag: 0.86, w0: 40 * k, w1: 64 * k, l0: 1.0, l1: 1.5, a: 0.7, s0: 0.5, s1: 1.1 });
        chips(x, y, side, n(16, s), ['drop0', 'drop1'], PAL.caramel, { sp0: 240 * k, sp1: 640 * k, g: 1150, w0: 22, w1: 34, l0: 0.5, l1: 0.9, vel: true, stretch: 0.0009 });
        chips(x, y, side, n(12, s), ['pearl'], PAL.pearl, { sp0: 220 * k, sp1: 520 * k, up: 300, g: 1180, w0: 18, w1: 26, l0: 1.0, l1: 1.6, vrot: 12 });
      },
      ember(x, y, side, s) {
        chips(x, y + 10, side, n(6, s), ['drop1'], PAL.caramel, { sp0: 20, sp1: 90, up: 0, g: 700, w0: 12, w1: 18, l0: 0.6, l1: 1.0, vel: true, stretch: 0.002, jx: 40, jy: 30 });
      },
    }),
    /* 枕头：浅粉一闪（小）；羽毛打着旋翻着往下飘（flip + sway，重力小）+ 几团绒；余烬是更小的绒羽慢落 */
    feather: layered({
      tint: [255, 238, 240],
      flash: (x, y, side, s) => flash(x, y, s, PAL.fluff, { R: 50 }),
      body(x, y, side, s) {
        const k = kk(s);
        puffs(x, y, side, n(4, s), PAL.fluff, { sp0: 60 * k, sp1: 220 * k, w0: 50 * k, w1: 80 * k, l0: 0.5, l1: 0.9, a: 0.55 });
        chips(x, y, side, n(20, s), ['feather0', 'feather1'], PAL.feather, { sp0: 180 * k, sp1: 560 * k, up: 170, g: 150, drag: 0.987, sway: 70,
              w0: 38, w1: 54, l0: 1.4, l1: 2.6, vrot: 4, flip: 3.2, jx: 30, jy: 40 });
      },
      ember(x, y, side, s) {
        chips(x, y, side, n(8, s), ['feather0', 'feather1'], PAL.feather, { all: true, sp0: 40, sp1: 160, up: 60, g: 60, drag: 0.98, sway: 40,
              w0: 22, w1: 28, l0: 1.6, l1: 2.6, vrot: 3, flip: 2.5, jx: 50, jy: 40 });
      },
    }),
    /* 西瓜：红闪；红瓤液滴 + 黑籽（水滴形，顺速度）+ 几片弯的绿皮 + 两团瓤糊住；余烬是往下滴的红汁和两三颗籽 */
    melon: layered({
      tint: [255, 214, 206],
      flash: (x, y, side, s) => flash(x, y, s, PAL.melon),
      body(x, y, side, s) {
        const k = kk(s);
        puffs(x, y, side, n(4, s), PAL.melon, { sp0: 90 * k, sp1: 240 * k, drag: 0.86, w0: 40 * k, w1: 60 * k, l0: 0.9, l1: 1.4, a: 0.7, s0: 0.5, s1: 1.05 });
        chips(x, y, side, n(12, s), ['drop0', 'drop1'], PAL.melon, { sp0: 240 * k, sp1: 600 * k, g: 1150, w0: 22, w1: 32, l0: 0.5, l1: 0.9, vel: true, stretch: 0.0009 });
        chips(x, y, side, n(16, s), ['seed0', 'seed1'], PAL.seed, { sp0: 260 * k, sp1: 560 * k, up: 300, g: 1180, w0: 14, w1: 20, l0: 0.9, l1: 1.5, vel: true, stretch: 0.0005 });
        chips(x, y, side, n(4, s), ['rind0', 'rind1'], PAL.rind, { sp0: 200 * k, sp1: 420 * k, up: 260, g: 1250, w0: 34, w1: 46, l0: 0.8, l1: 1.2, vrot: 10, flip: 6 });
      },
      ember(x, y, side, s) {
        chips(x, y + 10, side, n(5, s), ['drop1'], PAL.melon, { sp0: 20, sp1: 90, up: 0, g: 700, w0: 12, w1: 18, l0: 0.6, l1: 1.0, vel: true, stretch: 0.002, jx: 40, jy: 30 });
      },
    }),
    /* 斩：本色闪；两道交叉刀光（序列帧）+ 沿刀口飞的锥形火花；余烬是本色小光粒。颜色取 B23 斩痕的绿 */
    slash: layered({
      tint: [255, 242, 196],
      flash: (x, y, side, s) => flash(x, y, s, palOf([90, 230, 110]), { R: 52 }),
      body(x, y, side, s) {
        slash(x, y, -0.5, 230, [90, 230, 110], 0.5);
        slash(x, y, 0.75, 200, [90, 230, 110], 0.5, 0.06);
        sparks(x, y, side, s, n(6, s), palOf([90, 230, 110]), { all: true, g: 300, sp0: 200, sp1: 420 });
      },
      ember: (x, y, side, s) => embers(x, y, s, n(6, s), palOf([90, 230, 110])),
    }),
    /* 花束：粉闪；花瓣打着旋飘（深浅两种）+ 金色火花（包装纸反光）；余烬是慢落的小花瓣 */
    petal: layered({
      tint: [255, 214, 226],
      flash: (x, y, side, s) => flash(x, y, s, PAL.petal),
      body(x, y, side, s) {
        const k = kk(s);
        chips(x, y, side, n(22, s), ['petal0', 'petal1', 'petal2'], [PAL.petal, PAL.petal, PAL.petalDeep], { sp0: 200 * k, sp1: 560 * k, up: 180, g: 140, drag: 0.987, sway: 60,
              w0: 30, w1: 44, l0: 1.3, l1: 2.4, vrot: 3.5, flip: 3, jx: 30, jy: 40 });
        sparks(x, y, side, s, n(8, s), PAL.gold);
      },
      ember(x, y, side, s) {
        chips(x, y, side, n(7, s), ['petal1', 'petal2'], [PAL.petal, PAL.petalDeep], { all: true, sp0: 40, sp1: 140, up: 40, g: 70, drag: 0.98, sway: 40,
              w0: 18, w1: 24, l0: 1.6, l1: 2.6, vrot: 2.5, flip: 2.5, jx: 50, jy: 40 });
      },
    }),
    /* 硬东西崩碎（松果、木头）：橙闪；三角木屑（两面一明一暗，翻转）+ 橙色锥形火花 + 一撮灰；余烬是细木渣和灰 */
    debris: layered({
      tint: [226, 238, 255],
      flash: (x, y, side, s) => flash(x, y, s, PAL.ember, { R: 70 }),
      body(x, y, side, s) {
        const k = kk(s);
        chips(x, y, side, n(18, s), ['chip0', 'chip1', 'chip2'], PAL.wood, { sp0: 300 * k, sp1: 700 * k, up: 300, g: 1450, drag: 0.995, w0: 18, w1: 32, l0: 0.55, l1: 1.0, vrot: 20, flip: 10 });
        sparks(x, y, side, s, n(16, s), PAL.ember);
      },
      ember(x, y, side, s) {
        chips(x, y, side, n(10, s), ['chip1', 'chip2'], PAL.wood, { sp0: 60, sp1: 220, up: 120, g: 900, w0: 12, w1: 17, l0: 0.8, l1: 1.3, vrot: 16, flip: 9, jx: 20, jy: 20 });
        puffs(x, y, side, n(3, s), PAL.dust, { sp0: 60, sp1: 180, w0: 46 * kk(s), w1: 70 * kk(s), l0: 0.6, l1: 1.0, a: 0.45, delay: 0.1 });
      },
    }),
    /* 紫色光球（"茈"）：一圈紫冲击波先**往里收**（0.12 s）再往外炸；红、蓝锥形火花对着甩；余烬是往命中点吸的紫光粒 */
    hollow: layered({
      tint: [226, 196, 255],
      flash(x, y, side, s) {
        const k = kk(s);
        spawn({ m: 'ring', img: ringImg(PAL.purple), x, y, s0: 150 * k, s1: 10 * k, life: 0.12, a: 0.9, sq: 0.85 });
        flash(x, y, s, PAL.purple, { R: 76 });
      },
      body(x, y, side, s) {
        sparks(x, y, side, s, n(8, s), PAL.red, { all: true, g: 120 });
        sparks(x, y, side, s, n(8, s), PAL.blue, { all: true, g: 120 });
      },
      ember(x, y, side, s) {
        const k = kk(s);
        for (let i = 0; i < n(12, s); i++) {                // 吸：出生在一圈上，速度指向命中点，活到正好飞到
          const a = R() * 6.283, d = rr(90, 150) * k, life = rr(0.3, 0.5);
          spawn({ m: 'spr', img: glow('mote', PAL.purple), x: x + Math.cos(a) * d, y: y + Math.sin(a) * d * 0.8, vx: -Math.cos(a) * d / life, vy: -Math.sin(a) * d * 0.8 / life,
                  w: rr(16, 26), s0: 1, s1: 0.4, life, delay: rr(0.1, 0.35), a: 1, fo: 0.3 });
        }
      },
    }),
    /* 水：水蓝闪 + 冲击波；带高光的透明水滴（顺速度拉长）+ 一层水雾；余烬是往下滴的小水珠。drip：每滴打上去溅两三颗 + 偶尔一圈小水环 */
    water: layered({
      tint: [196, 228, 255],
      flash: (x, y, side, s) => flash(x, y, s, PAL.water),
      body(x, y, side, s) {
        const k = kk(s);
        chips(x, y, side, n(16, s), ['drop0', 'drop1'], PAL.water, { sp0: 220 * k, sp1: 620 * k, up: 220, g: 1100, w0: 20, w1: 32, l0: 0.45, l1: 0.8, vel: true, stretch: 0.0009 });
        puffs(x, y, side, n(3, s), PAL.water, { sp0: 60, sp1: 180, w0: 40 * k, w1: 64 * k, l0: 0.4, l1: 0.6, a: 0.35 });
      },
      ember(x, y, side, s) {
        chips(x, y + 10, side, n(6, s), ['drop1'], PAL.water, { sp0: 20, sp1: 90, up: 0, g: 800, w0: 12, w1: 16, l0: 0.5, l1: 0.9, vel: true, stretch: 0.002, jx: 40, jy: 30 });
      },
      drip(x, y, side) {
        chips(x, y, side, 2, ['drop1'], PAL.water, { sp0: 120, sp1: 300, up: 160, g: 1100, w0: 13, w1: 18, l0: 0.3, l1: 0.5, vel: true, stretch: 0.0012 });
        if (R() < 0.3) spawn({ m: 'ring', img: ringImg(PAL.water), x, y, s0: 8, s1: 34, life: 0.16, a: 0.8, sq: 0.78 });
      },
    }),
    /* 篮球砸中（不碎）：橙闪 + 一道大冲击波（弹的那一下）+ 速度线式的锥形火花 + 落灰；余烬是灰 */
    ball: layered({
      tint: [255, 255, 255],
      flash: (x, y, side, s) => flash(x, y, s, PAL.orange, { R: 80 }),
      body(x, y, side, s) {
        sparks(x, y, side, s, n(14, s), PAL.orange, { all: true, g: 200, sp0: 380, sp1: 760 });
        puffs(x, y, side, n(5, s), PAL.dust, { sp0: 60, sp1: 200, w0: 50 * kk(s), w1: 84 * kk(s), l0: 0.5, l1: 0.9, a: 0.5 });
      },
      ember: (x, y, side, s) => embers(x, y, s, n(5, s), PAL.orange),
    }),
    /* 口红：玫红闪；玫红液滴 + 粉色珠子；余烬是一闪一闪的粉色小星芒 */
    rouge: layered({
      tint: [255, 170, 210],
      flash: (x, y, side, s) => flash(x, y, s, PAL.rouge, { R: 54 }),
      body(x, y, side, s) {
        const k = 0.5 + s;                                // 同 main.js rouge：档 1 尺寸给足
        chips(x, y, side, n(8, k), ['drop0', 'drop1'], PAL.rouge, { sp0: 200, sp1: 480, up: 200, g: 1000, w0: 18, w1: 28, l0: 0.45, l1: 0.8, vel: true, stretch: 0.0009 });
        chips(x, y, side, n(6, k), ['pearl'], PAL.rouge, { sp0: 180, sp1: 400, up: 200, g: 900, w0: 14, w1: 20, l0: 0.45, l1: 0.8, vrot: 6 });
        sparks(x, y, side, s, n(6, k), PAL.rouge);
      },
      ember: (x, y, side, s) => embers(x, y, s, n(5, 0.5 + s), PAL.rouge, { flare: true, big: 1.4, g: 40 }),
    }),
  };

  /* ---------- 斩痕：刀光序列帧（划开 → 满弧 → 拉丝 → 碎散），带拖尾渐隐 ---------- */
  function slash(x, y, ang, len, rgb, life = 0.45, delay = 0) {
    const pal = palOf(rgb, 0.7, 0.6);
    const frames = [0, 1, 2, 3].map(i => ramp('slash', 'slash' + i, pal));
    const ft = [0, 0.05, 0.05 + life * 0.25, 0.05 + life * 0.55];
    /* 序列帧 256×160，弧心在下沿中点、半径 0.74 高 —— 让弧中点落在 (x, y)：往弧心方向挪 */
    const w = len * 1.15, h = w * 160 / 256;
    spawn({ m: 'seq', frames, ft, x: x - Math.sin(ang) * h * 0.24, y: y + Math.cos(ang) * h * 0.24, w, h, rot: ang, life, delay, a: 1, fo: 0.45 });
  }

  /* ---------- 光束 ---------- */
  /* 每人一个句柄：按 cfg.beam 把贴图条染好（外晕 / 暗轮廓 / 中层 / 芯各一张调色板），宽度从 layers 里取 */
  function beam(B) {
    const L = B.layers, inner = L[L.length - 1][1], hiC = L.length > 2 ? L[L.length - 2][1] : inner;
    const edge = B.edge, glowC = B.glow;
    const pals = {
      halo: [mix(edge, INK, 0.2), mix(edge, glowC, 0.35), glowC, hiC],
      body: [mix(edge, INK, 0.55), edge, glowC, hiC],
      mid: [edge, mix(edge, glowC, 0.5), glowC, hiC],
      core: [glowC, hiC, mix(hiC, WHITE, 0.6), WHITE],
      spark: [mix(edge, INK, 0.3), glowC, hiC, WHITE],
    };
    /* 宽度：外晕按最外层、光身和中层按第二层、芯按倒数第二层（最内一层是白芯线，贴图条芯本来就白）。外晕 / 中层 / 芯的横截面
       是高斯，可见宽度只有条高的四成上下，所以放大；光身是平顶管，条高九成都实，按 1.15 */
    const L1 = (L[1] || L[0])[0];
    const Wh = L[0][0] * 2.2, Wb = L1 * 1.15, Wm = L1 * 1.5, Wc = Math.max(9, (L.length > 2 ? L[L.length - 2] : L[0])[0] * 1.7);
    /* 出口 / 光头闪光的尺度：按外晕宽但封顶 —— G23 外晕 218 px，照比例画出口四角星是半径三百多的一团，把发波的人整个盖掉 */
    const Wf = Math.min(Wh, 70);
    /* 名、用哪条贴图、宽、alpha、滚动 px/s、贴图横向拉伸。从外往里：外晕（一缕缕的软光）→ 光身（平顶管，带 2~3 px 暗边）→
       中层（亮纹，流得更快）→ 芯。光身是第三版加的：只有高斯三层时 G23 的气浪读成一团半透明的雾，旧的平涂反而因为最外一层
       暗红立得住 —— 亮底图上光束也要靠轮廓（skill chashouji-fx） */
    const layers = [['halo', 'halo', Wh, 0.85, 240, 1.6], ['body', 'body', Wb, 1, 380, 1.2], ['mid', 'mid', Wm, 0.7, 560, 1.0], ['core', 'core', Wc, 1, 900, 0.8]];
    let strips = null, pats = new WeakMap();
    const S = { ph: 'rest', t: 0, from: null, dir: null, to: null, e: 0, k: 1, x: 0, y: 0, r: 0, acc: 0, accSp: 0, accRing: 0, hit: false };
    function prep() { if (!strips) strips = layers.map(([n, tex]) => ramp('beam', tex, pals[n])); return strips; }
    function patsFor(ctx) {
      let p = pats.get(ctx);
      if (!p) { p = prep().map(c => ctx.createPattern(c, 'repeat')); pats.set(ctx, p); }
      return p;
    }
    /* 路径：from 沿 dir 出去、弯到 to 的二次贝塞尔（dir null 或与 from→to 差不到 2° 就是直线）。返回采样点与累计弧长 */
    function path() {
      const [x0, y0] = S.from, [x1, y1] = S.to, D = Math.hypot(x1 - x0, y1 - y0) || 1;
      let cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, curved = false;
      if (S.dir != null) {
        const da = Math.atan2(Math.sin(S.dir - Math.atan2(y1 - y0, x1 - x0)), Math.cos(S.dir - Math.atan2(y1 - y0, x1 - x0)));
        if (Math.abs(da) > 0.035) { cx = x0 + Math.cos(S.dir) * D * 0.42; cy = y0 + Math.sin(S.dir) * D * 0.42; curved = true; }
      }
      const N = curved ? 24 : 1, pts = [], len = [0];
      for (let i = 0; i <= N; i++) {
        const t = i / N, q = 1 - t;
        pts.push([q * q * x0 + 2 * q * t * cx + t * t * x1, q * q * y0 + 2 * q * t * cy + t * t * y1]);
        if (i) len.push(len[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
      }
      return { pts, len, total: len[N] };
    }
    function along(P, d) {                                 // 弧长 d 处的点和切向
      let i = 1;
      while (i < P.len.length - 1 && P.len[i] < d) i++;
      const a = P.pts[i - 1], b = P.pts[i], seg = P.len[i] - P.len[i - 1] || 1, u = Math.min(1, Math.max(0, (d - P.len[i - 1]) / seg));
      return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, Math.atan2(b[1] - a[1], b[0] - a[0])];
    }

    return {
      look: pals, widths: [Wh, Wb, Wm, Wc],
      charge(dt, x, y, r) {
        if (!ready()) return;
        S.ph = 'charge'; S.x = x; S.y = y; S.r = r; S.t += dt;
        S.acc += dt * 34;                                  // 往手心吸的光粒：出生在 3r 外一圈，活到正好飞到
        while (S.acc >= 1) {
          S.acc -= 1;
          const a = R() * 6.283, d = r * rr(2.2, 3.4) + 20, life = rr(0.22, 0.36);
          spawn({ m: 'spr', img: glow('mote', pals.spark), x: x + Math.cos(a) * d, y: y + Math.sin(a) * d, vx: -Math.cos(a) * d / life, vy: -Math.sin(a) * d / life,
                  w: rr(8, 14), s0: 1, s1: 0.35, life, a: 1, fo: 0.25 });
        }
      },
      fire(dt, from, dir, to, e, k) {
        if (!ready()) return;
        if (S.ph !== 'fire') {                             // 开轰那一下：出口大闪 + 一圈冲击波
          S.t = 0; S.acc = S.accSp = S.accRing = 0; S.hit = false;
          spawn({ m: 'spr', img: glow('flare', pals.spark), x: from[0], y: from[1], w: Wf * 4, s0: 1.3, s1: 0.6, life: 0.12, rot: R(), a: 1, fo: 0.6 });
          spawn({ m: 'ring', img: ringImg(pals.spark), x: from[0], y: from[1], s0: Wf * 0.4, s1: Wf * 1.6, life: 0.2, a: 0.9, sq: 0.8 });
        }
        S.ph = 'fire'; S.from = from; S.dir = dir; S.to = to; S.e = e; S.k = k; S.t += dt;
        const P = path(), Ld = P.total * e, ang0 = along(P, 0)[2];
        /* 出口散射：沿出口方向 ±0.9 rad 的锥形火花 */
        S.accSp += dt * 36 * k;
        while (S.accSp >= 1) {
          S.accSp -= 1;
          const a = ang0 + rr(-0.9, 0.9), sp = rr(180, 420);
          spawn({ m: 'vel', img: glow('spark', pals.spark), x: from[0], y: from[1], vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, g: 300, drag: 0.96,
                  w: rr(16, 26), h: rr(5, 8), stretch: 0.0015, life: rr(0.14, 0.26), a: 1, fo: 0.5 });
        }
        /* 沿途甩光粒：每 40 px 一格，每格每秒约 7 颗，往两侧飘（略往前冲） */
        S.acc += dt * 7 * k * Ld / 40;
        while (S.acc >= 1) {
          S.acc -= 1;
          const [px, py, a] = along(P, rr(20, Math.max(21, Ld - 10))), side = R() < 0.5 ? -1 : 1, sp = rr(30, 110);
          spawn({ m: 'spr', img: glow('mote', R() < 0.5 ? pals.spark : pals.mid), x: px + Math.cos(a + 1.571) * side * Wm * 0.3, y: py + Math.sin(a + 1.571) * side * Wm * 0.3,
                  vx: Math.cos(a + 1.571) * side * sp + Math.cos(a) * 60, vy: Math.sin(a + 1.571) * side * sp + Math.sin(a) * 60 - 20, g: -30, drag: 0.95,
                  w: rr(8, 15), s0: 1, s1: 0.3, life: rr(0.3, 0.5), a: 1, fo: 0.4 });
        }
        /* 末端：伸到了（e = 1）才溅 —— 反溅的锥形火花 + 每 0.11 s 一圈冲击波 */
        if (e >= 1) {
          const [hx, hy, a] = along(P, Ld);
          if (!S.hit) { S.hit = true; S.accRing = 0.11; }   // 伸到的那一帧先溅一圈
          S.accRing += dt;
          if (S.accRing >= 0.11) { S.accRing -= 0.11; spawn({ m: 'ring', img: ringImg(pals.spark), x: hx, y: hy, s0: Wf * 0.35, s1: Wf * 1.5, life: 0.2, a: 0.85 * k, sq: 0.8 }); }
          for (let i = 0; i < 2; i++) if (R() < dt * 26 * k) {
            const b = a + Math.PI + rr(-1.3, 1.3), sp = rr(220, 520);
            spawn({ m: 'vel', img: glow('spark', pals.spark), x: hx, y: hy, vx: Math.cos(b) * sp, vy: Math.sin(b) * sp, g: 650, drag: 0.98,
                    w: rr(18, 28), h: rr(6, 9), stretch: 0.0015, life: rr(0.18, 0.32), a: 1, fo: 0.5 });
          }
        }
      },
      rest() { S.ph = 'rest'; },
      draw(ctx) {
        if (!ready() || S.ph === 'rest') return;
        if (S.ph === 'charge') { drawCharge(ctx); return; }
        const P = path(), Ld = P.total * S.e;
        if (Ld < 2) return;
        const pt = patsFor(ctx), t = S.t, k = S.k;
        ctx.save();
        /* 三层：外晕 → 中层 → 芯，各自滚动（越往里越快：读出"芯在冲、晕在拖"） */
        for (let li = 0; li < layers.length; li++) {
          const [, , W0, al, spd, sx] = layers[li], pat = pt[li];
          ctx.globalAlpha = al * k;
          ctx.fillStyle = pat;
          let d = 0;
          for (let i = 1; i < P.pts.length && d < Ld; i++) {
            const a = P.pts[i - 1], b = P.pts[i], seg = P.len[i] - P.len[i - 1];
            const segL = Math.min(seg, Ld - d);
            const mid = d + segL / 2;
            /* 粗细：出口 28 px 内从 0.55 胀满，光头前 20 px 收到 0.8；一道往前走的波纹（同一处粗细随时间起伏 = 在流） */
            const w = W0 * (0.6 + 0.4 * k) * (0.55 + 0.45 * Math.min(1, mid / 28)) * (Ld - mid < 20 ? 0.8 + 0.2 * (Ld - mid) / 20 : 1)
              * (1 + 0.08 * Math.sin(mid * 0.045 - t * 30) * (li === 0 ? 1.6 : 1));
            const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
            ctx.save();
            ctx.translate(a[0], a[1]);
            ctx.rotate(ang);
            ctx.scale(sx, w / 64);
            /* 贴图坐标：沿弧长 d、减去滚动量 —— 噪声往光头那边流 */
            ctx.translate(-((d - t * spd) / sx % 256), -32);
            ctx.fillRect(((d - t * spd) / sx % 256), 0, (segL + (P.pts.length > 2 ? 0.6 : 0)) / sx, 64);
            ctx.restore();
            d += seg;
          }
        }
        /* 光头：一团光 + 小四角星；出口：四角星闪光（转、跳） */
        const [hx, hy] = along(P, Ld), [fx, fy, a0] = along(P, 0);
        ctx.globalAlpha = k;
        const head = ramp('glow', 'mote', pals.mid), fl = ramp('glow', 'flare', pals.spark);
        const hr = Math.max(Wf, Wb * 0.8) * (1.1 + 0.1 * Math.sin(t * 47));
        ctx.drawImage(head, hx - hr, hy - hr, hr * 2, hr * 2);
        const fr = Wf * (1.5 + 0.25 * Math.sin(t * 37)) * (t < 0.1 ? 1.6 - 6 * t : 1);
        ctx.translate(fx, fy); ctx.rotate(a0 + t * 3);
        ctx.drawImage(fl, -fr, -fr, fr * 2, fr * 2);
        ctx.restore();
      },
    };
    function drawCharge(ctx) {
      const r = S.r, t = S.t;
      const orb = ramp('glow', 'mote', pals.mid), fl = ramp('glow', 'flare', pals.spark);
      ctx.save();
      const R0 = r * 1.6 * (1 + 0.08 * Math.sin(t * 40));
      ctx.drawImage(orb, S.x - R0, S.y - R0, R0 * 2, R0 * 2);
      ctx.translate(S.x, S.y); ctx.rotate(t * 4);
      const F = r * 2.2 * (0.85 + 0.15 * Math.sin(t * 23));
      ctx.globalAlpha = 0.9;
      ctx.drawImage(fl, -F, -F, F * 2, F * 2);
      ctx.restore();
    }
  }

  /* ---------- 尘土（P8）---------- */
  /* 落地：左右两团往外散（0.35 s 主体，尾巴再拖一点），中间一圈贴地的尘环、几颗小石子蹦一下。
     尘团贴图 128 格里烟只占中间六成，尺寸按格子写（第一版按烟本身写 46~74，胶片上是脚边两小撮，读不出"砸地"） */
  function land(x, y, s = 1) {
    if (!ready()) return;
    const k = Math.min(1.6, s);
    for (const d of [-1, 1]) {
      for (let i = 0; i < 6; i++) {
        const sp = rr(90, 300) * k;
        spawn({ m: 'spr', img: ramp('dust', 'dust' + (i % 4), PAL.dust), x: x + d * rr(8, 30) * k, y: y - rr(4, 18) * k,
                vx: d * sp, vy: -rr(20, 90) * k, g: 30, drag: 0.9, w: rr(90, 150) * k, s0: 0.5, s1: 1.3,
                life: rr(0.38, 0.6), a: 0.9, fo: 0.6 });
      }
    }
    spawn({ m: 'ring', img: ringImg(PAL.dust), x, y, s0: 30 * k, s1: 170 * k, life: 0.32, a: 0.7, sq: 0.22 });
    for (let i = 0; i < 6; i++) {
      const d = R() < 0.5 ? -1 : 1;
      spawn({ m: 'spr', img: frag('shard' + (i % 2), PAL.grit), x: x + rr(-20, 20), y: y - 4, vx: d * rr(60, 200), vy: -rr(140, 300), g: 1400, drag: 0.99,
              w: rr(10, 15) * CELL, life: rr(0.3, 0.45), rot: R() * 6.28, vrot: rr(-15, 15), a: 1, fo: 0.3 });
    }
  }
  /* 滑行 / 冲刺 / 骑：接触点每秒 |vx|/40 团尘（封顶 16）往身后翻起、一半带一颗砂粒，速度越快越密。
     尘团是这里最大的贴图，第一版 |vx|/18（600 px/s 时每秒 33 团、一条滑行同时挂 15 团）在压测里是粒子绘制最贵的一项；
     一团活 0.45 s、胀到 1.4 倍，每秒十几团已经连成一条 */
  function skid(st, x, y, vx, dt, s = 1) {
    if (!ready()) return;
    const sp = Math.abs(vx);
    if (sp < 40) return;
    const k = Math.min(1.6, s), back = vx > 0 ? -1 : 1;
    st._fxSkid = (st._fxSkid || 0) + dt * Math.min(16, sp / 40);
    while (st._fxSkid >= 1) {
      st._fxSkid -= 1;
      spawn({ m: 'spr', img: ramp('dust', 'dust' + ((R() * 4) | 0), PAL.dust), x: x + rr(-10, 10), y: y - rr(2, 10),
              vx: back * rr(20, 90) + vx * 0.15, vy: -rr(20, 70), g: -10, drag: 0.92, w: rr(60, 100) * k, s0: 0.5, s1: 1.4,
              life: rr(0.35, 0.55), a: 0.8, fo: 0.6 });
      if (R() < 0.5) spawn({ m: 'spr', img: frag('shard' + ((R() * 2) | 0), PAL.grit), x, y: y - 3, vx: back * rr(40, 160), vy: -rr(80, 200), g: 1300,
                             w: rr(7, 10) * CELL, life: rr(0.25, 0.4), rot: R() * 6.28, vrot: rr(-15, 15), a: 1, fo: 0.3 });
    }
  }

  function clear() { while (act.length) pool.push(act.pop()); }

  return { load, ready, update, draw, clear, count: () => act.length, RECIPE, beam, slash, land, skid, PAL, palOf, ramp };
})();
