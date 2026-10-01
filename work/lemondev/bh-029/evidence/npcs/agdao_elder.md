# agdao_elder — Agdao elders and healers (Mother Ysenne, Speaker Caius Wend) (bh-029, Builder N1)

- Module: `tools/blender/characters/town_agdao_elder.py` (palette `town_agdao_elder`, `TINTABLE = ("BH_Cloth_Primary",)`,
  `CLIPS_ONLY = TOWN_CLIPS`)
- GLB: `game/assets/characters/agdao_elder.glb` + `agdao_elder.glb.import` (copied from officer.glb.import, paths re-hashed, no uid=)
- Build: `cd tools/blender/characters && blender -b --factory-startup --python build.py -- agdao_elder`
- Game wiring: `DataNpcsZarael._m("agdao_elder", ...)` resolves `res://assets/characters/agdao_elder.glb` (previous fallback: elder).
  NPC tint: (0.5, 0.4, 0.3) Ysenne, (0.36, 0.28, 0.42) Caius -> long robe + sleeves.
- Triangles: 10470 (budget 15k). Verts: 5520.
- Height: T-pose top 1.752 m, idle top 1.741 m (includes headgear / props).
- Glow: BH_Emissive__town_agdao_elder albedo=(1.0, 1.0, 1.0, 1.0) emission=(1.0, 1.0, 1.0, 1.0) energy=4.50

## Look
Elder, slightly stooped, gender-neutral build: long robe (tinted) with a red sash; long cream mantle over the shoulders and down the back to mid-calf, red front edges, a red fret band with teal steps along the hem; collar of overlapping teal feathers over a scarlet under-row (portrait) with a jade throat clasp; jade ear-spool discs with copper cores; white hair, white brows, a top-knot bound in cream cloth with a jade pin; sandals; carved walking staff with a stepped head, jade inset, copper bands and one thin white-glowing wire ring (rigid to hand.R).

## Materials
BH_Cloth_Primary,BH_Cloth_Accent__town_agdao_elder,BH_Skin__town_agdao_elder,BH_Cloth_Secondary__town_agdao_elder,BH_Leather__town_agdao_elder,BH_Cloth_Teal__town_agdao_elder,BH_FeatherRed__town_agdao_elder,BH_Feather__town_agdao_elder,BH_Jade__town_agdao_elder,BH_Shadow__town_agdao_elder,BH_Hair__town_agdao_elder,BH_Gold__town_agdao_elder,BH_Wood__town_agdao_elder,BH_Emissive__town_agdao_elder

## Godot import (scratch project work/lemondev/bh-029/scratch/n1/proj, Godot 4.7.2 headless)
```
GLB agdao_elder tris=10470 bones=24 mats=14 anims=6 expected=6 missing=[] length_mismatch=[]
CLIPS agdao_elder idle:4.000:none idle_adjust:4.000:none idle_look:4.000:none interact_pickup:1.000:none interact_talk:3.000:none walk:0.867:none
```
Loop modes are `none` exactly like officer/elder (same import settings); CharacterVisual sets loop modes from anim_meta at load (character_visual.gd:177).

## Deformation (Blender, evaluated mesh vs rest; stretch ratio of the worst edge, absolute growth in m)
| clip | frames | max stretch (bone) | abs grow | min z |
|---|---|---|---|---|
| idle | 121 | 2.303 (shoulder.R) | 0.042 | -0.02 |
| idle_adjust | 121 | 2.345 (shoulder.R) | 0.047 | -0.015 |
| idle_look | 121 | 2.303 (shoulder.L) | 0.049 | -0.019 |
| interact_pickup | 31 | 3.794 (thigh.L) | 0.134 | -0.111 |
| interact_talk | 91 | 2.303 (shoulder.L) | 0.04 | -0.013 |
| walk | 27 | 5.042 (thigh.L) | 0.186 | -0.05 |

Reference: existing town_elder walk 5.02 / abs 0.195 / zmin -0.051; officer walk 3.79 (same shoulder-edge baseline ~2.3).

## Build log
```
[agdao_elder] mesh 10470 tris, 135 parts, 1.5s
[agdao_elder] baked 6 actions in 6.3s
[agdao_elder] clip lengths verified (6 clips)
[agdao_elder] -> A:\Python\beyond-heroes\game\assets\characters\agdao_elder.glb (1.2 MB)
[build] done in 9.3s
```

## Evidence
- `agdao_elder_rest_iso.png`: T-pose front/back, idle at 4 yaws, head close-ups, gameplay camera 54 deg at 16 m / 22 m.
- `agdao_elder_clips.png`: idle_look, interact_talk, walk, interact_pickup at 4 times each.

## Known limitations
Long robe dips below the floor in interact_pickup (same as the existing town_elder).
Workbench previews only (material colours; BH_Cloth_Primary shows the preview colour, the game tints it).
