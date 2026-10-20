"""精引3 判据读数：带状物（绸 / 鞭剑 / 橡皮臂 / 竹棒）由 TrioFX.ribbon 实际画出来的轮廓 —— 首段沿手、伸长肢体直、曲率连续无折角。
做法：页面里（正式页 / 临时页，用的就是那一页部署的 trio_fx.js）拿角色数据建 ribbon 句柄，画进一个"录路径"的 ctx（转发给真画布，同时记下
描边 stroke 的点列 = 带子的墨线轮廓：一边 → 梢 → 另一边），按引擎的时间轴（抽打 W.t / 出拳 b.pk.t）逐 1/60 秒推一整下，每帧量：
  a0    中线离手 12 px 那一点的方向与出口方向的差（°）—— 首段沿手（绸 / 剑：出口方向 = dir；臂 / 棒：前臂方向）
  cTurn 中线相邻两段的最大转角（°，去掉头尾各两个点）—— 折角：样条顺滑的带子 4° 一档地拐，折线在波峰处一下 20~60°
  eTurn 两条边线的最大转角 —— 中线顺、边线折 = 弯得比半宽还急（内侧边打结）或宽度突变
  dev   中线离"根 → 梢"直线最远多少 px（只看臂 / 棒：伸长肢体要直）
  只算伸出去 e ≥ 0.25 的帧；e < 0.25（刚出手 / 快收完，带子只是手边一小截）记在 early（帧数、a0、离手最远）
用法：python3 bands.py <页面 url> [out.json]（桌面里跑，需要 GUI Chrome / playwright）"""
import asyncio, json, sys
from playwright.async_api import async_playwright
URL = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/p3/bands.json'
JS = r"""
() => {
  const R = {}, deg = (a) => a * 57.2958, wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
  const cv = document.createElement('canvas'); cv.width = 960; cv.height = 1707;
  const real = cv.getContext('2d');
  let rec = [], cur = null;
  const ctx = new Proxy(real, { get(t, k) {
    if (k === 'beginPath') return () => { cur = []; t.beginPath(); };
    if (k === 'moveTo') return (x, y) => { if (cur) cur.push([[x, y]]); t.moveTo(x, y); };
    if (k === 'lineTo') return (x, y) => { if (cur && cur.length) cur[cur.length - 1].push([x, y]); t.lineTo(x, y); };
    if (k === 'stroke') return () => { if (cur) for (const sp of cur) if (sp.length >= 6) rec.push(sp); t.stroke(); };
    const v = t[k]; return typeof v === 'function' ? v.bind(t) : v; },
    set(t, k, v) { t[k] = v; return true; } });
  const easeOut = (x) => 1 - (1 - x) * (1 - x);
  const measure = (style, Q, from, dir, toAt, T, tube) => {
    /* 每帧：e ≥ 0.25（伸出去四分之一以上）才计判据；e < 0.25 的几帧单独记 early（刚出手 / 快收完时带子是横在手边的一小截） */
    const h = TrioFX.ribbon(Q, style), o = { style, frames: 0, a0max: 0, a0at: null, cTurnMax: 0, cTurnAt: null, eTurnMax: 0, eTurnAt: null, devMax: tube ? 0 : null, early: { frames: 0, a0max: 0, spanMax: 0 } };
    for (let t = 1 / 60; t <= T + 1e-9; t += 1 / 60) {
      const [to, e] = toAt(t); rec = [];
      h.draw(ctx, from, dir, to, e, t, 1);
      const sp = rec.sort((a, b) => b.length - a.length)[0];
      if (!sp) continue;
      const m = sp.length >> 1, L = sp.slice(0, m), Rr = sp.slice(m).reverse(), C = L.map((p, i) => [(p[0] + Rr[i][0]) / 2, (p[1] + Rr[i][1]) / 2]);
      const d0 = Array.isArray(dir) ? Math.atan2(dir[1] - from[1], dir[0] - from[0]) : dir == null ? Math.atan2(to[1] - from[1], to[0] - from[0]) : dir;
      const k = C.findIndex(p => Math.hypot(p[0] - from[0], p[1] - from[1]) > 12);
      const a0 = k > 0 ? Math.abs(deg(wrap(Math.atan2(C[k][1] - from[1], C[k][0] - from[0]) - d0))) : null;
      if (e < 0.25) {
        o.early.frames++; if (a0 != null) o.early.a0max = Math.max(o.early.a0max, +a0.toFixed(1));
        for (const p of C) o.early.spanMax = Math.max(o.early.spanMax, +Math.hypot(p[0] - from[0], p[1] - from[1]).toFixed(0));
        continue;
      }
      o.frames++;
      if (a0 != null && a0 > o.a0max) { o.a0max = +a0.toFixed(1); o.a0at = +t.toFixed(3); }
      const turns = (E, key, at) => { for (let i = 1; i < E.length - 1; i++) {
        const l0 = Math.hypot(E[i][0] - E[i - 1][0], E[i][1] - E[i - 1][1]), l1 = Math.hypot(E[i + 1][0] - E[i][0], E[i + 1][1] - E[i][1]);
        if (l0 < 2 || l1 < 2 || i < 2 || i > E.length - 3) continue;
        const x = Math.abs(deg(wrap(Math.atan2(E[i + 1][1] - E[i][1], E[i + 1][0] - E[i][0]) - Math.atan2(E[i][1] - E[i - 1][1], E[i][0] - E[i - 1][0]))));
        if (x > o[key]) { o[key] = +x.toFixed(1); o[at] = [+t.toFixed(3), +(i / E.length).toFixed(2)]; } } };
      turns(C, 'cTurnMax', 'cTurnAt'); turns(L, 'eTurnMax', 'eTurnAt'); turns(Rr, 'eTurnMax', 'eTurnAt');
      if (tube) { const q = C[C.length - 1], dx = q[0] - from[0], dy = q[1] - from[1], ll = Math.hypot(dx, dy) || 1;
                  for (const p of C) o.devMax = Math.max(o.devMax, +Math.abs(((p[0] - from[0]) * dy - (p[1] - from[1]) * dx) / ll).toFixed(1)); }
    }
    return o;
  };
  const cast = { ...TRIO_BUDDY.cast, ...TRIO_BESTIE.cast };
  /* 抽打：沿 dir 甩出去（控制点 = rayC(h, tg, d, 0.3)，引擎 drawWhip），e 同 drawWhip */
  for (const [id, style] of [['G9', 'silk'], ['G13', 'silk'], ['G17', 'blade']]) {
    const A = cast[id].atk, Ph = A.phases, h = [300, 760], tg = [640, 700], d = -0.5, L = Math.hypot(tg[0] - h[0], tg[1] - h[1]) * 0.3;
    const c = [h[0] + Math.cos(d) * L, h[1] + Math.sin(d) * L];
    const eAt = (t) => t < Ph[0] ? easeOut(t / Ph[0]) : t < Ph[0] + Ph[1] ? 1 : 1 - Math.pow(Math.min(1, (t - Ph[0] - Ph[1]) / Ph[2]), 2);
    R[id] = measure(style, A.whip, h, c, (t) => [tg, eAt(t)], Ph[0] + Ph[1] + Ph[2], false);
    R[id].dirNote = 'dir = 控制点 rayC（首段切线 = d = -28.6°）';
  }
  /* 出拳：腕 → 拳头沿前臂方向直伸（引擎 drawArm：拳头在前臂线上），伸 easeOut、停、回 */
  for (const [id, style] of [['B12', 'arm'], ['G29', 'bamboo']]) {
    const A = cast[id].atk, Ph = A.phases, wr = [600, 700], d = id[0] === 'B' ? Math.PI + 0.35 : -0.6, D = 380;
    const kAt = (t) => t < Ph[0] ? easeOut(t / Ph[0]) : t < Ph[0] + Ph[1] ? 1 : 1 - Math.min(1, (t - Ph[0] - Ph[1]) / Ph[2]);
    R[id] = measure(style, A, wr, d, (t) => { const k = 30 + D * kAt(t); return [[wr[0] + Math.cos(d) * k, wr[1] + Math.sin(d) * k], 1]; }, Ph[0] + Ph[1] + Ph[2], true);
  }
  return R;
}
"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(); pg.set_default_timeout(600000)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL + ('&' if '?' in URL else '?') + 'auto=0', timeout=600000)
        await pg.wait_for_function('typeof TrioFX !== "undefined" && TrioFX.ready()', timeout=600000)
        md5 = await pg.evaluate("fetch('trio_fx.js',{cache:'no-store'}).then(r=>r.text()).then(t=>t.length)")
        r = await pg.evaluate(JS); r['_trio_fx_len'] = md5; r['_errs'] = errs[:5]
        await b.close()
    json.dump(r, open(OUT, 'w'), ensure_ascii=False, indent=1); print(json.dumps(r, ensure_ascii=False, indent=1))
asyncio.run(main())
