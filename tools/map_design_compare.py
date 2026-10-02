"""Map-design pass: side-by-side before|after JPGs from the matched captures (output/map-design-20261003/captures/raw).
    python tools/map_design_compare.py [--kind clean|hud] [--quality high|low]
Writes output/map-design-20261003/captures/compare/<view>__<quality>_<kind>.jpg (each half 960 px wide)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "output/map-design-20261003/captures/raw"
OUT = ROOT / "output/map-design-20261003/captures/compare"
kind = sys.argv[sys.argv.index("--kind") + 1] if "--kind" in sys.argv else "clean"
q = sys.argv[sys.argv.index("--quality") + 1] if "--quality" in sys.argv else "high"
OUT.mkdir(parents=True, exist_ok=True)
n = 0
for after in sorted(RAW.glob(f"*__after_{q}_{kind}.png")):
    view = after.name.split("__")[0]
    before = RAW / f"{view}__before_{q}_{kind}.png"
    if not before.exists():
        continue
    a, b = Image.open(before).convert("RGB"), Image.open(after).convert("RGB")
    w = 960
    h = int(a.height * w / a.width)
    a, b = a.resize((w, h), Image.LANCZOS), b.resize((w, h), Image.LANCZOS)
    canvas = Image.new("RGB", (w * 2 + 8, h + 30), (20, 20, 24))
    canvas.paste(a, (0, 30))
    canvas.paste(b, (w + 8, 30))
    d = ImageDraw.Draw(canvas)
    d.text((8, 8), f"{view} - before (HEAD + bh-033)", fill=(230, 230, 230))
    d.text((w + 16, 8), f"{view} - after (map-design pass)", fill=(230, 230, 230))
    canvas.save(OUT / f"{view}__{q}_{kind}.jpg", quality=86)
    n += 1
print(n, "comparisons")
