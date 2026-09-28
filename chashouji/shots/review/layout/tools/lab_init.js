window.__q=[]; window.__now=0;
window.requestAnimationFrame = (cb)=>{ window.__q.push(cb); return window.__q.length; };
window.__step = (ms)=>{ window.__now += ms; const q=window.__q; window.__q=[]; for (const cb of q) cb(window.__now); };
window.__grab = ()=>{ const c=document.createElement('canvas'); c.width=960; c.height=1707; const x=c.getContext('2d');
  for (const id of ['bg','ch','fx']) x.drawImage(document.getElementById(id),0,0); return c.toDataURL('image/png'); };
/* 可见率：同一时刻重画三次（__step(0) 不推进时间）：①帮手身体全部挪到主角之后画（=全身轮廓）②正常 ③不画帮手。
   全身 = ①与③ 的差异像素；可见 = ②与③ 的差异像素。按每个人分别算（一次只留一个人的身体）。 */
window.__vis = () => {
  const ch = document.getElementById('ch'), W = ch.width, H = ch.height;
  const snap = () => ch.getContext('2d').getImageData(0, 0, W, H).data;
  const C = [['B', Bestie], ['T', Truth]], out = []; const R0 = Math.random; Math.random = () => 0.5;
  const orig = C.map(([n, c]) => c.items);
  const bodiesOf = (c) => { const ss = new Set(c.peek().map(b => b.s)); return (it) => ss.has(it.s); };
  const people = []; C.forEach(([n, c], ci) => c.peek().forEach(b => people.push([n, ci, b])));
  for (const [n, ci, b] of people) {
    const setMode = (mode) => C.forEach(([nn, c], cj) => {
      c.items = () => orig[cj].call(c).filter(it => cj === ci && it.s === b.s && mode !== 'none').map(it => mode === 'front' ? { ...it, front: true } : it);
    });
    setMode('none'); window.__step(0); const z = snap();
    setMode('front'); window.__step(0); const f = snap();
    setMode('normal'); window.__step(0); const v = snap();
    let F = 0, V = 0, minx = 1e9, maxx = -1, miny = 1e9, maxy = -1, cut = 0;
    for (let i = 0; i < z.length; i += 4) {
      const df = Math.abs(f[i]-z[i]) + Math.abs(f[i+1]-z[i+1]) + Math.abs(f[i+2]-z[i+2]) + Math.abs(f[i+3]-z[i+3]);
      if (df > 30) { F++; const px = (i/4) % W, py = (i/4/W)|0; if (px<minx)minx=px; if(px>maxx)maxx=px; if(py<miny)miny=py; if(py>maxy)maxy=py;
        const dv = Math.abs(v[i]-z[i]) + Math.abs(v[i+1]-z[i+1]) + Math.abs(v[i+2]-z[i+2]) + Math.abs(v[i+3]-z[i+3]);
        if (dv > 30) V++; }
    }
    if (window.__dbg) { const c=document.createElement('canvas'); c.width=W; c.height=H; const x=c.getContext('2d'); const im=x.createImageData(W,H); for (let i=0;i<z.length;i+=4){ const df=Math.abs(f[i]-z[i])+Math.abs(f[i+1]-z[i+1])+Math.abs(f[i+2]-z[i+2])+Math.abs(f[i+3]-z[i+3]); const dv=Math.abs(v[i]-z[i])+Math.abs(v[i+1]-z[i+1])+Math.abs(v[i+2]-z[i+2])+Math.abs(v[i+3]-z[i+3]); im.data[i]=df>30?255:0; im.data[i+1]=dv>30?255:0; im.data[i+3]=255;} x.putImageData(im,0,0); window.__masks=(window.__masks||[]); window.__masks.push(c.toDataURL()); }
    let HF = 0, HV = 0; const hy = miny + (maxy - miny) * 0.2;
    for (let i = 0; i < z.length; i += 4) { const py = (i/4/W)|0; if (py > hy) break;
      const df = Math.abs(f[i]-z[i]) + Math.abs(f[i+1]-z[i+1]) + Math.abs(f[i+2]-z[i+2]) + Math.abs(f[i+3]-z[i+3]);
      if (df > 30) { HF++; const dv = Math.abs(v[i]-z[i]) + Math.abs(v[i+1]-z[i+1]) + Math.abs(v[i+2]-z[i+2]) + Math.abs(v[i+3]-z[i+3]); if (dv > 30) HV++; } }
    out.push({ head: +(HV / Math.max(1, HF)).toFixed(3), who: n + b.skin, s: +b.s.toFixed(2), t: +b.t.toFixed(2), area: F, vis: +(V / Math.max(1, F)).toFixed(3), bbox: [minx, miny, maxx, maxy] });
  }
  C.forEach(([n, c], cj) => { c.items = orig[cj]; }); window.__step(0); Math.random = R0;
  return out;
};
