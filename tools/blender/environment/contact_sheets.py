"""Compose per-asset renders into labelled contact sheets (system Python + PIL).

    python tools/blender/environment/contact_sheets.py                 # all categories from build_log order
    python tools/blender/environment/contact_sheets.py --preview a b c # ad-hoc sheet -> renders/_preview.png
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVI = os.path.join(ROOT, "work", "lemondev", "bh-001", "evidence", "environment")
REN = os.path.join(EVI, "renders")

SHEETS = {
    "contact_architecture": ["wall_straight", "wall_stone_capped", "wall_corner", "wall_doorway", "wall_window",
                             "wall_broken", "pillar", "pillar_quoin", "pillar_broken", "arch", "arch_quoin", "stairs",
                             "floor_tile_4m", "ceiling_beam", "gate_iron", "rubble_spill"],
    "contact_landmarks": ["bridge_stone", "bridge_wood", "ruin_tower", "temple_facade", "house_intact",
                          "house_destroyed", "market_stall", "well", "fountain", "palisade_fence", "wood_fence",
                          "statue_knight", "statue_collapsed", "teleporter_platform", "teleporter_destroyed",
                          "obelisk_corrupted"],
    "contact_rocks_nature": ["cliff_a", "cliff_b", "rock_large", "rock_medium", "rock_small", "rubble_pile",
                             "tree_dead_a", "tree_dead_b", "tree_pine", "tree_oak_twisted", "bush_a", "bush_b",
                             "grass_clump", "fern", "mushrooms", "roots", "log_fallen", "stump"],
    "contact_crypt": ["altar", "sarcophagus", "coffin", "gravestone_a", "gravestone_b", "ritual_circle", "skull_pile",
                      "bones_scatter", "candles_cluster", "cobweb", "chains_hanging", "spikes_trap_plate",
                      "torch_sconce", "brazier", "bed", "bedroll", "table", "chair", "bookshelf", "rug"],
    "contact_props": ["wagon_broken", "cart_hay", "campfire", "tent_old", "weapon_rack", "weapons_discarded",
                      "banner_torn", "lamp_post", "anvil", "chest", "ladder", "scaffold_platform", "boat_rowing",
                      "winch", "dock_planks"],
    "contact_breakables": ["crate", "crate_fragments", "barrel", "barrel_fragments", "urn", "urn_fragments",
                           "statue_small", "statue_small_fragments"],
}


def sheet(names, out, cols=4, cell=400, title=None):
    names = [n for n in names if os.path.exists(os.path.join(REN, n + ".png"))]
    if not names:
        return None
    rows = (len(names) + cols - 1) // cols
    top = 44 if title else 0
    img = Image.new("RGB", (cols * cell, rows * (cell + 26) + top), (16, 15, 20))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 18)
        tfont = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 28)
    except Exception:
        font = tfont = ImageFont.load_default()
    if title:
        d.text((12, 6), title, fill=(235, 220, 190), font=tfont)
    for i, n in enumerate(names):
        im = Image.open(os.path.join(REN, n + ".png")).convert("RGB").resize((cell, cell), Image.LANCZOS)
        x, y = (i % cols) * cell, (i // cols) * (cell + 26) + top
        img.paste(im, (x, y))
        d.text((x + 8, y + cell + 2), n, fill=(225, 215, 195), font=font)
    img.save(out)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--preview":
        print(sheet(a[1:], os.path.join(REN, "_preview.png"), cols=min(4, max(1, len(a) - 1))))
    else:
        for k, v in SHEETS.items():
            print(sheet(v, os.path.join(EVI, k + ".png"), cols=4, title=k.replace("contact_", "").replace("_", " ").title()))
