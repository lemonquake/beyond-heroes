# tunnel_maw (Tunnel Maw, stem `maw_`)

- Script: `tools/blender/creatures/build_tunnel_maw.py`, using the shared kit `tools/blender/creatures/kit_c13.py`.
- GLB: `game/assets/characters/tunnel_maw.glb` (1.4 MB). The `.glb.import` is copied from rootback_boar with the uid line removed and the paths fixed.
- Triangles: 13,808. 20 bones:
  - root; mound (a static ring around the base that is scaled flat when it burrows)
  - base (a ground pivot whose translation sinks the whole worm), with seg1-seg7 (0.45 m each) and head (mouth rim)
  - petal1-4 (jaw petals); feeler1-5 on seg7
- Size: the visible body rises 3.1 m to the mouth rim, 3.3 m to the lip and 3.97 m to the tips of the rest-open petals. The body is about 1.1 m across over the armour bands. The mound is 3.5 m across and 0.46 m high. The flesh tube continues 0.75 m below ground, so tilts never show its end.
- The origin is on the ground at the centre of the mound, and the model faces -Y (Godot +Z).
- Clips (17, in place, 30 fps). Loop flags are the ones the game applies:
  - idle 3.0 s (loop, slow travelling sway with the top looking down at the ground in front), idle_look 2.5 s
  - walk 1.333 s (loop, ground_speed 1.5), run 0.8 s (loop, 4.0), run_combat 0.8 s (loop, 4.0). These are low sways only; the game hides the worm while it travels.
  - hit_light 0.4 s, hit_heavy 0.6 s, stagger_small 0.8 s, knockback 0.9 s, alert 1.0 s
  - death 1.8 s (topples to its right and lies across the mound and the ground; the head ends about 2.4 m out at y≈0.45)
  - death_back 1.8 s (the same fall, but backward)
  - `maw_bite` 1.0 s, hits [0.467, 0.567]: rears back, petals open wide, then lunges forward and down and the petals snap shut. The mouth reaches about 2.1 m in front at 1.2 m height.
  - `maw_slam` 1.4 s, hits [0.667, 0.767]: rears far back, then crashes the top half down onto the ground. The mouth rim lands about 2.3 m in front at about 0.6 m, with the petals touching the ground. The mound heaves.
  - `maw_spit` 0.9 s, hits [0.433, 0.5] (release): contracts with the mouth shut, then thrusts forward-up and the petals flare. Spawn the glob at the mouth, about 3 m up and 0.5-0.8 m forward.
  - `maw_burrow` 1.0 s, non-loop: the petals shut and the worm sinks straight down. On the last frame every bone is at or below y = -0.11 (base dropped 4.05 m). The mound flattens to 28 % height and 88 % width, leaving a dark hole. It ends hidden, so hold the last frame or hide the node.
  - `maw_emerge` 0.8 s: the reverse. It starts hidden with the mound flat, bursts up with the mound heaving, overshoots about 0.25 m with the petals flaring, and settles into the idle pose.
- creature_meta.json: merged `animations.maw_bite/maw_slam/maw_spit/maw_burrow/maw_emerge` and `models.tunnel_maw` (every clip, tris, bones). The file was re-read before writing, and a check after the write confirmed every other key is unchanged.
- Palette (`<name>__tunnel_maw`):
  - BH_Horn: sandy-ochre armour bands and outer petals
  - BH_Wood: dark band lips, dorsal studs, petal ridges
  - BH_Flesh: dark red-brown flesh between the bands and the lip ring
  - BH_Ichor: dark red gullet and inner petals
  - BH_Bone: teeth, three concentric rows of 16/13/10 down the gullet, plus hooked teeth on each petal
  - BH_Emissive: small red glow deep in the throat
  - BH_Skin: feelers
  - BH_Leather: broken earth
  - BH_Stone: rocks
  - BH_Shadow: the hole

## What makes it distinct
It is the only enemy that is a vertical column. From the high camera you look straight into a round, tooth-ringed red maw with four ochre-and-crimson petals, sitting on segmented sandy armour. The broken-earth mound and its rocks sit at the base. Its silhouette and sandy/crimson palette differ from every other creature.

## Evidence
- `tunnel_maw_rest_iso.png`: front, side, the mouth from above, the mound close-up, and game-camera crops at 16 m and 24 m.
- `tunnel_maw_clips.png`: idle, maw_bite, maw_slam, maw_spit, maw_burrow, maw_emerge and death at 5 normalized times.
- `godot_check.txt`: 17 clips import and none is missing. The lengths match the meta, and the loop flags match what the game applies.

## Build log
```
[tunnel_maw] mesh 13808 tris, 17 clips, 20 bones
[tunnel_maw] numpy FK vs Blender pose: worst 0.00 mm at ('death_back', 54, 'petal4')
[tunnel_maw] meta merged ['maw_bite', 'maw_burrow', 'maw_emerge', 'maw_slam', 'maw_spit'] + models.tunnel_maw -> ...creature_meta.json (verified: True)
[tunnel_maw] -> ...tunnel_maw.glb (1.4 MB)
[tunnel_maw] 17 animations in the GLB; length mismatches: []
```

## Known limitations
- The armour bands are rigid per segment, so in hard bends (slam, death) neighbouring bands overlap on the inside of the curve.
- In the deaths and the slam, the fallen body passes through the mound's rim geometry.
- While burrowed, the mound is still visible as a flattened ring with a dark hole. If it should vanish completely, hide the model after `maw_burrow`.
- The worm stays rooted at the origin in every clip. For bites and slams, the reach comes from bending, not from moving the root: roughly 2.1-2.3 m.
