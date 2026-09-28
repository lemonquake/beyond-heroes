# Warband Chieftain (`warband_chieftain`)

Built by Builder B1 (warriors); evidence written by Builder B2 (B1 was cut off before writing it). Not rebuilt.

- Module: `tools/blender/characters/enemy_warband_chieftain.py` (greenskin kit, custom proportions, S = 1.3)
- GLB: `game/assets/characters/warband_chieftain.glb` (3.4 MB) + `warband_chieftain.glb.import`
- Triangles: 16096 (budget 20k); 24 bones; 16 materials
- Height: ~2.45 m to the crown spikes; the back banner reaches ~3.44 m (T-pose top 3.46 m)
- Clips (48): the shared enemy base clips + `axe_1 axe_2 axe_heavy war_cry boss_roar boss_slam`
- Weapon: huge notched two-handed cleaver on `weapon.R`. Stance clip: `idle_2h`.

## Palette (`warband_chieftain`, exported as `BH_*__warband_chieftain`)
| material | use |
|---|---|
| BH_Skin (0.2, 0.25, 0.15) | green-grey orc skin |
| BH_Cloth_Primary (0.56, 0.04, 0.03) | clan red: banner field, war paint, cuirass claw marks |
| BH_Cloth_Secondary (0.025, 0.022, 0.02) | clan black: banner border and tusked-skull emblem |
| BH_DarkSteel / BH_Rust / BH_Steel | iron cuirass, pauldrons, crown, bracers / rust / cleaver edge |
| BH_Fur | brown-grey mantle and war-skirt |
| BH_Bone | tusks, trophy skulls, spikes |
| BH_Gold | arm rings, crown studs |
| BH_Wood, BH_Leather, BH_Horn, BH_Hair, BH_Flesh, BH_Shadow | pole, harness, trousers, braid, mouth, gaps |
| BH_Emissive (1.0, 0.36, 0.08) x5 | eye glints |

## What makes it distinct
The tall rigid red-and-black clan banner on a pole rising far above the head is unique among all enemies and reads
first at the gameplay camera (a red rectangle above a bulky armoured orc), identifying the rally leader from across
the fight. Much bigger and more decorated than the orc_reaver (fur mantle, spiked pauldrons, crown, trophy skulls).

## Evidence
- `warband_chieftain_rest_iso.png`: T-pose front/back, idle_2h at 4 yaws, head close-ups, gameplay camera 54 deg at 16 / 22 m (re-rendered by B2; B1's sheets predated the last module edit).
- `warband_chieftain_clips.png`: idle_2h, every attack clip, hit_heavy, death_back (re-rendered by B2).
- `logs/warband_chieftain_metrics.json`: worst absolute edge growth 0.16 m (wall_impact / boss_slam, thigh under the war-skirt).
- `logs/godot_check_warriors.txt`: scratch Godot 4.7.2 project, 0 import errors, all 48 expected clips present with the meta lengths.

## Build log
```
[warband_chieftain] mesh 16096 tris, 251 parts, 1.4s
[warband_chieftain] baked 48 actions in 19.9s
23:17:39 | INFO: Finished glTF 2.0 export in 3.85 s
[warband_chieftain] clip lengths verified (48 clips)
[warband_chieftain] -> A:\Python\beyond-heroes\game\assets\characters\warband_chieftain.glb (3.4 MB)
```

## Known limitations
- The banner is rigid (on the chest); it does not flutter, and in `death` / `death_back` it goes down flat with the body.
- The banner top is ~1 m above the head: the model's bounding height (3.44 m) is much larger than the body; scale by the crown (2.45 m), not by the AABB.
- Deep crouches (`boss_slam`, `wall_impact`) stretch the thigh skin under the war-skirt by up to 0.16 m (hidden by the skirt at the gameplay camera).
- `.glb.import` was re-imported by the Orchestrator with `use_name_suffixes=true`: `block_loop` imports as `block`.
