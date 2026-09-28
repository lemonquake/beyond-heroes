# bh-012 component K: dungeon environment kit (Builder F)

Source: `tools/blender/environment/assets_dungeon.py`, registered through one import line in `build_assets.py`.
Build: `blender -b --factory-startup --python tools/blender/environment/build_assets.py -- deeps warren ember rime orrery dungeon`.
Previews: `contact_<theme>.png`. Each asset has a beauty tile and a collision tile (orange = `-colonly`, magenta = sockets). The
renders are EEVEE via `scratch/env/render_env.py`, and glow is exaggerated compared with the game.
Godot 4.7.2 import check (scratch project `scratch/env/godot`): 27/27 load, 0 failures, and node trees match the list below.

Conventions: metres, front = -Y (Godot +Z), origin at the bottom centre unless noted. Every collision is one `-colonly` child.
New material names are registered in the module with export preview colours only: BH_Lava, BH_Ice, BH_Spore,
BH_Starglass, BH_Brass, BH_Coral, BH_Basalt, BH_Marble, BH_MushroomCap, BH_Fungus, BH_Snow, BH_Kelp.

| Asset | Size x/y/z (m) | Tris | Collision | Sockets / nodes | Materials (main) |
|---|---|---|---|---|---|
| coral_cluster | 1.1 x 1.0 x 1.05 | 3.4k | no | - | Coral, Stone |
| kelp_strands | 0.95 x 0.6 x 3.0 | 1.7k | no | - | Kelp, StoneDark |
| anchor_giant | 3.0 x 2.2 x 3.8 (crown sunk 0.3 below z=0) | 7.6k | shank + crown + mound | - | Iron, Bone (barnacles), Kelp, Stone |
| sunken_bell | 2.3 x 2.3 x 2.2 | 6.4k | tipped cylinder | - | Brass, Bone, Kelp, Iron, Stone |
| barnacle_pillar | 1.7 x 1.6 x 4.0 | 11.3k | box 1.3 x 1.3 x 4 (= pillar_quoin) | - | Stone/StoneDark, Bone, Kelp, Moss |
| mushroom_giant | 6.1 x 6.0 x 6.4 | 2.9k | stalk only (r 0.8, 4.6 m) | light (0.3, 0.1, 4.0) under the cap | Fungus, MushroomCap, Spore (gills) |
| mushroom_glow_cluster | 0.9 x 0.8 x 0.75 | 1.3k | no | - | MushroomCap, Spore, Fungus, Moss |
| fungus_shelf | 1.3 x 0.4 x 1.0, back on y=0, extends to -Y | 0.8k | no | - | MushroomCap, Spore (undersides), Fungus |
| root_arch | 5.8 x 2.0 x 4.8, legs at x=+-1.85, clear span ~3 m, clearance >= 3.2 m | 3.5k | legs only (2 boxes) | - | Bark, Moss, MushroomCap, Spore |
| spore_pod | 1.7 x 1.7 x 1.3 | 3.1k | cylinder | - | Fungus, Spore (veins) |
| forge_furnace | 3.7 x 3.6 x 4.0 (body 3.5 x 2.4, trough in front) | 9.2k | body + chimney + trough | flame (0, -0.65, 0.8) in mouth, light (0, -2.1, 1.3) | Basalt, StoneDark, Lava, Iron |
| lava_crucible | 1.5 x 1.5 x 1.5 | 3.2k | cylinder | light (0, 0, 1.7) | Iron, Lava, StoneDark, Basalt |
| ore_cart | 2.3 x 1.3 x 1.4 (incl. rails) | 5.1k | box | - | WoodDark, Iron, Basalt, Stone, Lava, Gold |
| basalt_column | 4.0 x 3.3 x 4.0 | 1.5k | hex prism | - | Basalt, Lava (seams) |
| chain_hoist | 4.0 x 0.5 x 4.05, origin at the TOP (z 0 to -4) | 4.9k | no | - | WoodDark, Iron |
| ice_crystal_large | 2.3 x 2.3 x 3.2 | 0.7k | cylinder | - | Ice, Snow, Stone |
| ice_crystal_small | 0.6 x 0.5 x 0.85 | 0.3k | no | - | Ice, Snow |
| icicles_hanging | 4.1 x 0.4 x 1.5, origin at the TOP back edge (y=0 wall face, hangs toward -Y) | 6.4k | no | - | Ice, Snow |
| frozen_coffin | 2.2 x 1.1 x 0.9 | 2.5k | box | - | Stone, Ice, Iron/Cloth/Metal (figure), Snow |
| snow_drift | 3.0 x 2.1 x 0.55 | 0.6k | no | - | Snow, Stone |
| armillary_sphere | 3.9 x 3.9 x 4.9, sphere centre z=3.2 | 1.3k (+rings) | pedestal only | child meshes `ring_a` (R1.7), `ring_b` (R1.42), `ring_c` (R1.15), `core`; origins at the centre; socket light at the centre | Marble, Brass, Starglass |
| crystal_pylon | 1.5 x 1.6 x 3.0 | 0.8k | cylinder | light (0, 0, 1.8) | Starglass, Brass, Marble |
| star_lens_disc | 6.0 dia x 0.04 | 3.9k | no | - | StoneDark, Brass, Starglass |
| brass_telescope | 2.2 x 1.8 x 3.2 | 1.1k | tripod cylinder | - | Brass, WoodDark, Starglass (lens) |
| floating_rock | 1.8 x 1.6 x 1.8 (bottom = crystal tips) | 1.0k | no | center (0, 0, 1.2) | Stone, Moss, Marble, Starglass |
| stairs_wood | 2.4 wide (2.6 incl. rails) x 4 run x 2 rise | 1.9k | same as `stairs`: sloped ramp box + two side boxes | - | Wood, WoodDark, Iron |
| gallery_railing | 4.0 x 0.4 x 1.06 | 2.5k | box 4 x 0.4 x 1.06 | - | Stone |

Armillary rings: each ring lies in its node's local XY plane in Blender, so it spins about its own local Y in Godot.
Node rotations are ring_a (90,0,0), ring_b (90,0,60) and ring_c (23,0,0) in Blender XYZ degrees.

Textures (`game/assets/textures/<set>_{albedo,normal,rough}.png`, 1024 px, tileable): `basalt`, `rime_ice`, `marble` and
`fungal_stone`. The sheet is `textures/textures_overview.png`, with 2x2 tiling checks and `seam_report.txt` next to it. The
generator is `tools/textures/gen_textures.py` (4 functions added to `SETS`; existing sets are unchanged).

## Notes
- frozen_coffin: in-game BH_Ice may be opaque, so the ice only covers the legs and head end, with crystals on the rim. The dark
  armoured figure is visible between the ice chunks.
- chain_hoist and icicles_hanging have all their geometry below z=0. The previews lift them onto the ground for display only.
- Collision is one concave `-colonly` mesh per asset, the same as the rest of the kit.

## Build log (final run)
```
coral_cluster 3412 | kelp_strands 1672 | anchor_giant 7642 | sunken_bell 6416 | barnacle_pillar 11296
mushroom_giant 2920 | mushroom_glow_cluster 1260 | fungus_shelf 820 | root_arch 3540 | spore_pod 3074
forge_furnace 9220 | lava_crucible 3158 | ore_cart 5132 | basalt_column 1456 | chain_hoist 4920
ice_crystal_large 714 | ice_crystal_small 284 | icicles_hanging 6392 | frozen_coffin 2514 | snow_drift 560
armillary_sphere 1276 | crystal_pylon 840 | star_lens_disc 3920 | brass_telescope 1112 | floating_rock 1004
stairs_wood 1914 | gallery_railing 2460          (tris, main mesh; full lines in tools/blender/environment/build_log.txt)
```
