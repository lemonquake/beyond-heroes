# Magma Golem (`magma_golem`)

- Module: `tools/blender/characters/enemy_magma_golem.py` (+ shared helpers `tools/blender/characters/kit_ember.py`)
- GLB: `game/assets/characters/magma_golem.glb` (+ `.glb.import` copied from goblin_skulker, uid removed)
- Triangles: 10798
- Height: 2.66 m (T-pose, shard tips), idle 2.65 m
- Clips: 47: shared enemy base + gs_1, gs_2, boss_slam, cast_heavy (lob), boss_charge
- Materials / palette: BH_Stone (basalt slabs), BH_DarkSteel (soot joint stones), BH_Horn (glossy obsidian shards), BH_Rust (core grate bars), BH_Shadow (seam grooves), BH_Emissive (molten core column / limb cores, seams, eyes), BH_WeakPoint (furnace core in the chest)

## What makes it distinct
Stacked basalt slabs around a glowing molten core column and glowing limb cores, so every gap between slabs glows; big boulder fists, obsidian shard ridge on the back and shard clusters on the shoulders, tiny fused-rock head with ember eyes, barred furnace core (BH_WeakPoint) in the chest. Reuses enemy_rune_golem slab helpers (imported, not edited).

## Evidence
`magma_golem_rest_iso.png` (T-pose 4 views, stance 3 views + close-up, gameplay camera 54 deg / 40 deg vFOV at 16 m and 24 m),
`magma_golem_clips.png` (stance, attack clips, death at 5 normalized times). Godot scratch import: `godot_check.txt`.

## Build log
```
[magma_golem] mesh 10798 tris
[magma_golem] clip lengths verified
[magma_golem] -> game/assets/characters/magma_golem.glb
```

## Known limitations
No weapon: the gs_* clips swing the boulder fists. Slab sleeves can open wider gaps on extreme elbow bends (reads as more glow, by design).
