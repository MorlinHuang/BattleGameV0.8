/* 点礼物按钮验"点一件出一件"：真页面上按按钮文字点一件礼物，之后 5 秒每 0.2 秒记一次
   场上弹幕数（Ammo.count）和哥们（B）、闺蜜（G）、榴莲鞋雨（R）、臭袜子足球（S）在不在场。放到桌面 /home/op/shots/ 下跑（那里有 playwright-core）：
   scp tools/clicktest.js kf-deployment:/home/op/shots/ && ssh kf-deployment "cd /home/op/shots && node clicktest.js" */
const { chromium } = require('/home/op/shots/node_modules/playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  await p.goto('http://127.0.0.1:40235/index.html?v=' + Date.now());
  /* 等 JS 初始化完：右边档 4 按钮的文字是 JS 改的（HTML 里写的是"相框 ④"），改名和挂 onclick 在同一个循环里（main.js 末尾）。
     不能按秒等：左边档 4 按钮 HTML 里就叫"真相女神 ④"，初始化没完就点得到、点了没反应；2026-09-29 加了潮贴图后初始化要 ~4 秒 */
  await p.waitForFunction(() => [...document.querySelectorAll('[data-shop]')].some(x => x.textContent.startsWith('灭迹恶魔')), null, { timeout: 60000 });
  for (const name of ['哥们', '闺蜜', '榴莲鞋雨', '臭袜子足球', '口红', '香蕉']) {
    await p.evaluate((n) => [...document.querySelectorAll('[data-shop]')].find(x => x.textContent.startsWith(n)).click(), name);
    const seq = [];
    for (let i = 0; i < 25; i++) {
      seq.push(await p.evaluate(() => Ammo.count() + (Buddy.active() ? 'B' : '') + (Bestie.active() ? 'G' : '') + (DurianRain.active() ? 'R' : '') + (SockRain.active() ? 'S' : '')));
      if (name === '哥们' && i === 8) await p.screenshot({ path: '/tmp/click_buddy.png' });
      await p.waitForTimeout(200);
    }
    console.log(name.padEnd(3), seq.join(' '));
    await p.waitForTimeout(3000);
  }
  await b.close();
})();
