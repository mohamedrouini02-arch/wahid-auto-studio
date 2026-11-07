import asyncio, subprocess, sys, os
from playwright.async_api import async_playwright
C = os.path.dirname(os.path.abspath(__file__)) + '/comeback'
FPS = 60
async def main(mode, arg, out):
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=['--force-color-profile=srgb'])
        pg = await b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        pg.on('pageerror', lambda e: print('ERR', e))
        pg.on('console', lambda m: m.type == 'error' and print('CONSOLE', m.text))
        await pg.goto('http://localhost:8770/index.html')
        await pg.wait_for_function('window.ready === true', timeout=30000, polling=100)
        if mode == 'stills':
            times = sorted(float(x) for x in arg.split(','))
            n = round(max(times) * FPS); want = {round(x * FPS): x for x in times}
            for i in range(n + 1):
                await pg.evaluate(f'render({i / FPS})')
                if i in want:
                    await pg.screenshot(path=f'{out}/s_{want[i]:05.2f}.jpg', type='jpeg', quality=88)
        else:
            dur = float(arg); n = round(dur * FPS)
            ff = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                                   '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
            for i in range(n):
                await pg.evaluate(f'render({i / FPS})')
                ff.stdin.write(await pg.screenshot(type='jpeg', quality=94))
                if i % 300 == 0: print('frame', i, '/', n, flush=True)
            ff.stdin.close(); ff.wait()
        await b.close()
asyncio.run(main(*sys.argv[1:4]))
