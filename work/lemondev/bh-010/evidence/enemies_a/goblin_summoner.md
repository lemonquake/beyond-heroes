# Goblin Summoner (`goblin_summoner`)

- Module: `tools/blender/characters/enemy_goblin_summoner.py`
- GLB: `game/assets/characters/goblin_summoner.glb`
- Triangles: 9962 (5483 verts); materials: BH_Skin, BH_Flesh, BH_Bone, BH_Fur, BH_Leather, BH_Gold, BH_Emissive, BH_Wood, BH_Horn, BH_Cloth_Primary, BH_Shadow, BH_Hair, BH_Cloth_Secondary
- Height: 1.31 m overall top incl. the feather fan; ~1.15 m to the crown of the head (measured non-weapon top: T-pose 1.311 m, idle f0 1.303 m)
- Clips (47): the 42 shared enemy base clips + `staff_1 cast_quick cast_area cast_weapon boss_summon`
- Palette: grey-green skin, tan hide cloak/loincloth (BH_Fur), wooden mask/staff/drum shell (BH_Wood), red + black feathers (BH_Cloth_Primary, BH_Hair), bone paint/rat skull (BH_Bone), drum heads (BH_Horn), coins (BH_Gold), sickly green BH_Emissive embers/eyes/bottle

## What makes it distinct
Different from the Goblin Skulker: carved wooden tribal mask pushed up on the head with a tall red/black feather fan, bone face paint, ragged hide cloak, hide war-drum on the left hip, belt of trinkets, crooked forked staff with a lashed rat skull and green-glowing smoking pouches.

## Evidence
- `goblin_summoner_rest_iso.png`: T-pose front/back, stance at 4 yaws, head close-ups, gameplay camera (54 deg pitch, 40 deg vFOV) at 16 m and 22 m (1080p render, 360 px crop at 1:1).
- `goblin_summoner_clips.png`: idle stance, every attack clip, hit_heavy, death_back at 5 normalized times (Workbench).
- `metrics/goblin_summoner_metrics.json`: deformation audit over every frame of every exported clip (max stretch ratio for edges > 4 mm, max absolute edge growth, lowest vertex z incl. weapon).
- Worst absolute edge growth over all clips: 0.05 m in `strafe_r` (dominant bone spine).
- Spot checks: idle ratio 1.251 / 0.008 m; hit_heavy ratio 1.5 / 0.017 m; death_back ratio 1.521 / 0.022 m; staff_1 ratio 1.886 / 0.029 m

## Build log
```
[goblin_summoner] mesh 9962 tris, 213 parts, 1.3s
[goblin_summoner] baked 47 actions in 30.1s
06:04:55 | INFO: Finished glTF 2.0 export in 5.992558717727661 s
[goblin_summoner] clip lengths verified (47 clips)
[goblin_summoner] -> A:\Python\beyond-heroes\game\assets\characters\goblin_summoner.glb (3.0 MB)
[build] done in 38.0s
```

## Known limitations
- Front/back loincloth flaps now use a soft L/R blend (fixed a 0.14 m centre-line tear in run); remaining worst edge growth 0.05 m (strafe).
- Staff tip dips into the ground in staff_1 / death poses (library hand pose).
