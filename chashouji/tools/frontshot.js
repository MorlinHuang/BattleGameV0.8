/* 哥们前排站位看效果（2026-09-29）：只留前排，叫 n 个哥们（可指定 r），等 wait 秒，每隔 gap 毫秒截一张，共 k 张。
   用法：node frontshot.js <截图前缀> [r 逗号分隔（第一个站前排）；不给 = 一个前排随机 r；back = 一个后排] [wait] [k] [gap] [额外 URL 参数]
   scp tools/frontshot.js kf-deployment:/home/op/shots/ */
const { chromium } = require('/home/op/shots/node_modules/playwright-core');
const [, , out = '/tmp/fr', rs = '', wait = '1.6', k = '1', gap = '600', extra = ''] = process.argv;
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1000, height: 1800 } });
  const errs = []; p.on('pageerror', e => errs.push(e.stack || e.message));
  await p.goto(`http://127.0.0.1:40235/index.html?v=${Date.now()}&${extra}`);
  await p.waitForFunction(() => [...document.querySelectorAll('[data-shop]')].some(x => x.textContent.startsWith('灭迹恶魔')), null, { timeout: 60000 });
  await p.evaluate((rs) => {
    const R = Buddy.cfg.rows, front = R.filter(r => r[0] > 1);
    if (!rs || rs === 'back') { Buddy.cfg.rows = rs ? R.filter(q => q[0] < 1) : front; summonCrew('buddy'); Buddy.cfg.rows = R; return; }
    rs.split(',').map(Number).forEach((r, i) => { Buddy.cfg.rows = i ? R.filter(q => q[0] < 1) : front; const x = summonCrew('buddy')[1]; if (!i) x.r = r; });
    Buddy.cfg.rows = R;
  }, rs);
  await p.waitForTimeout(+wait * 1000);
  const c = await p.$('canvas');
  for (let i = 0; i < +k; i++) { await c.screenshot({ path: `${out}_${i}.png` }); await p.waitForTimeout(+gap); }
  console.log('报错', errs.length ? errs.join(' | ') : '无');
  await b.close();
})();
