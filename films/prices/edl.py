"""Edit decisions for the comeback video: which words stay, how they are written, where the cuts fall.
python edl.py  ->  timeline.json  (segments in source time, caption words in output time, word anchors)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
W = json.load(open(os.path.join(HERE, 'words.json')))
FPS = 30

# fillers ("اه") and the repeated "تروح" go; numbers said in words keep their sound but show once as digits
DROP = {122, 149, 163, 173}
SOUND_ONLY = {76, 77, 94, 95, 110, 111, 124, 136, 138, 161, 162, 88}
DROP |= SOUND_ONLY
FIX = {5: 'وحيد', 6: 'أوتو', 7: 'كالعادة', 8: 'مع', 9: 'الخدمة', 10: 'ومع', 11: 'الجديد', 14: 'اللي', 15: 'ما يعرفش',
       16: 'وحيد', 17: 'أوتو', 18: 'وحيد', 19: 'أوتو', 23: 'بتصدير', 31: 'أيام', 33: 'درنا', 37: 'أنه', 42: 'بأرخص', 43: 'الأسعار',
       52: 'الأسعار', 54: 'نبداكم', 58: 'بأربع', 65: 'نبداو', 68: 'بواط', 69: 'مانيال', 72: 'راهي', 73: 'دايرة', 75: '275',
       79: 'ما زيد', 82: 'نروحو', 83: 'للسيارة', 84: 'رقم 2', 85: 'إم', 86: 'جي', 93: '275', 96: 'إذا', 99: 'أقل', 104: 'كاينة',
       105: 'الروي', 106: 'آي', 109: '275', 123: 'للدار', 125: 'نروحو', 128: 'أربعة', 131: 'الجيلي', 135: 'درنالها',
       137: '310', 139: 'كأحسن', 143: 'الأربع', 145: 'رانا', 152: 'ابتداءً', 156: 'إن', 160: 'نعلمكم', 166: 'آخر', 168: 'أسعار',
       170: 'الأخرى', 183: 'وحيد', 184: 'أوتو', 185: 'مرافقكم'}
AUDIO_DROP = DROP - SOUND_ONLY
BREAK_BEFORE = {5, 12, 14, 18, 22, 30, 36, 42, 47, 53, 58, 65, 70, 72, 79, 82, 85, 89, 96, 102, 105, 108, 113, 116, 121, 125, 129,
                131, 133, 139, 141, 145, 150, 156, 159, 167, 171, 174, 180, 183, 187, 189}
PRE, POST, MAXGAP = 0.07, 0.12, 0.42

def q(t): return round(t * FPS) / FPS

# 1. segments of source time to keep
segs, cur = [], None
for i, w in enumerate(W):
    if i in AUDIO_DROP:
        cur = None; continue
    s, e = w['start'], w['end']
    nxt = next((W[j]['start'] for j in range(i + 1, len(W))), e + 1)
    e = min(e + POST, nxt)                       # never run into the next word
    s = max(s - PRE, W[i - 1]['end'] if i else 0)
    if cur is not None and s - cur[1] <= MAXGAP:
        cur[1] = e; cur[2].append(i)
    else:
        cur = [s, e, [i]]; segs.append(cur)
segs[-1][1] = W[-1]['end'] + 0.45
out, t = [], 0.0
for s, e, idx in segs:
    s, e = q(s), q(e)
    if e - s < 2 / FPS: continue
    out.append({'src': [s, e], 'out': round(t, 4), 'words': idx}); t = round(t + (e - s), 4)
total = t

def to_out(src_t):
    for g in out:
        if g['src'][0] - 1e-6 <= src_t <= g['src'][1] + 1e-6: return round(g['out'] + src_t - g['src'][0], 3)
    prev = [g for g in out if g['src'][1] < src_t]
    return round(prev[-1]['out'] + prev[-1]['src'][1] - prev[-1]['src'][0], 3) if prev else 0.0

# 2. caption words and lines (output time)
anchors, cw = {}, []
for g in out:
    for i in g['words']:
        anchors[i] = to_out(W[i]['start'])
        if i in DROP: continue
        cw.append({'i': i, 't': to_out(W[i]['start']), 'e': to_out(min(W[i]['end'], g['src'][1])), 'w': FIX.get(i, W[i]['w'].strip('.?،, '))})
lines, cur = [], []
def flush():
    global cur
    if cur: lines.append({'t': cur[0]['t'], 'e': cur[-1]['e'], 'words': [{'t': w['t'], 'w': w['w']} for w in cur]})
    cur = []
for k, w in enumerate(cw):
    prev = cw[k - 1] if k else None
    chars = sum(len(x['w']) for x in cur) + len(cur)
    if cur and (w['i'] in BREAK_BEFORE or len(cur) >= 4 or chars + len(w['w']) > 21 or (prev and w['t'] - prev['e'] > 0.5) or (prev and w['i'] != prev['i'] + 1 and prev['i'] + 1 not in SOUND_ONLY)):
        flush()
    cur.append(w)
flush()
k = 1
while k < len(lines):                            # no one-word orphan lines when they fit on the line before
    a, b = lines[k - 1], lines[k]
    if len(b['words']) == 1 and b['t'] - a['words'][-1]['t'] < 1.3 and sum(len(w['w']) + 1 for w in a['words']) + len(b['words'][0]['w']) <= 27:
        a['words'] += b['words']; a['e'] = b['e']; lines.pop(k)
    else: k += 1
for a, b in zip(lines, lines[1:]):               # a line stays up until the next one, but not across a long pause
    a['e'] = b['t'] if b['t'] - a['e'] < 0.6 else a['e'] + 0.25
lines[-1]['e'] += 0.3
cuts = [g['out'] for g in out[1:]]
json.dump({'fps': FPS, 'duration': total, 'segments': [{'src': g['src'], 'out': g['out']} for g in out], 'cuts': cuts,
           'lines': lines, 'anchors': anchors}, open(os.path.join(HERE, 'timeline.json'), 'w'), ensure_ascii=False, indent=0)
open(os.path.join(HERE, 'timeline.js'), 'w').write('window.TL = ' + open(os.path.join(HERE, 'timeline.json')).read() + ';')
if __name__ == '__main__':
    print('duration %.1f s, %d segments, %d lines' % (total, len(out), len(lines)))
    for l in lines: print('%6.2f  %s' % (l['t'], ' '.join(w['w'] for w in l['words'])))
