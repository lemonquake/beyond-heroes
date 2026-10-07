# Handoff — bh-041 (2026-10-07)

Multiplayer trades fixed, Debug access swept, Tempo commands, Lape's new table and the Eschaton tier (470 new
pieces), Inventory/Skills/Talents windows that stay on screen. **Online version (protocol) 22**: everyone needs this
`build, and the official server must be restarted with it.

## What you need to do now

1. **Restart the official server** so it loads the trade fix and protocol 22 (it runs from this folder's source):
   double-click **Stop Official Server.cmd**, wait for it to finish, then **Start Official Server.cmd**.
   - Players still on the old game will be refused with "Your game is older than this one (online version 22 ...)".
   - A separate ``build\server\beyond-heroes-server-92e16ae8b9-windows\bin\beyond_heroes_server.exe` was also running on
     this PC (opened from Explorer). It is the old packaged server, not the one your friends use. Close it if you
     don't need it.
2. **Give your friends the new game**: `build\windows\BeyondHeroes.exe` (741 MB, single file). Send it to them; it replaces their old one.
3. **Trade once with a friend to confirm**: click their hero → Trade, both put something on the table, both press
   Accept. On the official server the window now says "Completing the trade…" for a moment, then both bags update.
   If one of you cancels or anything goes wrong, the trade is simply cancelled and neither player is disconnected.
4. **Debug access**: every character's Debug console was turned off once (on first load of this `build). Type
   `azrin azrael` again on a character that should have it; it stays from then on.

## 1. Trading (the bug and the fix)

**What happened.** On the official server, both players accept, and each game saves to the server and then sends
its approval. Whichever approval arrived first created a pending trade that **blocked saves for both characters**.
The slower player's own save before approving was refused until it gave up (20 s), so they never approved. The faster
player kept waiting for the 45 s expiry, and the game then treated any unconfirmed trade as fatal and disconnected
them. Your server database shows exactly this on 2026-10-07 06:24: one approval, the trade expired, and that player
rejoined a minute later. A friend playing over a VPN (the 26.x address in the logs) makes the race happen every time.

**Fix** (server `server/service.py`, client `official_service.gd`, `net.gd`):
- Only a character that **has already approved** a pending trade is held from saving, so the slower player's save
  goes through.
- New `/characters/trade_cancel`: either side withdraws at once. It also blocks a late approval from restarting a
  trade that was already withdrawn. Mismatched offers now cancel immediately instead of waiting out the expiry.
- The client is no longer fatal on a cancelled trade: nothing changed hands, play goes on. It is fatal only if the
  server stops answering entirely.
- Each side sends the server exactly the item records it sent and received. The new bag is written from the saved
  one, so no item is decoded and re-encoded on the way.
- Other fixes:
  - A Trade Request has its own question box, so another prompt can no longer swallow it.
  - Once both players accept, the trade window cannot be closed from one side.
  - Offers are size-checked.

**Verified**:
- `python -m server.integration_probe --godot <Godot> --stages=trade --output output/bh-041/official_trade`: two real
  clients on a dedicated server trade equipment while one is "far away" (1.5 s latency), plus a mid-confirmation
  cancel. Both stages pass with clean logs.
- **Against the old server the same probe fails** ("the trade did not complete"), which is the original bug.
- Custom games: `net_probe_trade` passes 35/35 on host and client.
- Server tests: 33 in `test_service`, plus 6 new ones for the race, cancels and mismatches.

## 2. Debug sweep

`HeroData.DEBUG_SWEEP` / save key `debug_sweep`: a save from before this `build loads with the Debug console locked.
`Game.reset_debug()` also turns every Debug switch (God Mode, One-Hit, Freeze Monsters, multipliers, drop floor) off at
the start of every session. To sweep again in a future update, raise `DEBUG_SWEEP`.

## 3. Tempo commands

A toggle over the Tempo frames on the HUD (click it, or press **Y**; rebindable in Settings), and Aggro / Defend /
Passive buttons at the top of the Tempo window. The order is saved per hero.
- **Aggro**: hunts every monster within 16 m of the hero, even idle ones; chases up to 24 m.
- **Defend**: how Tempos always fought; fights what threatens the hero or attacks them.
- **Passive**: never attacks; follows, dodges danger and still heals.

## 4. Lape the Ancient and Eschaton

Full design: **docs/ESCHATON_AND_LAPE.md**. In short:
- **Eschaton** is the new tier above Primordial (x2.30 base power, Unmaking). Only Lape makes it, from lots of the
  highest tiers: 63 % per look with three Primordial pieces.
- The catalogue covers ten of everything for every class: 40 collections, 10 shields, and ten weapons of every type
  each class masters. That is 470 pieces with models and icons, built in Blender in mirror chrome.
- Lape's table now deals 3-5 offers of seven kinds, steered by what you lay down, and a paid **Look Again** draws a
  new set.
- Drawing an Eschaton piece plays the eclipse reveal.

## 5. Windows that stay on the screen

- **Skills / Talents**: with Class Transcendence's pages plus locked previews, the page tabs ran off the right edge
  and pushed the window and its sidebar off screen. The tabs now wrap, with the page text on its own line.
- **Tooltips**: a tooltip taller than the screen (an Ascendant/Fabled piece with every socket, beside the equipped
  one) flows into columns, and shrinks only as a last resort.
- **Inventory**: the Item Sets list under the doll scrolls. Several worn Ascendant sets used to push the belt off the
  window.
- **Safety net**: every window's content is now clipped to its frame. `UIWindow.overflow()` and
  `capture_bh041_ui.tscn --sweep=1` found four more windows that were secretly stretching, all fixed: Lape, Sockets,
  Your Guild and Hero Register. All 26 windows fit in PC and touch mode for every class at both Transcendence stages.
- Also fixed: an 8-socket item lost a socket on loading (saves capped sockets at 7).

## Tests

- New suite `test_bh041` (15 tests, 2,528 checks) passes, as do the updated `test_bh019`, `test_bh034`, `test_items`,
  `test_bh016`, `test_tempos` and `test_loot`.
- Full suite: it was stopped on request after 60 of the suites. 59 passed; the only failure was `test_balance`
  (4 checks), which is inside its known flaky baseline of up to 10. The suites after the 60th were not run.
  Results are in `output/bh-041/tests_final.txt`.
- Server: `python -m unittest server.test_service server.test_hardening server.test_control` passes (49 tests, 1 skipped).
- Not done: an Android `build and new VPS server packages (your server runs from source, so it doesn't need them).

## Builds

- Windows: ``build\windows\BeyondHeroes.exe`, 741,040,904 bytes, sha256
  `2455354fbb06aff52ae82969770269466452c213168ed9c04d1c28f884c710d6` (`--export-release "Windows"`, exit 0; log
  `output/bh-041/export-windows.log`).

## Files

- New:
  - `game/src/data/data_eschaton.gd`
  - `game/src/ui/widgets/eschaton_reveal.gd`
  - `game/src/ui/widgets/tempo_command_bar.gd`
  - `game/tests/unit/test_bh041.gd`
  - `game/tests/tools/capture_bh041_ui.*`, `capture_bh041_game.*`, `trade_roundtrip_probe.*`
  - `tools/blender/items/eschaton_regalia.py`, `eschaton_icons.py`
  - `tools/ui_art/eschaton_frame.py`
  - `docs/ESCHATON_AND_LAPE.md`
- Evidence: `output/bh-041/`. Screenshots: `shots/`, `ui/`; probe logs: `official_trade/`, `trade_probe/`.
- Left alone: `game/tests/tools/friend_hunter.*` and `output/friend-hunter/` were created by another session and are
  not part of this change (not committed).
