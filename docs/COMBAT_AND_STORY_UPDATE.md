# Combat progression and the Forsaken Hero chapter

29 September 2026. Continues Claude Code's unfinished BH-021 story work and revises combat progression and guild ranks.

## Damage and equipment

Levels 1–5 retain their previous weapon, attribute and monster-health budgets. From level 6, Strength adds flat attack before the existing physical multipliers. Intelligence adds spell power and scales elemental staff/wand attacks; Wisdom and staff/wand damage contribute to spell power. Dexterity still improves accuracy and critical chance. Equipment, skill effectiveness, critical hits, elemental matchups and penetration remain separate contributors.

Weapon damage now uses the drop's item level as well as its base, quality, affixes and upgrades. Finding a level-30 version of an early weapon produces a stronger item; leveling the wearer does not silently level old equipment. Equipment requires at least item level minus three, or its original base requirement if higher. The extra item-level requirement stops at the player level cap, so pinnacle drops remain wearable. Beginner items retain their introductory budget. Armor receives a smaller increase. Item comparisons, character statistics, tooltips, auto-loot checks and Tempo equipment use these rules.

For `x = max(level - 5, 0)`, weapon growth is `1 + .065x + .0015x²`. A base-level normalization prevents low-level bases from becoming obsolete merely because their original damage budget is small. Enemy HP growth is `1 + .19x + .008x² + .0001x³`, on top of existing monster level, rank and difficulty scaling. Enemy outgoing damage keeps its existing curve, because player health was not multiplied by the weapon curve. Armor growth is `1 + .025x`.

Attribute growth ramps from zero at level 5 to full strength at level 15. Extra attack is `(.5s + .004s²) × ramp`, where `s = max(STR - 15, 0)`. Spell-power percentage is `(.7i + .006i² + .2 × max(WIS - 10, 0) + .25 × average staff/wand damage) × ramp`, where `i = max(INT - 15, 0)`. Percentage-based lightning, frozen explosions and Thorns do not apply the new spell-power multiplier again to damage that already inherited growth. Tempos inherit the relevant derived stats and receive a matching spirit weapon budget.

### Measured examples

These are deterministic averages of 300 successful, noncritical hits against a same-level Hollow Soldier, with level-appropriate Elite equipment, seed 2201, and two primary attribute points plus one secondary point per level. They include the target's actual defenses and elemental affinity. The comparison attack is a 1.9× heavy attack for weapon classes and a leveled Firebolt for Mage. They are representative builds, not guaranteed damage for every weapon or enemy.

| Class | Level | Normal hit | Heavy attack / Firebolt | Enemy HP |
|---|---:|---:|---:|---:|
| Knight | 25 | 405 | 770 | 1,611 |
| Knight | 30 | 502 | 953 | 2,617 |
| Mage | 25 | 494 | 465 | 1,611 |
| Mage | 30 | 893 | 622 | 2,617 |
| Ranger | 25 | 382 | 725 | 1,611 |
| Ranger | 30 | 441 | 838 | 2,617 |
| Shadowblade | 25 | 165 | 313 | 1,611 |
| Shadowblade | 30 | 285 | 542 | 2,617 |

Fast daggers have smaller individual hits; attack speed and skill behavior still matter. The complete automated matrix includes levels 5, 10, 15, 20, 25, 30, 45 and 60. Criticals and strong elemental matchups can exceed these numbers. This is not a claim that every class has equal sustained DPS.

### Ragnarok references

Ragnarok's useful pattern is the combination of attribute attack, weapon attack and separate combat modifiers, with meaningful roles for STR, INT and DEX. It is not simply a larger damage multiplier. Official stat descriptions: [Ragnarok guide](https://ro.gnjoy.asia/gameguide/?gg=2), [class stat bonuses](https://renewal.playragnarok.com/gameguide/classes_bonus.aspx). The [rAthena status implementation](https://github.com/rathena/rathena/blob/master/src/map/status.cpp) also separates base attack and weapon attack and implements different renewal/pre-renewal attribute curves. It is a primary source for that emulator, not proof of the exact current official-server formula. Beyond Heroes uses its own curves above.

## Earned class ranks

Promotions require all listed achievements, the minimum level, cumulative story deeds and the existing gold fee. Repeated kills of one champion or clears of one dungeon do not satisfy the distinct-content requirements. Jobs count only when handed in. The Character window and guild promotion text show actual progress.

| Class | Minimum level | Jobs handed in | Different champions | Different dungeons | Highest dungeon tier | New story deed |
|---|---:|---:|---:|---:|---:|---|
| E | 1 | 0 | 0 | 0 | — | Join a guild |
| D | 6 | 2 | 0 | 0 | — | Receive Maelis's orders |
| C | 12 | 5 | 1 | 1 | — | Witness the Catacombs ritual |
| B | 20 | 10 | 3 | 2 | — | Defeat Kethrax |
| A | 32 | 20 | 5 | 4 | — | Defeat the Hollow Warden |
| S | 45 | 40 | 8 | 8 | 4 | Previous deeds |
| SS | 55 | 75 | 12 | 12 | 5 | Previous deeds |
| SSS | 60 | 120 | 16 | 20 | 5 | Previous deeds |

Old saves reassess purchased ranks once against recorded achievements. Removed promotion fees are refunded; inventory, equipment, XP and victories are preserved. Already equipped items stay equipped; future equip actions use the new requirements. Save round-trips cannot repeatedly refund fees. The player's level cap remains 60. Class SX and level 200+ are reserved for the story's legendary NPCs. Multiplayer protocol 8 prevents mixing the old and new rules.

## Completed story work

The opening now runs through Maelis, Captain Hald, Wyman Outpost's reliquary and Paul David in Olivar. The shard reveals the story of Aljay, Roydo and Paul David. Aldric opens the Marsh Gate, leading to the Weeping Causeway and Kethrax. His defeat triggers the chain-breaking scene and a report to Paul David, before the existing forest, temple and Hollow Warden chapter.

Includes the four new character models, legendary weapons, textures, animations, portrait, SX emblem, story music and five cutscenes. The main flashback permits skipping individual scenes but has no Skip All control. Quest items have inventory models and icons. Delayed victory scenes cannot start after leaving the relevant map or changing heroes. Opening dialogue no longer gives the old introduction's reward a second time. The lakeside route reaches Paul's updated position, and the Marsh Gate route is verified with the gate open.

The chapter ends with discussion of the Black Spire. The rescue across the sea is a later chapter, as specified in the recovered story contract. See `LORE.md` section 10 and `work/lemondev/bh-021/contracts/story.md`.

## Verification

- Focused regression: 24,396 checks, zero failures across 14 suites covering the story, progression, navigation, dialogue, loot, damage, guilds, stats, items, inventory, companions, enemies and networking.
- Additional progression checks cover ordinary spell scaling and prevention of double scaling for percentage damage.
- Rendered live-game check verifies the Character window, Paul David in Olivar, an actual weapon hit that Kethrax survives, his defeat flag, the victory cutscene and return of player control.
- The wider initial run had 35,823 checks and 22 failures. The story integration failures and stale original-roster assertion were fixed and their suites passed. Eight assertions in the existing `test_enemies2` suite remain outside this change: War Totem comparisons and several timed live enemy behaviors. The separate old starter-gear class-balance gate also remains failing; this update does not claim equal class DPS. See local logs for exact failures.
- Godot still prints some navigation, viewport-sizing and shutdown resource warnings. They are not being represented as clean engine diagnostics.

## Builds

Built with Godot 4.7.2: Windows x64 release EXE with embedded game data, Windows ZIP, and Android ARMv7/ARM64 APK. Android uses the existing debug signing configuration; no release keystore is configured. Physical Android-device testing is not claimed. Artifacts and SHA-256 checksums are under `build/`; logs and screenshots are under `output/`.
