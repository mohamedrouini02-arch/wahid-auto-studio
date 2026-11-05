"""Edit for raw walk-around videos where someone films the car and talks.

The person's voice drives the edit (El Hadj Kia style):
  * the clip plays in order with its own sound; only long silences are cut out
  * what he says is transcribed, and when he names a feature its neon label pops up
  * every label is tracked on the footage (optical flow), so it stays on the car
  * logo intro before, end card with the numbers after
"""
import json, os, re, subprocess
import numpy as np

FPS = 30
INTRO = 1.4
W, H = 1080, 1920

# what he may say -> label (French as in the videos, Arabic subtitle)
KEYWORDS = [
    (['كاميرا', 'كامرا', 'camera', 'caméra'], 'CAMÉRA DE RECUL', 'كاميرا'),
    (['شاشة', 'شاشه', 'ecran', 'écran', 'تاكتيل', 'tactile'], 'ÉCRAN TACTILE', 'شاشة'),
    (['جي بي اس', 'جيبياس', 'gps', 'نافيڨاسيون', 'navigation'], 'GPS', 'جي بي إس'),
    (['كاربلاي', 'carplay', 'android auto', 'أندرويد'], 'CARPLAY / ANDROID AUTO', 'كاربلاي'),
    (['فولون', 'فولان', 'volant', 'المقود', 'ستيرينغ'], 'VOLANT MULTIFONCTION', 'الفولون'),
    (['كليم', 'clim', 'مكيف', 'كليماتيزور', 'climatisation'], 'CLIMATISATION', 'الكليم'),
    (['جلد', 'cuir', 'كوير'], 'SIÈGES EN CUIR', 'كراسي جلد'),
    (['شوفون', 'chauffant', 'مدفأ'], 'SIÈGES CHAUFFANTS', 'شوفون'),
    (['فونتيلي', 'ventilé', 'مبردة'], 'SIÈGES VENTILÉS', 'فونتيلي'),
    (['كراسي', 'سياج', 'siège', 'sieges', 'سيج'], 'SIÈGES', 'الكراسي'),
    (['تو ڨوفرون', 'toit ouvrant', 'سقف', 'بانوراميك', 'panoramique'], 'TOIT OUVRANT', 'السقف'),
    (['جونط', 'جنط', 'jante', 'jantes'], 'JANTES EN ALLIAGE', 'الجونط'),
    (['فار', 'فارات', 'phare', 'led', 'ليد'], 'PHARES LED', 'الفارات'),
    (['مالبقاج', 'كوفر', 'coffre', 'الصندوق'], 'COFFRE', 'المالبقاج'),
    (['أوتوماتيك', 'اوتوماتيك', 'automatique', 'اوطوماتيك', 'بوات', 'boite', 'boîte'], 'BOÎTE AUTOMATIQUE', 'أوتوماتيك'),
    (['ديماراج', 'demarrage', 'démarrage', 'ستارت', 'start'], 'DÉMARRAGE SANS CLÉ', 'ديماراج'),
    (['ريغولاتور', 'regulateur', 'régulateur', 'مثبت السرعة'], 'RÉGULATEUR DE VITESSE', 'ريغولاتور'),
    (['رادار', 'radar', 'كابتور', 'capteur'], 'RADARS DE STATIONNEMENT', 'رادارات'),
    (['موتور', 'moteur', 'محرك', 'تيربو', 'turbo'], 'MOTEUR', 'الموتور'),
    (['كوكبيت', 'cockpit', 'العداد', 'كادران'], 'COCKPIT', 'العدادات'),
    (['صبغة', 'صبغه', 'peinture', 'بانتير', 'لمعاود'], 'PEINTURE', 'الصبغة'),
    (['شارجور', 'wireless', 'وايرلس', 'لاسلكي'], 'CHARGEUR WIRELESS', 'شاحن'),
]


def norm(s):
    s = s.lower()
    s = re.sub('[إأآا]', 'ا', s)
    s = re.sub('ة', 'ه', s)
    return s


def transcribe(path, model_size='medium'):
    from faster_whisper import WhisperModel
    m = WhisperModel(model_size, device='cpu', compute_type='int8')
    segs, _ = m.transcribe(path, language='ar', word_timestamps=True, vad_filter=True)
    words = []
    for s in segs:
        for w in (s.words or []):
            words.append({'start': float(w.start), 'end': float(w.end), 'w': w.word.strip()})
    return words


def has_speech(words, length):
    return len(words) / max(length, 1) > 0.6


def keep_ranges(words, length, max_gap=1.1, pad=0.3):
    """Parts of the clip to keep: all speech, with long silences shortened (jump cuts)."""
    if not words:
        return [(0.0, length)]
    ranges, s, e = [], max(0.0, words[0]['start'] - pad), words[0]['end']
    for w in words[1:]:
        if w['start'] - e > max_gap:
            ranges.append((s, min(length, e + pad))); s = max(0.0, w['start'] - pad)
        e = w['end']
    ranges.append((s, min(length, e + pad)))
    return ranges


def find_labels(words, car):
    """Labels at the moments he names things. Returns [(source_time, title, sub, arabic)]."""
    out, last = [], {}
    feats_fr = set(car.get('features_fr') or [])
    text = [(w['start'], norm(w['w'])) for w in words]
    for i, (t, w) in enumerate(text):
        two = w + ' ' + (text[i + 1][1] if i + 1 < len(text) else '')
        for keys, fr, ar in KEYWORDS:
            if any(norm(k) in two for k in keys):
                if fr == 'MOTEUR' and car.get('engine_label'): fr = car['engine_label']
                if fr == 'PEINTURE' and car.get('paint_label'): fr, ar = car['paint_label'], car.get('paint_ar', ar)
                if fr == 'SIÈGES' and 'SIÈGES EN CUIR' in feats_fr: fr = 'SIÈGES EN CUIR'
                if t - last.get(fr, -99) > 8:
                    out.append((t, fr, '', ar)); last[fr] = t
                break
        if re.search(r'\d', w) or 'كيلو' in w or 'km' in w:
            if ('كيلو' in two or 'km' in two) and car.get('km_label') and t - last.get('km', -99) > 8:
                out.append((t, car['km_label'], '', 'كيلومتر')); last['km'] = t
        if 'مليون' in two and car.get('price_label') and t - last.get('price', -99) > 8:
            out.append((t, car['price_label'], '', 'السعر')); last['price'] = t
    # keep them readable: at least 2.4 s apart
    spaced = []
    for item in sorted(out):
        if not spaced or item[0] - spaced[-1][0] >= 2.4:
            spaced.append(item)
    return spaced


def track(frames_dir, src_w, src_h, f0, f1, anchor):
    """Follow a point on the footage from frame f0 to f1 (Lucas-Kanade on corners around it)."""
    import cv2
    files = sorted(os.listdir(frames_dir))
    f1 = min(f1, len(files) - 1)
    small = 540.0 / src_w
    def load(i):
        g = cv2.imread(os.path.join(frames_dir, files[i]), cv2.IMREAD_GRAYSCALE)
        return cv2.resize(g, (540, int(g.shape[0] * 540 / g.shape[1])))
    prev = load(f0)
    ax, ay = anchor[0] * small, anchor[1] * small
    mask = np.zeros_like(prev); r = 80
    mask[max(0, int(ay - r)):int(ay + r), max(0, int(ax - r)):int(ax + r)] = 255
    pts = cv2.goodFeaturesToTrack(prev, 40, 0.01, 6, mask=mask)
    path = [(anchor[0], anchor[1])]
    for i in range(f0 + 1, f1 + 1):
        cur = load(i)
        if pts is not None and len(pts) >= 4:
            nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, cur, pts, None, winSize=(21, 21), maxLevel=3)
            good = st.reshape(-1) == 1
            if good.sum() >= 4:
                d = np.median((nxt[good] - pts[good]).reshape(-1, 2), axis=0)
                ax, ay = ax + d[0], ay + d[1]
                pts = nxt[good].reshape(-1, 1, 2)
            else:
                pts = None
        if pts is None or len(pts) < 8:   # re-seed around the current anchor
            mask = np.zeros_like(cur)
            mask[max(0, int(ay - r)):int(ay + r), max(0, int(ax - r)):int(ax + r)] = 255
            pts = cv2.goodFeaturesToTrack(cur, 40, 0.01, 6, mask=mask)
        path.append((ax / small, ay / small))
        prev = cur
    return path


def best_anchor(frames_dir, frame_index, side):
    """A textured point on the car near the middle of the frame, on one side."""
    import cv2
    files = sorted(os.listdir(frames_dir))
    g = cv2.imread(os.path.join(frames_dir, files[min(frame_index, len(files) - 1)]), cv2.IMREAD_GRAYSCALE)
    h, w = g.shape
    x0, x1 = (int(w * .2), int(w * .5)) if side == 0 else (int(w * .5), int(w * .8))
    mask = np.zeros_like(g); mask[int(h * .35):int(h * .65), x0:x1] = 255
    p = cv2.goodFeaturesToTrack(g, 1, 0.01, 10, mask=mask)
    if p is None: return ((x0 + x1) / 2, h / 2)
    return tuple(p.reshape(2))


def screen_xform(src_w, src_h):
    cover = max(W / src_w, H / src_h) * 1.02
    iw, ih = src_w * cover, src_h * cover
    return cover, W / 2 - iw / 2, H / 2 - ih / 2


def plan(video, words, car, shot_index=0):
    """Timeline + labels + sound events for a talking video. `video` is the prepared media entry."""
    length = video['length']
    ranges = keep_ranges(words, length)
    labels = find_labels(words, car)
    cover, ox, oy = screen_xform(video['w'], video['h'])
    tl, sfx, t = [], [], INTRO
    frames_dir = video['_abs_dir']
    side = 0
    for (a, b) in ranges:
        e = {'t0': round(t, 3), 't1': round(t + (b - a), 3), 'shot': shot_index, 'from': a, 'fx': []}
        if not tl:
            e['hook'] = True
            e['fx'].append({'kind': 'title', 's': car['brand'].upper(), 't': car['model'].upper(), 'x': 50, 'y': 28, 'at': 0.2, 'dur': 2.6})
        for (st, fr, sub, ar) in labels:
            if not (a <= st < b - 0.8): continue
            dur = min(2.8, b - st - 0.1)
            f0 = int(st * FPS); f1 = int((st + dur) * FPS)
            anc = best_anchor(frames_dir, f0, side); side ^= 1
            path = track(frames_dir, video['w'], video['h'], f0, f1, anc)
            screen = [[round(ox + x * cover, 1), round(oy + y * cover - 140, 1)] for x, y in path]
            e['fx'].append({'kind': 'neon', 't': fr, 's': sub, 'a': ar, 'at': round(st - a, 3), 'dur': dur,
                            'track': screen, 'ry': -14 if side else 14})
            sfx.append((e['t0'] + st - a, 'pop', 0.6))
        tl.append(e)
        t += b - a
    sfx += [(0.0, 'riser', 0.45), (0.15, 'whoosh', 0.35), (INTRO - 0.02, 'impact', 0.6), (t - 0.25, 'whoosh', 0.45),
            (t + 0.62, 'impact', 0.35)]
    return {'tl': tl, 'hookEnd': INTRO, 'bodyEnd': round(t, 3), 'priceEnd': round(t, 3), 'total': round(t + 3.2, 3),
            'marks': [], 'ranges': ranges}, sfx


def speech_track(src, ranges, out):
    """The person's voice: kept parts joined, cleaned and levelled."""
    parts = ''.join(f'[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[a{i}];' for i, (a, b) in enumerate(ranges))
    cat = ''.join(f'[a{i}]' for i in range(len(ranges))) + f'concat=n={len(ranges)}:v=0:a=1[c];'
    chain = '[c]highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=8:release=150,loudnorm=I=-15:TP=-1.5[o]'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-filter_complex', parts + cat + chain, '-map', '[o]',
                    '-ac', '1', '-ar', '44100', out], check=True)
    return out
