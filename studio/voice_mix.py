"""Put Wahid's recorded voice-over on the car's edit (no re-render needed).

    python studio/voice_mix.py <silent_video_url> <voice_url> out.mp4

The voice was recorded in the app while the edit played, so it is already in
sync. The voice is cleaned (low rumble cut, noise reduced, levelled) and the
edit's sound effects are lowered under it.
"""
import subprocess, sys, tempfile, os, urllib.request

video, voice, out = sys.argv[1:4]
tmp = tempfile.mkdtemp()
v = os.path.join(tmp, 'v.mp4'); a = os.path.join(tmp, 'voice.in')
urllib.request.urlretrieve(video, v); urllib.request.urlretrieve(voice, a)
offset = os.environ.get('VOICE_OFFSET', '0')  # seconds to shift the voice if needed
voice_chain = ('highpass=f=90,lowpass=f=12000,afftdn=nf=-28,acompressor=threshold=-20dB:ratio=3:attack=8:release=120,'
               'loudnorm=I=-14:TP=-1.5:LRA=9')
flt = (f'[1:a]{voice_chain},adelay={int(float(offset) * 1000)}|{int(float(offset) * 1000)},asplit=2[vo][key];'
       '[0:a]volume=0.8[fx];[fx][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[duck];'
       '[duck][vo]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', v, '-i', a, '-filter_complex', flt,
                '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
                '-movflags', '+faststart', out], check=True)
print(out)
