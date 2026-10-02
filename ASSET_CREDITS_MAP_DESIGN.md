# Downloaded map design source credits

Downloaded and curated 3 October 2026; integrated in the map-design pass the same day. All five packs are by
[Kenney](https://kenney.nl) and licensed [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/); creator credit is
kept here although CC0 does not require it. Original licenses: `assets_src/map_design_20261003/licenses/`.

| Pack | Source | License | Models curated | Placed in the game |
| --- | --- | --- | ---: | ---: |
| nature-kit | https://kenney.nl/assets/nature-kit | CC0-1.0 | 48 | 45 |
| furniture-kit | https://kenney.nl/assets/furniture-kit | CC0-1.0 | 26 | 23 |
| pirate-kit | https://kenney.nl/assets/pirate-kit | CC0-1.0 | 20 | 16 |
| graveyard-kit | https://kenney.nl/assets/graveyard-kit | CC0-1.0 | 16 | 16 |
| modular-dungeon-kit | https://kenney.nl/assets/modular-dungeon-kit | CC0-1.0 | 4 | 3 |

## What was done to them

`tools/blender/environment/prepare_kenney.py` (Blender 5.2) reads each accepted canonical package (unchanged) and writes
`game/assets/environment/kd_<name>.glb`: every part joined into one mesh with its node transform applied, scaled to game
metres, seated on its origin, front +Z; animations, armatures and skins dropped; each part's material renamed to the game's
shared material set (flat-colour parts by source material name, palette-textured parts per face by the palette colour
under the face), so the game's own lit, textured materials replace the source colours. Simple box collision is added to
furniture, large rocks and tree trunks. Per-model receipts with source and derived SHA-256: `work/map-design/prepared/`.
Canonical packages were verified and admitted with the game-dev tool into `game/assets/vendor/` (ignored by Godot, not
exported); lock file: `game/.game-dev/vendor-lock.json`.

## Not used

| Source model | Decision | Reason |
| --- | --- | --- |
| kenney_nature_plant_bushsmall | rejected after in-game review | its 8 triangles read as a flat dark star from the gameplay camera; the kit's own bushes take its places |
| kenney_nature_stone_largea | rejected | recolour of rock_largeA (same geometry); not a distinct source model |
| kenney_nature_stone_smallflata | rejected | recolour of rock_smallFlatA (same geometry) |
| kenney_furniture_beddouble | deferred | the existing bed_double already fits every room that needs one |
| kenney_furniture_pillow | deferred | the prepared beds include pillows; a loose modern pillow adds nothing |
| kenney_furniture_ruground | deferred | the existing rug_round fills this role |
| kenney_pirate_boat_row_large | deferred | kd_rowboat and the existing boat_rowing cover every mooring |
| kenney_pirate_structure_fence | deferred | repeated railing spans are what the brief warns against on long bridges |
| kenney_pirate_flag_pennant | rejected | flags and pennants were rejected by the user (medieval, in-theme art only) |
| kenney_pirate_mast_ropes | deferred | no harbour scene needs a free-standing rigged mast; the wreck carries one |
| kenney_modular-dungeon_template_wall_half | deferred | the existing 4 m wall kit and low cutaway walls already do this |

The full per-model inventory with where each piece is used: `output/map-design-20261003/assets/accepted_assets.md`.
