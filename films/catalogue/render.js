// Film one car:  node render.js job.json out.mp4 [stills t1,t2,...]
// Frames are screenshots of car.html piped to ffmpeg; then a music bed and soft whooshes on the cuts are mixed in.
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs'); const { spawn, execFileSync } = require('child_process');
(async () => {
  const [jobPath, out, stills] = process.argv.slice(2);
  const job = JSON.parse(fs.readFileSync(jobPath, 'utf8')); const FPS = 30;
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => { console.log('PAGE ERROR', e.message); process.exit(1); });
  await p.goto('file://' + path.join(__dirname, 'car.html'));
  const info = await p.evaluate(j => window.setup(j), job);
  console.log(JSON.stringify(info));
  if (stills) {
    for (const t of stills.split(',')) { await p.evaluate(t => window.seek(t), +t); await p.screenshot({ path: `${out}-${t}.jpg`, type: 'jpeg', quality: 90 }); }
    await b.close(); return;
  }
  const tmp = out + '.video.mp4', N = Math.round(info.duration * FPS);
  const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(FPS), '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tmp], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < N; i++) {
    await p.evaluate(t => window.seek(t), i / FPS);
    const buf = await p.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log('frame', i, '/', N);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close();
  // sound
  const dir = path.dirname(out), bed = out + '.bed.wav', sfx = path.join(__dirname, '..', '..', 'studio', 'sfx');
  execFileSync('python3', [path.join(__dirname, '..', 'comeback2', 'bed.py'), bed, String(info.duration + 0.1)]);
  const cues = [...info.cuts.map(t => ['whoosh', t - 0.18, 0.22]), ['whoosh', info.price - 0.18, 0.3], ['pop', info.price + 0.3, 0.25], ['transition', info.end - 0.15, 0.25]];
  const args = ['-loglevel', 'error', '-y', '-i', tmp, '-i', bed];
  cues.forEach(([n]) => args.push('-i', path.join(sfx, n + '.wav')));
  const fx = cues.map(([, t, v], i) => `[${i + 2}:a]adelay=${Math.max(0, Math.round(t * 1000))}:all=1,volume=${v}[c${i}]`).join(';');
  args.push('-filter_complex', `[1:a]volume=0.55[m];${fx};[m]${cues.map((_, i) => `[c${i}]`).join('')}amix=inputs=${cues.length + 1}:normalize=0:duration=first,alimiter=limit=0.9[a]`,
    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out);
  execFileSync('ffmpeg', args, { stdio: 'inherit' });
  fs.unlinkSync(tmp); fs.unlinkSync(bed);
  console.log('done', out);
})();
