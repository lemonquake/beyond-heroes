# Jade-Wrapped Sleeper (`jade_sleeper`) - bh-029 Builder M5

- Module: `tools/blender/characters/enemy_jade_sleeper.py` (also holds the small M5 Jade kit: `surf_frame`, `plaque`,
  `torso_plaques`, `glow_wrap`, `linen_wrap`, `death_mask`, `WHITE_GLOW`)
- GLB: `game/assets/characters/jade_sleeper.glb` (+ `.glb.import` copied from `broodhost`, uid line removed)
- Build: `cd tools/blender/characters && "<blender>" -b --factory-startup --python build.py -- jade_sleeper`
- Triangles: 16,566 (budget 20k). Bones: 24 (shared enemy skeleton, SCALE 1.0).
- Height: 1.83 m (top of the head wraps / brow plaque).
- Role: fodder (idle stance `idle_1h`, archetype `fodder`).

## Clips
`CLIPS = ["axe_1", "axe_2", "cast_quick"]` + the 42 shared enemy base clips = 45 clips (Godot scratch import: all
present, lengths match `anim_meta.json`). Gameplay mapping (data_enemies_zarael.gd): grasp = `axe_1` (hit 0.30-0.40 s),
bind = `axe_2` (0.27-0.37 s), tomb_breath = `cast_quick`. Empty hands: both hands are open claws, the axe swings read
as raking grabs.

## Look / what makes it distinct
Gaunt body in pale funeral linen: diagonal bandage courses round the torso, spiral wraps on every limb, stained loose
ends hanging from the shoulders, elbows and the hip belt. Small jade plaques sewn on in gold wire: a 4 x 5 pectoral,
a collar ring of plaques, a plaque belt, six-plaque bracers, three-plaque shin guards, a round knee plaque. White
binding wire wound round chest (two crossing strands with a gold knot at the breastbone), waist, upper arms, forearms,
thighs and down the shins. Face: a carved jade death-mask (brow ridge, nose, almond eye slits lit white, dark mouth with
jade teeth, a gold brow band) with gold ear spools. Long dark-jade nail-guards on the claw fingers.

## Palette (`PALETTE_COLORS`)
BH_Cloth_Primary pale linen, BH_Cloth_Secondary stained linen, BH_Skin dried flesh, BH_Stone jade, BH_Horn dark jade,
BH_Gold gold wire, BH_Shadow, BH_Bone (ribs patch), **BH_Emissive albedo (1,1,1) / emission (1,1,1) energy 5.0**
(verified in the Godot import).

## Validation
- Scratch Godot import (`work/lemondev/bh-029/scratch/m5/tools/godot_check_m5.py`): `GODOT_RESULT OK`, 0 import errors.
- Deformation (scratch `ev_blender.py --mode metrics`): worst absolute edge growth 0.040 m at the shoulders
  (idle_2h / axe_1), comparable to the other bh-029 humanoids (0.05-0.11 m).
- Evidence: `jade_sleeper_rest_iso.png` (T-pose, idle_1h stance x4, head close-ups, gameplay camera 54 deg at 16 / 22 m),
  `jade_sleeper_clips.png` (idle, walk, axe_1, axe_2, cast_quick, death).

## Build log excerpt
```
[jade_sleeper] mesh 16566 tris, 243 parts, 1.8s
[jade_sleeper] baked 45 actions in 21.7s
[jade_sleeper] clip lengths verified (45 clips)
GLB jade_sleeper tris=16566 bones=24 mats=10 anims=45 expected=45 missing=[] length_mismatch=[]
```

## Known limitations
- No weapon: the axe clips swing an empty claw hand (intended "grasp").
- Revision passes: 2 (mask rim removed, eye slits narrowed, hip tatters added).
