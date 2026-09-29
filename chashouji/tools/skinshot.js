/* 帮手换皮一览（2026-09-29，闺蜜加到九个形象）：每次同时叫三个指定形象，等 wait 秒截一张；抓页面报错。
   用法：node skinshot.js <帮手 buddy|bestie> <截图前缀> <形象下标，逗号分隔，三个一组用 / 隔开> [wait 秒]
     node skinshot.js bestie /tmp/sk 0,1,2/3,4,5/6,7,8 1.6   → /tmp/sk_0.png …（每张是一组）
   scp tools/skinshot.js kf-deployment:/home/op/shots/ */
const { chromium } = require('/home/op/shots/node_modules/playwright-core');
const [, , who = 'bestie', out = '/tmp/sk', groups = '0,1,2', wait = '1.6'] = process.argv;
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
  const errs = [];
  for (const [gi, g] of groups.split('/').entries()) {
    const p = await b.newPage({ viewport: { width: 1000, height: 1800 } });
    p.on('pageerror', e => errs.push(e.stack || e.message));
    await p.goto(`http://127.0.0.1:40235/index.html?v=${Date.now()}`);
    await p.waitForFunction(() => [...document.querySelectorAll('[data-shop]')].some(x => x.textContent.startsWith('灭迹恶魔')), null, { timeout: 60000 });
    await p.evaluate(([w, ks]) => ks.forEach(k => summonCrew(w, k)), [who, g.split(',').map(Number)]);
    await p.waitForTimeout(+wait * 1000);
    await (await p.$('canvas')).screenshot({ path: `${out}_${gi}.png` });
    await p.close();
  }
  console.log('报错', errs.length ? errs.join(' | ') : '无');
  await b.close();
})();
