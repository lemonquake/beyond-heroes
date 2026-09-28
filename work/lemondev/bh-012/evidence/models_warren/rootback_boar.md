# rootback_boar

- Script: `tools/blender/creatures/build_rootback_boar.py`. The rig, planar leg IK, gait and bake machinery are copied from `build_wolf.py`, which is unchanged. The skeleton, mesh, clips, palette and meta merge are new.
- GLB: `game/assets/characters/rootback_boar.glb` (+ `.import` copied from the dire_wolf import)
- Triangles: 11164; 31 bones with wolf-style names: root, hips, spine, chest, neck, head, jaw, tail.1-4, ear.L/R, scap/upperarm/forearm/fpaw/ftoe.L/R, thigh/shin/hpaw/htoe.L/R
- Size: 1.14 m of hide at the withers (1.44 m to the tips of the back spines), 2.01 m from snout to tail tuft (1.9 m snout to rump), 0.67 m wide
- Clips (15, in place, 30 fps): idle (loops), idle_look, walk (loops, 1.1 m/s), run (loops, heavy trot at 4.4 m/s), run_combat (loops, 4.4 m/s), hit_light, hit_heavy, stagger_small, knockback, death, death_back and alert, plus:
  - `boar_gore` 1.0 s, hits [0.367, 0.533]: the head dips, then hooks the tusks upward to its right.
  - `boar_charge` 1.0 s one-shot, hits [0.1, 0.9], ground_speed 6.0: a head-down gallop over 2 gait cycles. The first and last frames are identical, so it can be replayed back to back while the boar runs.
  - `boar_stomp` 1.2 s, hits [0.633, 0.733]: rears onto the hind legs (front hooves about 0.5 m up), then slams both forelegs down.
- creature_meta.json: merged `animations.boar_gore/boar_charge/boar_stomp` and `models.rootback_boar` (every clip, tris, bones). The file was re-read right before writing, and a check after the write confirmed every other key is unchanged.
- Palette: bristly dark hide BH_Fur, black bristle crest, tail tuft and brows BH_Hair, bark plates BH_Wood, thorny root spines and bark grain BH_Horn, pale-wood tusks BH_Bone, moss BH_Cloth_Secondary, snout disc and inner ears BH_Flesh, hooves and nostrils BH_Shadow, pale fungus stalks BH_Skin, amber eyes BH_Aether (a second, amber emissive palette material), yellow-green glowing fungi BH_Emissive

## What makes it distinct
A heavy, deep-bellied boar. Its back is shingled with bark plates, bristles with raked thorny root spines (tallest over the withers), and is dotted with moss and clusters of small glowing mushrooms. It has two big curving pale tusks, small amber eyes and cloven hooves. At the gameplay camera it reads as a dark, spiky, moss-green back with glowing dots and a pale tusked head.

## Evidence
- `rootback_boar_rest_iso.png`: 4 rest views, a head close-up, the plated back, and gameplay-camera crops at 16 m and 24 m.
- `rootback_boar_clips.png`: boar_gore, boar_charge, boar_stomp, run, walk and death at 5 normalized times.
- `tools/boar_evidence.py` renders them. `godot_check.txt` shows all 15 clips importing; every clip imports with loop=0, and loops come from the meta, as with dire_wolf.

## Build log
```
[rootback_boar] mesh 11164 tris, 15 clips
[rootback_boar] meta merged ['boar_charge', 'boar_gore', 'boar_stomp'] + models.rootback_boar -> A:\Python\beyond-heroes\game\assets\characters\creature_meta.json (verified: True)
[rootback_boar] -> A:\Python\beyond-heroes\game\assets\characters\rootback_boar.glb (1.7 MB)
[rootback_boar] 15 animations in the GLB; length mismatches: []
```

## Known limitations
- Death reuses the wolf's roll-onto-side sequence, rescaled. The back spines sweep through the ground plane while it lies on its side.
- The bark plates and spines are skinned to hips/spine/chest/neck by distance, so they bend with the spine instead of staying rigid.
- The generic clip keys (walk, run, ...) in the top-level creature_meta `animations` still belong to dire_wolf. The boar's own ground speeds are in `models.rootback_boar.clips`.
