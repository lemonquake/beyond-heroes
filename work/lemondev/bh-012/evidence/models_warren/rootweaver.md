# rootweaver

- Module: `tools/blender/characters/enemy_rootweaver.py (+ kit_warren.py)`
- GLB: `game/assets/characters/rootweaver.glb` (+ `rootweaver.glb.import`, copied from the necromancer import without its uid/path lines)
- Triangles: 9214 (budget 20k); 24 bones (shared humanoid skeleton)
- Height: about 1.86 m to the crown; the antler branches reach 2.35 m
- Clips: 47: the base clips plus staff_1, cast_quick, cast_area, cast_heavy and cast_weapon
- Palette: dark bark BH_Wood, light braided root strands BH_Leather, pale bark mask BH_Horn, moss and vines BH_Fur + BH_Hair, ochre shelf fungi BH_Cloth_Primary with BH_Bone rims, rot-purple staff caps BH_Flesh, BH_Shadow sockets, yellow-green BH_Emissive (eyes, seed pod, spores)

## What makes it distinct
A gaunt figure of twisted roots: branching antlers, a pale bark mask with glowing sockets, a floor-length skirt of trailing roots and vines, a stack of shelf fungi on the left shoulder, and long twig fingers on an open left hand. The staff is a gnarled root ending in root claws around a glowing seed pod, which is the brightest point at gameplay distance.

## Evidence
- `rootweaver_rest_iso.png`: the T-pose at 4 yaws, the stance at 3 yaws, a close-up, and gameplay-camera crops (54 deg pitch, 40 deg vFOV, 16 m and 24 m, 1:1 px at 1080p), plus a lineup with a reference enemy.
- `rootweaver_clips.png`: every attack clip, plus a reaction or locomotion clip, at 5 normalized times.
- `godot_check.txt`: Godot 4.7.2 import on a scratch project. All listed clips import. `block_loop` imports as `block`, exactly as on every existing enemy (their imports use use_name_suffixes=true).

## Build log
```
[rootweaver] mesh 9214 tris, 176 parts, 0.9s
[rootweaver] baked 47 actions in 18.8s
[rootweaver] clip lengths verified (47 clips)
[rootweaver] -> A:\Python\beyond-heroes\game\assets\characters\rootweaver.glb (3.0 MB)
[build] done in 23.7s
```

## Known limitations
- The root skirt is split into panels weighted from the hips to the thighs and shins. In run and getup the strands stretch and the panels separate, in the same range as the robed casters.
- The staff is rigid on weapon.R and can clip the ground in death and getup.
