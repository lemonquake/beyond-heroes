"""Compose preview renders into one sheet (system Python + PIL):  python legend_sheet.py out.png a.png b.png ... [--h 600]"""
import sys
from PIL import Image

args = [a for a in sys.argv[1:] if not a.startswith("--")]
h = 600
for a in sys.argv[1:]:
    if a.startswith("--h="):
        h = int(a[4:])
out, files = args[0], args[1:]
ims = [Image.open(f).convert("RGB") for f in files]
ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
s = Image.new("RGB", (sum(i.width for i in ims), h))
x = 0
for i in ims:
    s.paste(i, (x, 0))
    x += i.width
s.save(out)
