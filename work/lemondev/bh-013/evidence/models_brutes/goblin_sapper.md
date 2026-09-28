# Goblin Sapper (`goblin_sapper`)

- Module: `tools/blender/characters/enemy_goblin_sapper.py` (greenskin kit; reuses the Goblin Skulker's skeleton proportions, torso rows, head rows and knife via `import enemy_goblin_skulker`)
- GLB: `game/assets/characters/goblin_sapper.glb` (3.1 MB) + `goblin_sapper.glb.import` (necromancer settings, own path hash, no uid, `nodes/use_name_suffixes=false`)
- Triangles: 12846 (budget 20k); 24 bones; 14 materials
- Height: ~1.12 m to the top of the padded cap; the bomb stack on the back rises behind the head to ~1.2 m and the top fuse spark to 1.26 m (T-pose AABB top 1.263 m). Scale by 1.15 m / 1.26 m if the game normalises by AABB.
- Clips (47): the 42 shared enemy base clips + `dagger_1 dagger_2 cast_quick cast_weapon blink`
  - `dagger_1` / `dagger_2`: knife stabs (hit 0.13-0.23 s of 0.43 s)
  - `cast_quick` (0.5 s): lob a bomb (no hit window in the meta; release at the forward arm swing, mid-clip)
  - `cast_weapon` (0.8 s): plant / throw the mine held in the left hand
  - `blink` (0.5 s): dive-roll escape
- Weapons (in-mesh, rigid): short notched knife on `weapon.R`, round studded clay mine with a lit fuse on `weapon.L`. Stance clip: `idle_dagger`. If the game spawns a thrown mine/bomb projectile, the left-hand mine stays in the hand (it is part of the mesh).

## Palette (`goblin_sapper`, exported as `BH_*__goblin_sapper`)
| material | use |
|---|---|
| BH_Skin (0.2, 0.19, 0.055) | mustard-green skin (skulker is olive, summoner grey-green) |
| BH_Flesh | inner ears |
| BH_Leather (0.05, 0.035, 0.025) | soot-black apron (bib + knee-length skirt), thick gloves, knee pads, straps, bandolier, pouches |
| BH_Cloth_Secondary (0.5, 0.33, 0.12) | quilted ochre padded cap, rope lashing, fuse cord, shin wraps |
| BH_Cloth_Primary (0.24, 0.07, 0.035) | rust-red breeches, fuse-stick wraps |
| BH_Stone (0.46, 0.17, 0.07) | terracotta fire-pots, the mine |
| BH_DarkSteel | black iron bombs, pot bands, mine rim |
| BH_Bronze | brass goggles, buckles, bomb necks, mine studs |
| BH_Aether (0.45, 0.62, 0.62), rough 0.08 | goggle glass |
| BH_Wood | pack frame and shelf |
| BH_Steel | knife blade |
| BH_Bone, BH_Shadow | teeth, toe claws / mouth, sockets, scorch mark |
| BH_Emissive (1.0, 0.55, 0.1), emission x9 | 11 fuse sparks on the pack, 1 on the mine, eyes |

## What makes it distinct
- Silhouette key: a wooden pack-frame wider than the goblin (0.4 m) stacked with pots and black bombs up past the head, sprinkled with orange spark stars; from the high front camera it frames the ochre cap, from behind it is a tower of pots.
- vs goblin_skulker: no oversized kettle helmet, no burlap loot sack, no belt fire-pots; instead ochre padded cap + brass goggles, long black apron, gloves and the bomb pack. vs goblin_summoner: no feather mask, cloak, drum or staff. vs bandit_bombardier: human-sized bandit with a single powder keg; the sapper is 1.15 m with a stacked multi-bomb pack.

## Evidence
- `goblin_sapper_rest_iso.png`: T-pose front/back, idle_dagger at 4 yaws, head close-ups, gameplay camera 54 deg at 16 / 22 m.
- `goblin_sapper_clips.png`: idle_dagger, the five attack clips, hit_heavy, death_back.
- `logs/goblin_sapper_metrics.json`: worst absolute edge growth 0.083 m (wall_impact, apron hem corner); run 0.063 m, dagger clips 0.063 m.
- `logs/godot_check_goblin_sapper.txt`: scratch Godot 4.7.2 project, 0 import errors, all 47 expected clips present with the meta lengths, `block_loop` keeps its name.

## Build log
```
[goblin_sapper] mesh 12846 tris, 230 parts, 1.0s
[goblin_sapper] baked 47 actions in 17.4s
[goblin_sapper] clip lengths verified (47 clips)
[goblin_sapper] -> A:\Python\beyond-heroes\game\assets\characters\goblin_sapper.glb (3.1 MB)
[build] done in 22.0s
```

## Revision passes
1. At the gameplay camera the first pack (narrower than the shoulders) hid completely behind the goblin from the front. Frame widened to 0.4 m, three rows of pots/bombs (11 items) rising above the head, sparks 25 % bigger.
2. Metrics: the apron skirt reached below the knees and stretched 0.13-0.18 m between the legs (idle stance, getup). Shortened to the knees and weighted more to the hips; worst now 0.083 m.

## Known limitations
- Workbench previews do not show emission strength; the sparks are small (about 4-5 cm) and rely on the emissive to read at 20 m.
- The pack is rigid on `chest`; in `death_back` it goes through the floor under the body (like every back-mounted prop).
- The mine is part of the left hand; there is no separate throwable mesh.
