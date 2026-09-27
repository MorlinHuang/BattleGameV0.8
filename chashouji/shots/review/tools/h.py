# 审查用观测脚本：接管 rAF，按固定步长推进真实主循环（live 路径），按时刻抓整帧 + 每帧记 Truth 状态。不改任何项目文件。
import json, sys, base64, time
from playwright.sync_api import sync_playwright
cfg = json.load(open(sys.argv[1]))
INIT = """
window.__q=[]; window.__now=0;
window.requestAnimationFrame = (cb)=>{ window.__q.push(cb); return window.__q.length; };
window.__step = (ms)=>{ window.__now += ms; const q=window.__q; window.__q=[]; for (const cb of q) cb(window.__now); };
window.__grab = ()=>{ const c=document.createElement('canvas'); c.width=960; c.height=1707; const x=c.getContext('2d');
  for (const id of ['bg','ch','fx']) x.drawImage(document.getElementById(id),0,0); return c.toDataURL('image/png'); };
"""
out = cfg['out']; logs = []; cons = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True,
        args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader','--disk-cache-dir=/tmp/hlc'])
    pg = b.new_page(viewport={'width':960,'height':1707}, device_scale_factor=1)
    pg.on('console', lambda m: cons.append(f'{m.type}: {m.text}'))
    pg.on('response', lambda r: cons.append(f'HTTP {r.status} {r.url}') if r.status>=400 else None)
    pg.on('pageerror', lambda e: cons.append(f'PAGEERROR: {e}'))
    pg.add_init_script(INIT)
    pg.goto('http://127.0.0.1:40235/index.html?' + cfg['q'], timeout=120000)
    for i in range(600):
        if pg.evaluate('window.__q.length') > 0: break
        time.sleep(0.2)
    pg.evaluate('window.__now = performance.now()')
    for _ in range(int(cfg.get('pre', 30))): pg.evaluate('window.__step(16.667)')
    if cfg.get('act'): pg.evaluate(cfg['act'])
    dt = cfg.get('dt', 16.667); T = cfg['total']; caps = sorted(cfg.get('caps', [])); ci = 0; t = 0.0
    fn = """() => { const r = []; for (const [nm,C] of [['T',Truth],['B',Bestie]]) for (const b of C.peek())
       r.push({c:nm, back:b.back||0, backT:b.backT||0, av:b.av||0, t:+b.t.toFixed(4), aim:+b.aim.toFixed(4), want:+(b.want??0).toFixed(4), kick:+b.kick.toFixed(3), lean:+b.lean.toFixed(3), ph:b.ph, s:b.s, skin:b.skin, spray:b.spray, m:b.m, tg:b.tg});
       return {r, mist: window.__mist||null, hits: window.__hits||0, splash: window.__spl||0, bob: FX.bob, pn: Particles.count(), p:S.p, pos:S.pos}; }"""
    while t <= T + 1e-6:
        while ci < len(caps) and caps[ci] <= t + 1e-6:
            d = pg.evaluate('window.__grab()'); open(f"{out}_{int(round(caps[ci])):05d}.png",'wb').write(base64.b64decode(d.split(',')[1])); ci += 1
        st = pg.evaluate(fn); st['t'] = round(t, 2); logs.append(st)
        k=str(int(round(t/100))*100)
        if cfg.get('acts') and k in cfg['acts'] and abs(t-int(k))<9: pg.evaluate(cfg['acts'][k])
        pg.evaluate(f'window.__step({dt})'); t += dt
    b.close()
json.dump({'log': logs, 'console': cons}, open(out + '_log.json', 'w'))
print('frames', len(logs), 'console', len(cons)); print('\n'.join(cons[:40]))
