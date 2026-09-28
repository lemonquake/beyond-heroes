# mycelid_hulk

- Module: `tools/blender/characters/enemy_mycelid_hulk.py (+ kit_warren.py)`
- GLB: `game/assets/characters/mycelid_hulk.glb` (+ `mycelid_hulk.glb.import`, copied from the necromancer import without its uid/path lines)
- Triangles: 10914 (budget 20k); 24 bones (shared humanoid skeleton)
- Height: 2.46 m to the top of the mantle cap (idle 2.45 m); the mantle radius is 0.82 m
- Clips: 47: the base clips plus axe_1, axe_2, boss_slam, cast_heavy and boss_charge. cast_heavy is the spore breath; the mouth has a BH_Emissive glow for it.
- Palette: rot-ochre cap BH_Flesh with pale BH_Bone warts, moss BH_Fur and small mushrooms, ochre gills BH_Horn, cream stalk flesh BH_Skin, rot-purple shelf fungi BH_Cloth_Primary with BH_Bone rims, root-knot club and root toes BH_Wood, yellow-green BH_Emissive (eyes, mouth glow, spore sacs, every 4th cap wart)

## What makes it distinct
A broad, flat ochre cap spreads over the hunched shoulders like a mantle. At the gameplay camera it reads as a big spotted ochre disc, clearly different from the purple Sporeling. A small face with glowing eyes sits low under the brim. Purple shelf fungi ridge the flanks and arms, glowing spore sacs cover the lower back, the fists are huge (2.5x), and the right fist is wrapped in a spiked knot of roots.

## Evidence
- `mycelid_hulk_rest_iso.png`: the T-pose at 4 yaws, the stance at 3 yaws, a close-up, and gameplay-camera crops (54 deg pitch, 40 deg vFOV, 16 m and 24 m, 1:1 px at 1080p), plus a lineup with a reference enemy.
- `mycelid_hulk_clips.png`: every attack clip, plus a reaction or locomotion clip, at 5 normalized times.
- `godot_check.txt`: Godot 4.7.2 import on a scratch project. All listed clips import. `block_loop` imports as `block`, exactly as on every existing enemy (their imports use use_name_suffixes=true).

## Build log
```
[mycelid_hulk] mesh 10914 tris, 177 parts, 0.9s
[mycelid_hulk] baked 47 actions in 19.3s
[mycelid_hulk] clip lengths verified (47 clips)
[mycelid_hulk] -> A:\Python\beyond-heroes\game\assets\characters\mycelid_hulk.glb (3.0 MB)
[build] done in 24.3s
```

## Known limitations
- The mantle cap is rigid on the chest. The arms pass through the brim in boss_slam and in the overhead part of axe_1.
- The face is small and shaded under the brim; from the high camera, the cap, the spore glows and the club are what make it readable.
- The root knot is rigid on weapon.R; finish_mesh makes weapon.R deform.
