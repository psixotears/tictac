const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const langs = (process.argv[2] || 'www,ru').split(',');
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--proxy-server=' + process.env.HTTPS_PROXY, '--ignore-certificate-errors-spki-list=' + process.env.CCR_SPKI] });
  const c = await b.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36', viewport: { width: 1400, height: 5000 } });
  for (const lang of langs) {
    const u = `https://${lang}.wowhead.com/forever/pets`;
    const p = await c.newPage();
    try { await p.goto(u, { waitUntil: 'networkidle', timeout: 90000 }); } catch (e) { console.log('WARN goto', lang, e.message.split('\n')[0]); }
    let lv = null;
    for (let i = 0; i < 20; i++) {
      lv = await p.evaluate(() => {
        const res = {};
        for (const k in (window.WH && WH.Listview && WH.Listview.instances) || {}) { const l = WH.Listview.instances[k]; res[k] = (l.data || []).map(r => { const o = {}; for (const kk in r) if (!kk.startsWith('__') && kk !== 'envChange') o[kk] = r[kk]; return o; }); }
        const g = {};
        try { for (const t of [3, 6, 13]) { const d = WH.Gatherer && WH.Gatherer.data && WH.Gatherer.data[t]; if (d) g[t] = d; } } catch (e) {}
        return { res, g, title: document.title, html: document.documentElement.outerHTML };
      });
      if (Object.values(lv.res).some(a => a.length)) break;
      await p.waitForTimeout(1500);
    }
    fs.writeFileSync(`raw/pets/pets_${lang}.html`, lv.html);
    delete lv.html;
    fs.writeFileSync(`data/pets_${lang}.json`, JSON.stringify(lv));
    console.log(lang, lv.title, Object.entries(lv.res).map(([k, v]) => k + ':' + v.length).join(' '), 'gatherer', Object.entries(lv.g).map(([k, v]) => k + ':' + Object.keys(v).length).join(' '));
    await p.close();
  }
  await b.close();
})();
