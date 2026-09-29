# BH-020 completion record

Date: 29 September 2026. Continued the uncommitted BH-018 and BH-019 work from main at `05d8219`.

## Changes

- Preserved all incoming socket/crystal, town, Lape, vault and dummy implementation and assets.
- Fixed a real deferred-dialogue bug: `DialogueBox.close()` cleared the NPC before `_open_socketing()` read the specialist name and shop. Capture the definition while the request is emitted and pass the values to the deferred method.
- Enabled click/tap purchases, reset merchant filters and Buyback when opening another shop, restored missing/newly unlocked unlimited stock in existing saves, and replaced the crystal shop's 99,999-minute refresh countdown with an accurate stock explanation.
- Render nearby town labels in front of roofs/geometry. Raised companion labels and their render priority above health bars.
- Exported the previously unfinished Lape character source (six animation clips verified) and the latest smithy, wagon, Wyman and crafting models. Inspected Lape, dummy, vault and shop windows in runtime captures.
- Fixed four stale town road endpoints; the Olivar apothecary destination now uses its accessible customer position rather than a point inside the stall.
- Updated the sanctuary population assertion for Ysolde and Lape.
- Added `test_bh020` and changed the socket capture to exercise dialogue -> socket work -> Buy Crystals -> purchase confirmation -> inventory.
- Created `docs/CHANGELOG.md` and the six-page PDF in `output/pdf`, covering the prior BH-016/BH-017 Git commits followed by BH-018/BH-019 and these fixes. All six PDF pages rendered and visually checked.

## Validation

- Godot 4.7.2, desktop Vulkan on an RTX 4060.
- BH-018: 18 tests, 474 checks, zero failures.
- BH-019: 11 tests, 393 checks, zero failures.
- BH-020: 2 tests, 41 checks, zero failures. Tests cover all three specialists, deferred handoff, stale filters, purchase confirmation, exact gold deduction and saved-stock recovery/unlocking.
- Full suite: 33,245 checks, 20 failures before the final apothecary correction. Eighteen failures are in the same balance/enemy assertions recorded in BH-017: 10 class balance, one outdated enemy-roster count and seven enemy behavior/balance checks. These were not changed to force a green report.
- The other two full-run failures were the apothecary path and an order-sensitive BH-014 separation-grid assertion. After the route correction, reran both entire suites: 23 tests, 1,180 checks, zero failures. No enemy-separation code was changed.
- No GDScript parse/runtime errors in the final full-test log. Existing engine teardown resource warnings remain; rendered startup also logs a minimap transform warning. These are not represented as clean logs.
- Real rendered captures completed for socket services, crystal purchase, Lape appraisal/offers, vault deposit and all three towns' dummies/vaults. The dummy capture recorded nine real attacks.
- Windows release export and Android debug export both returned exit code 0. Android export signed and verified the APK. Package: `com.aljayleodones.beyondheroes`; ARM64 and ARMv7; minimum SDK 24, target SDK 36. Existing application version fields were preserved.
- Windows executable launched successfully through the normal game entry with a hidden test save slot; Vulkan initialized. Native Computer Use window screenshots timed out, so the visual evidence comes from the project's rendered capture scenes. A release-binary attempt to override the entry scene was unsupported by the export template; the normal-entry smoke run was used instead.
- No Android device was attached (`adb devices` empty), so there was no physical-phone playtest.

## Outputs

- `build/windows/BeyondHeroes.exe` - Windows release, embedded game data.
- `build/BeyondHeroes-Windows.zip` - the standalone EXE in a ZIP.
- `build/BeyondHeroes.apk` - debug-signed Android APK, matching the existing local build setup.
- `output/pdf/Beyond-Heroes-Changelog-BH016-BH020.pdf` - checked six-page version history.
- Build hashes and condensed validation results are in `evidence/`. Large raw logs and intermediate projects remain local in ignored `scratch/` folders. Builds and signing configuration stay out of Git.

All test/capture game sessions used hidden save slots 96-99. Vault tests/captures use separate test/probe files. The user's open editor and game processes were not stopped.
