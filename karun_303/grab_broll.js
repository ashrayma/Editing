// Real screen recordings + screenshots for B-roll.
//   node grab_broll.js  ->  assets/broll/ss_*.png (2x stills) and assets/broll/rec_*.webm (1920x1080 recordings)
// Each recording: page loads, a highlight box draws around the line that matters, then a slow smooth scroll.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const OUT = path.join(__dirname, 'assets', 'broll');
fs.mkdirSync(OUT, { recursive: true });

const HILITE = `(sel) => {
  const el = sel(); if (!el) return false;
  el.scrollIntoView({block: 'center'});
  el.style.transition = 'background 0.6s, box-shadow 0.6s';
  setTimeout(() => { el.style.background = 'rgba(254,222,92,0.55)'; el.style.boxShadow = '0 0 0 4px #FEDE5C'; }, 900);
  return true; }`;

async function record(b, name, url, fn) {
  const tmp = path.join(OUT, 'tmp_' + name);
  const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1,
    recordVideo: { dir: tmp, size: { width: 1920, height: 1080 } } });
  const p = await ctx.newPage();
  await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.addStyleTag({ content: 'html{scroll-behavior:auto} body{zoom:1.35}' });
  await p.waitForTimeout(1500);
  await fn(p);
  const v = p.video();
  await ctx.close();
  fs.renameSync(await v.path(), path.join(OUT, `rec_${name}.webm`));
  fs.rmSync(tmp, { recursive: true, force: true });
}

async function glide(p, px, steps) {
  for (let i = 0; i < steps; i++) { await p.mouse.wheel(0, px); await p.waitForTimeout(33); }
}

(async () => {
  const b = await chromium.launch();

  // 1. Triple centuries list: glide to India's rows, highlight Karun's 303*
  await record(b, 'triple_list', 'https://en.wikipedia.org/wiki/List_of_Test_cricket_triple_centuries', async (p) => {
    await glide(p, 10, 60);
    await p.evaluate(`(${HILITE})(() => [...document.querySelectorAll('tr')].find(r => /Karun Nair/.test(r.textContent)))`);
    await p.waitForTimeout(2500);
    await glide(p, 3, 60);
  });

  // 2. Karun Nair article: top, then glide to the Test career paragraph and highlight "dropped"
  await record(b, 'karun_wiki', 'https://en.wikipedia.org/wiki/Karun_Nair', async (p) => {
    await p.waitForTimeout(1200);
    await glide(p, 8, 70);
    await p.evaluate(`(${HILITE})(() => [...document.querySelectorAll('p')].find(e => /he was dropped from the side/.test(e.textContent)))`);
    await p.waitForTimeout(2800);
    await glide(p, 3, 50);
  });

  // Stills (retina)
  const ctx = await b.newContext({ viewport: { width: 1500, height: 900 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  await p.goto('https://en.wikipedia.org/wiki/Karun_Nair', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForTimeout(1500);
  const box = await p.$('table.infobox');
  if (box) await box.screenshot({ path: path.join(OUT, 'ss_karun_infobox.png') });
  await p.goto('https://en.wikipedia.org/wiki/List_of_Test_cricket_triple_centuries', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForTimeout(1500);
  const row = await p.evaluateHandle(() => [...document.querySelectorAll('tr')].find(r => /Karun Nair/.test(r.textContent)));
  const el = row.asElement();
  if (el) {
    await el.evaluate(r => { r.scrollIntoView({ block: 'center' }); r.style.background = 'rgba(254,222,92,0.55)'; });
    await p.waitForTimeout(400);
    await p.screenshot({ path: path.join(OUT, 'ss_triple_list.png') });
  }
  await ctx.close();
  await b.close();
  console.log('done');
})();
