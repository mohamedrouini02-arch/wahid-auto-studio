// Stills of the graphics over a frame of the footage: node preview.js out_dir bg.jpg fg.png t1 t2 ...
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const [out, bg, fg, ...ts] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.log('PAGE ERROR', e.message));
  await p.goto('file://' + path.join(__dirname, 'overlay.html'));
  await p.evaluate(([bg, fg]) => {
    const mk = (src, z) => { const d = document.createElement('div'); d.style.cssText = `position:absolute;inset:0;overflow:hidden;z-index:${z}`; d.innerHTML = `<img src="${src}" style="width:1080px;height:1920px;transform-origin:0 0;transform:translate(-206px,0) scale(1.3)">`; document.body.appendChild(d); };
    mk(bg, 0); document.getElementById('behind').style.zIndex = 1; mk(fg, 2); document.getElementById('front').style.zIndex = 3;
  }, ['file://' + bg, 'file://' + fg]);
  console.log(JSON.stringify(await p.evaluate(() => window.info().behind)));
  for (const t of ts) { await p.evaluate(t => window.seek(t), parseFloat(t)); await p.waitForTimeout(120); await p.screenshot({ path: `${out}/p-${String(t).padStart(6, '0')}.jpg`, quality: 85, type: 'jpeg' }); }
  await b.close();
})();
