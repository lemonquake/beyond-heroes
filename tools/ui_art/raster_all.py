"""Registry of every raster builder, keyed by path relative to game/assets/ui (without .png)."""
from __future__ import annotations

import importlib

MODULES = [("frames", "raster_frames", "FRAMES"), ("slots", "raster_slots", "SLOTS"), ("hud", "raster_hud", "HUD"), ("tree", "raster_tree", "TREE"), ("menu", "raster_menu", "MENU"),
           # bh-010 additions
           ("tree", "bh010_tree", "TREE10")]


def builders():
    out = {}
    for folder, mod, attr in MODULES:
        reg = getattr(importlib.import_module(mod), attr)
        for name, (fn, meta) in reg.items():
            out[f"{folder}/{name}"] = (fn, meta)
    return out
