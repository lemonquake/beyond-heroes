# Drowned Deckhand (`drowned_deckhand`)

- Module: `tools/blender/characters/enemy_drowned_deckhand.py` (+ shared `tools/blender/characters/kit_deeps.py`)
- GLB: `game/assets/characters/drowned_deckhand.glb` + `.glb.import` (necromancer settings, own path hash, no uid)
- Triangles: 13748 (budget 20k)
- Height: 1.80 m (T-pose top); weapon: boat-hook ~2.35 m
- Clips: 42 enemy base clips + `spear_1 spear_2 spear_heavy` (45)
- Palette: grey-blue drowned skin, pale/navy striped shirt, sodden grey trousers, hemp rope, rusted hook/knife, kelp green, barnacle white, teal BH_Emissive eyes (14 materials `BH_*__drowned_deckhand`)

## What makes it distinct
Bloated striped sailor, slack gaping jaw, barnacle clusters on L shoulder / R forearm / L shin, kelp over shoulders and hair, long boat-hook (spike + back-curving hook) held on weapon.R, left hand at +0.34 m on the pole (spear two-hand pose).

## Evidence
`drowned_deckhand_rest_iso.png` (T-pose front/back, stance x4, head close-ups, gameplay camera 54 deg at 16 / 22 m), `drowned_deckhand_clips.png`.
Validation: `logs/godot_check.txt` (scratch Godot 4.7.2 project, 0 import errors, every clip present with the meta length). `block_loop` imports as `block` because the .import mirrors the existing enemies (`use_name_suffixes=true`); the necromancer baseline does exactly the same (`logs/godot_check_baseline_necromancer.txt`). Loop modes are applied at runtime from the meta (character_visual._prepare_animations).

## Build log
```
[drowned_deckhand] mesh 13748 tris, 208 parts, 1.4s
[drowned_deckhand] baked 45 actions in 19.0s
[drowned_deckhand] clip lengths verified (45 clips)
[drowned_deckhand] -> A:\Python\beyond-heroes\game\assets\characters\drowned_deckhand.glb (3.1 MB)
[build] done in 23.9s
```

## Known limitations
Eyes are small; at 22 m the teal reads as two dots. Hair cap reads a little like a knit cap. Kelp strands are rigid on chest/head (no secondary motion).
