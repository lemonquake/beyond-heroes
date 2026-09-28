# Slag Hound (`slag_hound`)

- Script: `tools/blender/creatures/build_slag_hound.py` (imports the rig, gaits, clip DSL and baker from build_wolf.py; not edited)
- GLB: `game/assets/characters/slag_hound.glb` (+ `.glb.import` copied from dire_wolf, uid removed)
- Triangles: 5476; 31 bones (dire_wolf skeleton)
- Height: withers ~0.97 m, 1.23 m to the mane spike tips; nose-to-tail-tip 1.95 m
- Clips (15, 30 fps, in place): idle idle_look walk run run_combat hit_light hit_heavy stagger_small knockback death
  death_back alert + hound_bite (0.8 s, hit 0.333-0.433), hound_lunge (pounce, 1.4 s, hit 0.767-0.9),
  hound_breath (1.4 s, plants and breathes forward, fire window 0.433-1.233)
- creature_meta.json: merged only hound_bite / hound_lunge / hound_breath into "animations" (re-read, verified other keys unchanged)
- Materials: BH_Stone (slag plates), BH_Fur (dark slag skin), BH_Horn (obsidian spikes/claws), BH_Bone (obsidian teeth),
  BH_Shadow, BH_Emissive (molten body core visible between plates, leg/tail seams, eyes, maw: tongue/palate/throat)

## What makes it distinct
Lean hound whose body is a glowing molten core crusted with slag plates (seams glow everywhere), a crest of jagged
obsidian spikes along neck and spine, glowing open maw, ember eyes, a thin whip tail ending in three obsidian spikes.

## Evidence
`slag_hound_rest_iso.png`, `slag_hound_clips.png` (walk, run, hound_bite, hound_lunge, hound_breath, hit_heavy, death).

## Build log
```
[slag_hound] mesh 5476 tris, 15 clips, 31 bones
[slag_hound] merged ['hound_bite', 'hound_breath', 'hound_lunge'] into game/assets/characters/creature_meta.json
[slag_hound] -> game/assets/characters/slag_hound.glb (1.4 MB), 15 animations, length mismatches: []
```

## Known limitations
Generic clip meta (walk/run ground speeds) is shared with dire_wolf via the humanoid-first lookup (same rig, fine).
Plates are rigid boxes on a smoothly weighted core, so the glow gaps widen/narrow in the run; spikes pierce the ground in death.
