# bh-016 handoff — 25 skill/talent levels, the Guild House with paid miniquests, player trades

Status: **IMPLEMENTED — UNVERIFIED for independent review.** Verified in the real runtime on this PC (Godot 4.7.2,
1916x1011 desktop, touch layout at 1920x1080, two-process multiplayer over 127.0.0.1). No blind critic ran (no commercial
benchmark capture available; the builder's own tests and captures are the only gate), and no phone test (APK rebuilt only).
Contract: `contract.md`. Full suite: `evidence/tests_final.txt`.

## 1. Every skill and talent goes to level 25
`TreeDef.finalize_levels()` (called for all 8 trees in `Database._init`) sets each node's `max_rank` to 25 and remembers the
old cap as `base_rank`. Effects are computed from `TreeDef.rank_power(rank, base)`: identical to the rank up to the old cap
(so every existing build and every existing save behaves exactly as before), then each extra level is worth **0.5** of a
normal one (single-level majors, keystones and one-off upgrades: **0.1**, because their numbers are drawbacks and counts,
not steps). Used by talent modifiers, passives, upgrade deltas, synergies, `SkillDef.resolve()` and `mana_at()`. Examples:
a 5-rank skill at level 25 counts as 15 ranks (Firebolt hits ~2.4x as hard as at level 5, not 3.5x); a keystone at level 25
is 3.4x. UI says "Level x / 25" (tooltips, tree pips, "Next level"). Saves clamp to 25. **Points are unchanged** (1 skill + 1
talent point per level, cap 60): reaching 25 in a node is a real commitment, not something to do everywhere. Say the word
if you want more points per level or a different taper (`TreeDef.TAIL`, `TAIL_SINGLE`).
`test_balance`'s builder now spends only up to the old cap, so its known baseline (11 failing lines, same as bh-015) is
unchanged; a level-25 hero is not part of that band test.

## 2. The Guild House (Malasugue)
- **Exterior:** Blender asset `guild_house` (`tools/blender/environment/assets_guildhouse.py`, built by an isolated asset
  subagent; 28,982 tris; sockets door / door_light / banner_l / banner_r / sign_light), signboard with both crests, blue
  Swordfin banner on the left, violet Lantern banner on the right. Lot: north-west of the plaza at (-11, -10), door facing the
  plaza. The town was too crowded for a full-size building anywhere else, so **the old well and Seris moved** to (7.4, -10.4)
  / (7.6, -7.6). Evidence: `evidence/guild_house/*.png` (Blender), `evidence/shots/sanctuary__guild_house.png` (in engine).
- **Interior** `int_guildhouse` (20 x 12 m): steward **Hollis Varnay** at reception, **Bram Ostler** at the Swordfin counter
  (west), **Sabeth Wynn** at the Lantern counter (east), two banners each side, and a **job board** (interactable) on each
  side wall. World-map place `town_guildhouse` + road `Guild Row` + door link; the minimap shows it as a place.
- **Choose a guild:** the Guild House window has one tab per guild (crest, motto, perks). A non-member sees **Register with
  … (fee)** / **Transfer to … (fee)** (the existing `GuildRules` fees: 50 first time, 300 to switch; the tier is kept).
- **Miniquests (`GuildJobs`, `DataGuildJobs`, `GuildJobsWindow`):** each guild posts 4 jobs at a time for the hero's level
  (Swordfin: map culls, elites, camps, stage sweeps, champions; Lantern: herbs, map surveys/ledger runs, crafting,
  specimens, camps, stages). Only a member of the posting guild may take them; up to 3 carried at once; progress counts as
  you play anywhere (kills, elites, `camp_cleared`, `stage_cleared`, `miniboss_defeated`, `herb_gathered`,
  `item_crafted`, `map_loaded`); **Hand In** pays gold once, +5 % per guild tier; a fresh posting replaces each one taken or
  finished; Drop asks first. Saved in `HeroData.guild_jobs` (optional key: old saves load unchanged; malformed jobs are
  dropped on load). The steward and both clerks open the boards from dialogue (`guild_jobs*` services).

## 3. Player trades (`Net` protocol 5, `TradeRules`, `TradeWindow`)
Click an ally's hero in the world (mouse; `Player._ally_under_cursor`), or press **Trade** on their party frame or next
to their name in **Multiplayer** (works on phones) -> "Send a Trade Request?" -> they get Accept / Decline (30 s) ->
the Trade window opens on both sides: click bag items to offer them (up to 10), type gold, **Accept Trade**. Nothing
moves until both accepted the same two offers; **any change clears both acceptances**; a stale acceptance (given for
older offers) is ignored by revision numbers. On both-accepted each machine re-checks its own hero (gold, items still in
the bag and unchanged, room for what arrives), tells the other, and swaps atomically (`TradeRules.swap`); a failed check
cancels both with the reason and changes nothing. Locked, favorite and quest items are refused; incoming items lose the
sender's lock/favorite/junk flags; incoming gold is capped and malformed items are dropped. Closing the window, the other
player leaving, or the session ending cancels. The hero is saved on completion. PROTOCOL 4 -> 5 (older games cannot join).
Probe: `tests/tools/net_probe_trade.gd`, host 20/20 and client 15/15 (`evidence/net/trade_*.txt`).

## Tests
New suite `test_bh016` (15 tests, 1,394 checks, all pass). `test_npcs` now expects 9 interiors; `test_bh015` accepts
protocol >= 4. Full run on the final revision: see `evidence/tests_final.txt` — the failing lines are the bh-015
baseline (test_balance x11, test_enemies x1, test_enemies2 x8).

## Not done / next
- Independent blind review and a phone test.
- More point income for 25-level builds, if wanted; a quantity prompt for partial stacks in trades (a stack is offered whole).
- Per-guild reputation ("standing") beyond the flat tier bonus.
