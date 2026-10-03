# bh-035 — QA, frame time, multiplayer efficiency and balance

Run / component ID: bh-035 (follows bh-034, commit 0437f968)
User outcome: QA and fixes; consistent 60-100 FPS without spikes; efficient multiplayer for an MMO-style game; necessary
balance; push to main; Windows EXE and Android APK.
Engine / platform: Godot 4.7.2 (Forward+ desktop, gl_compatibility mobile), Windows 10 PC (Ryzen 7 5700X, RTX 4060), Android arm64.
Baseline / rollback point: 0437f968 (frozen copy used for A/B runs).

## Components and gates (frozen before candidates were measured)

| Component | Owned files | Gate |
| --- | --- | --- |
| C1 spawn hitch | character_visual.gd | humanoid monster spawn + next frame < 20 ms (spawn_bench); no shared-clip writes after the first spawn (test_bh035) |
| C2 crowd simulation LOD | enemy.gd | 40-monster brawl (perf_probe --stress=40, pc-low 1280x720, vsync off) median frame <= 16.7 ms; attacking / token / knocked / boss monsters never thinned (test_bh035) |
| C3 animation stride LOD | character_visual.gd, perf.gd, npc.gd | same brawl gate; bosses, heroes, avatars and companions never coarse (test_bh035) |
| C4 multiplayer interest management | net.gd, net_codec.gd, net_avatar.gd, server protocol | 6 heroes on one map (integration_probe --stages bandwidth): map owner upload and member down/up at least halved vs baseline; all integration stages and the local probes pass; protocol bumped (19) |
| C5 QA fixes | character_window.gd, data_dungeon_roles.gd, touch_text.gd, probes | the previously failing suites pass; no freed-object deferred errors in probe logs |
| C6 balance | test_balance.gd (+ class data if needed) | balance bot plays finishers like a player; class power within the bh-010 band or the remaining gap documented |

Measurement conditions: perf_matrix.py scenarios (warm-up discarded, 300 frames x spots, 2 runs each), fresh processes, 1280x720,
vsync and frame cap off; "mobile" is the efficiency preset with gl_compatibility on this PC, not a phone.
Benchmark: the user's stated target (60-100 FPS, no spikes) and the bh-034 baseline measured on this PC; no commercial
telemetry is claimed. Pass budget: 8 per component.
