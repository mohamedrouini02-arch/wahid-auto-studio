"""Comeback video: cut the raw clip, stabilise and reframe it, put the graphics behind and in front of the speaker, mix the sound.
python render.py raw.mp4 out.mp4 [work_dir]
env: PLATE_W (width of the working copy, 1620), OUT_W (1080; 540 for a quick look), FROM/TO (output seconds, for a part only)"""
import sys, os, json, subprocess, wave, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
raw, out = sys.argv[1], sys.argv[2]
work = sys.argv[3] if len(sys.argv) > 3 else 'work/comeback'
os.makedirs(work, exist_ok=True)
PLATE_W = int(os.environ.get('PLATE_W', 1620)); OUT_W = int(os.environ.get('OUT_W', 1080)); OUT_H = OUT_W * 16 // 9
FPS = 30
subprocess.run([sys.executable, os.path.join(HERE, 'edl.py')], check=True, stdout=subprocess.DEVNULL)
TL = json.load(open(os.path.join(HERE, 'timeline.json')))
SFX = os.path.join(HERE, '..', '..', 'studio', 'sfx')

def sh(cmd, **kw):
    print('+', ' '.join(str(c) for c in cmd)[:300], flush=True)
    return subprocess.run([str(c) for c in cmd], **kw)

# ---------- 1. the cut: picture (working copy) and voice
plate, voice_raw = f'{work}/plate.mp4', f'{work}/voice_raw.wav'
spans = [(round(g['src'][0] * FPS), round(g['src'][1] * FPS)) for g in TL['segments']]
NV = sum(b - a for a, b in spans)
if not os.path.exists(plate):
    sel = '+'.join(f'between(n,{a},{b - 1})' for a, b in spans)
    probe = sh(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=color_space', '-of', 'csv=p=0', raw], capture_output=True, text=True).stdout
    grade = 'eq=saturation=1.12:contrast=1.04,format=yuv420p'
    chains = ([f'zscale=min=bt2020nc:m=bt709,{grade}'] if 'bt2020' in probe else []) + [grade]
    for chain in chains:
        r = sh(['ffmpeg', '-loglevel', 'error', '-y', '-i', raw, '-an', '-vf', f"fps={FPS},select='{sel}',setpts=N/{FPS}/TB,scale={PLATE_W}:-2:flags=lanczos,{chain}",
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '13', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', plate])
        if r.returncode == 0: break
    parts = ''.join(f'[0:a]atrim={a / FPS:.5f}:{b / FPS:.5f},asetpts=N/SR/TB,afade=t=in:d=0.006,afade=t=out:st={(b - a) / FPS - 0.006:.5f}:d=0.006[a{i}];' for i, (a, b) in enumerate(spans))
    sh(['ffmpeg', '-loglevel', 'error', '-y', '-i', raw, '-filter_complex', parts + ''.join(f'[a{i}]' for i in range(len(spans))) + f'concat=n={len(spans)}:v=0:a=1[a]',
        '-map', '[a]', '-ac', '1', '-ar', '48000', voice_raw], check=True)

# ---------- 2. the graphics, one transparent picture per frame
ov = f'{work}/ov'
if not os.path.exists(f'{ov}/info.json'):
    sh(['node', os.path.join(HERE, 'overlay.js'), ov, os.environ.get('OV_WORKERS', '4')], check=True)
info = json.load(open(f'{ov}/info.json'))
N = round(info['duration'] * FPS)
behind = lambda t: any(a - 1e-3 <= t < b for a, b in info['behind'])

# ---------- 3. camera: a new framing at every cut and every new idea, with a slow push in between
cuts = [0.0] + TL['cuts']
ideas = sorted(s['t'] for s in info['sfx'])
ev = [(c, 'cut') for c in cuts]
for a in ideas:
    if all(abs(a - e[0]) > 2.2 for e in ev): ev.append((a, 'ease'))
ev.sort()
LEVELS = [1.34, 1.27, 1.40, 1.30]
def level(i, t): return LEVELS[i % len(LEVELS)] + min(0.05, 0.007 * (t - ev[i][0]))
def zoom(t):
    t = min(t, TL['duration'] - 1 / FPS)
    i = max(k for k, e in enumerate(ev) if e[0] <= t + 1e-6)
    s = level(i, t)
    if ev[i][1] == 'ease' and i > 0:
        p = min(1.0, (t - ev[i][0]) / 0.4); p = 1 - (1 - p) ** 3
        s = level(i - 1, ev[i][0]) * (1 - p) + s * p
    return s

# ---------- 4. frame by frame
try:
    from rembg import remove, new_session
    SESSION = new_session('u2net_human_seg')
except Exception as e:
    print('no rembg here, colour key only:', e); SESSION = None
k = PLATE_W / 1080.0; o = OUT_W / 1080.0
cap = cv2.VideoCapture(plate)
ok, first = cap.read(); assert ok
PH = first.shape[0]
def find_remote(gray):
    """The air-conditioner remote on the wall: the dark thing in the bright wall above his head. Used as the fixed point of the room."""
    y0, y1, x0, x1 = int(150 * k), int(620 * k), int(430 * k), int(780 * k)
    band = gray[y0:y1, x0:x1].astype(np.float32) / 255
    col = cv2.blur(band.min(0)[None], (5, 1))[0]; xs = np.where(col < col.max() - 0.12)[0]
    row = band[:, xs.min():xs.max() + 1].min(1); ys = np.where(row < row.max() - 0.12)[0]
    return x0 + xs.min(), y0 + ys.min(), x0 + xs.max(), y0 + ys.max()
g0 = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
rx0, ry0, rx1, ry1 = find_remote(g0)
print('remote', [round(v / k) for v in (rx0, ry0, rx1, ry1)], flush=True)
m = int(8 * k); tmpl = g0[ry0 - m:ry1 + m, rx0 - m:rx1 + m].copy()
pos = np.array([rx0 - m, ry0 - m], np.float32); smooth = pos.copy()
tw, th = tmpl.shape[1], tmpl.shape[0]
def track(gray):
    global pos, smooth
    r = int(36 * k); x0, y0 = int(max(0, pos[0] - r)), int(max(0, pos[1] - r))
    win = gray[y0:y0 + th + 2 * r, x0:x0 + tw + 2 * r]
    if win.shape[0] > th and win.shape[1] > tw:
        res = cv2.matchTemplate(win, tmpl, cv2.TM_CCOEFF_NORMED); _, score, _, loc = cv2.minMaxLoc(res)
        if score > 0.55: pos = np.array([x0 + loc[0], y0 + loc[1]], np.float32)
    smooth = smooth * 0.8 + pos * 0.2
    return smooth
def patch(frame, p):
    """Paint the remote and its pipe out with the clean wall next to it."""
    x0, x1 = int(p[0] - 16 * k), int(p[0] + tw + 16 * k); y1 = int(p[1] + th + 34 * k); w = x1 - x0; sx = x0 - w - int(14 * k)
    if sx < 0: return
    f = int(14 * k); a = np.ones((y1, w), np.float32)
    ramp = np.linspace(0, 1, f, dtype=np.float32); a[:, :f] *= ramp; a[:, -f:] *= ramp[::-1]; a[-f:, :] *= ramp[::-1][:, None]
    a = a[..., None]
    frame[:y1, x0:x1] = (frame[:y1, sx:sx + w] * a + frame[:y1, x0:x1] * (1 - a)).astype(np.uint8)
def over(dst, png):
    if png is None: return
    al = png[..., 3]; ys, xs = np.where(al.any(1))[0], np.where(al.any(0))[0]
    if not len(ys): return
    y0, y1, x0, x1 = ys[0], ys[-1] + 1, xs[0], xs[-1] + 1
    a = al[y0:y1, x0:x1, None].astype(np.float32) / 255
    dst[y0:y1, x0:x1] = (dst[y0:y1, x0:x1] * (1 - a) + png[y0:y1, x0:x1, :3] * a).astype(np.uint8)
def load(name):
    p = f'{ov}/{name}.png'
    if not os.path.exists(p): return None
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 3: im = cv2.cvtColor(im, cv2.COLOR_BGR2BGRA)      # a fully opaque frame comes without alpha
    return im if OUT_W == 1080 else cv2.resize(im, (OUT_W, OUT_H), interpolation=cv2.INTER_AREA)
def person(frame):
    """Where he is in the frame (0..1): the neural mask says roughly, the white wall gives the clean edge."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32) / 255
    wall = ((hsv[..., 2] > 0.60) & (hsv[..., 1] < 0.14)).astype(np.float32)
    key = cv2.GaussianBlur(1 - wall, (0, 0), 1.6 * o)
    if SESSION is not None:
        small = cv2.resize(frame, (OUT_W // 3, OUT_H // 3), interpolation=cv2.INTER_AREA)
        mk = np.asarray(remove(cv2.cvtColor(small, cv2.COLOR_BGR2RGB), session=SESSION, only_mask=True)).astype(np.float32) / 255
        mk = cv2.resize(mk, (OUT_W, OUT_H), interpolation=cv2.INTER_LINEAR)
        near = cv2.dilate((mk > 0.4).astype(np.float32), np.ones((int(41 * o) | 1,) * 2, np.uint8))
        core = cv2.erode((mk > 0.6).astype(np.float32), np.ones((int(25 * o) | 1,) * 2, np.uint8))
        return np.maximum(key * cv2.GaussianBlur(near, (0, 0), 6 * o), cv2.GaussianBlur(core, (0, 0), 3 * o))
    key[:int(700 * o)] = 0; key[:, :int(250 * o)] = 0
    return key

f0, f1 = int(float(os.environ.get('FROM', 0)) * FPS), min(N, int(float(os.environ.get('TO', 1e9)) * FPS))
silent = f'{work}/silent.mp4'
enc = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OUT_W}x{OUT_H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-maxrate', '7M', '-bufsize', '14M', '-pix_fmt', 'yuv420p',
                        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', silent], stdin=subprocess.PIPE)
frame = first; base = None
for i in range(N):
    t = i / FPS
    if i > 0 and i < NV:
        ok, nxt = cap.read()
        if ok: frame = nxt
    if i < NV or base is None:
        p = track(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        if i < f0: continue
        patch(frame, p)
        s = zoom(t)
        ax, ay = (p[0] + tw / 2) / k + 95, (p[1] + th - m) / k + 292           # his face, measured from the remote
        tx = min(0, max(1080 - 1080 * s, 600 - ax * s)); ty = min(0, max(1920 - PH / k * s, 1105 - ay * s))
        M = np.float32([[s / k * o, 0, tx * o], [0, s / k * o, ty * o]])
        base = cv2.warpAffine(frame, M, (OUT_W, OUT_H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    if i < f0: continue
    if i >= f1: break
    img = base.copy(); n = f'{i:05d}'
    if behind(t):
        b = load('b' + n)
        if b is not None and b[..., 3].any():
            mk = person(base)[..., None]
            over(img, b); img = (img * (1 - mk) + base * mk).astype(np.uint8)
    over(img, load('f' + n))
    enc.stdin.write(img.tobytes())
    if i % 300 == 0: print('frame', i, '/', N, flush=True)
enc.stdin.close(); enc.wait(); cap.release()

# ---------- 5. sound: clean voice, a quiet bed that ducks under it, soft cues on the graphics
total = info['duration']
voice, bed, cues = f'{work}/voice.wav', f'{work}/bed.wav', f'{work}/cues.wav'
sh(['ffmpeg', '-loglevel', 'error', '-y', '-i', voice_raw, '-af',
    'highpass=f=85,afftdn=nr=9:nf=-42,equalizer=f=3400:t=q:w=1.2:g=2,acompressor=threshold=-21dB:ratio=3:attack=8:release=160:makeup=2,loudnorm=I=-15:TP=-1.5:LRA=9,apad=whole_dur=' + f'{total:.3f}',
    '-ar', '48000', '-ac', '2', voice], check=True)
sh([sys.executable, os.path.join(HERE, 'bed.py'), bed, f'{total:.3f}'], check=True)
SR = 48000; mix = np.zeros((int(total * SR) + SR, 2), np.float32)
def sfx(name, t, vol):
    raw_ = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', os.path.join(SFX, name + '.wav'), '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True).stdout
    x = np.frombuffer(raw_, np.float32).reshape(-1, 2); i0 = int(max(0, t) * SR); x = x[:len(mix) - i0]
    mix[i0:i0 + len(x)] += x * vol
for e in info['sfx']:
    if e['t'] < 0.2: continue
    sfx('whoosh' if e['kind'] == 'whoosh' else 'pop', e['t'] - (0.12 if e['kind'] == 'whoosh' else 0.0), 0.16 if e['kind'] == 'whoosh' else 0.13)
sfx('transition', info['video'] - 0.15, 0.16)
with wave.open(cues, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
a0 = f0 / FPS
sh(['ffmpeg', '-loglevel', 'error', '-y', '-i', silent, '-ss', f'{a0:.3f}', '-i', voice, '-ss', f'{a0:.3f}', '-i', bed, '-ss', f'{a0:.3f}', '-i', cues, '-filter_complex',
    '[2:a]aresample=48000,volume=0.20[b];[1:a]asplit[v1][v2];[b][v2]sidechaincompress=threshold=0.02:ratio=5:attack=60:release=700[bd];'
    '[v1][bd][3:a]amix=inputs=3:normalize=0,alimiter=limit=0.92[a]',
    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out], check=True)
print('done', out, flush=True)
