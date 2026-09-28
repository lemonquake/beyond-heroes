# Broodhost (`broodhost`)

- Module: `tools/blender/characters/enemy_broodhost.py` (kit `enemy_bandit_cutthroat` SB standard-space authoring, like `enemy_ghoul_brute`)
- GLB: `game/assets/characters/broodhost.glb` (3.4 MB) + `broodhost.glb.import` (necromancer settings, own path hash, no uid, `nodes/use_name_suffixes=false`)
- Triangles: 18386 (budget 20k); 24 bones; 8 materials
- Height: 2.5 m to the top of the hump sacs (SCALE 1.47; T-pose top 2.502 m, idle_1h f0 2.484 m). Width 1.43 m incl. the club arm in idle.
- Clips (48): the 42 shared enemy base clips + `axe_1 axe_2 axe_heavy boss_slam boss_roar cast_area`
  - `axe_1` / `axe_2`: club-fist swings (hits 0.30-0.40 s / 0.27-0.37 s of 0.6 s)
  - `axe_heavy`: overhead club smash (hit 0.67-0.77 s of 1.2 s)
  - `boss_slam`: two-handed ground slam (hit 0.67-0.80 s of 1.4 s)
  - `boss_roar` (1.53 s), `cast_area` (1.0 s, brood burst: crouch and heave - spawn the brood / pulse the sacs here)
- Weapon: none as a separate prop. The right forearm swells into a huge fleshy club-fist rigid on `weapon.R` (in-mesh, `K.enable_weapon_deform`), so a sword/axe attached by the game would clash with it - attach nothing. Left hand: long bone claws. Stance clip: `idle_1h`.

## Palette (`broodhost`, exported as `BH_*__broodhost`)
| material | use |
|---|---|
| BH_Skin (0.27, 0.235, 0.29) | bloated grey-violet hide |
| BH_Flesh (0.34, 0.09, 0.19) | raw rims round every sac, the club-fist flesh, the lamprey lips |
| BH_Emissive (0.95, 0.3, 0.9), emission (0.9, 0.22, 0.95) x6 | 32 glowing sacs (hump / back, shoulders, belly, forearm, thighs, club), tiny eyes |
| BH_Shadow (0.035, 0.01, 0.04) | the dark curled shapes pressed against the inside of each sac, the throat, gill slits |
| BH_Fur (0.1, 0.035, 0.12) | dark violet veins round the big sacs |
| BH_Bone | rings of hooked teeth, claws, knuckle bones, spurs, toenails |
| BH_Leather (0.23, 0.17, 0.09) | rope bindings (belly, diagonal wrap, arm and shin wraps, belt) |
| BH_Cloth_Primary | torn rag loincloth panels |

## What makes it distinct
- Silhouette: a hunched egg-shaped giant whose hump is crowned by a ring of bright magenta-violet sacs; from the high
  camera it reads as a dark mass rimmed with glowing pink bulbs, with a big pink club-fist on the right.
- vs plague_bloater (also glowing sacs): that one is yellow-green with green glow and a round gut; the Broodhost is grey-violet with magenta glow, ~0.4 m taller, hump-heavy (sacs mainly on top and back), and has the club-fist and lamprey mouth.
- vs ghoul_brute (club arm): grey-green, mossy, no glow except the eyes. vs mire_troll / ogre_crusher / mycelid_hulk: green / brown / pale fungus palettes, no magenta anywhere.
- Face: no jaw - a round sucker of hooked teeth round a black throat under two tiny glowing eyes.

## Evidence
- `broodhost_rest_iso.png`: T-pose front/back, idle_1h at 4 yaws, head close-ups, gameplay camera 54 deg at 16 / 22 m.
- `broodhost_clips.png`: idle_1h, all six attack clips, hit_heavy, death_back.
- `logs/broodhost_metrics.json`: worst absolute edge growth 0.12 m (run / boss_slam, lower corner of the front loincloth panel); body skin < 0.11 m.
- `logs/godot_check_broodhost.txt`: scratch Godot 4.7.2 project (`scratch/brutes/godot_broodhost`), 0 import errors, all 48 expected clips present with the `anim_meta.json` lengths, `block_loop` keeps its name.

## Build log
```
[broodhost] mesh 18386 tris, 205 parts, 1.5s
[broodhost] baked 48 actions in ~20s
[broodhost] clip lengths verified (48 clips)
[broodhost] -> A:\Python\beyond-heroes\game\assets\characters\broodhost.glb (3.4 MB)
[build] done in 24.3s
```

## Revision passes
1. First build read too slim and the club too small for a 2.5 m giant; the sacs sat on flat red "plates", thin veins stuck out of the hump like spikes, the belly sacs were buried in a separate belly lobe and the brow was a flat slab. Torso widened ~12 %, belly lobe removed (belly now in the torso rows so the sacs sit on it), club-fist enlarged (radius 0.21 std, 0.51 long), rims shrunk and sunk into the skin, veins shortened and dropped on the hump, dark curled shapes enlarged so they show on the membrane, brow rebuilt as a round ridge.
2. Metrics: the front loincloth corner stretched 0.3 m in run (weighted too far into the thigh) - panels now follow the hips more (max_leg 0.45), worst 0.12 m. SCALE 1.42 -> 1.47 to hit 2.5 m.

## Boss use (1.9x)
At 1.9x it is ~4.75 m. The sacs are 12-segment spheres and the club a 18-segment lathe, so the silhouette holds; up
close at that scale the teeth rings and ropes are the lowest-resolution parts (4-6 sided tubes). The glowing sacs are
the natural weak-point read; there is no separate `BH_WeakPoint` material (not requested).

## Known limitations
- The sacs are opaque emissive shells; the "translucent" look comes from a dark curled tube pressed against the inside surface (its back pokes through as a dark curl). No real transparency.
- Sacs, veins and ropes are rigid on their torso band (chest / spine weights); they do not jiggle.
- The head is sunk low and forward under the hump; head-turn clips (idle_look) turn it a little into the neck folds.
