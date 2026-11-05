"""Hand a finished edit to Wahid Auto.

    python studio/deliver.py <video.mp4> <name> [--car <uuid>]

Uploads to Supabase (public link that plays on any phone and shares to WhatsApp)
and prints the link. With --car it also becomes that car's final video in the app.
"""
import datetime, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from publish import URL, call, set_fields

path, name = sys.argv[1], re.sub(r'[^\w-]+', '-', sys.argv[2]).strip('-').lower() or 'edit'
size = os.path.getsize(path) / 1e6
if size > 49: sys.exit(f'{size:.0f} MB is over the 50 MB upload limit: re-encode smaller first')
stamp = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
key = f'videos/agent/{name}-{stamp}.mp4'
call('POST', f'/storage/v1/object/car-media/{key}', open(path, 'rb').read(), {'Content-Type': 'video/mp4', 'x-upsert': 'true'})
link = f'{URL}/storage/v1/object/public/car-media/{key}'
if '--car' in sys.argv:
    car_id = sys.argv[sys.argv.index('--car') + 1]
    set_fields(car_id, social_video_url=link, social_video_status='ready', social_video_at=datetime.datetime.utcnow().isoformat() + 'Z')
print(link)
