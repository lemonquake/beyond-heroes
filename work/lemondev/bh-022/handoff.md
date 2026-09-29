# BH-022 — socket visuals, infused names, safe-haven waypoints, Mythic/Eternal Tempos, rebuilt boss collections

State: **IMPLEMENTED — UNVERIFIED** under lemondev's full protocol (no independent blind critic was run; evidence below is
the builder's own real-renderer captures and automated tests). Baseline: `main` at `15a638f`.

## What changed

1. **Socket visuals** — `SocketArt` (`game/src/ui/widgets/socket_art.gd`) draws bronze socket bezels with their crystals
   (cut by grade) on every `ItemSlot` (bag, equipment, shop, vault) and as a strip in tooltips; socketed pieces glow in
   the blended crystal colour; held weapons shed infusion motes (`CharacterVisual.set_weapon_infusion`).
   Sprites: `tools/ui_art/bh022_sockets.py` → `game/assets/ui/slots/socket_*.png` (33).
2. **Infused names** — `CrystalNames` (`game/src/core/items/crystal_names.gd`): 32 single names, 28 hybrids,
   Grand/Eternal, third-family epithets, Fourfold/Prismatic. `ItemInstance.display_name()` and the tooltip header use
   it. Table: `docs/CRYSTAL_NAMES.md`.
3. **Waypoints** — `gate_shrine` (South Gate fork) and `mill_shrine` (Old Mill Crossroads) in Westreach, added to
   `DataIsland.NETWORK`; atlas draws a crossroads with a shrine as a shrine.
4. **Tempo tiers** — `DataTempos.RENOWNED_TIERS`: Mythic (level 25+, 85%) and Eternal (level 45+, 95%) replace the
   shrine's five and the 5-star pool; 20 new spirits + 20 unique skills, 10 portraits (`tools/ui_art/bh022_tempos.py`);
   tier glow in the world; guide and Tempo-Caller pages list the tiers. Bound spirits keep their tier.
5. **Boss collections** — `tools/blender/items/boss_regalia.py` rebuilds all 187 pieces (and routes the 15 signature
   weapons) as fitted, textured regalia; `BossSetVisuals.wear()` now loads the GLBs and re-parents `AT_<bone>` parts
   (pauldrons, hand plates, sabatons, tassets); `MaterialLibrary` maps `it_boss_*` palettes to the legend texture
   sets. The old Godot exporter (`tests/tools/build_boss_set_art.gd`) is disabled unless `--legacy`.
6. **PDF** — `tools/create_boss_sets_pdf.py` → `output/pdf/Beyond-Heroes-Boss-Collections.pdf` (17 pages).
7. **Icon audit** — all 309 non-boss 3D item icons checked on one sheet: consistent studio style; the boss icons were
   the outliers and are re-rendered in the same pipeline (`evidence/boss_icons_sheet.png`).

## Reproduce

```
blender -b --factory-startup --python tools/blender/items/boss_regalia.py -- models icons
python tools/blender/items/icons_post.py  (compose: see handoff note below)
Godot --headless --path game --import
Godot --path game --resolution 1916x1011 res://tests/tools/capture_bh022_game.tscn -- --class=knight --slot=96
Godot --path game res://tests/tools/capture_boss_sets.tscn -- --out=res://../work/lemondev/bh-022/evidence/sets [--theme=<set>]
python tools/create_boss_sets_pdf.py
```
Raw icon renders land in `work/lemondev/bh-022/scratch/icons_raw/`; compose them with `icons_post.game_icon` into
`game/assets/ui/icons/items3d/`. An open Godot editor re-imports files as they change and may hold them briefly;
the exporter retries.

## Evidence

- `evidence/shots/` — in-game: socketed inventory, infused tooltips, infused weapon, both waypoints, world map, the
  shrine at level 25 and 45, a boss set worn in town.
- `evidence/sets/` — all 15 sets, front and back, in the game's renderer.
- `evidence/boss_icons_sheet.png`, `evidence/tests_final.txt`.

## Limits

No blind critic review; no physical Android playtest. The mage model's own hat can poke through hood-type helms (the
hat is part of the class mesh). A full collection adds ~50k triangles to a character.
