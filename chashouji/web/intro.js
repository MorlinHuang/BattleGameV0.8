/* intro.js —— 档 4 的出场视频（2026-09-28，即梦 Seedance 生成）。
 *
 * 送礼 → 先放一段 8 秒视频（天降、对镜头放电、举罐瞄准），视频最后一秒机位固定，她悬在画面左上方；
 * 视频播完的那一刻，游戏里的她在**同一个位置、同一个姿势**出现（视频就是照着这张立绘生成的，尾帧对齐量过），
 * 然后视频淡掉、她留在原地，再滑一小段进悬停位开火。读起来是她从视频里走进游戏。
 *
 * **视频是一层特效，不是一块屏幕**（用户 2026-09-28："不要生硬的视频硬切，像图层一样在最上面，人物清晰，
 * 其他环境和游戏融合"）。视频文件是带透明通道的 VP9 webm，合成是离线烤进去的 —— 用视频抽帧工具
 * （video/vframes，网页版 :40232，拖入即梦原片 + 立绘，一键出 scheme1/alpha.webm 和下面 CLIPS 要的 vw / end；
 * 制作规范见 video/出场视频制作规范.md）：
 *   · 人物不透明，只在画框边软掉（底边软得最宽 —— 特写时她被画框底边截断）；
 *   · 环境只留 22%，越靠画框边越淡，透出底下的游戏，没有矩形边；
 *   · 亮部（金色光柱、亮片、金光爆开）留 90%，光是这段视频的"特效"，要亮在游戏上面；
 *   · 最后一秒她定住时，环境和光退干净，只剩她一个人浮在游戏上，再交给游戏里的立绘。
 * 为什么不在游戏里用 WebGL 实时合成（上下拼的 画 + 遮罩 视频）：试过，桌面容器 Chrome（无 GPU）里 WebGL 上下文
 * 一建就丢（isContextLost 恒为真），直播伴侣 / OBS 的环境同样没法保证；带 alpha 的 webm 用普通 <video> 就能放，
 * Chromium 内核（Chrome / Edge / OBS 浏览器源 / 直播伴侣）都支持。Safari 不支持 VP9 透明，会显示成黑底 ——
 * 所以非 Chromium 不放视频（不注册），她照原来从画外冲进来。
 * 视频区下沿压着调试按钮区，所以插在 .panel 之前（按钮仍可点）。
 *
 * 数值不等视频：送礼那一刻战力就加上了（main.js giveGift），视频只推迟她本人的出场 ——
 * 视频期间她在 Crew 里是"候场"（b.hold：占着名额、不走时钟、不画），CrewGroup 不会趁这 8 秒轮到下一个人；
 * 候场时又有人送，照常走续时间（crew.js renew），她出来时名字条带「×N」。
 */
'use strict';

const IntroVideo = (() => {
  /* 每个有出场视频的人一条。box：视频在画布上的位置 [x, y, w, h]（画布 960×1707；上沿 200 是拉力条下沿，HUD 不挡；
     宽 960 铺满，高按 3:4）。end：视频最后一帧里立绘的位置 —— 立绘 assets/world/truth2_up.webp 缩放 s 倍、左上角放在
     视频像素 (x, y) 时跟尾帧重合（在尾帧上按像素色差搜出来的，残差 18/255，发丝和罐口都对得上）；vw 是视频宽（像素）。 */
  const CLIPS = {
    truth: { src: 'assets/video/truth_intro_alpha.webm', box: [0, 200, 960, 1280], vw: 834, end: { s: 0.819, x: 6, y: 7 } },
    /* 白娘子（2026-09-29）：box 反过来按尾帧定 —— 最后一帧里她正好落在游戏悬停位（main.js G4STAND.baisu [110, 886, 1.005]）、
       同样大，视频放完立绘原地接上，不滑、不放大（真相女神尾帧是 0.94 倍，现身后要边滑边放大）。
       k = 1.005 / end.s（画布像素 / 视频像素）；box.x = 110 − (end.x + foot.x·end.s)·k，box.y = 886 − (end.y + foot.y·end.s)·k，
       宽高 = 834×1112 × k。右沿正好贴屏幕右边，左边 166 像素在屏幕外（#stage overflow:hidden），只裁掉开场正面镜头左侧一点衣袖。
       tide：视频最后一帧里海面的高度（视频像素，vframes --fx sea 量的）—— 游戏里的海从这个高度接上（sea.js handoff）。
       视频由 video/vframes 出：vframes.py 原片 -s baisu1_up.webp --fx sea（底部的海 + 虾兵蟹将整条保留、不随环境退掉）。 */
    baisu: { src: 'assets/video/baisu_intro_alpha.webm', box: [-165.9, 101.6, 1125.1, 1500.1], vw: 834, end: { s: 0.745, x: -51, y: 22 }, tide: 900, seaAt: 4.8,
             open: [-86.9, 101.6], move: [4.6, 6.2] },
    /* open / move：开场时视频区左上角在 open，move 这段（秒）平滑移到 box。box 是按尾帧反推的，比居中往左 79 像素 ——
       前 4.5 秒她正面居中（视频里人物重心在宽度的 50.4%），不挪回来就整段偏左（用户 2026-09-29："出场后位置偏左，不在正中心"）。
       move 取她飞向左上、镜头后拉那一段：画面本来就在动，视频区跟着平移看不出来，最后一帧照样压在悬停位上。 */
    /* 嫦娥（2026-09-29）：全程固定机位 —— 从左上一轮满月里飞出来、到镜头前近景、再飘回左上，满月缩成头后光环；
       底下月夜云海从左涌进来，肩上的玉兔化作流光跳进云里。box 同白娘子按尾帧反推（G4STAND.change [240, 908, 0.88]，
       尾帧对齐色差 7.3）；近景时她重心在视频宽 54.5%，open 往左 58 像素让她居中，4.4~5.6 秒她飘回左上时移回 box。
       视频由 vframes.py 原片 -s change1_up.webp --fx cloud 出（云海按"不像夜空"认，整条保留；法术潮进画面的帧盖掉再抠一次人物）。 */
    /* 2026-09-29 嫦娥站位下移 70（G4STAND.change 908 → 978，给头顶的月光束光点让出拉力条下的位置）：box / open 的 y 跟着 +70，尾帧照样对齐 */
    change: { src: 'assets/video/change_intro_alpha.webm', box: [7.6, 203.5, 973.4, 1297.8], vw: 834, end: { s: 0.754, x: -12, y: -15 }, tide: 953, seaAt: 5.4,
              open: [-50.5, 203.5], move: [4.4, 5.6] },
    /* 绿茶妹妹（2026-09-29）：男女主抢的那部手机亮了，兔耳先探出来、她从屏幕里钻出来 → 贴到镜头前撒娇、瞟姐姐装怕、躲手机后偷笑眨眼
       → 往后一蹦退到右边定成立绘姿势；底下奶盖泡泡海从右涌进来。制作包 video/sister。
       box 按尾帧反推（G4STAND.sister [848, 1136, 1.0]，尾帧对齐色差 13.2）。不加 open：开场那部手机在视频宽 45.8%、高 58.8%，
       按 box 落在画布 (451, 898) —— 正压在游戏里那部手机 (454, 898) 上；近景她重心在 51%（画布 501，只偏中线 21），挪了反而把手机挪开。
       视频由 vframes.py 原片 -s sister1_up.webp --fx tea 出（浪按"不像夜色"认、只要从右边缘连过来的那片）。 */
    sister: { src: 'assets/video/sister_intro_alpha.webm', box: [5.4, 134.5, 973.2, 1297.6], vw: 834, end: { s: 0.857, x: 483, y: 15 }, tide: 980, seaAt: 5.2 },
  };
  /* seaAt（秒）：视频里的海从这一刻起涌进来（底边一条的 alpha 由 ~0.3 升到 1：白娘子 5.75、嫦娥 6.5、绿茶妹妹 6.25 秒满，ffmpeg 逐 0.25 秒量），
     提前游戏海推满要的 1.4 秒左右。视频框下沿（1602 / 1501 / 1432）到画布底 1707 之间视频里什么都没有 —— 从 seaAt 起游戏自己那片海
     从同一侧推进来、垫在视频底下（seaUnder → main.js tideUpdate），海面停在视频尾帧的海面高度（tide），放完 handoff 原地接上。 */
  const POP = 0.35, FADE = 0.45;         // 浮现几秒、结尾淡掉几秒
  /* VP9 透明只有 Chromium 内核认。按 UA 判（Safari 的 canPlayType 也说能放 webm，但透明通道丢掉，变黑底） */
  const ALPHA_OK = /Chrom(e|ium)\/|Edg\//.test(navigator.userAgent);

  let stage = null, W = 960, H = 1707, cur = null, onRelease = null;
  const vids = {};                         // 配方名 → 预加载好的 <video>

  function init(opt) {
    stage = opt.stage; W = opt.W; H = opt.H; onRelease = opt.onRelease || null;
    if (new URLSearchParams(location.search).get('introvideo') === '0' || !ALPHA_OK) return;   // ?introvideo=0：关掉（胶片 / 压测用）
    for (const [k, c] of Object.entries(CLIPS)) {
      const v = document.createElement('video');
      /* preload none：首屏不碰视频（docs/首屏加载诊断.md R3：4 个视频 15 MB，preload auto 时在首屏那十几秒占掉 6 条连接里的 4 条）。
         首帧之后预取队列最后一项（load）才开始缓冲；缓冲够之前送礼，begin 按 readyState 跳过视频 */
      v.src = c.src; v.preload = 'none'; v.playsInline = true;
      const [, , w, h] = c.box;
      Object.assign(v.style, {
        position: 'absolute', width: w / W * 100 + '%', height: h / H * 100 + '%',
        objectFit: 'fill', visibility: 'hidden', pointerEvents: 'none',
      });
      place(v, c, 0);
      stage.insertBefore(v, stage.querySelector('.panel'));
      vids[k] = v;
    }
  }

  /* 视频区左上角跟着播放进度走（只有配了 open 的才动）：t 秒时在 open → box 之间哪里 */
  function place(v, c, t) {
    let [x, y] = c.box;
    if (c.open) {
      const u = Math.min(1, Math.max(0, (t - c.move[0]) / (c.move[1] - c.move[0]))), e = u * u * (3 - 2 * u);
      x = c.open[0] + (x - c.open[0]) * e; y = c.open[1] + (y - c.open[1]) * e;
    }
    v.style.left = x / W * 100 + '%'; v.style.top = y / H * 100 + '%';
  }
  function follow() {
    if (!cur || cur.done) return;
    place(cur.v, cur.c, cur.v.currentTime);
    requestAnimationFrame(follow);
  }

  /* 立绘在尾帧里的位置 → 游戏里她此刻该在哪：[脚底 x, 脚底 y, 缩放]（跟 crew.js hoverPose 同一套量） */
  function endPose(c, spr) {
    const k = c.box[2] / c.vw, s = c.end.s * k;
    return [c.box[0] + (c.end.x + spr.foot[0] * c.end.s) * k, c.box[1] + (c.end.y + spr.foot[1] * c.end.s) * k, s];
  }

  /* 召唤到了一个新的人（b）：有她的视频就让她候场、放视频，放完从视频里的位置放她出来。
     没有视频、视频还没加载好、或正在放别人的视频（两边同时刷档 4）→ 返回 false，照原来从画外冲进来。 */
  function begin(rcp, crew, b) {
    const c = CLIPS[rcp], v = vids[rcp];
    if (!c || !v || cur || v.readyState < 3) return false;
    b.hold = true;
    cur = { v, crew, b, c, done: false };
    v.currentTime = 0;
    place(v, c, 0);
    if (c.open) requestAnimationFrame(follow);
    v.style.transition = 'none'; v.style.opacity = '0'; v.style.transform = 'scale(1.04)'; v.style.visibility = 'visible';
    requestAnimationFrame(() => {             // 浮现：淡入 + 从略大收回来（没有弹框，是一层光慢慢显出来）
      v.style.transition = `opacity ${POP}s ease-out, transform ${POP * 1.6}s ease-out`;
      v.style.opacity = '1'; v.style.transform = 'scale(1)';
    });
    const go = v.play();
    /* 带声音自动播放被浏览器拦（页面还没被点过）：静音再放一次。画面照演，只是没声音 —— 直播时页面一定被点过。 */
    if (go) go.catch(() => { v.muted = true; return v.play(); }).catch(() => release());
    v.onended = release;
    v.onerror = release;
    return true;
  }

  /* 视频放完：她在尾帧那个位置现身（crew.js hoverPose 从 b.from 滑进悬停位），视频淡掉。
     收起一律用 visibility，不用 display:none：桌面容器的 Chrome 里，放过的 <video> 一被 display:none，
     整页合成就停了 —— JS 照跑（?titleclock=1 看得到时钟在走），画面定在最后一帧不再刷新（2026-09-28 录屏复现）。 */
  function release() {
    if (!cur || cur.done) return;
    const me = cur, { v, crew, b, c } = me;
    me.done = true;
    place(v, c, Infinity);                  // 放完一定落在 box（尾帧对准的位置），不管最后一帧 rAF 赶没赶上
    if (crew.peek().includes(b)) {
      b.hold = false; b.t = 0; b.from = endPose(c, crew.cfg.spr);
      /* 视频里带着的特效（白娘子的海）：游戏里那一份在视频底下原位铺好，视频淡掉时两层交叠换手（main.js 接） */
      if (onRelease && c.tide != null) onRelease(crew, c.box[1] + c.tide * c.box[2] / c.vw);
    }
    v.style.transition = `opacity ${FADE}s ease-in`;
    v.style.opacity = '0';
    setTimeout(() => { if (cur === me) { hide(v); cur = null; } }, FADE * 1000);
  }
  function hide(v) { v.pause(); v.muted = false; v.style.visibility = 'hidden'; }

  /* 重开一局 / 结算：正在放的直接收掉（她本人已经随 Crew.reset 清掉了） */
  function stop() {
    if (!cur) return;
    const v = cur.v;
    cur = null;
    v.onended = v.onerror = null;
    hide(v);
  }

  /* 首帧之后预取队列的最后一项（main.js / preload.js）：一个一个开始缓冲（一次一个，不跟送礼时的按需加载抢连接），
     每个到 canplaythrough（或出错）算这一个完。读够多少由浏览器定（服务器 serve.py 支持 Range，可以边下边放） */
  function load() {
    return Object.values(vids).reduce((p, v) => p.then(() => new Promise((ok) => {
      if (v.readyState >= 4) { ok(); return; }
      v.addEventListener('canplaythrough', ok, { once: true });
      v.addEventListener('error', ok, { once: true });
      v.preload = 'auto'; v.load();
    })), Promise.resolve());
  }

  const playing = () => !!cur && !cur.done;
  /* 此刻要不要给 crew 那片海垫底：正在放它的视频、过了 seaAt → 视频里海面的画布 y；否则 null */
  const seaUnder = (crew) => cur && !cur.done && cur.crew === crew && cur.c.seaAt != null && cur.v.currentTime >= cur.c.seaAt
    ? cur.c.box[1] + cur.c.tide * cur.c.box[2] / cur.c.vw : null;
  const owner = () => cur && cur.crew;         // 正在放谁的（调试台换人时要连视频一起收掉）
  return { init, load, begin, stop, playing, owner, seaUnder, CLIPS };
})();
