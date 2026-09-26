# Salmonan: world and playability specification

Status: proposed design, not shipped gameplay. Read `docs/LORE.md` first. New names and activities are provisional. The atlas is a visual target; the graph is a functional schematic, not a final geographic survey.

## What the player should experience

Malasugue feels like a town on an island: food arrives from farms, fish from the harbor, timber from the forest, and pilgrims once followed the road to the temple. Follow those movements when placing roads, carts, drainage, bridges and ruins. The lake feeds the millstream and marsh. High ground supplies distant landmarks. Aether shrines were built at places people traveled through, not dropped at arbitrary level exits.

After the short town introduction, the player can choose a coast errand, a farmland encounter or the existing forest investigation. These are independent early journeys with different scenery and rewards. Rejoining roads lets the player return by a different route. The main story still leads through the Catacombs to Morthar; optional exploration is not another mandatory checklist.

## Initial size and density

Prototype an island envelope approximately **1,200 × 1,000 metres**, split into bounded connected districts. This is a tuning proposal, not a claim of implemented or fully walkable area. Water and mountains occupy much of the envelope. The current town bounds are 84 × 84 m and forest bounds 144 × 96 m. Do not inflate all existing dimensions uniformly.

At the current 5.0–5.2 m/s base speeds, a 1,200 m direct walk takes approximately four minutes before detours or combat. Actual route lengths must be summed from authored walkable polylines. Target nearby forks/landmarks about 100–200 m apart (20–40 seconds), local circuit walks about 600–1,200 m (2–4 minutes), and distinct first-visit outings about 8–15 minutes including encounters. Test these targets with fresh characters before committing to total island scale.

Start with a 350–450 m Malasugue-adjacent district containing the coast/field/mill loop. Only expand once that loop is enjoyable, readable and reachable. Six awakened shrines later shorten repeat journeys. Walking remains worthwhile through side activities and alternative approaches; do not require players to repeatedly clear identical road packs.

## Places and their play purpose

| Place | Role and identity | Choices and activities | First balance target |
|---|---|---|---|
| Malasugue Town | Existing west-coast cliff town; fountain, north Sanctuary Terrace, Lantern House west, Swordfin Hall east | Guild/services, quest selection, harbor approach, three signed outward destinations | Safe town; preserve `sanctuary` ID |
| Tideglass Cove* | Fishing beach beneath western cliffs; piers, net racks, tide marks | Recover a missing shipment; coastal cave side encounter; climb back by farm road | Levels 1–3; shrine |
| Lantern Fields* | Working terraces, mill supply road and stone farms | Goblins stealing supplies; open-field combat or longer maintained road; returns through mill | Levels 1–4 |
| Old Mill Crossroads* | Watermill and three-way junction southwest of lake | Decision point, signpost, refill/rest stop if authored; roads visibly diverge to forest, chapel and fields | Low-danger road margin; no mandatory gate |
| Ruined Forest | Existing burnt village and graveyard | Reuse encounters, add second ravine crossing/hillside loop; bridge and forest trail rejoin | Existing levels 1–5; shrine |
| Watcher's Rise* | Northern watchtower with a view of lake and temple | Hill climb, optional orc/ogre encounter off main road, unlock a ridge shortcut | Levels 4–7; shrine |
| Stillwater Lake* | Central geographic anchor; source of millstream | Shore trails, flooded foundations and a later optional island-shrine excursion | Shore first; island access not in milestone one |
| Drowned Chapel | Surface entrance to existing Catacombs; wet stone, broken belfry, causeway | Reach by lake road or southern marsh; discover shrine; choose dungeon descent separately | Existing dungeon levels 4–8; surface shrine |
| Reedwater Marsh* | Eastern wetlands; boardwalks, old lock gates and reeds | Controlled alternate path to chapel, flooded combat pockets, optional lock-gate shortcut | Levels 3–6; shrine |
| Forgotten Temple | Existing northern/eastern mountain temple | Reach exterior from ridge or chapel switchbacks; story seal controls deeper access | Existing levels 7–10 |
| Ancient Catacombs | Underground layer beneath chapel | Preserve useful room loop and flooded cistern; existing ritual flag opens the story route | Existing levels 4–8 |
| Hollow Throne | Separate encounter behind temple threshold | Existing Morthar sequence and return rule; no apparent surface-road shortcut to boss | Existing level 10; existing seal/warden flags |

*New provisional place names. Drowned Chapel already exists descriptively in the slice; formal POI placement is proposed. No new major island is invented. Other-island travel is future scope, not a working ferry link.

## Required topology

1. **Coast circuit:** Malasugue → Tideglass Cove → Lantern Fields → Old Mill → Malasugue. Roads have gradual elevation changes between harbor and plateau, with visible switchbacks.
2. **Forest circuit:** Old Mill → forest southern bridge approach → burnt village → northern hillside crossing → Old Mill. The second crossing must be traversable; a painted dotted line does not qualify.
3. **Lake circuit:** Old Mill → western lake shore / Watcher's Rise → temple exterior → Drowned Chapel → eastern/southern shore → Old Mill. This longer circuit can include higher-risk optional sections without gating the short southern routes.
4. **Marsh alternative:** Chapel → Reedwater Marsh → Lantern Fields → Old Mill. Boardwalk widths and passing bays support companions; shortcuts never imply walking over water.

The functional graph supplies stable road IDs and actual connections. All major districts have two approaches where geography permits. Dead ends are allowed for a short vista, chest, cave or story scene with a deliberate payoff. Do not add loops consisting only of two identical corridors.

## First fifteen minutes: intended sequence to test

- 0–2 minutes: recognize fountain, guild halls, forge and terrace. Choose an initial errand; M shows town services, charted public roads and named directions. Do not reveal every hidden shrine/chest.
- 2–5 minutes: open or explain the town road access with Captain Hald. The three-year barred South Gate needs a deliberate story update; east/harbor exits also need physical and lore justification. Reach a real choice between coast, fields and forest.
- 5–10 minutes: complete one short outing. The player sees a return road, a distant landmark and a shrine in context. Combat sits in clearings with space to dodge and use impact mechanics.
- 10–15 minutes: awaken a shrine, return by another road, try a selected destination on M, or start the forest investigation. Either guild remains a valid choice. This is a desired test script, not a measured current-build timeline.

## M map and directions

Use three scales: Island (coastline/districts), Local (streets/services/junctions) and Underground (current dungeon/floor). Preserve orientation between views. The current player marker shows heading and true projected position; an indoor hero anchors to the correct building entrance on the island layer.

Search and click select a known destination. Sidebar shows name, role, level guidance, discovered/locked state and a plain reason when unavailable. **Directions** previews a route, **Set route** tracks it, **Clear route** removes it. A map click never silently teleports the hero.

Modes: **Roads** prefers maintained roads but does not promise safety; **Shortest walk** may include validated trails; **Waypoints** may combine a walking approach, eligible shrine transition and destination walk. Separate discovered, awakened and eligible state. The existing `unlocked_teleporters` dictionary can contain locked discoveries, so it cannot be trusted as travel permission.

Distance is sum of current navigable legs in metres. Walking estimate uses effective speed, excludes combat/loading and identifies the estimate. Show teleporter legs separately, including destination shrine and remaining foot route; never count a teleport as walked metres. Recompute after flags change, transitions, destination changes or an off-route threshold (initially 8–12 m for at least 1 second). Rate-limit replans (initially at most 2 per second) and tune after actual navigation tests.

In play, display only next instruction, remaining distance and destination pointer near minimap; optional faint ground hints fade outside the next junction. Reaching a turn advances the instruction. Wrong turns replan without punishing the player. Arrival clears the route within a tested POI radius and does not auto-enter a dungeon or auto-activate a shrine.

Single-player planning should pause world simulation, consistent with a tested modal/input design; opening M must not immobilize a still-vulnerable hero. Multiplayer, if later added, needs a separately designed rule. M/Escape close; pressing letters inside search must type rather than close the map. Controller/keyboard selection and focus return must work.

Known public geography may be charted at start; shrine eligibility requires actual discovery/awakening. Uncharted areas retain coastline silhouette and mist, without revealing secret encounters. Labels use shape as well as color: triangle player, circle shrine, doorway dungeon, diamond objective. Minimum essential body/label size target 16 px at 1280×720 after scaling; clickable controls at least 36 px. No essential information in tiny uppercase text.

## Art implementation rules

Use illustrated geography behind native labels/roads/markers/fog. Provide a clean base atlas, not just a flattened screenshot of this concept. Bronze/charcoal/ivory panels come from current UITheme. Pale cyan marks Aether and active routes; amber lamps mark habitation; restrained violet marks corruption. Do not use luminous route strokes for every ordinary road.

In-world roads should be 5–7 m wide where carts/two-way combat are expected; trails 2.5–3.5 m, bridge usable widths at least 3.5–4 m initially, with wider combat bays. These are blockout targets; validate against actual hero/Tempo/enemy collision sizes and camera. Keep climbable ramp slopes well below the current 40° navigation ceiling. Low southern walls and foliage fade preserve isometric visibility. Put carts and crates in pullouts, never across the only walkable seam.

The atlas painting exaggerates landmark sizes and the keyframe has more detail than the current kit. Reuse existing stone/timber modules and lighting first, then add only the meshes needed to support the layout. The decorative center-lake ruin and sea shipping are future art cues, not implied playable features in the first milestone.
