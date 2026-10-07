import sys
from PIL import Image, ImageDraw
for f in sys.argv[1:]:
    im = Image.open(f).convert("RGB"); d = ImageDraw.Draw(im); W, H = im.size; sc = W / 2.4   # px per metre, centre x=0, z=0.9
    for i in range(-12, 13):
        x = W / 2 + i * 0.1 * sc
        d.line([(x, 0), (x, H)], fill=(80, 80, 200) if i % 5 else (220, 60, 60), width=1)
        d.text((x + 2, 2), "%.1f" % (i * 0.1), fill=(255, 255, 0))
    for j in range(0, 22):
        z = j * 0.1; y = H / 2 - (z - 0.9) * sc
        d.line([(0, y), (W, y)], fill=(80, 80, 200) if j % 5 else (220, 60, 60), width=1)
        d.text((2, y - 12), "%.1f" % z, fill=(255, 255, 0))
    im.save(f)
