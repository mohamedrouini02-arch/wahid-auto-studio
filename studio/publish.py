"""Upload the finished video to Supabase storage and tell the app it is ready.

    python studio/publish.py <car_id> <video.mp4>
    python studio/publish.py <car_id> --failed
"""
import datetime, json, os, sys, urllib.request

URL = os.environ['SUPABASE_URL'].rstrip('/')
KEY = os.environ['SUPABASE_SERVICE_KEY']
H = {'apikey': KEY, 'Authorization': f'Bearer {KEY}'}


def call(method, path, body=None, headers=None):
    req = urllib.request.Request(URL + path, data=body, method=method, headers={**H, **(headers or {})})
    return urllib.request.urlopen(req).read()


def set_status(car_id, **fields):
    call('PATCH', f'/rest/v1/car_inventory?id=eq.{car_id}', json.dumps(fields).encode(),
         {'Content-Type': 'application/json', 'Prefer': 'return=minimal'})


car_id = sys.argv[1]
if sys.argv[2] == '--failed':
    set_status(car_id, social_video_status='failed')
    sys.exit(0)
stamp = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')
path = f'videos/{car_id}-{stamp}.mp4'
call('POST', f'/storage/v1/object/car-media/{path}', open(sys.argv[2], 'rb').read(),
     {'Content-Type': 'video/mp4', 'x-upsert': 'true'})
public = f'{URL}/storage/v1/object/public/car-media/{path}'
set_status(car_id, social_video_url=public, social_video_status='ready',
           social_video_at=datetime.datetime.utcnow().isoformat() + 'Z')
print(public)
