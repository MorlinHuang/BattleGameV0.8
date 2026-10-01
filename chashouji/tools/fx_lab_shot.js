/* fx_lab.html 拍胶片 / 压测（2026-10-01，trio_fx 新旧对比）。桌面容器上跑：
     node fx_lab_shot.js film hit  /tmp/fx_hit.png  [额外参数]
     node fx_lab_shot.js bench -   -               [额外参数]
     node fx_lab_shot.js live  beam /tmp/live.png  [额外参数]   → 交互模式（rAF 循环）跑 4 秒截整页，看报错
   film：等标题 FILMDONE，把 window.FILM（dataURL）存成 png；bench 见 fx_lab.html。都打印页面报错（pageerror + console.error），无报错打印 errors []。
   bench 要真实计时，走 headless=false（DISPLAY=:1 的 GUI Chrome；skill chashouji-verify：虚拟时间下 performance.now 不走） */
const { chromium } = require('/home/op/shots/node_modules/playwright-core');
const fs = require('fs');
const [, , what = 'film', kind = 'hit', out = '/tmp/fx.png', extra = ''] = process.argv;
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: what !== 'bench',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--enable-unsafe-swiftshader', '--force-device-scale-factor=1'] });
  const p = await b.newPage({ viewport: { width: 1400, height: 900 } });
  const errs = [];
  p.on('pageerror', e => errs.push(e.stack || e.message));
  p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  const url = what === 'live' ? `http://127.0.0.1:40235/fx_lab.html?v=${Date.now()}&mode=${kind}&${extra}`
    : `http://127.0.0.1:40235/fx_lab.html?v=${Date.now()}&${what}=${what === 'bench' ? 1 : kind}&${extra}`;
  await p.goto(url);
  if (what === 'live') {
    await p.waitForTimeout(4000);
    await p.screenshot({ path: out });
    console.log('写出', out, await p.evaluate(() => document.getElementById('note').textContent));
    console.log('errors', JSON.stringify(errs));
    await b.close();
    return;
  }
  /* 页面一报错就别再等完成信号（main() 抛了就永远不会置标题） */
  const t0 = Date.now();
  while (!errs.length && !/^(FILMDONE|BENCHDONE)/.test(await p.title())) {
    if (Date.now() - t0 > +(process.env.LAB_TIMEOUT || 240000)) { errs.push('超时：标题一直没置 FILMDONE / BENCHDONE'); break; }
    await p.waitForTimeout(500);
  }
  if (what === 'film') {
    const d = await p.evaluate(() => window.FILM || '');
    if (d) fs.writeFileSync(out, Buffer.from(d.split(',')[1], 'base64'));
    console.log('写出', out, d.length);
  } else console.log(await p.evaluate(() => JSON.stringify(window.BENCH)));
  console.log('errors', JSON.stringify(errs));
  await b.close();
})();
