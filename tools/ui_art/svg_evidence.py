"""bh-002 SVG contact sheets rendered through Godot 4.4.1's ThorVG (throwaway project tools/ui_art/godot_render).

Usage: python tools/ui_art/svg_evidence.py [category ...]   (items2 status2 ui portraits)
"""
from __future__ import annotations

import importlib
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_all import CATS, UI, ROOT  # noqa: E402
from render_evidence import render, sheet  # noqa: E402

EVID = os.path.join(ROOT, "work", "lemondev", "bh-002", "evidence", "ui_art")
NEW = ("items2", "status2", "ui", "portraits")
SIZES = {"items2": (48, 128), "status2": (48, 128), "ui": (32, 48, 128), "portraits": (64, 128, 256)}


def main(argv):
    cats = argv or list(NEW)
    os.makedirs(EVID, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="bh2_svg_")
    log = []
    for cat in cats:
        sub, mod, attr = CATS[cat]
        reg = getattr(importlib.import_module(mod), attr)
        files = [os.path.join(UI, sub, n + ".svg") for n in reg.keys()]
        sizes = SIZES[cat]
        pngs, out, rc = render(files, list(sizes), tmp)
        last = out.strip().splitlines()[-1] if out.strip() else ""
        fails = [l for l in out.splitlines() if l.startswith("FAIL")]
        log.append(f"{cat}: {len(files)} files, godot rc={rc} :: {last}")
        log.extend("  " + l for l in fails)
        for px in sizes:
            ents = [(os.path.splitext(os.path.basename(p))[0], pngs[(p, px)]) for p in files if os.path.exists(pngs[(p, px)])]
            sheet(ents, px, f"{cat} ({sub}) @ {px}px  (rendered by Godot 4.4.1 ThorVG)", os.path.join(EVID, f"svg_{cat}_{px}.png"))
    print("\n".join(log))
    with open(os.path.join(EVID, "svg_render_log.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(log) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
