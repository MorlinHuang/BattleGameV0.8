"""离场冲突扫描（修5）：胶片模式下每格记 帧名 + 阶段（trio.js phase()），数「离场阶段却画着出手帧」的格数，验收要求 0。
用法（桌面里跑）：python3 exitscan.py <页面地址> <buddy|bestie> <组号,逗号分隔> <ammoskip,逗号分隔> <ammoms> <每个组合拍几次>  > out.json"""
import asyncio, json, sys
from playwright.async_api import async_playwright
base, side, grps, skips, ms, reps = sys.argv[1], sys.argv[2], sys.argv[3].split(','), [float(x) for x in sys.argv[4].split(',')], sys.argv[5], int(sys.argv[6])
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader'])
        pg = await br.new_page(viewport={'width': 1200, 'height': 900})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('response', lambda r: errs.append(f'{r.status} {r.url}') if r.status >= 400 else None)
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        out = []
        for grp, s, _ in [(g, s, k) for g in grps for s in skips for k in range(reps)]:
            await pg.goto(f'{base}?zoom=1&auto=0&ammostrip=12&ammoms={ms}&ammosc=0.2&noshake=1&ammogift={side}&{side}={grp}&ammoskip={s:.2f}')
            try: await pg.wait_for_function('window.trioFaces && window.trioFaces.length >= 12', timeout=60000)
            except Exception as e: errs.append(f'timeout {side}{grp} skip {s}'); continue
            tf = await pg.evaluate('window.trioFrames'); fa = await pg.evaluate('window.trioFaces.map(f => f.ph)')
            clipset = await pg.evaluate('''(() => { const r = {}; for (const a of [...BuddyTrio.acts, ...BestieTrio.acts]) { const c = a.cfg, A = c.atk || {};
                 if (!A.seq) continue; const ex = [].concat(c.exit ? c.exit.frame : []), set = new Set(A.seq.flatMap(q => [].concat(q[0])));
                 ex.forEach(x => set.delete(x)); set.delete(c.idle && c.idle.frame); r[c.id] = [...set]; } return r; })()''')
            out.append({'grp': grp, 'skip': round(s, 2), 'tf': tf, 'ph': fa, 'clip': clipset})
        print(json.dumps({'errors': errs[:5], 'runs': out}, ensure_ascii=False))
        await br.close()
asyncio.run(main())
