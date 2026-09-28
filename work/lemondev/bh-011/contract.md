# bh-011 contract — Mobile waypoints, travel EXP bug, monsters under the bridge, potion belt, multiplayer polish

Run id `bh-011`, 28 September 2026. Engine Godot 4.7.2 (Jolt), Windows 10, RTX 4060. Branch `main`.
Baseline: HEAD 4a66120 (clean). The user asked for the result to be **committed and pushed to main** and the APK rebuilt
(this overrides the standing "leave uncommitted" rule for this run).

## Request (user, verbatim intent)
1. "Massive bug on the mobile version: it won't allow me to use any teleporters." Fix thoroughly.
2. Massively polish the multiplayer mode.
3. Allow the player to bind Q and E to any potion of their choice.
4. "If I use the waypoint/teleport I get random EXP and level up." Fix.
5. (follow-up, screenshot) "Also fix these monsters under the bridge" (Ruined Forest ravine).
6. Rebuild the APK, push all changes to main.

## Root causes (found before any fix, reproduced by probes)
- **Mobile waypoints**: `Teleporter` listened for a raw `interact` *key event* in `_unhandled_input`. The touch Interact
  button presses the action with `Input.action_press`, which never produces an event, so a dais could not be used on a
  phone. Evidence: `travel_probe` touch mode, before: leg 1 FAIL (no dialog, no travel).
- **Travel EXP / monsters under the bridge** (one cause): Godot 4.5+ syncs navigation *regions* asynchronously; only the
  map was forced synchronous, so every spawn-time `map_get_closest_point` returned (0,0,0) and camps fell back to their
  marker's height. Tower-mound monsters spawned inside the hill, fell below y = -40 and `_fell_out()` killed them —
  `Loot` paid the hero XP (520 XP, level 1 -> 2 on the first Ruined Forest arrival). The bridge camp's marker sits in the
  ravine: those monsters spawned under the deck (the user's screenshot). The Forgotten Temple west chapel also spawned
  1.2 m inside a raised floor. Evidence: `travel_probe` PC before (4 deaths, 520 XP), `spawn_audit` on the old code.

## Components
| # | Component | Files | Acceptance |
|---|---|---|---|
| C1 | Waypoints as interactables | `teleporter.gd`, `map_explorer.gd`, `touch_controls.gd` (icon/label) | touch Interact opens the waypoint on every network shrine; PC R unchanged; no double activation |
| C2 | Spawn placement + fall safety | `map_builder.gd` (region sync), `spawner.gd` (ground fallback), `enemy.gd` (`_fell_out`) | every monster on the 5 combat maps stands on the ground; none falls in 4 s; a fall nobody caused pays nothing |
| C3 | Potion belt | `hero_data.gd`, `player.gd`, `belt_picker.gd`, `hud.gd`, `skill_button.gd`, `inventory_window.gd`, `touch_controls.gd`, labels | each belt key: auto (strongest draught) or any consumable; saved; old saves default; HUD + touch orbs show the binding |
| C4 | Multiplayer polish | `net.gd` (protocol 3), `net_avatar.gd`, `ping_marker.gd`, `party_frames.gd`, `multiplayer_window.gd`, `pause_menu.gd`, `confirm_dialog.gd`, `game.gd`, `character_visual.gd`, `input_setup.gd`, docs | party frames; travel requests Go/Stay; Regroup; revive; ping; connect timeout; Rejoin; Send Home; join/leave notices; host death does not reload the shared map; fallen avatars stay down |
| C5 | Tests/tools | `test_bh011.gd`, `test_net.gd`, `travel_probe`, `spawn_audit`, `net_probe_party`, `capture_belt` | suite 0 failures; compile_all 0 failed; probes PASS |

## Benchmark
No commercial reference was supplied for these fixes/features. Mechanics are judged by explicit invariants (above) and
two-instance runtime probes. The blind A/B critic gate was not run (no independent reviewer requested): visual polish is
**UNVERIFIED** against a benchmark. Real Android phone: not available here (APK built, not device-tested).

Budget: max 8 build/review passes per component.
