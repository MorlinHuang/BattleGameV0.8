"""不限速跑一次，CPU profile 前 5 秒：脚本执行的 2.4 秒花在哪（按函数自耗时 + 所在文件行）"""
import asyncio, json, collections
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--enable-unsafe-swiftshader'])
        ctx = await b.new_context(viewport={'width': 540, 'height': 960}); pg = await ctx.new_page()
        cdp = await ctx.new_cdp_session(pg)
        await cdp.send('Profiler.enable'); await cdp.send('Profiler.setSamplingInterval', {'interval': 200}); await cdp.send('Profiler.start')
        await pg.goto('http://1.14.252.30:40235/index.html', wait_until='commit')
        await asyncio.sleep(5)
        prof = (await cdp.send('Profiler.stop'))['profile']
        nodes = {n['id']: n for n in prof['nodes']}; dt = collections.Counter()
        for sid, d in zip(prof['samples'], prof['timeDeltas']): dt[sid] += d
        by = collections.Counter(); byfile = collections.Counter()
        for i, t in dt.items():
            cf = nodes[i]['callFrame']; u = cf['url'].split('/')[-1] or cf['functionName'] or '(native)'
            by[f"{u}:{cf['lineNumber'] + 1} {cf['functionName'] or '(top)'}"] += t / 1000; byfile[u] += t / 1000
        print('按文件 ms', [(k, round(v)) for k, v in byfile.most_common(12)])
        for k, v in by.most_common(15): print(f'  {v:7.0f} ms  {k}')
        await b.close()
asyncio.run(main())
