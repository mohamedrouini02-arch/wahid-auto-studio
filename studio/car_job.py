"""Build a video job from a car in the app's database.

    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python studio/car_job.py <car_id> jobs/auto/<car_id>.json

The script follows Wahid's way of talking (greeting, the car, "from the real
ground", WhatsApp, goodbye) and fills it with the car's own data.
"""
import json, os, random, subprocess, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ONES = ['', 'واحد', 'اثنين', 'ثلاثة', 'أربعة', 'خمسة', 'ستة', 'سبعة', 'ثمانية', 'تسعة']
TEENS = ['عشرة', 'حداش', 'طناش', 'طلطاش', 'ربعطاش', 'خمسطاش', 'سطاش', 'سبعطاش', 'ثمنطاش', 'تسعطاش']
TENS = ['', '', 'عشرين', 'ثلاثين', 'أربعين', 'خمسين', 'ستين', 'سبعين', 'ثمانين', 'تسعين']
HUNDREDS = ['', 'مية', 'ميتين', 'ثلاث مية', 'ربع مية', 'خمس مية', 'ست مية', 'سبع مية', 'ثمن مية', 'تسع مية']


def under_1000(n):
    h, r = divmod(n, 100)
    parts = [HUNDREDS[h]] if h else []
    if r:
        if r < 10: parts.append(ONES[r])
        elif r < 20: parts.append(TEENS[r - 10])
        else:
            t, o = divmod(r, 10)
            parts.append(f'{ONES[o]} و{TENS[t]}' if o else TENS[t])
    return ' و'.join(parts)


def words(n):
    """Algerian way of saying a number: 2022 -> ألفين واثنين وعشرين, 58000 -> ثمانية وخمسين ألف."""
    n = int(n)
    if n == 0: return 'صفر'
    th, r = divmod(n, 1000)
    parts = []
    if th:
        if th == 1: parts.append('ألف')
        elif th == 2: parts.append('ألفين')
        elif th <= 10: parts.append(f'{under_1000(th)} آلاف')
        else: parts.append(f'{under_1000(th)} ألف')
    if r: parts.append(under_1000(r))
    return ' و'.join(parts)


NAMES = {
    'kia': 'كيا', 'hyundai': 'هيونداي', 'renault': 'رونو', 'chevrolet': 'شفروليه', 'geely': 'جيلي', 'chery': 'شيري',
    'ssangyong': 'سانغ يونغ', 'kgm': 'كي جي إم', 'genesis': 'جينيسيس', 'samsung': 'سامسونغ', 'byd': 'بي واي دي',
    'morning': 'مورنينغ', 'picanto': 'بيكانتو', 'ray': 'راي', 'k3': 'كي ثري', 'k5': 'كي فايف', 'k8': 'كي إيت',
    'seltos': 'سيلتوس', 'sportage': 'سبورتاج', 'sorento': 'سورينتو', 'carnival': 'كرنفال', 'niro': 'نيرو', 'stonic': 'ستونيك',
    'avante': 'أفانتي', 'elantra': 'إلنترا', 'sonata': 'سوناتا', 'tucson': 'توسان', 'santa fe': 'سانتافي', 'kona': 'كونا',
    'casper': 'كاسبر', 'venue': 'فينيو', 'palisade': 'باليسيد', 'grandeur': 'غرانجور', 'staria': 'ستاريا',
    'arkana': 'أركانا', 'xm3': 'إكس إم ثري', 'qm6': 'كيو إم سيكس', 'koleos': 'كوليوس', 'spark': 'سبارك', 'trax': 'تراكس',
    'trailblazer': 'تريلبلايزر', 'coolray': 'كولراي', 'torres': 'توريس', 'tivoli': 'تيفولي',
}
FEATURES = {  # key: (label in the video, Arabic for the script, where it is seen)
    'volant_multi': ('VOLANT MULTIFONCTION', 'مقود متعدد الوظائف', 'dash'), 'camera': ('CAMÉRA DE RECUL', 'كاميرا دريكيل', 'rear'),
    'radars': ('RADARS DE STATIONNEMENT', 'رادارات', 'rear'), 'ecran': ('ÉCRAN TACTILE', 'شاشة تاكتيل', 'gear'),
    'carplay': ('CARPLAY / ANDROID AUTO', 'كاربلاي', 'gear'), 'gps': ('GPS', 'جي بي إس', 'gear'), 'cockpit': ('COCKPIT DIGITAL', 'كوكبيت ديجيتال', 'dash'),
    'clim_auto': ('CLIMATISATION AUTO', 'الكليم أوتو', 'gear'), 'keyless': ('DÉMARRAGE SANS CLÉ', 'ديماراج بلا كلي', 'dash'),
    'regulateur': ('RÉGULATEUR DE VITESSE', 'ريغولاتور', 'dash'), 'regulateur_adaptatif': ('RÉGULATEUR ADAPTATIF', 'ريغولاتور أدابتاتيف', 'dash'),
    'maintien_voie': ('MAINTIEN DE VOIE', 'مانتيان دو فوا', 'dash'), 'angles_morts': ('DÉTECTION ANGLES MORTS', 'كشف الأنغل مور', 'side'),
    'sieges_cuir': ('SIÈGES EN CUIR', 'كراسي جلد', 'seats'), 'sieges_chauffants': ('SIÈGES CHAUFFANTS', 'كراسي شوفون', 'seats'),
    'sieges_ventiles': ('SIÈGES VENTILÉS', 'كراسي فونتيلي', 'seats'), 'sieges_electriques': ('SIÈGES ÉLECTRIQUES', 'كراسي إلكتريك', 'seats'),
    'volant_chauffant': ('VOLANT CHAUFFANT', 'فولون شوفون', 'dash'), 'toit_ouvrant': ('TOIT OUVRANT', 'تو ڨوفرون', 'seats'),
    'toit_pano': ('TOIT PANORAMIQUE', 'تو بانوراميك', 'seats'), 'wireless': ('CHARGEUR WIRELESS', 'شارجور وايرلس', 'gear'),
    'palettes': ('PALETTES AU VOLANT', 'باليت في الفولون', 'dash'), 'phares_led': ('PHARES LED', 'فارات LED', 'front'),
    'jantes': ('JANTES EN ALLIAGE', 'جونط ألمنيوم', 'side'), 'retros_rabattables': ('RÉTROS RABATTABLES', 'روترو رابتابل', 'side'),
    'coffre_electrique': ('COFFRE ÉLECTRIQUE', 'مالبقاج إلكتريك', 'trunk'),
}
FUELS = {'essence': ('ESSENCE', 'ليسونس'), 'diesel': ('DIESEL', 'مازوت'), 'hybride': ('HYBRIDE', 'هيبريد'), 'electrique': ('ÉLECTRIQUE', 'إلكتريك'), 'gpl': ('GPL', 'سيرغاز')}
GENERIC = {'dash': ('TABLEAU DE BORD', 'الطابلو'), 'gear': ('CONSOLE CENTRALE', 'الكونسول'), 'seats': ('SIÈGES AVANT', 'الكراسي'),
           'rearseats': ('SIÈGES ARRIÈRE', 'الكراسي اللورانيين'), 'trunk': ('COFFRE', 'المالبقاج')}
GEARBOXES = {'auto': ('BOÎTE AUTOMATIQUE', 'أوتوماتيك'), 'manuelle': ('BOÎTE MANUELLE', 'مانويل')}
PANELS = {'capot': ('Capot', 'الكابو'), 'toit': ('Toit', 'السقف'), 'coffre': ('Coffre', 'المالبقاج'), 'pc_av': ('Pare-choc AV', 'البارشوك القدامي'),
    'pc_ar': ('Pare-choc AR', 'البارشوك اللوراني'), 'aile_avg': ('Aile AV G', 'الجناح القدامي اليسار'), 'aile_avd': ('Aile AV D', 'الجناح القدامي اليمين'),
    'aile_arg': ('Aile AR G', 'الجناح اللوراني اليسار'), 'aile_ard': ('Aile AR D', 'الجناح اللوراني اليمين'), 'porte_avg': ('Porte AV G', 'الباب القدامي اليسار'),
    'porte_avd': ('Porte AV D', 'الباب القدامي اليمين'), 'porte_arg': ('Porte AR G', 'الباب اللوراني اليسار'), 'porte_ard': ('Porte AR D', 'الباب اللوراني اليمين')}
LOCATION = {'korea': 'في كوريا', 'china': 'في الصين', 'algeria': 'في الجزائر'}
LOCATION_LABEL = {'korea': 'من كوريا', 'china': 'من الصين', 'algeria': 'في الجزائر'}


def say_name(text):
    t = (text or '').strip().lower()
    return NAMES.get(t, ' '.join(NAMES.get(w, w) for w in t.split()))


def talking_job(car, video, words):
    specs = car.get('specs') or {}
    cond = car.get('condition') or {}
    price = car.get('selling_price') if not (car.get('specs') or {}).get('video_hide_price') and (car.get('selling_price') or 0) > 0 else None   # app switch: show price in the video
    km = car.get('mileage')
    paint = [PANELS[p][0] for p in (cond.get('paint') or []) if p in PANELS]
    talk = {
        'brand': (car.get('brand') or '').strip(), 'model': (car.get('model') or '').strip(),
        'km_label': f'{int(km):,} KM'.replace(',', '.') if km else None,
        'price_label': f'{round(float(price) / 10000)} MILLIONS' if price else None,
        'engine_label': ' '.join(b for b in [specs.get('engine') or '', FUELS.get(specs.get('fuel', ''), ('',))[0]] if b) or None,
        'paint_label': ('ZÉRO PEINTURE' if cond and not cond.get('paint') and not cond.get('replaced') else ('PEINTURE: ' + ', '.join(paint)) if paint else None),
        'paint_ar': 'زيرو صبغة' if cond and not cond.get('paint') else '',
        'features_fr': [FEATURES[f][0] for f in (car.get('features') or []) if f in FEATURES],
    }
    millions = round(float(price) / 10000) if price else None
    return {'mode': 'talking', 'style': STYLE, 'voice': None, 'talk': talk, 'words': words,
            'car': {'title': f"{talk['brand']} {talk['model']}".upper(), 'year': str(car.get('year') or ''), 'priceMillions': millions,
                    'priceDa': f'{int(float(price)):,} DA'.replace(',', '.') if price else '', 'ticker': '', 'chips': []},
            'media': [{'src': video, 'type': 'video'}], 'script': []}


STYLE = os.environ.get('VIDEO_STYLE') or 'clean'   # clean (default) | neon | classic


def fetch_car(car_id):
    url = os.environ['SUPABASE_URL'].rstrip('/') + f'/rest/v1/car_inventory?id=eq.{car_id}&select=*'
    key = os.environ['SUPABASE_SERVICE_KEY']
    req = urllib.request.Request(url, headers={'apikey': key, 'Authorization': f'Bearer {key}'})
    rows = json.load(urllib.request.urlopen(req))
    if not rows: sys.exit(f'car {car_id} not found')
    return rows[0]


def build(car):
    brand, model = (car.get('brand') or '').strip(), (car.get('model') or '').strip()
    year, km, color = car.get('year'), car.get('mileage'), (car.get('color') or '').strip()
    loc = (car.get('location') or '').lower()
    price = car.get('selling_price') if not (car.get('specs') or {}).get('video_hide_price') and (car.get('selling_price') or 0) > 0 else None   # app switch: show price in the video
    photos = [p for p in (car.get('photos_urls') or []) if p]
    video = car.get('video_url')

    # a raw walk-around where someone talks: keep his voice and build the edit around it
    if video:
        import tempfile, talking
        tmpv = os.path.join(tempfile.mkdtemp(), 'v.mp4'); urllib.request.urlretrieve(video, tmpv)
        words = talking.transcribe(tmpv)
        length = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', tmpv],
                                      capture_output=True, text=True).stdout.strip() or 0)
        if talking.has_speech(words, length):
            return talking_job(car, video, words)

    # look at the media and decide which shot goes where
    from pick_shots import analyse, best, video_runs, EXTERIOR
    a = analyse(photos, video)
    MOVE = {'front34': 'pull', 'front': 'push', 'side': 'pan', 'rear': 'pull', 'dash': 'push', 'gear': 'push',
            'seats': 'pull', 'rearseats': 'pull', 'trunk': 'push'}
    media, P = [], {}
    for i, kind, _ in a['photos']:
        if kind in ('door', 'other'): continue
        P[i] = len(media); media.append({'src': photos[i], 'move': MOVE.get(kind, 'push'), 'kind': kind})
    good = [(P[i], k, sc) for i, k, sc in a['photos'] if i in P]
    V = None
    if video:
        media.append({'src': video, 'type': 'video'}); V = len(media) - 1
    used = set()

    def photos_of(kinds, n):
        return [m for m, _, _ in best(good, kinds, used, n)]

    def clips_of(kinds, n):  # steady moments of the walk-around showing these kinds
        if V is None: return []
        runs = video_runs(a['video'], set(kinds))
        return [{'m': V, 'at': float(st + max(0, ln - 2.6) / 2)} for st, ln in runs[:n]]

    def shots(video_kinds, photo_kinds, n):
        out = clips_of(video_kinds, 1) if video_kinds else []
        out += photos_of(photo_kinds, n - len(out))
        if not out: out = [m for m, _, _ in good[:n]] or ([{'m': V, 'at': 0.0}] if V is not None else [0])
        return out

    hook = shots(['front34', 'front'], ['front34', 'front', 'side'], 2)
    s_car = shots(['side'], ['side', 'front34', 'front'], 2)
    s_where = shots(['rear'], ['rear', 'side'], 2)
    s_inside = shots(['dash', 'gear'], ['dash', 'gear', 'seats'], 3)
    s_real = shots(['seats', 'rearseats'], ['rearseats', 'trunk', 'seats'], 2)
    price_bg = next((m for m, k, _ in good if k in ('front34', 'front')), good[0][0] if good else 0)

    title = f'{brand} {model}'.upper().strip()
    millions = round(float(price) / 10000) if price else None
    chips = []
    if km: chips.append(f'{int(km):,} KM'.replace(',', '.'))
    chips.append('{KR} → {DZ}' if loc != 'china' else '{CN} → {DZ}')
    specs = car.get('specs') or {}
    feats = [f for f in (car.get('features') or []) if f in FEATURES]
    cond = car.get('condition') or None

    # every remake picks other phrasings, so videos don't all sound the same
    rnd = random.Random(f"{car.get('id')}-{os.environ.get('GITHUB_RUN_ID', '')}")
    pick1 = rnd.choice
    name = f'{say_name(brand)} {say_name(model)}'.strip()
    yr = f'موديل {words(year)}' if year else ''
    col = f'اللون {color}' if color else ''
    line_car = pick1([
        f'اليوم جبنالكم {name}، {yr}، {col}.',
        f'هاد المرة عندنا {name}، {yr}، {col}.',
        f'سيارة اليوم خاوتنا: {name}، {yr}، {col}.',
        f'عندنا {name} {yr}، {col}، ربي بارك.',
    ]).replace('، ،', '،').replace(' ،', '،')

    eng_bits = [specs.get('engine') or '', FUELS.get(specs.get('fuel', ''), ('', ''))[1]]
    eng = ' '.join(b for b in eng_bits if b).strip()
    box = GEARBOXES.get(specs.get('gearbox', ''), ('', ''))[1]
    line_engine = None
    if eng or box:
        line_engine = pick1([
            f'تجي بموتور {eng}' + (f'، وبوات {box}.' if box else '.'),
            f'الموتور {eng}' + (f'، والبوات {box}.' if box else '.'),
            (f'بوات {box}، ' if box else '') + f'موتور {eng}.',
        ]) if eng else f'البوات {box}.'

    km_words = f'{words(round(int(km) / 1000) * 1000)} كيلومتر' if km else ''
    where = LOCATION.get(loc, '')
    line_where = pick1([
        f'العداد فيه {km_words} برك، والسيارة راهي {where}.',
        f'{km_words} برك، وراهي حاليا {where}.',
        f'السيارة راهي {where}، والكيلومترات: {km_words}.',
    ]) if km and where else (f'السيارة راهي {where}.' if where else None)

    feat_ar = [FEATURES[f][1] for f in feats]
    line_feats = None
    if feat_ar:
        top = feat_ar[:4]
        joined = '، '.join(top[:-1]) + (f' و{top[-1]}' if len(top) > 1 else top[0])
        line_feats = pick1([f'فيها {joined}.', f'من بين المميزات: {joined}.', f'كاين {joined}، وزيد بزاف حوايج.'])

    line_cond = None
    if cond and (cond.get('paint') is not None):
        paint, repl = cond.get('paint') or [], cond.get('replaced') or []
        if not paint and not repl:
            line_cond = pick1(['زيرو صبغة، زيرو تبديل.', 'الحالة نقية: لا صبغة لا تبديل.', 'لا صبغة، لا تبديل، ربي بارك.'])
        else:
            parts = []
            if paint: parts.append('فيها صبغة في ' + '، '.join(PANELS[p][1] for p in paint if p in PANELS))
            if repl: parts.append('وتبدل ' + '، '.join(PANELS[p][1] for p in repl if p in PANELS))
            line_cond = 'بالصراحة، ' + ' '.join(parts) + '، وكلشي واضح في الفيديو.'

    line_trust = pick1(['كلشي من أرض الواقع مباشرة.', 'الصور والفيديو حقيقيين، كيما راكم تشوفو.', 'الشفافية قبل كلشي.', 'وحيد أوتو، الصدق والمصداقية.'])
    line_price = pick1([f'السعر: {words(millions)} مليون.', f'السعر خاوتنا {words(millions)} مليون.', f'دايرينلها {words(millions)} مليون.']) if millions else None
    line_end = pick1([
        'للمهتم، تواصل معانا على الواتساب، الأرقام في أسفل الفيديو.',
        'اللي حاب يحجزها، الأرقام موجودين، راسلونا على الواتساب.',
        'للحجز والمعلومات، الواتساب مفتوح، الأرقام في الفيديو.',
    ]) + ' والسلام عليكم ورحمة الله وبركاته.'

    # El Hadj–style neon labels, placed on the shots that show the thing they name
    sides = [(32, 46, 16), (68, 52, -16), (36, 60, 14), (64, 40, -14)]
    def neon(j, t, sub='', ar='', at=0.3):
        x, y, ry = sides[j % len(sides)]
        return {'on': j, 'kind': 'neon', 't': t, 's': sub, 'a': ar, 'x': x, 'y': y, 'ry': ry, 'at': at}

    s_inside_all = s_inside + photos_of(['seats', 'rearseats', 'trunk'], 2)
    def kind_of(spec):
        if isinstance(spec, dict): return 'dash'
        return media[spec].get('kind', '')
    inside_fx, left = [], list(feats)
    for j, spec in enumerate(s_inside_all):
        k = kind_of(spec)
        want = [f for f in left if FEATURES[f][2] == k] or left
        if want:
            f = want[0]; left.remove(f)
            inside_fx.append(neon(j, FEATURES[f][0], ar=FEATURES[f][1]))
        elif k in GENERIC:   # no features filled in yet: name what the shot shows
            inside_fx.append(neon(j, GENERIC[k][0], ar=GENERIC[k][1]))

    script = [
        {'kind': 'hook', 'say': 'السلام عليكم ورحمة الله وبركاته. وحيد أوتو، كالعادة مع الخدمة ومع الجديد.', 'shots': hook, 'min': 4.6,
         'fx': [{'on': 0, 'kind': 'title', 's': brand.upper(), 't': model.upper(), 'x': 50, 'y': 30, 'at': 1.5},
                {'on': 0, 'kind': 'ground', 't': (specs.get('version') or str(year or '')).upper(), 'x': 50, 'y': 88, 'at': 2.3, 'size': 150}]
                + ([{'on': 1 if len(hook) > 1 else 0, 'kind': 'neon', 't': chips[0], 's': color.upper() if color.isascii() else '', 'a': '' if color.isascii() else color, 'x': 50, 'y': 58, 'ry': -12, 'at': 0.3}] if km else [])},
        {'say': line_car, 'shots': s_car, 'fx': [neon(0, title, ar=color)]},
    ]
    if line_engine:
        script.append({'say': line_engine, 'shots': s_where[:1] or s_car[:1],
                       'fx': [neon(0, ' '.join(b for b in [specs.get('engine') or '', FUELS.get(specs.get('fuel', ''), ('',))[0]] if b) or 'MOTEUR',
                                   sub=GEARBOXES.get(specs.get('gearbox', ''), ('',))[0])]})
    if line_where:
        script.append({'say': line_where, 'shots': s_where[1:] or s_where, 'fx': [neon(0, chips[0] if km else '', ar=LOCATION_LABEL.get(loc, ''))]})
    line_inside = pick1(['ندخلو للداخل، كما راكم تشوفو.', 'هذا هو الداخل تاعها، شوفو معايا.', 'نشوفو الداخل مع بعض.'])
    script.append({'say': line_feats or line_inside, 'shots': s_inside_all, 'fx': inside_fx})
    if line_cond:
        clean = not (cond.get('paint') or cond.get('replaced'))
        script.append({'say': line_cond, 'shots': s_real[:1] or s_car[:1], 'fx': [neon(0, 'ZÉRO PEINTURE' if clean else 'ÉTAT DE LA CARROSSERIE',
                       sub='ZÉRO CHANGEMENT' if clean else ', '.join(PANELS[p][0] for p in (cond.get('paint') or []) + (cond.get('replaced') or []) if p in PANELS)[:60],
                       ar='زيرو صبغة' if clean else '')]})
    else:
        script.append({'say': line_trust, 'shots': s_real, 'fx': []})
    script.append({'kind': 'price', 'say': line_price or 'للسعر، راسلونا على الواتساب.'})   # price hidden -> "price on WhatsApp" screen
    script.append({'kind': 'end', 'say': line_end})
    return {
        'car': {'title': title, 'year': str(year or ''), 'priceMillions': millions,
                'priceDa': f'{int(float(price)):,} DA'.replace(',', '.') if price else 'راسلونا',
                'ticker': ' · '.join(x for x in [title, str(year or ''), chips[0] if km else ''] if x),
                'chips': chips},
        # no synthetic voice: the lines below are the script Wahid reads (see script.txt)
        'voice': None,
        'style': STYLE,
        'priceShot': price_bg,
        'analysis': {'photos': a['photos'], 'video': a['video']},
        'media': media,
        'script': script,
    }


if __name__ == '__main__':
    job = build(fetch_car(sys.argv[1]))
    os.makedirs(os.path.dirname(os.path.abspath(sys.argv[2])), exist_ok=True)
    json.dump(job, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    lines = [b['say'] for b in job['script'] if b.get('say')]
    open(os.path.splitext(sys.argv[2])[0] + '-script.txt', 'w').write('\n'.join(lines) + '\n')
    print(sys.argv[2])
