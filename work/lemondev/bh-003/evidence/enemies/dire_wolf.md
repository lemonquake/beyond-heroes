# dire_wolf (Builder C)

- Source: `tools/blender/creatures/build_wolf.py`. It builds the armature, mesh, clips, `creature_meta.json` and the GLB. Previews: `--preview DIR --clips a,b --frames … --views … --no-export`.
- GLB: `game/assets/characters/dire_wolf.glb` (16 glTF animations, one per clip, ACTIONS-mode export; the lengths are checked against the clip definitions after export)
- Size: withers ~0.95 m, ear tips 1.24 m, nose to tail tip ~1.73 m (the tail hangs). Faces -Y in Blender (= +Z in Godot); origin on the ground.
- Triangles: **6,516**
- Materials (`__dire_wolf`): BH_Fur (grey-black coat), BH_Hair (near-black ragged mane, back stripe, tail tip), BH_Stone (pale muzzle, jaw, belly and chest ruff), BH_Bone (teeth, claws), BH_Flesh (mouth, inner ears, scars), BH_Shadow (nose, lips), BH_Emissive (pale cyan eyes, the faint Aether glint)
- Armature (31 bones):
  - root, hips, spine, chest, neck, head, jaw, ear.L/R, tail.1–4
  - Front legs: scap.L/R → upperarm → forearm → fpaw → ftoe
  - Hind legs: thigh.L/R → shin → hpaw → htoe
  - The root carries the body offsets (location + rotation); every other bone is rotation only.
- Clips (30 fps, all in place; lengths also in `creature_meta.json`):

| clip | length s | loop | notes |
|---|---|---|---|
| idle | 3.0 | yes | breathing, tail sway, ear flick |
| idle_look | 2.5 | no | looks left, then right |
| walk | 1.0 | yes | lateral-sequence walk, ground_speed 1.25 m/s |
| run | 0.5 | yes | rotary gallop with spine flex, ground_speed 5.5 m/s |
| run_combat | 0.5 | yes | same gait, lower, ears pinned, 5.5 m/s |
| hit_light / hit_heavy | 0.4 / 0.6 | no | |
| stagger_small | 0.8 | no | |
| knockback | 0.9 | no | pushed back 0.3 m and recovers to the origin |
| death / death_back | 1.5 / 1.5 | no | buckles and rolls onto its right / left side; the last frame is held lying |
| alert | 1.0 | no | |
| wolf_bite | 0.8 | no | hits [0.333, 0.433]; lunges 0.3 m forward and returns |
| wolf_pounce | 1.4 | no | hits [0.767, 0.9] (landing); leap peaks at 0.3 m, lands 0.55 m forward, returns to the origin by the end |
| wolf_howl | 2.5 | no | |
| devour | 2.0 | yes | head down, tearing |

- Gait: the feet are IK-planted and move at exactly `ground_speed` during stance, so there is no foot slide by construction.
- Evidence: `dire_wolf_rest_iso.png`, `dire_wolf_gaits.png`, `dire_wolf_attacks.png`, `dire_wolf_reactions_deaths.png`
- Known issues:
  - The mesh is lofted tubes with fur shards, so it has a low-poly, faceted look.
  - The legs are fairly thin.
  - The bite and pounce lunges move the body off the origin mid-clip (see the table), and the game should expect that.
  - No hit_front/left/right variants: only the contract's clip list was made.
