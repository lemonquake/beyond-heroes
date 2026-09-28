# bh-013 contract — Dungeons on the map, 15 new dungeons, raid recovery, 21 new monsters, push + APK

Run id `bh-013`, 28 September 2026. Godot 4.7.2 (`C:\Users\Lemon PC\Desktop\Godot.exe`), Blender 5.2, Windows 10.
Branch `main`. Baseline: HEAD b386a80 + the uncommitted bh-012 work (dungeons, 25 monsters, gacha) already in the tree.

## Request (user)
1. Dungeons exist but are nowhere on the map (M). Show them.
2. The island needs many more dungeons: varying levels, difficulties and themes.
3. A raided dungeon recovers after 30 min – 2 h: its monsters replenish, the dungeon boss does not come back, but
   minibosses are still produced.
4. At least 20 new, different enemies, including unique ones such as Summoners.
5. Push to main; rebuild the Android APK.

## Frozen design

### Map (M)
- Every dungeon gate is a known place from the start (public) and draws on the Island/Local views with the arch
  dungeon icon, its name and level range; the sidebar shows difficulty, floors, levels, progress and raid status.
- The Underground view lists every dungeon (old Catacombs chain included) as a grid: name, difficulty stars, levels,
  floors reached, and state (Unexplored / Floor n of N / Raided — recovers in m min / Recovered, boss defeated).
- Search finds dungeons and gates; Directions/Set route reach a gate by roads + trails.

### Dungeons
- 5 existing + 15 new = 20 multi-floor dungeons. Floors per dungeon: 2–5 (was fixed 4). Floors 1..N-2 are sealed by
  Seal Keepers, floor N-1 by the dungeon champion, floor N is the boss sanctum.
- Difficulty tier 1–5 (Easy, Normal, Hard, Brutal, Mythic): drives elite chance, camp size and recovery time.
- New floor plans are produced offline by a deterministic generator (`tools/dungeon_gen/gen_plans.py`) into
  `game/src/data/data_dungeons_x.gd`, validated by the same rules as bh-012's `validate_plans.py` (stairs, heights,
  connectivity from the arrival portal, markers on walkable cells).
- 11 new themes: hideout, crypt, hive, mire, thorn, sandtomb, storm, umbral, crystal, gilded, abyss (+ reuse).

| id | Name | Theme | Tier | Floors | Levels | Surface |
|---|---|---|---|---|---|---|
| cellars | Cutpurse Cellars | hideout | 1 | 2 | 2–4 | Westreach |
| burrows | Gnashgut Burrows | hideout (goblin) | 1 | 3 | 4–7 | Ruined Forest |
| ossuary | Blackvault Ossuary | crypt | 2 | 3 | 6–10 | Ruined Forest |
| warcamp | Ironjaw Warcamp | hideout (orc) | 2 | 3 | 9–13 | Westreach |
| hive | The Waxen Hive | hive | 2 | 3 | 12–16 | Olivar |
| sump | Blackwater Sump | mire | 3 | 4 | 15–19 | Wyman Outpost |
| briar | Briarheart Hollow | thorn | 3 | 4 | 18–22 | Westreach |
| dunemourn | Dunemourn Tomb | sandtomb | 3 | 4 | 21–25 | Olivar |
| thunderwell | Thunderwell Spire | storm | 3 | 4 | 24–28 | Ruined Forest |
| undercroft | The Umbral Undercroft | umbral | 4 | 4 | 28–32 | Wyman Outpost |
| geode | Prismdeep Geode | crystal | 4 | 4 | 32–36 | Westreach |
| vault | The Gilded Vault | gilded | 4 | 4 | 36–40 | Olivar |
| reliquary | Twinspire Reliquary | crypt (soul) | 5 | 5 | 40–46 | Wyman Outpost |
| wyrmcoil | Wyrmcoil Caverns | cavern | 5 | 5 | 45–51 | Westreach |
| maw | The Maw Beneath | abyss | 5 | 5 | 52–58 | Wyman Outpost |

### Raid recovery (all 20 dungeons)
- Raided = the dungeon boss falls. The raid is recorded per hero (`hero.dungeon_raids[id] = {at, until}`, wall-clock
  unix seconds) with a recovery time rolled in [30, 120] minutes, biased by tier (tier 1 ≈ 30–55 min, tier 5 ≈ 95–120).
- While recovering: floor camps and Seal Keepers do not spawn (the halls are empty and quiet); chests follow their own
  timer; minibosses (the floor champion and the sanctum Usurper) still spawn on their own respawn timer.
- After recovery: every camp replenishes. The boss never returns for that hero once raided; its sanctum is held by the
  dungeon's Usurper, a named champion (miniboss) that returns like any champion.
- Seals broken stay broken; the exit portal stays awake.

### 21 new monsters (+4 helpers without new models)
| id | Name | Body | Signature mechanic |
|---|---|---|---|
| gravecaller | Gravecaller | humanoid (robed) | SUMMONER: raises a ring of Bone Thralls bound to it (they crumble when it dies) |
| riftcaller | Riftcaller | humanoid (robed) | SUMMONER: tears open a Void Rift (a destructible structure) that keeps spawning shades until closed |
| mirage_weaver | Mirage Weaver | humanoid | Illusionist: two mirror images that mimic it; swaps places with an image when struck |
| bloodbinder | Bloodbinder | humanoid (robed) | Blood tether: channels a beam that drains the hero and heals itself; break by distance/LoS |
| aegis_acolyte | Aegis Acolyte | humanoid (shield) | Ward link: an ally it links takes 85% less damage until the acolyte falls |
| storm_herald | Storm Herald | humanoid (robed) | Marked strikes: runes around the hero, bolts fall after a delay; static charges stack to a stun |
| mirror_knight | Mirror Knight | humanoid (armored) | Mirror stance: reflects projectiles and part of frontal damage; weak from behind |
| warband_chieftain | Warband Chieftain | humanoid (big) | Rally: war cry hastes/empowers allies; its death demoralizes (fears) its band |
| soulbound_twin | Soulbound Twin | humanoid | Twin link: spawns in pairs; a fallen twin is revived by the other unless both die close together |
| briar_lasher | Briar Lasher | humanoid (plant) | Thorn hide: melee attackers take thorns damage; vine lash pulls |
| broodhost | Broodhost | humanoid (big) | Parasite burst: sheds Leechlings when hurt and on death |
| goblin_sapper | Goblin Sapper | humanoid (small) | Mine layer: plants proximity mines, throws satchels |
| treasure_gremlin | Treasure Gremlin | humanoid (small) | Loot runner: never fights, flees, sheds gold when hit, escapes through a portal after 25 s |
| gloam_ooze | Gloam Ooze | creature (blob) | Splitter: splits into two smaller oozes on death (two generations) |
| tunnel_maw | Tunnel Maw | creature (worm) | Burrower: dives underground (untargetable), erupts under the hero, surfaces to bite |
| stonegaze_basilisk | Stonegaze Basilisk | creature (lizard) | Petrifying gaze: channelled cone that builds petrification unless you leave it |
| shellback_grinder | Shellback Grinder | creature (armadillo) | Curl: curls into an armored ball and rolls; a poise break flips it, exposed |
| hive_nest | Waxen Hive | static structure | Nest: stationary, keeps releasing Hive Drones until destroyed |
| hive_drone | Hive Drone | floating (wings) | Dive-stinging flier, poison |
| gloomwraith | Gloomwraith | floating | Phase shift: ethereal (immune to physical, weak to elements) / tangible |
| prism_sentinel | Prism Sentinel | floating construct | Sweeping beam: a rotating laser line |
Helpers (existing models): bone_thrall (Hollow Soldier), void_rift (floating portal, new small model by Builder D),
leechling (spiderling model, tinted), mirror_image (weaver clone).

15 dungeon bosses: new EnemyDefs that reuse a model (new or existing) at boss scale with their own tint, phases and
attacks. 15 champions (floor N-1) + 20 Usurpers (sanctum after a raid) are miniboss entries.

## Gates (evidence, VERIFIED only with inspected output)
- Map: capture of the M map (Island + Underground) showing dungeon icons; routing test to a new gate.
- Plans: validator 100% of generated floors OK; every floor builds headless without errors; overview renders.
- Recovery: unit tests — boss kill records a raid in [30,120] min; camps skipped while recovering; boss never returns;
  usurper/champion spawn during recovery; camps return after recovery.
- Monsters: unit tests per mechanic (summon cap + bound death, rift spawns/closes, split generations, burrow
  untargetable, tether drain/break, ward link DR, mines, reflect, twin revive, gremlin escape, phase immunity, curl DR,
  gaze buildup, beam sweep); in-game bestiary captures per model.
- Full test suite: no new failures vs baseline (bh-012: 19 known failures in test_balance/test_enemies/test_enemies2).
- Android: debug APK exported with 4.7.2 templates to `build/BeyondHeroes.apk`.
- Blind benchmark review: not run this cycle (no benchmark supplied) → reported UNVERIFIED.
