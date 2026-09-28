# Treasure Gremlin (`treasure_gremlin`)

- Module: `tools/blender/characters/enemy_treasure_gremlin.py` (greenskin kit; custom proportions = goblin proportions x 0.88)
- GLB: `game/assets/characters/treasure_gremlin.glb` (2.8 MB) + `treasure_gremlin.glb.import` (necromancer settings, own path hash, no uid, `nodes/use_name_suffixes=false`)
- Triangles: 8756 (budget 20k); 24 bones; 11 materials
- Height: 1.04 m to the crown tips (T-pose top 1.041 m, idle f0 1.036 m); head top ~0.97 m. The sack makes it 0.7 m wide and 0.8 m deep (AABB y -0.23..0.58).
- Clips (45): the 42 shared enemy base clips + `dagger_1 cast_quick blink`
  - `dagger_1` (0.43 s, hit 0.13-0.23 s): panicked claw swipe if cornered
  - `cast_quick` (0.5 s): toss a coin / flash
  - `blink` (0.5 s): vanish / teleport away
  - It flees: use `run` (loops) as its main clip; `idle_hurt` / `run_hurt` also exist.
- Weapon: none. Both sockets empty; do not attach a weapon. Stance clip: `idle`.

## Palette (`treasure_gremlin`, exported as `BH_*__treasure_gremlin`)
| material | use |
|---|---|
| BH_Skin (0.3, 0.23, 0.18) | warm grey-brown skin |
| BH_Flesh | pink inner ears, gums |
| BH_Cloth_Primary (0.24, 0.05, 0.3) | purple waistcoat |
| BH_Fur (0.09, 0.2, 0.12) | green lapels and a green patch on the waistcoat |
| BH_Cloth_Secondary (0.3, 0.2, 0.09) | the huge burlap sack, its rolled lip and a burlap patch |
| BH_Leather | ragged breeches, rope belt, sack straps, leather patches on the sack |
| BH_Gold (1.0, 0.72, 0.22), metallic 1.0, roughness 0.18 | heap of coins in the sack mouth (~30 coins on a gold mound), two ingots, the goblet, coins spilling from a split seam, crown, 3 neck chains + medallion, waistcoat buttons, ear hoop, bangle |
| BH_Aether (0.8, 0.03, 0.08), rough 0.08, faint red emission | rubies on the goblet, crown and medallion |
| BH_Bone | needle teeth, claws, pearl string over the sack lip |
| BH_Emissive (1.0, 0.8, 0.25) x7 | big greedy gold eyes |
| BH_Shadow | eye sockets, mouth |

## What makes it distinct
- Silhouette: a tiny stooped creature almost hidden in front of a round sack as big as itself, gold heaped on top of the sack; huge bat ears stick out to both sides. From the high camera it reads as a brown ball with a gold cap and two ears - unlike anything else in the roster.
- vs goblins (skulker has a small loot sack): no helmet, no weapon, not green, purple waistcoat, crown, and the sack is ~3x the skulker's and overflowing with gold.

## Evidence
- `treasure_gremlin_rest_iso.png`: T-pose front/back, idle at 4 yaws, head close-ups, gameplay camera 54 deg at 16 / 22 m.
- `treasure_gremlin_clips.png`: idle, dagger_1, cast_quick, blink, run, hit_heavy, death_back.
- `logs/treasure_gremlin_metrics.json`: worst absolute edge growth 0.053 m (revive, thigh); run 0.028 m.
- `logs/godot_check_treasure_gremlin.txt`: scratch Godot 4.7.2 project, 0 import errors, all 45 expected clips present with the meta lengths, `block_loop` keeps its name.

## Build log
```
[treasure_gremlin] mesh 8756 tris, 162 parts, 0.7s
[treasure_gremlin] clip lengths verified (45 clips)
[treasure_gremlin] -> A:\Python\beyond-heroes\game\assets\characters\treasure_gremlin.glb (2.8 MB)
[build] done in 20.7s
```

## Revision passes
1. The gold heap in the sack mouth was too small to read at the gameplay camera, and a column of spilled coins dangled under the sack like a chain. Mouth widened, the mound made taller (12 cm) with 30 larger coins, two ingots and the goblet raised out of it; the spill cut to 3 coins close to the split seam.

## Known limitations
- The stoop is in the mesh only (upper torso and head shifted 4.5-5.5 cm forward); the bones stay upright, so the shared clips do not add extra hunching.
- Metallic gold with low roughness depends on environment reflections; in very dark areas it can look darker than the Workbench previews suggest. If it reads dull in game, the Orchestrator can raise the gold's emission or the area's ambient light.
- The sack is rigid on `chest`: in `death_back` (lying on its back) it goes through the floor, and it does not swing when running. A gold-burst VFX on death would cover it.
