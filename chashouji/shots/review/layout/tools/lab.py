# 构图实验：只在本会话里改配置（TRUTH/MIST 对象、init 参数、items 覆盖），不动任何项目文件。
# 输出：整帧 PNG + 每个帮手身体的可见率（被主角挡掉多少）。
import json, sys, base64, time
from playwright.sync_api import sync_playwright
cfg = json.load(open(sys.argv[1]))
INIT = open('/tmp/rv/lab_init.js').read()
res = {}
with sync_playwright() as p:
    br = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True,
        args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader','--disk-cache-dir=/tmp/hlc'])
    for run in cfg['runs']:
        pg = br.new_page(viewport={'width':960,'height':1707})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type=='error' else None)
        pg.add_init_script(INIT)
        pg.goto('http://127.0.0.1:40235/index.html?' + run['q'] + '&auto=0&v=lab', timeout=120000)
        for i in range(600):
            if pg.evaluate('window.__q.length') > 0: break
            time.sleep(0.2)
        pg.evaluate('window.__now = performance.now()')
        for _ in range(30): pg.evaluate('window.__step(16.667)')
        pg.evaluate(cfg.get('setup','') + ';' + run.get('setup',''))
        vis = []
        for tr in range(run.get('trials', 1)):
            pg.evaluate('window.__hitsB=0;Bestie.reset();Truth.reset();Buddy.reset();Particles.clear();' + ('window.__dbg=1;' if run.get('dbg') else '') + run['act'])
            n = int(run.get('t', 1600) / 16.667)
            pg.evaluate(f'for(let i=0;i<{n};i++) window.__step(16.667)')
            vis += pg.evaluate('window.__vis()')
            if tr == 0:
                d0 = pg.evaluate('window.__grab()')
        if run.get('dbg'):
            for k,m in enumerate(pg.evaluate('window.__masks||[]')): open(f"/tmp/rv/lab_{run['name']}_m{k}.png",'wb').write(base64.b64decode(m.split(',')[1]))
        d = d0
        open(f"/tmp/rv/lab_{run['name']}.png", 'wb').write(base64.b64decode(d.split(',')[1]))
        res[run['name']] = {'vis': vis, 'errs': errs}
        agg = {}
        for v in vis: k = v['who'][0]; agg.setdefault(k, []).append(v['vis']); agg.setdefault(k+'head', []).append(v['head']); agg.setdefault(k+'h', []).append(v['bbox'][3]-v['bbox'][1])
        hb = pg.evaluate('window.__hitsB||0'); agg['hitsB']=[hb,hb,hb]
        print(run['name'], {k: [round(min(a),2), round(sum(a)/len(a),2), round(max(a),2)] for k, a in agg.items()}, errs[:3], flush=True)
        pg.close()
    br.close()
json.dump(res, open('/tmp/rv/lab_res_%s.json' % cfg.get('tag','x'), 'w'))
