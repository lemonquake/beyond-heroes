# Art direction (derived from the user's reference images, supplied in chat 2026-09-26)

The images were shared in the conversation only; they are not on disk. To use them as blind-review benchmark evidence,
save them to `A:\Python\beyond-heroes\references\` (the benchmark gate stays UNVERIFIED until then).

## Reference 1 — isometric cutaway of a flooded cistern/keep
- **Vertical layering:** rooms and walkways stacked over a deep flooded hall; stairs, ladders, wooden scaffolding and landings climb
  the walls; arches and buttress pillars stand in the water. Maps should use elevation (raised walkways, sunken floors,
  stairs, balconies over pits/water), not flat floors.
- **Warm/cool lighting contrast:** amber torch pools (sconces every few meters on walls, warm light spilling on stone) against
  luminous teal/cyan water that lights the lower walls from below. Dark navy/violet shadow tones, never pure black.
- **Materials:** cut-stone blocks with lighter quoins on pillar/arch edges, damp streaks and moss drips on walls, worn flagstone
  floors, rotting planks. Small storytelling props (barrels, beds, tables, a sarcophagus, a winch over a shaft, a moored boat).
- **Readability:** thick dark outlines/silhouettes; clear separation of floor (lit) vs walls (shaded).

## Reference 2 — top-down crypt floor plan
- **Room-and-corridor structure:** distinct purposeful rooms joined by narrow 2-tile corridors and short stair runs; not a maze of
  identical halls. Rooms seen: ritual circle chamber with pillars and sarcophagi, sarcophagus rows hall, flooded chamber with
  floating coffins and rubble, dining/meeting room with broken tables, barracks with beds and bedrolls, coffin niches corridor,
  storage with barrels/crates, a treasure alcove behind stairs.
- Walls have visible thickness with lighter capstones; floors vary per room (flagstone, cracked tile, cobble, dirt).
- Clutter hugs walls and corners; rubble spills from broken wall sections; cobwebs, bones, candles.

## Reference 3 — top-down modern house battlemap (used for composition and density only, not its setting)
- **Density and lived-in detail:** every room furnished, a floor material per room, rugs and furniture grouped logically.
- **Soft ambient-occlusion drop shadows** under walls and trees; trees/bushes cluster at edges to frame the playable lot.
- **Exterior framing:** hedges, flowerbeds, paths of paving stones, a boundary (fence/road) defining the space.

## Rules for Beyond Heroes maps
1. Each map is a composition of named, purposeful spaces with a landmark visible from the entrance.
2. Use elevation in every map (stairs, ledges, bridges, pits, water levels).
3. Light with warm local sources (torches, braziers, candles) against a cool ambient (teal water, moonlit fog, violet corruption).
4. Clutter along walls and in corners, open combat floor in the middle of rooms; corridors stay readable.
5. Dark silhouettes and contact shadows (SSAO + baked-style AO) so props sit in the scene.
6. Foliage and rocks frame outdoor spaces; the playable area is bounded by cliffs/walls/dense trees, not invisible walls on flat grass.
