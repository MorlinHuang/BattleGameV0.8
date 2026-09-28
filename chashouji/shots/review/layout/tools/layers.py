import json, base64, time
from playwright.sync_api import sync_playwright
INIT = open('/tmp/rv/lab_init.js').read()
P = [('p50','p=50'),('p30','p=30'),('p70','p=70'),('p5','p=5'),('p95','p=95'),('pos20','p=50&pos=20'),('posm20','p=50&pos=-20')]
geo = {}
with sync_playwright() as p:
    br = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True, args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader','--disk-cache-dir=/tmp/hlc'])
    for n, q in P:
        pg = br.new_page(viewport={'width':960,'height':1707}); pg.add_init_script(INIT)
        pg.goto('http://127.0.0.1:40235/index.html?' + q + '&auto=0&v=lay', timeout=120000)
        for i in range(600):
            if pg.evaluate('window.__q.length') > 0: break
            time.sleep(0.2)
        pg.evaluate('window.__now = performance.now(); Bubble.clear && Bubble.clear(); for(let i=0;i<40;i++) window.__step(16.667); Bubble.clear && Bubble.clear(); window.__step(0)')
        r = pg.evaluate("""() => { const g = id => document.getElementById(id).toDataURL('image/png');
            return { bg: g('bg'), ch: g('ch'), fa: faceOf('a'), fb: faceOf('b'), phone: [FX.phoneX, FX.phoneY], frame: FX.frame }; }""")
        for k in ['bg','ch']: open(f'/tmp/rv/L_{n}_{k}.png','wb').write(base64.b64decode(r[k].split(',')[1]))
        geo[n] = {k: r[k] for k in ['fa','fb','phone','frame']}; print(n, geo[n], flush=True); pg.close()
    br.close()
json.dump(geo, open('/tmp/rv/L_geo.json','w'))
