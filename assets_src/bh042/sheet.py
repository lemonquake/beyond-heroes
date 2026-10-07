import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; items = [x.split("|") for x in sys.argv[2].split(";") if x]
ims = [(Image.open(f).convert("RGB"), c) for f, c in items]
cols = min(6, len(ims)); rows = (len(ims) + cols - 1) // cols
w, h = ims[0][0].size
S = Image.new("RGB", (w * cols, h * rows), (30, 30, 34))
for i, (im, c) in enumerate(ims):
    S.paste(im, ((i % cols) * w, (i // cols) * h))
    ImageDraw.Draw(S).text(((i % cols) * w + 6, (i // cols) * h + 6), c, fill=(255, 255, 255))
S.save(out)
