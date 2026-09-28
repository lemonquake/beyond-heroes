# shellback_grinder (Shellback Grinder, stem `shell_`)

- Script: `tools/blender/creatures/build_shellback_grinder.py`, using the shared kit `tools/blender/creatures/kit_c13.py` (a quadruped with planar leg IK and gait layers, ported from `build_rootback_boar.py` / `build_wolf.py`; those files are not modified). Builder C started the script (rig and palette); Builder C2 finished it (clips, mesh, ground fit, export).
- GLB: `game/assets/characters/shellback_grinder.glb` (1.6 MB). The `.glb.import` is copied from rootback_boar with the uid line removed and the paths fixed.
- Triangles: 9,058 (budget 20k). 30 bones:
  - root, hips, spine1, spine2, chest, neck, head, jaw
  - tail.1-4
  - per side: scap / upperarm / forearm / fpaw / ftoe (front) and thigh / shin / hpaw / htoe (hind)
  - A flexible spine: a `ball` channel (0..1) bends spine1 / spine2 / chest / neck / head nose-down by 34 / 40 / 44 / 48 / 52° and each tail bone by 44°, so the chain rolls up nearly 400° with the tail wrapping round the outside.
- Size (rest bounds): x ±0.49 m, y -1.07 (snout) .. +1.31 (tail tip), z 0 .. 1.19 m. That is about 2.4 m from snout to tail tip (about 2.1 m without the tail's last taper) and 1.19 m to the top of the back plates. The head is small and low: its top is at about 0.8 m.
- Curled ball: about 0.96 × 1.24 × 1.17 m (x × y × z). It is centred at y ≈ 0.05 over the origin and rests on the ground.
- The origin is on the ground under the body, and the model faces -Y (Godot +Z).

## Clips (18, in place, 30 fps)
Loop flags are the ones the game applies.
- idle 3.0 s (loop): breathing, sniffing, head sway, tail sway
- idle_look 2.5 s
- walk 0.933 s (loop, ground_speed 0.6): a heavy waddle with short steps and body roll
- run 0.4 s (loop, ground_speed 2.4), run_combat 0.4 s (loop, 2.4): a fast short-stepped trot; run_combat is lower, jaw open and slightly hunched
- hit_light 0.4 s, hit_heavy 0.6 s (flinches into a slight curl), stagger_small 0.8 s, knockback 0.9 s (slides back 0.3 m)
- death 1.5 s: the legs buckle, it slumps onto its left side and half curls up
- death_back 1.5 s: rears up, topples sideways and ends belly-up with the legs limp in the air
- alert 1.0 s: rears up on its hind legs a little and sniffs with the horn raised, then drops back
- `shell_bite` 0.9 s, hits [0.433, 0.533]: draws the head back, lunges forward and down about 0.2 m, and the toothy snout snaps shut at about 0.47 s.
- `shell_swipe` 0.9 s, hits [0.467, 0.567]: rears the forequarters, raises the **right** fore-claw high, then rakes it down and across in front, reaching about 0.3 m forward of the rest foot.
- `shell_curl` 0.6 s, non-loop: tucks the head, humps the back and rolls into the ball. The last frame equals the first frame of `shell_roll`.
- `shell_roll` 0.6 s, **loop**: the curled ball turns once forward about its side axis (the whole body rotates 360° per cycle) in place. At ground_speed the game should move it about 2πr ≈ 3.7 m per cycle, i.e. about 6 m/s for a rolling look without slip. The model is not quite round, so a per-frame lift fitted from the skinned mesh keeps the lowest point on the ground; the centre bobs by about 0.11 m.
- `shell_uncurl` 0.6 s: opens from the ball pose, the legs come down, and it settles into the idle pose.
- `shell_flipped` 1.0 s, **loop**: on its back with the pale belly up. It rocks ±7°, all four legs flail in the air out of phase, and the head and tail thrash. This is the vulnerable state.

Suggested wiring:
- Roll attack: `shell_curl`, then `shell_roll` (loop) while the game moves the node, then `shell_uncurl`.
- Stun / weak window: `shell_flipped` (loop), then `shell_uncurl` or a return to `idle`.

creature_meta.json holds `animations.shell_bite/shell_swipe/shell_curl/shell_roll/shell_uncurl/shell_flipped` and `models.shellback_grinder` (every clip, tris 9058, bones 30), registered exactly as stonegaze_basilisk and rootback_boar are. The build re-read the file before writing, and the verify step after the write found every other key unchanged.

## Palette (`<name>__shellback_grinder`)
- BH_Steel: iron-grey plates, with the head hood, brows and upper-leg plates
- BH_Rust: rust-brown plates. Every third row from shoulders to tail tip is rust, so the back shows bold grey-rust stripes.
- BH_Skin: pale soft underbelly, body, legs, face, jaw
- BH_Bone: teeth, snout horn and nub, digging claws
- BH_Horn: dark claw tips, nose pad
- BH_Flesh: gums, ears
- BH_Shadow: mouth
- BH_Emissive: small amber eyes (emission 5)

The plates are overlapping shingle rows with pointed trailing edges. There are about 17 rows from the shoulders to the tail tip, plus 2 on the neck and 3 on the head. The rear edge of each row is lifted over the row behind it.

## What makes it distinct
It is the only armoured "pangolin" shape. From the gameplay camera it reads as a long oval dome of pointed grey scales banded with rust stripes, ending in a scaled tapering tail and a small pale horned snout. The palette is metallic grey and rust over pale beige. It differs from rootback_boar (brown bark and moss), stonegaze_basilisk (slate with moss and a green-glowing frill), slag_hound and reef_crawler. Its signature states, the rolling ball and the belly-up flail, are unique silhouettes.

## Evidence
- `shellback_grinder_rest_iso.png`: front 3/4, side, back 3/4, a head close-up, and game-camera crops (16 m facing 0 and 150, 24 m facing 60).
- `shellback_grinder_clips.png`: shell_bite, shell_swipe, shell_curl, shell_roll, shell_uncurl, shell_flipped, walk and death_back at 5 normalized times.
- `godot_check.txt` (scratch Godot 4.7.2 project, `tools/godot_check_creatures.py`, all four Builder C creatures): 18 clips imported, none missing, no length mismatches and no loop-flag mismatches, 0 import errors. RESULT OK.
- Revision passes: 2.
  - Pass 1: full build and previews.
  - Pass 2: the roll pivot moved from the bone-chain centre to the centre of the skinned ball's bounds, cutting the roll bob from 0.33 m to 0.11 m.

## Build log
```
[shellback_grinder] ground fit: ball up 0.066, roll up 0.004..0.113, flip -0.261, death -0.231, death_back -0.268
[shellback_grinder] ball: centre [-0.001  0.14   0.502], bounds [-0.48 -0.57  0.01] .. [0.48 0.67 1.18], radius p50 0.303 p95 0.636 max 0.718
[shellback_grinder] mesh 9058 tris, 18 clips, 30 bones
[shellback_grinder] numpy FK vs Blender pose: worst 0.00 mm at ('knockback', 14, 'ftoe.R')
[shellback_grinder] meta merged ['shell_bite', 'shell_curl', 'shell_flipped', 'shell_roll', 'shell_swipe', 'shell_uncurl'] + models.shellback_grinder -> ...creature_meta.json (verified: True)
[shellback_grinder] -> ...shellback_grinder.glb (1.6 MB)
[shellback_grinder] 18 animations in the GLB; length mismatches: []
[evidence] shellback_grinder rest bounds [-0.485 -1.073  0.012] [0.485 1.312 1.188]
```

## Known limitations
- The ball is skinned from the standing mesh, so the plate rows stretch on the outside of the curl instead of sliding. At the two sides of the ball the tucked pale legs and belly show through the opening. During the roll you can see them for part of each turn.
- The ball is slightly oval, so the rolling ball bobs by about 0.11 m per turn. That reads as a heavy lumpy roll.
- The head plates' pointed edges point forward rather than back. This is only visible in the close-up.
- `shell_swipe` only uses the right fore-claw. There is no mirrored left variant.
- The upper-leg plates are simple ellipsoid caps.
- The legs are short (about 0.45 m) and nearly straight at rest, so walk and run use short strides with low ground speeds (0.6 / 2.4 m/s). Faster travel should use the roll.
