"""Upload a finished video to Supabase storage and tell the app.

    python studio/publish.py <car_id> <video.mp4>            new edit (no voice yet)
    python studio/publish.py <car_id> <video.mp4> --voiced   final video with Wahid's voice
    python studio/publish.py <car_id> --failed
"""
import datetime, json, os, sys, urllib.request

URL = os.environ['SUPABASE_URL'].rstrip('/')
KEY = os.environ['SUPABASE_SERVICE_KEY']
H = {'apikey': KEY, 'Authorization': f'Bearer {KEY}'}


def call(method, path, body=None, headers=None):
    req = urllib.request.Request(URL + path, data=body, method=method, headers={**H, **(headers or {})})
    return urllib.request.urlopen(req).read()


def set_fields(car_id, **fields):
    call('PATCH', f'/rest/v1/car_inventory?id=eq.{car_id}', json.dumps(fields).encode(),
         {'Content-Type': 'application/json', 'Prefer': 'return=minimal'})


def upload(car_id, path, suffix):
    stamp = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
    key = f'videos/{car_id}-{stamp}{suffix}.mp4'
    call('POST', f'/storage/v1/object/car-media/{key}', open(path, 'rb').read(), {'Content-Type': 'video/mp4', 'x-upsert': 'true'})
    return f'{URL}/storage/v1/object/public/car-media/{key}'


if __name__ == '__main__':
    car_id = sys.argv[1]
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    if sys.argv[2] == '--failed':
        set_fields(car_id, social_video_status='failed')
    elif '--voiced' in sys.argv:
        set_fields(car_id, social_video_url=upload(car_id, sys.argv[2], '-voice'), social_video_status='ready', social_video_at=now)
    else:
        url = upload(car_id, sys.argv[2], '')
        script_file = sys.argv[2][:-4] + '-script.json'
        script = json.load(open(script_file)) if os.path.exists(script_file) else None
        set_fields(car_id, social_video_url=url, social_video_silent_url=url, social_video_script=script,
                   social_video_status='ready', social_video_at=now)
    print('ok')
