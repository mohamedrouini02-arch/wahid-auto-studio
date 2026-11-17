"""Prices video: cut the raw clip, take the clock off the wall, put the graphics behind and in front of Wahid, mix the sound.
python render.py raw.mp4 out.mp4 [work_dir]
env: PLATE_W (width of the working copy, 1620), OUT_W (1080; 540 for a quick look), FROM/TO (output seconds, for a part only)"""
import sys, os, json, subprocess, wave, math
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
raw, out = sys.argv[1], sys.argv[2]
work = sys.argv[3] if len(sys.argv) > 3 else 'work/prices'
os.makedirs(work, exist_ok=True)
PLATE_W = int(os.environ.get('PLATE_W', 1080)); OUT_W = int(os.environ.get('OUT_W', 1080)); OUT_H = OUT_W * 16 // 9
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
    grade = 'eq=saturation=1.08:contrast=1.03,format=yuv420p'
    # the phone filmed in HLG: tone-map to normal video first
    hlg = 'zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0:peak=4,zscale=t=bt709:m=bt709:r=tv,format=yuv420p'
    chains = ([f'{hlg},{grade}', f'zscale=min=bt2020nc:m=bt709,{grade}'] if 'bt2020' in probe else []) + [grade]
    for chain in chains:
        r = sh(['ffmpeg', '-loglevel', 'error', '-y', '-i', raw, '-an', '-vf', f"fps={FPS},select='{sel}',setpts=N/{FPS}/TB,scale={PLATE_W}:-2:flags=lanczos,{chain}",
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '13', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', plate])
        if r.returncode == 0: break
    parts = ''.join(f'[0:a]atrim={a / FPS:.5f}:{b / FPS:.5f},asetpts=N/SR/TB,afade=t=in:d=0.006,afade=t=out:st={(b - a) / FPS - 0.006:.5f}:d=0.006[a{i}];' for i, (a, b) in enumerate(spans))
    sh(['ffmpeg', '-loglevel', 'error', '-y', '-i', raw, '-filter_complex', parts + ''.join(f'[a{i}]' for i in range(len(spans))) + f'concat=n={len(spans)}:v=0:a=1[a]',
        '-map', '[a]', '-ac', '1', '-ar', '48000', voice_raw], check=True)

# ---------- 2. the graphics, one transparent picture per frame
ov = f'{work}/ov'
STILL_FRAMES = ','.join(str(round(float(x) * FPS)) for x in os.environ.get('STILLS', '').split(',') if x)
if not os.path.exists(f'{ov}/info.json'):
    if STILL_FRAMES: os.environ['OV_FRAMES'] = STILL_FRAMES
    sh(['node', os.path.join(HERE, 'overlay.js'), ov, os.environ.get('OV_WORKERS', '4')], check=True)
info = json.load(open(f'{ov}/info.json'))
N = round(info['duration'] * FPS)
behind = lambda t: any(a - 1e-3 <= t < b for a, b in info['behind'])


# ---------- 3. camera: slow pushes, a new framing at each car; anchored at the top so the graphics keep their wall
ideas = sorted(set(round(s['t'], 2) for s in info['sfx']))
ev = [0.0]
for a in ideas:
    if a - ev[-1] > 2.0: ev.append(a)
LEVELS = [1.0, 1.05, 1.02, 1.07]
def zoom(t):
    i = max(k for k, e in enumerate(ev) if e <= t + 1e-6)
    s = LEVELS[i % len(LEVELS)] + min(0.035, 0.005 * (t - ev[i]))
    if i > 0:
        p = min(1.0, (t - ev[i]) / 0.45); p = 1 - (1 - p) ** 3
        prev = LEVELS[(i - 1) % len(LEVELS)] + min(0.035, 0.005 * (ev[i] - ev[i - 1]))
        s = prev * (1 - p) + s * p
    return s

# ---------- 4. frame by frame
sys.path.insert(0, HERE)
import cleanwall
from rembg import remove, new_session
SESSION = new_session('u2net_human_seg')
GUIDED = hasattr(cv2, 'ximgproc')
print('guided filter', GUIDED, flush=True)

def matte(frame):
    """Wahid as a soft alpha matte: the network finds him, the picture itself gives the fine edge (hair, fleece)."""
    H, W = frame.shape[:2]
    small = cv2.resize(frame, (W // 3, H // 3), interpolation=cv2.INTER_AREA)
    m = np.asarray(remove(cv2.cvtColor(small, cv2.COLOR_BGR2RGB), session=SESSION, only_mask=True)).astype(np.float32) / 255
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    if GUIDED:
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
        m = cv2.ximgproc.guidedFilter(g, m, 6, 1e-3)
    # the wall is light and grey: where the network is unsure, trust that
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32) / 255
    wall = np.clip((hsv[..., 2] - 0.5) / 0.12, 0, 1) * np.clip((0.2 - hsv[..., 1]) / 0.08, 0, 1)
    band = (m > 0.08) & (m < 0.92)
    m = np.where(band, np.minimum(m, 1 - 0.85 * wall), m)
    return np.clip(m, 0, 1)

def clean_frame(frame, m):
    """Take the clock off the wall, never touching him."""
    hsv, non = cleanwall.split(frame)
    him = cv2.dilate((m > 0.15).astype(np.uint8), np.ones((9, 9), np.uint8))
    cand = non & (1 - him)
    cand = cv2.morphologyEx(cand, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(cand)
    keep = np.zeros_like(cand)
    for j in range(1, n):
        if st[j, 4] > 18: keep[lab == j] = 1
    keep = cv2.dilate(keep, np.ones((17, 17), np.uint8)) & (1 - him)
    if not keep.any(): return frame
    return cleanwall.clean(frame, keep)

o = OUT_W / 1080.0
cap = cv2.VideoCapture(plate)
STILLS = [float(x) for x in os.environ.get('STILLS', '').split(',') if x]
f0, f1 = int(float(os.environ.get('FROM', 0)) * FPS), min(N, int(float(os.environ.get('TO', 1e9)) * FPS))
if STILLS: f0, f1 = 0, min(N, int(max(STILLS) * FPS) + 1)
silent = f'{work}/silent.mp4'
enc = None if STILLS else subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OUT_W}x{OUT_H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-maxrate', '7M', '-bufsize', '14M', '-pix_fmt', 'yuv420p',
                        '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', silent], stdin=subprocess.PIPE)
want = set(round(s * FPS) for s in STILLS)
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
    if im.shape[2] == 3: im = cv2.cvtColor(im, cv2.COLOR_BGR2BGRA)
    return im if OUT_W == 1080 else cv2.resize(im, (OUT_W, OUT_H), interpolation=cv2.INTER_AREA)
frame = None; base = None; mb = None
for i in range(N):
    t = i / FPS
    if i < NV:
        ok, nxt = cap.read()
        if ok: frame = nxt
    if i < f0 or (STILLS and i not in want): continue
    if i >= f1: break
    if i < NV or base is None:
        s = zoom(t)
        H0, W0 = frame.shape[:2]
        M = np.float32([[s * OUT_W / W0, 0, -(s - 1) * OUT_W / 2], [0, s * OUT_W / W0, 0]])
        view = cv2.warpAffine(frame, M, (OUT_W, OUT_H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        mb = matte(view)
        base = clean_frame(view, mb)
    img = base.copy(); n = f'{i:05d}'
    if behind(t):
        b = load('b' + n)
        if b is not None and b[..., 3].any():
            over(img, b); a = mb[..., None]; img = (img * (1 - a) + base * a).astype(np.uint8)
    over(img, load('f' + n))
    if STILLS:
        cv2.imwrite(f'{work}/still-{t:06.2f}.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        cv2.imwrite(f'{work}/matte-{t:06.2f}.jpg', (mb * 255).astype(np.uint8))
        continue
    enc.stdin.write(img.tobytes())
    if i % 300 == 0: print('frame', i, '/', N, flush=True)
cap.release()
if STILLS:
    print('stills done'); sys.exit(0)
enc.stdin.close(); enc.wait()


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
