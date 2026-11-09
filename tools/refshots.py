"""Study a reference website: screenshots down the page (desktop + phone), a scroll recording, fonts and scripts.
python tools/refshots.py URL out_dir"""
import sys, asyncio, json
from playwright.async_api import async_playwright
url, out = sys.argv[1], sys.argv[2]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, vp, mob in (('desk', {'width': 1440, 'height': 900}, False), ('phone', {'width': 390, 'height': 844}, True)):
            ctx = await b.new_context(viewport=vp, device_scale_factor=1, is_mobile=mob, has_touch=mob,
                                      record_video_dir=f'{out}/vid-{name}', record_video_size=vp)
            pg = await ctx.new_page()
            await pg.goto(url, wait_until='load', timeout=90000); await pg.wait_for_timeout(7000)
            for sel in ['text=Reject all', 'text=Alle ablehnen', 'text=Accept all', '#onetrust-reject-all-handler', 'button:has-text("Reject")']:
                try: await pg.click(sel, timeout=1500); break
                except Exception: pass
            await pg.wait_for_timeout(1500)
            H = await pg.evaluate('document.documentElement.scrollHeight'); vh = vp['height']
            if name == 'desk':
                info = await pg.evaluate('''() => ({scripts:[...document.scripts].map(s=>s.src).filter(Boolean),
                  fonts:[...new Set([...document.querySelectorAll('h1,h2,h3,p,a,button')].map(e=>getComputedStyle(e).fontFamily+' | '+getComputedStyle(e).fontSize+' | '+getComputedStyle(e).fontWeight))].slice(0,30),
                  bg:getComputedStyle(document.body).backgroundColor, height:document.documentElement.scrollHeight,
                  sticky:[...document.querySelectorAll('*')].filter(e=>getComputedStyle(e).position==='sticky').map(e=>e.className).slice(0,20),
                  canvases:document.querySelectorAll('canvas').length, videos:[...document.querySelectorAll('video')].map(v=>v.currentSrc||v.src)})''')
                json.dump(info, open(f'{out}/info.json', 'w'), indent=1)
            # smooth scroll down (recorded), with stills every half screen
            y, i = 0, 0
            while y < H:
                await pg.mouse.wheel(0, vh * 0.5) if not mob else await pg.evaluate(f'window.scrollBy(0,{vh*0.5})')
                await pg.wait_for_timeout(900)
                await pg.screenshot(path=f'{out}/{name}-{i:03d}.jpg', quality=60, type='jpeg')
                y += vh * 0.5; i += 1
                H = await pg.evaluate('document.documentElement.scrollHeight')
                if i > 80: break
            await ctx.close()
        await b.close()
asyncio.run(main())
