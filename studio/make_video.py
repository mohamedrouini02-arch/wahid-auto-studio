"""Wahid Auto video maker.

    python studio/make_video.py jobs/<job>.json out/<name>.mp4

A job describes the car, its media (photo/video URLs or paths) and a script:
a list of beats, each with a line for the voice-over and the shots shown while
it is spoken. Timing comes from the voice: each beat lasts as long as its line.
"""
import asyncio, json, math, os, random, shutil, subprocess, sys, urllib.request, wave
import numpy as np
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
SR = 44100
KR = '<svg width="52" height="36" viewBox="0 0 30 20" style="border-radius:4px"><rect width="30" height="20" fill="#fff"/><g transform="translate(15 10) rotate(33.7)"><circle r="5" fill="#0047A0"/><path d="M-5 0A5 5 0 0 1 5 0A2.5 2.5 0 0 0 0 0A2.5 2.5 0 0 1 -5 0Z" fill="#CD2E3A"/></g><g fill="#111"><rect x="4" y="3" width="1" height="4" transform="rotate(-56 4.5 5)"/><rect x="25" y="13" width="1" height="4" transform="rotate(-56 25.5 15)"/><rect x="25" y="3" width="1" height="4" transform="rotate(56 25.5 5)"/><rect x="4" y="13" width="1" height="4" transform="rotate(56 4.5 15)"/></g></svg>'
CN = '<svg width="52" height="36" viewBox="0 0 30 20" style="border-radius:4px"><rect width="30" height="20" fill="#DE2910"/><path fill="#FFDE00" d="M5 3l1.2 3.6H10L7 8.8l1.1 3.6L5 10.2 1.9 12.4 3 8.8 0 6.6h3.8z"/></svg>'
DZ = '<svg width="52" height="36" viewBox="0 0 30 20" style="border-radius:4px"><rect width="15" height="20" fill="#006233"/><rect x="15" width="15" height="20" fill="#fff"/><path fill="#D21034" fill-rule="evenodd" d="M15.7 4.8a5.2 5.2 0 1 0 0 10.4a5.2 5.2 0 1 0 0-10.4M17 5.9a4.1 4.1 0 1 0 0 8.2a4.1 4.1 0 1 0 0-8.2"/></svg>'


def run(*cmd):
    subprocess.run(cmd, check=True)


def fetch(src, dest):
    if src.startswith('http'):
        urllib.request.urlretrieve(src, dest)
    else:
        shutil.copy(src, dest)
    return dest


def audio_len(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


# ---------------- sound effects (synthesised, no licences needed) ----------------
def _env(n, attack, release):
    e = np.ones(n)
    a = max(1, int(attack * SR)); r = max(1, int(release * SR))
    e[:a] = np.linspace(0, 1, a)
    e[-r:] *= np.linspace(1, 0, r) ** 2
    return e


def _bandnoise(n, lo, hi, seed=0):
    rng = np.random.default_rng(seed)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[(f < lo) | (f > hi)] = 0
    x = np.fft.irfft(spec, n)
    return x / (np.abs(x).max() + 1e-9)


def make_sfx():
    s = {}
    # whoosh: noise whose band sweeps up then down, soft in and out
    n = int(0.42 * SR); t = np.linspace(0, 1, n)
    parts = []
    for k, (lo, hi) in enumerate([(300, 1200), (800, 3000), (1500, 6000), (900, 3500), (400, 1500)]):
        parts.append(_bandnoise(n, lo, hi, k) * np.exp(-((t - (k + 0.5) / 5) ** 2) / 0.012))
    w = sum(parts) * np.sin(np.pi * t) ** 1.5
    s['whoosh'] = 0.55 * w / np.abs(w).max()
    # pop: quick pitched blip with a click on top
    n = int(0.11 * SR); t = np.arange(n) / SR
    f = 620 + 900 * np.exp(-t * 60)
    p = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
    p[:60] += np.random.default_rng(3).standard_normal(60) * 0.4
    s['pop'] = 0.5 * p / np.abs(p).max()
    # impact: sub drop + noise crack, for the price
    n = int(0.9 * SR); t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * (48 + 60 * np.exp(-t * 18)) * t) * np.exp(-t * 4.5)
    crack = _bandnoise(n, 200, 5000, 9) * np.exp(-t * 22)
    im = sub + 0.45 * crack
    s['impact'] = 0.8 * im / np.abs(im).max()
    # riser: noise + rising tone into the price
    n = int(1.1 * SR); t = np.linspace(0, 1, n)
    tone = np.sin(2 * np.pi * np.cumsum(220 + 900 * t ** 2) / SR)
    r = (_bandnoise(n, 1000, 7000, 5) * 0.6 + tone * 0.25) * t ** 2.2
    s['riser'] = 0.45 * r / np.abs(r).max()
    # tick: tiny click for counting numbers
    n = int(0.03 * SR); t = np.arange(n) / SR
    s['tick'] = 0.25 * np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 300)
    return s


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def read_audio(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


# ---------------- voice-over ----------------
def tts(text, out, voice, rate):
    raw = out + '.raw.mp3'
    run('edge-tts', '--voice', voice, f'--rate={rate}', '--text', text, '--write-media', raw)
    # trim the silence the engine leaves at both ends so lines follow each other like real speech
    run('ffmpeg', '-loglevel', 'error', '-y', '-i', raw, '-af',
        'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse',
        out)


# ---------------- media ----------------
def prepare_media(job, work):
    shots = []
    for i, m in enumerate(job['media']):
        m = dict(m)
        ext = '.mp4' if m.get('type') == 'video' else '.jpg'
        src = fetch(m['src'], os.path.join(work, f'src{i}{ext}'))
        if m.get('type') == 'video':
            d = os.path.join(work, f'v{i}'); os.makedirs(d, exist_ok=True)
            run('ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-vf',
                f'fps={FPS},scale=1500:1500:force_original_aspect_ratio=decrease', '-q:v', '3', f'{d}/%05d.jpg')
            first = Image.open(f'{d}/00001.jpg')
            # contact sheet of the clip (one frame per second) so the editor can pick the best moments
            sheet = os.path.join(os.path.dirname(os.path.abspath(sys.argv[2])), f'clip{i}-sheet.jpg')
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-vf', 'fps=1,scale=180:-1,drawtext=text=%{pts\\:hms}:x=4:y=4:fontcolor=yellow:fontsize=14,tile=8x4', '-frames:v', '1', sheet])
            m.update(dir=os.path.relpath(d, HERE), frames=len(os.listdir(d)), fps=FPS, w=first.width, h=first.height,
                     length=len(os.listdir(d)) / FPS)
        else:
            im = ImageOps.exif_transpose(Image.open(src)).convert('RGB'); im.thumbnail((1600, 1600))
            out = os.path.join(work, f'p{i}.jpg'); im.save(out, quality=90)
            m.update(src=os.path.relpath(out, HERE), w=im.width, h=im.height, type='photo')
        shots.append(m)
    return shots


# ---------------- timeline ----------------
def build(job, shots, work):
    voice = job.get('voice') or {}
    vname, vrate = voice.get('name', 'ar-DZ-IsmaelNeural'), voice.get('rate', '+0%')
    pad = job.get('pad', 0.25)
    beats = job['script']
    clips = []
    for k, b in enumerate(beats):
        if b.get('say') and job.get('voice'):
            p = os.path.join(work, f'vo{k}.mp3'); tts(b['say'], p, vname, vrate)
            b['_vo'], b['_len'] = p, audio_len(p)
        else:
            b['_len'] = 0
    tl, sfx, vo, marks = [], [], [], []
    t = 0.0
    hook_end = body_end = price_end = None
    video_cursor = {}
    for k, b in enumerate(beats):
        kind = b.get('kind', 'body')
        if b.get('_vo'):
            dur = max(b.get('min', 0), b['_len'] + pad)
        else:  # no voice-over: give every shot time to be seen
            dur = b.get('dur') or (len(b.get('shots', [])) * job.get('shot', 2.4) if kind == 'body' else 0)
        if kind == 'hook':
            dur = max(dur, 3.4)
        if kind == 'price':
            dur = max(dur, 3.4)
        if kind == 'end':
            dur = max(dur, 3.0)
        if b.get('_vo'):
            vo.append((t + b.get('delay', 0.15), b['_vo']))
        if b.get('say'):
            marks.append({'t': round(t, 2), 'end': round(t + dur, 2), 'say': b['say']})
        if kind in ('hook', 'body'):
            ids = b['shots']
            each = dur / len(ids)
            for j, spec in enumerate(ids):
                # a shot is a media index, or {"m": index, "at": seconds into a video}
                si = spec['m'] if isinstance(spec, dict) else spec
                e = {'t0': round(t + j * each, 3), 't1': round(t + (j + 1) * each, 3), 'shot': si}
                if kind == 'hook':
                    e['hook'] = True
                if b.get('label') and j == 0:
                    e['label'] = b['label']
                s = shots[si]
                if s.get('type') == 'video':
                    if isinstance(spec, dict) and 'frac' in spec:
                        c = max(0.0, spec['frac'] * s['length'] - each / 2)
                    elif isinstance(spec, dict) and 'at' in spec:
                        c = spec['at']
                    else:
                        c = video_cursor.get(si, s.get('start', 0))
                    if c + each > s['length']:
                        c = 0
                    e['from'] = c; video_cursor[si] = c + each
                tl.append(e)
                if j == 0 and kind == 'body':
                    sfx.append((e['t0'] - 0.25, 'whoosh', 0.5))      # a new idea starts
                elif j > 0:
                    sfx.append((e['t0'] - 0.05, 'cut', 0.35))        # light hit on other cuts
                if e.get('label'):
                    sfx.append((e['t0'] + 0.25, 'pop', 0.6))          # label box
                    sfx.append((e['t0'] + 0.4, 'click', 0.45))        # second line
            if kind == 'hook':
                hook_end = t + dur
                sfx += [(0.0, 'impact', 0.55), (0.3, 'pop', 0.6), (0.7, 'pop', 0.55),
                        (1.3, 'click', 0.45), (1.55, 'click', 0.45), (1.8, 'click', 0.45), (2.3, 'pop', 0.6)]

        elif kind == 'price':
            body_end = t
            sfx += [(t - 1.0, 'riser', 0.5), (t - 0.3, 'transition', 0.5), (t + 0.1, 'pop', 0.5),
                    (t + 1.25, 'impact', 0.8), (t + 1.7, 'click', 0.45)]
        elif kind == 'end':
            price_end = t
            sfx += [(t - 0.25, 'whoosh', 0.45), (t + 0.35, 'pop', 0.5), (t + 0.75, 'click', 0.4),
                    (t + 1.1, 'click', 0.4), (t + 1.45, 'click', 0.35)]
        t += dur
    return {'tl': tl, 'hookEnd': hook_end, 'bodyEnd': body_end, 'priceEnd': price_end, 'total': round(t, 3), 'marks': marks}, sfx, vo


LEVEL = {'whoosh': 0.25, 'transition': 0.3, 'cut': 0.14, 'pop': 0.22, 'click': 0.11, 'impact': 0.5, 'riser': 0.22}


def mix(total, sfx, vo, music, out):
    n = int(total * SR) + SR
    bus = np.zeros(n, np.float32)
    # only real recorded sounds from studio/sfx/<name>.(wav|mp3); a missing one is simply silent
    lib = {}
    for name in ('whoosh', 'transition', 'cut', 'pop', 'click', 'impact', 'riser'):
        for ext in ('wav', 'mp3'):
            f = os.path.join(HERE, 'sfx', f'{name}.{ext}')
            if os.path.exists(f):
                lib[name] = read_audio(f); break
    for at, name, gain in sfx:
        if name not in lib: continue
        # every sound is levelled to its own target so no effect jumps out of the mix
        x = lib[name] / (np.abs(lib[name]).max() + 1e-9) * LEVEL.get(name, 0.2) * (gain / 0.5)
        i = int(max(0, at) * SR); bus[i:i + len(x)] += x[: n - i]
    voice = np.zeros(n, np.float32)
    for at, path in vo:
        x = read_audio(path); i = int(at * SR); voice[i:i + len(x)] += x[: n - i] * 1.0
    if music:
        m = read_audio(music)
        m = np.tile(m, int(np.ceil(n / len(m))))[:n]
        # duck the music under the voice
        env = np.convolve(np.abs(voice) > 0.02, np.ones(SR // 5) / (SR // 5), 'same')
        bus += m * (0.22 - 0.14 * np.clip(env * 3, 0, 1))
    y = bus + voice
    y = y[: int(total * SR)]
    y = y / max(1.0, np.abs(y).max() / 0.95)
    write_wav(out, y)


async def render(cfg, frames_dir):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': 1080, 'height': 1920})
        await pg.add_init_script(f'window.CONFIG = {json.dumps(cfg)}')
        await pg.goto('file://' + HERE + '/template.html')
        await pg.evaluate('document.fonts.ready')
        await pg.evaluate("Promise.all([...document.images].map(i => i.decode().catch(()=>{})))")
        n = round(cfg['total'] * FPS)
        for i in range(n):
            await pg.evaluate(f'render({i / FPS})')
            await pg.screenshot(path=f'{frames_dir}/f{i:05d}.jpg', type='jpeg', quality=92)
        await b.close()


def main():
    job = json.load(open(sys.argv[1])); out = sys.argv[2]
    work = os.path.join(HERE, 'work'); shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
    frames = os.path.join(work, 'frames'); os.makedirs(frames)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    car = job['car']
    car['chips'] = [c.replace('{KR}', KR).replace('{CN}', CN).replace('{DZ}', DZ) for c in car['chips']]
    shots = prepare_media(job, work)
    timing, sfx, vo = build(job, shots, work)
    cfg = {'car': car, 'shots': shots, 'priceShot': job.get('priceShot', 0), **timing}
    asyncio.run(render(cfg, frames))
    wav = os.path.join(work, 'mix.wav')
    mix(timing['total'], sfx, vo, job.get('music'), wav)
    run('ffmpeg', '-loglevel', 'error', '-y', '-framerate', str(FPS), '-i', f'{frames}/f%05d.jpg', '-i', wav,
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
        '-shortest', '-movflags', '+faststart', out)
    json.dump({'total': timing['total'], 'lines': timing['marks']}, open(out[:-4] + '-script.json', 'w'), ensure_ascii=False, indent=1)
    print(out, timing['total'], 's')


if __name__ == '__main__':
    main()
