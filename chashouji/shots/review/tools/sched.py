import json
from playwright.sync_api import sync_playwright
JS = r"""() => {
 const res = {first:{}, seq:[], over:[]};
 const snap = () => [...Bestie.peek().map(b=>'B'+b.skin), ...Truth.peek().map(b=>'T'+b.skin)].sort().join(',');
 for (let i=0;i<3000;i++){ Bestie.reset(); Truth.reset(); BestieGroup.summon(); const k=snap(); res.first[k]=(res.first[k]||0)+1; }
 const cnt = {};
 for (let i=0;i<2000;i++){ Bestie.reset(); Truth.reset(); for(let j=0;j<4;j++) BestieGroup.summon(); const k=snap(); cnt[k]=(cnt[k]||0)+1; }
 res.four = cnt;
 const c3 = {};
 for (let i=0;i<2000;i++){ Bestie.reset(); Truth.reset(); for(let j=0;j<3;j++) BestieGroup.summon(); const k=snap(); c3[k]=(c3[k]||0)+1; }
 res.three = c3;
 const c5 = {};
 for (let i=0;i<2000;i++){ Bestie.reset(); Truth.reset(); for(let j=0;j<5;j++) BestieGroup.summon(); const k=snap(); c5[k]=(c5[k]||0)+1; }
 res.five = c5;
 try { Bestie.reset(); Truth.reset(); BestieGroup.summon(5); BestieGroup.summon(-3); res.e3 = 'ok ' + snap(); } catch (e) { res.e3 = 'ERR ' + e; }
 // 续时间：Truth 在场且满员时再召唤
 Bestie.reset(); Truth.reset(); Truth.summon(); for (let i=0;i<60;i++) Truth.update(1/60);
 const before = Truth.peek()[0].spray; Truth.summon(); res.extend = [before, Truth.peek()[0].spray, Truth.peek().length];
 // Truth 正在离场时再召唤（强制成员1）
 Bestie.reset(); Truth.reset(); Truth.summon(); for (let i=0;i<Math.round((0.55+2.8+0.1)*60);i++) Truth.update(1/60);
 const b0 = Truth.peek()[0]; const t0=b0.t; Truth.summon(); res.exitResummon = {oldT:t0, now: Truth.peek().map(b=>({t:+b.t.toFixed(3), spray:+b.spray.toFixed(3), back:+(b.back||0).toFixed(1)}))};
 Bestie.reset(); Truth.reset();
 return res; }"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader','--disk-cache-dir=/tmp/hlc'])
    pg = b.new_page(viewport={'width':960,'height':1707})
    pg.goto('http://127.0.0.1:40235/index.html?p=50&v=r2s', timeout=120000); pg.wait_for_timeout(8000)
    print(json.dumps(pg.evaluate(JS), ensure_ascii=False, indent=1)); b.close()
