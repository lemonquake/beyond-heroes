"""bh-010 evidence rasteriser: renders SVGs through Godot 4.4.1's ThorVG (the throwaway headless project in
tools/ui_art/godot_render - never the game project) and composes labelled contact sheets with PIL.

Usage (dev preview):  python tools/ui_art/bh010_render.py OUT.png PX file.svg [file.svg ...]
"""
from __future__ import annotations

import os
import sys
import tempfile

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from render_evidence import render, font, BG, CELL_BG  # noqa: E402


def render_many(files, sizes):
    """-> ({(path, px): PIL image}, log, rc)"""
    tmp = tempfile.mkdtemp(prefix="bh010_svg_")
    files = [os.path.abspath(p) for p in files]
    pngs, log, rc = render(files, list(sizes), tmp)
    out = {}
    for k, p in pngs.items():
        if os.path.exists(p):
            out[k] = Image.open(p).convert("RGBA")
    return out, log, rc


def sheet(entries, title, out_path, cols=None, label=True, min_cell=None, groups=None):
    """entries: list of (name, PIL image). groups: optional list of (heading, [entries]) instead of entries."""
    if groups is None:
        groups = [(None, entries)]
    allims = [im for _, ents in groups for _, im in ents]
    cw = max(im.width for im in allims)
    ch = max(im.height for im in allims)
    pad = 10 if cw <= 64 else 14
    lab_h = 16 if label else 0
    cellw = max(cw, min_cell or (132 if cw <= 64 else cw)) + pad
    maxn = max(len(e) for _, e in groups)
    cols = cols or max(1, min(maxn, 1800 // cellw))
    head = 34
    gh = 24
    H = head
    for g, ents in groups:
        rows = (len(ents) + cols - 1) // cols
        H += (gh if g else 0) + rows * (ch + lab_h + pad)
    H += pad
    W = cols * cellw + pad
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 8), title, fill=(230, 214, 180), font=font(16))
    fs = font(11)
    y = head
    for g, ents in groups:
        if g:
            dr.text((pad, y + 2), g, fill=(190, 170, 130), font=font(14))
            y += gh
        for i, (name, im) in enumerate(ents):
            c, r = i % cols, i // cols
            x0 = pad + c * cellw
            y0 = y + r * (ch + lab_h + pad)
            dr.rectangle([x0 - 2, y0 - 2, x0 + cellw - pad + 1, y0 + ch + lab_h + 1], fill=CELL_BG)
            img.paste(im, (x0 + (cellw - pad - im.width) // 2, y0 + (ch - im.height) // 2), im)
            if label:
                tw = dr.textlength(name, font=fs)
                dr.text((x0 + (cellw - pad - tw) / 2, y0 + ch + 2), name, fill=(200, 196, 210), font=fs)
        y += ((len(ents) + cols - 1) // cols) * (ch + lab_h + pad)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path)
    return out_path


if __name__ == "__main__":
    out, px, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    ims, log, rc = render_many(files, [px])
    print(log.strip().splitlines()[-1] if log.strip() else "", "rc", rc)
    files = [os.path.abspath(p) for p in files]
    ents = [(os.path.splitext(os.path.basename(p))[0], ims[(p, px)]) for p in files if (p, px) in ims]
    sheet(ents, os.path.basename(out), out)
