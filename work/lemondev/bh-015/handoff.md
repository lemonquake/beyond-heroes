# bh-015 handoff — HUD stretch fix, minimap overhaul, rolled names, 65 weapons, independent multiplayer, safer saves

Status: **IMPLEMENTED — verified in the real runtime on this PC (1920×1080 desktop, touch layout at 1920×1080, two-process
multiplayer on 127.0.0.1).** Not reviewed by an independent critic; no phone test (APK rebuilt only).

## 1. The minimap pushed off screen (the user's screenshot)
Cause (reproduced, `evidence/shots/layout_*`, probe `tests/tools/capture_bh015.gd --only=layout`): the right-hand HUD
column is anchored to the top-right corner but grew to the **right** whenever a child needed more width. On a dungeon
the stage tracker's one-line title "HOLLOWROOT WARREN — FLOOR I · Stage" is ~400 px, so the column grew from 306 to
405 px and the minimap (right-aligned in it) went ~100 px off screen. Fix: the column grows left
(`grow_horizontal = BEGIN`), long one-line titles end in "…" (`UITheme.fit_line`), and the HUD re-seats its regions on
resize / minimise-restore / focus / map load (`Hud._relayout`). Probe after the fix: minimap inside at every step.

## 2. Minimap overhaul (`src/ui/hud/minimap.gd`, `src/ui/hud/quest_target.gd`)
- Map fills the frame's opening (the old render disc was smaller than the frame's hole: a see-through ring).
- Three zoom levels (16 / 26 / 42 m), eased; wheel, − / + buttons, `=` / `-` keys; saved (`Settings.minimap_zoom`).
- Icons drawn every frame (12 Hz in efficiency mode): hero arrow + view cone; party arrows in player colour with names,
  low-HP pulse, fallen X with a pulse; their Tempos; pings ripple (right-click the minimap to ping); townsfolk by trade
  (merchant, smith, inn, healer, guild, Tempo-Caller, heroes); waypoints (dormant grey), dungeon gates, stairs, doors,
  exits, bonfires, stations, unopened chests, herbs, uncleared camps; monsters (hunting you = ringed), elites, crowned
  champions, bosses (skull, on the rim when far); loot by rarity.
- Quests: `QuestTarget` finds the objective spot on this map (the NPC, the `Trigger_<done_flag>`, the boss) or the way
  on (RoutePlanner to the objective's new `place`), draws a gold marching trail and a gold rim chevron with distance.
- Rim pins with distance for quest, allies, bosses, portal, exits, pings, tracked route. Hover names. N/E/S/W.
- Effects (floating numbers, sprites, particles, stains) moved to `Perf.FX_LAYER`: the map-load warm-up numbers
  "0123456789!" had been baked into the minimap render until the hero walked far enough for a re-render.

## 3. Names (`src/core/name_forge.gd`)
Prefix + middle + suffix syllables (invented; a refuse list blocks real-world words). The starter Tempo is rolled per
hero (`HeroData.starter_name`; the guide quotes `{tempo}`); roster/gacha spirits roll too. Weapons Common..Advanced get
a forged prefix and/or suffix ("Saltworn Shortbow", "Emberkissed Hornbow of the Grey Ferry") from the item's own seed;
affix names still win their side; Licensed+ keep their proper names. Tooltips show the base under a proper name.

## 4. Weapons
`DataItems.ROSTER_BH015`: 5 per type × 13 types = 65, levels 4–54. Models by the Blender pipeline
(`tools/blender/items/item_weapons.py`: new staff heads orb / crook / branch, wand heads orb / branch / crescent),
icons by `icons_post.py`. Contact sheet: `evidence/weapons_sheet.png`. Roster weapons now carry the right class hint
(bows were all "knight" gear).

## 5. Multiplayer (`src/net/net.gd`, protocol 4)
Independent exploring: a joiner arrives at the host once, then travels freely. On the host's map monsters are the
host's (shared); elsewhere a client's world runs its own. Host walks in → the client's own monsters give way; host
leaves → the map fills with the client's own. Other players' heroes are not chased where their hits cannot be
resolved. **Summon Party** (P, party frames button, Multiplayer window, touch swirl button): each away player gets
Go / Stay (30 s → Stay). `Net.status` carries every player's map/HP/level everywhere: party frames show "in Olivar"
with HP, the world map draws allies. Probe: `tests/tools/net_probe_explore.gd` — host 9/9, client 18/18 ok
(`evidence/net/`). The bh-011 party probe's travel-request step is obsolete.

## 6. Saves
New fields are optional (save version stays 4, old saves load unchanged — tested). `SaveSystem.save_hero` now writes a
temp file, reads it back, keeps the previous save as `slot_<n>.json.bak`, and `read_slot` falls back to the backup (or
a checked temp file) when a slot is missing or corrupt. `delete_slot` removes all three.

## Tests
New suite `test_bh015` (11 tests, all pass). Full run: 29,527 checks, 20 failures — the same 20 lines as the bh-014
baseline (test_balance x11 incl. its known flake, test_enemies x1, test_enemies2 x8). `evidence/tests_final.txt`.
