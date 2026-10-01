# Obsidian Golem (`obsidian_golem`)

- Module: `tools/blender/characters/enemy_obsidian_golem.py` (also holds the small M6 "obsidian kit": `Facet`, `flimb`, `fprism`, `seam`, `jag`, `ridge`)
- GLB: `game/assets/characters/obsidian_golem.glb` + `.glb.import` (copied from broodhost: `nodes/use_name_suffixes=false`, own path hash, no uid)
- Triangles: 6,644 (budget 20k)
- Height: body/head ~2.9 m; glass crest shards to 3.17 m (idle). Bounding width 2.3 m in idle (shoulder clusters). PREVIEW_HEIGHT 3.3
- Clips: 42 base + `boss_charge boss_slam gs_1 gs_2` (required) + `cast_heavy` = 47
- Materials (palette `obsidian_golem`): BH_Stone glossy black glass, BH_Horn smoky glass shards, BH_DarkSteel inner core / joint balls, BH_Bronze old copper frame, BH_Gold copper seam lips, BH_Shadow, BH_Emissive pure white (1,1,1) energy 5

## What makes it distinct
Everything is knapped: flat-sided glass lofts (irregular polygon facets, hard ridges) held by copper bands, collars and clamps. Molten seams are copper-lipped white lines branching from a clamped seam-knot on the sternum. A crest of tall glass shards up the back and bursting from each pauldron is the gameplay-camera silhouette; small six-sided crystal head with a V of white eyes; forearms swell into faceted glass fists with shard knuckles. Not the bh-012 magma golem: no lava core, no basalt slabs, no orange.

## Evidence
`obsidian_golem_rest_iso.png` (T-pose front/back, idle x4 yaws, head close-ups, gameplay camera 54 deg at 16 / 22 m), `obsidian_golem_clips.png` (boss_charge, boss_slam, gs_1, gs_2).
Validation: `logs/godot_check.txt` (scratch Godot 4.7.2 project, 0 import errors, all 47 clips present with the anim_meta length). Worst skin stretch: 0.076 m (core column, death_crumple).

## Build log
```
[obsidian_golem] mesh 6644 tris, 174 parts, 0.7s
[obsidian_golem] baked 47 actions in 24.8s
[obsidian_golem] clip lengths verified (47 clips)
```

## Known limitations
No weapon (fists strike; gs_* swing both fists together). Low triangle count by design (flat facets); detail is in silhouette, not micro-geometry. Seams are white per the bh-029 rule (the "molten copper" reads through the copper lips around them).
