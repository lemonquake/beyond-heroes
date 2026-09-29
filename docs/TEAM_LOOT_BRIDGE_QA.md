# Class loot, independent multiplayer, and Westreach bridges

Verified with Godot 4.7.2 on Windows, 29 September 2026.

## Changes

- Ordinary equipment generation chooses a compatible class pool on 80% of rolls. The other 20% can include any class, so the observed compatible share can exceed 80%. Weapon rolls distribute across eligible weapon families, allowing axes and great axes to appear regularly instead of being crowded out by the larger sword catalogue.
- Minibosses drop 3–4 equipment pieces, all Elite or better; bosses drop 5–6, all Master or better. Every piece fits the recipient's class, including special items, and the first piece is a compatible weapon. Existing level, attribute, and earned-rank requirements still apply.
- Players can use doors and waypoints independently. Each occupied map has one combat owner, including maps the party leader is not visiting. Enemy state, cleared camps, and stage completion survive ownership changes through checkpoints. Personal drops and experience remain personal.
- Team Portal (`P` or the touch/party button) takes a member to the leader. The leader selects a member in Multiplayer. It uses a 1.25-second cast and 10-second cooldown; movement, damage, death, map travel, or disconnect cancels the cast. Destination position is requested when casting completes. Same-map portals move the player without reloading the map. Summon Party remains an optional Go/Stay invitation.
- Reliable appearance updates keep allies visible after map travel. Map and generation checks reject stale combat packets. Revives require a living nearby ally on the same map. Party rows show each player's location and provide Team Portal controls.
- Both Westreach bridge approaches now meet their bridge decks. The river terrain previously left a vertical collision step at the main bridge's west entrance.

## Verification

- `output/bridge-before.log` reproduces the original main-bridge obstruction in all three west-to-east lanes with the original terrain calculation.
- `output/bridge-after.log` passes 12 physical player crossings: both bridges, both directions, three lanes each, plus navigation checks.
- `output/team-final-focused.log`: **22,694 checks, zero failures** across class loot, network rules, auto-loot filters, and bridge traversal. The loot test covers all four classes at multiple levels, guaranteed boss/miniboss equipment, strict special-item filtering, and axe/great-axe availability.
- The three-process ENet probe passed **28 steps with zero failures**, exercising independent exploration, remote map combat, personal kill rewards, both portal directions, cancellation and cooldown, visible allies, stale-packet rejection, ownership handoff, stage rewards, cross-map revive rejection, optional summons, reconnects, owner disconnects, and host shutdown. Final logs: `output/team-host-final.log`, `output/team-scout-final.log`, `output/team-ally-final.log`.
- Four-player desktop and touch layout captures: `output/team-ui-desktop.png`, `output/team-ui-touch.png`.
- Windows release export and startup smoke: `output/team-export-windows.log`, `output/team-exe-smoke.log`. Android debug export and signature verification: `output/team-export-android.log`, `output/team-apk-verify.log`. The APK contains ARM64 and ARMv7 libraries. Checksums are in `output/team-build-checksums.json`.

## Limits and broader regression results

The accelerated full suite ran 57,594 checks and reported 24 failures (`output/team-regression.log`, `output/team-full-report.json`). Fifteen concern the existing class-power balance band, seven concern existing enemy balance/ability expectations, one was an auto-loot test depending on the user's saved filter mode, and one concerns a Tempo target-switch timing assertion. The auto-loot test now isolates its mode and passes in the final focused run. The Tempo suite passed all 3,537 checks at normal speed (`output/team-tempos-recheck.log`). Earlier logs already contain the balance and enemy failures; they are not presented as passing here. The full suite has not been rerun after the filter-test correction.

Android packaging and signing were verified, but no connected Android device was available for a physical-device play test. Multiplayer was exercised with three local processes; internet latency and packet-loss testing remain unverified. Abrupt loss of a map owner restores the latest checkpoint (normally at most one second old); transient AI actions restart. The room still depends on its hosting player: closing the room returns remaining players to offline play at their current maps rather than migrating the ENet server. All players must use protocol 9 builds to join this version.
