"""Featured car photo: crop the whole car away from the dealer watermark, replace the red dealer plate with a Wahid Auto plate."""
import sys, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
src, out, y0, zoom = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
im = cv2.imread(src); H, W = im.shape[:2]
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
red = (((hsv[..., 0] < 8) | (hsv[..., 0] > 172)) & (hsv[..., 1] > 120) & (hsv[..., 2] > 80)).astype(np.uint8)
red[: int(H * .35)] = 0
red = cv2.morphologyEx(red, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(red)
best = None
for i in range(1, n):
    x, y, w, h, a = st[i]
    if w > W * .05 and 2.2 < w / max(h, 1) < 7 and a > .5 * w * h:
        if best is None or a > best[4]: best = (x, y, w, h, a)
zone = np.zeros((H, W), np.uint8)
spec = sys.argv[5] if len(sys.argv) > 5 else "0-.30:.55"
if ":" not in spec: spec = f"0-{spec}:{sys.argv[6] if len(sys.argv) > 6 else .55}"
tzone = np.zeros((H, W), np.uint8)
for z in spec.split(","):
    tgt = zone
    if z.startswith("t"): z = z[1:]; tgt = tzone
    ys, xs = z.split(":"); ya, yb = ys.split("-")
    tgt[int(H * float(ya)): int(H * float(yb)), int(W * float(xs)):] = 1
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
bgest = cv2.medianBlur(g.astype(np.uint8), 41).astype(np.float32)
mark = ((np.abs(g - bgest) > 14) | (hsv[..., 1] > 70) | (red_all := (((hsv[..., 0] < 10) | (hsv[..., 0] > 170)) & (hsv[..., 1] > 90)))) & (zone > 0)
mark = cv2.dilate(mark.astype(np.uint8) * 255, np.ones((15, 15), np.uint8))
if tzone.any():   # small letters only: thin bright/dark marks, not the car body
    diff = (np.abs(g - bgest) > 22).astype(np.uint8) * (tzone > 0)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(diff)
    small = np.isin(lab2, [i for i in range(1, n2) if st2[i, 4] < W * H * 0.0012 and st2[i, 3] < H * 0.05])
    mark = np.maximum(mark, cv2.dilate(small.astype(np.uint8) * 255, np.ones((11, 11), np.uint8)))
im = cv2.inpaint(im, mark, 12, cv2.INPAINT_TELEA)
pil = Image.fromarray(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
if best:
    x, y, w, h, _ = best; p = max(2, int(h * .08))
    d = ImageDraw.Draw(pil)
    d.rounded_rectangle([x - p, y - p, x + w + p, y + h + p], radius=int(h * .18), fill=(18, 21, 20))
    d.rounded_rectangle([x - p + 3, y - p + 3, x + w + p - 3, y + h + p - 3], radius=int(h * .15), outline=(95, 184, 155), width=max(2, int(h * .05)))
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', int(h * .5))
    t = 'WAHID AUTO'; tw = d.textlength(t, font=f)
    if tw > w * .9: f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', int(h * .5 * w * .9 / tw)); tw = d.textlength(t, font=f)
    d.text((x + w / 2 - tw / 2, y + h / 2), t, font=f, fill=(242, 242, 238), anchor='lm')
    print('plate', best[:4])
# crop: 3:2, top at y0*H, height = (1-y0)*H/zoom, centred on the car horizontally
ch = (1 - y0) * H / zoom; cw = ch * 1.5
if cw > W: cw = W; ch = cw / 1.5
cx = W / 2; x1 = int(np.clip(cx - cw / 2, 0, W - cw)); y1 = int(y0 * H)
pil = pil.crop((x1, y1, int(x1 + cw), int(y1 + ch))).resize((1500, 1000), Image.LANCZOS)
pil.save(out, 'WEBP', quality=82)
