# agdao_vendor — Agdao traders (Dorrit Vask, Brisa Kettle, Sorrel) (bh-029, Builder N1)

- Module: `tools/blender/characters/town_agdao_vendor.py` (palette `town_agdao_vendor`, `TINTABLE = ("BH_Cloth_Primary",)`,
  `CLIPS_ONLY = TOWN_CLIPS`)
- GLB: `game/assets/characters/agdao_vendor.glb` + `agdao_vendor.glb.import` (copied from officer.glb.import, paths re-hashed, no uid=)
- Build: `cd tools/blender/characters && blender -b --factory-startup --python build.py -- agdao_vendor`
- Game wiring: `DataNpcsZarael._m("agdao_vendor", ...)` resolves `res://assets/characters/agdao_vendor.glb` (previous fallback: merchant / fisher).
  NPC tint: (0.5, 0.2, 0.14) Dorrit, (0.18, 0.4, 0.36) Brisa, (0.2, 0.36, 0.42) Sorrel -> tunic + sleeves.
- Triangles: 9200 (budget 15k). Verts: 4903.
- Height: T-pose top 1.870 m, idle top 1.859 m (includes headgear / props).
- Glow: BH_Emissive__town_agdao_vendor albedo=(1.0, 1.0, 1.0, 1.0) emission=(1.0, 1.0, 1.0, 1.0) energy=4.50

## Look
Market woman: long woven tunic (tinted) to mid-calf with an ochre neck band and an ochre hem band with cream fret steps; cream apron with two red stripes and a red waist sash; short sleeves with ochre hems, bare forearms, copper bracelets (one thin white-glowing wire on the right forearm); three bead strands (turquoise / coral / jade runs); woven wicker shoulder bag on a red cross strap at the left hip with greens poking out; tall striped headwrap (red, teal, ochre, red, cream) with a jade bead (portrait); jade drop earrings; sandals.

## Materials
BH_Cloth_Primary,BH_Cloth_Accent__town_agdao_vendor,BH_Cloth_Secondary__town_agdao_vendor,BH_Cloth_Red__town_agdao_vendor,BH_Skin__town_agdao_vendor,BH_Gold__town_agdao_vendor,BH_Emissive__town_agdao_vendor,BH_Leather__town_agdao_vendor,BH_Turquoise__town_agdao_vendor,BH_Coral__town_agdao_vendor,BH_Jade__town_agdao_vendor,BH_Wicker__town_agdao_vendor,BH_Cloth_Teal__town_agdao_vendor,BH_Shadow__town_agdao_vendor,BH_Hair__town_agdao_vendor

## Godot import (scratch project work/lemondev/bh-029/scratch/n1/proj, Godot 4.7.2 headless)
```
GLB agdao_vendor tris=9200 bones=24 mats=15 anims=6 expected=6 missing=[] length_mismatch=[]
CLIPS agdao_vendor idle:4.000:none idle_adjust:4.000:none idle_look:4.000:none interact_pickup:1.000:none interact_talk:3.000:none walk:0.867:none
```
Loop modes are `none` exactly like officer/elder (same import settings); CharacterVisual sets loop modes from anim_meta at load (character_visual.gd:177).

## Deformation (Blender, evaluated mesh vs rest; stretch ratio of the worst edge, absolute growth in m)
| clip | frames | max stretch (bone) | abs grow | min z |
|---|---|---|---|---|
| idle | 121 | 2.313 (shoulder.L) | 0.041 | -0.0 |
| idle_adjust | 121 | 2.357 (shoulder.R) | 0.049 | -0.0 |
| idle_look | 121 | 2.313 (shoulder.L) | 0.048 | -0.0 |
| interact_pickup | 31 | 3.539 (hips) | 0.134 | -0.0 |
| interact_talk | 91 | 2.313 (shoulder.L) | 0.04 | -0.0 |
| walk | 27 | 4.161 (thigh.L) | 0.156 | -0.002 |

Reference: existing town_elder walk 5.02 / abs 0.195 / zmin -0.051; officer walk 3.79 (same shoulder-edge baseline ~2.3).

## Build log
```
[agdao_vendor] mesh 9200 tris, 97 parts, 1.2s
[agdao_vendor] baked 6 actions in 6.2s
[agdao_vendor] clip lengths verified (6 clips)
[agdao_vendor] -> A:\Python\beyond-heroes\game\assets\characters\agdao_vendor.glb (1.1 MB)
[build] done in 8.8s
```

## Evidence
- `agdao_vendor_rest_iso.png`: T-pose front/back, idle at 4 yaws, head close-ups, gameplay camera 54 deg at 16 m / 22 m.
- `agdao_vendor_clips.png`: idle_look, interact_talk, walk, interact_pickup at 4 times each.

## Known limitations
Same model for all three traders; only the tunic colour changes. The bag sits behind the left hip to stay clear of the arm swing.
Workbench previews only (material colours; BH_Cloth_Primary shows the preview colour, the game tints it).
