# Ysvharn, the Giant's Heart (`vein_mother`) - BOSS

- Module: `tools/blender/characters/enemy_vein_mother.py` (reuses `horn` / `plate` / `rock` / `vcrack` from `enemy_gigas_spawn.py`)
- GLB: `game/assets/characters/vein_mother.glb` + `.glb.import` (broodhost settings, own path hash, no uid)
- Triangles: 20,676 (budget 35k)
- Height: crown spur tips 4.45 m in idle (4.49 T-pose); the head is thrust low and forward (stooped). PREVIEW_HEIGHT 5.0
- Clips: 42 base + required `boss_roar boss_slam boss_summon boss_sweep cast_area cast_heavy cast_ultimate cast_weapon` + extras `boss_charge gs_1` = 52
- Materials (palette `vein_mother`): BH_Stone grey-violet giant-stone, BH_DarkSteel joint stone, BH_Bone pale bone (ribs, face plate, plates, fingers), BH_Horn old dark bone (spurs, talons), BH_Flesh dark raw sinew (torso, neck, vein cables), BH_Cloth_Secondary membrane skirt, BH_Shadow, BH_Emissive white (vein lines/nodes, four eyes, throat, cracks), **BH_WeakPoint** white (the heart)

## What makes it distinct
An opened ribcage: five pale ribs a side split down the front, sternum halves hanging open, and in the pit of dark sinew the big white heart (the weak point) at the solar plexus, visible from the front and from the gameplay camera. Vein cables (dark sinew tubes with a white line and white nodes) leave the heart over both shoulders and into the neck, wind round the forearms, cross the belly to the hips, and loop down the back. Crown of eleven long bone spurs splayed up and out round the back of the skull (silhouette key). Very long arms (knuckles at the knees) ending in five-fingered jointed bone claws. Vertebra spurs up the hump, bone plates on shoulders/back/knees, ragged membrane skirt, clawed stone feet. Distinct from M4's gigas_spawn (no hump plates / closed stone torso; open cage + heart + cables + crown).

## Wiring notes
- No weapon: claws strike (gs_1 / boss_slam / boss_sweep). BH_WeakPoint = the heart on the chest bone at ~2.75 m.

## Evidence
`vein_mother_rest_iso.png`, `vein_mother_clips.png` (all 8 required clips). Validation `logs/godot_check.txt` (0 errors, 52 clips at meta length). Worst stretch 0.171 m (front cable at the neck in death_crumple); fixed earlier peaks by subdividing cables and giving the centre membrane rags shared thigh weights.

## Build log
```
[vein_mother] mesh 20676 tris, 260 parts, 1.7s
[vein_mother] baked 52 actions in 22.5s
[vein_mother] clip lengths verified (52 clips)
```

## Known limitations
The "pulse" of the heart / veins is not animated in the GLB (emissive is static; the game can pulse BH_WeakPoint energy). Long fingers are rigid to the hand bone (no finger bones in the shared skeleton). Stoop is in the authored head/torso shape; the shared clips stand it fairly upright.
