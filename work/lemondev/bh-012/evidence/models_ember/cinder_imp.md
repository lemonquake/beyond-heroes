# Cinder Imp (`cinder_imp`)

- Module: `tools/blender/characters/enemy_cinder_imp.py` (+ shared helpers `tools/blender/characters/kit_ember.py`)
- GLB: `game/assets/characters/cinder_imp.glb` (+ `.glb.import` copied from goblin_skulker, uid removed)
- Triangles: 8708
- Height: 1.09 m (horn tips; T-pose), idle 1.08 m
- Clips: 46: shared enemy base + wand_1, cast_quick, cast_weapon, dagger_1
- Materials / palette: BH_Skin (charcoal), BH_Flesh (wing membrane, ember red), BH_Horn (horns/claws/spars), BH_Shadow, BH_Leather, BH_DarkSteel (fork-brand), BH_Bone (teeth), BH_Emissive (1.0,0.45,0.1 x10: lava seams, eyes, grin, fork tip, tail flame)

## What makes it distinct
Wiry charcoal imp with glowing crack network over torso and limbs, curled horns, long pointed ears, glowing grin; half-spread bat wings (rigid on chest) and a long tail curling up into a flame tip (rigid on hips) make the silhouette; iron fork-brand with a white-hot tip and ember in the right hand.

## Evidence
`cinder_imp_rest_iso.png` (T-pose 4 views, stance 3 views + close-up, gameplay camera 54 deg / 40 deg vFOV at 16 m and 24 m),
`cinder_imp_clips.png` (stance, attack clips, death at 5 normalized times). Godot scratch import: `godot_check.txt`.

## Build log
```
[cinder_imp] mesh 8708 tris
[cinder_imp] clip lengths verified
[cinder_imp] -> game/assets/characters/cinder_imp.glb
```

## Known limitations
Tail and wings are rigid (hips / chest): the tail pierces the ground in lying death poses; wings clip the upper arms in some extreme cast poses. Seams are thin at 24 m - the eyes, fork tip and tail flame carry the read.
