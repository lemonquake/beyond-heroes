# Stoker Thrall (`stoker_thrall`)

- Module: `tools/blender/characters/enemy_stoker_thrall.py` (bandit kit SB, standard 1.8 m space, SCALE 1.85/1.818)
- GLB: `game/assets/characters/stoker_thrall.glb` + `.glb.import` (broodhost settings, own path hash, no uid)
- Triangles: 14,886 (budget 20k)
- Height: ~1.85 m to the cap; chimney top 2.22 m
- Clips: 42 base + `axe_1 cast_heavy cast_quick cast_weapon` = 46
- Materials (palette `stoker_thrall`): BH_Skin soot-grey, BH_Flesh raw wire roots, BH_Leather apron/cap/gauntlets, BH_Horn straps, BH_Cloth_Primary ochre quilted kilt, BH_Cloth_Secondary trousers, BH_DarkSteel blackened iron, BH_Bronze copper, BH_Stone terracotta pots, BH_Shadow, **BH_Coals** orange fire (real fire only: furnace grate, fire-door, chimney mouth, pot coals, tong coal), BH_Emissive pure white (wire veins, furnace glyphs, goggle lenses)

## What makes it distinct
A stepped Wirewright firebox strapped high on the back (copper bands, white glyph frets on both flanks, open top grate of orange coals visible from above, barred fire-door behind, copper chimney over the right shoulder). Copper feed-wires plug into his spine; white wire veins spread under the skin of back, shoulders, collarbones, neck and arms. Split leather apron with a copper fret hem over an ochre quilted kilt, harness, heat gauntlets, leather cap + neck flap, copper breathing mask, white-glass goggles. Distinct from bh-012 forge_thrall (no hammer/shield; back furnace + chimney silhouette, tongs, fire-pot).

## Weapons / wiring
- weapon.R: iron furnace tongs (~0.8 m) gripping an orange coal - `axe_1` is the tong swing.
- weapon.L: clay fire-pot bound in copper wire, hanging from its bail, coals in its mouth (the game should spawn its own projectile copy for `cast_quick` / `cast_heavy`). Two spare pots hang at the belt.
- `BH_Coals__stoker_thrall` is an unknown base name to MaterialLibrary.CHAR, so it keeps its imported orange emission (clamped <= 4); BH_Emissive is forced white by `zr_white_palette` anyway.

## Evidence
`stoker_thrall_rest_iso.png`, `stoker_thrall_clips.png`. Validation `logs/godot_check.txt` (0 errors, 46 clips at meta length). Worst stretch 0.105 m (trouser/apron at the thigh in `run`).

## Build log
```
[stoker_thrall] mesh 14886 tris, 233 parts, 1.8s
[stoker_thrall] baked 46 actions in 23.3s
[stoker_thrall] clip lengths verified (46 clips)
```

## Known limitations
The pot is rigid on weapon.L (it does not swing on its bail). Smoke is not modelled (game VFX). Apron flaps are skinned like a skirt.
