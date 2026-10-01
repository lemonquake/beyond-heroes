# Obsidian Shardcaster (`shardcaster`)

- Module: `tools/blender/characters/enemy_shardcaster.py` (bandit kit SB + ashen_cultist hood, SCALE 1.88/1.818)
- GLB: `game/assets/characters/shardcaster.glb` + `.glb.import` (broodhost settings, own path hash, no uid)
- Triangles: 13,074 (budget 20k)
- Height: ~1.88 m to the hood; glass crest 2.15 m
- Clips: 42 base + `cast_area cast_weapon dagger_1 wand_1` = 46
- Materials (palette `shardcaster`): BH_Stone glossy obsidian scales / mask / bracers, BH_Horn smoky glass shards, BH_Cloth_Primary deep-red quilted under-tunic, BH_Cloth_Secondary dark teal hood, BH_Leather sleeves / straps / cradle, BH_Bronze copper edging, BH_Skin, BH_Ichor dark trousers, BH_Shadow, BH_Emissive pure white (eye slits, brow glyph, gorget glyph, bracer glyphs, sling-shard glyph)

## What makes it distinct
Lean figure in a coat of ~200 lozenge obsidian scales (copper collar/hem bands, obsidian gorget with a white stepped glyph), long split scale strips to the knee, scale pauldrons. Dark teal hood with three tall glass shards rising from its back (silhouette key), smooth black glass face-mask with two white eye slits. Bandolier of black shards point-up in copper loops, a quiver-sheaf of shards at the right hip, obsidian blade lashed along the right forearm.

## Weapons / wiring
- weapon.R: the glass sling - two bead cords (obsidian + copper beads) hanging from the fist to a leather cradle holding a knapped shard with a white glyph. Rigid. `wand_1` / `cast_weapon` = sling casts (game spawns the shard projectile).
- weapon.L: a jagged shard held point-forward with a copper-wound grip.
- `dagger_1` (right hand) reads as the forearm-blade slash.

## Evidence
`shardcaster_rest_iso.png`, `shardcaster_clips.png`. Validation `logs/godot_check.txt` (0 errors, 46 clips at meta length). Worst stretch 0.071 m (after giving the centre skirt strips shared thigh weights).

## Build log
```
[shardcaster] mesh 13074 tris, 509 parts, 1.3s
[shardcaster] baked 46 actions in 19.0s
[shardcaster] clip lengths verified (46 clips)
```

## Known limitations
The sling is rigid (cords do not swing). The palette is dark by design (obsidian dungeon); readability comes from the white mask eyes, glyphs and the shard crest.
