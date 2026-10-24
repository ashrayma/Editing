// Scripted browser session -> screen recording (webm) + hi-res screenshot.
// usage: node tools/record_screen.cjs <out_dir>
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const out = path.resolve(process.argv[2] || 'film/assets/broll');
  const page_url = 'file://' + path.resolve(__dirname, 'innings_explorer.html');
  const size = { width: 650, height: 560 };
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: size, recordVideo: { dir: out, size } });
  const page = await ctx.newPage();
  const wait = ms => page.waitForTimeout(ms);
  await page.goto(page_url);
  await page.mouse.move(560, 420);
  await wait(250);
  const box = await page.locator('#search').boundingBox();
  await page.mouse.move(box.x + 120, box.y + box.height / 2, { steps: 12 });
  await page.mouse.down(); await page.mouse.up();
  for (const ch of 'Sharjah 1998 Sachin') { await page.evaluate(c => typeQuery(c), ch); await wait(30); }
  await wait(120);
  await page.evaluate(() => showResults());
  await wait(350);
  const r1 = await page.locator('#r1').boundingBox();
  await page.mouse.move(r1.x + 260, r1.y + r1.height / 2, { steps: 14 });
  await wait(150);
  await page.mouse.down(); await wait(90); await page.mouse.up();
  await page.locator('#r1').click();
  await wait(350);
  // smooth scroll to the scorecard
  for (let i = 0; i < 34; i++) { await page.evaluate(y => document.getElementById('main').scrollBy(0, y), 9); await wait(16); }
  await wait(2900);
  await page.screenshot({ path: path.join(out, 'explorer_scorecard.png'), scale: 'device' });
  const v = page.video();
  await ctx.close();
  const p = await v.path();
  require('fs').renameSync(p, path.join(out, 'screen_recording.webm'));
  // separate 2x screenshot of the scorecard card for a crisp still
  const ctx2 = await browser.newContext({ viewport: size, deviceScaleFactor: 2 });
  const p2 = await ctx2.newPage();
  await p2.goto(page_url);
  await p2.evaluate(() => { for (const c of 'Sharjah 1998 Sachin') typeQuery(c); showResults(); });
  await p2.locator('#r1').click();
  await p2.waitForTimeout(4200);
  await p2.evaluate(() => document.getElementById('cursor').style.display = 'none');
  await p2.locator('#card').screenshot({ path: path.join(out, 'screenshot_scorecard.png') });
  await browser.close();
  console.log('done', out);
})();
