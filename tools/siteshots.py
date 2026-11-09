"""Screenshots of the website build at given scroll positions: desktop + phone, Arabic + French.
python tools/siteshots.py http://localhost:4173 out_dir "0,0.5,1,1.6,2.4"   (positions in screen heights)
SHOT_PATHS="/,/cars" shoots several pages (files prefixed with the page name); SHOT_ANCHOR starts the
positions at an element; SHOT_WAIT is the pause before each shot in ms."""
import sys, asyncio, os
from playwright.async_api import async_playwright

url, out, pos = sys.argv[1], sys.argv[2], [float(x) for x in sys.argv[3].split(',')]
anchor = os.environ.get('SHOT_ANCHOR', '')
wait = int(os.environ.get('SHOT_WAIT', '4000'))
paths = [p.strip() for p in os.environ.get('SHOT_PATHS', '/').split(',') if p.strip()] or ['/']


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for path in paths:
            tag = '' if path == '/' else path.strip('/').replace('/', '_') + '-'
            for name, vp, mob in (('desk', {'width': 1440, 'height': 900}, False), ('phone', {'width': 390, 'height': 844}, True)):
                for lang in ('ar', 'fr'):
                    ctx = await b.new_context(viewport=vp, device_scale_factor=1, is_mobile=mob, has_touch=mob)
                    pg = await ctx.new_page()
                    await pg.add_init_script(f"sessionStorage.setItem('wa-loaded','1');localStorage.setItem('wahid-auto-lang','{lang}')")
                    await pg.goto(url + path, wait_until='networkidle')
                    await pg.wait_for_timeout(5000)
                    for y in pos:
                        await pg.evaluate(f"(() => {{ const a = document.querySelector('{anchor}' || 'html'); const top = a ? a.getBoundingClientRect().top + scrollY : 0; window.scrollTo(0, top + {y} * innerHeight) }})()")
                        await pg.wait_for_timeout(wait)
                        await pg.screenshot(path=f"{out}/{tag}{name}-{lang}-{y}.jpg", quality=70, type='jpeg')
                    await ctx.close()
        await b.close()

asyncio.run(main())
