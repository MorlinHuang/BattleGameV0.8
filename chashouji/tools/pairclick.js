/* 档 4 一对人物的真页面点击（2026-09-29）：先点「灭迹恶魔 ④」（男生侧），3 秒后点「真相女神 ④」（女生侧），每秒记一格，抓页面报错，截三张。
   用法：node pairclick.js '<额外 URL 参数>' <截图前缀> [秒数]
     node pairclick.js 'g4L=2&g4R=2&introvideo=0' /tmp/cp      → 嫦娥 / 后羿
     node pairclick.js 'g4L=1&g4R=1' /tmp/td 24                 → 真相女神（带出场视频）/ 灭迹恶魔
   ?g4L= / ?g4R= 是组内下标（main.js G4L / G4R：0 白娘子 / 法海、1 真相女神 / 灭迹恶魔、2 嫦娥 / 后羿）。
   每格：L:名字(在场秒数) R:名字(秒数) 潮：左 / 右进度最大那片的进度；! = 对局结束。截图：<前缀>_1.png（只有男生侧）、_2.png（女生侧刚进场）、_3.png（同场）。
   scp tools/pairclick.js kf-deployment:/home/op/shots/ && ssh kf-deployment "cd /home/op/shots && node pairclick.js ..." */
const { chromium } = require('/home/op/shots/node_modules/playwright-core');
const [, , extra = '', out = '/tmp/pc', secs = '18'] = process.argv;
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'] });
  const p = await b.newPage({ viewport: { width: 1000, height: 1800 } });
  const errs = [];
  p.on('pageerror', e => errs.push(e.stack || e.message));
  await p.goto(`http://127.0.0.1:40235/index.html?v=${Date.now()}&${extra}`);
  /* 等 JS 初始化完：右边档 4 按钮的文字是 JS 改的（HTML 里写的是"相框 ④"），改名和挂 onclick 在同一个循环里（main.js 末尾）。
     不能按秒等：左边档 4 按钮 HTML 里就叫"真相女神 ④"，初始化没完就点得到、点了没反应；2026-09-29 加了潮贴图后初始化要 ~4 秒 */
  await p.waitForFunction(() => [...document.querySelectorAll('[data-shop]')].some(x => x.textContent.startsWith('灭迹恶魔')), null, { timeout: 60000 });
  const who = () => p.evaluate(() => {
    const one = (g) => { const c = g.members.find(m => m.peek()[0]); if (!c) return '-'; const x = c.peek()[0]; return c.cfg.spr.src.split('/').pop().split('%')[0] + (x.hold ? '(视频)' : '(' + x.t.toFixed(0) + ')'); };
    const lv = (ts) => Math.max(...ts.map(t => t.level())).toFixed(1);
    return `L:${one(G4L)} R:${one(G4R)} 潮${lv(TIDES_L)}/${lv(TIDES_R)}${S.phase === 'over' ? '!' : ''}`;
  });
  const click = (n) => p.evaluate((n) => [...document.querySelectorAll('[data-shop]')].find(x => x.textContent.startsWith(n)).click(), n);
  const c = await p.$('canvas');
  await click('灭迹恶魔');
  const seq = [];
  for (let i = 0; i < +secs; i++) {
    seq.push(await who());
    if (i === 3) { await c.screenshot({ path: out + '_1.png' }); await click('真相女神'); }
    if (i === 5) await c.screenshot({ path: out + '_2.png' });
    if (i === +secs - 6) await c.screenshot({ path: out + '_3.png' });
    await p.waitForTimeout(1000);
  }
  console.log(seq.join('\n'));
  console.log('报错', errs.length ? errs.join(' | ') : '无');
  await b.close();
})();
