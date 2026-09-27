# Plague Bloater (`plague_bloater`)

- Module: `tools/blender/characters/enemy_plague_bloater.py`
- GLB: `game/assets/characters/plague_bloater.glb`
- Triangles: 17458 (9223 verts); materials: BH_Skin, BH_Shadow, BH_Emissive, BH_Flesh, BH_Bone, BH_Leather, BH_Fur, BH_Cloth_Primary, BH_Wood, BH_Rust
- Height: 2.00 m overall top (T-pose); 1.99 m in idle (measured non-weapon top: T-pose 2.000 m, idle f0 1.990 m)
- Clips (47): the 42 shared enemy base clips + `axe_1 boss_slam cast_heavy boss_roar cast_area`
- Palette: taut sickly yellow-green skin (BH_Skin), raw pustules and sac rims (BH_Flesh), dark veins (BH_Fur), teeth/nails (BH_Bone), filthy rags (BH_Cloth_Primary), rope/stitches/bandages (BH_Leather), rusty cleaver-axe (BH_Rust, BH_Wood), sickly green BH_Emissive plague sacs/eyes/slime

## What makes it distinct
Grotesque ball-shaped gut wider than the shoulders and hanging to mid-thigh, crossed by stitched seams, large glowing green plague sacs (belly, back, shoulders, right forearm, scalp) with vein webs, ~45 pustules; small bald head sunk into the shoulders with a wide black gaping maw and crooked teeth; heavy arms, stubby thick legs in torn rag trousers, rope belt under the overhang, rag loincloth, rusty butcher's cleaver-axe in the right hand.

## Evidence
- `plague_bloater_rest_iso.png`: T-pose front/back, stance at 4 yaws, head close-ups, gameplay camera (54 deg pitch, 40 deg vFOV) at 16 m and 22 m (1080p render, 360 px crop at 1:1).
- `plague_bloater_clips.png`: idle stance, every attack clip, hit_heavy, death_back at 5 normalized times (Workbench).
- `metrics/plague_bloater_metrics.json`: deformation audit over every frame of every exported clip (max stretch ratio for edges > 4 mm, max absolute edge growth, lowest vertex z incl. weapon).
- Worst absolute edge growth over all clips: 0.158 m in `boss_slam` (dominant bone hips).
- Spot checks: idle ratio 3.774 / 0.056 m; hit_heavy ratio 3.774 / 0.091 m; death_back ratio 3.774 / 0.101 m; axe_1 ratio 4.582 / 0.113 m

## Build log
```
[plague_bloater] mesh 17458 tris, 245 parts, 2.1s
[plague_bloater] baked 47 actions in 30.9s
06:04:57 | INFO: Finished glTF 2.0 export in 6.047193765640259 s
[plague_bloater] clip lengths verified (47 clips)
[plague_bloater] -> A:\Python\beyond-heroes\game\assets\characters\plague_bloater.glb (3.4 MB)
[build] done in 39.7s
```

## Known limitations
- Arms can intersect the sides of the gut in clips that bring the arms across the body (library poses were authored for normal bodies).
- Trouser tops at the seat stretch up to 0.16 m in boss_slam/cast_area (thigh raise); the shoulder sac cluster has short edges with ratio up to 4.4 in boss_slam (visually clean in the sheet).
- Skeleton keeps standard leg lengths (scale 1.18); the stubby-leg read comes from the low-hanging gut and baggy trousers.
