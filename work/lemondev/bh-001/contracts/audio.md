# Contract: audio (bh-001 / C8)

Synthesize all sound effects and music procedurally with Python 3.12 (numpy, scipy available; no downloads, no samples from
elsewhere). Scripts in `tools/audio/`; outputs in `game/assets/audio/sfx/` and `game/assets/audio/music/` as 16-bit PCM WAV.
SFX mono 44.1 kHz; music and ambience stereo 44.1 kHz. Deterministic (fixed seeds). Do not touch other folders; do not run Godot
on `game/`.

Quality bar: sounds must read as what they are in a dark-fantasy action RPG. Use layered synthesis: filtered noise bursts,
FM/additive tones, pitch envelopes, transient clicks, convolution/feedback-delay reverb, saturation, EQ. Peak-normalize SFX to
-1 dBFS with no clipping, trim silence, fade tails (no clicks at start/end). Loops (ambience/music) must loop seamlessly
(crossfade the seam; verify by checking the sample discontinuity at the loop point).

## SFX (file names are a contract; `_1.._3` = variations with different seeds/pitch)

Weapons: `swing_light_1..3`, `swing_heavy_1..3`, `swing_dagger_1..2`, `swing_blunt_1..2`, `bow_draw`, `bow_release`,
`arrow_impact_1..2`.
Impacts: `hit_flesh_1..3`, `hit_bone_1..3`, `hit_armor_1..3`, `hit_heavy_1..2` (big meaty thud with low boom), `crit_hit`
(sharp bright layered impact), `block_1..2` (metal clang), `parry` (ringing high clang), `wall_impact_1..2` (body slamming
stone), `body_fall`, `stagger`, `shatter_ice`.
Magic: `cast_fire`, `fire_whoosh`, `fire_explode`, `burn_loop` (loop), `cast_ice`, `ice_nova`, `freeze`, `cast_lightning`,
`lightning_zap_1..2`, `thunder_strike`, `cast_earth`, `earth_quake`, `rock_impact`, `wind_gust`, `water_splash`, `water_wave`,
`holy_chime`, `holy_strike`, `heal`, `dark_cast`, `dark_curse`, `drain`, `blink`, `arcane_charge`, `arcane_surge`, `meteor_fall`,
`meteor_impact`, `war_cry` (processed roar/horn), `whirlwind_loop` (loop).
Movement: `footstep_stone_1..4`, `footstep_dirt_1..4`, `footstep_grass_1..3`, `footstep_heavy_1..2`, `dodge_roll`,
`armor_rustle_1..2`.
Enemies: `skeleton_rattle_1..2`, `skeleton_death`, `ghoul_growl_1..2`, `ghoul_death`, `cultist_chant`, `cultist_death`,
`shade_hiss`, `boss_roar`, `boss_slam`, `boss_charge`, `boss_phase` (ominous rising stinger), `elite_spawn`, `explode`.
World: `break_wood_1..2`, `break_pottery_1..2`, `break_stone`, `chest_open`, `door_gate`, `teleport_charge`, `teleport_whoosh`,
`teleporter_hum` (loop), `torch_crackle` (loop), `fire_campfire` (loop).
Loot / progression: `loot_drop`, `loot_drop_rare`, `loot_drop_legendary` (distinct shimmering fanfare), `gold_pickup`,
`item_pickup`, `potion_drink`, `level_up` (satisfying ascending fanfare ~2 s), `skill_unlock`, `talent_unlock`.
UI: `ui_hover`, `ui_click`, `ui_open`, `ui_close`, `ui_equip`, `ui_unequip`, `ui_error`, `ui_page`.

## Ambience loops (stereo, 30–60 s)

`amb_town` (distant wind, fire crackle, faint bells, birds), `amb_forest` (wind through dead trees, crows, creaks),
`amb_catacombs` (low drones, drips, distant rumbles), `amb_temple` (hollow reverb wind, faint choir-like pad), `amb_arena`.

## Music loops (stereo, 90–150 s, seamless)

`music_menu` (somber, memorable motif — e.g. a slow minor-key melody on a plucked/lute-like or bowed timbre over dark pads),
`music_town` (calm, melancholic, warm), `music_dungeon` (tense, sparse, percussive pulses), `music_boss` (driving drums,
low brass-like stabs, urgency). Write them as actual compositions (defined chord progressions, melody phrases, dynamics,
arrangement sections), not random noise. Keep them mixed ~ -14 LUFS-ish (moderate) so they sit under SFX.

## Evidence to return

`work/lemondev/bh-001/evidence/audio/report.txt`: file list with duration, peak dBFS, RMS, loop seam discontinuity for loops;
plus spectrogram PNGs for a representative subset (~12 files) and full music tracks. README in `tools/audio/` with the
regeneration command.
