# Weapon mechanics handoff

State: IMPLEMENTED — UNVERIFIED (independent benchmark/rendered integration review outstanding).
Baseline: 8cde5d1. Component pass: 1 of maximum 8 (builder corrections and self-checks; no valid critic decision yet).

Implemented shared two-handed validation for shields and all secondary weapons, drag-swap validation, full-bag transactional preflight for Tempo changes, lossless legacy save repair. Displaced legacy pieces persist in Equipment.recovered_items and return as general bag slots open. Player and Tempo equip/unequip/release flows prevent recovery from interrupting their inventory transactions.

Crossbow: type crossbow; representative ashwood_crossbow; two-handed ranged; base 0.82 APS, 26m reach, 45m/s projectiles, heavy shot pierces two additional targets. Registered for Ranger mastery and skills, Archer Tempos, physical shops, crafting, type damage bonuses and bow-related talent. Short bolt visuals preserved for Split Shot. Custom crossbow idle/aim/fire/heavy clips are installed from the existing horizontal spear rig; fire/heavy clips include recoil and reload motion. Artisan models preserve their silhouette on Aether rolls.

Verification: Godot 4.7.2, headless. output/crossbow-tests.log: test_crossbows, test_class_rework, test_inventory_overhaul, test_stats, test_tempos, 16,575 checks, 0 failures. Only warning was CharacterPreview stretch sizing, forwarded to UI owner. output/crossbow-final.log: final weapon state test_crossbows 8 tests, 10,766 checks, 0 failures, exit 0, clean log.

The focused suite exercises equip ordering, shield/secondary rejection, full bags, drag swapping, legacy repair/reload/automatic recovery, 10,000 fixed 1/60s action steps, real player basic/charged/Power Shot bolt release, real rig animation availability and 500 concurrent 1000m/s projectiles against a 2cm wall (all blocked). This is correctness evidence, not a rendered FPS measurement.

Final small changes after the combined suites: include pending recovery pieces in Tempo release/hall release transactions, preserve artisan Aether geometry, update Split Shot text. These are covered by the root's planned final full regression; focused crossbow suite already rerun after these edits. No commits performed.

Remaining: final full suite, gameplay crossbow pose/render inspection, independent review and final export/cold boot are owned by integration. No commercial mechanics benchmark was available to the builder, so that gate stays unverified. Context telemetry unknown. Next action: root integrated validation.
