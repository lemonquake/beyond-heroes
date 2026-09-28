# gloam_ooze (Gloam Ooze, stem `ooze_`)

- Script: `tools/blender/creatures/build_gloam_ooze.py`. It uses the shared bh-013 kit `tools/blender/creatures/kit_c13.py`: a generic rig, the channel DSL, a numpy FK that is checked against Blender after baking, GLB export, the meta merge and the evidence renders. No existing script was changed.
- GLB: `game/assets/characters/gloam_ooze.glb` (0.9 MB). The `.glb.import` is copied from rootback_boar with the uid line removed and the paths fixed.
- Triangles: 11,908. 15 bones: root, body, spine1, spine2, crown, wobF/wobB/wobL/wobR (radial wobble bones), skull, jaw, podL1/podL2, podR1/podR2. The body, spine and wobble bones animate scale, and the wobble bones also animate translation. Godot imports scale tracks without errors.
- Size: the body is 1.13 m tall (1.35 m to the top of the crown bubbles) and 1.72 m wide. Pseudopod tips reach 1.0 m forward. The origin is on the ground at the centre, and the model faces -Y (Godot +Z).
- Clips (15, in place, 30 fps). Loop flags are the ones the game applies:
  - idle 2.0 s (loop), idle_look 2.5 s, walk 1.333 s (loop, ground_speed 1.0), run 0.8 s (loop, 2.8), run_combat 0.8 s (loop, 2.8)
  - hit_light 0.4 s, hit_heavy 0.667 s, stagger_small 0.8 s, knockback 0.9 s, death 1.5 s, death_back 1.5 s, alert 1.0 s
  - `ooze_slam` 1.067 s, hits [0.5, 0.633]: rears up tall with the pods high, then slams down forward. It squashes flat at about 0.55 s and jiggles.
  - `ooze_spit` 0.9 s, hits [0.433, 0.5]: contracts, then lurches forward. The skull's jaw gapes at about 0.45 s, so launch the projectile from the skull (front, about 0.55 m up).
  - `ooze_split` 0.9 s, hits [0.8, 0.9]: bulges wide, then pinches along the middle. The front and back pull in, the left and right halves hump up and spread, and the top sinks. It ends in the pinched pose, so spawn the two copies at about 0.9 s.
- creature_meta.json: merged `animations.ooze_slam/ooze_spit/ooze_split` and `models.gloam_ooze` (every clip, tris, bones), in the same way as rootback_boar. The file was re-read right before writing, and a check after the write confirmed every other key is unchanged.
- Palette (`<name>__gloam_ooze`):
  - BH_Ichor: dark teal slime (0.018, 0.105, 0.115), glossy, with a faint teal self-glow
  - BH_Flesh: lighter teal crown lumps
  - BH_Aether: violet emissive rim
  - BH_Emissive: cyan bubbles, pod-tip nubs and skull eye glints
  - BH_Bone: ivory skull, ribs and femur
  - BH_Horn: muted teal-ivory "submerged" bones
  - BH_Shadow: skull sockets
- Translucency trick: there is no real transparency. An inverted-hull shell (the blob, pods and crown bubbles pushed out 3-4 cm with flipped faces, material BH_Aether) is drawn only where it sticks out past the silhouette, so it shows as a glowing violet outline. Bones that press out of the skin are ivory. Bones meant to look sunk inside are flat, muted teal-ivory shapes lying flush on the skin.

## What makes it distinct
A squat, glossy dark-teal dome with a violet glowing outline and a lumpy crown of dark bubbles capped by cyan glints. It has two fat stubby pseudopods, a grinning skull pushing out of its front, ribs arching out of one flank and a femur jutting from its back. It has no legs and moves by squashing and sliding. At the gameplay camera it reads as a round teal blob with a bright rim, ivory bones and cyan dots. It stays readable at scale 0.65 and 0.45 (see the last three game-camera crops).

## Evidence
- `gloam_ooze_rest_iso.png`: 3 rest views, a skull close-up, and game-camera crops at 16 m and 24 m at scales 1.0, 0.65 and 0.45.
- `gloam_ooze_clips.png`: ooze_slam, ooze_spit, ooze_split, walk, death and idle at 5 normalized times.
- `godot_check.txt` (made by `tools/godot_check_creatures.py` on a throwaway project): 15 clips import and none is missing. The lengths match the meta, and the loop flags match what the game applies.

## Build log
```
[gloam_ooze] mesh 11908 tris, 15 clips, 15 bones
[gloam_ooze] numpy FK vs Blender pose: worst 0.00 mm at ('ooze_slam', 16, 'podL2')
[gloam_ooze] meta merged ['ooze_slam', 'ooze_spit', 'ooze_split'] + models.gloam_ooze -> ...creature_meta.json (verified: True)
[gloam_ooze] -> ...gloam_ooze.glb (0.9 MB)
[gloam_ooze] 15 animations in the GLB; length mismatches: []
```

## Known limitations
- The rim relies on back-face culling, which is the default cull mode of the materials the game builds in `MaterialLibrary._palette_mat`. If a double-sided material were ever forced onto the model, the shell would cover the body in violet.
- Squash and stretch uses non-uniform bone scale. In the extreme poses (the slam rear-up, the death puddle, the split) the crown bubbles and their rim rings stretch or flatten with the body, and the rim rings show as violet circles on the flattened puddle.
- `ooze_split` does not separate the mesh. It is a peanut-shaped pinch, and the game does the actual split by spawning copies.
- idle_look is looped by the game, because the humanoid anim_meta has loop=true for it. The clip starts and ends at rest, so the loop is seamless.
