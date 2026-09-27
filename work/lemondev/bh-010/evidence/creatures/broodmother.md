# Broodmother (broodmother.glb)

Generator: `tools/blender/creatures/build_broodmother.py` -> `game/assets/characters/broodmother.glb`

- Size: abdomen top 1.10 m, leg span ~2.6 m (L1 foot to R4 foot); Spiderling = same GLB x0.42.
- Triangles: 14812; vertices 8609; bones 43 (root non-deform).
- Materials: BH_Bone__broodmother, BH_Emissive__broodmother, BH_Flesh__broodmother, BH_Fur__broodmother, BH_Hair__broodmother, BH_Horn__broodmother, BH_Shadow__broodmother
- Bones: `root`, `body`, `abdomen`, `chel.L`, `fang.L`, `palp.1.L`, `palp.2.L`, `chel.R`, `fang.R`, `palp.1.R`, `palp.2.R`, `coxa.1.L`, `femur.1.L`, `tibia.1.L`, `tarsus.1.L`, `coxa.2.L`, `femur.2.L`, `tibia.2.L`, `tarsus.2.L`, `coxa.3.L`, `femur.3.L`, `tibia.3.L`, `tarsus.3.L`, `coxa.4.L`, `femur.4.L`, `tibia.4.L`, `tarsus.4.L`, `coxa.1.R`, `femur.1.R`, `tibia.1.R`, `tarsus.1.R`, `coxa.2.R`, `femur.2.R`, `tibia.2.R`, `tarsus.2.R`, `coxa.3.R`, `femur.3.R`, `tibia.3.R`, `tarsus.3.R`, `coxa.4.R`, `femur.4.R`, `tibia.4.R`, `tarsus.4.R`

## Clips

| clip | frames | length (s) | loop | hits (s) | ground_speed (m/s) |
|---|---|---|---|---|---|
| `idle` | 90 | 3.000 | yes | - | - |
| `idle_look` | 75 | 2.500 | no | - | - |
| `walk` | 20 | 0.667 | yes | - | 1.6 |
| `run` | 10 | 0.333 | yes | - | 5.0 |
| `run_combat` | 10 | 0.333 | yes | - | 4.6 |
| `hit_light` | 12 | 0.400 | no | - | - |
| `hit_heavy` | 18 | 0.600 | no | - | - |
| `stagger_small` | 24 | 0.800 | no | - | - |
| `knockback` | 27 | 0.900 | no | - | - |
| `death` | 45 | 1.500 | no | - | - |
| `death_back` | 45 | 1.500 | no | - | - |
| `alert` | 30 | 1.000 | no | - | - |
| `spider_bite` | 24 | 0.800 | no | [0.367, 0.467] | - |
| `spider_spit` | 36 | 1.200 | no | [0.600, 0.667] | - |
| `spider_pounce` | 42 | 1.400 | no | [0.800, 0.900] | - |
| `spider_brood` | 60 | 2.000 | no | - | - |

## Foot contact (in-place clips; stance feet should slide back at exactly ground_speed)

| clip | max slip mm/frame | mean slip mm/frame | stance fraction |
|---|---|---|---|
| walk | 12.18 | 0.28 | 0.55 |
| run | 0.00 | 0.00 | 0.38 |
| run_combat | 0.00 | 0.00 | 0.38 |
| dire_wolf walk (same metric) | 12.01 | 3.39 | 0.53 |
| dire_wolf run (same metric) | 20.92 | 2.33 | 0.25 |

Worst IK reach miss per clip (mm; legs in FK curl excluded): idle 0.0, idle_look 0.0, walk 0.0, run 0.0, run_combat 0.0, hit_light 0.0, hit_heavy 0.0, stagger_small 0.0, knockback 0.0, death 18.2, death_back 12.1, alert 0.0, spider_bite 0.0, spider_spit 0.0, spider_pounce 0.0, spider_brood 0.0
