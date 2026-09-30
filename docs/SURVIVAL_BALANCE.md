# HP, Mana and survival balance

- Each STR adds 6 HP; each WIS adds 4 HP; each INT adds 4 Mana; each Spirit adds 3 Mana. Existing Spirit HP and WIS Mana bonuses remain.
- Each level grants 10 stat points and 2 skill points. Talent points stay at 1. Older saves receive the missing 7 stat points and 1 skill point per previously earned level once, without changing existing allocations.
- AGI supplies 2 Evasion per point; DEX supplies 3 Accuracy. Evasion now uses `Evasion / (Evasion + Accuracy)`, capped at 65%. Enemy aimed spells/projectiles marked evadable participate. Unavoidable ground effects remain unavoidable. Character-sheet estimates use the same formula and enemy reference growth.
- Mirror Guard returns 15% of damage received instead of 150%. Enemy Mirror and Thorns damage cannot exceed 8% of the victim's maximum HP per hit, and share a 0.5-second cooldown per victim. Reflections cannot trigger another Mirror reflection.
- Enemy damage grows at half its previous per-level rate after level 25, easing the approach to level 40 and beyond. The milestone damage bonus stops growing at 12%; enemy health growth is unchanged.
- Movement caps after rank and passive bonuses: Shield Bash 8 m, Leap Slam 14 m, Blink 12 m, Vault 10 m, Shadow Step 12 m. Tooltips show these limits. Dash movement cannot overshoot due to a long physics frame, and Shadow Step includes its behind-target offset within the travel limit.

## Verification

The main regression run passed 7,483 checks, including live casts of every active skill, old-save migration, real Mirror/Thorns damage, evasion probability, and level 40–300 damage budgets. The updated balance audit passed 4,467 checks. All 407 scripts compiled.

Additional enemy, dungeon, networking, item, status and Tempo suites ran 35,689 checks. Three old damage-budget expectations were updated for the larger stat-point pool and pass in the separate audit. The remaining nine failures in `test_bh017` and `test_enemies2` also reproduce against the original main source; they concern weapon tempering, totem reference stats and older live enemy fixtures.

## Builds

- `build/survival-balance/windows/BeyondHeroes.exe`: Windows x64 release with embedded game data; headless startup passed.
- `build/survival-balance/BeyondHeroes.apk`: ARM64/ARMv7 APK signed with the existing debug key; v2/v3 signatures verified. No Android device was connected for installation testing.

Builds use Godot 4.7.2. The separate folder avoids replacing the old EXE while it is running. Checksums and verification details are recorded in `output/survival-build-summary.json`.
