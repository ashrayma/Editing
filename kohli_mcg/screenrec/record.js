// Screen recording + screenshot B-roll, captured with the pre-installed Playwright Chromium.
//   node screenrec/record.js  ->  footage/screenrec_match_centre.mp4 (phone, scrolling) + assets/photos/screenshot_drought.png
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');

const HERE = __dirname;
const ROOT = path.join(HERE, '..');

(async () => {
  const browser = await chromium.launch();
  // 1) Screen recording: phone viewport, the page scrolls through the last two overs like a thumb would
  const vidDir = path.join(HERE, 'tmp');
  fs.rmSync(vidDir, { recursive: true, force: true });
  const ctx = await browser.newContext({ viewport: { width: 780, height: 1688 }, deviceScaleFactor: 1,
    recordVideo: { dir: vidDir, size: { width: 780, height: 1688 } } });
  const page = await ctx.newPage();
  await page.goto('file://' + path.join(HERE, 'match_centre.html'));
  await page.waitForTimeout(1200);
  const maxY = await page.evaluate(() => document.documentElement.scrollHeight - innerHeight);
  for (const y of [600, 1040, 1520, 2000, maxY]) {
    await page.evaluate((y) => window.scrollTo({ top: y, behavior: 'smooth' }), Math.min(y, maxY));
    await page.waitForTimeout(1700);
  }
  await page.waitForTimeout(600);
  await ctx.close();
  const webm = fs.readdirSync(vidDir).find((f) => f.endsWith('.webm'));
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', path.join(vidDir, webm), '-vf', 'fps=30',
    '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', path.join(ROOT, 'footage', 'screenrec_match_centre.mp4')]);
  fs.rmSync(vidDir, { recursive: true, force: true });

  // 2) Screenshot: the drought stats page
  const p2 = await browser.newPage({ viewport: { width: 1200, height: 640 }, deviceScaleFactor: 2 });
  await p2.goto('file://' + path.join(HERE, 'drought.html'));
  await p2.screenshot({ path: path.join(ROOT, 'assets', 'photos', 'screenshot_drought.png'), fullPage: true });
  await browser.close();
  console.log('SCREENREC_DONE');
})();
