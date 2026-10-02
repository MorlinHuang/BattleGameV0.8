/* light.js —— 人物的立体感：接地阴影 / 吃场景光 / 轮廓光（2026-10-01，docs/三人组角色规范.md「立体感」）。
 *
 * 用户："三人组 60 人在游戏里要更真实、高级、精细，更立体，加阴影、光线，看起来不那么像纸片人"。
 * 先量了（tools/light/measure_lum.py）：雷雨夜三间房的背景平均 L* 25~46、最亮的 p90 只有 39~58，而男女主平均 L* 67~69、
 * p90 92，三人组彩度 p90 55~74 是背景的 2~3 倍 —— 人是按白天棚拍的亮度画的，贴在夜里的房间上，就是贴纸。
 * 所以三样东西在引擎层统一做，60 人和男女主走同一套（男女主不做的话，三人组压暗了反而衬得主角更像贴纸）：
 *
 * 1. 接地阴影（contact）：每一帧的剪影底边自动量出来（profile：贴图缩到 1/4 读 alpha，在 Worker 里量、按格缓存），
 *    贴地的几段（脚、轮子、趴着的身子）各一团深的接触影，整片靠近地面的部分一团大而淡的环境影，略往背光那边偏。
 *    离地（进场跳起、腾空、走路一颠）按离地高度变淡变散。站在场景层（墙沿、石台）上的人，影子画在台面上（场景层之后、人之前）。
 * 2. 吃场景光（grade）：人乘一层"此处的光色"（multiply，房间底色 × 亮度 + 附近每盏灯按距离加回来），
 *    沿光的方向从亮到暗渐变（朝灯那侧亮、背灯那侧暗一点 = 体积），再降一点饱和（saturation 混灰）——
 *    乘法不抬黑：描边和暗部还是干净的黑，不会像盖一层半透明色那样发灰发脏。
 * 3. 轮廓光（rim）：朝主光那一侧、描边以内一窄条（剪影往光的方向挪 w 还在、挪 w + r 就出界的那一圈），用 screen 叠上灯的颜色。
 *    描边只有 1~2px（量过），条带从描边里面开始，线条不被吃掉。
 * **都在贴图空间里做、按格缓存**（tex / lit）：一张图集（姿势图、挂件、布景）打好光（连轮廓光一起烘进去）的副本按格懒算，
 *    这一格的光（key：乘色、方向、轮廓光颜色量化后）变了才重算这一格；每帧画人就是照常 drawImage 打好光的那张，不多画一笔。
 *    第一版每帧把每个人画进离屏再合成十来次，桌面实测角色层 9.3 → 196 ms（saturation 混合一次 2.4 ms、destination-in 1.5 ms × 7 人），推翻。
 *    三人组的光按到位时的位置取（进场一路滑进来不重算），男女主按此刻的位置取（被拖着穿过三间房，颜色跟着变）。
 * 悬空的人（秋千、飞、倒挂、扒墙）：脚下几百像素外的地板被后排的人占着，影子投过去读不出是谁的；他们贴着墙，
 * 影子投在身后的墙上（剪影缩到 1/6 再放大 = 便宜的模糊，往背光方向偏一点），读成"离墙有一段距离、悬在半空"。
 *
 * 灯和房间底色是布景数据，按背景套（rooms.json 的那一套）写在 SETS 里；没写的套（?bg=v14 白天长卷）整个不开。
 * 诊断：?light=0 全关（改前）；?light=shadow / grade / rim（可逗号连写）只开其中几样（逐项对比胶片）；?lightdbg=rim 只看轮廓光那一条。
 * 代价：每个人每帧多 ~10 次画人外框那么大的离屏合成（bench 量过，见规范「立体感 · 性能」）。
 */
'use strict';

const Light = (() => {
  /* 一套背景的光：
     rooms[i]：amb 房间底色（乘到人身上，0~1）、lvl 远离所有灯时多亮、sat 降饱和几成、shade 地上阴影的颜色（房间暗部的色相，不用纯黑）
     lights：x, y 世界坐标（像素，房间图上量的），col 光色，p 强度（加回到乘色上的量），r 衰减半径（这么远强度剩一半） */
  const SETS = {
    v15: {
      rooms: [
        { amb: [1.00, 0.86, 0.88], lvl: 0.74, sat: 0.08, shade: [44, 16, 24] },    // 卧室：粉暖
        { amb: [1.00, 0.95, 0.90], lvl: 0.72, sat: 0.06, shade: [30, 22, 22] },    // 客厅：蓝灰墙、暖色落地灯
        { amb: [0.72, 0.74, 1.00], lvl: 0.68, sat: 0.16, shade: [12, 8, 40] },     // 电竞房：蓝紫
      ],
      lights: [
        { x: 485, y: 600, col: [1.00, 0.76, 0.48], p: 0.30, r: 420 },     // 卧室 床头灯
        { x: 1180, y: 520, col: [1.00, 0.84, 0.60], p: 0.40, r: 520 },    // 卧室 化妆镜灯泡
        { x: 300, y: 380, col: [1.00, 0.80, 0.56], p: 0.22, r: 420 },     // 卧室 床幔串灯
        { x: 800, y: 480, col: [0.56, 0.60, 1.00], p: 0.10, r: 400 },     // 卧室 窗（雨夜城市光）
        { x: 2318, y: 560, col: [1.00, 0.76, 0.46], p: 0.50, r: 520 },    // 客厅 落地灯
        { x: 1738, y: 620, col: [0.36, 0.95, 1.00], p: 0.22, r: 380 },    // 客厅 鱼缸
        { x: 2458, y: 520, col: [0.56, 0.66, 1.00], p: 0.14, r: 420 },    // 客厅 落地窗
        { x: 2642, y: 560, col: [1.00, 0.74, 0.44], p: 0.20, r: 300 },    // 电竞房 台灯
        { x: 2842, y: 540, col: [0.56, 0.76, 1.00], p: 0.50, r: 520 },    // 电竞房 显示器
        { x: 3072, y: 400, col: [0.82, 0.44, 1.00], p: 0.32, r: 420 },    // 电竞房 霓虹手柄灯
        { x: 3202, y: 560, col: [0.74, 0.40, 1.00], p: 0.26, r: 360 },    // 电竞房 机箱灯
        { x: 3462, y: 480, col: [0.46, 0.56, 1.00], p: 0.18, r: 480 },    // 电竞房 窗
        { x: 3632, y: 1000, col: [0.90, 0.36, 1.00], p: 0.26, r: 360 },   // 电竞房 终点发光地垫
      ],
    },
  };
  const BLEND = 160;              // 两间房交界处底色过渡多宽（像素）
  const RIM = { w: 1.4, r: 4.2, a: 0.85 };   // 轮廓光：从剪影边往里 w 起、宽 r（× 画多大 s），叠多亮
  const WALL = { d: 34, down: 16, a: 0.40, q: 6 };   // 墙上的影子：往背光方向偏 d、往下 down、多深、缩到 1/q 当模糊
  let set = null, rooms = null, ox = 0;                 // ox：屏幕 x → 世界 x 的偏移（镜头）

  /* 背景套：main.js boot 时按 ?bg 告诉这里用哪一套、三间房多宽；没有这一套的光 → 不开 */
  function use(name, widths) {
    set = SETS[name] || null;
    let x = 0;
    rooms = widths.map(w => { const r = [x, x + w]; x += w; return r; });
    api.on = !!set && api.on;
  }
  /* 每帧开头：镜头位置；预热名额（warm）重置 */
  function next(camX, mid) { ox = camX - mid; spare = 1; }
  let spare = 1;

  /* 世界 x 处的房间底色（交界处线性过渡）→ { amb, lvl, sat, shade } 混好的 */
  function room(wx) {
    const R = set.rooms;
    let i = rooms.findIndex(r => wx < r[1]);
    if (i < 0) i = R.length - 1;
    const mix = (a, b, k) => ({ amb: a.amb.map((v, j) => v + (b.amb[j] - v) * k), lvl: a.lvl + (b.lvl - a.lvl) * k,
                                sat: a.sat + (b.sat - a.sat) * k, shade: a.shade.map((v, j) => v + (b.shade[j] - v) * k) });
    const [x0, x1] = rooms[i];
    if (i > 0 && wx < x0 + BLEND / 2) return mix(R[i], R[i - 1], 0.5 - (wx - x0) / BLEND);
    if (i < R.length - 1 && wx > x1 - BLEND / 2) return mix(R[i], R[i + 1], 0.5 - (x1 - wx) / BLEND);
    return R[i];
  }
  /* 屏幕点 (x, y) 处的乘色 [r, g, b]（0~1）和光从哪来：每盏灯按距离高斯衰减（k = p·exp(−(d/r)²)，隔一间房的灯基本照不到），
     方向按 k 加权；轮廓光的颜色按 k² 加权（最近最亮的那盏说了算 —— 按 k 平均十几盏灯会混成灰白） */
  function tone(x, y) {
    const wx = x + ox, rm = room(wx), m = rm.amb.map(v => v * rm.lvl);
    let ux = 0, uy = 0, e = 0, top = 0, w2 = 0, cr = 0, cg = 0, cb = 0;
    for (const L of set.lights) {
      const dx = L.x - wx, dy = L.y - y, d = Math.hypot(dx, dy) || 1, k = L.p * Math.exp(-(d / L.r) * (d / L.r));
      m[0] += L.col[0] * k; m[1] += L.col[1] * k; m[2] += L.col[2] * k;
      ux += dx / d * k; uy += dy / d * k; e += k; top = Math.max(top, k);
      cr += L.col[0] * k * k; cg += L.col[1] * k * k; cb += L.col[2] * k * k; w2 += k * k;
    }
    return { m: m.map(v => Math.min(1, v)), rm, ux, uy, e, top, col: w2 ? [cr / w2, cg / w2, cb / w2] : [1, 1, 1] };
  }
  const css = (m, a = 1) => `rgba(${Math.round(m[0] * 255)},${Math.round(m[1] * 255)},${Math.round(m[2] * 255)},${a})`;

  /* 一个人此刻吃到的光：c = 外框中心（屏幕），R = 半径。光的方向 = 各盏灯方向按强度加权；
     乘色沿这个方向从朝灯那一侧（near）到背灯那一侧（far）渐变，背灯那侧再暗 FAR 成 × 方向有多集中 */
  const FAR = 0.16;
  function at(cx, cy, R) {
    if (!set) return null;                                          // 这套背景没写光（?bg=v14）：不打光
    const t = tone(cx, cy), len = Math.hypot(t.ux, t.uy), u = len > 1e-6 ? [t.ux / len, t.uy / len] : [0, -1];
    const focus = Math.min(1, len / Math.max(1e-6, t.e));          // 1 = 只有一个方向来光，0 = 四面八方
    const str = Math.min(1, t.top * 3.2);                           // 最亮那盏灯在这里有多强（轮廓光亮度）
    const near = tone(cx + u[0] * R, cy + u[1] * R).m, far = tone(cx - u[0] * R, cy - u[1] * R).m.map(v => v * (1 - FAR * focus * Math.min(1, str * 1.5)));
    /* 缓存 key：乘色量化到 1/48、方向 24 档、轮廓光颜色 1/16 —— 比这细的变化肉眼分不出，重算一格要好几次整格合成 */
    const qz = (v, n) => Math.round(v * n), dir = Math.round(Math.atan2(u[1], u[0]) / (Math.PI / 12));
    const near48 = near.map(v => qz(v, 48) / 48), far48 = far.map(v => qz(v, 48) / 48), rim16 = t.col.map(v => qz(v, 16) / 16);
    const ud = [Math.cos(dir * Math.PI / 12), Math.sin(dir * Math.PI / 12)];
    return { u: ud, str, rim: rim16, near: near48, far: far48, sat: t.rm.sat, shade: t.rm.shade.map(Math.round),
             gkey: near48.join(',') + '|' + far48.join(',') + '|' + dir + '|' + t.rm.sat.toFixed(3), rkey: dir + '|' + rim16.join(',') };
  }

  /* ---- 剪影底边（接地阴影的形状）---- */
  const PROF = new Map(), Q = 4;
  /* 贴图 img 上 (sx, sy, sw, sh) 这一格的剪影底边 → 贴图像素：
     yb 最低的不透明行；touch 贴地的几段 [x0, x1, 这一段最低点 y]（最低点离 yb 在 4% 格高以内的列，断开 > 2 列算两段）；
     near 靠近地面的几片 [x0, x1, y]（15% 以内，断开 > 40 像素算两片 —— 男女主一张图里两个人，各一片；没有 = null） */
  const keyOf = (img, sx, sy, sw, sh) => img.src + '|' + sx + ',' + sy + ',' + sw + ',' + sh;
  /* 量剪影要读回像素。**不在主线程读**：主线程 drawImage 一张图集再 getImageData = 强制解码 + 等 GPU 交回像素，
     平时一张 50~90 ms，送礼正忙时一张 5~10 秒（2026-10-02 用户"频繁点礼物会卡死"，tools/load/stress.py 实测：
     预取队列 66 张图集挨个量，主线程被堵住几十秒）。改成 Worker 里 fetch 原图 → createImageBitmap 解码 → OffscreenCanvas 缩到 1/Q 读 alpha，
     主线程只收结果。同一张图（img.src）一次读完所有格；没有 Worker / OffscreenCanvas 的浏览器不画接地影（has.shadow = false）。 */
  const canWork = typeof Worker === 'function' && typeof OffscreenCanvas === 'function' && typeof createImageBitmap === 'function';
  let worker = null, seq = 0;
  const WAIT = new Map(), BUSY = new Map();
  function workerOf() {
    if (worker) return worker;
    const src = `'use strict'; const Q = ${Q};\n${scan.toString()}\n` +
      `onmessage = async (e) => { const { id, src, cells } = e.data;
        try {
          const bm = await createImageBitmap(await (await fetch(src)).blob());
          const W = Math.max(1, Math.ceil(bm.width / Q)), H = Math.max(1, Math.ceil(bm.height / Q));
          const c = new OffscreenCanvas(W, H).getContext('2d', { willReadFrequently: true });
          c.drawImage(bm, 0, 0, W, H); bm.close();
          const d = c.getImageData(0, 0, W, H).data;
          postMessage({ id, profs: cells.map(([sx, sy, sw, sh]) => scan(d, W, Math.floor(sx / Q), Math.floor(sy / Q), Math.ceil(sw / Q), Math.ceil(sh / Q))) });
        } catch (err) { postMessage({ id, err: String(err) }); } };`;
    worker = new Worker(URL.createObjectURL(new Blob([src], { type: 'text/javascript' })));
    worker.onmessage = (e) => { const w = WAIT.get(e.data.id); WAIT.delete(e.data.id); w(e.data); };
    return worker;
  }
  /* 量 img 上这几格（[sx, sy, sw, sh]），结果进 PROF；返回量完的 promise。同一张图正在量就并到那一次后面 */
  function measure(img, cells) {
    const todo = cells.filter(([sx, sy, sw, sh]) => !PROF.has(keyOf(img, sx, sy, sw, sh)));
    if (!todo.length) return Promise.resolve();
    if (!canWork) { api.has.shadow = false; return Promise.resolve(); }
    const prev = BUSY.get(img.src) || Promise.resolve();
    const run = prev.then(() => new Promise((ok) => {
      const left = todo.filter(([sx, sy, sw, sh]) => !PROF.has(keyOf(img, sx, sy, sw, sh)));
      if (!left.length) return ok();
      const id = ++seq;
      WAIT.set(id, ({ profs, err }) => {
        if (err) console.warn('light: 量剪影失败', img.src, err);
        else left.forEach(([sx, sy, sw, sh], i) => PROF.set(keyOf(img, sx, sy, sw, sh), profs[i]));
        ok();
      });
      workerOf().postMessage({ id, src: img.src, cells: left });
    }));
    BUSY.set(img.src, run);
    return run;
  }
  /* 这一格的剪影底边；还没量好 = null（这一帧不画接地影），顺手发起量 */
  function profile(img, sx, sy, sw, sh) {
    const p = PROF.get(keyOf(img, sx, sy, sw, sh));
    if (!p) measure(img, [[sx, sy, sw, sh]]);
    return p || null;
  }
  /* 一张图集的每一格一起量（Act.load 加载完就调，等它量完再算 ready —— 人出场时剪影一定已经有了） */
  function profiles(img, cw, ch, n, cols) {
    const cells = [];
    for (let i = 0; i < n; i++) cells.push([(i % cols) * cw, Math.floor(i / cols) * ch, cw, ch]);
    return measure(img, cells);
  }
  /* 读回的 alpha（行宽 W）里 (ox, oy) 起 w × h 这一块 → 剪影底边（贴图像素，相对这一格） */
  function scan(d, W, ox, oy, w, h) {
    const low = new Int32Array(w).fill(-1);
    for (let x = 0; x < w; x++) for (let y = h - 1; y >= 0; y--) if (d[((oy + y) * W + ox + x) * 4 + 3] > 128) { low[x] = y; break; }
    let yb = -1;
    for (const v of low) if (v > yb) yb = v;
    const p = { yb: (yb + 1) * Q, touch: [], near: null };
    /* 一行里 low ≥ lim 的列连成段，断开超过 gap 列就另起一段 → 贴图像素 [x0, x1, 这一段最低点 y] */
    const runs = (lim, gap) => {
      const out = [];
      let s = -1, e = -1, lo = -1;
      const push = () => out.push([s * Q, (e + 1) * Q, (lo + 1) * Q]);
      for (let x = 0; x < w; x++) {
        if (low[x] < lim) continue;
        if (s >= 0 && x - e - 1 > gap) { push(); s = -1; }
        if (s < 0) { s = x; lo = -1; }
        e = x; lo = Math.max(lo, low[x]);
      }
      if (s >= 0) push();
      return out;
    };
    if (yb >= 0) {
      p.touch = runs(yb - Math.max(1, Math.round(h * 0.04)), 2);
      const nr = runs(yb - Math.max(2, Math.round(h * 0.15)), Math.ceil(40 / Q));
      p.near = nr.length ? nr : null;
    }
    return p;
  }

  /* 一团柔影的贴图（64 见方，径向渐变：中心 1、55% 处 0.55、边上 0），按阴影色缓存 —— 每帧每团 createRadialGradient 再填，比贴一张图贵 */
  const BLOB = new Map();
  function blobOf(shade) {
    const key = shade.join(',');
    let c = BLOB.get(key);
    if (!c) {
      c = canvasOf(64, 64);
      const x = c.getContext('2d'), g = x.createRadialGradient(32, 32, 0, 32, 32, 32), rgb = `${shade[0]},${shade[1]},${shade[2]}`;
      g.addColorStop(0, `rgba(${rgb},1)`); g.addColorStop(0.55, `rgba(${rgb},0.55)`); g.addColorStop(1, `rgba(${rgb},0)`);
      x.fillStyle = g; x.fillRect(0, 0, 64, 64);
      BLOB.set(key, c);
    }
    return c;
  }

  /* ---- 地上的接触影 ----
     touch：贴地几段 [[x0, x1, y 地面], ...]（屏幕，y = 这一段脚底此刻落在地上的那条线）、near 靠近地面的几片（同上）、s 画多大、
     lift 离地多高（屏幕像素）、k 整体不透明度（淡入淡出）、L at() 的结果 */
  function contact(ctx, touch, near, s, lift, k, L) {
    if (!api.has.shadow || !near || k <= 0.01) return;
    const up = Math.max(0, lift), fade = Math.exp(-up / (140 * s)), core = Math.exp(-up / (34 * s)), grow = 1 + Math.min(0.6, up / (360 * s));
    const lean = -L.u[0] * 0.12;                                    // 往背光那边偏一点
    const sp = blobOf(L.shade), ga = ctx.globalAlpha;
    const blob = (cx, y, rx, ry, a) => {
      if (a <= 0.01 || rx < 1) return;
      ctx.globalAlpha = ga * a; ctx.drawImage(sp, cx - rx, y - ry, rx * 2, ry * 2);
    };
    for (const [x0, x1, y] of near) {
      const w = x1 - x0, rx = (w / 2 + 14 * s) * grow;
      blob((x0 + x1) / 2 + lean * w, y, rx, Math.max(7 * s, Math.min(rx * 0.17, 26 * s)), 0.46 * k * fade);
    }
    for (const [x0, x1, y] of touch) {
      const r = ((x1 - x0) / 2 + 7 * s) * grow;
      blob((x0 + x1) / 2 + lean * (x1 - x0), y, r, Math.max(3.5 * s, Math.min(r * 0.3, 12 * s)), 0.55 * k * core);
    }
    ctx.globalAlpha = ga;
  }

  /* ---- 贴图空间的打光缓存 ----
     tex(img)：这张源图的缓存（WeakMap，同一张图集共用）；g 打好光（含轮廓光）的整张（跟源图同尺寸、同布局），
     sil 墙上影子用的剪影（1/WALL.q）。每一格记着算它时的 key，key 不变就直接用 */
  const TEX = new WeakMap();
  function tex(img) {
    let T = TEX.get(img);
    if (!T) { T = { img, g: null, sil: null, gk: new Map(), sk: new Map() }; TEX.set(img, T); }
    /* 最近用过的排在后面；打好光的副本合计超过 BUDGET 像素就从最久没用的放掉（男女主一局要过几十张姿势图，三人组离场的 Act 自己会 drop） */
    LRU.delete(img); LRU.set(img, T);
    let px = 0;
    for (const t of LRU.values()) px += t.g ? t.g.width * t.g.height : 0;
    for (const [k, t] of LRU) {
      if (px <= BUDGET || k === img) break;
      px -= t.g ? t.g.width * t.g.height : 0; drop(k);
    }
    return T;
  }
  const LRU = new Map(), BUDGET = 24e6;
  const canvasOf = (w, h) => { const c = document.createElement('canvas'); c.width = Math.max(1, Math.ceil(w)); c.height = Math.max(1, Math.ceil(h)); return c; };
  /* 人不在场了：放掉打好光的副本（一张图集 1700² 的副本 ~12 MB，60 个人攒下来手机吃不消） */
  function drop(img) {
    const T = img && TEX.get(img);
    if (!T) return;
    for (const k of ['g', 'sil']) if (T[k]) { T[k].width = T[k].height = 0; T[k] = null; }
    T.gk.clear(); T.sk.clear();
    LRU.delete(img);
  }
  /* 这一格（源图 sx, sy, sw, sh）在光 L 下打好光（含轮廓光）的图：返回跟源图同布局的画布（没开就是源图本身）。
     s = 这张图画到屏幕上放大几倍（轮廓光宽度按屏幕像素算）；rim = false 不加轮廓光（挂件、布景）。
     轮廓光直接烘进这一格（不在每帧另叠）：flex 条带错位、挂件跟着画，光边天然对齐；每帧的代价就是照常画一次图（第二版每帧另叠一次 screen，
     条带错位的人要多画几百条，实测占了开销的一大半） */
  /* 这一格打光的 key：乘色那一份 + 轮廓光那一份（方向、颜色、亮度、宽度） */
  function keyFor(L, s, rim) {
    const ra = rim && api.has.rim ? RIM.a * L.str : 0;
    return (api.has.grade ? L.gkey : '') + '#' + (ra > 0.03 ? L.rkey + '|' + ra.toFixed(2) + '|' + s.toFixed(2) : '');
  }
  function lit(img, sx, sy, sw, sh, L, s, rim = true) {
    if (!api.on || !L || !(api.has.grade || api.has.rim)) return img;
    const T = tex(img), id = sx + ',' + sy, ra = rim && api.has.rim ? RIM.a * L.str : 0, key = keyFor(L, s, rim);
    if (!T.g) T.g = canvasOf(img.width, img.height);
    if (T.gk.get(id) !== key) {
      const c = T.g.getContext('2d');
      c.save(); c.beginPath(); c.rect(sx, sy, sw, sh); c.clip();
      c.globalCompositeOperation = 'copy'; c.drawImage(img, sx, sy, sw, sh, sx, sy, sw, sh);
      if (api.has.grade) grade(c, img, sx, sy, sw, sh, L);
      if (ra > 0.03) { rimCell(img, sx, sy, sw, sh, L, s); c.globalCompositeOperation = 'screen'; c.globalAlpha = api.dbg === 'rim' ? 1 : ra; c.drawImage(scratch, 0, 0, sw, sh, sx, sy, sw, sh); }
      c.restore();
      T.gk.set(id, key);
    }
    return T.g;
  }
  /* 预热：这一格还没按光 L 打好就打，每帧全场只打一格（spare）。在场的人每帧把自己图集里下一格递过来 ——
     出手、离场那几格等用到时已经打好了，不会在出手那一帧一下算好几格（桌面 p95 从 17 涨到 28 ms 就是这个） */
  function warm(img, sx, sy, sw, sh, L, s) {
    if (spare <= 0 || !api.on || !L) return;
    const T = TEX.get(img);
    if (T && T.g && T.gk.get(sx + ',' + sy) === keyFor(L, s, true)) return;
    spare--; lit(img, sx, sy, sw, sh, L, s);
  }
  /* 打光（c 已经剪在这一格、画好原图）：垫黑底 → 降饱和 → 乘光色（沿光方向渐变，格中心 ± R·u）→ 按原图 alpha 剪回剪影。
     垫黑底：混合模式在透明处直接把填色画上去，抗锯齿那一圈半透明像素会混进一半乘色 → 细线外面泛一圈浅色毛边（第一版羽毛、旗角实测）；
     垫黑底后边缘像素只会略暗（描边本来就是深的） */
  function grade(c, img, sx, sy, sw, sh, L) {
    c.globalCompositeOperation = 'destination-over'; c.fillStyle = '#000'; c.fillRect(sx, sy, sw, sh);
    c.globalCompositeOperation = 'saturation'; c.fillStyle = `rgba(128,128,128,${L.sat})`; c.fillRect(sx, sy, sw, sh);
    const R = Math.max(sw, sh) * 0.45, cx = sx + sw / 2, cy = sy + sh / 2;
    const gr = c.createLinearGradient(cx + L.u[0] * R, cy + L.u[1] * R, cx - L.u[0] * R, cy - L.u[1] * R);
    gr.addColorStop(0, css(L.near)); gr.addColorStop(1, css(L.far));
    c.globalCompositeOperation = 'multiply'; c.fillStyle = gr; c.fillRect(sx, sy, sw, sh);
    c.globalCompositeOperation = 'destination-in'; c.drawImage(img, sx, sy, sw, sh, sx, sy, sw, sh);
  }
  /* 轮廓光那一条画进 scratch（0, 0 起、格大小）：剪影往光的方向挪 w 还在、挪 w + r 就出界 → 朝光那一侧描边以内的一窄条，
     染成灯的颜色。宽度按屏幕像素 ÷ s 换成贴图像素 */
  let scratch = null;
  function rimCell(img, sx, sy, sw, sh, L, s) {
    if (!scratch) scratch = canvasOf(sw, sh);
    if (scratch.width < sw || scratch.height < sh) { scratch.width = Math.max(scratch.width, sw); scratch.height = Math.max(scratch.height, sh); }
    const c = scratch.getContext('2d'), w = RIM.w / s, r = RIM.r / s, [ux, uy] = L.u;
    c.save(); c.beginPath(); c.rect(0, 0, sw, sh); c.clip();
    c.globalCompositeOperation = 'copy'; c.drawImage(img, sx, sy, sw, sh, -ux * w, -uy * w, sw, sh);
    c.globalCompositeOperation = 'destination-out'; c.drawImage(img, sx, sy, sw, sh, -ux * (w + r), -uy * (w + r), sw, sh);
    c.globalCompositeOperation = 'destination-in'; c.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh);
    c.globalCompositeOperation = 'source-in'; c.fillStyle = css(L.rim); c.fillRect(0, 0, sw, sh);
    c.restore();
  }
  /* 墙上影子用的剪影一格（1/WALL.q，放大回来自带模糊），染成阴影色：{ im, k 坐标缩放 } */
  function sil(img, sx, sy, sw, sh, shade) {
    const T = tex(img), id = sx + ',' + sy, key = shade.join(','), q = 1 / WALL.q;
    if (!T.sil) T.sil = canvasOf(img.width * q, img.height * q);
    if (T.sk.get(id) !== key) {
      const c = T.sil.getContext('2d'), X = sx * q, Y = sy * q, W = sw * q, H = sh * q;
      c.save(); c.beginPath(); c.rect(X, Y, W, H); c.clip();
      c.globalCompositeOperation = 'copy'; c.imageSmoothingQuality = 'high'; c.drawImage(img, sx, sy, sw, sh, X, Y, W, H);
      c.globalCompositeOperation = 'source-in'; c.fillStyle = `rgb(${shade[0]},${shade[1]},${shade[2]})`; c.fillRect(X, Y, W, H);
      c.restore();
      T.sk.set(id, key);
    }
    return { im: T.sil, k: q };
  }
  /* 墙上影子画在哪：从人此刻的位置往背光方向偏 d、往下 down（屏幕像素），多深 */
  const wallOff = (L) => [-L.u[0] * WALL.d, -L.u[1] * WALL.d + WALL.down];

  const api = { on: true, has: { shadow: true, grade: true, rim: true }, dbg: null, use, next, at, profile, profiles, contact, lit, warm, sil, wallOff, drop, WALL, SETS };
  return api;
})();
