/* preload.js —— 首帧之后的预取队列（2026-10-01，docs/首屏加载诊断.md P1~P3）。
 *
 * 改之前 main.js boot 把 330 个请求（38.8 MB：60 人三人组、礼物图集、档 4、结算图……）全部 await 完才起主循环、绑按钮，
 * 5 Mbps 下首帧 66 秒。现在 boot 只等首帧必需的（长卷背景、待机那 5 张姿势、头像），其余登记成一个个"活"（job），
 * 首帧之后按登记顺序（= 用户最可能先用到的顺序）在后台跑，同时最多 MAX 个在跑 ——
 * 同一个 host 浏览器只开 6 条连接，留两条给送礼时的按需加载（need）插队。
 * 有插队的活没跑完时，后台不再开新的活（已经在跑的照跑）：带宽先给送礼要用的（5 Mbps 下首帧刚出来两边同时送档 3 + 档 4，
 * 要的东西就有 5 MB 上下，后台再开新活只会让人更晚到）。
 *
 * job：{ key, run }，run() 返回 promise（各模块的 load 失败也 resolve，不 reject —— 缺图的路径各自有画法）。
 * 同一个 job 只跑一次：need(key) 插队、队列排到、all() 一起要，拿到的都是同一个 promise。
 * wait: false 的 job（档 4 出场视频）不算进 all()：视频缓冲多少由浏览器定，没缓冲够的送礼直接跳过视频（intro.js begin）。
 */
'use strict';

const Preload = (() => {
  const MAX = 4;
  const jobs = new Map(), order = [];
  let running = 0, urgent = 0, on = false, t0 = 0;
  const listeners = [];

  function add(key, run, opt = {}) {
    const j = { key, run, wait: opt.wait !== false, p: null, done: false, ms: null };
    jobs.set(key, j); order.push(j);
    return j;
  }

  function start(j) {
    if (j.p) return j.p;
    running++;
    const s = performance.now();
    j.p = Promise.resolve(j.run()).then((v) => {
      j.done = true; j.ms = performance.now() - s; running--;
      pump();
      return v;
    });
    return j.p;
  }

  function pump() {
    while (on && running < MAX && !urgent) {
      const j = order.find(q => !q.p);
      if (!j) break;
      start(j);
    }
    if (order.every(q => q.done || !q.wait) && order.length) {
      const fs = listeners.splice(0);
      fs.forEach(f => f());
    }
  }

  return {
    add,
    /* 首帧之后开跑 */
    run() { on = true; t0 = performance.now(); pump(); },
    /* 送礼要用、还没排到：马上开始（不占队列的名额，结束了照样让队列往下走） */
    need(key) {
      const j = jobs.get(key);
      if (j.p) return j.p;
      urgent++;
      return start(j).then((v) => { urgent--; pump(); return v; });
    },
    ready: (key) => jobs.get(key).done,
    /* 全部（wait 的）一起要：诊断模式（胶片 / 压测 / ?live）照旧等全部加载完再开始，结果可复现 */
    all() { order.forEach(start); return Promise.all(order.filter(q => q.wait).map(q => q.p)); },
    /* 队列跑完（wait 的都完了）时回调一次 */
    onIdle(f) { listeners.push(f); pump(); },
    stats: () => ({ n: order.length, done: order.filter(q => q.done).length, ms: on ? performance.now() - t0 : 0 }),
  };
})();
