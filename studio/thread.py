"""Jarvis <-> the Editor chat in the Wahid Auto app.

    python studio/thread.py show <thread>                  the conversation (+ attached cars, media links)
    python studio/thread.py say <thread> "text" [--video URL]... [--image URL]...
    python studio/thread.py say <thread> --file reply.txt [--video URL]
    python studio/thread.py status <thread> idle|working
"""
import datetime, json, os, sys, urllib.request

URL = os.environ.get('SUPABASE_URL', 'https://qtgvmqdvghvijfbacnza.supabase.co').rstrip('/')
KEY = os.environ['SUPABASE_SERVICE_KEY']
H = {'apikey': KEY, 'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}


def rest(method, path, body=None):
    req = urllib.request.Request(f'{URL}/rest/v1/{path}', method=method, headers={**H, 'Prefer': 'return=representation'},
                                 data=json.dumps(body).encode() if body is not None else None)
    return json.loads(urllib.request.urlopen(req).read() or b'null')


def car_line(cid):
    c = rest('GET', f'car_inventory?id=eq.{cid}&select=id,brand,model,year,mileage,color,selling_price,currency,video_url,photos_urls,notes,specs,features,condition,status')
    if not c: return f'(car {cid} not found)'
    c = c[0]
    return (f"CAR {c['id']}: {c['brand']} {c['model']} {c.get('year') or ''}, {c.get('mileage') or '?'} km, {c.get('color') or ''}, "
            f"price {c.get('selling_price')} {c.get('currency')}, video: {'yes' if c.get('video_url') else 'NO'}, "
            f"photos: {len(c.get('photos_urls') or [])}, specs {json.dumps(c.get('specs') or {}, ensure_ascii=False)}, "
            f"features {c.get('features') or []}, condition {json.dumps(c.get('condition') or {}, ensure_ascii=False)}, notes: {c.get('notes') or '-'}")


def show(tid):
    t = rest('GET', f'editor_threads?id=eq.{tid}&select=*')
    if not t: sys.exit('thread not found')
    print(f"THREAD {tid} — {t[0].get('title') or ''}")
    for m in rest('GET', f'editor_messages?thread_id=eq.{tid}&select=*&order=created_at'):
        who = 'MOHAMED' if m['role'] == 'user' else 'JARVIS'
        print(f"\n[{m['created_at'][:16]}] {who}:")
        if m.get('car_id'): print('  ' + car_line(m['car_id']))
        for x in m.get('media') or []: print(f"  {x['type'].upper()}: {x['url']}  ({x.get('name') or ''})")
        if m.get('text'): print('  ' + m['text'].replace('\n', '\n  '))


def say(tid, args):
    media, text, i = [], [], 0
    while i < len(args):
        a = args[i]
        if a in ('--video', '--image'): media.append({'type': a[2:], 'url': args[i + 1]}); i += 2
        elif a == '--file': text.append(open(args[i + 1], encoding='utf-8').read().strip()); i += 2
        else: text.append(a); i += 1
    rest('POST', 'editor_messages', {'thread_id': tid, 'role': 'agent', 'text': '\n'.join(text) or None, 'media': media})
    rest('PATCH', f'editor_threads?id=eq.{tid}', {'updated_at': datetime.datetime.utcnow().isoformat() + 'Z'})
    print('sent')


def status(tid, s):
    rest('PATCH', f'editor_threads?id=eq.{tid}', {'status': s})


if __name__ == '__main__':
    cmd, tid = sys.argv[1], sys.argv[2]
    {'show': lambda: show(tid), 'say': lambda: say(tid, sys.argv[3:]), 'status': lambda: status(tid, sys.argv[3])}[cmd]()
