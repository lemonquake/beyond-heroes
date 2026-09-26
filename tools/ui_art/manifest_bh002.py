"""Write game/assets/ui/ui_art_manifest.json for every bh-002 texture (raster + SVG).

Raster entries: {"margins": [l, t, r, b] | null (texture px), "use": str, "scale": draw scale, "size": [w, h], ...extras}
SVG entries:    {"margins": null, "use": str, "scale": null, "viewbox": "0 0 w h", "kind": "svg"}
"""
from __future__ import annotations

import importlib
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_all import CATS, UI  # noqa: E402

ABOUT = {
    "margins": None,
    "scale": None,
    "use": ("Beyond Heroes bh-002 UI art manifest. Raster textures are authored at 2x: 'margins' are 9-slice patch margins "
            "in TEXTURE pixels (left, top, right, bottom; null = not a 9-slice) and 'scale' is the intended draw scale at "
            "1920x1080 (0.5 = draw at half texel size, i.e. margins on screen = margins*scale; at 3840x2160 with the "
            "canvas_items stretch the same logical size maps 1:1 to texels). 'stretch' tells which axes may be stretched "
            "(both | h | v). 'content_margins' (texture px) is the padding for content inside the frame; 'expand_margins' "
            "(texture px) is transparent glow padding outside the visual edge. Centres of panel textures are periodic noise, "
            "so AXIS_STRETCH_MODE_TILE/TILE_FIT or STRETCH both work. Cursors are 1:1 with 'hotspot' in px. "
            "Regenerate everything with: python tools/ui_art/build_bh002.py"),
}

SVG_USE = {
    "items2": "Item icon (bh-002 tier/set/unique/consumable/material/quest), transparent background, 128 viewBox.",
    "status2": "Status-effect badge (bh-002), 128 viewBox, same frame as bh-001 status icons.",
    "ui": "Interface glyph, 64 viewBox, near-white body + dark outline: modulate to tint; draw 24-64 px.",
    "portraits": "Character portrait bust with vignette background and ornate frame, 256 viewBox (HUD, save slots, dialogue).",
}


def build():
    import raster_all
    out = {"_about": ABOUT}
    for key, (fn, meta) in raster_all.builders().items():
        rel = key + ".png"
        p = os.path.join(UI, rel)
        e = dict(meta)
        e.setdefault("stretch", "both" if e.get("margins") else None)
        if os.path.exists(p):
            e["size"] = list(Image.open(p).size)
        out[rel] = {k: v for k, v in e.items() if v is not None or k in ("margins", "scale")}
    for cat, use in SVG_USE.items():
        sub, mod, attr = CATS[cat]
        reg = getattr(importlib.import_module(mod), attr)
        vb = {"items2": "0 0 128 128", "status2": "0 0 128 128", "ui": "0 0 64 64", "portraits": "0 0 256 256"}[cat]
        for name in reg:
            out[f"{sub}/{name}.svg"] = {"margins": None, "use": use, "scale": None, "viewbox": vb, "kind": "svg"}
    path = os.path.join(UI, "ui_art_manifest.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, sort_keys=False)
        fh.write("\n")
    return path, len(out) - 1


if __name__ == "__main__":
    p, n = build()
    print(p, n, "entries")
