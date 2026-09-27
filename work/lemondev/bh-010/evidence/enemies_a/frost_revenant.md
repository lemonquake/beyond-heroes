# Frost Revenant (`frost_revenant`)

- Module: `tools/blender/characters/enemy_frost_revenant.py`
- GLB: `game/assets/characters/frost_revenant.glb`
- Triangles: 18388 (9843 verts); materials: BH_Steel, BH_Rust, BH_DarkSteel, BH_Emissive, BH_Stone, BH_Leather, BH_Cloth_Primary, BH_Shadow
- Height: 2.42 m overall top incl. the ice crown; great helm top ~2.2 m (knight plate kit at scale 1.2) (measured non-weapon top: T-pose 2.421 m, idle f0 2.416 m)
- Clips (48): the 42 shared enemy base clips + `gs_1 gs_2 gs_heavy cast_area cast_heavy boss_slam`
- Palette: dark cold plate (BH_Steel/BH_DarkSteel), rust rims (BH_Rust), glassy pale frost crust and icicles (BH_Stone), dark frozen cloak/tabard (BH_Cloth_Primary), pale-cyan BH_Emissive ice shards, visor-slit glow and eyes

## What makes it distinct
Massive armoured undead knight: ice-crystal crown round the great helm, glowing cyan visor slit, huge frost-burst pauldrons, frozen ridge of shards down the back, glowing ice heart in the cracked chest, tattered cloak with icicle hem, huge ice-crusted greatsword rigid on weapon.R.

## Evidence
- `frost_revenant_rest_iso.png`: T-pose front/back, stance at 4 yaws, head close-ups, gameplay camera (54 deg pitch, 40 deg vFOV) at 16 m and 22 m (1080p render, 360 px crop at 1:1).
- `frost_revenant_clips.png`: idle stance, every attack clip, hit_heavy, death_back at 5 normalized times (Workbench).
- `metrics/frost_revenant_metrics.json`: deformation audit over every frame of every exported clip (max stretch ratio for edges > 4 mm, max absolute edge growth, lowest vertex z incl. weapon).
- Worst absolute edge growth over all clips: 0.173 m in `run` (dominant bone hips).
- Spot checks: idle ratio 1.498 / 0.032 m; hit_heavy ratio 2.013 / 0.062 m; death_back ratio 1.907 / 0.053 m; gs_1 ratio 3.338 / 0.132 m

## Build log
```
[frost_revenant] mesh 18388 tris, 256 parts, 2.2s
[frost_revenant] baked 48 actions in 27.8s
06:09:59 | INFO: Finished glTF 2.0 export in 5.14386248588562 s
[frost_revenant] clip lengths verified (48 clips)
[frost_revenant] -> A:\Python\beyond-heroes\game\assets\characters\frost_revenant.glb (3.7 MB)
[build] done in 35.6s
```

## Known limitations
- Tabard front panel stretches between the legs in run (max 0.17 m edge growth, ratio 4.1) after softening its leg weights; the hollow_soldier baseline using the same panel measures 0.18 m / 5.6.
- Visor glow and eyes only read from the front; from the gameplay camera the head reads mainly by the ice crown.
- Greatsword goes below the ground plane in the cast_area / boss_slam crouches and stands blade-up while lying in death_back (shared library weapon pose).
