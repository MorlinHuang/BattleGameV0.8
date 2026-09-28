/* 档 4 女生侧真页面点击：点两次「真相女神」按钮（场上没人时按顺序轮换：第一次真相女神、放完第二次白娘子），
   每秒记谁在场、海水在不在，抓页面报错，白娘子施法中截一张 /tmp/g4_baisu.png。
   scp tools/g4click.js kf-deployment:/home/op/shots/ && ssh kf-deployment "cd /home/op/shots && node g4click.js" */
const { chromium } = require('/home/op/shots/node_modules/playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'] });
  const p = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  const errs = [];
  p.on('pageerror', e => errs.push(e.stack || e.message));
  await p.goto('http://127.0.0.1:40235/index.html?v=' + Date.now());
  await p.waitForTimeout(4000);
  const who = () => p.evaluate(() => (Truth.active() ? 'T' : '') + (Baisu.active() ? 'B' : '') + (Widow.active() ? 'W' : '') + (Sea.active() ? '~' : ''));
  const click = () => p.evaluate(() => [...document.querySelectorAll('[data-shop]')].find(x => x.textContent.startsWith('真相女神')).click());
  await click();
  let seq = [];
  for (let i = 0; i < 16; i++) { seq.push(await who()); await p.waitForTimeout(1000); }
  console.log('第一次', seq.join(' '));
  await click();
  seq = [];
  for (let i = 0; i < 19; i++) { seq.push(await who()); if (i === 5) await p.screenshot({ path: '/tmp/g4_baisu.png' }); await p.waitForTimeout(1000); }
  console.log('第二次', seq.join(' '));
  console.log('报错', errs.length ? errs.join(' | ') : '无');
  await b.close();
})();
