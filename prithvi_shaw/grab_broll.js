// Real screen recordings + screenshots of Prithvi Shaw's public record (Wikipedia), for B-roll.
//   node grab_broll.js  ->  assets/broll/rec_*.webm (1920x1080) and ss_*.png (2x)
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const OUT = path.join(__dirname, 'assets', 'broll');
fs.mkdirSync(OUT, { recursive: true });

const HILITE = (re) => `(() => {
  const el = [...document.querySelectorAll('p, tr, li')].find(e => ${re}.test(e.textContent));
  if (!el) return false;
  el.scrollIntoView({block: 'center'});
  el.style.transition = 'background 0.6s, box-shadow 0.6s';
  setTimeout(() => { el.style.background = 'rgba(254,222,92,0.55)'; el.style.boxShadow = '0 0 0 4px #FEDE5C'; }, 900);
  return true; })()`;

async function glide(p, px, steps) { for (let i = 0; i < steps; i++) { await p.mouse.wheel(0, px); await p.waitForTimeout(33); } }

async function record(b, name, url, fn) {
  const tmp = path.join(OUT, 'tmp_' + name);
  const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 }, recordVideo: { dir: tmp, size: { width: 1920, height: 1080 } } });
  const p = await ctx.newPage();
  await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.addStyleTag({ content: 'body{zoom:1.4}' });
  await p.waitForTimeout(1500);
  await fn(p);
  const v = p.video();
  await ctx.close();
  fs.renameSync(await v.path(), path.join(OUT, `rec_${name}.webm`));
  fs.rmSync(tmp, { recursive: true, force: true });
}

(async () => {
  const b = await chromium.launch();
  // 1. Shaw's page: the 546-run Harris Shield record
  await record(b, 'shaw_546', 'https://en.wikipedia.org/wiki/Prithvi_Shaw', async (p) => {
    await glide(p, 9, 50);
    await p.evaluate(HILITE('/546 runs from 330 balls/'));
    await p.waitForTimeout(2800); await glide(p, 3, 50);
  });
  // 2. 2020-21 tour page: 36 all out
  await record(b, 'adelaide_36', 'https://en.wikipedia.org/wiki/Indian_cricket_team_in_Australia_in_2020%E2%80%9321', async (p) => {
    await glide(p, 9, 40);
    await p.evaluate(HILITE('/36/'));
    await p.waitForTimeout(2800); await glide(p, 3, 50);
  });
  // 3. Shaw's page: the Maharashtra fresh start
  await record(b, 'shaw_maharashtra', 'https://en.wikipedia.org/wiki/Prithvi_Shaw', async (p) => {
    await p.evaluate(HILITE('/fresh start from scratch/'));
    await p.waitForTimeout(2800); await glide(p, 3, 50);
  });
  // Stills
  const ctx = await b.newContext({ viewport: { width: 1500, height: 900 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  await p.goto('https://en.wikipedia.org/wiki/Prithvi_Shaw', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForTimeout(1500);
  const box = await p.$('table.infobox'); if (box) await box.screenshot({ path: path.join(OUT, 'ss_shaw_infobox.png') });
  await p.evaluate(HILITE('/227\\* off 152/')); await p.waitForTimeout(1300);
  await p.screenshot({ path: path.join(OUT, 'ss_shaw_227.png') });
  await ctx.close(); await b.close(); console.log('done');
})();
