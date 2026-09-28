# rot_mother

- Module: `tools/blender/characters/enemy_rot_mother.py (+ kit_warren.py)`
- GLB: `game/assets/characters/rot_mother.glb` (+ `rot_mother.glb.import`, copied from the necromancer import without its uid/path lines)
- Triangles: 17184 (budget 35k boss); 24 bones (shared humanoid skeleton)
- Height: about 2.17 m to the crown; the fungal halo reaches 2.90 m (the game scales her about 2x)
- Clips: 50: the base clips plus staff_1, staff_heavy, cast_area, cast_heavy, cast_ultimate, boss_roar, boss_summon and boss_slam
- Palette: moss over-robe, sleeves and cowl BH_Fur, rot-purple under-robe and sash BH_Cloth_Secondary, pale fungal mask BH_Horn, mycelium threads, cap warts and shelf rims BH_Bone, rot-purple halo caps BH_Flesh, ochre gills BH_Leather, ochre shelf fungi BH_Cloth_Primary, roots BH_Wood, yellow-green BH_Emissive (7 eyes, chest spore sacs, staff pod, halo spore warts)

## What makes it distinct
A fan of 9 rot-purple mushroom caps on pale stalks rises behind the head like a halo, with 8 ochre shelf fungi between them. It dominates the silhouette from the front, from above and from behind. Below it are a pale mask with seven small glowing eyes, glowing purple-ringed spore sacs on the chest, and layered moss robes hung with pale mycelium threads. She has long root fingers and carries a living-root staff with a large glowing pod.

## Evidence
- `rot_mother_rest_iso.png`: the T-pose at 4 yaws, the stance at 3 yaws, a close-up, and gameplay-camera crops (54 deg pitch, 40 deg vFOV, 16 m and 24 m, 1:1 px at 1080p).
- `rot_mother_clips.png`: every attack clip, plus a reaction or locomotion clip, at 5 normalized times.
- `godot_check.txt`: Godot 4.7.2 import on a scratch project. All listed clips import. `block_loop` imports as `block`, exactly as on every existing enemy (their imports use use_name_suffixes=true).

## Build log
```
[rot_mother] mesh 17184 tris, 302 parts, 1.7s
[rot_mother] baked 50 actions in 22.0s
[rot_mother] clip lengths verified (50 clips)
[rot_mother] -> A:\Python\beyond-heroes\game\assets\characters\rot_mother.glb (3.6 MB)
[build] done in 28.6s
```

## Known limitations
- The halo is rigid on the chest. It tips with the torso in the cast_area, cast_ultimate and boss_slam crouches (intended) and can clip the raised staff arm.
- The mycelium threads are rigid per bone and do not swing.
- The robe panels separate at the side seams in wide strides.
