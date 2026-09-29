/* 帮手前排站位看效果（2026-09-29）：只留前排，叫 n 个哥们 / 闺蜜（可指定 r），等 wait 秒，每隔 gap 毫秒截一张，共 k 张。
   用法：node frontshot.js <截图前缀> [r 逗号分隔（前 nf 个站前排，写成 r,r,r:nf，nf 默认 1）；不给 = 一个前排随机 r；back = 一个后排] [wait] [k] [gap] [额外 URL 参数] [buddy|bestie]
   scp tools/frontshot.js kf-deployment:/home/op/shots/ */
const { chromium } = require('/home/op/shots/node_modules/playwright-core');
const [, , out = '/tmp/fr', rs = '', wait = '1.6', k = '1', gap = '600', extra = '', who = 'buddy'] = process.argv;
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1000, height: 1800 } });
  const errs = []; p.on('pageerror', e => errs.push(e.stack || e.message));
  await p.goto(`http://127.0.0.1:40235/index.html?v=${Date.now()}&${extra}`);
  await p.waitForFunction(() => [...document.querySelectorAll('[data-shop]')].some(x => x.textContent.startsWith('灭迹恶魔')), null, { timeout: 60000 });
  await p.evaluate(([rs, who]) => {
    const nf = +(rs.split(':')[1] || 1); rs = rs.split(':')[0];
    const C = { buddy: Buddy, bestie: Bestie }[who], R = C.cfg.rows, front = R.filter(r => r[0] > 1);
    if (!rs || rs === 'back') { C.cfg.rows = rs ? R.filter(q => q[0] < 1) : front; summonCrew(who); C.cfg.rows = R; return; }
    rs.split(',').map(Number).forEach((r, i) => { C.cfg.rows = i < nf ? front : R.filter(q => q[0] < 1); const x = summonCrew(who)[1]; if (i < nf) x.r = r; });
    C.cfg.rows = R;
  }, [rs, who]);
  await p.waitForTimeout(+wait * 1000);
  const c = await p.$('canvas');
  for (let i = 0; i < +k; i++) { await c.screenshot({ path: `${out}_${i}.png` }); await p.waitForTimeout(+gap); }
  console.log('报错', errs.length ? errs.join(' | ') : '无');
  await b.close();
})();
