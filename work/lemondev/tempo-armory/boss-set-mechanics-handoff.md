# Boss-set mechanics handoff

State: IMPLEMENTED — UNVERIFIED (root integration, art inspection, independent review and release build remain).
Component budget: pass 1 of maximum 8; no valid blind rejection/acceptance yet. Context usage telemetry unknown.

DataBossSets contains 15 collections and 187 pieces. Complete loadouts are 12 pieces for two-handed weapon sets or 13 with a shield for one-handed sets. ItemBaseDef.equip_slots enforces specific left/right/accessory slots; Equipment and Tempo auto-slot paths honor them. Master rarity and Class D rank gating preserved; every piece starts at level 30, needs 32 of its class attribute, and uses existing item-level damage/defense/affix scaling. Set bonuses accumulate at 3, 6 and full; each collection's full effect has a distinct existing runtime flag.

Loot.equipment_for adds exactly 1 special boss-set piece and suppresses that encounter's generic set roll, preserving ordinary equipment. Eligibility uses actual enemy level>=30, then a true boss archetype, repeatable raid_only Usurper or named depth_guardian. Other minibosses/elites/normals excluded. Repeatable bosses are deliberately included because dungeon lords never respawn. random_special excludes boss_exclusive metadata; standard pool and crafting already exclude set pieces. All 15 collections remain possible for every class.

Weights: class affinity 2x; currently owned incomplete set 4x; within chosen set each missing piece 6x vs owned 1x. Current ownership scans bag,worn,Tempos,SpiritHall,pending recovery plus injected storage. Loot injects HeroVault.shared().cells only for the local Game.hero. Extra copies do not increase weights. Unpicked ground loot and sold pieces do not count. Selection functions are pure and do not read or write saves.

Verification: Godot 4.7.2 headless, output/boss-set-tests.log exit 0:7 tests, 5959 checks, 0 failures. Seed 303015 real 10,000-drop sample: all 15 sets observed; ownedcrossclass Truth of Raikuru 1,821 vs emptycrossclass Wailing Mistress 484; missing 1,555 vs owned 266 among equal six-piece groups(~5.85x). Crossclass progression and duplicate possibility both confirmed.

Targeted final regression output/boss-set-regressions.log exit 0, clean: boss_sets 5,959 + crafting 680 + crossbows 10,766 + dungeon_growth 22,207 + inventory_overhaul 2,035 + items 2,477 = 44,124 checks, 0 failures. test_dungeon_growth was updated to allow randomized boss_exclusive collections while preserving its strict classfit check for ordinary Guardian gear. Dedicated new tests independently enforce exactly one piece, level 29/30 transitions, complete equipment/bonuses, ownership and no merchant/cache/craft/general-pool leakage. JSON copied to output/boss-set-regression-report.json.

Player documentation: docs/BOSS_SETS.md with all 15 names, weapons, classes, fullbonus descriptions, farming rules, exact odds, slots and Master/Class D gates.

No commits. Source ownership returned to root. Art owners handle model/icon completeness and actual equipped rendering. Pure loot distribution has no continuous physics step requirement; the 10,000-drop sample is not a frame-rate measurement. Existing crossbow 10k-step and 500-projectile tests remain passing. No commercial mechanics benchmark available; do not claim Gauntlet VERIFIED until required root evidence/review exists.
