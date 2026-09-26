# Salmonan island design package

Design review, 27 September 2026. This package proposes a larger playable Salmonan around the existing Malasugue Town. It contains design artwork, a functional atlas prototype, source audit, measured runtime playtest evidence and implementation instructions. The proposed island is **not implemented in the game**.

Start with [the island atlas](images/salmonan-island.png), [the junction environment design](images/old-mill-crossroads.png), and [the M-map interface design](images/map-directions-ui.png). Open [atlas-preview.html](atlas-preview.html) to select destinations and try route choices. The preview is separate from the game. The generated paintings establish visual direction; the graph and specifications define functional behavior.

## Design decision

Make Salmonan a connected island with Malasugue on its west coast, a lake in its interior, forest and mountains to the north, working farmland to the south and drowned ruins to the east. Roads form reconverging loops, and six discoverable shrines reduce repeat travel. The existing Catacombs–Temple–Warden story remains an ordered dungeon journey within this larger geography.

Keep the inhabited, dark-fantasy character of the current build: cut stone, timber, moss, warm lanterns, cool mist and pale cyan Aether. Improve ground readability and geographic structure. Every road needs a purpose, destination and actual traversable counterpart.

## Files

- [Agent directives](AGENT-DIRECTIVES.md): prioritized tasks, ownership, acceptance criteria and handoff prompts.
- [World and playability specification](WORLD-DESIGN.md): location roles, early choices, travel rules, scale and pacing.
- [Architecture audit](architecture-audit.md): verified existing source locations and implementation constraints.
- [Runtime playtest](review-playtest.md): real Player movement, M input, combat results, native screenshots and limitations.
- [Graph](island-graph.json) and [interactive preview](atlas-preview.html): deterministic schematic route model. This is a proposed graph, not current world data.
- [Generation prompts](IMAGE-PROMPTS.md): exact prompts and source references, using the built-in image tool.

## Evidence and limits

Desktop window capture failed twice. We used instrumented runtime playtesting in the actual Godot build: real Player input/physics, a physical M key event, engine-rendered screenshots and the existing combat bot. Town movement covered 7.07 m; forest movement covered 15.69 m. The 30-second forest combat run recorded five kills, zero deaths and 433 XP. This is not a manual desktop playthrough of every map or a full QA certification.

The current M screen has a hardcoded five-node chain. The forest has a primary west/east road and one main bridge, though some dungeon interiors already contain loops. Preserve those good interior layouts. See the report for raw evidence and existing runtime errors.

All new place names, geography, level bands, encounter ideas and dimensions here are provisional proposals. Existing canon in `docs/LORE.md` wins. Before implementation, enter accepted additions there as provisional and resolve the change to the barred South Gate explicitly.

## Artwork interpretation

The island painting uses exaggerated landmark size for readability. Do not derive metres, road widths, shrine state, collisions or exact world coordinates from painted pixels. The original generation draft (`salmonan-island-v1.png`) contains rejected decorative copy and an unsupported scale bar; use `salmonan-island.png` as the selected atlas concept. Dynamic names, routes, positions, distances and fog must be native UI layers in the shipped game. The clean atlas base and production layers remain implementation deliverables.

The crossroads keyframe shows a local waystone to make the destination visible. Treat this as a directional landmark, not a seventh network shrine unless the graph is explicitly expanded. The image's hill stair also needs a traversable companion-friendly ramp validated in-engine. The painting is an art target, not proof of navigation or performance.
