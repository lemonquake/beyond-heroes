# Dungeon progression and equipment

All 20 dungeons now share one progression policy in `game/src/core/progression/dungeon_growth.gd`.
Original floor IDs, champions, bosses, seals, raid recovery and save records remain intact. Extra floors continue
below the original boss arena; that arena keeps its separate route home.

| Hero level on entry | Added floors | Changes |
| --- | ---: | --- |
| 1–24 | 0 | Original dungeon layouts and enemy levels |
| 25–34 | 1 | First themed reinforcement, extra elites, named depth guardian, new equipment and relics |
| 35–44 | 2 | Second reinforcement type, one additional enemy per pack |
| 45–49 | 3 | Another floor; elite and reward bonuses continue increasing |
| 50–54 | 4 | Two reinforcement positions per pack, third reinforcement type, two additional pack members, three elite abilities |
| 55–59 | 5 | Another floor and increasing elite/reward chances |
| 60 | 6 | Full depth, with enemy levels capped at 60 |

## Scaling and persistence

The hero's level is saved at dungeon entry. It remains fixed while moving between that dungeon's floors, reloading,
or continuing a saved game. Leaving and returning starts a new visit. Multiplayer arrivals use an occupied floor's
owner profile. The policy never reads damage, gear score or current health: finding a better weapon still makes the
hero stronger against the same enemies.

A party portal or saved return point to a floor above the hero's own unlock level retains that floor's minimum
stage. This keeps its routes and exit valid; it does not unlock that depth at the surface gate for a low-level hero.

Original low-level dungeons ease toward the hero's level over levels 25–35. Naturally harder dungeons keep their
minimum level. Added floors match the hero immediately, so level-25 equipment can drop at the first milestone.
Floor depth adds up to two levels above the hero, bounded by the level cap. Stats use the existing combat growth
formulas and difficulty setting, avoiding a second multiplicative stat-scaling system.

The surface gate lists sequentially unlocked floors. Defeating the original lord opens the first added floor.
Each added floor has a guaranteed named guardian inside its Seal Keeper pack. Clearing the entire pack breaks
the descent seal; the final available floor instead opens a route home. Arrival portals always offer a way out.
If another floor later unlocks, the previous final floor becomes a descent without losing its completed seal.

Original raid recovery affects original floors only. Added floors remain populated. Both added-floor chests require
clearing the current visit's Seal Keepers, even if the route was opened earlier. Chest refill timing is unchanged.
Enemy checkpoints preserve guardian identity and rewards during multiplayer ownership changes.

## Encounters and rewards

Reinforcement pools are specific to all 17 dungeon themes. They reuse enemies with established models and working
combat mechanics: summoners, healers, stealth attackers, reflection guards, linked twins, brutes and elemental casters.
The selected enemies replace actual pack positions rather than being appended beyond the spawned pack size.

At level 25 elite probability gains 5 percentage points, rising to 20 by level 50. Level 50 adds another 12 points,
which grows to 20 at level 60. Ordinary pack probability is bounded at 90%; Seal Keepers remain guaranteed.
Level-50 elites have three distinct existing abilities. Guardian health and damage use modest champion multipliers
on top of those elite stats. Difficulty and telegraphs remain those of the existing combat system.

Dungeon rarity-roll bonuses grow from 0.15 at level 25 to 1.0 at 50 and 1.25 at 60. Guardians drop 3–4 pieces, at
least Elite quality, including a weapon for the hero's class. They also have a 35% chance of a new class relic below
enemy level 50 and 65% from level 50, before Magic Find. These are chances, not guaranteed relics. Named relics
retain their fixed Mythical or Legendary quality and signature powers.

Monster equipment and dungeon chest equipment use strict class selection. Weapon families are selected before
bases, keeping large catalogs from crowding out axes and other existing families. Bases more than eight levels old
lose weight smoothly; they remain possible because existing item-level scaling can keep them useful. A single
equipment bundle avoids repeating a base while eligible alternatives remain. Dedicated special rolls respect item
level and class. Ordinary equip requirements and earned-rank rules still apply.

## Equipment and art

80 new bases, 20 for each class:

| Class | Weapons | Armor |
| --- | --- | --- |
| Knight | 12 swords, 4 greatswords | Coat, crown, grips, treads |
| Mage | 8 staves, 8 wands | Coat, crown, grips, treads |
| Ranger | 8 bows, 8 javelins | Coat, crown, grips, treads |
| Shadowblade | 8 daggers, 8 claws | Coat, crown, grips, treads |

The eight coats and grips are named relics with functional signature powers. Weapon bases vary in silhouette,
proportions, guards, ornament, material, weight, attack speed, elemental share and implicit bonuses. Damage budgets
use the existing weapon-family formula. Boots retain the normal movement-speed bonus. Every piece has its own
GLB used by the item model system and a rendered inventory icon; weapons also use their models when held.

Authoring source: `tools/blender/items/depth_catalog.py`. Running it regenerates the GDScript catalog and
`depth_specs.json`. The existing Blender item pipeline consumes those specifications without generic fallback.
Run the Godot `dump_items.tscn` scene before generating models. Limit the build to the IDs in `depth_specs.json`.
The 80-piece preview is `output/depth-equipment-catalog.png`.

## Verification

`test_dungeon_growth.gd` checks milestone boundaries, monotonic bounded levels, saved visits, sequential gate
access, every added plan's connectivity, reinforcement IDs, all 80 models/icons, class selection, drop variety,
signature powers, and a populated floor where clearing the guardian pack opens treasure and the final exit.
`capture_depths.tscn` exercises the real renderer and enemy deaths using scratch save slot 94.

Final validation: 75 tests across eight suites passed with 50,970 checks and zero failures. Suites cover dungeon
progression, original dungeon builders, combat growth, equipment, loot, network data and team loot. Results are
saved in `output/depth-final-tests.log` and `output/depth-final-report.json`.

The renderer capture passed in Compatibility and Forward+ modes: a populated floor has a named guardian with
three abilities, and real enemy deaths open the final exit and guarded treasure. See `output/depth-guardian.png`
and `output/depth-render-final.log`. Multiplayer validation covers serialization and replica behavior; it does
not include a live session across multiple computers.

The broader legacy class-balance simulation still fails its class performance bands. The repository's pre-change
balance evidence already records the same imbalance; this update does not resolve it. Godot also emits shutdown
resource warnings in these test scenes. Existing exported EXE/APK builds have not been rebuilt.
