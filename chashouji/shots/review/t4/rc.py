import json,time
from playwright.sync_api import sync_playwright
INIT=open('/tmp/rv/lab_init.js').read()
JS=r"""()=>{ const c=document.createElement('canvas'); c.width=960;c.height=1707; const x=c.getContext('2d'); const out=[];
 Bestie.reset();Truth.reset();Particles.clear(); Truth.summon();
 const cen=()=>{ x.clearRect(0,0,960,1707); Truth.items()[0].draw(x); const d=x.getImageData(0,0,960,1707).data; let n=0,sy=0; for(let i=3;i<d.length;i+=16) if(d[i]>40){n++; sy+=(i>>2)/960|0;} return n?sy/n:null; };
 for(let f=0;f<60*5;f++){ Truth.update(1/60); const b=Truth.peek()[0]; if(!b) break; if (Math.abs(b.t-(0.55+2.8+0.2))<0.009) { Truth.summon(); out.push('RECALL'); }
   if (b.t>3.0 && b.t<4.6) out.push([+b.t.toFixed(3), +cen().toFixed(1)]); }
 return out; }"""
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader','--disk-cache-dir=/tmp/hlc'])
    pg=b.new_page(viewport={'width':960,'height':1707}); pg.add_init_script(INIT)
    pg.goto('http://127.0.0.1:40235/index.html?p=50&auto=0&v=t4rc',timeout=120000)
    for i in range(600):
        if pg.evaluate('window.__q.length')>0: break
        time.sleep(0.2)
    r=pg.evaluate(JS); print(json.dumps(r)); b.close()
