"""Design the sound-effect kit (writes studio/sfx/*.wav).

Built to be soft and short, the way modern car-reel edits use them: a sound
supports the graphic, it never covers the voice. Each sound has a quick
attack, no harsh highs (everything above ~9 kHz is rolled off) and a small
room tail so it sits in the mix instead of sounding like a beep.

    python studio/make_sfx.py
"""
import os, wave
import numpy as np

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sfx')
rng = np.random.default_rng(7)


def t_(sec): return np.arange(int(sec * SR)) / SR


def lowpass(x, hz):
    s = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    s *= 1 / np.sqrt(1 + (f / hz) ** 8)
    return np.fft.irfft(s, len(x))


def highpass(x, hz):
    s = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    s *= 1 / np.sqrt(1 + (hz / np.maximum(f, 1)) ** 8)
    return np.fft.irfft(s, len(x))


def band(x, lo, hi): return lowpass(highpass(x, lo), hi)


def pink(n):
    s = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / SR)
    s /= np.sqrt(np.maximum(f, 20)); x = np.fft.irfft(s, n)
    return x / np.abs(x).max()


def room(x, size=0.18, mix=0.18):
    """Tiny plate-like tail: a few decaying noise taps convolved in."""
    n = int(size * SR); ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (n / 5))
    ir = lowpass(ir, 6000); ir /= np.abs(ir).sum() / 4
    wet = np.convolve(x, ir)[: len(x) + n]
    wet = np.pad(wet, (0, len(x) + n - len(wet)))
    dry = np.concatenate([x, np.zeros(n)])
    return dry * (1 - mix) + wet * mix


def fade(x, a=0.002, r=0.02):
    a, r = int(a * SR), int(r * SR); x = x.copy()
    x[:a] *= np.linspace(0, 1, a); x[-r:] *= np.linspace(1, 0, r)
    return x


def norm(x, peak_db): return x / np.abs(x).max() * 10 ** (peak_db / 20)


def save(name, x):
    os.makedirs(OUT, exist_ok=True)
    x = np.clip(x, -1, 1)
    with wave.open(os.path.join(OUT, f'{name}.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def whoosh():
    # air moving past: pink noise through a band that sweeps up then down, swelling in the middle
    t = t_(0.55); n = len(t); u = t / t[-1]
    noise = pink(n); out = np.zeros(n)
    centers = 500 + 2600 * np.sin(np.pi * u) ** 1.5
    for k in range(0, n, 1200):  # short-time filtering so the band can move
        seg = noise[k:k + 2400]
        c = centers[min(k + 600, n - 1)]
        out[k:k + len(seg)] += band(seg, c * 0.5, c * 1.6) * np.hanning(len(seg))
    env = np.sin(np.pi * u) ** 2.2
    return norm(fade(room(out * env, 0.25, 0.2)), -10)


def cut():
    # soft "thump-swish" for cuts inside a part: low tap + a breath of air
    t = t_(0.18)
    thump = np.sin(2 * np.pi * (90 + 60 * np.exp(-t * 40)) * t) * np.exp(-t * 28)
    air = band(pink(len(t)), 1500, 6000) * np.exp(-t * 35) * 0.25
    return norm(fade(room(thump + air, 0.12, 0.12)), -14)


def pop():
    # rounded bubble pop: pitch falls fast, no click, warm
    t = t_(0.12)
    f = 260 + 700 * np.exp(-t * 55)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)
    x = lowpass(x, 3500)
    return norm(fade(room(x, 0.1, 0.12), 0.003, 0.03), -12)


def click():
    # small UI tick: two very short damped partials, low level
    t = t_(0.05)
    x = (np.sin(2 * np.pi * 1800 * t) + 0.5 * np.sin(2 * np.pi * 3100 * t)) * np.exp(-t * 160)
    return norm(fade(lowpass(x, 7000), 0.001, 0.01), -18)


def impact():
    # deep cinematic hit: sub drop + body + short noise crack, with a room tail
    t = t_(1.2)
    sub = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-t * 14)) / SR) * np.exp(-t * 3.2)
    body = np.sin(2 * np.pi * 110 * t) * np.exp(-t * 12) * 0.35
    crack = band(pink(len(t)), 300, 4000) * np.exp(-t * 30) * 0.35
    return norm(fade(room(sub + body + crack, 0.4, 0.22), 0.001, 0.2), -6)


def riser():
    # build-up into the price: rising filtered noise + rising soft tone, ends just before the hit
    t = t_(1.1); u = t / t[-1]; n = len(t)
    noise = pink(n); out = np.zeros(n)
    for k in range(0, n, 1200):
        seg = noise[k:k + 2400]; c = 400 + 5000 * u[min(k, n - 1)] ** 2
        out[k:k + len(seg)] += band(seg, c * 0.6, c * 1.4) * np.hanning(len(seg))
    tone = np.sin(2 * np.pi * np.cumsum(180 + 520 * u ** 2) / SR) * 0.18
    x = (out + tone) * u ** 2.4
    return norm(fade(x, 0.05, 0.03), -12)


def transition():
    # longer swoosh with a low tail for the switch to the price screen
    w = whoosh(); t = t_(len(w) / SR)
    tail = np.sin(2 * np.pi * 60 * t) * np.exp(-((t - 0.3) ** 2) / 0.02) * 0.3
    return norm(fade(w + tail[: len(w)]), -9)


if __name__ == '__main__':
    import sys
    keep_real = '--all' not in sys.argv  # the recorded swooshes from the Premiere Composer pack stay
    for name, fn in [('whoosh', whoosh), ('cut', cut), ('pop', pop), ('click', click),
                     ('impact', impact), ('riser', riser), ('transition', transition)]:
        if keep_real and name in ('whoosh', 'transition') and os.path.exists(os.path.join(OUT, f'{name}.wav')):
            continue
        save(name, fn()); print('wrote', name)
