# bh-035 handoff: frame time in big fights, spawn hitches, multiplayer bandwidth, Shadowblade weapon scaling, QA fixes

Measured on the development PC (Ryzen 7 5700X, RTX 4060), 1280x720, vsync and frame cap off, fresh processes, warm-up
discarded. "mobile" is the phone preset with the OpenGL renderer on this PC, not a phone. Evidence and raw numbers:
`work/lemondev/bh-035/evidence/`, `output/bh-035/`.

## Results

| Scenario (perf_matrix.py, 2 runs) | before: median / p99 frame | after: median / p99 frame |
| --- | --- | --- |
| 40-monster brawl, pc-low | 32.0 / 182.6 ms | 15.6 / 34.8 ms |
| 40-monster brawl, mobile preset | 58.7 / 93.1 ms | 33.8 / 63.7 ms |
| 12-monster fight, pc-low | 5.6 / 14.5 ms | 4.2 / 11.6 ms |
| 12-monster fight, mobile preset | 11.5 / 20.3 ms | 8.9 / 17.2 ms |
| dungeon, pc-low | 3.1 / 10.4 ms | 2.0 / 5.6 ms |
| town, forest, Agdao (pc-low) | 2.3-4.9 / 6.7-10.6 ms | 2.0-3.7 / 3.9-8.8 ms |

| Six heroes on one map (integration_probe --stages bandwidth) | before | after |
| --- | --- | --- |
| map owner upload | 3,400 kbit/s | 528 kbit/s |
| member upload | 365 kbit/s | 45 kbit/s |
| member download | 870 kbit/s | 250 kbit/s |
| dedicated server egress | 2,870 kbit/s | 1,080-1,430 kbit/s (two runs) |

## Spawn hitch (the 80-140 ms freeze whenever a humanoid monster appeared)

`CharacterVisual._prepare_animations()` set `loop_mode` on every clip of the model's animation library for every new
character. The library is shared by all characters with that model, and Godot emits `changed` for every assignment even
when the value is the same, which cleared the animation caches of every hero-body NPC, monster and companion in the
map. They all rebuilt the caches on the next frame: ~75 ms after one spawn, ~140 ms after two. Only the first character
of a model writes now. `test_bh035.test_spawning_leaves_the_shared_animations_alone` guards it.
Same family as the bh-034 cutscene bug (CHANGELOG, "Animations after cutscenes"): never write to a GLB's shared animations.

## Crowd simulation LOD (`Enemy._crowd_half`)

A brawl spent ~9 ms per physics step on monster scripts and `move_and_slide`; with other frame costs that pushed frames
past 16.7 ms, so Godot ran two physics steps per frame, which made the frame longer still. When more than 14 monsters are
awake (7 in efficiency mode), a monster that is only waiting for an attack token (circling, closing in, backing off)
thinks, steers and collides on every other step and coasts along its velocity in between. Anything attacking, casting,
charging, staggered, knocked back, airborne, holding a token, a boss or a miniboss runs every step. Each monster
alternates on its own, so half the crowd works on each step.

## Animation stride LOD (`CharacterVisual.set_anim_stride`, `Perf._sleep_animations`)

Of the ordinary monsters and townsfolk animating on screen, the nearest 12 animate every frame, the next 16 every second
frame and the rest every third frame (half those counts in efficiency mode). The tree is advanced by hand with the time
that passed, so clips stay in step. Bosses, the hero, companions and other players never take part (`crowd_lod`).

Blind review (two passes, fresh reviewers, baseline vs this build, mapping revealed after): neither found a motion defect
in this build that the baseline lacks; the formal pick was the baseline both times, without a clear advantage. Recorded
as "no visible regression found", not as a visual improvement.

## Multiplayer (protocol 19; `server/service.py` and the healthcheck match)

- **Hero snapshots go to the room host only**, which forwards them: every snapshot to heroes within 80 m on the same map,
  every third to heroes farther away on that map, and a slim presence update (place, health, level) every eighth to
  heroes on other maps (`_relay_allies`, `_ally_relay`). They used to be broadcast to everyone at 15 Hz.
- **Packed snapshots** (`NetCodec.pack_actor`, `pack_monsters`): a hero or monster state is ~45 bytes instead of 136-192
  as generic Variants. Decoding is bounds-checked: a short or malformed packet decodes to nothing.
- **Idle monsters are not re-sent**: each state is built once per round (not once per member); a member gets a monster
  only when it changed since the snapshot that member last received, and otherwise once a second as a keep-alive. Calm or
  far (35 m+) monsters go out at 4 Hz; replicas and far avatars dead-reckon between snapshots.
- **Checkpoints**: the full monster list goes to the room host every 2 s and to members every 6 s; the small
  camps/cleared/arena part goes whenever it changes. A mass kill triggers one checkpoint, not one per monster. Roster
  updates carry a map's saved state only to that map's owner (they used to carry every map's state to every player).
- Appearances are re-sent when the roster changes and every 10 s (was every 2 s), and an avatar re-dresses only when a
  new appearance arrives (it rebuilt its gear plan 15 times a second).

## Balance

- **Shadowblade weapons scaled with Strength.** Daggers, claws and knuckles took both their percentage scaling and their
  flat attack from Strength, the Shadowblade's weakest attribute, so its weapon damage reached about a third of the
  other classes' by level 30. Daggers now scale with Agility 70% / Dexterity 30%, claws with Agility, knuckles with
  Strength and Agility; the flat attack uses Agility (daggers, claws) or the better of Strength and Agility (knuckles)
  (`StatCalculator.finesse_attribute`).
- Knight **Cleave**: +12% weapon damage per rank (was +18%; rank 5: 210%, was 240%).
- Mage **Elemental Attunement**: 25% increased elemental damage (was 10%).
- The balance bot (`test_balance`) spends finishers on a full bar (4 Combo pips, 60 Focus) instead of on cooldown.

`test_balance` (bh-010 band: every class within 20% of the mean power): 11 of 16 checks pass (7 before). Level 30: all
four classes within -7%..+5%. Still outside: level 1 (Ranger -27%, Shadowblade +28%: starting kits), Knight +33% / +44%
at levels 10 / 20 (its effective HP is ~1.5x the average and the power score multiplies it in; its damage is now
average), Mage -23% at level 20 (inside the simulation's known +-10% run-to-run noise).

## QA fixes

- Character window: a long rank checklist pushed the window 33 px past its 900 px frame; the attribute hint is one line
  (full text in its tooltip) and the checklist starts at 64 px.
- The Warren (fungal) dungeon dressed its work rooms with the Deeps' wet storage; it uses dry storage and fungal stumps.
- `TouchText` queued a deferred call for every control added on desktop too, and a control freed before the call reached
  a typed parameter as a dead object (an engine error each time). It only queues in touch mode, by instance id.
- Probes: `net_probe_trade` offered bag cell 0 although potions fill the belt first (since bh-030); `net_probe_explore`
  expected the host to take a map back from its first explorer (bh-032 keeps the first explorer in charge);
  `net_probe_team` could lose its 1-HP test monster to the owner's own Tempo before the other member saw it.

## Tools

- `tools/net_probes.py`: runs the local explore, trade, arena, guild and team probes and summarises them
  (`--game <folder>` runs a frozen copy).
- `tests/tools/perf_probe.gd`: `--phases=1` (where a frame goes), `--anim_cost=1`, `--census=all`,
  `--spawn_bench=map`, `--persona_bench=<enemy>`, `--strip=<dir>` (consecutive frames for review), more `--freeze=` cases.
- `tests/tools/net_size_probe.tscn`: payload sizes of this machine's ally pack and the map's monster states.
