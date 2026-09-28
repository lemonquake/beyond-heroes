# Brinecaller (`brinecaller`)

- Module: `tools/blender/characters/enemy_brinecaller.py` (+ shared `tools/blender/characters/kit_deeps.py`)
- GLB: `game/assets/characters/brinecaller.glb` + `.glb.import` (necromancer settings, own path hash, no uid)
- Triangles: 15094 (budget 20k)
- Height: ~1.86 m to the head, 2.04 m to the coral crown tips
- Clips: 42 base + `staff_1 cast_quick cast_heavy cast_area cast_weapon` (47)
- Palette: sea-green robe / deep-green mantle, kelp ribbons, pale blue-grey skin, wet black hair, bleached coral, shell white, pearl, bleached driftwood, teal BH_Emissive (eyes, polyps, pearl)

## What makes it distinct
Gaunt robed priestess; the branching coral crown with teal polyp tips is the silhouette key; conch-topped driftwood staff with a glowing teal pearl in front of the aperture; shell/pearl necklaces, shell girdle; left hand open with long fingers.

## Evidence
`brinecaller_rest_iso.png` (T-pose front/back, stance x4, head close-ups, gameplay camera 54 deg at 16 / 22 m), `brinecaller_clips.png`.
Validation: `logs/godot_check.txt` (scratch Godot 4.7.2 project, 0 import errors, every clip present with the meta length). `block_loop` imports as `block` because the .import mirrors the existing enemies (`use_name_suffixes=true`); the necromancer baseline does exactly the same (`logs/godot_check_baseline_necromancer.txt`). Loop modes are applied at runtime from the meta (character_visual._prepare_animations).

## Build log
```
[brinecaller] mesh 15094 tris, 242 parts, 1.2s
[brinecaller] baked 47 actions in 17.9s
[brinecaller] clip lengths verified (47 clips)
[brinecaller] -> A:\Python\beyond-heroes\game\assets\characters\brinecaller.glb (3.4 MB)
[build] done in 23.2s
```

## Known limitations
Robe hem ribbons are skinned to the robe panels (hips/thighs) like the necromancer's robe; expect the same robe stretch range in run/getup. Staff dips under the ground in death/getup (shared library pose).
