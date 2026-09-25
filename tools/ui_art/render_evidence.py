"""Rasterise the generated SVGs with Godot 4.4.1's own SVG loader (ThorVG, via Image.load_svg_from_string in a
throwaway headless project under tools/ui_art/godot_render - NOT the game project) and compose contact sheets.

Usage: python tools/ui_art/render_evidence.py [--out DIR] [category ...]
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_all import CATS, UI, ROOT  # noqa: E402

GODOT = os.environ.get("GODOT_BIN", r"A:\Installer\Godot_v4.4.1-stable_win64.exe\Godot_v4.4.1-stable_win64_console.exe")
PROJ = os.path.join(HERE, "godot_render")
EVID = os.path.join(ROOT, "work", "lemondev", "bh-001", "evidence", "ui_art")
BG = (22, 18, 28)
CELL_BG = (34, 28, 42)


def svg_size(path):
    s = open(path, encoding="utf-8").read(400)
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', s)
    return float(m.group(1)), float(m.group(2))


def render(files, px_list, tmp):
    """Returns {(path, px): png_path}. px = target width in pixels."""
    lines, out = [], {}
    for p in files:
        w, h = svg_size(p)
        for px in px_list:
            png = os.path.join(tmp, f"{os.path.basename(os.path.dirname(p))}__{os.path.splitext(os.path.basename(p))[0]}_{px}.png")
            lines.append(f"{p}|{px / w}|{png}")
            out[(p, px)] = png
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    r = subprocess.run([GODOT, "--headless", "--path", PROJ, "--script", "render.gd", "--", lst], capture_output=True, text=True, timeout=600)
    log = (r.stdout or "") + (r.stderr or "")
    return out, log, r.returncode


def font(size):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", size)
    except Exception:
        return ImageFont.load_default()


def sheet(entries, px, title, out_path, cols=None, label=True):
    """entries: list of (name, png_path)."""
    n = len(entries)
    pad = 10 if px <= 64 else 14
    lab_h = 16 if label else 0
    cellw = max(px, 150 if px <= 64 else px) + pad
    cols = cols or max(1, min(n, (1600 // cellw)))
    rows = (n + cols - 1) // cols
    head = 34
    W = cols * cellw + pad
    H = head + rows * (px + lab_h + pad) + pad
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    dr.text((pad, 8), title, fill=(230, 214, 180), font=font(16))
    fs = font(11)
    for i, (name, png) in enumerate(entries):
        c, r = i % cols, i // cols
        x0 = pad + c * cellw
        y0 = head + r * (px + lab_h + pad)
        dr.rectangle([x0 - 2, y0 - 2, x0 + cellw - pad + 1, y0 + px + lab_h + 1], fill=CELL_BG)
        im = Image.open(png).convert("RGBA")
        img.paste(im, (x0 + (cellw - pad - im.width) // 2, y0), im)
        if label:
            tw = dr.textlength(name, font=fs)
            dr.text((x0 + (cellw - pad - tw) / 2, y0 + px + 2), name, fill=(200, 196, 210), font=fs)
    img.save(out_path)
    return out_path


def main(argv):
    out_dir = EVID
    if "--out" in argv:
        i = argv.index("--out")
        out_dir = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    cats = argv or list(CATS.keys())
    os.makedirs(out_dir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="bh_ui_render_")
    report = []
    for cat in cats:
        sub = CATS[cat][0]
        folder = os.path.join(UI, sub)
        files = sorted(os.path.join(folder, x) for x in os.listdir(folder) if x.endswith(".svg"))
        # keep registry order when available
        try:
            import importlib
            reg = getattr(importlib.import_module(CATS[cat][1]), CATS[cat][2])
            order = {k: i for i, k in enumerate(reg.keys())}
            files.sort(key=lambda p: order.get(os.path.splitext(os.path.basename(p))[0], 999))
        except Exception:
            pass
        if cat == "emblem":
            pngs, log, rc = render(files, [128, 512], tmp)
            report.append(f"{cat}: {len(files)} files, godot rc={rc} :: {log.strip().splitlines()[-1] if log.strip() else ''}")
            for p in files:
                nm = os.path.splitext(os.path.basename(p))[0]
                big = pngs[(p, 512)]
                im = Image.open(big).convert("RGBA")
                canvas = Image.new("RGB", (im.width + 40, im.height + 40), BG)
                canvas.paste(im, (20, 20), im)
                canvas.save(os.path.join(out_dir, f"emblem_{nm}_512w.png"))
            sheet([(os.path.splitext(os.path.basename(p))[0], pngs[(p, 128)]) for p in files], 128, "emblem @128px wide",
                  os.path.join(out_dir, "emblem_128.png"), label=True)
            continue
        pngs, log, rc = render(files, [48, 128], tmp)
        last = log.strip().splitlines()[-1] if log.strip() else ""
        report.append(f"{cat}: {len(files)} files, godot rc={rc} :: {last}")
        fails = [l for l in log.splitlines() if l.startswith("FAIL")]
        report.extend("  " + l for l in fails)
        for px in (48, 128):
            ents = [(os.path.splitext(os.path.basename(p))[0], pngs[(p, px)]) for p in files if os.path.exists(pngs[(p, px)])]
            sheet(ents, px, f"{cat} @ {px}px  (rendered by Godot 4.4.1 ThorVG)", os.path.join(out_dir, f"{cat}_{px}.png"))
    print("\n".join(report))
    with open(os.path.join(out_dir, "render_log.txt"), "a", encoding="utf-8") as fh:
        fh.write("\n".join(report) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
