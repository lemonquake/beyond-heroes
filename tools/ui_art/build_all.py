"""Generate every Beyond Heroes UI SVG into game/assets/ui/.

Usage:  python tools/ui_art/build_all.py [category ...]
Categories: skills talents items elements status attributes classes emblem items2 status2 ui portraits
            skills10 talents10 status10 classes10 portraits10 (bh-010)
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
UI = os.path.join(ROOT, "game", "assets", "ui")


CATS = {
    "skills": ("icons/skills", "icons_skills", "SKILLS"),
    "talents": ("icons/talents", "icons_talents", "TALENTS"),
    "items": ("icons/items", "icons_items", "ITEMS"),
    "elements": ("icons/elements", "icons_badges", "ELEMENTS"),
    "status": ("icons/status", "icons_badges", "STATUS"),
    "attributes": ("icons/attributes", "icons_badges", "ATTRIBUTES"),
    "classes": ("icons/classes", "icons_crests", "CLASSES"),
    "emblem": ("emblem", "icons_crests", "EMBLEM"),
    # bh-002 additions
    "items2": ("icons/items", "icons_items2", "ITEMS2"),
    "status2": ("icons/status", "icons_status2", "STATUS2"),
    "ui": ("icons/ui", "icons_ui", "UI_ICONS"),
    "portraits": ("portraits", "portraits", "PORTRAITS"),
    # bh-010 additions (ranger / shadowblade heroes, knight auras + passives, mage passives)
    "skills10": ("icons/skills", "icons_skills_bh010", "SKILLS10"),
    "talents10": ("icons/talents", "bh010_talents", "TALENTS10"),
    "status10": ("icons/status", "bh010_status", "STATUS10"),
    "classes10": ("icons/classes", "bh010_classes", "CLASSES10"),
    "portraits10": ("portraits", "bh010_classes", "PORTRAITS10"),
}


def registries(cats=None):
    import importlib
    out = {}
    for cat, (sub, mod, attr) in CATS.items():
        if cats and cat not in cats:
            continue
        out[cat] = (sub, getattr(importlib.import_module(mod), attr))
    return out


def build(cats=None):
    regs = registries(cats)
    written = []
    for cat, (sub, reg) in regs.items():
        out = os.path.join(UI, sub)
        os.makedirs(out, exist_ok=True)
        for name, fn in reg.items():
            d = fn()
            p = os.path.join(out, name + ".svg")
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(d.svg())
            written.append((cat, p))
    return written


if __name__ == "__main__":
    w = build(sys.argv[1:] or None)
    from collections import Counter
    c = Counter(cat for cat, _ in w)
    for k, v in c.items():
        print(f"{k}: {v}")
    print("total", len(w))
