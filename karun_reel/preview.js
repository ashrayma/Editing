// Still frames of the composition at given times, tiled into one contact sheet (layout checks without a full render).
//   node preview.js out/sheet.png 0.5 2 4 ...
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [out, ...times] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + path.join(__dirname, 'hf', 'index.html'));
  await p.waitForTimeout(800);
  const shots = [];
  for (const t of times) {
    await p.evaluate((t) => {
      const tl = window.__timelines.root; tl.seek(+t, false);
      document.querySelectorAll('.clip').forEach((el) => {
        const s = +el.dataset.start, d = +el.dataset.duration;
        el.style.visibility = (+t >= s && +t < s + d) ? 'visible' : 'hidden';
        if (el.tagName === 'VIDEO') { try { el.currentTime = Math.max(0, +t - s); } catch (e) {} }
      });
    }, t);
    await p.waitForTimeout(250);
    shots.push(await p.screenshot({ type: 'png' }));
  }
  // tile with a second page
  const tp = await b.newPage({ viewport: { width: 270 * Math.min(6, shots.length), height: 480 * Math.ceil(shots.length / 6) + 30 * Math.ceil(shots.length / 6) } });
  const imgs = shots.map((s, k) => `<div style="display:inline-block;position:relative;width:270px;height:510px"><img src="data:image/png;base64,${s.toString('base64')}" style="width:270px;height:480px"><div style="font:16px sans-serif;color:#fff">${times[k]}s</div></div>`).join('');
  await tp.setContent(`<body style="margin:0;background:#222;font-size:0">${imgs}</body>`);
  await tp.screenshot({ path: out, fullPage: true });
  await b.close();
})();
