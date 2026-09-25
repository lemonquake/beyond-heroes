# Contract: environment kit + tileable textures (bh-001 / C4)

Build with Blender 5.2.1 Python (`"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --python <script>`) and
Python 3.12 (numpy, PIL, scipy available). Scripts in `tools/blender/environment/` and `tools/textures/`; outputs in
`game/assets/environment/` (GLB) and `game/assets/textures/` (PNG). Everything must regenerate from scripts deterministically
(fixed seeds). Do not touch other folders and do NOT run Godot on the main project `game/` (a throwaway Godot project in your
scratch dir is fine for checks).

**Read `work/lemondev/bh-001/art_direction.md` first** — it describes the user's reference images (flooded cistern cutaway with
warm torch vs teal water, crypt room-and-corridor plan, dense lived-in battlemap). Match that direction: cut-stone blocks with lighter
quoin stones on pillar/arch edges, damp streaks, moss drips, worn flagstones, rotting planks, visible wall thickness with capstones.
Art direction: dark, atmospheric high fantasy (mood of Diablo II; original designs, no copied locations). Weathered stone,
moss, rotting wood, iron, candlelight. Every prop needs a purposeful silhouette and secondary detail (chipped edges, cracks,
bevels, plank separation, rivets, carved trim). Viewed from an elevated isometric camera ~14 m away. Keep triangle counts
game-friendly (small props 200–2k tris, architecture 1k–8k, trees 2k–6k with alpha-card or mesh leaves).

## Conventions

- Meters, Blender Z-up, exported glTF binary with `export_yup=True`, transforms applied, origin at the bottom center (on the ground)
  unless noted. Modular architecture snaps to a **2 m grid** (walls 4 m long, 4 m tall, 0.8 m thick).
- UVs required on everything (box/cube projection is fine for stone; textures are tileable at ~2 m per tile). World-space triplanar
  may be used in Godot, but UVs must still be sane.
- **Material names are a contract** (Godot replaces them with its own shaders using the textures below):
  `BH_Stone`, `BH_StoneDark`, `BH_Brick`, `BH_Cobble`, `BH_Wood`, `BH_WoodDark`, `BH_Bark`, `BH_Leaves`, `BH_Grass`, `BH_Moss`,
  `BH_Metal`, `BH_Iron`, `BH_Gold`, `BH_Cloth`, `BH_ClothRed`, `BH_Bone`, `BH_Candle`, `BH_Flame` (emissive), `BH_Rune` (emissive
  cyan/violet), `BH_Corruption` (emissive purple), `BH_Water`, `BH_Glass`, `BH_Thatch`, `BH_Dirt`. Set plausible Blender colors too.
- Also write collision helpers: for each GLB add a simplified convex/box mesh child named `<name>-colonly` (Godot import hint) for
  architecture and large props. Small clutter (skulls, candles, grass) gets no collision.

## Assets (`game/assets/environment/<name>.glb`)

Architecture: `wall_straight`, `wall_broken`, `wall_corner`, `wall_doorway`, `wall_window`, `pillar`, `pillar_broken`,
`arch`, `stairs` (2 m rise over 4 m), `floor_tile_4m` (catacomb floor slab, 4x4 m, 0.3 m thick), `ceiling_beam`,
`gate_iron`, `bridge_stone` (12 m span), `bridge_wood` (8 m), `ruin_tower` (collapsed watchtower landmark ~12 m),
`temple_facade` (landmark ~14 m wide), `house_intact`, `house_destroyed`, `market_stall`, `well`, `fountain`,
`palisade_fence`, `wood_fence`, `cliff_a`, `cliff_b` (6–10 m rock faces), `rock_large`, `rock_medium`, `rock_small`,
`rubble_pile`, `statue_knight` (3 m), `statue_collapsed`, `altar`, `sarcophagus`, `gravestone_a`, `gravestone_b`,
`teleporter_platform` (circular runic dais ~4 m diameter with 3 standing stones, rune grooves on `BH_Rune`),
`teleporter_destroyed` (broken version), `obelisk_corrupted`.
Nature: `tree_dead_a`, `tree_dead_b`, `tree_pine`, `tree_oak_twisted`, `bush_a`, `bush_b`, `grass_clump`, `fern`,
`mushrooms`, `roots`, `log_fallen`, `stump`.
Props / storytelling: `wagon_broken`, `crate`, `barrel`, `urn`, `chest`, `campfire` (logs + stones, no flame), `tent_old`,
`weapon_rack`, `weapons_discarded`, `skull_pile`, `bones_scatter`, `candles_cluster`, `cobweb` (alpha card), `banner_torn`,
`torch_sconce` (wall-mounted, flame socket empty), `brazier`, `lamp_post`, `anvil`, `bookshelf`, `table`, `chair`, `cart_hay`,
`chains_hanging`, `spikes_trap_plate`.
From the references: `ladder` (3 m), `scaffold_platform` (2x2 m wooden landing on posts, 3 m high), `boat_rowing`, `winch`
(wooden crane/winch over a shaft), `bed`, `bedroll`, `coffin` (plain wooden; also usable floating), `dock_planks` (4 m jetty
section on posts), `rug` (flat mesh, `BH_ClothRed`), `wall_stone_capped` (4 m wall with lighter capstone course on top, for
top-down readability), `pillar_quoin` (pillar with alternating lighter quoin blocks), `arch_quoin`, `ritual_circle` (floor inlay
disk 6 m with rune grooves `BH_Rune`), `rubble_spill` (collapsed wall debris fan).
Breakables: for `crate`, `barrel`, `urn`, `statue_small` produce `<name>.glb` (intact) and `<name>_fragments.glb` where each
fragment is a separate mesh object named `frag_00`, `frag_01`, … (6–14 fragments, each a closed mesh, positioned in place so they
reassemble the intact prop).

## Tileable textures (`game/assets/textures/<set>_albedo.png`, `_normal.png` (OpenGL +Y), `_rough.png`)

1024x1024, seamless (verify by tiling 2x2 in a check image), sRGB albedo, linear normal/roughness. Sets:
`stone_blocks`, `stone_floor`, `cobblestone`, `brick`, `dirt`, `mud`, `grass`, `forest_floor` (leaves+twigs), `rock_cliff`,
`wood_planks`, `bark`, `moss`, `metal_iron`, `cloth`, `thatch`, `sand_path`. Plus `leaves_atlas.png` (RGBA alpha-cut leaf clusters,
1024) and `grass_blades.png` (RGBA). Generate with procedural noise / Voronoi / SDF shapes (numpy/scipy) or Blender bakes.
Colors should be muted and cohesive; avoid pure saturated colors.

## Evidence to return

- `work/lemondev/bh-001/evidence/environment/`: contact sheet renders of all assets (EEVEE, consistent 3/4 camera & light rig);
  a composed "vignette" render (ruined forest corner + crypt corner) showing the kit together; 2x2 tiling checks of each texture.
- `validation.txt`: every GLB re-imported → object/material names, triangle counts, bounds; asserts material names are in the list.
- README in `tools/blender/environment/` with regeneration commands.
