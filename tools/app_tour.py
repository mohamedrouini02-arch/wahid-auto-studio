"""Screen-record the Wahid Auto app as a branch-office user (Tebessa), for a tutorial video.

  python tools/app_tour.py setup      # temporary demo account (office tebessa) + 2 demo entries
  python tools/app_tour.py record BASE_URL OUT_DIR
  python tools/app_tour.py cleanup    # deletes everything the demo account added, then the account

Each scene is its own phone-size video (OUT_DIR/<scene>.webm) and OUT_DIR/steps.json lists, per scene,
the moments (seconds from the start of that video) where something happens, for the captions.
Never prints the password; it only lives in /tmp/demo.json on the runner.
"""
import asyncio, json, os, secrets, sys, time, uuid
import urllib.request, urllib.error

URL = os.environ.get('SUPABASE_URL', 'https://qtgvmqdvghvijfbacnza.supabase.co').rstrip('/')
EMAIL = 'demo.tebessa@wahid-auto.com'
STATE = '/tmp/demo.json'
DEMO_VIN = 'DEMO0TEBESSA00001'


def api(method, path, body=None, prefer=None):
    key = os.environ['SUPABASE_SERVICE_KEY']
    h = {'apikey': key, 'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    if prefer: h['Prefer'] = prefer
    req = urllib.request.Request(URL + path, method=method, headers=h, data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            t = r.read().decode()
            return json.loads(t) if t else None
    except urllib.error.HTTPError as e:
        raise SystemExit(f'{method} {path.split("?")[0]} -> {e.code} {e.read().decode()[:300]}')


def find_user():
    for page in range(1, 6):
        users = api('GET', f'/auth/v1/admin/users?page={page}&per_page=200').get('users', [])
        for u in users:
            if (u.get('email') or '').lower() == EMAIL: return u['id']
        if len(users) < 200: return None


def cleanup():
    uid = find_user()
    if not uid: print('no demo account'); return
    forms = api('GET', f'/rest/v1/shipping_forms?added_by=eq.{uid}&select=pdf_url') or []
    files = [f['pdf_url'].split('/object/public/shipping/')[-1] for f in forms if f.get('pdf_url') and '/object/public/shipping/' in f['pdf_url']]
    if files: api('DELETE', '/storage/v1/object/shipping', {'prefixes': files})
    for t in ('shipping_forms', 'financial_transactions', 'orders', 'car_inventory'):
        api('DELETE', f'/rest/v1/{t}?added_by=eq.{uid}')
    api('DELETE', f'/rest/v1/shipping_forms?vin_number=eq.{DEMO_VIN}')
    api('DELETE', f'/rest/v1/editor_threads?created_by=eq.{uid}')
    api('DELETE', f'/rest/v1/profiles?id=eq.{uid}')
    api('DELETE', f'/auth/v1/admin/users/{uid}')
    left = sum(len(api('GET', f'/rest/v1/{t}?added_by=eq.{uid}&select=id') or []) for t in ('shipping_forms', 'financial_transactions', 'orders'))
    print('cleaned demo account and its entries; left:', left, '; pdfs removed:', len(files))


def setup():
    cleanup()
    pw = secrets.token_urlsafe(18)
    uid = api('POST', '/auth/v1/admin/users', {'email': EMAIL, 'password': pw, 'email_confirm': True})['id']
    for _ in range(10):
        if api('GET', f'/rest/v1/profiles?id=eq.{uid}&select=id'): break
        time.sleep(1)
    else:
        api('POST', '/rest/v1/profiles', {'id': uid, 'email': EMAIL})
    api('PATCH', f'/rest/v1/profiles?id=eq.{uid}', {'office': 'tebessa', 'role': 'staff', 'full_name': 'مكتب تبسة'})
    common = {'office': 'tebessa', 'added_by': uid}
    api('POST', '/rest/v1/orders', {**common, 'reference_number': 'DEMO-TB-001', 'status': 'confirmed', 'customer_name': 'زبون تجريبي 1',
                                    'customer_phone': '0550 00 00 01', 'customer_wilaya': 'Tébessa', 'car_brand': 'Kia', 'car_model': 'Sportage', 'source': 'manual'})
    api('POST', '/rest/v1/financial_transactions', {**common, 'id': str(uuid.uuid4()), 'type': 'Income', 'category': 'Car Sale', 'amount': 5_200_000, 'paid_amount': 5_200_000,
        'payment_status': 'Paid', 'currency': 'DZD', 'transaction_date': time.strftime('%Y-%m-%d'), 'customer_name': 'زبون تجريبي 1',
        'customer_phone': '0550 00 00 01', 'car_brand': 'Kia', 'car_model': 'Sportage', 'car_year': '2022', 'car_color': 'Gris',
        'car_milage': 61000, 'car_vin': 'DEMO0SPORTAGE0001', 'description': 'Kia Sportage 2022 — زبون تجريبي 1'})
    json.dump({'id': uid, 'pw': pw}, open(STATE, 'w'))
    print('demo account ready (office tebessa) + 2 demo entries')


# ---------------------------------------------------------------- recording
TOUCH = """
(() => {
  const css = `#__f{position:fixed;z-index:2147483647;width:34px;height:34px;margin:-17px 0 0 -17px;border-radius:50%;
    background:rgba(95,184,155,.35);border:2px solid rgba(255,255,255,.95);box-shadow:0 2px 10px rgba(0,0,0,.35);pointer-events:none;
    transition:transform .12s ease, opacity .3s; left:-100px; top:-100px}
    #__f.down{transform:scale(.75);background:rgba(95,184,155,.7)}
    .__r{position:fixed;z-index:2147483646;width:20px;height:20px;margin:-10px 0 0 -10px;border-radius:50%;border:3px solid #5FB89B;pointer-events:none;
    animation:__r .6s ease-out forwards}@keyframes __r{to{transform:scale(3.4);opacity:0}}`;
  const add = () => {
    if (document.getElementById('__f')) return;
    const s = document.createElement('style'); s.textContent = css; document.head.appendChild(s);
    const f = document.createElement('div'); f.id = '__f'; document.body.appendChild(f);
    addEventListener('mousemove', e => { f.style.left = e.clientX + 'px'; f.style.top = e.clientY + 'px' }, true);
    addEventListener('mousedown', e => { f.classList.add('down'); const r = document.createElement('div'); r.className = '__r';
      r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px'; document.body.appendChild(r); setTimeout(() => r.remove(), 700) }, true);
    addEventListener('mouseup', () => f.classList.remove('down'), true);
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', add); else add();
})();
"""


class Scene:
    def __init__(self, page, t0, name):
        self.page, self.t0, self.name, self.steps = page, t0, name, []
        self.mx, self.my = 195, 600

    def mark(self, key):
        self.steps.append({'t': round(time.time() - self.t0, 2), 'k': key})
        print(f'  {self.name} {self.steps[-1]["t"]:6.2f}s {key}', flush=True)

    async def wait(self, ms): await self.page.wait_for_timeout(ms)

    async def move(self, x, y, steps=18):
        await self.page.mouse.move(x, y, steps=steps); self.mx, self.my = x, y

    async def tap(self, sel, key=None, settle=500):
        el = self.page.locator(sel).first
        await el.scroll_into_view_if_needed(timeout=10000)
        # keep the target in the middle of the screen, clear of the header and the bottom tab bar
        await el.evaluate("e => { const r = e.getBoundingClientRect(); if (r.top < 90 || r.bottom > innerHeight - 110) e.scrollIntoView({block: 'center', behavior: 'smooth'}) }")
        await self.wait(450)
        b = await el.bounding_box()
        x, y = b['x'] + b['width'] / 2, b['y'] + min(b['height'] / 2, 22)
        await self.move(x, y)
        if key: self.mark(key)
        await self.wait(220)
        await self.page.mouse.down(); await self.wait(90); await self.page.mouse.up()
        await self.wait(settle)

    async def type(self, sel, text, key=None, delay=55):
        await self.tap(sel, key, settle=150)
        await self.page.locator(sel).first.press_sequentially(text, delay=delay)
        await self.wait(300)

    async def pick(self, sel, key=None, **opt):
        await self.tap(sel, key, settle=200)
        await self.page.keyboard.press('Escape')
        await self.page.locator(sel).first.select_option(**opt)
        await self.wait(500)

    async def scroll(self, dy, key=None):
        if key: self.mark(key)
        for _ in range(8):
            await self.page.mouse.wheel(0, dy / 8); await self.wait(45)
        await self.wait(500)


async def record(base, out):
    from playwright.async_api import async_playwright
    st = json.load(open(STATE))
    os.makedirs(out, exist_ok=True)
    log = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        storage = None
        size = {'width': 390, 'height': 844}

        async def scene(name, fn, start='/'):
            nonlocal storage
            ctx = await b.new_context(viewport=size, device_scale_factor=2, is_mobile=True, has_touch=False, locale='ar-DZ',
                                      record_video_dir=f'{out}/raw_{name}', record_video_size={'width': 780, 'height': 1688},
                                      storage_state=storage)
            await ctx.add_init_script("try{localStorage.setItem('language','ar');localStorage.setItem('theme','light')}catch(e){}")
            await ctx.add_init_script(TOUCH)
            page = await ctx.new_page()
            t0 = time.time()
            s = Scene(page, t0, name)
            await page.goto(base + start, wait_until='networkidle')
            await page.wait_for_timeout(1200)
            await s.move(195, 560, 4)
            try:
                await fn(s)
            except Exception as e:
                print(f'!! scene {name} stopped: {e}', flush=True)
                await page.screenshot(path=f'{out}/error_{name}.png')
            await page.wait_for_timeout(900)
            storage = await ctx.storage_state()
            vid = page.video
            await ctx.close()
            os.replace(await vid.path(), f'{out}/{name}.webm')
            log[name] = s.steps

        async def login(s):
            s.mark('login')
            await s.type('input[type=email]', EMAIL, 'email', delay=35)
            await s.type('input[type=password]', st['pw'], 'password', delay=20)
            await s.tap('button[type=submit]', 'submit', settle=300)
            await s.page.wait_for_url(lambda u: not u.rstrip('/').endswith('/login'), timeout=20000)
            await s.page.wait_for_load_state('networkidle'); await s.wait(1500)
            s.mark('home')
            await s.wait(2500)
            await s.scroll(500, 'home_scroll'); await s.wait(1200); await s.scroll(-500)
            await s.tap('nav.fixed button', 'menu', settle=1200)
            s.mark('menu_open'); await s.wait(3200)
            await s.page.keyboard.press('Escape'); await s.wait(300)

        async def orders(s):
            s.mark('orders_list'); await s.wait(2500)
            await s.tap('a[href="/orders/new"]', 'order_new', settle=1200)
            await s.type('#o-name', 'زبون تجريبي 2', 'order_client')
            await s.type('#o-phone', '0550000002')
            await s.pick('#o-wilaya', 'order_wilaya', index=12)
            await s.pick('#o-brand', 'order_car', label='Hyundai')
            try: await s.pick('#o-model', None, label='Tucson')
            except Exception: pass
            await s.type('#o-budget', '520')
            await s.tap('button[type=submit]', 'order_save', settle=300)
            await s.page.wait_for_url('**/orders/details**', timeout=20000); await s.page.wait_for_load_state('networkidle')
            s.mark('order_details'); await s.wait(3000)
            await s.scroll(500); await s.wait(1200)
            await s.page.goto(base + '/orders', wait_until='networkidle'); await s.wait(800)
            s.mark('orders_badge'); await s.wait(3000)

        async def stock(s):
            s.mark('stock_list'); await s.wait(2200)
            await s.scroll(700, 'stock_scroll'); await s.wait(1000); await s.scroll(-700)
            await s.tap('a[href^="/inventory/details"]', 'stock_open', settle=1500)
            await s.page.wait_for_load_state('networkidle'); s.mark('stock_details'); await s.wait(2500)
            await s.scroll(700); await s.wait(1500)

        async def sale(s):
            s.mark('sales_list'); await s.wait(2500)
            await s.tap('a[href="/finance/new"]', 'sale_new', settle=1200)
            await s.type('#customerName', 'زبون تجريبي 2', 'sale_client')
            await s.type('#customerPhone', '0550000002')
            await s.type('#customerAddress', 'تبسة، حي تجريبي')
            await s.type('#passportNumber', 'DEMO12345')
            await s.scroll(500, 'sale_docs'); await s.wait(1500)
            await s.pick('#carBrand', 'sale_car', label='Hyundai')
            try: await s.pick('#carModel', None, label='Tucson')
            except Exception: pass
            await s.type('#carYear', '2021')
            await s.type('#carColor', 'Blanc', 'sale_color')
            await s.type('#carMileage', '74000', 'sale_km')
            await s.type('#carVin', 'DEMO0TUCSON000002', 'sale_vin')
            await s.type('#amount', '5400000', 'sale_price')
            await s.tap('button[role=radio]:has-text("عربون")', 'sale_deposit', settle=500)
            await s.type('#paidAmount', '2000000', 'sale_paid')
            await s.scroll(400); await s.wait(1200)
            await s.tap('button[type=submit]', 'sale_save', settle=300)
            await s.page.wait_for_url('**/finance/details**', timeout=20000); await s.page.wait_for_load_state('networkidle')
            s.mark('sale_details'); await s.wait(3000)
            sid = s.page.url.split('id=')[-1]
            await s.tap('a[href^="/finance/invoice"]', 'invoice', settle=1500)
            await s.page.wait_for_load_state('networkidle'); await s.wait(1500)
            s.mark('invoice_view'); await s.scroll(900); await s.wait(1200); await s.scroll(-900)
            await s.tap('label:has(input[type=checkbox])', 'stamp_toggle', settle=1200)
            await s.scroll(900); await s.wait(1600); await s.scroll(-900)
            await s.tap('label:has(input[type=checkbox])', None, settle=600)
            await s.move(330, 70); s.mark('print'); await s.wait(1800)
            await s.page.goto(base + f'/finance/contract?id={sid}', wait_until='networkidle'); await s.wait(1000)
            s.mark('contract_view'); await s.scroll(900); await s.wait(1600)
            await s.page.goto(base + '/finance', wait_until='networkidle'); await s.wait(1000)
            s.mark('sales_list_after'); await s.wait(2000)
            await s.tap('td select', 'batch_select', settle=300); await s.page.keyboard.press('Escape'); await s.wait(2000)

        async def shipping(s):
            s.mark('ship_list'); await s.wait(2200)
            await s.tap('a[href^="/shipping/new"]', 'ship_new', settle=1200)
            await s.type('#s-name', 'زبون تجريبي 2', 'ship_client')
            await s.type('#s-phone', '0550000002')
            await s.type('#s-address', 'تبسة، حي تجريبي')
            await s.type('#s-passport', 'DEMO12345')
            await s.type('#s-model', 'Hyundai Tucson 2021', 'ship_car')
            await s.type('#s-vin', DEMO_VIN)
            try: await s.pick('#s-provider', 'ship_provider', index=1)
            except Exception: pass
            await s.tap('button[type=submit]', 'ship_save', settle=300)
            await s.page.wait_for_url('**/shipping/details**', timeout=40000); await s.page.wait_for_load_state('networkidle')
            s.mark('ship_details'); await s.wait(3000)
            await s.page.goto(base + '/shipping', wait_until='networkidle'); await s.wait(800)
            s.mark('ship_whatsapp'); await s.wait(1200)
            await s.move(250, 330); await s.wait(2500)

        await scene('login', login, '/login')
        await scene('orders', orders, '/orders')
        await scene('stock', stock, '/inventory')
        await scene('sale', sale, '/finance')
        await scene('shipping', shipping, '/shipping')
        await b.close()
    json.dump(log, open(f'{out}/steps.json', 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'setup': setup()
    elif cmd == 'cleanup': cleanup()
    elif cmd == 'record': asyncio.run(record(sys.argv[2].rstrip('/'), sys.argv[3]))
