"""Open web pages in a real browser and keep every large image they load.
python tools/grabimages.py out_dir name=url [name=url ...]   (a url ending in an image extension is downloaded directly)"""
import sys, os, asyncio, hashlib, re
from playwright.async_api import async_playwright
out = sys.argv[1]; jobs = [a.split('=', 1) for a in sys.argv[2:]]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 1600, 'height': 1000}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36')
        for name, url in jobs:
            d = os.path.join(out, name); os.makedirs(d, exist_ok=True); seen = set(); n = [0]
            pg = await ctx.new_page()
            async def keep(resp):
                try:
                    ct = resp.headers.get('content-type', '')
                    if not ct.startswith('image/') or 'svg' in ct or 'gif' in ct: return
                    body = await resp.body()
                    if len(body) < 60_000: return
                    h = hashlib.md5(body).hexdigest()[:10]
                    if h in seen: return
                    seen.add(h); n[0] += 1
                    ext = {'image/png': 'png', 'image/webp': 'webp', 'image/avif': 'avif'}.get(ct.split(';')[0], 'jpg')
                    open(os.path.join(d, f'{n[0]:03d}-{h}.{ext}'), 'wb').write(body)
                    open(os.path.join(d, 'sources.txt'), 'a').write(f'{n[0]:03d}-{h}.{ext} {resp.url}\n')
                except Exception: pass
            pg.on('response', lambda r: asyncio.ensure_future(keep(r)))
            try:
                await pg.goto(url, wait_until='load', timeout=60000)
                for _ in range(14):
                    await pg.mouse.wheel(0, 900); await pg.wait_for_timeout(700)
                await pg.wait_for_timeout(3000)
            except Exception as e: print(name, 'error', e)
            print(name, n[0], 'images', flush=True)
            await pg.close()
        await b.close()
asyncio.run(main())
