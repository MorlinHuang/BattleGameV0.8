/* intro.js —— 档 4 的出场视频（2026-09-28，即梦 Seedance 生成）。
 *
 * 送礼 → 先放一段 8 秒视频（天降、对镜头放电、举罐瞄准），视频最后一秒机位固定，她悬在画面左上方、背景过曝成金白；
 * 视频播完的那一刻，游戏里的她在**同一个位置、同一个姿势**出现（视频就是照着这张立绘生成的，尾帧对齐量过），
 * 然后视频整片淡掉 —— 金白色背景溶开露出游戏，她留在原地，再滑一小段进悬停位开火。读起来是她从视频里走进游戏。
 *
 * 为什么是 DOM <video> 盖在画布上、不画进 canvas：视频有自己的音轨，<video> 自带音画同步；画进 canvas 要每帧
 * drawImage 一张 834×1112 的视频帧，还得自己对音频时钟。视频区下沿压着调试按钮区，所以插在 .panel 之前（按钮仍可点）。
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
    truth: { src: 'assets/video/truth_intro.mp4', box: [0, 200, 960, 1280], vw: 834, end: { s: 0.819, x: 6, y: 7 } },
  };
  const POP = 0.25, FADE = 0.45;          // 弹出几秒、结尾淡掉几秒

  let stage = null, W = 960, H = 1707, cur = null;
  const vids = {};                         // 配方名 → 预加载好的 <video>

  function init(opt) {
    stage = opt.stage; W = opt.W; H = opt.H;
    if (new URLSearchParams(location.search).get('introvideo') === '0') return;   // ?introvideo=0：关掉（胶片 / 压测用）
    for (const [k, c] of Object.entries(CLIPS)) {
      const v = document.createElement('video');
      v.src = c.src; v.preload = 'auto'; v.playsInline = true;
      const [x, y, w, h] = c.box;
      Object.assign(v.style, {
        position: 'absolute', left: x / W * 100 + '%', top: y / H * 100 + '%', width: w / W * 100 + '%', height: h / H * 100 + '%',
        objectFit: 'fill', visibility: 'hidden', pointerEvents: 'none', borderRadius: '1.2cqw',
        boxShadow: '0 0 0 0.4cqw rgba(255,214,110,.9), 0 0 4cqw rgba(255,200,80,.55)',
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
    cur = { v, crew, b, c, t: 0, done: false };
    v.currentTime = 0;
    v.style.transition = 'none'; v.style.opacity = '0'; v.style.transform = 'scale(.92)'; v.style.visibility = 'visible';
    requestAnimationFrame(() => {
      v.style.transition = `opacity ${POP}s ease-out, transform ${POP}s cubic-bezier(.2,1.4,.4,1)`;
      v.style.opacity = '1'; v.style.transform = 'scale(1)';
    });
    const go = v.play();
    /* 带声音自动播放被浏览器拦（页面还没被点过）：静音再放一次。画面照演，只是没声音 —— 直播时页面一定被点过。 */
    if (go) go.catch(() => { v.muted = true; return v.play(); }).catch(() => release());
    v.onended = release;
    v.onerror = release;
    return true;
  }

  /* 收起视频一律用 visibility，不用 display:none：桌面容器的 Chrome 里，放过的 <video> 一被 display:none，
     整页合成就停了 —— JS 照跑（?titleclock=1 看得到时钟在走），画面定在最后一帧不再刷新（2026-09-28 录屏复现，
     换 visibility 后同一流程正常）。 */
  /* 视频放完：她在尾帧那个位置现身（crew.js hoverPose 从 b.from 滑进悬停位），视频淡掉 */
  function release() {
    if (!cur || cur.done) return;
    const { v, crew, b, c } = cur;
    cur.done = true;
    if (crew.peek().includes(b)) { b.hold = false; b.t = 0; b.from = endPose(c, crew.cfg.spr); }
    v.style.transition = `opacity ${FADE}s ease-in`;
    v.style.opacity = '0';
    setTimeout(() => { v.pause(); v.style.visibility = 'hidden'; v.muted = false; if (cur && cur.v === v) cur = null; }, FADE * 1000);
  }

  /* 重开一局 / 结算：正在放的直接收掉（她本人已经随 Crew.reset 清掉了） */
  function stop() {
    if (!cur) return;
    const v = cur.v;
    cur = null;
    v.onended = v.onerror = null;
    v.pause(); v.style.visibility = 'hidden'; v.muted = false;
  }

  const playing = () => !!cur && !cur.done;
  return { init, begin, stop, playing, CLIPS };
})();
