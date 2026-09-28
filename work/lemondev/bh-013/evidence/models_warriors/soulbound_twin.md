# Soulbound Twin (`soulbound_twin`)

Built by Builder B1 (warriors); evidence written by Builder B2 (B1 was cut off before writing it). Not rebuilt.

- Module: `tools/blender/characters/enemy_soulbound_twin.py` (knight plate kit `char_knight` via `enemy_hollow_soldier.Scaled`, face from the `enemy_bandit_cutthroat` kit)
- GLB: `game/assets/characters/soulbound_twin.glb` (3.3 MB) + `soulbound_twin.glb.import`
- Triangles: 17336 (budget 20k); 24 bones; 8 materials
- Height: ~1.95 m to the helm crown (T-pose top 1.947 m, idle_1h f0 1.934 m; standard skeleton x 1.05)
- Clips (47): the shared enemy base clips + `sword_1 sword_2 sword_3 sword_heavy taunt cast_quick` (`taunt` is in the base set)
- Weapon: black-hilted longsword with a cyan fuller line on `weapon.R`; left hand empty. Stance clip: `idle_1h`.

## Palette (`soulbound_twin`, exported as `BH_*__soulbound_twin`)
| material | use |
|---|---|
| BH_DarkSteel (0.07, 0.07, 0.075) | tarnished black plate, bascinet |
| BH_Steel (0.64, 0.66, 0.7) metal 1.0 | polished silver pauldrons, couters, knee cops, trim, brow band |
| BH_Cloth_Primary (0.42, 0.41, 0.39) | long tattered ashen tabard |
| BH_Cloth_Secondary | dark under-cloth |
| BH_Skin (0.6, 0.61, 0.6) | pale bloodless face |
| BH_Leather, BH_Shadow | straps, eye sockets |
| BH_Emissive (0.3, 0.9, 1.0) x6 | broken spectral chain from the chest padlock, eyes, sword fuller |

## What makes it distinct
Neutral black/silver/ash base (deliberately, so the game's per-twin tint reads) with one strong accent: a broken
glowing cyan chain hanging from a padlock on the chest (long strand to the left hip, short snapped stub to the right),
which reads at the gameplay camera as a cyan diagonal across a black knight. Open-faced helm with cyan eyes; the
mirror knight is sand-gold, the frost revenant is icy blue-white.

## Evidence
- `soulbound_twin_rest_iso.png`: T-pose front/back, idle_1h at 4 yaws, head close-ups, gameplay camera 54 deg at 16 / 22 m (B1's render, same build).
- `soulbound_twin_clips.png`: idle_1h, every attack clip, hit_heavy, death_back (rendered by B2; B1 had only rendered a run check).
- `logs/soulbound_twin_metrics.json`: worst absolute edge growth 0.09 m (run, upper thigh).
- `logs/godot_check_warriors.txt`: scratch Godot 4.7.2 project, 0 import errors, all 47 expected clips present with the meta lengths.

## Build log
```
[soulbound_twin] mesh 17336 tris, 125 parts, 1.9s
[soulbound_twin] baked 47 actions in 20.1s
23:19:31 | INFO: Finished glTF 2.0 export in 3.76 s
[soulbound_twin] clip lengths verified (47 clips)
[soulbound_twin] -> A:\Python\beyond-heroes\game\assets\characters\soulbound_twin.glb (3.3 MB)
```

## Known limitations
- The chain is rigid (chest-weighted); it does not swing.
- Per-twin tinting must be done by the game (material override / modulate); the model ships one neutral palette.
- `.glb.import` was re-imported by the Orchestrator with `use_name_suffixes=true`: `block_loop` imports as `block`.
