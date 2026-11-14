"""Record the home page journey on a phone as numbered frames (for use inside videos).
python tools/sitecap.py http://localhost:4173 out_dir [frames]"""
import sys, asyncio, json
from playwright.async_api import async_playwright
url, out = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 240
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=1.25, is_mobile=True, has_touch=True, locale='ar')
        pg = await ctx.new_page()
        await pg.goto(url, wait_until='load', timeout=90000); await pg.wait_for_timeout(4000)
        info = await pg.evaluate("() => { const j = document.querySelector('.jh'); const r = j.getBoundingClientRect(); return { top: r.top + scrollY, h: r.height, H: document.documentElement.scrollHeight, lang: document.documentElement.lang } }")
        print(json.dumps(info))
        top, end = info['top'], info['top'] + info['h'] - 844
        for i in range(N):
            u = i / (N - 1); e = 2 * u * u if u < .5 else 1 - (-2 * u + 2) ** 2 / 2
            y = top if i == 0 else top + (end - top) * (0.25 * e + 0.75 * u)
            await pg.evaluate('y => window.scrollTo(0, y)', y)
            await pg.wait_for_timeout(500 if i < 3 else 80)
            await pg.screenshot(path=f'{out}/s{i:03d}.jpg', quality=78, type='jpeg')
        await pg.evaluate('window.scrollTo(0, 0)'); await pg.wait_for_timeout(800)
        await pg.screenshot(path=f'{out}/top.jpg', quality=85, type='jpeg')
        await b.close()
asyncio.run(main())
