# Necromancer (`necromancer`)

- Module: `tools/blender/characters/enemy_necromancer.py`
- GLB: `game/assets/characters/necromancer.glb`
- Triangles: 16092 (8584 verts); materials: BH_Cloth_Primary, BH_Cloth_Secondary, BH_Leather, BH_Bone, BH_Shadow, BH_Emissive, BH_Skin, BH_DarkSteel, BH_Horn
- Height: 2.05 m overall top (T-pose, excluding the staff); designed ~1.95 m to the crown, the rib-bone collar rises above it (measured non-weapon top: T-pose 2.048 m, idle f0 2.036 m)
- Clips (48): the 42 shared enemy base clips + `staff_1 cast_quick cast_area cast_heavy cast_weapon boss_summon`
- Palette: black grave-robe (BH_Cloth_Primary), violet over-robe/stole (BH_Cloth_Secondary), corpse-pale skull face (BH_Skin), old bone collar/ribcage/staff/charms (BH_Bone, BH_Horn), dark iron lantern cage (BH_DarkSteel), violet BH_Emissive eyes and caged-skull light

## What makes it distinct
Tall, gaunt, slightly hunched robed caster. Silhouette keys: fan of curved rib bones rising behind the head, ribcage breastplate over the robe, long bone staff with a violet-glowing caged skull lantern. Skull face with violet eyes under a finger-bone circlet; open clawed left hand; rope belt with bone charms and small skulls.

## Evidence
- `necromancer_rest_iso.png`: T-pose front/back, stance at 4 yaws, head close-ups, gameplay camera (54 deg pitch, 40 deg vFOV) at 16 m and 22 m (1080p render, 360 px crop at 1:1).
- `necromancer_clips.png`: idle stance, every attack clip, hit_heavy, death_back at 5 normalized times (Workbench).
- `metrics/necromancer_metrics.json`: deformation audit over every frame of every exported clip (max stretch ratio for edges > 4 mm, max absolute edge growth, lowest vertex z incl. weapon).
- Worst absolute edge growth over all clips: 0.099 m in `run` (dominant bone hips).
- Spot checks: idle ratio 1.405 / 0.052 m; hit_heavy ratio 1.405 / 0.052 m; death_back ratio 1.407 / 0.052 m; staff_1 ratio 1.681 / 0.058 m

## Build log
```
[necromancer] mesh 16092 tris, 248 parts, 2.4s
[necromancer] baked 48 actions in 32.4s
05:53:59 | INFO: Finished glTF 2.0 export in 5.702691078186035 s
[necromancer] clip lengths verified (48 clips)
[necromancer] -> A:\Python\beyond-heroes\game\assets\characters\necromancer.glb (3.4 MB)
[build] done in 41.1s
```

## Known limitations
- Robe hem stretch in run/getup up to ratio 2.1 / 0.10 m (hips-weighted robe), same range as the ashen_cultist baseline (ratio 2.05).
- Staff (rigid on weapon.R) passes below the ground plane while lying in death/getup and in the cast_area crouch (library hand pose; the ashen_cultist baseline does the same).
