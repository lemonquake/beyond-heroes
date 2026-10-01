# Quorrath, the Jade Sleeper (`jade_king`) - bh-029 Builder M5, BOSS of the Jade Sepulchre

- Module: `tools/blender/characters/enemy_jade_king.py` (SB standard-space authoring, SCALE 1.95; cape bones from
  `char_knight.CAPE_BONES` with `secondary()` motion)
- GLB: `game/assets/characters/jade_king.glb` (+ `.glb.import` copied from `broodhost`, uid line removed)
- Build: `cd tools/blender/characters && "<blender>" -b --factory-startup --python build.py -- jade_king`
- Triangles: 34,294 (budget 35k). Bones: 26 (24 + cape.1, cape.2).
- Height (authored, model scale 1.0): head ~3.5 m, crown top ~3.9 m, feather fan tip 4.54 m.
- Role: boss (idle stance `idle_2h`). Sceptre on weapon.R.

## Clips
`CLIPS = ["boss_roar", "boss_slam", "boss_summon", "cast_area", "cast_heavy", "cast_ultimate", "staff_heavy",
"boss_sweep", "cast_quick"]` + base set = 51 clips (all present in Godot, lengths match). Mapping: sceptre =
`staff_heavy` (hit 0.67-0.8 s), serpent_volley = `cast_heavy`, court_rises = `boss_summon`, green_fire = `cast_area`,
tomb_slam = `boss_slam` (0.67-0.8 s), call_guard = `boss_roar`, jade_storm = `cast_ultimate`. `boss_sweep` and
`cast_quick` are spares.

## Look / what makes it distinct
A mummified king in jade throne-armour. Under it: funeral linen, linen-wrapped arms and legs with white binding wire.
Cuirass of gold-stitched jade plaque courses all round the torso; the breast is broken open - a dark cavity with three
white wire coils (gold helices round white cores, gold collars), bone ribs across the opening, jagged jade shards round
the edge and torn gold wires hanging. Broad jade collar with turquoise and gold rings, a gold-and-jade plaque belt,
stepped three-tier jade pauldrons with turquoise edges and gold bosses, jade bracers, gold armlets, a long kilt of jade
and turquoise plaque rows (front, back and per-thigh panels on gold beads) over a scarlet loincloth, jade greaves with
turquoise side plates. Face: the M5 jade death-mask (white eye slits) with jade ear flares and bead strings. The
crown: four octagonal jade tiers widening upward, gold bands, turquoise studs, stepped jade side wings, a jade
medallion with a gold coiled serpent and white eyes, and a 15-feather teal/scarlet fan with an inner scarlet fan.
A feather cape (dark backing, four rows of feathers, scarlet-tipped hem) on the cape bones.
Serpent sceptre (~1.95 m standard x 1.95): jade staff in gold bands, gold wire grip, a white wire coil, a feather collar,
a rearing S-curved jade serpent with gold scale rings, white eyes, gold fangs and a feather crest. Left hand: open
linen claw with long jade nail-guards (casting hand).

## Palette
BH_Stone jade, BH_Horn turquoise, BH_Cloth_Primary linen, BH_Cloth_Secondary scarlet, BH_Skin, BH_Bone ribs,
BH_Hair teal feathers, BH_Flesh scarlet, BH_Fur cape backing, BH_Gold, BH_Shadow, **BH_Emissive (1,1,1)/(1,1,1)
energy 5.0** (verified in Godot). No BH_WeakPoint (not asked for this boss).

## Validation
- Scratch Godot import: OK, 0 errors. Metrics: worst edge growth 0.104 m (spine, strafe_r), 0.093 m at the shoulder in
  boss_slam / boss_sweep - in line with the other bosses (deathspan_colossus 0.111 m).
- Evidence: `jade_king_rest_iso.png` (T-pose, idle_2h x4, chest-cavity close-ups, gameplay camera at 16 / 22 m),
  `jade_king_clips.png` (idle_2h, staff_heavy, boss_slam, boss_roar, boss_summon, cast_area, cast_heavy, cast_ultimate,
  walk, death).

## Build log excerpt
```
[jade_king] mesh 34294 tris, 664 parts, 4.3s
[jade_king] baked 51 actions in 27.8s
GLB jade_king tris=34294 bones=26 mats=12 anims=51 expected=51 missing=[] length_mismatch=[]
```

## Known limitations / wiring
- **Scale:** the model is authored at true size (~4 m crown). `data_enemies_zarael.gd` gives it `model_scale 1.7`,
  which would make it ~6.6 m to the crown (7.7 m to the feather tips). Use `model_scale` ~1.0 for the brief's ~4 m
  (body_height 4.0 already matches the authored model).
- Close to the triangle budget (34.3k / 35k).
- Revision passes: 3 (crown shortened and recoloured, gold collar changed to jade with gold/turquoise rims, fan
  shortened ~15%).
