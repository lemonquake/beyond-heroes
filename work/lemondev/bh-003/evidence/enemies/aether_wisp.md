# aether_wisp (Builder C)

- Source: `tools/blender/creatures/build_wisp.py` (`python3 build_wisp.py [--preview DIR]`)
- GLB: `game/assets/characters/aether_wisp.glb`: static, no armature, no animations
- Nodes (separate meshes, origin = creature centre):
  - `core`: faceted Aether crystal cluster, radius ~0.25 m, `BH_Aether__aether_wisp`, 346 tris
  - `ring_1`: 6 shards, radius 0.45 m, 144 tris
  - `ring_2`: 7 shards, radius 0.58 m, 168 tris
  - `ring_3`: 5 shards, radius 0.70 m, 120 tris
  - The ring shards use `BH_Stone__aether_wisp` (pale blue-grey crystal with a faint glow).
  - `ribbons`: 3 hanging light ribbons, `BH_Emissive__aether_wisp`, 420 tris
- Triangles total: **1,198**
- Bounds: about 1.6 m wide and 1.5 m tall (z -0.80 to +0.71; the ribbons hang to -0.8 m and the tilted rings add height). The core and rings alone span about ±0.5 m vertically.
- **Spin axis:** each ring's shards lie in its node's local XY plane (Blender), which is the XZ plane in Godot. The tilt is stored in the node's own rotation (ring_1: 18° about X; ring_2: -10° about X, 30° about Y; ring_3: 34° about X, -24° about Y). Spin a ring about its **local +Y (Godot)** to rotate it in its own plane.
- Evidence: `aether_wisp_rest.png` (3 views + iso). Workbench cannot show emission, so the glow is not in the picture.
- Known issues: none known. The model has no animation of its own; the game animates the float, the ring spin and the ribbon sway.
