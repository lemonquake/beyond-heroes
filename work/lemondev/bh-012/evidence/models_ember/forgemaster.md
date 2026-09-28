# Brakka Durnhelm, the Forgemaster (BOSS) (`forgemaster`)

- Module: `tools/blender/characters/enemy_forgemaster.py` (+ shared helpers `tools/blender/characters/kit_ember.py`)
- GLB: `game/assets/characters/forgemaster.glb` (+ `.glb.import` copied from goblin_skulker, uid removed)
- Triangles: 15074
- Height: 2.37 m to the chimney flames (T-pose; helm crown ~1.95 m), dwarf-king proportions: pelvis 0.78 m, shoulder span ~0.9 m
- Clips: 51: shared enemy base + gs_1, gs_2, gs_heavy, boss_slam, boss_sweep, boss_charge, boss_roar, boss_summon, cast_heavy
- Materials / palette: BH_DarkSteel (blackened forge-plate), BH_Steel (iron-wire beard), BH_Bronze (crown, trims, anvil emblem), BH_Leather, BH_Cloth_Primary (red undercoat), BH_Rust (furnace box, chimneys), BH_Stone (coal heap), BH_Shadow, BH_Emissive (rivets, visor slit, grate coals, chimney throats/flames, beard embers, hammer face/runes)

## What makes it distinct
Short-legged, huge-chested armoured dwarf-king. Silhouette: furnace backpack with a glowing grate and two tall chimneys with flames, colossal forge hammer (0.5 m head, glowing face and side runes; greatsword clips, weapon.R, haft extends 0.62 m below the grip for the left hand), crowned helm with glowing visor slit, braided iron-wire beard with ember beads, rows of glowing rivets on plate, pauldrons and faulds.

## Evidence
`forgemaster_rest_iso.png` (T-pose 4 views, stance 3 views + close-up, gameplay camera 54 deg / 40 deg vFOV at 16 m and 24 m),
`forgemaster_clips.png` (stance, attack clips, death at 5 normalized times). Godot scratch import: `godot_check.txt`.

## Build log
```
[forgemaster] mesh 15074 tris
[forgemaster] clip lengths verified
[forgemaster] -> game/assets/characters/forgemaster.glb
```

## Known limitations
Helm/face read weakly black-on-black at 16-24 m; the chimneys, hammer and rivets carry the silhouette. In gs_heavy/boss_slam follow-through the hammer head dips into the ground (library pose).
