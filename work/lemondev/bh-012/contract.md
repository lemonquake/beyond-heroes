# bh-012 contract — Dungeons, 25 new monsters, gacha loot names, Tempo summoning, new gear passives, road camps

Run id `bh-012`, 28 September 2026. Engine Godot 4.7.2 (Jolt) at `C:\Users\Lemon PC\Desktop\Godot.exe`, Blender 5.2
(`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`), Windows 10, RTX 4060. Branch `main`.
Baseline: HEAD b386a80, clean tree. Work stays uncommitted in the main tree (user rule) unless the user asks.

## Request (user, verbatim intent)
1. Complex dungeons across the island, each with a very unique design and theme and themed monsters; real 2nd / 3rd
   storeys you can walk/climb via stairs; portals down one level at a time to stronger monsters, then a miniboss, then
   the dungeon boss. Not easy raids — the player should take time to get stronger. Art reference supplied by the user:
   a multi-storey flooded cistern cutaway (teal water below, torch-lit rooms on upper storeys joined by stairs and
   ladders, arches standing in the water, a boat, scaffolding) — saved as `references/bh012_dungeon_reference.jpg`.
2. Gear as unique as possible: randomized proper names and subnames so every run differs, "kinda like a Gacha".
3. Gacha vibes across the game, applied to Tempos (summoning).
4. More unique equipment passives: higher gold drops, higher EXP rate, +% HP / Mana regeneration, etc.
5. More enemy camps outside, especially on the roads to Wyman Outpost (they are empty); a dungeon here and there.
6. At least 20 new unique monsters for the dungeon themes.

## House rules (every builder)
- Never use Filipino words, names or folklore. Invent original fantasy names (no real-culture pastiche).
- Probes/captures that boot a hero pass `--slot=93..99`. Never kill Godot by image name. Tests never write settings.cfg.
- Never run Godot `--import` (or the editor) on `game/`; builders use a scratch copy (`godot_check.py --scratch`).
  Only the Orchestrator imports into `game/`.
- Each builder writes ONLY its owned files. Shared files are owned by the Orchestrator.

## Frozen design

### Dungeons (5 themes x 4 floors = 20 floor maps, built by one shared builder `src/world/maps/dungeon.gd`)
| Dungeon | Theme | Entrance (surface) | Levels (F1..F4) |
|---|---|---|---|
| Hollowroot Warren | fungal cavern, roots, glowing caps, spore bogs | Westreach, off the Fen Road (road to Wyman) | 5-7, 7-9, 9-10, 11 |
| Saltmouth Deeps | drowned vault / flooded cistern (the reference) | Westreach, Saltmouth Cave by Tideglass Cove | 7-9, 9-11, 11-12, 13 |
| Emberforge Depths | volcanic forge, lava channels, basalt | Westreach, off the Lake Shore Road (road to Olivar) | 10-12, 12-14, 14-15, 16 |
| Rimeglass Barrow | frozen crypt, ice crystals | Ruined Forest, north rim | 13-15, 15-17, 17-19, 20 |
| The Shattered Orrery | ruined Aether observatory, brass rings, starglass | Wyman Outpost, beyond the north gate (Watch Road) | 17-19, 19-21, 21-23, 25 |

Every floor: several rooms on the 4 m grid, at least one walkable upper storey (gallery at +4 m) reached by stairs, and
from floor 2 a third storey (+8 m) on at least one floor; a themed hazard pit (water / spores / lava / ice / void)
under the lower storey; an arrival portal (back up) and a sealed descent portal that opens when the floor's Seal
Keeper pack (an elite camp) is cleared. Floor 3 holds the dungeon miniboss beside the descent portal. Floor 4 is the
boss sanctum; the boss drops a Relic Cache and opens the way home.

### 25 new monsters (5 per theme; the 5th is the boss)
| Theme | id | Name | Body | Role |
|---|---|---|---|---|
| Deeps | drowned_deckhand | Drowned Deckhand | humanoid | melee grunt (boat hook) |
| Deeps | brinecaller | Brinecaller | humanoid | caster |
| Deeps | reef_crawler | Reef Crawler | crab (8-leg kit) | shell tank |
| Deeps | barnacle_hulk | Barnacle Hulk | humanoid, big | brute (anchor) |
| Deeps | bell_warden | Ossric Vael, the Drowned Bell | humanoid | BOSS |
| Warren | sporeling | Sporeling | humanoid, small | swarm fodder (bursts) |
| Warren | rootback_boar | Rootback Boar | quadruped (wolf kit) | charger |
| Warren | rootweaver | Rootweaver | humanoid | root-snare caster / healer |
| Warren | mycelid_hulk | Mycelid Hulk | humanoid, big | brute (spore breath) |
| Warren | rot_mother | Verdigast, the Rot Mother | humanoid | BOSS |
| Ember | cinder_imp | Cinder Imp | humanoid, small | blinking fire caster |
| Ember | slag_hound | Slag Hound | quadruped (wolf kit) | pack hunter (fire) |
| Ember | forge_thrall | Forge Thrall | humanoid | shield tank |
| Ember | magma_golem | Magma Golem | humanoid, big | brute (lava) |
| Ember | forgemaster | Brakka Durnhelm, the Forgemaster | humanoid | BOSS |
| Rime | rime_husk | Rimebound Husk | humanoid | grunt (shatters) |
| Rime | ice_wraith | Ice Wraith | floating (wisp convention) | caster |
| Rime | rime_weaver | Rime Weaver | spider (8-leg kit) | freezing webs |
| Rime | barrow_jarl | Barrow Jarl | humanoid | elite shield warrior |
| Rime | winter_crown | Skaldra, the Winter Crown | humanoid | BOSS |
| Orrery | clockwork_sentry | Clockwork Sentry | humanoid construct | ranged (crossbow) |
| Orrery | star_mote | Starmote | floating (wisp convention) | seeker / bomber |
| Orrery | astral_duelist | Astral Duelist | humanoid | blinking duelist |
| Orrery | void_seer | Void Seer | humanoid | gravity caster |
| Orrery | astrarch | The Astrarch | humanoid construct | BOSS |

### Loot, gacha, passives
- Named gear: every Elite+ item gets a generated proper name + epithet ("Vornhald, Oath of the Last Tide"), drawn from
  syllable tables and theme word pools keyed by its element/affixes/powers; deterministic per item seed; saved.
- Gear stars (1-5) from how close the rolls are to perfect; a "Perfect" roll flourish.
- Relic Caches (Worn / Gilded / Radiant): dungeon chests, minibosses, bosses; opening plays a gacha reveal.
- Tempo summoning: Soul Embers currency; single / ten-call; star grades 3-5; pity (a 4-star within every 10 calls,
  soft pity toward 5-star, hard pity at 70); duplicates raise Resonance (bonus strength, up to R5); a spirit hall
  keeps unbound spirits; new renowned spirits join the banner pool; a reveal sequence.
- New equipment passives (affixes): Gold Find, Experience Gain, increased HP / Mana Regeneration %, Life / Mana on
  Kill, Potion Effectiveness, Thorns, damage vs Elites and Champions, Soul Ember find, Tempo damage; plus new relic
  powers.

### Road camps
New enemy camps along Westreach's Lake Shore Road, Mill Lane, Fen Road, Field Road and Coast Road, and "wild" camps
outside the Olivar and Wyman palisades on the Watch Road (towns stay safe inside their walls).

## Components (one owner each)
| # | Component | Owner | Files |
|---|---|---|---|
| M-A | Deeps models (5) | Builder A | `tools/blender/characters/enemy_<id>.py`, `tools/blender/creatures/build_reef_crawler.py`, GLBs + `.import` in `game/assets/characters/`, `creature_meta.json` (merge own keys only), `work/lemondev/bh-012/evidence/models_deeps/` |
| M-B | Warren models (5) | Builder B | same pattern (`build_rootback_boar.py`), `evidence/models_warren/` |
| M-C | Ember models (5) | Builder C | same pattern (`build_slag_hound.py`), `evidence/models_ember/` |
| M-D | Rime models (5) | Builder D | same pattern (`build_ice_wraith.py`, `build_rime_weaver.py`), `evidence/models_rime/` |
| M-E | Orrery models (5) | Builder E | same pattern (`build_star_mote.py`), `evidence/models_orrery/` |
| K | Dungeon environment kit (25 props) + 3 texture sets | Builder F | `tools/blender/environment/assets_dungeon.py` (+ one import line in `build_assets.py`), new GLBs in `game/assets/environment/`, `tools/textures/` additions, new texture PNGs, `evidence/env_kit/` |
| S1 | Dungeon framework, floors, island placement, portals, seals | Orchestrator | `data_dungeons.gd`, `dungeon.gd`, `data_maps.gd`, `data_island.gd`, surface map builders, `spawner.gd`, `material_library.gd` |
| S2 | Monster runtime: defs, traits, minibosses, bosses | Orchestrator | `data_enemies*.gd`, `enemy*.gd`, `data_minibosses.gd` |
| S3 | Gear names, stars, relic caches, passives | Orchestrator | `item_generator.gd`, `item_names.gd`, `item_instance.gd`, `data_items.gd`, `loot.gd`, stats, UI |
| S4 | Tempo summoning | Orchestrator | `tempo_gacha.gd`, `data_tempos.gd`, `hero_data.gd`, `tempo_summon_window.gd`, dialogue/UI |
| S5 | Road camps | Orchestrator | `westreach.gd`, `olivar.gd`, `wyman_outpost.gd`, `spawner.gd` |
| T | Tests, probes, captures | Orchestrator | `tests/unit/test_bh012*.gd`, `tests/tools/*` |

## Acceptance gates
- Headless suite: no new failures versus the bh-011 baseline (pre-existing failing suites listed in bh-011 handoff);
  compile_all 0 failed; new tests: every dungeon floor builds, bakes a navmesh with an upper storey reachable by path
  from arrival, has arrival + descent/return portals; every new monster def loads with a GLB and each attack anim exists
  in its model; gacha pity invariants (10,000 simulated calls: a 4-star in every 10, a 5-star by 70); saves round-trip.
- Every GLB imports in Godot with its listed clips (builders: scratch project; Orchestrator: game import).
- Runtime probe: walk each dungeon floor's arrival -> stairs -> upper storey; kill the seal pack; descend; boss.
- Captures (native, 1920x1080): each dungeon floor overview, upper storeys, every new monster in game, the summon
  reveal, a named-gear tooltip.
- Blind benchmark (dungeon look vs the user's reference): UNVERIFIED unless an independent critic is run.
- Budget: max 8 build/review passes per component.
