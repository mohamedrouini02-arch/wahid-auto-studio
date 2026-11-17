"""Find the wall clock (hub, hands, numbers) in a frame of the prices video and paint it out.
clock_mask(frame) -> uint8 mask of the clock pixels, never on the person
clean(frame, mask) -> frame with the masked pixels filled from the wall around them"""
import numpy as np, cv2

def split(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32) / 255
    wall = ((hsv[..., 2] > 0.55) & (hsv[..., 1] < 0.16)).astype(np.uint8)
    non = cv2.morphologyEx(1 - wall, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return hsv, non

def person_mask(frame):
    """Him, as one blob: the wall is light and grey; a wide opening cuts the thin clock hand off his hair."""
    H, W = frame.shape[:2]; k = W / 1080
    hsv, non = split(frame)
    op = cv2.morphologyEx(non, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(31 * k) | 1,) * 2))
    n, lab, st, _ = cv2.connectedComponentsWithStats(op)
    big = 1 + np.argmax(st[1:, 4]); body = (lab == big).astype(np.uint8)
    # give back the fine edge (hair, fingers) that the opening took, but only next to the body
    near = cv2.dilate(body, np.ones((int(15 * k) | 1,) * 2, np.uint8))
    person = np.maximum(body, non & near)
    # fill the light patches of the jacket: anything the outside wall can't reach is him
    ff = (1 - person).copy(); pad = np.zeros((H + 2, W + 2), np.uint8)
    for x in range(0, W, max(1, W // 40)):
        for y in (0, H - 1):
            if ff[y, x] == 1: cv2.floodFill(ff, pad, (x, y), 2)
    for y in range(0, H, max(1, H // 40)):
        for x in (0, W - 1):
            if ff[y, x] == 1: cv2.floodFill(ff, pad, (x, y), 2)
    person = (ff != 2).astype(np.uint8)
    return person, hsv, non

def clock_mask(frame):
    H, W = frame.shape[:2]; k = W / 1080
    person, hsv, non = person_mask(frame)
    m = non & (1 - person)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    keep = np.zeros_like(m)
    for i in range(1, n):
        if st[i, 4] > 18 * k * k: keep[lab == i] = 1
    keep = cv2.dilate(keep, np.ones((int(19 * k) | 1,) * 2, np.uint8))
    keep &= 1 - cv2.dilate(person, np.ones((int(5 * k) | 1,) * 2, np.uint8))
    return keep, person

def clean(frame, m, seed=0):
    out = cv2.inpaint(frame, m, int(15 * frame.shape[1] / 1080), cv2.INPAINT_TELEA)
    rng = np.random.default_rng(seed)
    noise = cv2.GaussianBlur(rng.standard_normal(frame.shape[:2]).astype(np.float32), (0, 0), 1.2) * 6
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3)[..., None]
    return np.clip(out + noise[..., None] * a, 0, 255).astype(np.uint8)
