# Touch component builder record

Status: IMPLEMENTED — UNVERIFIED. Pass 2 of at most 8; no acceptance claimed. Test execution is coordinated by the integration owner to avoid shared Godot import-cache conflicts. Builder context telemetry: unknown.

Scope: Android GUI parity and held-input lifecycle, with mobile presentation caching. Simulation/combat rules and model/performance-owned files were not edited. No 10,000-step simulation gate applies to this presentation/input adapter.

Changed source:
- game/src/ui/mobile/touch_gesture.gd (new): one target-owned gesture tracks the actual GUI target and local point, waits to resolve touch primary on release, performs a still hold's secondary action once, and cancels after movement, multiple fingers, native contact cancellation, transform/scroll, hidden target, new modal, or lifecycle reset. Real mouse events use existing paths.
- game/src/ui/mobile/touch_controls.gd: raw-contact routing replaces global synthesized right-clicks. Application/window focus, pause/background, visibility, restart/player replacement, and exit release actions and clear aiming/pinch state. Multiple fingers holding the same combat button retain ownership until the final finger releases.
- game/src/ui/mobile/touch_button.gd: transformed hit tests and no-op layout guards.
- game/src/ui/widgets/item_slot.gd; game/src/ui/hud/skill_button.gd; game/src/ui/widgets/tree_view.gd: target-owned touch dispatch into existing owner actions. Item replacement, skill replacement, tree page/hero changes cancel pending work.
- game/src/ui/windows/inventory_window.gd: holding a bag/equipment item selects it and opens Item Options. It reuses the action bar's labels, handlers and enabled states (including protected items and belt assignment), without equipping/using first. Mouse right-click quick use is preserved. The menu closes with the window.
- game/src/ui/windows/shop_window.gd: hold a stack to choose quantity without an initial purchase; touch selling reuses the existing protected-sale path. Touch guidance updated.
- game/src/ui/windows/skills_window.gd; game/src/ui/windows/talents_window.gd: readable tap/hold instructions and numbered touch skill assignment.

Presentation work: touch cooldown/state refresh is bounded to about 30 Hz while input and action releases retain engine event/frame rate. Main weapon and skill icons update when their identity changes. Belt previews/count scans are cached until inventory events, a hero change, or belt binding change. Orb positions are laid out only when their rectangles change. The static stick and unchanged Interact button no longer request redraw every frame. These are structural overhead reductions, not rendered FPS claims.

Regression suite: game/tests/unit/test_touch_parity.gd. It routes Android's raw-touch + emulated-mouse event pair through actual SubViewport GUI dispatch instead of calling the target's _gui_input. Ten cases cover (1) tap/hold exactly once plus real mouse, (2) moving away and returning, canceled touch, and multitouch, (3) scaled/translated targets and scroll/layout/visibility/modal/focus invalidation, (4) inventory context and protected options, (5) skill/talent refund, (6) combat input release on modal/focus/restart/hide/cancel and shared button ownership, (7) merchant quantity, (8) belt context and chat Send/X buttons, (9) belt preview reuse and invalidation, (10) two fingers holding a channel/nonchannel skill in both release orders.

Reproduction command, to be run by integration owner:
A:/Installer/Godot_v4.7.2-stable_win64/Godot_v4.7.2-stable_win64_console.exe --headless --path output/hero-port-20261026/candidate-game res://tests/run_tests.tscn -- --only=test_touch_parity,test_inventory_overhaul,test_items,test_shops_dialogue,test_skills,test_chat_upgrade,test_bh032,test_control_limits,test_character_skills_layout

Actual execution at this record revision: not run by builder. Integration owner is importing the isolated QA project; its src/tests/assets/.godot junctions refer to the shared source. Candidate user data is isolated through its project settings. No commits made.

Remaining gates: compile/import, actual test results, 1080p/4K/mobile viewport captures of the context menu, mouse regression, independent review, combined integration, and physical Android touch/keyboard/refresh checks. The desktop event harness cannot certify physical-device gesture delivery, software-keyboard behavior, or touch latency. No benchmark or independent acceptance is claimed.


Pass 2 correction: independent correctness review identified shared-skill release ownership (latest finger owned aim while early return kept that stale index). The release path now transfers aim and drag direction to the remaining holder before returning; the final holder releases a channel or casts a nonchannel skill. A Viewport-event regression covers both release orders for Whirlwind and a nonchannel skill. The raw audit also accounted for embedded PopupMenu open/close transitions, which UIRoot.any_window_open does not itself report; these now release gameplay input and discard old GUI contact ownership. Source frozen pending central compilation and test results.
