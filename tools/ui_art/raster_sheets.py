"""Contact sheets + 9-slice stretch tests for the raster UI art (evidence for bh-002).

Usage: python tools/ui_art/raster_sheets.py [--out DIR] [folder ...]
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_raster import UI, ROOT  # noqa: E402

EVID = os.path.join(ROOT, "work", "lemondev", "bh-002", "evidence", "ui_art")
BG = (20, 16, 22)
CELL = (30, 25, 33)
CHECK = ((44, 38, 48), (34, 29, 38))


def font(size):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", size)
    except Exception:
        return ImageFont.load_default()


def checker(w, h, s=16):
    im = Image.new("RGB", (w, h), CHECK[0])
    dr = ImageDraw.Draw(im)
    for y in range(0, h, s):
        for x in range(0, w, s):
            if (x // s + y // s) % 2:
                dr.rectangle([x, y, x + s - 1, y + s - 1], fill=CHECK[1])
    return im


def contact(entries, title, out_path, scale=1.0, max_w=2400, max_cell=None):
    """entries: [(label, PIL RGBA)] -> shelf-packed sheet on a dark checker so alpha is visible."""
    pad, lab = 14, 18
    ims = []
    for name, im in entries:
        if scale != 1.0:
            im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
        if max_cell and max(im.size) > max_cell:
            k = max_cell / max(im.size)
            im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
            name += f" (shown {k * scale:.2f}x)"
        ims.append((name, im))
    rows, row, x, rh = [], [], pad, 0
    fs = font(12)
    for name, im in ims:
        cw = max(im.width, int(fs.getlength(name)) + 6)
        if row and x + cw + pad > max_w:
            rows.append((row, rh))
            row, x, rh = [], pad, 0
        row.append((name, im, x, cw))
        x += cw + pad
        rh = max(rh, im.height)
    if row:
        rows.append((row, rh))
    W = max_w if len(rows) > 1 else max(x for x in [pad + sum(cw + pad for _, _, _, cw in rows[0][0])])
    H = 40 + sum(rh + lab + pad for _, rh in rows) + pad
    sheet = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(sheet)
    dr.text((pad, 10), title, fill=(232, 214, 176), font=font(17))
    y = 40
    for row, rh in rows:
        for name, im, x0, cw in row:
            cell = checker(cw, rh)
            sheet.paste(cell, (x0, y))
            px = x0 + (cw - im.width) // 2
            sheet.paste(im, (px, y + (rh - im.height) // 2), im)
            dr.text((x0, y + rh + 2), name, fill=(200, 194, 208), font=fs)
        y += rh + lab + pad
    sheet.save(out_path, optimize=True)
    return out_path


def load(folder):
    import raster_all
    out = []
    for key, (fn, meta) in raster_all.builders().items():
        if key.split("/")[0] != folder:
            continue
        p = os.path.join(UI, key + ".png")
        if os.path.exists(p):
            out.append((key.split("/", 1)[1], Image.open(p).convert("RGBA"), meta))
    return out


def stretch_tests(entries, out_base, sizes=((300, 120), (800, 500), (1400, 220)), page_h=1900):
    """Each 9-slice texture stretched (texture px, NinePatchRect STRETCH semantics) into three target rects.
    Textures flagged stretch='h' / 'v' keep their native height / width. Paginates; returns written paths."""
    from rast import nine_slice
    pad = 16
    blocks = []
    for name, im, meta in entries:
        if not meta.get("margins"):
            continue
        l, t, r, b = meta["margins"]
        mode = meta.get("stretch", "both")
        tiles = []
        for (w, h) in sizes:
            if mode == "h":
                w, h = w, im.height
            elif mode == "v":
                w, h = im.width, max(h, 120) if h < 300 else h
            tiles.append(nine_slice(im, meta["margins"], (max(w, l + r + 2), max(h, t + b + 2)), 1.0))
        blocks.append((name, meta["margins"], mode, tiles))
    W = max(1600, pad + sum(max(t.width for t in tl) for *_, tl in blocks[:1]) + pad * 4)
    W = max(W, max(pad + sum(t.width + pad for t in tl) for *_, tl in blocks))
    pages, cur, h = [], [], 40
    for bl in blocks:
        bh = max(t.height for t in bl[3]) + 30
        if cur and h + bh > page_h:
            pages.append(cur)
            cur, h = [], 40
        cur.append(bl)
        h += bh
    if cur:
        pages.append(cur)
    out = []
    fs = font(12)
    for pi, page in enumerate(pages):
        H = 40 + sum(max(t.height for t in tl) + 30 for *_, tl in page)
        sheet = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(sheet)
        dr.text((pad, 10), f"9-slice stretch tests, page {pi + 1}/{len(pages)} (texture px; margins from ui_art_manifest.json; "
                           "sizes 300x120 / 800x500 / 1400x220, 'h'/'v' textures keep native cross size)",
                fill=(232, 214, 176), font=font(16))
        y = 40
        for name, m, mode, tiles in page:
            dr.text((pad, y), f"{name}  margins={m}  stretch={mode}", fill=(200, 194, 208), font=fs)
            x = pad
            for t in tiles:
                sheet.paste(checker(t.width, t.height), (x, y + 16))
                sheet.paste(t, (x, y + 16), t)
                x += t.width + pad
            y += max(t.height for t in tiles) + 30
        p = f"{out_base}_{pi + 1}.png"
        sheet.save(p, optimize=True)
        out.append(p)
    return out


def main(argv):
    out = EVID
    if "--out" in argv:
        i = argv.index("--out")
        out = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    os.makedirs(out, exist_ok=True)
    folders = argv or ["frames", "slots", "hud", "tree", "menu"]
    written = []
    for folder in folders:
        ents = load(folder)
        if not ents:
            continue
        big = [(n, im) for n, im, m in ents]
        written.append(contact(big, f"{folder}/ at native texture size (2x authoring; dark checker = transparent)",
                               os.path.join(out, f"raster_{folder}_native.png"), 1.0, max_cell=1100))
        written.append(contact(big, f"{folder}/ at 0.5x (intended 1080p draw size)",
                               os.path.join(out, f"raster_{folder}_half.png"), 0.5, max_cell=700))
        nine = [(n, im, m) for n, im, m in ents if m.get("margins")]
        if nine:
            for old in os.listdir(out):
                if old.startswith(f"ninepatch_{folder}"):
                    os.remove(os.path.join(out, old))
            written.extend(stretch_tests(nine, os.path.join(out, f"ninepatch_{folder}")))
    for w in written:
        print(w)


if __name__ == "__main__":
    main(sys.argv[1:])
