"""Shared material contract for the bh-018 trade quarters (shop stands and crafting stations).

Every name here also exists in game/src/world/material_library.gd ENV (the game swaps imported materials by name),
so a stand looks the same in Blender previews and in Godot. Export colours are linear previews only.
Import this module (``import market_common``) before building any stand.
"""
import kit

EXTRA_MATERIALS = {
    #  name              base colour (linear)            rough metal  emission (colour, strength)
    "BH_ClothGreen":   ((0.035, 0.09, 0.03, 1), 0.93, 0.0, None),    # provisions / herbs canvas
    "BH_ClothOchre":   ((0.33, 0.18, 0.03, 1), 0.93, 0.0, None),     # mustard field canvas
    "BH_ClothTeal":    ((0.02, 0.12, 0.13, 1), 0.9, 0.0, None),      # jeweller's canopy
    "BH_ClothCream":   ((0.5, 0.43, 0.3, 1), 0.93, 0.0, None),       # undyed linen
    "BH_ClothBlack":   ((0.012, 0.011, 0.013, 1), 0.95, 0.0, None),  # the stranger's wagon cover
    "BH_ClothBlue":    ((0.025, 0.06, 0.22, 1), 0.92, 0.0, None),
    "BH_ClothViolet":  ((0.07, 0.025, 0.14, 1), 0.92, 0.0, None),
    "BH_Velvet":       ((0.12, 0.008, 0.03, 1), 0.7, 0.0, None),     # deep wine velvet (display beds)
    "BH_Leather":      ((0.07, 0.035, 0.018, 1), 0.75, 0.0, None),
    "BH_Copper":       ((0.55, 0.22, 0.1, 1), 0.4, 1.0, None),
    "BH_Verdigris":    ((0.1, 0.3, 0.24, 1), 0.8, 0.3, None),        # weathered copper roofing
    "BH_Slate":        ((0.05, 0.055, 0.065, 1), 0.8, 0.0, None),
    "BH_Brass":        ((0.55, 0.38, 0.12, 1), 0.35, 1.0, None),
    "BH_Silver":       ((0.6, 0.62, 0.66, 1), 0.3, 1.0, None),
    "BH_Paper":        ((0.6, 0.52, 0.36, 1), 0.9, 0.0, None),
    "BH_Rope":         ((0.3, 0.22, 0.12, 1), 0.95, 0.0, None),
    "BH_Bottle":       ((0.04, 0.12, 0.05, 1), 0.08, 0.0, None),
    # glowing liquids / crystals (small emissive accents only, never large surfaces)
    "BH_GemRed":       ((0.6, 0.04, 0.03, 1), 0.15, 0.0, ((1.0, 0.18, 0.12), 3.0)),
    "BH_GemAmber":     ((0.7, 0.3, 0.03, 1), 0.15, 0.0, ((1.0, 0.55, 0.12), 3.0)),
    "BH_GemAqua":      ((0.03, 0.3, 0.6, 1), 0.12, 0.0, ((0.25, 0.7, 1.0), 3.0)),
    "BH_GemGreen":     ((0.06, 0.45, 0.08, 1), 0.15, 0.0, ((0.35, 1.0, 0.3), 3.0)),
    "BH_GemGold":      ((0.7, 0.55, 0.2, 1), 0.15, 0.0, ((1.0, 0.85, 0.45), 3.0)),
    "BH_GemViolet":    ((0.3, 0.08, 0.6, 1), 0.15, 0.0, ((0.7, 0.35, 1.0), 3.0)),
    "BH_Coals":        ((0.5, 0.1, 0.02, 1), 0.7, 0.0, ((1.0, 0.3, 0.05), 5.0)),
}
for _n, _v in EXTRA_MATERIALS.items():
    kit.MATERIALS.setdefault(_n, _v)
    if _n not in kit.MATERIAL_NAMES:
        kit.MATERIAL_NAMES.append(_n)
