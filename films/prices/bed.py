"""A calm music bed (warm pad, soft pulse) of the length asked:  python bed.py out.wav seconds"""
import sys, wave, numpy as np
out, dur = sys.argv[1], float(sys.argv[2])
SR = 44100; n = int(SR * dur); t = np.arange(n) / SR
f = lambda m: 440 * 2 ** ((m - 69) / 12)
CH = [[50, 57, 62, 66, 69, 73], [47, 54, 59, 62, 66, 69], [43, 50, 55, 59, 62, 66], [45, 52, 57, 62, 64, 69]]   # Dmaj7  Bm7  Gmaj7  Asus
BAR = 60 / 76 * 4; LEN = BAR * 2
L = np.zeros(n); R = np.zeros(n)
for k in range(int(dur / LEN) + 2):
    notes = CH[k % 4]; a = k * LEN
    env = np.clip((t - a + 1.2) / 2.4, 0, 1) * np.clip((a + LEN + 1.2 - t) / 2.4, 0, 1); env = env * env * (3 - 2 * env)
    if not env.any(): continue
    for j, m in enumerate(notes):
        g = 0.5 if j == 0 else 0.26
        for det, pan in ((-0.004, 0.25), (0.0, 0.5), (0.004, 0.75)):
            w = np.sin(2 * np.pi * f(m) * (1 + det) * t + j) + 0.18 * np.sin(4 * np.pi * f(m) * (1 + det) * t)
            w *= env * g * (1 + 0.12 * np.sin(2 * np.pi * 0.11 * t + j))
            L += w * (1 - pan); R += w * pan
    # soft pulse on the beat: root and fifth, an octave up
    for b in range(8):
        tb = a + b * BAR / 4; i0 = int(tb * SR)
        if i0 >= n: break
        seg = np.arange(min(int(0.9 * SR), n - i0)) / SR
        m = notes[0] + 12 + (7 if b % 2 else 0)
        p = np.sin(2 * np.pi * f(m) * seg) * np.exp(-seg * 7) * np.clip(seg / 0.008, 0, 1) * (0.5 if b % 4 == 0 else 0.3)
        L[i0:i0 + len(seg)] += p * 0.9; R[i0:i0 + len(seg)] += p * 0.9
x = np.stack([L, R], 1); x /= np.abs(x).max(); x *= 0.5
fade = np.clip(t / 1.5, 0, 1) * np.clip((dur - t) / 2.2, 0, 1); x *= fade[:, None]
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype('<i2').tobytes())
