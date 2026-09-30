import sys
from PIL import Image
out, cols, h = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
ims = [Image.open(p).convert("RGB") for p in sys.argv[4:]]
ims = [im.resize((int(im.width * h / im.height), h), Image.LANCZOS) for im in ims]
rows = [ims[i:i + cols] for i in range(0, len(ims), cols)]
W = max(sum(im.width for im in r) for r in rows)
sheet = Image.new("RGB", (W, h * len(rows)), (20, 20, 24))
y = 0
for r in rows:
    x = 0
    for im in r:
        sheet.paste(im, (x, y)); x += im.width
    y += h
sheet.save(out)
print(out, sheet.size)
