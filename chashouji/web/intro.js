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
  };
  const POP = 0.35, FADE = 0.45;         // 浮现几秒、结尾淡掉几秒
  /* VP9 透明只有 Chromium 内核认。按 UA 判（Safari 的 canPlayType 也说能放 webm，但透明通道丢掉，变黑底） */
  const ALPHA_OK = /Chrom(e|ium)\/|Edg\//.test(navigator.userAgent);

  let stage = null, W = 960, H = 1707, cur = null;
  const vids = {};                         // 配方名 → 预加载好的 <video>

  function init(opt) {
    stage = opt.stage; W = opt.W; H = opt.H;
    if (new URLSearchParams(location.search).get('introvideo') === '0' || !ALPHA_OK) return;   // ?introvideo=0：关掉（胶片 / 压测用）
    for (const [k, c] of Object.entries(CLIPS)) {
      const v = document.createElement('video');
      v.src = c.src; v.preload = 'auto'; v.playsInline = true;
      const [x, y, w, h] = c.box;
      Object.assign(v.style, {
        position: 'absolute', left: x / W * 100 + '%', top: y / H * 100 + '%', width: w / W * 100 + '%', height: h / H * 100 + '%',
        objectFit: 'fill', visibility: 'hidden', pointerEvents: 'none',
      });
      stage.insertBefore(v, stage.querySelector('.panel'));
      vids[k] = v;
    }
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
    if (crew.peek().includes(b)) { b.hold = false; b.t = 0; b.from = endPose(c, crew.cfg.spr); }
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

  const playing = () => !!cur && !cur.done;
  return { init, begin, stop, playing, CLIPS };
})();
