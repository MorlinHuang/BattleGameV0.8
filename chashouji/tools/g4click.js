/* 档 4 女生侧真页面点击：点三次「真相女神 ④」按钮，场上没人时按顺序轮换 —— 第一次白娘子、第二次真相女神、第三次嫦娥
   （main.js G4L；每人在场 15 秒，等前一个走了再点）。每秒记谁在场、左边哪片潮有进度，抓页面报错；白娘子施法中截一张 /tmp/g4_baisu.png。
   关掉出场视频（?introvideo=0）：视频推迟女神 8 秒，三轮会超时；视频交接见 pairclick.js 'g4L=1&g4R=1'。
   scp tools/g4click.js kf-deployment:/home/op/shots/ && ssh kf-deployment "cd /home/op/shots && node g4click.js" */
const { chromium } = require('/home/op/shots/node_modules/playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  const errs = [];
  p.on('pageerror', e => errs.push(e.stack || e.message));
  await p.goto('http://127.0.0.1:40235/index.html?introvideo=0&v=' + Date.now());
  /* 等 JS 初始化完：右边档 4 按钮的文字是 JS 改的（HTML 里写的是"相框 ④"），改名和挂 onclick 在同一个循环里（main.js 末尾）。
     不能按秒等：左边档 4 按钮 HTML 里就叫"真相女神 ④"，初始化没完就点得到、点了没反应；2026-09-29 加了潮贴图后初始化要 ~4 秒 */
  await p.waitForFunction(() => [...document.querySelectorAll('[data-shop]')].some(x => x.textContent.startsWith('灭迹恶魔')), null, { timeout: 60000 });
  /* B 白娘子 / T 真相女神 / C 嫦娥；~ 海、g 真相云海、m 月夜银云海（有进度就记） */
  const who = () => p.evaluate(() => (Baisu.active() ? 'B' : '') + (Truth.active() ? 'T' : '') + (Change.active() ? 'C' : '')
    + (Sea.active() ? '~' : '') + (TruthTide.active() ? 'g' : '') + (MoonSky.active() ? 'm' : ''));
  const click = () => p.evaluate(() => [...document.querySelectorAll('[data-shop]')].find(x => x.textContent.startsWith('真相女神')).click());
  for (const [name, n] of [['第一次', 19], ['第二次', 19], ['第三次', 19]]) {
    await click();
    const seq = [];
    for (let i = 0; i < n; i++) { seq.push(await who()); if (name === '第一次' && i === 5) await p.screenshot({ path: '/tmp/g4_baisu.png' }); await p.waitForTimeout(1000); }
    console.log(name, seq.join(' '));
  }
  console.log('报错', errs.length ? errs.join(' | ') : '无');
  await b.close();
})();
