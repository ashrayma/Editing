// Sample the composition every 0.1 s: on-screen boxes of visible faces (from the face markers), every movable
// type element (.avoid: exact text extent, not the full-width box) and the logo.   node measure.js -> out/measure.json
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + path.join(__dirname, 'hf', 'index.html'));
  await p.waitForTimeout(800);
  const total = await p.evaluate(() => +document.getElementById('root').dataset.duration);
  const samples = [];
  for (let t = 0; t < total; t += 0.1) {
    samples.push(await p.evaluate((t) => {
      window.__timelines.root.seek(t, false);
      document.querySelectorAll('.clip').forEach((el) => {
        const s = +el.dataset.start, d = +el.dataset.duration;
        el.style.visibility = (t >= s && t < s + d) ? 'visible' : 'hidden';
      });
      const alpha = (el) => { let a = 1; for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
        const cs = getComputedStyle(e); if (cs.visibility === 'hidden' || cs.display === 'none') return 0; a *= +cs.opacity; } return a; };
      const R = (r) => [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
      const union = (rs) => { rs = rs.filter((r) => r.width > 1 && r.height > 1); if (!rs.length) return null;
        const x0 = Math.min(...rs.map((r) => r.left)), y0 = Math.min(...rs.map((r) => r.top));
        const x1 = Math.max(...rs.map((r) => r.right)), y1 = Math.max(...rs.map((r) => r.bottom));
        return { left: x0, top: y0, width: x1 - x0, height: y1 - y0 }; };
      const z = (el) => +(el.closest('[style*="z-index"]') || el).style.zIndex || 0;
      // topmost opaque full-frame layer: anything below it is covered
      let topFull = 0;
      document.querySelectorAll('.layer.full').forEach((l) => { if (alpha(l) > 0.6) topFull = Math.max(topFull, z(l)); });
      const faces = [];
      document.querySelectorAll('.face').forEach((f) => {
        const l = f.closest('.layer'); if (!l || alpha(f) < 0.3 || z(l) < topFull) return;
        // a layer still sliding into frame: its faces sweep past, they don't sit under the type
        const mx = new DOMMatrix(getComputedStyle(l).transform);
        if (Math.abs(mx.m41) > 40 || Math.abs(mx.m42) > 40) return;
        const r = f.getBoundingClientRect();
        if (r.right > 0 && r.left < 1080 && r.bottom > 0 && r.top < 1920) faces.push(R(r));
      });
      const els = {};
      document.querySelectorAll('.avoid').forEach((el) => {
        if (alpha(el) < 0.3 || z(el) < topFull) return;  // faded, or covered by a later full-frame layer
        let rs;
        if (el.querySelector('.dcol')) rs = [...el.querySelectorAll('.dcol,.olab,.digits > span:not(.dcol)')].map((e) => e.getBoundingClientRect());
        else if (el.classList.contains('cap')) rs = [el.querySelector('span').getBoundingClientRect()];
        else if (el.classList.contains('tag') || el.classList.contains('chip')) rs = [el.getBoundingClientRect()];
        else { rs = []; const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
          for (let n; (n = w.nextNode());) { if (!n.textContent.trim()) continue; const rg = document.createRange(); rg.selectNodeContents(n); rs.push(...rg.getClientRects()); } }
        const u = union(rs); if (!u) return;
        const cs = getComputedStyle(el);
        els[el.id] = { r: R(u), top: parseFloat(cs.top), left: parseFloat(cs.left) || 0, z: z(el) };
      });
      const br = document.querySelector('#brand img');
      return { t: +t.toFixed(2), faces, els, brand: alpha(br) > 0.3 ? R(br.getBoundingClientRect()) : null };
    }, t));
  }
  fs.writeFileSync(path.join(__dirname, 'out', 'measure.json'), JSON.stringify({ total, samples }));
  console.log('samples', samples.length);
  await b.close();
})();
