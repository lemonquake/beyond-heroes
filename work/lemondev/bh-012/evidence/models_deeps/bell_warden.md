# Ossric Vael, the Drowned Bell (boss) (`bell_warden`)

- Module: `tools/blender/characters/enemy_bell_warden.py` (+ shared `tools/blender/characters/kit_deeps.py`)
- GLB: `game/assets/characters/bell_warden.glb` + `.glb.import` (necromancer settings, own path hash, no uid)
- Triangles: 21752 (budget 35k boss)
- Height: 2.30 m to the bell crown, 2.35 m incl. the hanging loop (K = 2.3/1.98; the game scales ~1.9x)
- Clips: 42 base + `spear_1 spear_2 spear_heavy boss_sweep boss_slam boss_charge boss_roar boss_summon cast_heavy` (51)
- Palette: green-bronze plate (BH_Steel), old bronze bell (BH_Bronze), dark verdigris trim (BH_Gold), deep sea-green cloak, barnacle white, kelp, rusted chains, teal BH_Emissive (bell slit + inner mouth band)

## What makes it distinct
Knight-commander (knight plate kit) whose head is a sunken bronze bell: cross-shaped teal slit, teal band inside the mouth, hanging loop on top, weed and chain stubs from the rim; barnacled pauldrons trailing kelp; tattered sea-cloak on cape bones (boss_warden cape logic); anchor-axe halberd (crescent blade +X, anchor arm + fluke -X, spike on top).

## Evidence
`bell_warden_rest_iso.png` (T-pose front/back, stance x4, head close-ups, gameplay camera 54 deg at 16 / 22 m), `bell_warden_clips.png`.
Validation: `logs/godot_check.txt` (scratch Godot 4.7.2 project, 0 import errors, every clip present with the meta length). `block_loop` imports as `block` because the .import mirrors the existing enemies (`use_name_suffixes=true`); the necromancer baseline does exactly the same (`logs/godot_check_baseline_necromancer.txt`). Loop modes are applied at runtime from the meta (character_visual._prepare_animations).

## Build log
```
[bell_warden] mesh 21752 tris, 309 parts, 1.8s
[bell_warden] baked 51 actions in 21.3s
[bell_warden] clip lengths verified (51 clips)
[bell_warden] -> A:\Python\beyond-heroes\game\assets\characters\bell_warden.glb (4.1 MB)
[build] done in 28.3s
```

## Known limitations
Bell is rigid on `head`; being a solid of revolution it hides head yaw, but strong head pitch/roll can push its rim into the pauldrons. No BH_WeakPoint (not requested).
