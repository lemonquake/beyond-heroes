# bh-016 contract — 25 levels, the Guild House, player trades

Engine Godot 4.7.2 (Forward+ desktop, Android arm64 APK). Target 1920x1080 desktop and the touch layout. Budget: no
frame-time regression (Perf autoload gates and `test_perf` unchanged), old saves load unchanged (save version stays 4,
new fields optional), no Filipino names (memory rule).

## Components (one owner per file set)

| # | Component | Owner | Public interface | Acceptance |
|---|-----------|-------|------------------|------------|
| 1 | Skill / talent levels to 25 | System | `TreeDef.LEVEL_MAX`, `finalize_levels()`, `rank_power()`, `power_of()`; `SkillDef.power()` | every node of the 8 trees has `max_rank` 25 and keeps its old cap as `base_rank`; ranks <= old cap give the old numbers exactly; level 25 stays finite/sane; levels save and load; a hand-edited 99 clamps to 25 |
| 2 | Guild House exterior | Asset builder (subagent, isolated) | `assets/environment/guild_house.glb`, sockets `door door_light banner_l banner_r sign_light`, `-colonly` | renders without floating pieces / gaps; door on the -Y face; <= 45k tris; matches the halls' style |
| 3 | Guild House interior + NPCs | System/UI | `int_guildhouse`, NPCs `hollis bram sabeth`, `GuildJobBoard` | builds, has entrance, 3 residents grounded, 2 boards, world-map place + door link + road |
| 4 | Miniquests | System | `GuildJobs` (rules), `DataGuildJobs` (templates), `GuildJobsWindow`, dialogue services `guild_jobs*` | board of 4 per guild at every level; membership-gated accept; max 3 carried; progress by kill/map/elite/camp/stage/champion/herb/craft/visit; gold paid once with tier bonus; saves; malformed jobs dropped |
| 5 | Player trade | System/UI | `TradeRules`, `Net.request_trade / trade_prompt / trade_set_offer / trade_accept / trade_cancel`, `TradeWindow`, PROTOCOL 5 | request -> accept -> offers -> both accept -> atomic swap on both machines; any offer change clears both acceptances; declined/cancelled/closed/left cleans up; locked, favorite and quest items refused; bag-full refused without changing anything |

## Decisions
- Levels beyond the old cap use a diminishing curve (each extra level is worth 0.5 of a normal one; single-level
  majors/keystones/upgrades 0.1) so a node cannot be stacked into absurd numbers; the 60-level point supply is unchanged.
- The Guild House lot is the north-west corner of the plaza. The well and Seris moved (7.4, -10.4) / (7.6, -7.6).
- Guild membership stays the only gate to a guild's jobs; the window joins/transfers with the existing GuildRules fees.

## Benchmark
No commercial benchmark capture is available to this run; the gate is the project's own tests plus runtime captures.
Independent blind review: not performed (UNVERIFIED).
