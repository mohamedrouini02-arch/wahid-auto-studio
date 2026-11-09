"""For each photo in a folder: car mask (rembg) and relative depth (Depth Anything V2 small).
python tools/depth_mask.py IN_DIR OUT_DIR   ->  OUT/<name>_mask.png, OUT/<name>_depth.png (16-bit, near = bright)"""
import os, sys, glob
import numpy as np
from PIL import Image
from rembg import remove, new_session
from transformers import pipeline

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
sess = new_session('isnet-general-use')
depth = pipeline('depth-estimation', model='depth-anything/Depth-Anything-V2-Small-hf')
for f in sorted(glob.glob(f'{src}/*.jpg')):
    name = os.path.splitext(os.path.basename(f))[0]
    im = Image.open(f).convert('RGB')
    m = remove(im, session=sess, only_mask=True, post_process_mask=True)
    m.save(f'{out}/{name}_mask.png')
    d = depth(im.resize((1400, int(1400 * im.height / im.width))))['predicted_depth']
    d = np.array(d.squeeze().cpu().numpy() if hasattr(d, 'cpu') else d, dtype=np.float32)
    d = (d - d.min()) / max(1e-6, d.max() - d.min())
    Image.fromarray((d * 65535).astype(np.uint16)).resize(im.size, Image.BICUBIC).save(f'{out}/{name}_depth.png')
    print('done', name, im.size, d.shape, flush=True)
