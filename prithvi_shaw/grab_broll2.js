// Screen recording of the public record of the Feb 2023 incident (Wikipedia, Prithvi Shaw > Personal life).
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const OUT = path.join(__dirname, 'assets', 'broll');
(async () => {
  const b = await chromium.launch();
  const tmp = path.join(OUT, 'tmp_inc');
  const ctx = await b.newContext({ viewport: { width: 1920, height: 1080 }, recordVideo: { dir: tmp, size: { width: 1920, height: 1080 } } });
  const p = await ctx.newPage();
  await p.goto('https://en.wikipedia.org/wiki/Prithvi_Shaw', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.addStyleTag({ content: 'body{zoom:1.4}' });
  await p.waitForTimeout(1200);
  await p.evaluate(() => { const el = [...document.querySelectorAll('p')].find(e => /Sapna Gill/.test(e.textContent));
    el.scrollIntoView({block:'center'}); el.style.transition='background .6s, box-shadow .6s';
    setTimeout(() => { el.style.background='rgba(254,222,92,.55)'; el.style.boxShadow='0 0 0 4px #FEDE5C'; }, 900); });
  await p.waitForTimeout(3200);
  for (let i = 0; i < 40; i++) { await p.mouse.wheel(0, 3); await p.waitForTimeout(33); }
  const v = p.video(); await ctx.close();
  fs.renameSync(await v.path(), path.join(OUT, 'rec_incident.webm')); fs.rmSync(tmp, { recursive: true, force: true });
  await b.close(); console.log('done');
})();
