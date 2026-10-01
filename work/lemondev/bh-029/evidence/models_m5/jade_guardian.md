# Jade Guardian (`jade_guardian`) - bh-029 Builder M5

- Module: `tools/blender/characters/enemy_jade_guardian.py` (construct helpers from `enemy_rune_golem` /
  `enemy_span_warden`, plaques from the M5 kit)
- GLB: `game/assets/characters/jade_guardian.glb` (+ `.glb.import` copied from `broodhost`, uid line removed)
- Build: `cd tools/blender/characters && "<blender>" -b --factory-startup --python build.py -- jade_guardian`
- Triangles: 16,772 (budget 20k). Bones: 24. Proportions x1.2 with broad shoulders.
- Height: 2.2 m to the helm; 2.49 m to the top of the stone feather crest.
- Role: shield tank (idle stance `idle_shield`). Shield on weapon.L (face -Y), spear on weapon.R.

## Clips
`CLIPS = ["shield_bash", "spear_1", "spear_heavy", "spear_2"]` + base set = 46 clips (all present in Godot, lengths
match). Mapping: thrust = `spear_1` (hit 0.17-0.27 s), bash = `shield_bash` (0.2-0.3 s), impale = `spear_heavy`
(0.67-0.77 s). `spear_2` is a spare.

## Look / what makes it distinct
A statue warrior, not a machine: one block of polished jade with smooth rounded limbs, a carved stern face (brow,
broad nose, lips, cheekbones) with white eye slits, a crest helm (gold brow band with turquoise studs, jade ear spools
with turquoise centres, a fan of nine carved stone feathers with quill grooves). Carved quilted cuirass (proud ridges,
the lowest gold-edged), a turquoise-and-gold mosaic arc round a jade glyph disc with a white core and channel ring,
round domed shoulder discs with turquoise rims and white dots, a skirt of jade slabs with a carved fret and
turquoise hems, carved bracers and greaves with white channels, sandalled slab feet with carved toes and gold straps.
The lore's "line of wire for a spine": a white channel from nape to pelvis with gold vertebra studs. Damage: dark
cracks across the right breast, the left flank and the left thigh, one greave channel broken.
Square shield (~0.78 m): jade slab in a gold frame, turquoise/gold mosaic border, a carved square spiral with the white
current in its groove (broken once) ending in a glyph eye, a crack, the lower corner snapped off.
Stone spear: dark-jade shaft in gold bands with a turquoise-wire grip, a broad carved jade leaf blade with white
channels on both flats, a turquoise feather tassel.

## Palette
BH_Stone jade, BH_Horn dark jade, BH_Bronze slot used for turquoise mosaic, BH_Gold, BH_Shadow, **BH_Emissive
(1,1,1)/(1,1,1) energy 5.0** (verified in Godot).

## Validation
- Scratch Godot import: OK, 0 errors. Metrics: worst edge growth 0.058 m (hips, spear_heavy / charge_hold).
- Evidence: `jade_guardian_rest_iso.png` (idle_shield stance), `jade_guardian_clips.png` (idle_shield, shield_bash,
  spear_1, spear_heavy, walk, death).

## Build log excerpt
```
[jade_guardian] mesh 16772 tris, 271 parts, 1.6s
[jade_guardian] baked 46 actions in 23.7s
GLB jade_guardian tris=16772 bones=24 mats=7 anims=46 expected=46 missing=[] length_mismatch=[]
```

## Known limitations
- The spear clips raise the shield arm roughly horizontal (shared library pose; the shield stays readable in
  `idle_shield` / `shield_bash`).
- Revision passes: 1 (stance check: the game plays `idle_shield` for archetype `shield`).
