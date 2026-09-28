# Briar Lasher (`briar_lasher`)

Built by Builder B1 (warriors); evidence written by Builder B2 (B1 was cut off before writing it). Not rebuilt.

- Module: `tools/blender/characters/enemy_briar_lasher.py` (greenskin kit + `kit_warren` roots, S = 1.08)
- GLB: `game/assets/characters/briar_lasher.glb` (3.3 MB) + `briar_lasher.glb.import`
- Triangles: 12128 (budget 20k); 24 bones; 7 materials
- Height: ~2.1 m to the thorn crown tips (T-pose top 2.111 m, idle f0 2.107 m), hunched
- Clips (48): the shared enemy base clips + `sword_1 sword_2 spear_heavy cast_quick cast_area boss_roar`
  - `sword_1`, `sword_2` = whip lashes; `spear_heavy` = lash-and-pull thrust (the vine-pull attack); `cast_quick` / `cast_area` = thorn casts; `boss_roar` = bristle roar
- Weapon: long rigid curling thorned vine whip on `weapon.R`; the left forearm ends in a knotted bark club studded with thorns (rigid on `hand.L`, not a socket weapon). Stance clip: `idle_1h`.

## Palette (`briar_lasher`, exported as `BH_*__briar_lasher`)
| material | use |
|---|---|
| BH_Wood (0.085, 0.055, 0.035) | dark twisted bark body |
| BH_Leather (0.2, 0.13, 0.07) | lighter bark ridges, the lip of the head hollow |
| BH_Fur (0.07, 0.13, 0.035) | thorny green vines wrapping the limbs |
| BH_Cloth_Primary (0.62, 0.04, 0.07) | crimson thorns (crown, shoulder tufts, spine ridge, limb vines) |
| BH_Flesh (0.3, 0.03, 0.05) | dark red dried leaves |
| BH_Shadow | the hollow face |
| BH_Emissive (1.0, 0.28, 0.05) x6 | two ember eyes inside the hollow |

## What makes it distinct
Dark bark body with bright crimson thorn crown and shoulder tufts: at the gameplay camera a dark figure with a red
spiky crown and a long curling whip. Different from the rootweaver / mycelid hulk (no cap, no robe, no glowing sacs)
and the only enemy with a whip silhouette; the lopsided club forearm balances the whip side.

## Evidence
- `briar_lasher_rest_iso.png`: T-pose front/back, idle_1h at 4 yaws, head close-ups, gameplay camera 54 deg at 16 / 22 m (B1's render, 23:21, same build).
- `briar_lasher_clips.png`: every attack clip at 5 frames (B1's render, same build).
- `logs/briar_lasher_metrics.json`: worst absolute edge growth 0.08 m (run, thigh).
- `logs/godot_check_warriors.txt`: scratch Godot 4.7.2 project, 0 import errors, all 48 expected clips present with the meta lengths.

## Build log
```
[briar_lasher] mesh 12128 tris, 317 parts, 1.3s
[briar_lasher] baked 48 actions in 20.8s
23:22:21 | INFO: Finished glTF 2.0 export in 3.74 s
[briar_lasher] clip lengths verified (48 clips)
[briar_lasher] -> A:\Python\beyond-heroes\game\assets\characters\briar_lasher.glb (3.3 MB)
```

## Known limitations
- The whip is a rigid curled shape on `weapon.R`: it swings with the arm but does not uncoil; a lash-pull VFX / tether line should come from the game.
- The shared sword clips drive the whip arm, so the lashes are sword arcs, not true whip cracks.
- `.glb.import` was re-imported by the Orchestrator with `use_name_suffixes=true`: `block_loop` imports as `block`.
