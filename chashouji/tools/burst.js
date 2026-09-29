/* 档 4 单人连拍（2026-09-29，看嫦娥月光束的蓄—轰节奏）：点一边的档 4，等 wait 秒，之后每 gap 毫秒截一张，共 n 张；抓页面报错。
   用法：node burst.js '<额外 URL 参数>' <截图前缀> <按钮名开头> [wait 秒] [n] [gap 毫秒]
     node burst.js 'g4L=2&introvideo=0' /tmp/mb 真相女神 4 12 150   → 嫦娥 → /tmp/mb_00.png …
   按钮名：左边档 4 叫「真相女神 ④」、右边「灭迹恶魔 ④」（main.js SHOP）。每张同时打印那一刻她的光束状态（第几个光点 / 蓄 / 轰 / 隔）。
   gap 给 fire：不按时间拍，每张都等到光束正在轰（b.beam.ph 'fire'）才拍 —— 软件渲染下截一张要一秒多，按时间拍多半拍不到那 0.3 秒。
   scp tools/burst.js kf-deployment:/home/op/shots/ */
const { chromium } = require('/home/op/shots/node_modules/playwright-core');
const [, , extra = '', out = '/tmp/mb', btn = '真相女神', wait = '4', n = '12', gap = '150'] = process.argv;
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'] });
  const p = await b.newPage({ viewport: { width: 1000, height: 1800 } });
  const errs = [];
  p.on('pageerror', e => errs.push(e.stack || e.message));
  await p.goto(`http://127.0.0.1:40235/index.html?v=${Date.now()}&${extra}`);
  await p.waitForFunction(() => [...document.querySelectorAll('[data-shop]')].some(x => x.textContent.startsWith('灭迹恶魔')), null, { timeout: 60000 });
  await p.evaluate((n) => [...document.querySelectorAll('[data-shop]')].find(x => x.textContent.startsWith(n)).click(), btn);
  await p.waitForTimeout(+wait * 1000);
  const c = await p.$('canvas');
  for (let i = 0; i < +n; i++) {
    const st = await p.evaluate(() => {
      for (const g of [G4L, G4R]) for (const m of g.members) { const x = m.peek()[0]; if (x) return `t=${x.t.toFixed(2)} ` + (x.beam ? `${x.beam.k}${x.beam.ph}${x.beam.pt.toFixed(2)}` : ''); }
      return '-';
    });
    if (gap === 'fire') await p.waitForFunction(() => [G4L, G4R].some(g => g.members.some(m => { const x = m.peek()[0]; return x && x.beam && x.beam.ph === 'fire' && x.beam.pt > 0.06; })), null, { timeout: 20000, polling: 16 });
    await c.screenshot({ path: `${out}_${String(i).padStart(2, '0')}.png` });
    console.log(i, st);
    await p.waitForTimeout(gap === 'fire' ? 400 : +gap);
  }
  console.log('报错', errs.length ? errs.join(' | ') : '无');
  await b.close();
})();
