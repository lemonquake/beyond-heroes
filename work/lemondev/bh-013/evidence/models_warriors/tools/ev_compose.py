"""Compose an ev_blender manifest into a labelled contact sheet (system Python + PIL).
python ev_compose.py manifest.json out.png [title]"""
import json
import sys

from PIL import Image, ImageDraw, ImageFont


def main():
    man = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else man["character"]
    R = man["res"]
    rows = man["rows"]
    ncol = max(len(r) for r in rows)
    TH = 34
    sheet = Image.new("RGB", (ncol * R, TH + len(rows) * R), (18, 18, 22))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 15)
        tfont = ImageFont.truetype("arialbd.ttf", 20)
    except Exception:
        font = tfont = ImageFont.load_default()
    d.text((8, 6), title, fill=(235, 235, 235), font=tfont)
    for i, r in enumerate(rows):
        for j, t in enumerate(r):
            im = Image.open(t["path"]).convert("RGB")
            if "crop" in t:
                im = im.crop(tuple(t["crop"]))
            im = im.resize((R, R), Image.LANCZOS if "crop" not in t else Image.NEAREST)
            x, y = j * R, TH + i * R
            sheet.paste(im, (x, y))
            d.rectangle((x, y, x + len(t["label"]) * 7 + 10, y + 20), fill=(0, 0, 0))
            d.text((x + 4, y + 2), t["label"], fill=(255, 255, 210), font=font)
    sheet.save(out)
    print("SHEET", out, sheet.size)


if __name__ == "__main__":
    main()
