# bh-029 contract — Zarael Island: the ship, Agdao, Terax, the Bridge of Death, three Vaults, 30 new monsters

Run id `bh-029`, 1 October 2026. Godot 4.7.2 (`C:\Users\Lemon PC\Desktop\Godot.exe`), Blender 5.2
(`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`), Windows 10, RTX 4060. Branch `main`, baseline HEAD
`94a7dc6`. Work stays in the main tree; at the end the user asked to push everything to main and build the EXE + APK.

## Request (user, verbatim intent)
- Lore: Jre has 4 main islands. After Kethrax dies a **Ship** appears near **Wyman Outpost** ("Hyman Outpost" in the
  request) that carries the hero to the next island, **Zarael Island, the corrupted**. Old saves where Kethrax is
  already dead get the ship immediately.
- A whole new epic island about **1.5x the size of Salmonan**, with all-new textures, assets, objects and structures.
- Town **Agdao**: larger than Malasugue, a new design, ancient tech features, lots of elevated floors and stairs.
- Arriving at Agdao's pier, the hero is greeted by **Terax** in a cutscene. Terax saw **Aljay** pass by a couple of
  years ago; Aljay helped clear **3 of the most impossible dungeons** on the island so people could cross the
  **Bridge of Death**, a very dangerous route (epic bridge, lots of ancient tech design).
- Agdao needs the hero's help to bring back its once peaceful ways (a convincing story with ancient tech).
- Theme: somewhat ancient Aztec, glowing wires, ancient markings.
- At least **30 brand-new enemies and types** (island + dungeons). Enemy levels **30–50 and above**.
- Then push everything to main and compile the EXE and APK. Screenshots along the way.

## House rules (every builder)
- Names the user supplied are used as given: Zarael, Agdao, Terax, Aljay, Bridge of Death, Kethrax, Wyman.
  Every other new name is invented for Jre: **no Filipino words/names/folklore, and no borrowed real-culture names
  (no Nahuatl/Maya words)** — the Aztec feel is visual only (stepped pyramids, fret/glyph bands, feather crests,
  obsidian edges, jade, turquoise mosaic).
- Art must look hand-made and in-world (see memory: neon signs, flat colour placards and purposeless structures were
  rejected). Glowing wires and glyphs are *ancient engineering*: inlaid copper/gold channels, not neon tubes.
- Probes/captures that boot a hero pass `--slot=93..99`. Never kill Godot/Blender by image name — only your own PID.
  Never run Godot `--import` or the editor on `game/`; builders validate on a scratch copy. Only the Orchestrator
  imports into `game/`.
- Each builder writes ONLY its owned files (below). Shared files are owned by the Orchestrator.
- Write helper scripts with a file tool, not bash heredocs (apostrophes break heredocs in this harness).

## Story (frozen; provisional details are marked in docs/LORE.md)
- **Zarael** is the eastern island (it takes the place of the provisional "Corvessa"). Its people say the island is
  named after what sleeps under it: **Zarael, a Gigas**. Long before the Binding, the **Wirewrights** (Zarael's
  ancient builders) did not swear oaths over their giant: they laid the **Heartwire** — a net of gold-bright wire
  inlaid through the island's stone — and fed it from the **Dawn Engine** in the **Heart Citadel**. Its slow
  current is a lullaby that keeps Zarael asleep; as a gift of the same current, Agdao's lamps burned without oil,
  its lifts climbed the terraces, its water ran uphill and its gates knew friend from foe.
- **The Dimming** (seven winters ago): Kharvenn **chain-priests** (the Dominion that leashes Gigas with pain) came
  quietly and drove rune-chains into the three **Vaults** where the Heartwire's great lines cross. The current
  turned: the **Blackwire**, violet-red. Wirewright constructs went mad, beasts near the lines changed, and people
  who worked the wires fell **wire-sick**. The Bridge of Death's own ward pylons, fed by the Vaults, began to burn
  anyone who set foot on it — the only road to the Heart Citadel and the farms beyond the gorge.
- **Two winters ago** a man in black dragon-scale with broken chain links hanging from his wrists came over the sea:
  **Aljay**. With Terax he went down into the three Vaults — the Jade Sepulchre, the Obsidian Engine, the Veinworks —
  and killed what held them. The bridge went quiet; people crossed the Bridge of Death for the first time in five
  years. Aljay crossed alone to the Heart Citadel; for one season the wires burned gold. Then he walked back over the
  bridge, asked for a boat, and sailed east without a word. (Mystery hook: the Accord says he was taken at the
  Weeping Causeway three winters ago. Terax: "Then the Accord is wrong, or he walked out of his chains. I know what I saw.")
- **Now**: since last winter the chain-priests are back under a new master, **Orvul Dram, the Leash-Abbot**. The Vaults
  woke again, worse. The Blackwire is in Agdao's own streets: lifts dead, half the terraces dark, wire-sick in every
  family. When Kethrax fell, Terax sent Agdao's ship to find the hero who broke a Kharvenn-made chain.
- **Quest chain "Act IV — Zarael, the Corrupted"** (Objectives; levels are recommended):
  1. `zr_ship` The Ship at Wyman (L30) — after Kethrax: a ship at the Marsh Jetty; Captain **Ilsa Rhondar**. Flag `zr_ship_sailed`.
  2. `zr_terax` Agdao (cutscene on arrival) — Terax greets the hero at the pier. Flag `zr_terax_met`.
  3. `zr_council` The Wirekeeper (L30) — Wirekeeper **Halvessa Orn** at the Crown of Steps explains the Heartwire. Flag `zr_wirekeeper_met`.
  4. `zr_relays` Wire-sick (L32) — cut the chains off three corrupted relay pylons in the Coilwood. Flag `zr_relays_cut` (counts `zr_relay_1..3`).
  5. `zr_vault_jade` / `zr_vault_obsidian` / `zr_vault_vein` — clear the three Vaults (their lords). Flags `boss_jade_king_defeated`,
     `boss_engine_heart_defeated`, `boss_vein_mother_defeated`. Each relights one ward pylon on the Bridge.
  6. `zr_bridge` The Bridge of Death (L44) — cross it; defeat **Varrogh, the Deathspan Colossus**. Flag `boss_deathspan_defeated`.
  7. `zr_abbot` The Leash-Abbot (L50) — in the Heart Citadel defeat **Orvul Dram**. Flag `boss_leash_abbot_defeated`.
  8. `zr_dawn` The Dawn Current — return to Terax; the Heartwire burns gold again (Agdao's wires and lamps change from
     violet-red to gold on `zr_heartwire_restored`). Visit-based end with a hook toward Aljay's trail east.

## Geography (frozen ids; sizes are walkable bounds)
Salmonan surface maps total ≈ 117,000 m². Zarael's surface ≈ 190,000 m² (≈1.6x), plus three dungeons.

| Map id | Name | Levels | Bounds | Notes |
|---|---|---|---|---|
| `agdao` | Agdao | town | ~170 x 160 | Pier (south, the ship + Terax), harbour terrace, market terrace, Wire Market, council hall, houses on stepped terraces joined by stairs and footbridges, the **Crown of Steps** pyramid (north, Wirekeeper at its top), waypoint, Hero's Vault, shops/forge. Exits: north-east gate → Coilwood. |
| `zr_coilwood` | The Coilwood | 30–36 | ~280 x 200 | Jungle of giant buttress trees over abandoned step-farms and aqueducts; three corrupted relay pylons; Jade Sepulchre gate; Kharvenn camp; exit east → Barrens. |
| `zr_barrens` | The Glasswire Barrens | 36–42 | ~260 x 200 | Plain where the Blackwire surfaced: cracked red ground, violet glass growths, a fallen colossus; Obsidian Engine and Veinworks gates; waypoint camp; exit north → Bridge. |
| `bridge_of_death` | The Bridge of Death | 42–46 | ~80 x 330 | A 300 m Wirewright span over a bottomless gorge: gatehouses at both ends, ward pylons (3, relit by the Vaults), guardian boss on the far platform. |
| `zr_citadel` | The Heart Citadel | 46–52 | ~200 x 170 | Temple-fortress around the Dawn Engine; Kharvenn siege works; Leash-Abbot arena at the Engine. |

Dungeons (DataDungeons-style, generated floor plans, 6 floors each, `zarael` group):
| id | Name | Theme | Levels | Gate on | Lord |
|---|---|---|---|---|---|
| `jade_sepulchre` | The Jade Sepulchre | `jade` (jade-green tombs, serpent friezes, green-gold wire) | 33–40 | zr_coilwood | Quorrath, the Jade Sleeper (`jade_king`) |
| `obsidian_engine` | The Obsidian Engine | `obsidian` (black glass machine halls, molten copper channels) | 39–46 | zr_barrens | Kalvex, the Engine Heart (`engine_heart`) |
| `veinworks` | The Veinworks | `vein` (inside the Gigas: bone, red-violet wire veins, pulsing light) | 45–53 | zr_barrens | Ysvharn, the Giant's Heart (`vein_mother`) |

Travel: the ship `zr_ship` (an interactable at Wyman's Marsh Jetty and Agdao's pier) sails between `wyman_outpost`
(spawn `jetty`) and `agdao` (spawn `pier`). Agdao's waypoint (`agdao_shrine`) and the Barrens camp shrine join the network.

## The 30 new monsters (frozen ids; body: H humanoid, Q quadruped wolf-kit, S 8-leg kit, F floating wisp convention)
| # | id | Name | Body | Role | Where | Builder |
|---|---|---|---|---|---|---|
| 1 | glyphbound_warrior | Glyphbound Warrior | H | melee grunt: quilted armour, feathered crest helm, obsidian-edged war club + round hide shield | Coilwood | M1 |
| 2 | coil_shaman | Coil Shaman | H | caster: jade mask, feather cape, staff wound with glowing wire | Coilwood | M1 |
| 3 | mossback_idol | Mossback Idol | H (big) | construct brute: squat carved stone idol, moss, glowing eye-slots, stone fists | Coilwood | M1 |
| 4 | wireback_stalker | Wireback Stalker | Q (stem `cat_`) | pouncing charger: big spotted cat, copper wire spine glowing | Coilwood | M1 |
| 5 | relay_mote | Relay Mote | F | seeker/bomber: carved glyph-disc core with copper rings | Coilwood/Barrens | M1 |
| 6 | wiresick_husk | Wire-sick Husk | H | swarm fodder: a townsperson with wires grown out of back and arms | Barrens | M2 |
| 7 | arc_sentinel | Arc Sentinel | H construct | ranged + melee: Wirewright guard with a lightning spear | Barrens | M2 |
| 8 | chain_priest | Kharvenn Chain-Priest | H | caster/support: grey iron robes, rune-chains, censer | Barrens/Citadel | M2 |
| 9 | chain_bearer | Kharvenn Chain-Bearer | H (big) | brute: drags an anchor on a rune-chain | Barrens/Citadel | M2 |
| 10 | glasswire_scorpion | Glasswire Scorpion | S (stem `scorp_`) | tank/striker: violet glass-shelled scorpion, sting tail | Barrens | M2 |
| 11 | span_warden | Span Warden | H construct | shield tank: glyph-stone tower shield, bronze body | Bridge | M3 |
| 12 | wire_leaper | Wire Leaper | H | blinking duelist: twin obsidian blades, feather cloak, wire tattoos | Bridge/Citadel | M3 |
| 13 | ward_eye | Ward Eye | F | beam caster: stone eye in bronze rings | Bridge | M3 |
| 14 | deathspan_colossus | Varrogh, the Deathspan Colossus | H construct BOSS | the bridge's guardian, arc coils on its back | Bridge | M3 |
| 15 | leash_knight | Kharvenn Leash-Knight | H | elite: heavy iron plate, chain-flail | Citadel | M3 |
| 16 | gigas_spawn | Gigas Spawnling | H (big) | brute: stone-and-bone creature grown from the giant | Citadel/Veinworks | M4 |
| 17 | heartwire_wraith | Heartwire Wraith | F | caster: a knot of corrupted current around a mask | Citadel | M4 |
| 18 | leash_abbot | Orvul Dram, the Leash-Abbot | H BOSS | final boss: chain-priest master, great chain-censer | Citadel | M4 |
| 19 | marrow_hound | Marrow Hound | Q (stem `mhound_`) | pack hunter: bone-plated hound with red veins | Veinworks | M4 |
| 20 | vein_knight | Veinbound Knight | H | elite melee: bone-and-wire armour, greatsword | Veinworks | M4 |
| 21 | jade_sleeper | Jade-Wrapped Sleeper | H | fodder: mummy in jade plates and wire bindings | Jade | M5 |
| 22 | serpent_oracle | Serpent Oracle | H | caster: serpent-head headdress, turquoise mosaic | Jade | M5 |
| 23 | jade_guardian | Jade Guardian | H construct | shield tank: jade statue warrior | Jade | M5 |
| 24 | sepulchre_beetle | Sepulchre Beetle | S (stem `beetle_`) | tank/charger: jade-shelled beetle | Jade | M5 |
| 25 | jade_king | Quorrath, the Jade Sleeper | H BOSS | the Sepulchre's lord, jade throne-armour, serpent sceptre | Jade | M5 |
| 26 | obsidian_golem | Obsidian Golem | H (big) construct | brute: black glass body, molten copper seams | Obsidian | M6 |
| 27 | stoker_thrall | Stoker Thrall | H | fire bomber: engine worker with a furnace on the back | Obsidian | M6 |
| 28 | shardcaster | Obsidian Shardcaster | H | ranged: throws obsidian shards, glass sling | Obsidian | M6 |
| 29 | engine_heart | Kalvex, the Engine Heart | H construct BOSS | the Engine's lord: furnace chest, piston arms | Obsidian | M6 |
| 30 | vein_mother | Ysvharn, the Giant's Heart | H BOSS | the Veinworks' lord: a huge figure of bone and pulsing veins | Veinworks | M6 |

## Kit assets (frozen names; GLBs in `game/assets/environment/<name>.glb`)
**K1 — Agdao town kit** (`tools/blender/environment/assets_zarael_town.py`): `zr_step_pyramid`, `zr_terrace_2m`,
`zr_terrace_4m`, `zr_stair_2m`, `zr_stair_4m`, `zr_house_a`, `zr_house_b`, `zr_house_c`, `zr_hall_council`,
`zr_market_stall_a`, `zr_market_stall_b`, `zr_wire_pylon`, `zr_wire_conduit_4m`, `zr_wire_lamp`, `zr_glyph_stele`,
`zr_serpent_statue`, `zr_lift_platform`, `zr_aqueduct_4m`, `zr_fountain_wire`, `zr_pier_4m`, `zr_pier_end`,
`zr_ship`, `zr_gate_arch`, `zr_brazier_stone`, `zr_planter`, `zr_footbridge_8m`, `zr_wall_4m`, `zr_wall_tower`.
**K2 — wilds / bridge / citadel kit** (`tools/blender/environment/assets_zarael_wild.py`): `zr_tree_ceiba`, `zr_palm`,
`zr_fern_giant`, `zr_agave`, `zr_vine_curtain`, `zr_bush_jungle`, `zr_ruin_wall`, `zr_ruin_column`, `zr_ruin_shrine`,
`zr_relay_pylon`, `zr_chain_spike`, `zr_colossus_fallen`, `zr_glass_growth`, `zr_bridge_span_8m`, `zr_bridge_pylon`,
`zr_bridge_gatehouse`, `zr_bridge_pier`, `zr_gate_jade`, `zr_gate_obsidian`, `zr_gate_vein`, `zr_rock_ochre_large`,
`zr_rock_ochre_medium`, `zr_cliff_ochre`, `zr_dawn_engine`, `zr_citadel_wall`, `zr_citadel_tower`, `zr_kharvenn_tent`,
`zr_chain_rack`, `zr_jetty_wood`.

## New materials (frozen names; the Orchestrator adds them to `MaterialLibrary.ENV`)
| Name | Look | Texture set |
|---|---|---|
| `BH_GlyphStone` | pale weathered limestone with carved stepped-fret / glyph bands | `glyph_stone` |
| `BH_GlyphStoneDark` | the same, darker, mossy | `glyph_stone` |
| `BH_Jade` | polished jade, green, veined | `jade_stone` |
| `BH_Obsidian` | black volcanic glass, glossy | `obsidian` |
| `BH_LimePlaster` | ochre lime plaster on walls | `lime_plaster` |
| `BH_LimePlasterRed` | red-painted plaster | `lime_plaster` |
| `BH_TerracePave` | fitted stone paving with glyph tiles | `terrace_paving` |
| `BH_Turquoise` | turquoise mosaic | `turquoise_mosaic` |
| `BH_Wire` | inlaid Heartwire: emissive; violet-red while corrupted, gold once restored (runtime) | — |
| `BH_Glyph` | carved glyph inlay, emissive teal | — |
| `BH_Blackwire` | always-corrupted wire (Kharvenn chains, corrupted pylons): emissive violet-red | — |
| `BH_Feather` / `BH_FeatherRed` | feather crests / capes (green-teal / scarlet) | — |
| `BH_JungleLeaf` | broad jungle leaves | — |
Terrain texture sets (T1): `jungle_floor`, `red_clay`, `blackwire_soil`, `cliff_ochre`, `terrace_paving`.

## Components (one owner each)
| # | Component | Owner | Files |
|---|---|---|---|
| T1 | Textures + portraits + Zarael atlas art | Builder T1 | `tools/textures/gen_zarael_textures.py`, `game/assets/textures/{set}_{albedo,normal,rough}.png` for the sets above, `tools/ui_art/bh029_*.py`, `game/assets/ui/portraits/{terax,wirekeeper,ilsa,agdao_*}.svg`, `game/assets/ui/atlas/zarael_atlas.png`, `work/lemondev/bh-029/evidence/textures/` |
| K1 | Agdao town kit | Builder K1 | `assets_zarael_town.py` (+ one import line in `build_assets.py`/`registry.py` as its pattern needs), the K1 GLBs (+`.import` copied from a sibling), `evidence/kit_town/` |
| K2 | Wilds/bridge/citadel kit | Builder K2 | `assets_zarael_wild.py` (+ its registration line), the K2 GLBs, `evidence/kit_wild/` |
| M1–M6 | Monster models (5 each) | Builders M1–M6 | `tools/blender/characters/enemy_<id>.py`, `tools/blender/creatures/build_<id>.py`, `game/assets/characters/<id>.glb(.import)`, own keys in `creature_meta.json`, `evidence/models_m<n>/` |
| N1 | Terax + Agdao people (6 NPC models) | Builder N1 | `tools/blender/characters/town_{terax,wirekeeper,ilsa,agdao_porter,agdao_vendor,agdao_elder}.py`, their GLBs, `evidence/npcs/` |
| S | Maps, data, story, quests, cutscenes, ship, enemy defs, dungeons, UI, tests | Orchestrator | everything in `game/src`, `game/tests`, docs |

## Acceptance gates
- Headless suite: no new failures versus the known baseline (docs/HANDOFF_bh-027 + memory: test_balance, test_enemies,
  test_enemies2, test_dungeon_growth pre-existing); new `test_bh029.gd`: every Zarael map builds and bakes a navmesh;
  the ship appears iff `boss_kethrax_defeated` (old-save case included); the quest chain advances flag by flag; all 30
  monster defs load with a GLB and each attack anim exists in its model; the three Vaults have floors and lords; save
  round trip with the new flags; Zarael enemies' levels sit in 30–53.
- Every GLB imports in Godot with its listed clips (builders: scratch project; Orchestrator: game import).
- Captures (native 1920x1080, real renderer): the ship at Wyman, the Terax cutscene, Agdao overview/terraces/pyramid,
  each wild map, the Bridge of Death, the Citadel, each dungeon, every new monster in game.
- Blind benchmark vs a commercial reference: UNVERIFIED unless an independent critic is run (state it in the handoff).
- Budget: max 8 build/review passes per component.
