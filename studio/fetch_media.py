"""Get the footage the editor was given into a local file.

    python studio/fetch_media.py <source> <out_path>

<source> can be:
  * a car id (uuid) from the app            -> its raw video (car_inventory.video_url)
  * car:<uuid>:photos                       -> all its photos into <out_path>/ (a folder)
  * a Supabase storage path / public URL    -> e.g. videos/abc.mp4
  * a GitHub issue attachment URL           -> downloaded with the repo token
  * a Google Drive share link               -> needs "anyone with the link"
  * any direct http(s) link to a file
"""
import json, os, re, subprocess, sys, urllib.request

SB = os.environ.get('SUPABASE_URL', 'https://qtgvmqdvghvijfbacnza.supabase.co').rstrip('/')
KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


def public(path):
    return path if path.startswith('http') else f'{SB}/storage/v1/object/public/car-media/{path.lstrip("/")}'


def car(car_id):
    req = urllib.request.Request(f'{SB}/rest/v1/car_inventory?id=eq.{car_id}&select=*', headers={'apikey': KEY, 'Authorization': f'Bearer {KEY}'})
    rows = json.load(urllib.request.urlopen(req))
    if not rows: sys.exit(f'car {car_id} not found')
    return rows[0]


def download(url, out, headers=None):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    cmd = ['curl', '-fsSL', '--retry', '3', '-o', out]
    for k, v in (headers or {}).items(): cmd += ['-H', f'{k}: {v}']
    subprocess.run(cmd + [url], check=True)
    return out


def main(src, out):
    if src.startswith('car:') and src.endswith(':photos'):
        c = car(src.split(':')[1]); os.makedirs(out, exist_ok=True)
        for i, p in enumerate(c.get('photos_urls') or []):
            download(public(p), os.path.join(out, f'{i:02d}.jpg'))
        print(out); return
    if UUID.match(src):
        c = car(src)
        if not c.get('video_url'): sys.exit('this car has no video in the app')
        download(public(c['video_url']), out); print(out); return
    m = re.search(r'drive\.google\.com/(?:file/d/|open\?id=|uc\?id=)([\w-]+)', src)
    if m:
        download(f'https://drive.usercontent.google.com/download?id={m.group(1)}&export=download&confirm=t', out); print(out); return
    if 'github.com/user-attachments' in src or 'githubusercontent.com' in src:
        tok = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN', '')
        download(src, out, {'Authorization': f'token {tok}'} if tok else None); print(out); return
    download(public(src), out); print(out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
