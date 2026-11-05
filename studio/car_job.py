"""Build a video job from a car in the app's database.

    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python studio/car_job.py <car_id> jobs/auto/<car_id>.json

The script follows Wahid's way of talking (greeting, the car, "from the real
ground", WhatsApp, goodbye) and fills it with the car's own data.
"""
import json, os, sys, urllib.request

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
LOCATION = {'korea': 'في كوريا', 'china': 'في الصين', 'algeria': 'في الجزائر'}
LOCATION_LABEL = {'korea': 'من كوريا', 'china': 'من الصين', 'algeria': 'في الجزائر'}


def say_name(text):
    t = (text or '').strip().lower()
    return NAMES.get(t, ' '.join(NAMES.get(w, w) for w in t.split()))


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
    price = car.get('selling_price') if car.get('show_price_on_website') else None
    photos = [p for p in (car.get('photos_urls') or []) if p]
    video = car.get('video_url')

    media = [{'src': p, 'move': mv} for p, mv in zip(photos, ['pull', 'pan', 'push', 'pan', 'pull', 'push', 'push', 'pull', 'push', 'pull', 'pan', 'push'] * 3)]
    V = None
    if video:
        media.append({'src': video, 'type': 'video'}); V = len(media) - 1
    P = list(range(len(photos))) or ([V] if V is not None else [])

    def pick(i): return P[i % len(P)]

    def vid(frac):  # a moment in the walk-around, as a fraction of its length (resolved by the renderer)
        return {'m': V, 'frac': frac}

    title = f'{brand} {model}'.upper().strip()
    millions = round(float(price) / 10000) if price else None
    chips = []
    if km: chips.append(f'{int(km):,} KM'.replace(',', '.'))
    chips.append('{KR} → {DZ}' if loc != 'china' else '{CN} → {DZ}')

    line_car = f'{say_name(brand)} {say_name(model)}'
    if year: line_car += f'، موديل {words(year)}'
    if color: line_car += f'، لونها {color}'
    line_where = (LOCATION.get(loc, '') and f'راهي {LOCATION[loc]}') or 'السيارة جاهزة'
    if km: line_where += f'، العداد تاعها {words(round(int(km) / 1000) * 1000)} كيلو'

    script = [
        {'kind': 'hook', 'say': 'السلام عليكم خوتنا. وحيد أوتو، كالعادة مع الجديد.',
         'shots': [vid(0.08), pick(0)] if V is not None else [pick(0), pick(1)]},
        {'say': line_car + '.', 'shots': [vid(0.25), pick(1)] if V is not None else [pick(1), pick(2)],
         'label': [say_name(model) or say_name(brand), str(year or '')]},
        {'say': line_where + '.', 'shots': [pick(2), pick(3)],
         'label': [LOCATION_LABEL.get(loc, ''), chips[0] if km else '']},
        {'say': 'كيما راكم تشوفوا، الداخل والخارج، كلشي واضح.',
         'shots': [vid(0.5), vid(0.68), vid(0.84)] if V is not None else [pick(4), pick(5), pick(6)]},
        {'say': 'الصور والفيديو من أرض الواقع. كلشي بالشفافية.', 'shots': [pick(5), pick(6)] if V is not None else [pick(7), pick(8)],
         'label': ['من أرض الواقع', '']},
        ({'kind': 'price', 'say': f'السعر: {words(millions)} مليون.'} if millions else
         {'say': 'للسعر، راسلونا على الواتساب.', 'shots': [pick(2)], 'label': ['السعر', 'WHATSAPP']}),
        {'kind': 'end', 'say': 'المهتم، تواصل معانا عبر الواتساب. مع السلامة.'},
    ]
    return {
        'car': {'title': title, 'year': str(year or ''), 'priceMillions': millions,
                'priceDa': f'{int(float(price)):,} DA'.replace(',', '.') if price else 'راسلونا',
                'ticker': ' · '.join(x for x in [title, str(year or ''), chips[0] if km else ''] if x),
                'chips': chips},
        'voice': {'name': 'ar-DZ-IsmaelNeural', 'rate': '+12%'},
        'priceShot': pick(2),
        'media': media,
        'script': script,
    }


if __name__ == '__main__':
    job = build(fetch_car(sys.argv[1]))
    os.makedirs(os.path.dirname(os.path.abspath(sys.argv[2])), exist_ok=True)
    json.dump(job, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
    print(sys.argv[2])
