// Screen-record a real browser session on the record-book page: type a search, switch tabs, scroll, highlight.
//   node record.js  ->  out/screen_*.webm (one per take), out/shot_*.png screenshots
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const OUT = path.join(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });
const url = 'file://' + path.join(__dirname, 'stats.html');
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// A visible cursor (headless Chromium draws none): a dot that follows mouse moves and pulses on click.
const CURSOR = `const c=document.createElement('div');c.style.cssText='position:fixed;z-index:99;width:26px;height:26px;margin:-13px 0 0 -13px;border-radius:50%;background:rgba(255,255,255,.9);box-shadow:0 2px 10px rgba(0,0,0,.6);pointer-events:none;transition:transform .12s;left:-50px;top:-50px';
addEventListener('DOMContentLoaded',()=>document.body.appendChild(c));
addEventListener('mousemove',e=>{c.style.left=e.clientX+'px';c.style.top=e.clientY+'px'});
addEventListener('mousedown',()=>c.style.transform='scale(.7)');addEventListener('mouseup',()=>c.style.transform='scale(1)');`;

async function take(name, fn) {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1,
    recordVideo: { dir: OUT, size: { width: 1280, height: 800 } } });
  await ctx.addInitScript(CURSOR);
  const page = await ctx.newPage();
  await page.goto(url);
  await page.mouse.move(900, 500);
  await wait(400);
  await fn(page);
  const v = page.video();
  await ctx.close();
  await browser.close();
  fs.renameSync(await v.path(), path.join(OUT, `screen_${name}.webm`));
  console.log('recorded', name);
}

async function tab(page, i) {
  const box = await page.locator('.tab').nth(i).boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 25 });
  await wait(150);
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
}

(async () => {
  await take('avg', async (page) => {
    const s = await page.locator('#s').boundingBox();
    await page.mouse.move(s.x + 120, s.y + s.height / 2, { steps: 25 });
    await page.mouse.click(s.x + 120, s.y + s.height / 2);
    await page.evaluate(() => window.typeQ('highest world cup batting average'));
    await wait(500);
    await page.mouse.move(1060, 372, { steps: 30 });
    await page.evaluate(() => window.hl(['a-ab']));
    await page.screenshot({ path: path.join(OUT, 'shot_avg.png') });
    await wait(900);
    await page.evaluate(() => window.hl(['a-ab', 'a-viv']));
    await wait(1400);
  });
  await take('f150', async (page) => {
    await tab(page, 1);
    await wait(500);
    await page.mouse.move(1110, 372, { steps: 30 });
    await page.evaluate(() => window.hl(['f-ab']));
    await page.screenshot({ path: path.join(OUT, 'shot_f150.png') });
    await wait(2200);
  });
})();
