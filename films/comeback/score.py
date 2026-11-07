"""Original score for the Wahid Auto comeback film: 100 BPM, A minor, 48 s.
Sections follow the edit (a bar = 2.4 s). Pad from the first frame; sub at "ورجعنا";
kick + shaker for the identity; plucks for the website; full groove for the process;
a lift for "what's next"; pads and one last hit on the logo. SFX sit on the animations.

    python score.py out.wav
"""
import sys, wave, os
import numpy as np

SR = 48000
DUR = 48.0
BEAT = 0.6
N = int(SR * DUR)
rng = np.random.default_rng(3)
S2, S3, S4, S5, S6, S7, END = 4.8, 9.6, 16.8, 24.0, 36.0, 43.2, 48.0
SFX = '/home/claude/wahid-auto-studio/studio/sfx'


def tt(sec): return np.arange(int(sec * SR)) / SR
def midi(m): return 440.0 * 2 ** ((m - 69) / 12)


def lowpass(x, hz):
    s = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(s / np.sqrt(1 + (f / hz) ** 4), len(x))


def highpass(x, hz):
    s = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(s / np.sqrt(1 + (hz / np.maximum(f, 1)) ** 4), len(x))


def add(buf, x, at, g=1.0):
    i = int(at * SR)
    if i >= len(buf): return
    x = x[: len(buf) - i]
    buf[i:i + len(x)] += x * g


def env(n, a, r):
    e = np.ones(n); A = max(1, int(a * SR)); R = max(1, int(r * SR))
    e[:A] = np.linspace(0, 1, A); e[-R:] *= np.linspace(1, 0, R)
    return e


def reverb(x, sec=2.4, mix=0.3):
    n = int(sec * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 6))
    ir = lowpass(ir, 5000); ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n; f = 1 << int(np.ceil(np.log2(L)))
    wet = np.fft.irfft(np.fft.rfft(x, f) * np.fft.rfft(ir, f), f)[:len(x)]
    return x * (1 - mix) + wet * mix * 0.9


def section_gain(t, pts):
    """piecewise-linear automation: pts = [(time, gain), ...]"""
    ts, gs = zip(*pts)
    return np.interp(t, ts, gs)


T = np.arange(N) / SR
# Am(add9) — Fmaj7 — C(add9) — G6 , one chord per bar
CHORDS = [[57, 60, 64, 71], [53, 57, 60, 64], [48, 55, 60, 62], [55, 59, 62, 64]]
ROOTS = [45, 41, 48, 43]
bar = lambda t: int(t // (4 * BEAT))

# ---------- pad ----------
pad = np.zeros(N)
for b in range(int(DUR / (4 * BEAT)) + 1):
    ch = CHORDS[b % 4]; start = b * 4 * BEAT; length = 4 * BEAT + 1.2
    tx = tt(length)
    v = np.zeros(len(tx))
    for m in ch:
        for det in (-0.07, 0.0, 0.08):
            f = midi(m) * 2 ** (det / 12)
            ph = rng.uniform(0, 1)
            v += (2 * ((tx * f + ph) % 1) - 1) * 0.33
    v = lowpass(v, 1400) * env(len(tx), 0.9, 1.3)
    add(pad, v, start, 0.06)
pad = reverb(pad, 3.2, 0.45)

# ---------- sub bass (sidechained to the beat) ----------
sub = np.zeros(N)
for b in range(int(DUR / (4 * BEAT)) + 1):
    tx = tt(4 * BEAT)
    f = midi(ROOTS[b % 4] - 12)
    v = np.sin(2 * np.pi * f * tx) + 0.25 * np.sin(4 * np.pi * f * tx)
    add(sub, v * env(len(tx), 0.02, 0.15), b * 4 * BEAT, 0.22)

# ---------- kick, clap, shaker ----------
def kick():
    x = tt(0.42); f = 46 + 90 * np.exp(-x * 26)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9) + 0.12 * lowpass(rng.standard_normal(len(x)), 3000) * np.exp(-x * 80)
def clap():
    x = tt(0.3); n = highpass(lowpass(rng.standard_normal(len(x)), 6000), 900)
    e = sum(np.exp(-np.maximum(x - d, 0) * 60) * (x >= d) for d in (0, 0.011, 0.023)) * np.exp(-x * 18)
    return reverb(n * e, 0.8, 0.25)
def shaker():
    x = tt(0.09); return highpass(rng.standard_normal(len(x)), 7000) * np.exp(-x * 55)
KICK, CLAP, SHK = kick(), clap(), shaker()
drums = np.zeros(N); duck = np.ones(N)
t = 0.0
while t < DUR - 0.2:
    if S3 <= t < S7 or S7 + 0.0 > t >= S5:
        g = 0.55 if t < S5 else 0.85
        if S6 - 2.4 <= t < S6: g = 0.0                         # a breath before "what's next"
        if g:
            add(drums, KICK, t, g)
            i = int(t * SR); k = int(0.35 * SR)
            duck[i:i + k] = np.minimum(duck[i:i + k], 1 - 0.55 * np.exp(-np.arange(min(k, N - i)) / (0.09 * SR)))
    beat_in_bar = round((t % (4 * BEAT)) / BEAT)
    if S5 <= t < S7 and beat_in_bar in (1, 3) and not (S6 - 2.4 <= t < S6): add(drums, CLAP, t, 0.22)
    if S4 <= t < S7 - 0.1: add(drums, SHK, t + BEAT / 2, 0.08); add(drums, SHK, t + BEAT * 0.75, 0.04)
    t += BEAT

# ---------- pluck arpeggio (with dotted-eighth echo) ----------
plk = np.zeros(N)
step = BEAT / 4
t = S4
pattern = [0, 2, 1, 3, 2, 1, 3, 2]
k = 0
while t < S7 + 2.4:
    ch = CHORDS[bar(t) % 4]
    m = ch[pattern[k % 8] % 4] + 12
    x = tt(0.5); f = midi(m)
    v = (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(4 * np.pi * f * x + 0.3) + 0.15 * np.sin(6 * np.pi * f * x)) * np.exp(-x * 11)
    gain = 0.05 if t < S5 else 0.065
    if S6 - 2.4 <= t < S6: gain *= 0.5
    add(plk, v, t, gain)
    t += step; k += 1
echo = np.zeros(N); d = int(BEAT * 0.75 * SR)
echo[d:] = plk[:-d] * 0.35; echo[2 * d:] += plk[:-2 * d] * 0.15
plk = reverb(plk + lowpass(echo, 3000), 1.6, 0.3)

# ---------- automation ----------
padG = section_gain(T, [(0, 0), (0.6, 0.8), (S2, 1.0), (S3, 0.8), (S5, 0.75), (S6 - 2.4, 1.0), (S6, 0.8), (S7, 1.0), (END - 1.2, 0.9), (END, 0)])
subG = section_gain(T, [(0, 0), (S2 - 0.1, 0), (S2, 0.9), (S3, 1.0), (S6 - 2.4, 0.6), (S6, 1.0), (S7, 0.5), (END, 0)])
mus = pad * padG * (0.55 + 0.45 * duck) + sub * subG * duck + drums + plk * duck
mus = highpass(mus, 28)

# ---------- sound design (uses the studio kit) ----------
def load(name):
    import subprocess
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', os.path.join(SFX, name + '.wav'), '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)
K = {n: load(n) for n in ('whoosh', 'transition', 'cut', 'pop', 'click', 'impact', 'riser')}
fx = np.zeros(N)
def e(at, name, g): add(fx, K[name], at, g)
# S1
e(0.2, 'whoosh', 0.25); e(0.55, 'click', 0.35); e(0.85, 'click', 0.3); e(1.7, 'pop', 0.25); e(2.0, 'whoosh', 0.2)
# S2 "ورجعنا."
e(S2 - 1.1, 'riser', 0.35); e(S2 - 0.02, 'impact', 0.75); e(6.55, 'whoosh', 0.3)
# open into the identity
e(8.0, 'riser', 0.45); e(8.75, 'transition', 0.45); e(S3 - 0.02, 'impact', 0.55); e(S3 + 0.05, 'pop', 0.3)
for i in range(8): e(S3 + 0.3 + i * 0.05, 'click', 0.08)
e(S3 + 1.2, 'whoosh', 0.18)
for i in range(5): e(S3 + 2.6 + i * 0.16, 'pop', 0.22)
# to the website
e(S4 - 0.8, 'whoosh', 0.3); e(S4 - 0.02, 'impact', 0.45); e(S4 + 0.3, 'transition', 0.35)
for i in range(3): e(S4 + 1.6 + i * 0.9, 'pop', 0.28)
e(S4 + 2.6, 'whoosh', 0.18); e(S4 + 4.6, 'whoosh', 0.18)
for i in range(6): e(S4 + 5.0 + i * 0.12, 'click', 0.18)
# into the process
e(S5 - 1.1, 'riser', 0.45); e(S5 - 0.02, 'impact', 0.7); e(S5 - 0.3, 'transition', 0.35)
for i in range(6):
    a = S5 + i * 2
    if i: e(a - 0.05, 'whoosh', 0.22)
    e(a + 0.45, 'pop', 0.3); e(a + 0.5, 'click', 0.18)
# what's next
e(S6 - 1.1, 'riser', 0.4); e(S6 - 0.02, 'impact', 0.6); e(S6 + 0.1, 'transition', 0.3)
for i in range(5): e(S6 + 1.3 + i * 0.32, 'pop', 0.22)
# outro
e(S7 - 1.1, 'riser', 0.4); e(S7 - 0.02, 'impact', 0.55); e(S7 + 1.3, 'whoosh', 0.25)
e(S7 + 2.2, 'impact', 0.75)
for i, d in enumerate((2.8, 3.05, 3.25)): e(S7 + d, 'click', 0.16)

fx = highpass(fx, 40)
mix = mus * 0.9 + fx * 0.95
# master: gentle bus compression + limiter, fade out
lvl = np.sqrt(np.convolve(mix ** 2, np.ones(2400) / 2400, 'same')) + 1e-6
gain = np.minimum(1, (0.22 / lvl) ** 0.35)
mix = mix * gain
mix = mix / np.max(np.abs(mix)) * 0.89
mix *= section_gain(T, [(0, 1), (END - 0.8, 1), (END, 0)])
st = np.stack([mix, np.roll(mix, 24) * 0.98], 1)          # a touch of width
out = sys.argv[1] if len(sys.argv) > 1 else 'score.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
print('wrote', out)
