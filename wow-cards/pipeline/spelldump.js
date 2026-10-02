const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const ids = process.argv[2].split(',');
  const lang = process.argv[3] || 'www';
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--proxy-server=' + process.env.HTTPS_PROXY, '--ignore-certificate-errors-spki-list=' + process.env.CCR_SPKI] });
  const c = await b.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36', viewport: { width: 1400, height: 3000 } });
  await c.route('**/*', r => { const u = r.request().url(); if (/wowhead\.com|zamimg\.com/.test(u)) r.continue(); else r.abort(); });
  const out = {};
  for (const id of ids) {
    const p = await c.newPage();
    try { await p.goto(`https://${lang}.wowhead.com/forever/spell=${id}`, { waitUntil: 'domcontentloaded', timeout: 60000 }); } catch (e) { console.log('WARN', id, e.message.split('\n')[0]); }
    let r = null;
    for (let i = 0; i < 10; i++) {
      r = await p.evaluate(() => {
        const tt = document.querySelector('.wowhead-tooltip');
        const qf = document.querySelector('#infobox-contents-0, .infobox');
        return { title: document.title, tooltip: tt ? tt.innerText : null, infobox: qf ? qf.innerText : null };
      });
      if (r.tooltip) break;
      await p.waitForTimeout(1000);
    }
    out[id] = r;
    console.log(id, r.title, '|', (r.tooltip || '').replace(/\n+/g, ' / ').slice(0, 220));
    await p.close();
  }
  fs.writeFileSync(`data/petspells_${lang}.json`, JSON.stringify(out, null, 1));
  await b.close();
})();
