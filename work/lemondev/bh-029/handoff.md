# bh-029 handoff (continued 2 Oct 2026)

State: DONE. Pushed to main as 75848de; EXE (build/windows/BeyondHeroes.exe, zipped as build/BeyondHeroes-Windows.zip) and APK (build/BeyondHeroes.apk) built 2 Oct 2026, EXE smoke boot clean.

## User requests this session
- Continue bh-029, send screenshots, **replace the glowing colour with pure white**, then push to main and build
  the EXE and APK.

## White glows (done)
- `MaterialLibrary.ZR_GLOW` (white). `BH_Wire` / `BH_Glyph` / `BH_Blackwire` are white; the corrupted Heartwire is dim
  (energy 1.6), restored is bright (`WIRE_GOLD` kept as the name, now white at 4.2). Zarael map lights, pylons, Dawn
  Engine, cutscene flashes, hazard colours, Vault theme glow/rune colours: white. Vault torches stay firelight.
- Monster palettes: `MaterialLibrary.zr_white_palette()` forces `BH_Emissive`/`BH_WeakPoint` white on every Zarael
  monster and Agdao NPC model at runtime; the M1 sources were switched to white and rebuilt; `brief_models.md` and
  `brief_npcs.md` tell builders to author white.
- Story text no longer says the wire burns violet or gold: corrupted = "stutters / flickers", healthy = "steady".
- `zr_gate_obsidian` seams rebuilt with `BH_Glyph` (white) instead of `BH_Lava`; `BH_CliffOchre` added to ENV.
- Agdao and the four wild maps: magenta environment tint halved toward neutral.

## Other fixes this session
- Zarael atlas re-laid to the real map layout (1 m/px, `DataIsland.ZARAEL_*`, `show_island`, `island_of`); the M map
  shows the hero's island. test_island accepts Zarael maps and the ship link.
- Agdao navmesh: roof footbridges crossed both grand stairs at head height (houses moved to z -1 / -27); the Crown of
  Steps sat 8 m too far south so its stair floated over the terrace below (pyramid now at z -70; Wirekeeper at z -67).
  Gate/harbour/Vault-trail road ends moved off arches. `probe_bh029_nav.tscn` checks it.
- test_bh029 API fixes (HeroData setup, DialogueSession begin/lines/choices).
- CharacterVisual falls back when a GLB exists but is not imported yet.
- Corvessa (provisional east island) replaced by Zarael in game text and LORE; LORE §11, MAPS.md, CHANGELOG BH-029.

## Builders
- All done: M1–M6 (30 monsters), N1 (six Agdao NPC models: terax, wirekeeper, ilsa, agdao_porter/vendor/elder).
  Evidence in `evidence/models_m1..m6/` and `evidence/npcs/` (M2–M4 previews copied from their scratch dirs).

## Fixes this session (continued)
- Zarael boss `model_scale` 1.7–1.9 → 1.0 (1.1 Leash-Abbot): the models are authored at full size (4–4.6 m); the old
  scale drew Varrogh ~8.7 m tall.
- Monster lineup capture moved from Wyman's night arena (grey models read moon-blue) to the Glasswire Barrens.
- Terax cutscene: Terax now faces the hero walking up the pier (yaw 0); the Crown of Steps close-up moved to his front.
- `quest_broken_link` item model (`tools/blender/characters/zarael_quest_items.py`).
- test_npcs: Ilsa (Wyman + Agdao twin NPC) allowed to share her name; Ysenne's unknown `heal` service removed (her
  title still gives the healer map icon). test_bh029: an unimported GLB counts as missing instead of crashing.
- CHANGELOG: NPC models, CDR cap 50% + 1 s minimum cooldown, tree fit, minimap FX layer, water/mist fixes.

## Tests
`evidence/tests_final.txt`: only the known baseline fails (test_balance x8, test_enemies2 x8, test_inventory_overhaul x15,
test_bh017 Fore-Tech x1). The full run used to hang in test_perf after test_npcs: Perf._restore_lights walked a
Dictionary whose keys included freed lights (Godot 4.7 hangs); fixed (iterate keys(), prune freed). The runner prints
`[TRACE] suite.test` per test when BH_TEST_TRACE is set.

Blind benchmark vs a commercial reference: UNVERIFIED (no independent critic run).
