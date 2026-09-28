# stonegaze_basilisk (Stonegaze Basilisk, stem `basilisk_`)

- Script: `tools/blender/creatures/build_stonegaze_basilisk.py`, using the shared kit `tools/blender/creatures/kit_c13.py` (a quadruped with planar leg IK and gait layers, ported from `build_rootback_boar.py` / `build_wolf.py`; those files are not modified).
- GLB: `game/assets/characters/stonegaze_basilisk.glb` (1.7 MB). The `.glb.import` is copied from rootback_boar with the uid line removed and the paths fixed.
- Triangles: 9,446. 36 bones:
  - root, hips, spine, chest, neck, head, jaw
  - frill.C / frill.L / frill.R (the fan; it folds back at rest and spreads during the gaze)
  - tail.1-6
  - per side: scap / upperarm / forearm / fpaw / ftoe (front) and femur / thigh / shin / hpaw / htoe (hind)
  - Sprawl: the horizontal scap / femur bones carry each leg about 0.55 m out from the spine, so the feet are planted wide like a lizard's.
- Size (rest bounds): x ±0.71 m, y -1.57 (snout) .. +1.84 (tail club), z 0 .. 1.36 m. That is about 3.4 m nose to club. The back is about 1.05 m high, the dorsal spikes reach about 1.2 m and the folded frill tips 1.36 m.
- The origin is on the ground under the body, and the model faces -Y (Godot +Z).
- Eyes (the gaze source): two big emissive spheres at about (±0.15, -1.06, 0.97) in rest space on the `head` bone. During `basilisk_gaze` the head is raised and locked forward. If the game draws a beam, attach it to the head bone about 0.2 m above and forward of the head bone origin.

## Clips (15, in place, 30 fps)
Loop flags are the ones the game applies.
- idle 3.0 s (loop): breathing, slow head sway, tail wag, jaw and frill twitch
- idle_look 2.5 s: looks left then right, and the frill lifts
- walk 1.333 s (loop, ground_speed 1.0): diagonal gait with lizard body undulation; shoulders and hips swing opposite and the tail follows
- run 0.733 s (loop, 3.4), run_combat 0.733 s (loop, 3.4): a faster, lower undulating trot; run_combat carries the head lower, the jaw open and the frill half raised
- hit_light 0.4 s, hit_heavy 0.6 s, stagger_small 0.8 s, knockback 0.9 s (slides back about 0.3 m)
- death 1.5 s: the legs buckle and it rolls about 80° onto its right side
- death_back 1.5 s: the same collapse, rolling onto its left side
- alert 1.0 s: head up, the frill flicks open, the tail lifts, then a hiss
- `basilisk_bite` 0.9 s, hits [0.4, 0.533]: draws the head back, then snaps forward and down. The body lunges about 0.22 m and the jaws close at about 0.47 s.
- `basilisk_gaze` 1.2 s, **loop** (hold it while channelling): forequarters reared about 13°, frill spread wide with its 5 glowing eye-spots, head locked on the target, jaw ajar. It only trembles, breathes and pulses the frill; the first frame equals the last. There are no hit times, so the game times the petrify effect.
- `basilisk_tail` 0.9 s, hits [0.533, 0.667]: turns the hips and winds the club tail to its right, then sweeps it round its left side toward the front. The club passes the front-left flank at about 0.6 s. This is a one-sided sweep, so it covers roughly the left and front-left arc.

creature_meta.json holds `animations.basilisk_bite/basilisk_gaze/basilisk_tail` and `models.stonegaze_basilisk` (every clip, tris 9446, bones 36). The build re-read the file before writing, and the verify step after the write found every other key unchanged.

## Palette (`<name>__stonegaze_basilisk`)
- BH_Stone: slate-grey hide, legs, tail
- BH_Horn: dark scale plates, dorsal spikes, brows, the stone tail club, frill spines
- BH_Skin: pale belly plates and throat
- BH_Cloth_Secondary: moss patches
- BH_Fur: pale lichen
- BH_Flesh: rust frill membrane
- BH_Wood: dark hooked claws
- BH_Bone: teeth
- BH_Shadow: mouth, slit pupils, nostrils
- BH_Emissive: yellow-green eyes and frill eye-spots (emission 7)

## What makes it distinct
It is a low, wide, sprawling lizard with a long spiked tail ending in a stone club. Its signature is a rust-coloured fan frill with glowing eye-spots behind two big yellow-green eyes. From the gameplay camera it reads as a long grey cross shape: splayed legs, a spiked ridge, and a rust half-disc with green dots at the head end. No other enemy has a sprawling lizard stance or a frill. The slate-grey with moss and green glow palette differs from the rootback boar (brown and bark), the slag hound and the reef crawler.

## Evidence
- `stonegaze_basilisk_rest_iso.png`: front 3/4, side, back 3/4, a head close-up, and game-camera crops (16 m facing 0 and 150, 24 m facing 60).
- `stonegaze_basilisk_clips.png`: basilisk_bite, basilisk_gaze, basilisk_tail, walk, run and death at 5 normalized times.
- `godot_check.txt` (scratch Godot 4.7.2 project, `tools/godot_check_creatures.py`): 15 clips imported, none missing, no length mismatches and no loop-flag mismatches. RESULT OK.

## Build log
```
[stonegaze_basilisk] mesh 9446 tris, 15 clips, 36 bones
[stonegaze_basilisk] numpy FK vs Blender pose: worst 0.00 mm at ('death', 45, 'frill.L')
[stonegaze_basilisk] meta merged ['basilisk_bite', 'basilisk_gaze', 'basilisk_tail'] + models.stonegaze_basilisk -> ...creature_meta.json (verified: True)
[stonegaze_basilisk] -> ...stonegaze_basilisk.glb (1.7 MB)
[stonegaze_basilisk] 15 animations in the GLB; length mismatches: []
[evidence] stonegaze_basilisk rest bounds [-0.709 -1.57   0.013] [0.703 1.84  1.356]
```

## Known limitations
- The frill membrane is a thin two-sided sheet (two offset surfaces), so at grazing angles it looks paper-thin.
- In the deaths the folded frill and the dorsal spikes on the downward side pass slightly into the ground.
- The back plates, moss and spikes are skinned to the three back bones. Under strong undulation (run) neighbouring plates overlap a little on the inside of the bend.
- `basilisk_tail` only sweeps to the left. There is no mirrored right-side variant.
- The gaze has no built-in beam or VFX; the game must supply the petrify effect.
- This evidence file was written after the build by Builder C2 (the original builder was cut off). The model was not rebuilt because the scratch Godot check passed.
