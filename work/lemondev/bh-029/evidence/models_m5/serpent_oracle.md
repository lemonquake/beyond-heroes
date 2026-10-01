# Serpent Oracle (`serpent_oracle`) - bh-029 Builder M5

- Module: `tools/blender/characters/enemy_serpent_oracle.py`
- GLB: `game/assets/characters/serpent_oracle.glb` (+ `.glb.import` copied from `broodhost`, uid line removed)
- Build: `cd tools/blender/characters && "<blender>" -b --factory-startup --python build.py -- serpent_oracle`
- Triangles: 18,670 (budget 20k). Bones: 24 (SCALE 1.0).
- Height: 1.84 m to the head; 2.20 m to the tip of the feather fan.
- Role: caster (idle stance `idle_staff`). Staff on weapon.R (mesh, deforming with the socket).

## Clips
`CLIPS = ["cast_area", "cast_heavy", "cast_quick", "staff_1", "cast_weapon"]` + base set = 47 clips (all present in
Godot, lengths match). Mapping: staff = `staff_1` (hit 0.13-0.27 s), venom_bolt = `cast_quick`, serpent_coil =
`cast_heavy`, green_fire + mend = `cast_area`. `cast_weapon` added as a spare.

## Look / what makes it distinct
Feathered-serpent headdress: a jade serpent head worn on the crown - the upper jaw arches over her brow (gold lip
band, hanging fangs), the open lower jaw runs down beside her cheeks to a chin piece, white serpent eyes, gold-edged
scale ridges and a turquoise spine row, a ruff of short feathers at the jaw hinge and a 13-feather teal/scarlet fan
behind. Painted face (dark band + small white eyes), long black hair. Broad turquoise mosaic collar: three rows of
tiles (turquoise / jade / turquoise) on a gold backing with a gold rim, and a jade pectoral disc with a white light.
Long deep-green robe with a gold stepped-fret band above a gold hem, scarlet sash with jade-tasselled ends, a feather
bustle at the back of the waist. Gold armbands, turquoise cuffs, a white wire round the casting (left) forearm.
Staff: black wood, jade foot, a carved jade serpent coiling up the shaft in gold bands, rearing through a gold ring
of turquoise tiles that holds a white light on four gold spokes; small feather crest.

## Palette
BH_Cloth_Primary deep green, BH_Cloth_Secondary scarlet, BH_Skin, BH_Hair teal feathers, BH_Flesh scarlet tips,
BH_Fur black hair, BH_Stone jade, BH_Horn turquoise, BH_Bone fangs, BH_Wood black wood, BH_Gold, BH_Leather,
BH_Shadow, **BH_Emissive (1,1,1)/(1,1,1) energy 5.0** (verified in Godot).

## Validation
- Scratch Godot import: OK, 0 errors. Metrics: worst edge growth 0.05 m (neck, wall_impact).
- Evidence: `serpent_oracle_rest_iso.png`, `serpent_oracle_clips.png` (idle_staff, cast_area, cast_heavy, cast_quick,
  staff_1, walk).

## Build log excerpt
```
[serpent_oracle] mesh 18670 tris, 378 parts, 2.1s
[serpent_oracle] baked 47 actions in 23.6s
GLB serpent_oracle tris=18670 bones=24 mats=15 anims=47 expected=47 missing=[] length_mismatch=[]
```

## Known limitations
- In the shared cast clips the staff hangs low / points back (library hand pose, same as the other staff casters).
- Revision passes: 2 (collar tiles made flat to get under budget: 21.5k -> 18.7k; serpent nostrils / eyes tuned).
