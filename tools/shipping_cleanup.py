"""Back up, then delete, every shipping form and its files (the app no longer uses shipping forms).

  python tools/shipping_cleanup.py backup OUT_DIR   # forms.json + every file they reference
  python tools/shipping_cleanup.py delete OUT_DIR   # only after a backup in OUT_DIR: delete files (not used by sales) and rows
"""
import json, os, re, sys, urllib.request, urllib.error, urllib.parse

URL = os.environ.get('SUPABASE_URL', 'https://qtgvmqdvghvijfbacnza.supabase.co').rstrip('/')
KEY = os.environ['SUPABASE_SERVICE_KEY']
H = {'apikey': KEY, 'Authorization': f'Bearer {KEY}'}
PUB = re.compile(r'/storage/v1/object/public/([^/]+)/([^?]+)')


def api(method, path, body=None, raw=False):
    h = dict(H)
    if body is not None: h['Content-Type'] = 'application/json'
    req = urllib.request.Request(URL + path, method=method, headers=h, data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
        return data if raw else (json.loads(data) if data else None)


def rows(table, select='*'):
    out, step = [], 1000
    while True:
        h = dict(H, Range=f'{len(out)}-{len(out) + step - 1}')
        req = urllib.request.Request(f'{URL}/rest/v1/{table}?select={select}&order=id', headers=h)
        with urllib.request.urlopen(req, timeout=120) as r: page = json.loads(r.read())
        out += page
        if len(page) < step: return out


def urls_of_form(f):
    us = [f.get('pdf_url'), f.get('passport_photo_url'), f.get('id_card_url'), f.get('id_card_back_url')]
    v = f.get('vehicle_photos_urls')
    if isinstance(v, str) and v.strip().startswith('['):
        try: us += json.loads(v)
        except Exception: pass
    elif isinstance(v, list): us += v
    return [u for u in us if isinstance(u, str) and u]


def urls_of_sale(t):
    us = [t.get('passport_photo_url'), t.get('id_card_url'), t.get('id_card_back_url')] + list(t.get('vehicle_photos_urls') or [])
    return {u for u in us if isinstance(u, str) and u}


def backup(out):
    os.makedirs(f'{out}/files', exist_ok=True)
    forms = rows('shipping_forms')
    json.dump(forms, open(f'{out}/forms.json', 'w'), ensure_ascii=False, indent=1)
    ok = miss = 0
    for f in forms:
        for u in urls_of_form(f):
            m = PUB.search(u)
            if not m: continue
            bucket, path = m.group(1), urllib.parse.unquote(m.group(2))
            dest = f'{out}/files/{bucket}/{path}'
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            try:
                open(dest, 'wb').write(api('GET', f'/storage/v1/object/{bucket}/{urllib.parse.quote(path)}', raw=True)); ok += 1
            except urllib.error.HTTPError:
                miss += 1
    json.dump({'forms': len(forms), 'files': ok, 'missing': miss}, open(f'{out}/summary.json', 'w'))
    print(f'backup: {len(forms)} forms, {ok} files saved, {miss} already missing', flush=True)


def delete(out):
    s = json.load(open(f'{out}/summary.json'))
    forms = json.load(open(f'{out}/forms.json'))
    assert s['forms'] == len(forms) and len(forms) > 0, 'no backup'
    keep = set()
    for t in rows('financial_transactions', 'passport_photo_url,id_card_url,id_card_back_url,vehicle_photos_urls'):
        keep |= urls_of_sale(t)
    files, kept = {}, 0
    for f in forms:
        for u in urls_of_form(f):
            if u in keep: kept += 1; continue
            m = PUB.search(u)
            if m: files.setdefault(m.group(1), set()).add(urllib.parse.unquote(m.group(2)))
    gone = 0
    for bucket, paths in files.items():
        paths = sorted(paths)
        for i in range(0, len(paths), 100):
            res = api('DELETE', f'/storage/v1/object/{bucket}', {'prefixes': paths[i:i + 100]}) or []
            gone += len(res)
    ids = [str(f['id']) for f in forms]
    for i in range(0, len(ids), 100):
        api('DELETE', '/rest/v1/shipping_forms?id=in.(' + ','.join(ids[i:i + 100]) + ')')
    left = len(rows('shipping_forms', 'id'))
    print(f'deleted: {len(ids)} forms, {gone} files removed, {kept} kept (used by sales); forms left: {left}', flush=True)


if __name__ == '__main__':
    {'backup': backup, 'delete': delete}[sys.argv[1]](sys.argv[2])
