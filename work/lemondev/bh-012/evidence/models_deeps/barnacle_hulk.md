# Barnacle Hulk (`barnacle_hulk`)

- Module: `tools/blender/characters/enemy_barnacle_hulk.py` (+ shared `tools/blender/characters/kit_deeps.py`)
- GLB: `game/assets/characters/barnacle_hulk.glb` + `.glb.import` (necromancer settings, own path hash, no uid)
- Triangles: 18652 (budget 20k)
- Height: ~2.38 m hump top, 2.46 m incl. coral (SCALE 1.45, PREVIEW_HEIGHT 2.9)
- Clips: 42 base + `gs_1 gs_2 boss_slam boss_charge cast_heavy` (47)
- Palette: drowned grey-green hide, barnacle white, bleached coral, kelp green, rotten sailcloth, rope, rusted anchor/chain, teal BH_Emissive eyes

## What makes it distinct
Hunched giant with a barnacle-and-coral hump, small head sunk low and forward (jutting jaw, tusks, gill slits), ship-chain across the chest/back, sailcloth wrap; a rusted anchor ~1.95 m (weapon space x1.3) held by the rope-wrapped shank near the ring, crown + flukes forward.

## Evidence
`barnacle_hulk_rest_iso.png` (T-pose front/back, stance x4, head close-ups, gameplay camera 54 deg at 16 / 22 m), `barnacle_hulk_clips.png`.
Validation: `logs/godot_check.txt` (scratch Godot 4.7.2 project, 0 import errors, every clip present with the meta length). `block_loop` imports as `block` because the .import mirrors the existing enemies (`use_name_suffixes=true`); the necromancer baseline does exactly the same (`logs/godot_check_baseline_necromancer.txt`). Loop modes are applied at runtime from the meta (character_visual._prepare_animations).

## Build log
```
[barnacle_hulk] mesh 18652 tris, 460 parts, 1.5s
[barnacle_hulk] baked 47 actions in 18.5s
[barnacle_hulk] clip lengths verified (47 clips)
[barnacle_hulk] -> A:\Python\beyond-heroes\game\assets\characters\barnacle_hulk.glb (3.7 MB)
[build] done in 24.2s
```

## Known limitations
cast_heavy is the shared library throw pose with the anchor rigid in hand (the game spawns the thrown projectile). Chain links are skinned to the torso (rigid-ish). The anchor sweeps close to the ground in gs_1 recovery.
