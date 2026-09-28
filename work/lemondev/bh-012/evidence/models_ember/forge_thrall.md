# Forge Thrall (`forge_thrall`)

- Module: `tools/blender/characters/enemy_forge_thrall.py` (+ shared helpers `tools/blender/characters/kit_ember.py`)
- GLB: `game/assets/characters/forge_thrall.glb` (+ `.glb.import` copied from goblin_skulker, uid removed)
- Triangles: 9694
- Height: 1.91 m (T-pose), idle_shield 1.92 m
- Clips: 46: shared enemy base + shield_bash, axe_1, axe_heavy, sword_1
- Materials / palette: BH_Skin (soot-dark skin), BH_Flesh (burn weals), BH_Leather (apron, lighter brown), BH_Horn (straps, bracers, boots), BH_Cloth_Secondary (trousers), BH_DarkSteel (mask, collar, furnace door, hammer), BH_Rust (chains, shackles), BH_Wood, BH_Hair, BH_Shadow, BH_Emissive (burn-scar cores, eyes, grille fire, hammer hot face, apron ember)

## What makes it distinct
Stocky bare-armed smith-slave: heavy leather apron over soot skin, riveted iron half-mask, iron collar with broken chains front and back, shackle cuffs with chain stubs, tongs on the hip. Forge hammer (weapon.R) with a glowing striking face; furnace-door tower shield (weapon.L, face -Y) with a glowing barred grille - the grille is the read at gameplay distance.

## Evidence
`forge_thrall_rest_iso.png` (T-pose 4 views, stance 3 views + close-up, gameplay camera 54 deg / 40 deg vFOV at 16 m and 24 m),
`forge_thrall_clips.png` (stance, attack clips, death at 5 normalized times). Godot scratch import: `godot_check.txt`.

## Build log
```
[forge_thrall] mesh 9694 tris
[forge_thrall] clip lengths verified
[forge_thrall] -> game/assets/characters/forge_thrall.glb
```

## Known limitations
Head is small under the mask at 24 m; burn scars are subtle by design. Shield goes through the ground briefly in death poses (library hand pose).
