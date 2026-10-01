# Kalvex, the Engine Heart (`engine_heart`) - BOSS

- Module: `tools/blender/characters/enemy_engine_heart.py` (imports the obsidian kit from `enemy_obsidian_golem.py`)
- GLB: `game/assets/characters/engine_heart.glb` + `.glb.import` (broodhost settings, own path hash, no uid)
- Triangles: 13,516 (budget 35k)
- Height: head/crown ~4.2 m; smokestack caps 4.85 m (idle). Width in idle ~3.9 m (hammers + pauldrons). PREVIEW_HEIGHT 4.9
- Clips: 42 base + required `boss_charge boss_slam boss_summon cast_area cast_heavy cast_ultimate gs_1` + extras `boss_roar boss_sweep gs_2` = 52
- Materials (palette `engine_heart`): BH_Stone black glass, BH_Horn shard spikes, BH_DarkSteel core / joint balls, BH_Bronze copper frame / housings / stacks, BH_Gold copper rims & seam lips, BH_Steel polished piston rods, BH_Rust blackened iron grille bars & rivets, BH_Shadow, BH_Coals (small orange ash-mouth fire), BH_Emissive white (seams, face-grille light, stack throats), **BH_WeakPoint** white (the molten core behind the chest grille)

## What makes it distinct
The chest is a furnace: a big copper-rimmed round firebox with heavy iron grille bars and the white molten core behind them (the weak point), riveted copper corner plates, an ash-mouth of orange coals beneath. Two tall stepped smokestacks behind the shoulders with a ring of glass spikes between (the gameplay-camera silhouette). Piston arms: copper cylinder housings on the upper arms, copper sleeves + polished rods + slave pistons on the forearms, each ending in a huge copper-banded hammer head with a knapped obsidian striking face and a white glyph. Grille face (copper bars over white light) in a small glass head under a stepped crown. Crank-drum waist, glass tassets, shin pistons, slab feet.

## Wiring notes
- No weapon sockets: both hammers are the hands (gs_1 / boss_slam strike with them). BH_WeakPoint = the chest core, centred on the sternum at ~3.2 m (chest bone).
- Authored at true size (game scale 1.0 gives a ~4.2 m boss).

## Evidence
`engine_heart_rest_iso.png`, `engine_heart_clips.png` (all 7 required clips). Validation `logs/godot_check.txt` (0 errors, 52 clips at meta length). Worst stretch 0.117 m (core column, death_crumple).

## Build log
```
[engine_heart] mesh 13516 tris, 308 parts, 1.4s
[engine_heart] baked 52 actions in 27.7s
[engine_heart] clip lengths verified (52 clips)
```

## Known limitations
Pistons are rigid on their bones (no telescoping). The orange ash-mouth is small and mostly shadowed by the furnace rim in the Workbench previews. The 16 m gameplay crop is filled by the model (true-size 4.2 m boss).
