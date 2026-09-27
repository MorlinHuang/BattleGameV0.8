import json,sys
REINIT = """(function(px,py,rows){ TRUTH.rows=[rows];
 Truth.init({ W, ground: () => GROUND + FX.bob, horizon: () => 0, perch: () => [px, GROUND - py],
  target(u){ const f = faceOf('b'); return f && [f[0] - 0.3 * f[2], f[1] + (u * 0.6 - 0.55) * f[2]]; },
  front: () => null, onArrive: (x, y, s) => RECIPE.truth.arrive(x, y, s), onSplash: (x, y) => RECIPE.truth.drip(x, y, -1),
  onHit: (x, y, first) => impact(-1, y, first ? GIFT.bestie.power : 1, RECIPE.truth, x) }); Truth.summon(); })(%s,%s,[%s,%s])"""
n,q,px,py,s=sys.argv[1:6]
json.dump({"q":q+"&auto=0&v=rv8","out":f"/tmp/rv/{n}","act":REINIT%(px,py,s,s),"total":1400,"caps":[1300]},open(f'/tmp/rv/{n}.json','w'))
