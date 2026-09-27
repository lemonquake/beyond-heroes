# Orc Shaman (`orc_shaman`)

- Module: `tools/blender/characters/enemy_orc_shaman.py`
- GLB: `game/assets/characters/orc_shaman.glb`
- Triangles: 13962 (7675 verts); materials: BH_Skin, BH_Cloth_Secondary, BH_Leather, BH_Bone, BH_Wood, BH_Cloth_Primary, BH_Emissive, BH_Fur, BH_Shadow, BH_Hair, BH_Horn
- Height: 2.14 m overall top incl. antlers; ~1.9 m to the crown (measured non-weapon top: T-pose 2.136 m, idle f0 2.121 m)
- Clips (49): the 42 shared enemy base clips + `staff_1 staff_2 cast_quick cast_area cast_heavy cast_weapon war_cry`
- Palette: old grey-green skin, grey wolf pelt (BH_Fur), hide kilt/cap (BH_Leather), antlers (BH_Horn), bone fetishes/beads/tusks (BH_Bone), grey hair+beard (BH_Hair), dark red wraps (BH_Cloth_Primary), blue-white war paint (BH_Cloth_Secondary), blue-white BH_Emissive lightning crystal + eyes

## What makes it distinct
Distinct from the Orc Reaver: no armour, antler headdress with bone fetishes and feathers, wolf-pelt mantle with the wolf head on the left shoulder, braided grey beard, long hide kilt with fur hem, gnarled totem staff gripping a glowing crystal.

## Evidence
- `orc_shaman_rest_iso.png`: T-pose front/back, stance at 4 yaws, head close-ups, gameplay camera (54 deg pitch, 40 deg vFOV) at 16 m and 22 m (1080p render, 360 px crop at 1:1).
- `orc_shaman_clips.png`: idle stance, every attack clip, hit_heavy, death_back at 5 normalized times (Workbench).
- `metrics/orc_shaman_metrics.json`: deformation audit over every frame of every exported clip (max stretch ratio for edges > 4 mm, max absolute edge growth, lowest vertex z incl. weapon).
- Worst absolute edge growth over all clips: 0.102 m in `strafe_l` (dominant bone chest).
- Spot checks: idle ratio 1.249 / 0.018 m; hit_heavy ratio 1.501 / 0.047 m; death_back ratio 1.779 / 0.051 m; staff_1 ratio 1.857 / 0.052 m

## Build log
```
[orc_shaman] mesh 13962 tris, 316 parts, 1.8s
[orc_shaman] baked 49 actions in 31.0s
06:04:56 | INFO: Finished glTF 2.0 export in 6.2136149406433105 s
[orc_shaman] clip lengths verified (49 clips)
[orc_shaman] -> A:\Python\beyond-heroes\game\assets\characters\orc_shaman.glb (3.4 MB)
[build] done in 39.7s
```

## Known limitations
- Kilt front/back panels and seat re-weighted (soft L/R blend) to fix a 0.56 m centre-line tear in run; remaining worst edge growth 0.10 m (strafe_l, chest beads/pelt).
- Uses the shared skeleton and idles; the 'hunched' read comes from the mesh (forward head, pelt mound) rather than a custom pose.
