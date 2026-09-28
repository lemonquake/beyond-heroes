# sporeling

- Module: `tools/blender/characters/enemy_sporeling.py (+ shared kit tools/blender/characters/kit_warren.py)`
- GLB: `game/assets/characters/sporeling.glb` (+ `sporeling.glb.import`, copied from the necromancer import without its uid/path lines)
- Triangles: 5674 (budget 20k); 24 bones (shared humanoid skeleton)
- Height: 1.07 m to the cap top (idle 1.06 m); the body and stalk head stand about 0.85 m, under a 0.33 m-radius cap
- Clips: 45: the 42 enemy base clips plus axe_1, axe_2 and cast_quick. There is no weapon; the root-fingered hands do the swipes.
- Palette: rot-purple cap BH_Flesh, pale warts BH_Bone, ochre gills and gill veil BH_Horn, cream stalk flesh BH_Skin, root fingers and toes BH_Wood, moss BH_Fur, face shade BH_Shadow, yellow-green BH_Emissive (eyes, spore blisters, every 5th cap wart)

## What makes it distinct
An oversized speckled purple cap sits over a squat, pear-shaped cream body. At the gameplay camera it reads as a spotted purple toadstool on legs. Two glowing eyes peek out between ochre gill frills under the brim, and glowing spore blisters dot the body.

## Evidence
- `sporeling_rest_iso.png`: the T-pose at 4 yaws, the stance at 3 yaws, a close-up, and gameplay-camera crops (54 deg pitch, 40 deg vFOV, 16 m and 24 m, 1:1 px at 1080p), plus a lineup with a reference enemy.
- `sporeling_clips.png`: every attack clip, plus a reaction or locomotion clip, at 5 normalized times.
- `godot_check.txt`: Godot 4.7.2 import on a scratch project. All listed clips import. `block_loop` imports as `block`, exactly as on every existing enemy (their imports use use_name_suffixes=true).

## Build log
```
[sporeling] mesh 5674 tris, 109 parts, 0.5s
[sporeling] baked 45 actions in 18.1s
[sporeling] clip lengths verified (45 clips)
[sporeling] -> A:\Python\beyond-heroes\game\assets\characters\sporeling.glb (2.6 MB)
[build] done in 22.6s
```

## Known limitations
- Workbench previews only; there is no in-game capture.
- There is no weapon. The attack clips are the shared axe/cast library swings, so the stubby arms sweep in front of the cap, not over it.
- The cap is rigid on the head. In extreme library poses (knockdown, getup) the cap rim can dip into the ground.
