"""bh-010: validate the new UI SVGs with the bh-001 contract rules (validate.check: XML parse, <svg> root, viewBox,
ThorVG-safe element whitelist, no style/filter/mask/clip-path/href/class, url(#id) refs resolve, full-bleed background
for skill/talent icons) plus the two tree backdrop PNGs (1600x900, fully opaque).
Writes work/lemondev/bh-010/evidence/ui_art/validation.txt (the bh-001 validation.txt is left untouched).

Usage: python tools/ui_art/bh010_validate.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_all import UI, ROOT  # noqa: E402
import validate as v1  # noqa: E402
import bh010_check  # noqa: E402

EVID = os.path.join(ROOT, "work", "lemondev", "bh-010", "evidence", "ui_art")
VIEWBOX = {"icons/skills": "0 0 128 128", "icons/talents": "0 0 128 128", "icons/status": "0 0 128 128",
           "icons/classes": "0 0 256 256", "portraits": "0 0 256 256"}


def main():
    from PIL import Image
    lines = ["bh-010 UI art validation (tools/ui_art/bh010_validate.py, rules from tools/ui_art/validate.py check())", ""]
    total = bad = 0
    for rel in bh010_check.REQUIRED:
        p = os.path.join(UI, rel)
        sub, fn = os.path.split(rel)
        if not os.path.isfile(p):
            lines.append(f"  MISSING {rel}")
            bad += 1
            continue
        total += 1
        if fn.endswith(".png"):
            im = Image.open(p)
            amin = im.convert("RGBA").getextrema()[3][0]
            errs = [] if (im.size == (1600, 900) and amin == 255) else [f"size {im.size} min alpha {amin}"]
            info = f"{im.size[0]}x{im.size[1]} {im.mode} min_alpha={amin}"
        else:
            errs, vb = v1.check(p, sub, fn[:-4])
            errs = [e for e in errs if not e.startswith("viewBox")]  # checked below against the bh-010 sizes
            if vb != VIEWBOX[sub]:
                errs.append(f"viewBox {vb} != {VIEWBOX[sub]}")
            info = f'viewBox="{vb}"'
        bad += bool(errs)
        lines.append(f"  {'OK  ' if not errs else 'FAIL'} {rel}  {info}  {os.path.getsize(p)} bytes" + ("" if not errs else "  -> " + "; ".join(sorted(set(errs)))))
    lines += ["", f"files checked: {total}; failures: {bad}", "RESULT: " + ("PASS" if bad == 0 else "FAIL")]
    os.makedirs(EVID, exist_ok=True)
    with open(os.path.join(EVID, "validation.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[-3:]))
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
