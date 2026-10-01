# terax — Terax, Warden of Agdao (bh-029, Builder N1)

- Module: `tools/blender/characters/town_terax.py` (palette `town_terax`, `TINTABLE = ("BH_Cloth_Primary",)`,
  `CLIPS_ONLY = TOWN_CLIPS`) — also holds the shared Zarael townsfolk kit (feather, fret_band, wrap_spiral, WHITE_GLOW)
- GLB: `game/assets/characters/terax.glb` + `terax.glb.import` (copied from officer.glb.import, paths re-hashed, no uid=)
- Build: `cd tools/blender/characters && blender -b --factory-startup --python build.py -- terax`
- Game wiring: `DataNpcsZarael._m("terax", ...)` resolves `res://assets/characters/terax.glb` (previous fallback: officer).
  NPC tint: (0.3, 0.5, 0.4) jade green -> under-tunic + kilt.
- Triangles: 14688 (budget 15k). Verts: 7735.
- Height: T-pose top 2.299 m, idle top 2.287 m (includes headgear / props).
- Glow: BH_Emissive__town_terax albedo=(1.0, 1.0, 1.0, 1.0) emission=(1.0, 1.0, 1.0, 1.0) energy=4.50

## Look
Broad warrior-guard: cream/ochre quilted armour vest (raised quilt ridges) with a brick-red stepped-fret hem and rolled red collar; jade-green under-tunic and kilt (tinted) with a cream front flap and fret hem; short teal feather shoulder cape with hanging feathers tipped scarlet; bronze vambraces wound with copper wire, a thin white-glowing wire at each wrist; gold armbands; jade pendant with a gold step glyph; jade-green crested helm with gold fret rim and a fan of seven teal feathers tipped red (portrait); short dark hair, scar through the right brow; laced sandals, leg wraps, bronze knee guards; obsidian-bladed spear slung diagonally across the back (rigid to chest, feather tassel).

## Materials
BH_Cloth_Primary,BH_Cloth_Secondary__town_terax,BH_Cloth_Accent__town_terax,BH_Gold__town_terax,BH_Skin__town_terax,BH_Bronze__town_terax,BH_Emissive__town_terax,BH_Leather__town_terax,BH_Feather__town_terax,BH_FeatherRed__town_terax,BH_Jade__town_terax,BH_Wood__town_terax,BH_Obsidian__town_terax,BH_Shadow__town_terax,BH_Scar__town_terax,BH_Hair__town_terax

## Godot import (scratch project work/lemondev/bh-029/scratch/n1/proj, Godot 4.7.2 headless)
```
GLB terax tris=14688 bones=24 mats=16 anims=6 expected=6 missing=[] length_mismatch=[]
CLIPS terax idle:4.000:none idle_adjust:4.000:none idle_look:4.000:none interact_pickup:1.000:none interact_talk:3.000:none walk:0.867:none
```
Loop modes are `none` exactly like officer/elder (same import settings); CharacterVisual sets loop modes from anim_meta at load (character_visual.gd:177).

## Deformation (Blender, evaluated mesh vs rest; stretch ratio of the worst edge, absolute growth in m)
| clip | frames | max stretch (bone) | abs grow | min z |
|---|---|---|---|---|
| idle | 121 | 2.467 (shoulder.R) | 0.054 | -0.0 |
| idle_adjust | 121 | 2.674 (shoulder.R) | 0.064 | -0.0 |
| idle_look | 121 | 2.467 (shoulder.R) | 0.054 | -0.0 |
| interact_pickup | 31 | 3.207 (thigh.L) | 0.119 | -0.001 |
| interact_talk | 91 | 2.467 (shoulder.R) | 0.054 | -0.0 |
| walk | 27 | 3.488 (thigh.L) | 0.129 | -0.002 |

Reference: existing town_elder walk 5.02 / abs 0.195 / zmin -0.051; officer walk 3.79 (same shoulder-edge baseline ~2.3).

## Build log
```
[terax] mesh 14688 tris, 184 parts, 1.8s
[terax] baked 6 actions in 5.8s
[terax] clip lengths verified (6 clips)
[terax] -> A:\Python\beyond-heroes\game\assets\characters\terax.glb (1.4 MB)
[build] done in 9.3s
```

## Evidence
- `terax_rest_iso.png`: T-pose front/back, idle at 4 yaws, head close-ups, gameplay camera 54 deg at 16 m / 22 m.
- `terax_clips.png`: idle_look, interact_talk, walk, interact_pickup at 4 times each.

## Known limitations
Spear and crest add height (AABB top 2.30 m; body ~1.84 m). Spear is rigid to the chest bone, so it follows torso sway only. Helm replaces visible hair on top (portrait shows a helm).
Workbench previews only (material colours; BH_Cloth_Primary shows the preview colour, the game tints it).
