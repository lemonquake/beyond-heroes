# Balance and gem upgrades: verification

Date: 3 October 2026, Asia/Manila.

Source revision: `7324e7aeea3afa5284295139cb7ae12297c8941b`.

Knockback is limited to 12 m/s, 3 m per episode and 0.75 seconds, with 0.6 seconds of recovery. Throws are capped at 6 m/s and 1 m upward travel. Poise stagger cannot be refreshed and has its own recovery window. Side upgrades have maximum levels of 1 or 4; major talents and keystones have one level. Older saves receive refunds for ranks above the new caps. See `docs/CONTROL_BALANCE.md` for values and affected skills.

Gem Upgrades appear in Recipes at Forges, Alchemy Tables and Workbenches. Four matching loose gems make one of the next tier; Orbital is the maximum. All twelve families are supported. No gold or scroll is required. Locked, favorite and socketed gems are preserved. Ingredient hints describe boss, champion and specialist-shop sources.

## Checks

- Focused skills, crafting, inventory and combat suites: 8,013 checks, no failed assertions.
- Final status/control/network follow-up: 814 checks, no failed assertions.
- Final gem hints, gem upgrades and control suites: 28,086 checks, no failed assertions. These fixed all twelve gem-source assertions found in the broader run.
- Broader run excluding the separately completed class-power simulation: 154,945 checks, eighteen failed assertions before the gem-hint fix. Six remain: arena retreat (two), character-window height (three), and fungal dungeon decoration (one).
- Separate class-power simulation: eight failed power-band assertions. This balance gate also failed in the earlier QA baseline; this update does not resolve overall class balance.
- Server tests: 45 tests completed successfully, one skipped.

The wider Godot runs also emit freed-lambda, navigation, fixture metadata and shutdown resource diagnostics. The remaining failures are recorded in `test-results.json`; this is not a fully passing general release gate.

## Packages

Windows uses the release export and an embedded game pack. Android uses the project's debug signing identity and includes ARM64 and ARMv7. The Windows ZIP contains the current EXE. Checksums, source revision and verification are recorded in `builds.json`. Startup checks cover headless loading; no physical Android device is connected for install or play testing.

All existing changes and map captures requested by the user are included in main. Oversized raw diagnostic logs remain local, with compact results committed instead.
