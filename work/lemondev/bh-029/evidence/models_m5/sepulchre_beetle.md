# Sepulchre Beetle (`sepulchre_beetle`) - bh-029 Builder M5

- Script: `tools/blender/creatures/build_sepulchre_beetle.py` (imports `creature_kit_c`, layout after
  `build_glasswire_scorpion.py`; no existing script edited)
- Run: `cd tools/blender/creatures && "<blender>" -b --factory-startup --python build_sepulchre_beetle.py --`
  (`--no-export --evidence` for renders only)
- GLB: `game/assets/characters/sepulchre_beetle.glb` (+ `.glb.import` copied from `glasswire_scorpion`, uid removed)
- Triangles: 10,476. Bones: 31 (root, body, head, mand.L/R, elytra.L/R, 6 legs x 4).
- Size: 2.36 m long (horn base to the end of the wing cases), 2.56 m leg span, shell top ~1.15 m, horn tip 1.59 m.
  Authored on a 2.0 m layout and scaled by `SC = 1.22` (rig and mesh together).
- **Six legs**, not eight: a beetle is an insect. It uses the 8-leg ("spider") kit (`creature_kit_c.plane_leg`) with
  three pairs and an alternating tripod gait (L1 R2 L3 / R1 L2 R3). `body_shape: spider` in the data still applies.

## Clips (30 fps, in place) - creature_meta.json `models.sepulchre_beetle` + `animations.beetle_*`
| clip | length (s) | loop | hits (s) | ground_speed |
|---|---|---|---|---|
| idle | 3.0 | yes | - | - |
| idle_look | 2.5 | no | - | - |
| walk | 0.733 | yes | - | 1.3 |
| run | 0.333 | yes | - | 4.0 |
| run_combat | 0.333 | yes (head lowered, horn levelled: the charge hold) | - | 3.8 |
| hit_light / hit_heavy | 0.4 / 0.6 | no | - | - |
| stagger_small / knockback | 0.8 / 0.9 | no | - | - |
| death | 1.5 | no (tips onto its back, legs curl) | - | - |
| death_back | 1.5 | no (drops flat, wing cases fall open) | - | - |
| alert | 1.0 | no (rears, wing cases lift, mandibles wide) | - | - |
| `beetle_bite` | 0.8 | no | [0.367, 0.467] | - |
| `beetle_ram` | 1.0 | no | [0.6, 0.733] | - |
| `beetle_spit` | 1.333 | no | [0.867, 1.033] | - |

- `beetle_bite`: head draws back, mandibles open wide, lunge (+0.2 m) and snap shut.
- `beetle_ram`: crouch, the right front leg paws twice, head drops with the horn levelled, lunge horn-first
  (+0.3 m) at 0.6 s - matches the data's 0.7 s wind-up; the game's `hold_anim: run_combat` continues the charge.
- `beetle_spit`: rears back (wing cases lift, shell pumps), head thrown up, then forward/down with the mouth wide;
  the spit leaves at ~0.9 s, matching the data's 1.0 s wind-up.
- Foot slip: walk max 4.4 mm/frame (mean 0.1), run / run_combat 0. IK reach misses 0 mm except death clips (14-17 mm,
  legs curled). numpy-vs-Blender pose check 0.002 mm.

## Look
Domed jade pronotum with a gold rim, a gold stepped-fret band between gold lines, a jade keel, a gold knot with a
white glow, gold studs. Two great jade elytra (own bones) with gold-wire inlay: three lines down each case, a gold
suture and outer rim, a fret band across the shoulders with white knots where the lines cross, a row of jade bosses
in gold collars. Dark folded wings under the cases, dark underside plates. Dark-jade head with a tall curved horn in
three gold bands with a white channel up its front and two small tines, white compound eyes ringed dark, clubbed
black antennae, serrated black mandibles (own bones) with gold bases, palps, a white glow in the mouth. Six thick
spined dark-jade legs with gold joint rings, segmented tarsi and black hooked claws.

## Palette
BH_Stone jade shell, BH_Horn dark jade, BH_Gold gold wire, BH_Flesh underside, BH_Leather membranes / wings,
BH_DarkSteel black mandibles / claws / spines, BH_Shadow, **BH_Emissive (1,1,1)/(1,1,1) energy 5.0** (verified).

## Validation
- Scratch Godot import: `GLB sepulchre_beetle tris=10476 bones=31 mats=9 anims=15 expected=15 missing=[]
  length_mismatch=[]`, `GODOT_RESULT OK`.
- creature_meta.json merge: only `animations.beetle_*` and `models.sepulchre_beetle` written; re-read before
  writing and verified after (all other models / animations unchanged; scorp_, cat_, mhound_ keys present).
- Evidence: `sepulchre_beetle_rest_iso.png`, `sepulchre_beetle_clips.png` (HIT frames labelled).

## Build log excerpt
```
[sepulchre_beetle] numpy-vs-Blender pose check: worst bone head/tail error 0.002 mm
[sepulchre_beetle] mesh 10476 tris, 5596 verts, 31 bones, 15 clips; rest bounds x -1.279..1.279 y -1.165..1.196 z -0.026..1.592
[sepulchre_beetle] check_lengths: 15 animations in the GLB; mismatches: []
[sepulchre_beetle] meta merged ['beetle_bite', 'beetle_ram', 'beetle_spit'] + models.sepulchre_beetle -> ...creature_meta.json (verified: True)
```

## Known limitations
- Six legs on the 8-leg kit (see above).
- Leg span (2.56 m) is wider than `body_radius 0.95`; the shell itself is ~1.0 m wide.
- Revision passes: 3 (body lowered and legs shortened/thickened - less spider-like; stride lengths fixed for IK
  reach; whole model scaled x1.22 to the brief's ~2.4 m).
