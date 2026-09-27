import json
from playwright.sync_api import sync_playwright
JS = r"""() => {
 const res = {};
 const snap = () => [...Bestie.peek().map(b=>'B'+b.skin), ...Truth.peek().map(b=>'T'+b.skin)].sort().join(',');
 const reset = () => { Bestie.reset(); Truth.reset(); Buddy.reset(); Ammo.clear(); };
 for (const n of [1,2,3,4,5]) { const c = {}; let dup=0, maxN=0;
   for (let i=0;i<2000;i++){ reset(); for(let j=0;j<n;j++) Bestie.summon(); const k=snap(); c[k]=(c[k]||0)+1;
     const sk=Bestie.peek().map(b=>b.skin); if (new Set(sk).size!==sk.length) dup++; maxN=Math.max(maxN,sk.length); }
   res['bestie'+n] = {kinds:Object.keys(c).length, dup, maxN, sample:Object.entries(c).slice(0,8)}; }
 // skin 越界
 try { reset(); Bestie.summon(9); Bestie.summon(-4); Truth.summon(7); res.skinClamp = snap(); } catch(e) { res.skinClamp='ERR '+e; }
 // R2 路由：giveGift
 const route = (key) => { reset(); const before = {q: Ammo.count ? Ammo.count() : null}; giveGift(+1, key); return {people: snap(), ammo: (typeof Ammo.peek==='function')? 'peek' : null}; };
 res.routeBoom = []; for (let i=0;i<5;i++) res.routeBoom.push(route('boom').people);
 res.routeMic = route('mic').people; res.routeDrop = route('drop').people;
 // T1 力度
 const hits=[]; const I0 = impact; impact = function(side,y,power,recipe,x){ hits.push([side, power, recipe===RECIPE.truth?'truth':recipe===RECIPE.pepper?'pepper':'?']); return I0.apply(this, arguments); };
 reset(); giveGift(+1,'drop'); for (let i=0;i<60*3.8;i++) { Truth.update(1/60); }
 impact = I0; res.truthHits = {n:hits.length, first: hits.slice(0,4), powers:[...new Set(hits.map(h=>h[1]))]};
 // T3 续时间 / 召回
 reset(); Truth.summon(); for (let i=0;i<60;i++) Truth.update(1/60);
 const b1 = Truth.peek()[0], s0=b1.spray, t0=b1.t; Truth.summon(); res.extend = {spray:[s0, Truth.peek()[0].spray], n: Truth.peek().length, t:[t0, Truth.peek()[0].t]};
 reset(); Truth.summon(); for (let i=0;i<Math.round((0.55+2.8+0.2)*60);i++) Truth.update(1/60);
 const t2 = Truth.peek()[0].t; Truth.summon(); res.recall = {t: [t2, Truth.peek()[0].t], n: Truth.peek().length};
 reset();
 res.gift = GIFT.truth; res.itemL = ITEM_OF.L; res.btn = [...document.querySelectorAll('button[data-shop]')].map(b=>b.textContent);
 return res; }"""
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader','--disk-cache-dir=/tmp/hlc'])
    pg = b.new_page(viewport={'width':960,'height':1707}); errs=[]
    pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.type+': '+m.text) if m.type in('error','warning') else None)
    pg.goto('http://127.0.0.1:40235/index.html?p=50&auto=0&v=t4s1', timeout=120000); pg.wait_for_timeout(8000)
    print(json.dumps(pg.evaluate(JS), ensure_ascii=False, indent=1)); print('errs', errs); b.close()
