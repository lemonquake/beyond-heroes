"""Compose rendered frames into labeled contact sheets (system Python + PIL).

python compose_sheets.py job.json      job = {paths, labels, out, cols, title, cell}
"""
import json
import math
import sys

from PIL import Image, ImageDraw, ImageFont


def font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def compose(paths, labels, out, cols=6, title="", cell=None):
    ims = [Image.open(p).convert("RGB") for p in paths]
    if not ims:
        return
    w, h = ims[0].size
    if cell:
        w, h = cell, cell
        ims = [im.resize((w, h), Image.LANCZOS) for im in ims]
    cols = max(1, min(cols, len(ims)))
    rows = math.ceil(len(ims) / cols)
    lab_h = max(18, h // 14)
    top = lab_h * 2 if title else 0
    sheet = Image.new("RGB", (cols * w, top + rows * (h + lab_h)), (18, 18, 24))
    d = ImageDraw.Draw(sheet)
    f = font(int(lab_h * 0.72))
    if title:
        d.text((8, lab_h * 0.4), title, fill=(235, 225, 200), font=font(int(lab_h * 1.1)))
    for i, (im, lab) in enumerate(zip(ims, labels)):
        x = (i % cols) * w
        y = top + (i // cols) * (h + lab_h)
        sheet.paste(im, (x, y + lab_h))
        d.text((x + 6, y + 2), lab, fill=(220, 220, 230), font=f)
    sheet.save(out)
    print("[compose]", out, sheet.size)


if __name__ == "__main__":
    job = json.load(open(sys.argv[1]))
    compose(job["paths"], job["labels"], job["out"], job.get("cols", 6), job.get("title", ""), job.get("cell"))
