# bh-038 — Zarael for strong heroes, Agdao ground glitches, Barrens black materials, crystal spirits (2026-10-05)

Request: raise Zarael's monster levels by 20 and its dungeon levels by 40; personally sweep Agdao for glitching ground
graphics and fix them; fix the pure-black, texture-less surfaces in the Glasswire Barrens; give every crystal its own
special effect on a weapon — e.g. Ember, Nova and Sora set in one weapon = three different orbs circling it like spirits.

## 1. Levels

| Place | Before | After |
|---|---|---|
| The Coilwood | 30–36 | 50–56 |
| The Glasswire Barrens | 36–42 | 56–62 |
| The Bridge of Death | 42–46 | 62–66 |
| The Heart Citadel | 46–52 | 66–72 |
| The Jade Sepulchre (7 floors) | 33–40 | 73–80 |
| The Obsidian Engine | 39–46 | 79–86 |
| The Veinworks | 45–53 | 85–93 |

Every camp table moved with its map (`zr_*.gd`, `bridge_of_death.gd`), bosses and minibosses follow `level_max`, the
ward pylons' fallback level, the atlas labels (`DataIsland`), the quest tracker's recommended levels (`Objectives`:
ship 50, Vaults 76/82/88, Bridge 66, Abbot 70) and `Objectives.ZARAEL_LEVEL` 28 → 48 (when a hero still on Salmonan is
pointed at the ship). Note: the story still sends the hero into the Vaults (73+) before the Bridge (62–66); the Bridge
can be crossed without them (the pylons only throw lightning).

## 2. Agdao ground glitches — swept in the real game

`game/tests/tools/capture_sweep.tscn` walks a grid over a whole map in the real game (hero teleported onto the ground
found by a ray), photographs each spot twice with the hero nudged 3 cm, and reports flicker and near-black pixel shares
(`output/bh-038/sweep/`: agdao 168 spots before/after, town area 90 spots, barrens 140 spots).

| # | Cause | Fix |
|---|---|---|
| 1 | All 129 world texture sets (`assets/textures/*_albedo/normal/rough.png`, legend sets) were imported **without mipmaps** and uncompressed: paving, glyph stone, clay and stairs shimmered and crawled whenever the camera moved (the terrain shader even asked for anisotropic mip filtering). 1024² each, ~460 MB if all loaded. | Imports set to VRAM compressed (S3TC/BPTC desktop, ETC2/ASTC Android) with mipmaps. |
| 2 | Harbour quay: the quay wall's 8 m blocks (and the pier's root) have paved tops exactly at the harbour floor's height; terrain and blocks z-fought along the whole quay (offset patches and triangles of mismatched paving). bh-034 fixed this for the upper terraces only. | `agdao.gd _terrain_h` keeps the terrain 0.35 m under the quay blocks and pier root (`_quay_span`). |
| 3 | Camera see-through fade (a house between camera and hero) used alpha-hash dithering at 28 %: seen from above, a faded roof became a rectangle of crawling static over the ground. | `MaterialLibrary.see_through()`: smooth alpha blend with depth writes for architecture (PlayerCamera, FX warm-up, walk_probe). Characters keep the dithered `faded()` copy their warm-up relies on. |

Before/after: `agdao_quay_before_after.jpg`, `agdao_fade_before_after.jpg`.

## 3. Barrens black materials

`game/tests/tools/map_material_audit.tscn` lists every material a built map draws with (DARK / NOTEX / NOMAT / GLOW
flags). The black surfaces were all `BH_Obsidian` (the Obsidian Engine's gate block, every glass growth): a near-black
texture (mean 18/255) times a 0.42 tint. Basalt had the same problem (0.42 tint on a 33/255 texture).

- `tools/textures/gen_zarael_textures.py obsidian`: albedo lifted ~2.5x (still the darkest stone; shells and fractures read).
- `BH_Obsidian` tint 0.42 → 0.96 (roughness 0.3), `BH_Basalt` 0.42 → 0.78, Obsidian Vault dark-stone tint 0.42 → 0.62.
- Barrens near-black pixel share at the Obsidian gate: 12.5 % → 0.03 % (`barrens_black_before_after.jpg`).

## 4. Crystal spirits (`src/vfx/gem_spirits.gd`)

Each crystal set in a held weapon or shield is its own spirit circling the weapon's axis, evenly spaced in phase and
spread along the blade; same family twice = two of that kind. One billboard shader (12 drawn designs, compiled once,
materials shared per family+grade), a particle trail per spirit for heroes, none for companions (cheap). Higher grade =
larger, brighter.

| Family | Spirit | Motion | Trail |
|---|---|---|---|
| Ember | flickering flame-tongue | bobs | rising embers |
| Aqua | water bead, rolling highlight, ripples | wobbles | drips |
| Nova | turning four-point star, twinkles | steady | glints |
| Thundra | white core in re-striking jagged lightning ring | twitches | sparks |
| Vipera | serpent eye, slit pupil narrows, blinks | weaves up and down | venom drips |
| Bloodrift | dark heart with glowing veins, double beat | slow | sinking blood mist |
| Essencerift | violet vortex into a black centre | breathes in/out | motes |
| Aetherift | rotating prismatic hex shard split by a white rift | steady | prismatic motes |
| Sora | wind curls racing round a cloud heart | fast | puffs |
| Luna | pale crescent moon, glint | slow drift | falling motes |
| Sol | small sun with two counter-turning ray crowns | steady | rising sparks |
| Airah | two mint leaves spinning like a seed | figure-eights | drifting motes |

Shown on the hero, companions (Tempos), Quake allies, the inventory preview and other players online (the synced
appearance carries `gems`; older peers ignore it, no protocol bump). Replaces bh-022's single mixed-colour mote stream
(`set_weapon_infusion` removed). Captures: `sheets/gems*.jpg` (`tests/tools/capture_gems.tscn`).

## Tests

`tests/unit/test_bh038.gd` (levels, camp bands, objectives, texture imports, obsidian brightness, spirits, visual
wiring/sync). `test_bh029` updated for the new bands. Suite results: `tests_final.txt`.
Raw sweep frames stay local (1.6 GB); `sheets/` holds downscaled contact sheets of every sweep.
