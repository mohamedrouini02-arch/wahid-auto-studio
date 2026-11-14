"""Edit decisions for the comeback video: which words stay, how they are written, where the cuts fall.
python edl.py  ->  timeline.json  (segments in source time, caption words in output time, word anchors)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
W = json.load(open(os.path.join(HERE, 'words.json')))
FPS = 30

DROP = set()
for a, b in [(56, 65), (73, 81), (97, 97), (100, 106), (141, 147), (222, 222), (242, 242), (251, 251), (253, 253), (256, 256),
             (262, 262), (272, 276), (285, 288), (324, 330), (337, 340), (8, 8), (172, 172)]:
    DROP.update(range(a, b + 1))
# words 8 and 172 are the second half of a word written as one ("كالعادة", "كابابل"): keep their sound, drop their text
SOUND_ONLY = {8, 172, 262}
FIX = {5: 'وحيد', 6: 'أوتو', 7: 'كالعادة', 12: 'الجديد', 13: 'خوتنا', 14: 'الشوروم', 20: 'لافامي', 22: 'وحيد', 23: 'أوتو',
       27: 'نشطناش', 29: 'في الريزو', 30: 'سوسيو', 33: 'خوتنا', 34: 'أنه', 36: 'أهم', 37: 'أكثر', 41: 'أي', 43: 'أخرى', 47: 'أحسن',
       87: 'إن', 110: 'تروا دي', 111: 'لكيفية', 119: 'يسهّل', 122: 'أقرب', 134: 'الولاية', 135: 'إن', 138: 'قريباً',
       149: 'كاينة', 150: 'ليزوفر', 163: 'أي', 164: 'أسعار', 171: 'كابابل', 175: 'أخرى', 178: 'راهي', 182: 'السيارات',
       183: 'تاع لاشين', 185: 'أي', 186: 'كاينة', 187: 'أمور', 192: 'لأنو', 199: 'أنو', 204: 'أنو', 207: 'يطيح', 208: 'لأنو',
       211: 'راهي', 212: 'تدخل', 215: 'الجديدة', 220: 'الموان دو', 221: 'تروا زون', 225: 'شامل', 228: 'أي', 231: 'يديره',
       235: 'راه', 240: 'زمان', 243: 'اليوم', 245: 'خوتنا؟', 248: 'نقولو', 250: 'نعطيك', 252: 'مثال', 255: 'الليفان',
       260: 'بـ 285', 261: 'مليون', 265: 'التكاليف', 267: 'كيف', 269: 'لـ إم', 271: 'فايف', 278: 'كولراي', 280: 'نقدر',
       283: 'بـ 310', 284: 'مليون', 291: 'التكاليف', 293: 'خوتنا', 295: 'ما ننساو', 296: 'أنها', 299: 'موان دو', 300: 'تروا زون',
       303: 'طاح', 305: 'طاحش', 307: 'ممكن', 311: 'السعر', 314: 'تبقى', 315: 'موان', 317: 'تروا زون', 320: 'ثلاث', 323: 'ما تبيع',
       332: 'إذا', 334: 'تاخذ', 343: 'خوتنا', 344: 'بسعر', 345: 'مرتفع', 347: 'هاذ', 348: 'السيارة', 350: 'هاذي', 354: 'نلعبو',
       357: 'الناس', 358: 'نجيو', 359: 'معاهم', 360: 'أون فاص', 361: 'نعطيوهم', 366: 'إكزاكتمون', 367: 'هذي', 368: 'خوتنا',
       370: 'منا', 373: 'وحيد', 374: 'أوتو', 376: 'الدائم', 379: 'والصينية', 380: 'سلام'}
AUDIO_DROP = DROP - SOUND_ONLY
# lines never run across these word starts (new thought)
BREAK_BEFORE = {5, 13, 20, 24, 31, 37, 44, 52, 66, 70, 82, 85, 90, 93, 107, 111, 114, 117, 122, 130, 135, 148, 153, 156, 161, 163, 169,
                174, 176, 180, 185, 189, 192, 198, 202, 208, 216, 223, 226, 232, 238, 244, 246, 250, 257, 260, 263, 266, 268, 277,
                280, 283, 289, 292, 296, 301, 304, 306, 312, 315, 318, 322, 331, 341, 344, 349, 351, 355, 358, 361, 364, 367, 369,
                373, 375, 377, 380}
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
if __name__ == '__main__':
    print('duration %.1f s, %d segments, %d lines' % (total, len(out), len(lines)))
    for l in lines: print('%6.2f  %s' % (l['t'], ' '.join(w['w'] for w in l['words'])))
