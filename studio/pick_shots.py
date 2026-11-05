"""Look at a car's photos and video and decide which shot goes where.

Uses a small open image model (CLIP) to tell front / side / rear / dashboard /
seats / boot / door close-ups apart, drops near-duplicates and weak shots, and
returns the best media for each part of the script.
"""
import os, subprocess, tempfile, urllib.request
import numpy as np
from PIL import Image, ImageOps

KINDS = {
    'front': 'a photo of the front of a car, headlights and grille',
    'front34': 'a photo of a whole car from the front three-quarter angle',
    'side': 'a side view photo of a whole car',
    'rear': 'a photo of the back of a car with tail lights',
    'dash': 'a photo of a car dashboard with the steering wheel',
    'gear': 'a photo of a car gear shifter and center console',
    'seats': 'a photo of the front seats inside a car',
    'rearseats': 'a photo of the back seats inside a car',
    'trunk': 'a photo of an open car trunk',
    'door': 'a close-up photo of the inside of a car door panel',
    'other': 'a photo of trees, buildings or a parking lot without a clear car',
}
EXTERIOR = ['front34', 'front', 'side', 'rear']
INTERIOR = ['dash', 'gear', 'seats', 'rearseats', 'trunk']

_model = None


def model():
    global _model
    if _model is None:
        import open_clip, torch
        m, _, pre = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
        tok = open_clip.get_tokenizer('ViT-B-32')
        with torch.no_grad():
            t = m.encode_text(tok(list(KINDS.values())))
            t /= t.norm(dim=-1, keepdim=True)
        _model = (m.eval(), pre, t)
    return _model


def embed(images):
    import torch
    m, pre, text = model()
    with torch.no_grad():
        x = torch.stack([pre(im) for im in images])
        f = m.encode_image(x); f /= f.norm(dim=-1, keepdim=True)
        probs = (100 * f @ text.T).softmax(dim=-1)
    return f.numpy(), probs.numpy()


def load(src, dest):
    if src.startswith('http'): urllib.request.urlretrieve(src, dest)
    return dest if src.startswith('http') else src


def analyse(photos, video=None):
    """Return {'photos': [(index, kind, score)], 'video': [(second, kind, score)], 'length': s}."""
    tmp = tempfile.mkdtemp()
    ims = []
    for i, p in enumerate(photos):
        im = ImageOps.exif_transpose(Image.open(load(p, os.path.join(tmp, f'p{i}.jpg')))).convert('RGB')
        im.thumbnail((512, 512)); ims.append(im)
    out = {'photos': [], 'video': [], 'length': 0}
    if ims:
        feats, probs = embed(ims)
        keep = []
        for i in range(len(ims)):
            # skip near-duplicates of a photo we already kept
            if any(float(feats[i] @ feats[j]) > 0.95 for j in keep): continue
            keep.append(i)
            k = int(probs[i].argmax())
            out['photos'].append((i, list(KINDS)[k], float(probs[i][k])))
    if video:
        v = load(video, os.path.join(tmp, 'v.mp4'))
        d = os.path.join(tmp, 'frames'); os.makedirs(d)
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', v, '-vf', 'fps=1,scale=512:-1', f'{d}/%04d.jpg'], check=True)
        frames = sorted(os.listdir(d))
        out['length'] = len(frames)
        if frames:
            _, probs = embed([Image.open(os.path.join(d, f)).convert('RGB') for f in frames])
            for s, p in enumerate(probs):
                k = int(p.argmax()); out['video'].append((s, list(KINDS)[k], float(p[k])))
    return out


def best(items, kinds, used, n=1):
    """Pick up to n items whose kind is in kinds (in that order of preference), not used yet."""
    picked = []
    for kind in kinds:
        for it in sorted((x for x in items if x[1] == kind and x[0] not in used), key=lambda x: -x[2]):
            picked.append(it); used.add(it[0])
            if len(picked) == n: return picked
    return picked


def video_runs(frames, kinds, min_len=2):
    """Start seconds of steady stretches of the video showing one of kinds (good for a 2-3 s shot)."""
    runs, start = [], None
    for s, k, _ in frames + [(len(frames), None, 0)]:
        if k in kinds and start is None: start = s
        if k not in kinds and start is not None:
            if s - start >= min_len: runs.append((start, s - start))
            start = None
    return sorted(runs, key=lambda r: -r[1])
