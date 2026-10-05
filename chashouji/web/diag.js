/* diag.js —— 真机诊断信标（2026-10-06）。
 *
 * 用户在安卓微信 / 抖音内置浏览器里打开：档 4 没有动画、很多特效是老贴图。服务器日志看得到手机把视频、图集都请求到了，
 * 但网页里各模块加载失败都是静默退回老画法（矢量弹道、立绘、老配方），看不出是哪一步、因为什么失败。
 * 这里在所有脚本之前挂上，记下：内核版本、几个新接口支不支持、脚本报错（含语法错误：旧内核解析不了某个文件时整份不执行）、
 * 预取队列每一项到没到、页面上每个 <video> 的状态，以及一段带透明通道的 webm 解出来角上是不是透明的。
 * 打开 40 秒后发一次（再出新报错补发一次）：GET /diag?d=<json>，serve.py 回 404，但访问日志里留下整条 —— 不用用户截图。
 * ?diag=1 时同时把结果铺在页面上。
 * 只用 ES5 写：要在旧内核上跑起来才诊断得了旧内核。
 */
(function () {
  var Q = new URLSearchParams(location.search);
  if (Q.get('diag') === '0') return;
  var t0 = Date.now(), errs = [], sent = 0;

  function short(s) { return String(s || '').replace(location.origin + '/', '').slice(0, 160); }
  window.addEventListener('error', function (e) {
    if (errs.length < 12) errs.push([Math.round((Date.now() - t0) / 1000), short(e.message), short(e.filename) + ':' + e.lineno]);
    if (sent) send('err');
  }, true);
  window.addEventListener('unhandledrejection', function (e) {
    var r = e.reason;
    if (errs.length < 12) errs.push([Math.round((Date.now() - t0) / 1000), 'reject ' + short(r && (r.stack || r.message) || r)]);
    if (sent) send('err');
  });

  function feats() {
    var c = document.createElement('canvas').getContext('2d'), v = document.createElement('video');
    return {
      roundRect: !!(c && c.roundRect), at: !!Array.prototype.at, rvfc: !!(v.requestVideoFrameCallback),
      offscreen: typeof OffscreenCanvas !== 'undefined', bitmap: typeof createImageBitmap !== 'undefined', worker: typeof Worker !== 'undefined',
      filter: !!(c && 'filter' in c), vp9: v.canPlayType('video/webm; codecs="vp9"'), mem: navigator.deviceMemory || null,
      dpr: window.devicePixelRatio, scr: screen.width + 'x' + screen.height,
    };
  }

  /* 带透明通道的 webm 在这台机器上解出来是不是透明的：最小的那段循环视频，取第一帧左上角（那里是透明背景）的 alpha */
  var alpha = null;
  function alphaTest() {
    var v = document.createElement('video');
    v.muted = true; v.playsInline = true; v.preload = 'auto'; v.src = 'assets/video/sister_loop_alpha.webm';
    v.style.cssText = 'position:fixed;left:0;top:0;width:1px;height:1px;opacity:0;pointer-events:none';
    document.body.appendChild(v);
    alpha = 'loading';
    v.addEventListener('error', function () { alpha = 'error ' + (v.error && v.error.code); });
    v.addEventListener('loadeddata', function () {
      try {
        var cv = document.createElement('canvas'); cv.width = 8; cv.height = 8;
        var cx = cv.getContext('2d'); cx.drawImage(v, 0, 0, 8, 8, 0, 0, 8, 8);
        alpha = 'a=' + cx.getImageData(0, 0, 1, 1).data[3] + ' ' + v.videoWidth + 'x' + v.videoHeight;
      } catch (e) { alpha = 'draw ' + e.message; }
      v.parentNode && v.parentNode.removeChild(v);
    });
  }

  function report(why) {
    var vids = [], vs = document.querySelectorAll('video');
    for (var i = 0; i < vs.length; i++) {
      var v = vs[i];
      vids.push([short(v.currentSrc || v.src).replace('assets/video/', ''), v.readyState, v.networkState, v.error ? v.error.code : 0, v.paused ? 0 : 1]);
    }
    var pre = null;
    try {   // 姿势几十项只记到了几张，其余每项记 [key, 开跑, 用时]
      var L = Preload.list(), np = 0, dp = 0;
      pre = [];
      for (var j = 0; j < L.length; j++) {
        if (L[j][0].indexOf('pose:') === 0) { np++; if (L[j][2] != null) dp++; }
        else pre.push(L[j]);
      }
      pre.unshift(['pose', dp + '/' + np]);
    } catch (e) { pre = 'n/a ' + e.message; }
    return {
      why: why, t: Math.round((Date.now() - t0) / 1000), ua: navigator.userAgent, f: feats(), alpha: alpha,
      err: errs, pre: pre, vid: vids,
    };
  }

  function send(why) {
    sent++;
    var r = report(why), s = JSON.stringify(r);
    new Image().src = '/diag?d=' + encodeURIComponent(s.slice(0, 6000));
    if (Q.get('diag') === '1') {
      var el = document.getElementById('diagbox');
      if (!el) {
        el = document.createElement('pre'); el.id = 'diagbox';
        el.style.cssText = 'position:fixed;left:0;top:0;right:0;max-height:70%;overflow:auto;z-index:99;margin:0;padding:6px;' +
          'background:rgba(0,0,0,.8);color:#0f0;font:11px/1.35 monospace;white-space:pre-wrap;word-break:break-all';
        document.body.appendChild(el);
      }
      el.textContent = JSON.stringify(r, null, 1);
    }
  }

  window.addEventListener('load', function () {
    alphaTest();
    setTimeout(function () { send('t40'); }, 40000);
  });
})();
