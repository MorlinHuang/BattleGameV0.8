import json,time
from playwright.sync_api import sync_playwright
INIT=open('/tmp/rv/lab_init.js').read()
JS=r"""(q)=>{ const out=[]; const c=document.createElement('canvas'); c.width=960;c.height=1707; const x=c.getContext('2d');
 Bestie.reset();Truth.reset();Particles.clear(); giveGift(+1,'drop');
 for(let f=0;f<=90;f++){ const t=Truth.peek()[0].t; x.clearRect(0,0,960,1707); for(const it of Truth.items()) it.draw(x);
  const d=x.getImageData(0,0,960,1707).data; let A=0,B=0,miny=1e9,maxy=-1;
  for(let i=3;i<d.length;i+=4) if(d[i]>40){const py=(i>>2)/960|0; if(py<miny)miny=py; if(py>maxy)maxy=py;}
  const hy=miny+(maxy-miny)*0.3; let HA=0,HB=0;
  const u=Math.min(1,t/0.25), e=1-Math.pow(1-u,3), bw=960*e;
  for(let i=3;i<d.length;i+=4) if(d[i]>40){A++; const p=i>>2, px=p%960, py=p/960|0; const inb= py>=274&&py<=386&&px<bw; if(inb)B++; if(py<=hy){HA++; if(inb)HB++;}}
  const alpha = t<1.1?1:Math.max(0,1-(t-1.1)/0.3);
  out.push([+t.toFixed(3), A, A?+(B/A).toFixed(3):0, HA?+(HB/HA).toFixed(3):0, alpha, miny, maxy]); window.__step(16.667);}
 return out;}"""
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader','--disk-cache-dir=/tmp/hlc'])
    for q in ['p=50','p=95']:
        pg=b.new_page(viewport={'width':960,'height':1707}); pg.add_init_script(INIT)
        pg.goto('http://127.0.0.1:40235/index.html?'+q+'&auto=0&v=t4ov',timeout=120000)
        for i in range(600):
            if pg.evaluate('window.__q.length')>0: break
            time.sleep(0.2)
        pg.evaluate('window.__now=performance.now()')
        for _ in range(30): pg.evaluate('window.__step(16.667)')
        r=pg.evaluate(JS,q); print(q); [print(row) for row in r if row[2]>0 or row[0]<0.05]
    b.close()
