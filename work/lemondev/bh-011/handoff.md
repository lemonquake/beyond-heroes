# bh-011 handoff — Mobile waypoints, travel EXP bug, monsters under the bridge, potion belt, multiplayer polish

Status: **IMPLEMENTED — mechanics verified by tests and two-instance probes; blind benchmark review and real phone
UNVERIFIED.** Committed and pushed to `main` at the user's request. APK rebuilt: `build/BeyondHeroes.apk` (debug, arm64 +
armv7, 216 MB, exported 28 Sep 2026 09:18, `evidence/apk_export.log`).

## What changed
| Area | Change | Files |
|---|---|---|
| **Mobile waypoints** (bug) | The dais only heard a raw key *event*; the touch Interact button presses the action without one. Waypoints are now ordinary interactables (like doors and NPCs), so R, a pad and the touch button all work; the touch button shows a waypoint icon and a label that fits ("Use Waypoint (4 places)"). | `world/teleporter.gd`, `ui/mobile/touch_controls.gd`, `world/dev/map_explorer.gd` |
| **Travel EXP / level-ups** (bug) | Godot 4.5+ syncs navigation *regions* asynchronously: every spawn query returned (0,0,0), so camps used their marker's height. On the Ruined Forest tower mound monsters spawned inside the hill, fell out of the world and "died", paying XP (520 XP, level 1 -> 2 on arrival). Regions now sync on the main thread; placement falls back to a ground ray, never the marker height; a monster that falls on its own returns to its camp and pays nothing (a knock-off by a hero still counts as that hero's kill). | `world/map_builder.gd`, `world/spawner.gd`, `actors/enemy/enemy.gd` |
| **Monsters under the bridge** (bug, user screenshot) | Same cause: the bridge camp's marker is in the ravine; the camp now stands on the deck. Also fixed: Forgotten Temple west chapel monsters 1.2 m inside a raised floor. | same |
| **Potion belt** (feature) | Q / E (HP / Mana orbs on a phone) each hold "strongest health/mana draught (auto)" or **any consumable** (elixirs, tonics, wards, salts, Frost Flask, Scroll of Return …). Choose it in the Bag's new Potion Belt row, with "Put on Q / E", by dragging a consumable onto a belt slot, by right-clicking a HUD belt slot, or (PC) hovering a consumable and pressing Q / E. Saved per hero; old saves get the defaults. | `core/hero_data.gd`, `actors/player/player.gd`, `ui/widgets/belt_picker.gd` (new), `ui/hud/hud.gd`, `ui/hud/skill_button.gd`, `ui/windows/inventory_window.gd`, `ui/mobile/touch_controls.gd`, settings/guide/tips labels |
| **Multiplayer polish** (protocol 3) | HUD **party frames** (portrait, name in player colour, HP, distance, ping, "Fallen", other map); **travel requests** (a client's waypoint/door asks the host: Go / Stay; lapses after 20 s); **Regroup** (window, touch button, click the host's frame; respawn menu "Respawn beside <host>"); **revive** a fallen friend with Interact (they stand up at 40 % HP where they fell; death screen explains it); **ping markers** (G / touch "!" button, 5 s, rate-limited); **connect timeout** (10 s, clear message); **Rejoin** the last room; host **Send Home**; join/leave notices; profile (level) updates; **host death no longer rebuilds the shared map** (clients were dragged through a loading screen and lost their fights); fallen avatars stay down (death pose was cancelled by the next snapshot). | `net/net.gd`, `net/net_avatar.gd`, `net/ping_marker.gd` (new), `ui/hud/party_frames.gd` (new), `ui/windows/multiplayer_window.gd`, `ui/windows/pause_menu.gd`, `ui/windows/confirm_dialog.gd`, `autoload/game.gd`, `autoload/input_setup.gd`, `actors/character_visual.gd`, `docs/MULTIPLAYER_GUIDE.md`, `ui/windows/guide_window.gd` |

## Evidence (`evidence/`)
- `travel_touch/`, `travel_pc/` — `travel_probe` (7 waypoint trips through 5 maps). Before: touch leg 1 FAIL (no
  travel); PC 4 monster deaths + 520 XP (level 1 -> 2). After: **TRAVEL PASS** in touch mode (efficiency renderer) and
  PC mode, 0 deaths, 0 XP.
- `spawn_audit.txt` — 138 monsters on 5 combat maps: 0 off the ground, 0 fell, 0 deaths. On the old code the same audit
  reports the bridge camp 7.4 m below its deck, the tower camp falling 178 m (2 deaths), the temple chapel 1.2 m in the floor.
- `party/` — `net_probe_party` two real instances (PC Knight host + touch-mode Shadowblade client): party frames, ping
  seen by the host, revive by Interact, host respawn without reload, client waypoint -> Go -> both in town, Regroup
  35.1 m -> 1.8 m, Send Home: **PASS / PASS**. Screenshots of each step.
- `net_regression/` — the bh-010 `net_probe`: replicas stream, client kills land, summons replicate, a protocol-1 client
  is refused ("Different game versions (host 3, you 1)"), leaving restores the client's own world.
- `belt/` — Inventory Potion Belt row, the chooser, HUD and touch orbs after binding (PC and touch).
- Tests: `tests_final.txt` — **15,760 checks, 20 failures**, all in three suites that fail identically on the untouched
  baseline 4a66120 (`tests_baseline_subset.txt`): `test_balance` (stochastic class power bands, Shadowblade sim 0 power,
  9–11 failures per run), `test_enemies` roster count (expects 16, has 28 since bh-010), `test_enemies2` (8 checks:
  bloater/keg/chain lightning/web/mimic vs the hero, war totem stats). New `test_bh011` (6 tests, 45 checks) passes;
  `test_net` passes. compile_all: 245 scripts, 0 failed.

## Save slot incident (pre-existing test leak, now fixed)
The full suite run at 08:42 wrote the test hero "Crafter" (Knight, level 5) into `saves/slot_0.json` (the menu's Slot 1):
`test_crafting`'s bonfire rest saved to `Game.save_slot`, which is 0 in a headless run. What slot 0 held before cannot
be recovered here. Fixed in `tests/run_tests.gd` (every suite now saves to hidden slot 99; verified: `slot_99.json`
written, slots 0-2 untouched). Slots 1 and 2 (menu Slots 2 and 3) were not touched.

## Not verified / known
- No real phone here: the touch fixes are verified with the game's touch mode on this PC (same input path); the APK is
  built but not installed on a device.
- The blind A/B benchmark gate was not run (no commercial reference supplied; no independent reviewer requested).
- Pre-existing failing suites listed above were not changed in this run.
- The HUD belt icons look dark because the hotbar bezel art overlays every icon (pre-existing styling, unchanged).
