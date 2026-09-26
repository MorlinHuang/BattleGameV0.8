/* 点礼物按钮验"点一件出一件"：真页面上按按钮文字点一件礼物，之后 5 秒每 0.2 秒记一次
   场上弹幕数（Ammo.count）和哥们在不在场（B）。放到桌面 /home/op/shots/ 下跑（那里有 playwright-core）：
   scp tools/clicktest.js kf-deployment:/home/op/shots/ && ssh kf-deployment "cd /home/op/shots && node clicktest.js" */
const { chromium } = require('/home/op/shots/node_modules/playwright-core');
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  await p.goto('http://127.0.0.1:40235/index.html?v=' + Date.now());
  await p.waitForTimeout(4000);
  for (const name of ['哥们', '口红', '手柄', '香蕉']) {
    await p.evaluate((n) => [...document.querySelectorAll('[data-shop]')].find(x => x.textContent.startsWith(n)).click(), name);
    const seq = [];
    for (let i = 0; i < 25; i++) {
      seq.push(await p.evaluate(() => Ammo.count() + (Buddy.active() ? 'B' : '')));
      if (name === '哥们' && i === 8) await p.screenshot({ path: '/tmp/click_buddy.png' });
      await p.waitForTimeout(200);
    }
    console.log(name.padEnd(3), seq.join(' '));
    await p.waitForTimeout(3000);
  }
  await b.close();
})();
