"""One-shot regeneration of all bh-002 UI art + manifest + evidence.

Usage: python tools/ui_art/build_bh002.py [--no-evidence] [--no-godot]
  1. SVG icons/portraits (items2, status2, ui, portraits) via build_all
  2. raster textures (frames, slots, hud, tree, menu) via build_raster (parallel, deterministic)
  3. game/assets/ui/ui_art_manifest.json
  4. evidence: raster contact sheets (native + 0.5x) and 9-slice stretch tests, SVG sheets through Godot ThorVG
     (throwaway project tools/ui_art/godot_render, never the game project), validation.txt
"""
from __future__ import annotations

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main(argv):
    t0 = time.time()
    import build_all
    w = build_all.build(["items2", "status2", "ui", "portraits"])
    print(f"svg: {len(w)} files")
    import build_raster
    r = build_raster.build()
    print(f"raster: {len(r)} textures")
    import manifest_bh002
    p, n = manifest_bh002.build()
    print(f"manifest: {n} entries -> {p}")
    if "--no-evidence" not in argv:
        import raster_sheets
        raster_sheets.main([])
        if "--no-godot" not in argv:
            import svg_evidence
            svg_evidence.main([])
    import validate_bh002
    bad = validate_bh002.main(["--determinism"])
    print(f"done in {time.time() - t0:.0f}s")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
