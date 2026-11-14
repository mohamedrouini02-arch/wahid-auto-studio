// Render the graphics as transparent PNGs, one per frame:  node overlay.js out_dir [workers] [from] [to]
// out_dir/f00000.png is what goes in front of the speaker, out_dir/b00000.png what goes behind him (only where there is any).
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => {
  const out = process.argv[2], K = parseInt(process.argv[3] || '4');
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const open = async () => { const p = await b.newPage({ viewport: { width: 1080, height: 1920 } }); p.on('pageerror', e => { console.log('PAGE ERROR', e.message); process.exit(1); });
    await p.goto('file://' + path.join(__dirname, 'overlay.html')); await p.evaluate(() => document.fonts.ready); return p; };
  const p0 = await open(); const info = await p0.evaluate(() => window.info());
  fs.writeFileSync(path.join(out, 'info.json'), JSON.stringify(info));
  const N = Math.round(info.duration * info.fps), from = parseInt(process.argv[4] || '0'), to = Math.min(N, parseInt(process.argv[5] || N));
  const isBehind = t => info.behind.some(([a, c]) => t >= a - 0.001 && t < c);
  let next = from, done = 0;
  const work = async p => { for (;;) { const i = next++; if (i >= to) return; const t = i / info.fps, n = String(i).padStart(5, '0');
      await p.evaluate(t => window.seek(t), t);
      await p.evaluate(() => window.layer('front')); await p.screenshot({ path: `${out}/f${n}.png`, omitBackground: true });
      if (isBehind(t)) { await p.evaluate(() => window.layer('behind')); await p.screenshot({ path: `${out}/b${n}.png`, omitBackground: true }); }
      if (++done % 300 === 0) console.log('overlay', done, '/', to - from); } };
  await Promise.all([work(p0), ...(await Promise.all(Array.from({ length: K - 1 }, open))).map(work)]);
  console.log('overlay done', done); await b.close();
})();
