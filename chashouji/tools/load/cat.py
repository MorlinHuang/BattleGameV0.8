import json, sys, collections, re
def cat(u):
    u = u.split('?')[0]
    if u.endswith(('.js', '.html')) or u == '': return 'A 页面+脚本'
    if u.startswith('assets/world/pose_'): return 'B 主角姿势图 pose_*'
    if re.match(r'assets/world/v15/room\d', u) or u.startswith('assets/world/v15/rooms') or u == 'assets/world/world.json': return 'B 长卷背景 room + world.json'
    if u.startswith('assets/world/v15/fx') or u.startswith('assets/world/v15/anim/') and u.endswith('.json'): return 'C 背景光效 fx/'
    if u.startswith('assets/world/v15/anim'): return 'C 背景动区视频 mp4'
    if u.startswith('assets/ui/av_'): return 'B HUD 头像'
    if u.startswith('assets/ui/win_'): return 'D 结算图 win_*'
    if u.startswith('assets/video/'): return 'D 档4出场视频 webm'
    if u.startswith('assets/trio/'): return 'D 档3三人组 60 人'
    if u.startswith('assets/items/'): return 'D 飞行物品/道具图集 items'
    if u.startswith('assets/fx/'): return 'D 命中粒子 fx'
    if u.startswith('assets/world/'): return 'D 档4 其他 world/*'
    return 'E ' + u[:40]
d = json.load(open(sys.argv[1])); t0 = d['t0']; fr = d['marks']['frame']
g = collections.defaultdict(lambda: [0, 0, 0, 1e9, 0])
for r in d['req']:
    k = cat(r['url']); x = g[k]; x[0] += 1; x[1] += r.get('rx', 0); x[2] += r.get('bytes') or 0
    x[3] = min(x[3], (r['start'] - t0) * 1000); x[4] = max(x[4], ((r.get('end') or r['start']) - t0) * 1000)
print(f"| 类别 | 请求数 | 实收 MB | 开始 s | 最后完成 s |")
for k in sorted(g):
    n, rx, b, s, e = g[k]; print(f"| {k} | {n} | {rx/1e6:.2f} | {s/1000:.1f} | {e/1000:.1f} |")
print('合计', len(d['req']), round(sum(v[1] for v in g.values())/1e6, 2), '首帧', round(fr))
