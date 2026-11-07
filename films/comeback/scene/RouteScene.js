const TAU = Math.PI * 2, C30 = Math.cos(Math.PI / 6);
const lerp = (a, b, t) => a + (b - a) * t;
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const smooth = (t) => { t = clamp(t); return t * t * (3 - 2 * t); };
const easeIO = (t) => { t = clamp(t); return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const mix = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
const rgba = (c, a = 1) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`;
const shade = (c, k) => (k <= 1 ? [c[0] * k, c[1] * k, c[2] * k] : mix(c, [255, 255, 255], Math.min(1, k - 1)));
const PAL = {
    dark: {
        pad: [20, 40, 33], padLine: [70, 110, 95], neutral: [44, 72, 61], accent: [95, 184, 155], ice: [168, 230, 207],
        line: [159, 227, 200], text: [128, 150, 140], textHi: [238, 244, 240], water: [95, 184, 155], hull: [26, 46, 39], deck: [58, 92, 79],
        car1: [226, 234, 229], car2: [112, 138, 127], sand: [196, 170, 122], build: [36, 60, 51], tyre: [12, 20, 17], shadow: [0, 0, 0], roof: [95, 184, 155], glass: [20, 34, 30],
    },
    light: {
        pad: [214, 226, 218], padLine: [160, 182, 171], neutral: [170, 190, 180], accent: [46, 150, 116], ice: [14, 90, 71],
        line: [10, 23, 18], text: [82, 102, 93], textHi: [10, 23, 18], water: [30, 138, 102], hull: [70, 96, 86], deck: [160, 182, 171],
        car1: [252, 253, 252], car2: [150, 170, 160], sand: [196, 160, 100], build: [236, 242, 238], tyre: [40, 52, 47], shadow: [10, 40, 30], roof: [46, 150, 116], glass: [44, 64, 58],
    },
};
const SHOTS = {
    hero: { x: 5, y: 0, z: 0.5, ax: 0.7, ay: 0.55, alpha: 0.85 },
    order: { x: 4, y: -2, z: 0.62, ax: 0.62, ay: 0.55, alpha: 0.95 },
    inspect: { x: -26.5, y: -6.5, z: 1.9, ax: 0.66, ay: 0.55, alpha: 1 },
    buy: { x: -19, y: -2, z: 1.35, ax: 0.66, ay: 0.55, alpha: 1 },
    ship: { x: -3, y: 0, z: 1.05, ax: 0.62, ay: 0.55, alpha: 1 },
    customs: { x: 19, y: 0, z: 1.6, ax: 0.64, ay: 0.55, alpha: 1 },
    keys: { x: 37, y: -2.6, z: 1.3, ax: 0.64, ay: 0.55, alpha: 1 },
    all: { x: 5, y: 0, z: 0.5, ax: 0.5, ay: 0.55, alpha: 0.4 },
    quiet: { x: 5, y: 0, z: 0.55, ax: 0.5, ay: 0.55, alpha: 0.25 },
};
const STEPS = ['order', 'inspect', 'buy', 'ship', 'customs', 'keys'];
const LABELS = {
    ar: { korea: 'كوريا · 한국', china: 'الصين · 中国', export: 'ميناء التصدير', sea: 'في البحر', port: 'ميناء الجزائر', customs: 'الجمارك', showroom: 'وحيد أوتو · جيجل', home: 'دارك', ok: 'مفحوصة ✓', doc: 'الأوراق', stamp: 'مُجمركة', keys: 'المفاتيح' },
    fr: { korea: 'CORÉE · 한국', china: 'CHINE · 中国', export: 'PORT D’EXPORT', sea: 'EN MER', port: 'PORT · ALGÉRIE', customs: 'DOUANE', showroom: 'WAHID AUTO · JIJEL', home: 'CHEZ VOUS', ok: 'INSPECTÉE ✓', doc: 'DOCUMENTS', stamp: 'DÉDOUANÉE', keys: 'VOS CLÉS' },
};
function flagCanvas(kind) {
    const c = document.createElement('canvas');
    c.width = 60;
    c.height = 40;
    const g = c.getContext('2d');
    if (kind === 'dz') {
        g.fillStyle = '#006233';
        g.fillRect(0, 0, 30, 40);
        g.fillStyle = '#fff';
        g.fillRect(30, 0, 30, 40);
        g.fillStyle = '#d21034';
        g.beginPath();
        g.arc(30, 20, 10, 0, TAU);
        g.fill();
        g.fillStyle = '#fff';
        g.beginPath();
        g.arc(33, 20, 8, 0, TAU);
        g.fill();
        g.fillStyle = '#006233';
        g.beginPath();
        g.arc(33, 20, 8, Math.PI / 2, Math.PI * 1.5);
        g.fill();
        g.fillStyle = '#d21034';
        g.beginPath();
        for (let i = 0; i < 10; i++) {
            const r = i % 2 ? 2.2 : 5, a = -Math.PI / 2 + (i * Math.PI) / 5;
            g.lineTo(35 + Math.cos(a) * r, 20 + Math.sin(a) * r);
        }
        g.fill();
    }
    else if (kind === 'kr') {
        g.fillStyle = '#fff';
        g.fillRect(0, 0, 60, 40);
        g.fillStyle = '#cd2e3a';
        g.beginPath();
        g.arc(30, 20, 9, Math.PI, TAU);
        g.fill();
        g.fillStyle = '#0047a0';
        g.beginPath();
        g.arc(30, 20, 9, 0, Math.PI);
        g.fill();
        g.fillStyle = '#cd2e3a';
        g.beginPath();
        g.arc(25.5, 20, 4.5, 0, TAU);
        g.fill();
        g.fillStyle = '#0047a0';
        g.beginPath();
        g.arc(34.5, 20, 4.5, 0, TAU);
        g.fill();
        g.fillStyle = '#111';
        for (const [x, y, r] of [[11, 8, -0.6], [49, 8, 0.6], [11, 32, 0.6], [49, 32, -0.6]]) {
            g.save();
            g.translate(x, y);
            g.rotate(r);
            for (let k = -1; k <= 1; k++)
                g.fillRect(-5, k * 2.6 - 0.8, 10, 1.6);
            g.restore();
        }
    }
    else {
        g.fillStyle = '#de2910';
        g.fillRect(0, 0, 60, 40);
        g.fillStyle = '#ffde00';
        g.beginPath();
        for (let i = 0; i < 10; i++) {
            const r = i % 2 ? 2.6 : 6.5, a = -Math.PI / 2 + (i * Math.PI) / 5;
            g.lineTo(12 + Math.cos(a) * r, 11 + Math.sin(a) * r);
        }
        g.fill();
    }
    return c;
}
export function startScene(canvas) {
    return (() => {
        if (!canvas)
            return;
        const main = canvas.getContext('2d');
        // the still world (ground, yards, buildings, parked cars) is drawn into its own canvas and only redrawn when the camera or tone moves
        const still = document.createElement('canvas'), stillCtx = still.getContext('2d');
        let ctx = main, stillKey = '';
        const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        let W = 0, H = 0, DPR = 1;
        const resize = () => {
            DPR = Math.min(window.devicePixelRatio || 1, 1.5);
            W = window.innerWidth;
            H = window.innerHeight;
            canvas.width = still.width = Math.round(W * DPR);
            canvas.height = still.height = Math.round(H * DPR);
            stillKey = '';
        };
        resize();
        window.addEventListener('resize', resize);
        const flags = { kr: flagCanvas('kr'), dz: flagCanvas('dz'), cn: flagCanvas('cn') };
        let tone = 0;
        const C = {};
        const palette = () => { for (const k in PAL.dark)
            C[k] = mix(PAL.dark[k], PAL.light[k], tone); };
        palette();
        const cam = { ...SHOTS.hero };
        const focus = Object.fromEntries(STEPS.map(s => [s, 0])); // how lit each step is
        let SU = 1, mirror = false;
        const P = (x, y, z = 0) => {
            const dx = x - cam.x, dy = y - cam.y;
            const sx = cam.ax * W + (dx - dy) * C30 * SU;
            return [mirror ? W - sx : sx, cam.ay * H + ((dx + dy) * 0.5 - z * 0.92) * SU];
        };
        // ---------- primitives ----------
        let ops = [], target = null;
        const push = (o) => (target || ops).push(o);
        const poly = (pts, fill, stroke, lw = 1) => {
            ctx.beginPath();
            pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
            ctx.closePath();
            if (fill) {
                ctx.fillStyle = fill;
                ctx.fill();
            }
            if (stroke) {
                ctx.strokeStyle = stroke;
                ctx.lineWidth = lw;
                ctx.stroke();
            }
        };
        const quad = (x, y, w, d, z) => [P(x, y, z), P(x + w, y, z), P(x + w, y + d, z), P(x, y + d, z)];
        const box = (x, y, z, w, d, h, c, a = 1, edge = 0.16, sides) => {
            push({
                d: x + w + y + d + z * 0.02, f: () => {
                    const e = edge ? rgba(C.line, edge * a) : undefined, sc = sides || c;
                    poly([P(x + w, y, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x + w, y, z + h)], rgba(shade(sc, 0.82), a), e);
                    poly([P(x, y + d, z), P(x + w, y + d, z), P(x + w, y + d, z + h), P(x, y + d, z + h)], rgba(shade(sc, 0.64), a), e);
                    poly(quad(x, y, w, d, z + h), rgba(shade(c, 1.1), a), e);
                },
            });
        };
        const shadow = (x, y, rx, ry, a) => {
            const [sx, sy] = P(x, y, 0);
            ctx.fillStyle = rgba(C.shadow, 0.28 * a * (1 - tone * 0.4));
            ctx.beginPath();
            ctx.ellipse(sx, sy, rx * SU, ry * SU, 0, 0, TAU);
            ctx.fill();
        };
        // a car: soft shadow, wheels that show under the body, low painted body, glass cabin with painted roof
        const car = (x, y, heading, c, a = 1, lights = false) => {
            if (a <= 0.01)
                return;
            const ax = heading < 0.5;
            const L2 = 1.0, W2 = 0.46; // half length / half width
            const at = (along, across) => (ax ? [x + along, y + across] : [x + across, y + along]);
            const bx = (along0, across0, len, wid, z, h, col, edge, sides) => {
                const [x0, y0] = at(along0, across0);
                box(x0, y0, z, ax ? len : wid, ax ? wid : len, h, col, a, edge, sides);
            };
            shadow(x + 0.12, y + 0.12, 1.25, 0.6, a);
            // one car = one group drawn in a fixed order, so the body never covers the windows
            const outer = target, parts = [];
            target = parts;
            for (const al of [-0.62, 0.52])
                for (const ac of [-W2 - 0.02, W2 - 0.12])
                    bx(al, ac, 0.36, 0.14, 0, 0.3, C.tyre, 0);
            bx(-L2, -W2, 2 * L2, 2 * W2, 0.16, 0.3, c, 0.14); // body
            bx(-0.56, -W2 + 0.07, 1.06, 2 * W2 - 0.14, 0.46, 0.27, c, 0.14, C.glass); // cabin: glass sides, roof in body colour
            target = outer;
            const body = parts.splice(4, 2), tyres = parts.sort((p1, p2) => p1.d - p2.d);
            push({ d: x + y + 1.4, f: () => { tyres.forEach(o => o.f()); body.forEach(o => o.f()); } });
            if (lights)
                push({ d: x + y + 3, f: () => { const [lx, ly] = P(...at(L2 + 0.05, 0), 0.3); ctx.fillStyle = rgba(C.ice, 0.55 * a * (1 - tone * 0.6)); ctx.beginPath(); ctx.ellipse(lx, ly, SU * 0.16, SU * 0.08, 0, 0, TAU); ctx.fill(); } });
        };
        const person = (x, y, a) => {
            shadow(x, y, 0.35, 0.18, a);
            box(x - 0.18, y - 0.18, 0, 0.36, 0.36, 0.95, C.accent, a, 0.2);
            box(x - 0.14, y - 0.14, 0.98, 0.28, 0.28, 0.28, C.car1, a, 0.2);
        };
        const flag = (x, y, kind, t, a) => {
            push({
                d: x + y + 0.5, f: () => {
                    const [bx, by] = P(x, y, 0), [tx, ty] = P(x, y, 4.2);
                    ctx.strokeStyle = rgba(C.text, 0.8 * a);
                    ctx.lineWidth = Math.max(1, SU * 0.06);
                    ctx.beginPath();
                    ctx.moveTo(bx, by);
                    ctx.lineTo(tx, ty);
                    ctx.stroke();
                    const fw = SU * 1.9, fh = SU * 1.26, img = flags[kind], strips = 10;
                    ctx.globalAlpha = 0.95 * a;
                    for (let i = 0; i < strips; i++) {
                        const u = i / strips, wave = Math.sin(u * 5.2 - t * 2.6) * SU * 0.12 * u;
                        ctx.drawImage(img, u * img.width, 0, img.width / strips + 0.6, img.height, mirror ? tx - fw + u * fw : tx + u * fw, ty + wave, fw / strips + 0.6, fh);
                    }
                    ctx.globalAlpha = 1;
                },
            });
        };
        const text = (s, x, y, size, c, a) => {
            const arabic = /[؀-ۿ]/.test(s);
            try {
                ctx.letterSpacing = arabic ? '0px' : '1.5px';
            }
            catch { /* old browsers */ }
            ctx.font = arabic ? `500 ${size + 2}px "IBM Plex Sans Arabic", sans-serif` : `500 ${size}px "JetBrains Mono", monospace`;
            const tw = ctx.measureText(s).width;
            ctx.fillStyle = rgba(c, a);
            ctx.textBaseline = 'bottom';
            ctx.fillText(s, x - tw / 2, y);
            return tw;
        };
        const label = (x, y, z, s, a, hi = 0) => {
            if (W < 760)
                return;
            push({
                d: 999, f: () => {
                    const [px, py] = P(x, y, z), up = 30 + hi * 8;
                    ctx.strokeStyle = rgba(C.line, (0.3 + 0.3 * hi) * a);
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(px, py);
                    ctx.lineTo(px, py - up);
                    ctx.stroke();
                    ctx.fillStyle = rgba(hi > 0.5 ? C.accent : C.line, a);
                    ctx.beginPath();
                    ctx.arc(px, py, 2.4 + hi, 0, TAU);
                    ctx.fill();
                    text(s, px, py - up - 6, 10, mix(C.text, C.textHi, hi), a);
                },
            });
        };
        // a chip that rises and fades (ticks, documents, stamp, keys)
        const chip = (x, y, z, s, life, a) => {
            if (W < 760 && !document.querySelector('[data-active-section] [data-anchor]'))
                return;
            if (life <= 0 || life >= 1 || a <= 0.01)
                return;
            const k = Math.sin(Math.PI * life);
            push({
                d: 1000, f: () => {
                    const [px, py0] = P(x, y, z), py = py0 - 24 - life * 26;
                    ctx.font = '600 11px "JetBrains Mono", "IBM Plex Sans Arabic", monospace';
                    const tw = ctx.measureText(s).width + 20, h = 24;
                    ctx.globalAlpha = k * a;
                    ctx.fillStyle = rgba(C.accent, 1);
                    ctx.beginPath();
                    ctx.roundRect(px - tw / 2, py - h, tw, h, 12);
                    ctx.fill();
                    try {
                        ctx.letterSpacing = '0.5px';
                    }
                    catch { /* */ }
                    ctx.fillStyle = '#fff';
                    ctx.textBaseline = 'middle';
                    const w2 = ctx.measureText(s).width;
                    ctx.fillText(s, px - w2 / 2, py - h / 2 + 1);
                    ctx.globalAlpha = 1;
                },
            });
        };
        const pad = (x, y, w, d, a) => {
            poly(quad(x, y, w, d, 0), rgba(C.pad, 0.75 * a), rgba(C.line, 0.14 * a));
            ctx.setLineDash([3, 5]);
            ctx.strokeStyle = rgba(C.padLine, 0.35 * a);
            for (let k = 1; k < w; k += 2) {
                const p1 = P(x + k, y + 0.3), p2 = P(x + k, y + d - 0.3);
                ctx.beginPath();
                ctx.moveTo(...p1);
                ctx.lineTo(...p2);
                ctx.stroke();
            }
            ctx.setLineDash([]);
        };
        const road = (pts, wdt, a) => {
            for (let i = 1; i < pts.length; i++) {
                const [x0, y0] = pts[i - 1], [x1, y1] = pts[i], h = wdt / 2;
                const r = y0 === y1 ? quad(Math.min(x0, x1) - h, y0 - h, Math.abs(x1 - x0) + wdt, wdt, 0) : quad(x0 - h, Math.min(y0, y1) - h, wdt, Math.abs(y1 - y0) + wdt, 0);
                poly(r, rgba(C.pad, 0.55 * a));
            }
        };
        // drive along a polyline; slows into corners and at the ends, like a real car
        const drive = (pts, u) => {
            const segs = pts.slice(1).map((p, i) => Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]));
            const total = segs.reduce((a, b) => a + b, 0);
            let s = easeIO(u) * total;
            for (let i = 0; i < segs.length; i++) {
                if (s <= segs[i] || i === segs.length - 1) {
                    const k = clamp(s / segs[i]), a = pts[i], b = pts[i + 1];
                    return { x: lerp(a[0], b[0], k), y: lerp(a[1], b[1], k), heading: a[1] === b[1] ? 0 : 1 };
                }
                s -= segs[i];
            }
            return { x: pts[0][0], y: pts[0][1], heading: 0 };
        };
        // ---------- world layout ----------
        const SHIP_LEN = 7.4, SHIP_W = 2.7, CYCLE = 30;
        const KR = [[-23.4, -6.6], [-21.5, -6.6], [-21.5, -1.1], [-14.5, -1.1]];
        const CN = [[-23.4, 6.6], [-21.5, 6.6], [-21.5, 1.1], [-14.5, 1.1]];
        const DZ = [[14.5, 0], [39, 0], [39, -3.4]];
        const HOUSE = { x: 39.2, y: -6.4 };
        const ship = (t) => {
            const u = ((t % CYCLE) + CYCLE) % CYCLE / CYCLE;
            if (u < 0.2)
                return { x: -11.4, phase: 'load', load: u / 0.2, u };
            if (u < 0.52)
                return { x: lerp(-11.4, 3.6, easeIO((u - 0.2) / 0.32)), phase: 'sea', load: 1, u };
            if (u < 0.7)
                return { x: 3.6, phase: 'port', load: 1 - (u - 0.52) / 0.18, u };
            return { x: lerp(3.6, -11.4, easeIO((u - 0.7) / 0.3)), phase: 'back', load: 0, u };
        };
        let raf = 0, prev = performance.now(), shown = '';
        const t0 = performance.now();
        const draw = (now) => {
            raf = requestAnimationFrame(draw);
            if (document.hidden) {
                prev = now;
                return;
            }
            const dt = Math.min(0.05, (now - prev) / 1000);
            prev = now;
            const t = reduce ? 9 : (now - t0) / 1000;
            const follow = (rate) => (reduce ? 1 : 1 - Math.exp(-rate * dt)); // same feel at any frame rate
            // follow the page
            const body = document.body, scene = body.dataset.scene || 'hero';
            tone = lerp(tone, body.dataset.tone === 'light' ? 1 : 0, follow(3));
            palette();
            const shot = SHOTS[scene] || SHOTS.quiet;
            const mobile = W < 760;
            mirror = document.documentElement.dir === 'rtl';
            let gx = window.__ax ?? (mobile ? 0.5 : shot.ax), gy = window.__ay ?? (mobile ? 0.4 : shot.ay);
            const anchor = document.querySelector('[data-active-section] [data-anchor]');
            let framed = false;
            if (anchor) {
                const r = anchor.getBoundingClientRect();
                if (r.bottom > 0 && r.top < H) {
                    const cx = (r.left + r.width / 2) / W;
                    gx = mirror ? 1 - cx : cx;
                    gy = (r.top + r.height / 2) / H;
                    framed = true;
                }
            }
            const kc = follow(2.2);
            cam.x = lerp(cam.x, shot.x, kc);
            cam.y = lerp(cam.y, shot.y, kc);
            const zoomK = mobile ? (framed ? 1.15 : 1.9) : 1;
            cam.z = lerp(cam.z, shot.z * zoomK, kc);
            cam.ax = lerp(cam.ax, gx, follow(4));
            cam.ay = lerp(cam.ay, gy, follow(4));
            const alphaK = mobile && !framed ? 0.5 : 1;
            cam.alpha = lerp(cam.alpha, shot.alpha * alphaK, follow(2.5));
            const snap = (k, goal, eps) => { if (Math.abs(cam[k] - goal) < eps)
                cam[k] = goal; };
            snap('x', shot.x, 0.004);
            snap('y', shot.y, 0.004);
            snap('z', shot.z * zoomK, 0.0005);
            snap('ax', gx, 0.0004);
            snap('ay', gy, 0.0004);
            snap('alpha', shot.alpha * alphaK, 0.003);
            if (Math.abs(tone - (body.dataset.tone === 'light' ? 1 : 0)) < 0.004)
                tone = body.dataset.tone === 'light' ? 1 : 0;
            for (const s of STEPS)
                focus[s] = lerp(focus[s], scene === s ? 1 : scene === 'hero' || scene === 'all' ? 0.35 : 0, follow(3));
            SU = (24 * cam.z * Math.min(W, H * 1.6)) / 1200 * (window.__zoomK || 1);
            const A = cam.alpha, L = document.documentElement.lang === 'fr' ? LABELS.fr : LABELS.ar;
            if (A < 0.02) {
                main.setTransform(1, 0, 0, 1, 0, 0);
                main.clearRect(0, 0, canvas.width, canvas.height);
                stillKey = '';
                return;
            }
            const cols = [C.car1, C.car2, C.accent, C.sand, C.car1];
            const key = [cam.x, cam.y, cam.z, cam.ax, cam.ay, cam.alpha, tone].map(v => v.toFixed(4)).join() + (mirror ? 'r' : 'l') + L.home;
            if (key !== stillKey) {
                stillKey = key;
                ctx = stillCtx;
                ops = [];
                ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
                ctx.clearRect(0, 0, W, H);
                // ---- ground ----
                pad(-30, -9.5, 7, 5, A);
                pad(-30, 4.5, 7, 5, A);
                pad(-20, -3.5, 8, 7, A);
                pad(12, -3.5, 8, 7, A);
                road([[-23, -6.6], [-21.5, -6.6], [-21.5, 6.6], [-23, 6.6]], 1.3, A);
                road([[-21.5, 0], [-20, 0]], 1.3, A);
                road([[20, 0], [39, 0], [39, -4.6]], 1.5, A);
                poly(quad(HOUSE.x - 3.6, HOUSE.y - 2.2, 6.4, 4.6, 0), rgba(C.pad, 0.7 * A), rgba(C.line, 0.12 * A)); // garden
                // sea
                poly(quad(-11.6, -6.6, 23.2, 13.2, -0.05), rgba(C.water, (0.08 + 0.05 * tone) * A), rgba(C.water, 0.22 * A));
                for (let i = 0; i < 6; i++) {
                    car(-29 + (i % 3) * 2.3, -8.5 + Math.floor(i / 3) * 2.3, 1, cols[i % 5], A);
                    car(-29 + (i % 3) * 2.3, 5.4 + Math.floor(i / 3) * 2.3, 1, cols[(i + 2) % 5], A);
                }
                const gateX0 = 23.5;
                box(gateX0 - 0.2, 1.1, 0, 0.4, 0.4, 1.3, C.neutral, A);
                // showroom + the client's house
                box(26.5, -6.6, 0, 5, 3.4, 2.3, C.build, A, 0.3);
                box(26.5, -6.6, 2.3, 5, 3.4, 0.22, C.roof, A);
                car(28, -1.9, 1, C.accent, A);
                car(30.2, -1.9, 1, C.car1, A);
                box(HOUSE.x - 2.4, HOUSE.y - 1.4, 0, 3.2, 2.8, 1.8, C.build, A, 0.3);
                box(HOUSE.x - 2.6, HOUSE.y - 1.6, 1.8, 3.6, 3.2, 0.5, C.roof, A, 0.25);
                ops.sort((a, b) => a.d - b.d).forEach(o => o.f());
                ctx = main;
            }
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(still, 0, 0);
            ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
            ops = [];
            ctx.lineWidth = 1;
            for (let gx2 = -10.4; gx2 <= 10.4; gx2 += 1.75) {
                ctx.strokeStyle = rgba(C.water, (0.18 + 0.12 * Math.sin(gx2 + t * 0.6)) * A);
                ctx.beginPath();
                for (let gy2 = -6.2; gy2 <= 6.2; gy2 += 0.8) {
                    const [sx, sy] = P(gx2 + Math.sin(gy2 * 0.8 + t * 0.9 + gx2) * 0.22, gy2, Math.sin(gx2 * 0.7 + gy2 * 0.5 + t * 1.3) * 0.08);
                    gy2 === -6.2 ? ctx.moveTo(sx, sy) : ctx.lineTo(sx, sy);
                }
                ctx.stroke();
            }
            ctx.setLineDash([6, 9]);
            ctx.lineDashOffset = -t * 10;
            ctx.strokeStyle = rgba(C.accent, (0.35 + 0.4 * focus.ship) * A);
            ctx.beginPath();
            ctx.moveTo(...P(-11.4, 0, 0.02));
            ctx.lineTo(...P(11.4, 0, 0.02));
            ctx.stroke();
            ctx.setLineDash([]);
            // ---- 02 INSPECT: yards, inspector circling the first car, ticks ----
            const ia = t * 0.55, ix = -29 + Math.cos(ia) * 1.6, iy = -8.5 + Math.sin(ia) * 1.5;
            person(ix, iy, A * (0.4 + 0.6 * Math.max(focus.inspect, 0.35)));
            const tick = (t * 0.55) % 1;
            chip(-29, -8.5, 1.2, L.ok, tick, A * Math.max(focus.inspect, 0.25));
            // ---- 03 BUY → 01 ORDER: cars leave the yards with their papers ----
            for (let i = 0; i < 2; i++) {
                const u = ((t / 12 + i / 2) % 1);
                const fade = smooth(u * 10) * smooth((1 - u) * 10);
                const pk = drive(KR, u), pc = drive(CN, (u + 0.5) % 1);
                car(pk.x, pk.y, pk.heading, cols[i], A * fade, true);
                car(pc.x, pc.y, pc.heading, cols[i + 2], A * smooth(((u + 0.5) % 1) * 10) * smooth((1 - (u + 0.5) % 1) * 10), true);
                chip(pk.x, pk.y, 1, L.doc, clamp((u - 0.55) / 0.4), A * focus.buy);
            }
            // ---- 04 SHIP: cranes, ship, containers loaded one by one ----
            const s = ship(t);
            const crane = (x, y, lift, reach) => {
                box(x, y, 0, 0.6, 0.6, 5.4, C.neutral, A);
                box(x - 2.4 + reach, y, 5.4, 4.8, 0.5, 0.34, C.accent, A);
                const hx = x + 1.6 + reach, hz = lerp(5.3, 1.6, lift);
                push({ d: x + y + 1.5, f: () => { const a1 = P(hx, y + 0.25, 5.4), a2 = P(hx, y + 0.25, hz); ctx.strokeStyle = rgba(C.line, 0.5 * A); ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(...a1); ctx.lineTo(...a2); ctx.stroke(); } });
                return { hx, hz };
            };
            // the crane dips once per container while the ship loads / unloads
            const dip = (load, n) => { const f = (load * n) % 1; return Math.sin(Math.PI * f); };
            crane(-14.2, -3, s.phase === 'load' ? dip(s.load, 8) : 0.1 + 0.05 * Math.sin(t), 1.2);
            crane(13.2, 2.6, s.phase === 'port' ? dip(1 - s.load, 8) : 0.1 + 0.05 * Math.sin(t + 2), -1.2);
            const roll = Math.sin(t * 0.9) * 0.05, sy = -SHIP_W / 2;
            const shipOps = [];
            target = shipOps;
            box(s.x, sy, roll, SHIP_LEN, SHIP_W, 0.75, C.hull, A, 0.3);
            const n = Math.floor(s.load * 8 + 0.001);
            for (let i = 0; i < n; i++) {
                const cx = s.x + 0.45 + (i % 4) * 1.4, cy = sy + 0.28 + Math.floor(i / 4) * 1.1;
                box(cx, cy, 0.75 + roll, 1.3, 1.02, 0.64, [C.accent, C.ice, C.sand, C.neutral][i % 4], A);
            }
            box(s.x + SHIP_LEN - 1.45, sy + 0.42, 0.75 + roll, 1.15, SHIP_W - 0.84, 1.15, C.deck, A);
            target = null;
            const hull = shipOps.shift();
            shipOps.sort((a, b) => a.d - b.d);
            ops.push({ d: s.x + SHIP_LEN + 1, f: () => { hull.f(); shipOps.forEach(o => o.f()); } });
            if (s.phase === 'sea' || s.phase === 'back') { // soft wake
                const dir = s.phase === 'sea' ? -1 : 1, bx = s.phase === 'sea' ? s.x : s.x + SHIP_LEN;
                for (let k = 1; k <= 4; k++) {
                    ctx.strokeStyle = rgba(C.ice, (0.32 - k * 0.06) * A);
                    ctx.beginPath();
                    ctx.moveTo(...P(bx + dir * k * 0.9, -0.5 - k * 0.3));
                    ctx.quadraticCurveTo(...P(bx + dir * (k * 0.9 + 0.5), 0), ...P(bx + dir * k * 0.9, 0.5 + k * 0.3));
                    ctx.stroke();
                }
            }
            // ---- 05 CUSTOMS + 06 KEYS: cars roll off, pass the barrier, one goes home ----
            const gateX = 23.5;
            let gate = 0;
            for (let i = 0; i < 3; i++) {
                const u = ((t / 14 + i / 3) % 1);
                // pause at the barrier, then drive on
                const v = u < 0.3 ? easeIO(u / 0.3) * 0.36 : u < 0.42 ? 0.36 : 0.36 + easeIO((u - 0.42) / 0.58) * 0.64;
                const p = drive(DZ, v);
                if (u > 0.36 && u < 0.46)
                    gate = Math.max(gate, smooth((u - 0.36) / 0.05));
                const atHome = v > 0.98;
                car(p.x, p.y, p.heading, cols[(i + 1) % 5], A * smooth(u * 12) * (atHome ? smooth((1 - u) * 14) : 1), true);
                chip(gateX, 0, 1.6, L.stamp, clamp((u - 0.38) / 0.16), A * focus.customs);
                chip(39, -3.4, 1.2, L.keys, clamp((u - 0.86) / 0.13), A * Math.max(focus.keys, 0.3));
            }
            push({ d: gateX + 1.6, f: () => { const [px, py] = P(gateX, 1.3, 1.2); ctx.save(); ctx.translate(px, py); ctx.rotate((mirror ? 1.2 : -1.2) * gate); ctx.strokeStyle = rgba(C.accent, A); ctx.lineWidth = Math.max(2, SU * 0.14); ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo((mirror ? 1 : -1) * SU * 1.7, -SU * 0.85); ctx.stroke(); ctx.restore(); } });
            push({ d: HOUSE.x + HOUSE.y + 2, f: () => { const [wx, wy] = P(HOUSE.x + 0.8, HOUSE.y + 0.4, 0.9); ctx.fillStyle = rgba(C.sand, (0.5 + 0.3 * Math.sin(t * 2)) * A * Math.max(focus.keys, 0.4)); ctx.fillRect(wx - SU * 0.25, wy - SU * 0.3, SU * 0.5, SU * 0.5); } });
            // ---- 01 ORDER: a request travels from the house to the yards ----
            const oa = A * Math.max(focus.order, 0.2);
            if (oa > 0.02)
                push({
                    d: 1001, f: () => {
                        const a = P(HOUSE.x, HOUSE.y, 2.6), b = P(-26.5, -7, 1.5);
                        const mx = (a[0] + b[0]) / 2, my = Math.min(a[1], b[1]) - H * 0.22;
                        ctx.setLineDash([2, 7]);
                        ctx.strokeStyle = rgba(C.accent, 0.6 * oa);
                        ctx.lineWidth = 1.2;
                        ctx.beginPath();
                        ctx.moveTo(...a);
                        ctx.quadraticCurveTo(mx, my, ...b);
                        ctx.stroke();
                        ctx.setLineDash([]);
                        for (let k = 0; k < 3; k++) {
                            const u = ((t * 0.22 + k / 3) % 1), q = 1 - u;
                            const px = q * q * a[0] + 2 * q * u * mx + u * u * b[0], py = q * q * a[1] + 2 * q * u * my + u * u * b[1];
                            ctx.fillStyle = rgba(C.accent, oa * Math.sin(Math.PI * u));
                            ctx.beginPath();
                            ctx.arc(px, py, 4, 0, TAU);
                            ctx.fill();
                        }
                    },
                });
            flag(-23.8, -9.3, 'kr', t, A);
            flag(-23.8, 4.7, 'cn', t, A);
            flag(19.4, -3.3, 'dz', t + 1, A);
            flag(32.2, -6.4, 'dz', t + 2, A);
            label(-26.5, -9.5, 0, L.korea, A, focus.inspect);
            label(-26.5, 9.5, 0, L.china, A, focus.inspect);
            label(-16, -3.5, 0, L.export, A, focus.buy);
            label(s.x + SHIP_LEN / 2, -1.35, 1.7, L.sea, A, focus.ship);
            label(16, 3.5, 0, L.port, A, focus.customs);
            label(gateX, 1.3, 1.5, L.customs, A, focus.customs);
            label(29, -6.6, 2.6, L.showroom, A, 0);
            label(HOUSE.x, HOUSE.y - 1.6, 2.4, L.home, A, focus.keys);
            ops.sort((a, b) => a.d - b.d).forEach(o => o.f());
            // the hero's mini flow follows the ship's trip
            const stage = s.phase === 'load' ? 'buy' : s.phase === 'sea' ? 'ship' : s.phase === 'port' ? 'customs' : 'keys';
            if (shown !== stage) {
                shown = stage;
                document.documentElement.dataset.stage = stage;
            }
        };
        raf = requestAnimationFrame(draw);
        return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize); };
    })();
}
