/* 档 4 两边真页面点击（2026-09-28）：先点「灭迹恶魔」（男生侧第一个是法海），3 秒后点「真相女神」（女生侧第一个是白娘子），
   每秒记谁在场（F 法海 / B 白娘子 / ~ 海 / = 经卷），抓页面报错；截三张：只有法海 /tmp/fh_1.png、两人同场 /tmp/fh_2.png、/tmp/fh_3.png。
   scp tools/fahaiclick.js kf-deployment:/home/op/shots/ && ssh kf-deployment "cd /home/op/shots && node fahaiclick.js" */
const { chromium } = require('/home/op/shots/node_modules/playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1000, height: 1800 } });
  const errs = [];
  p.on('pageerror', e => errs.push(e.stack || e.message));
  await p.goto('http://127.0.0.1:40235/index.html?v=' + Date.now());
  await p.waitForTimeout(4000);
  const who = () => p.evaluate(() => (Fahai.active() ? 'F' : '') + (Baisu.active() ? 'B' : '') + (Sea.active() ? '~' : '') + (Scroll.active() ? '=' : '') + (S.phase === 'over' ? '!' : '') + (Fahai.peek()[0] ? Fahai.peek()[0].t.toFixed(0) : ''));
  const click = (n) => p.evaluate((n) => [...document.querySelectorAll('[data-shop]')].find(x => x.textContent.startsWith(n)).click(), n);
  const c = await p.$('canvas');
  await click('灭迹恶魔');
  const seq = [];
  for (let i = 0; i < 18; i++) {
    seq.push(await who());
    if (i === 3) { await c.screenshot({ path: '/tmp/fh_1.png' }); await click('真相女神'); }
    if (i === 5) await c.screenshot({ path: '/tmp/fh_in.png' });   // 海正从左边推进来
    if (i === 7) await c.screenshot({ path: '/tmp/fh_2.png' });
    if (i === 10) await c.screenshot({ path: '/tmp/fh_3.png' });
    await p.waitForTimeout(1000);
  }
  console.log(seq.join(' '));
  console.log('报错', errs.length ? errs.join(' | ') : '无');
  await b.close();
})();
