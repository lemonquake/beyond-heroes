# Tempo, armory and cheats contract

Baseline: 8cde5d1 on main, 2026-09-30. Preserve pre-existing untracked output/depth-* evidence.
Engine: existing Godot 4.7.2; Windows and Android exports. No engine migration.

Scope: bounded Tempo layout, two-handed bow/crossbow exclusion, ten distinct designs each for bow/crossbow/dagger/sword/axe, three specified plus ten new cheats, complete cheat PDF, main push, EXE/APK.
Owners: tempo_ui (Tempo window + dedicated captures/tests), weapon_designs (item catalog + procedural weapon assets), weapon_mechanics (equipment/combat/category integration), root (cheats/PDF/integration/build).
Invariants: window and close control fit viewport; all bag cells reachable; no two-handed/offhand combination through equip/swap/load; full bags never lose displaced gear; new designs have distinct models/icons and are obtainable; codes normalize case/space and match whole chat messages; item gifts are atomic; cheats survive normal serialization.
Evidence: supplied obstruction screenshot is UI baseline, existing game weapon models are asset baseline. No supplied commercial comparison exists; commercial superiority remains unverified. Fresh independent reviewer receives only anonymous rendered evidence when ready (instruction-enforced filesystem isolation).
Render checks: 1920x1080, 3840x2160, 1280x720 and touch landscape; actual engine captures. New weapons use established procedural Blender GLB/icon pipeline. Tests: dedicated regression suites plus impacted existing suites and full suite. Equipment transitions are discrete (10,000 simulation steps N/A); projectile checks are applicable if mechanics change.
Performance target: 60s representative rendering, p95 <=16.67ms, record p99/max and hardware when measurable. Physical Android performance remains unverified without device. Export success is not device playtest.
Budget: maximum 8 build/review passes per component; repeated same valid rejection twice stops that component. No quality or FPS claims without measured evidence. Context usage unknown.
Publishing/build authorization: user explicitly requested push all to main and compile EXE/APK. Keep build binaries in existing ignored build/ directory, record hashes; push task source, assets, PDF and concise evidence, preserve unrelated local files.

## Added boss-set component (user steering)

15 complete visually distinct boss sets: Dragonforge; Truth of Raikuru; Crimson Glory; Grievance of the Fairy; Wailing Mistress; ten additional names. Available from actual boss level30, not a level28 boss whose item level is raised. Each eligible kill grants exactly one special set piece. Selection remains random; owning part of a set raises chances of that set and of its missing pieces. Ordinary drops retained under the stated interpretation. No generic shop/chest/craft/elite leakage. Equipment visuals must appear worn in world and preview, with matching item assets/icons; distinct shape and theme beyond recoloring. Source/loot owner weapon_mechanics; art/wardrobe owner tempo_ui. Weapon builder finishes original armory first; root integrates all into same final source/build/push.

Independent-review limitation: attempting to spawn a fresh context reviewer on2026-09-30 returned agent thread limit reached. Existing builders have project context and cannot count as blind critics. Self inspection and objective tests remain valid; blind/commercial comparison stays UNVERIFIED. No publication delay or user approval implied by this evidence limitation.
