/* bgmotion.js —— 长卷背景里会动的几块（v15 雷雨夜，2026-09-29）。
 *
 * 用户："背景要活起来，但不能喧宾夺主，礼物特效出来时不能乱""画龙点睛，不要什么都动"。
 * 素材是即梦图生视频（取景图 = 游戏里镜头停在某处的一整屏），离线由 v14/bg/v15/video/anim.py 处理成一块块小视频：
 * 配准到底图、逐帧配色、羽化边缘（边缘像素就是底图本身）、常驻的接成无缝循环、偶发的首尾淡回底图。
 * 所以这里只做一件事：把每块小视频按世界坐标**整块盖在房间图上**，不用遮罩，也不用管接缝。
 *
 *   loop  常驻（鱼缸、雨窗、黑猫、床幔）：在镜头里就播，出了镜头就暂停（不占解码）。
 *   event 偶发（写真相框里的人眨眼浅笑）：每隔 GAP 秒、且在镜头里时演一次，演完回到底图。
 * 让位（全盘规划.md 第 5 节）：档 3/4 帮手在场时，常驻的淡到 CALM（往静止底图退三成），偶发的不开演。
 * 按真实时间播（视频自己的时钟），跟对局的顿帧、慢放无关 —— 背景不参与打击感。
 */
'use strict';

const BgMotion = (() => {
  const GAP = [14, 26];     // 偶发事件间隔（秒）
  const CALM = 0.7;         // 让位时动区的不透明度（盖在静止底图上 = 动效退三成）
  const EASE = 2.5;         // 让位进出的快慢（每秒走多少）
  let zones = [], calmK = 0, busy = null, last = 0;

  const gap = () => GAP[0] + Math.random() * (GAP[1] - GAP[0]);

  /* dir 下的 anim.json：[{name, kind, x, y, w, h, src, rate}]，x/y 是世界像素。没有这个文件就是这套房间没有动区 */
  async function load(dir, q) {
    const r = await fetch(dir + 'anim.json' + q);
    if (!r.ok) return 0;
    const now = performance.now() / 1000;
    zones = (await r.json()).map(z => {
      const v = document.createElement('video');
      v.muted = true; v.setAttribute('muted', ''); v.setAttribute('playsinline', ''); v.playsInline = true;
      v.loop = z.kind === 'loop'; v.preload = 'auto';
      v.src = dir + z.src + q;
      v.defaultPlaybackRate = v.playbackRate = z.rate || 1;
      return { ...z, v, next: now + gap() };
    });
    return zones.length;
  }

  /* 浏览器拒绝播放（省电模式、后台标签页）时视频停在原地：画面就是静止的底图，不影响对局 */
  const play = (v) => { if (v.paused) v.play().catch(() => {}); };

  /* x0：房间图第 0 张画在屏幕上的 x（drawWorld 用的同一个取整值），动区跟着房间逐像素对齐 */
  function draw(ctx, x0, W, calm) {
    if (!zones.length) return;
    const now = performance.now() / 1000, dt = Math.min(0.1, now - (last || now)); last = now;
    calmK = Math.min(1, Math.max(0, calmK + (calm ? EASE : -EASE) * dt));
    for (const z of zones) {
      const sx = x0 + z.x, seen = sx + z.w > 0 && sx < W, v = z.v;
      if (z.kind === 'loop') {
        if (!seen) { if (!v.paused) v.pause(); continue; }
        play(v);
      } else {
        if (busy === z && v.ended) { busy = null; z.next = now + gap(); }
        if (busy !== z) {
          if (!seen || calm || busy || now < z.next) continue;
          busy = z; v.currentTime = 0; play(v);
        }
        if (!seen) continue;
      }
      if (v.readyState < 2) continue;
      ctx.globalAlpha = 1 - (1 - CALM) * calmK;
      ctx.drawImage(v, sx, z.y, z.w, z.h);
    }
    ctx.globalAlpha = 1;
  }

  return { load, draw, zones: () => zones };   // zones 给截图脚本查播放状态
})();
