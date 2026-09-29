// Usage: node shot.js <html file> <out png> [scale]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [html, out, scale] = process.argv.slice(2);
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const c = await b.newContext({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: parseFloat(scale || '1') });
  const p = await c.newPage();
  await p.goto('file://' + path.resolve(html));
  await p.evaluate(() => document.body.offsetHeight);          // force layout so font requests start
  await p.evaluate(() => document.fonts.ready);
  await p.waitForFunction(() => document.fonts.status === 'loaded' && ![...document.fonts].some(f => f.status === 'loading'), null, { timeout: 15000 }).catch(() => {});
  await p.waitForTimeout(500);
  // report overflow so we can catch layouts that don't fit
  const m = await p.evaluate(() => { const card = document.querySelector('.card'); return { scrollH: document.documentElement.scrollHeight, cardH: card.scrollHeight, foot: document.querySelector('.foot').getBoundingClientRect().bottom, panel: [...document.querySelectorAll('.panel')].pop().getBoundingClientRect().bottom }; });
  await p.screenshot({ path: out, type: 'png' });
  console.log(JSON.stringify(m));
  await b.close();
})();
