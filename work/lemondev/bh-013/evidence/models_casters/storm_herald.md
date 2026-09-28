# Storm Herald (`storm_herald`)

- Module: `tools/blender/characters/enemy_storm_herald.py` (Builder A2; kits: `enemy_bandit_cutthroat` SB/head/arms/belt/boots, `enemy_ashen_cultist` robe, `enemy_bloodbinder` domed hair cap, `enemy_hollow_soldier` cloth weights, `kit_a_common`, `kit_e_orrery`)
- GLB: `game/assets/characters/storm_herald.glb` (3.3 MB) + `storm_herald.glb.import` (necromancer settings, own path hash, no uid, `nodes/use_name_suffixes=false`)
- Triangles: 15584 (budget 20k); 24 bones; 8 materials; 8068 verts
- Height: 2.0 m to the tip of the front crown spike (SCALE = 2.0 / 1.93; T-pose top 2.003, idle f0 1.996); head top ~1.9 m. Staff tip + spark ~2.3 m in idle_staff.
- Clips (48): the 42 shared enemy base clips + `staff_1 staff_heavy cast_quick cast_area cast_heavy cast_ultimate`
- Weapon: copper lightning-rod staff rigid on `weapon.R` (grip at origin, ~1.0 m below / 1.3 m above the hand incl. the spark; weapon verts deform, `K.enable_weapon_deform`). Left hand open. Stance clip: `idle_staff`.

## Palette (`storm_herald`, exported as `BH_*__storm_herald`)
| material | use |
|---|---|
| BH_Cloth_Primary (0.2, 0.21, 0.23) | slate-grey upper robe, short sleeves, skirt hem band |
| BH_Cloth_Secondary (0.05, 0.12, 0.3) | storm-blue skirt (ragged hem), two-tier shoulder mantles, tabard, trousers |
| BH_Bronze (0.78, 0.38, 0.19) metallic 0.85 = copper | crown + spikes, mantle hem trims, tabard cords + lightning-bolt appliqué, forearm coils and rings, staff (shaft, collars, knot, helix, prongs), belt buckle, throat clasp |
| BH_Skin (0.6, 0.46, 0.38) | weathered face, bare forearms, hands |
| BH_Hair (0.72, 0.74, 0.76) | storm-white domed hair, back hair, long forked beard + moustache |
| BH_Leather / BH_Shadow | belt, boots, staff grip / sockets, nails |
| BH_Emissive (0.2, 0.88, 1.0) x11 | electric cyan: floating spark above the staff prongs, staff knot ring, crown gem + spike beads, eyes, forearm-coil nodes, throat clasp, bolt tip |

## What makes it distinct
Silhouette: two tiers of wide stiff shoulder mantles with jagged lightning-point hems (broad, stepped shoulders no other caster has), a spiked copper crown with a tall centre spike, a long white forked beard, and a tall copper staff with a coil and a floating cyan spark well above the head. Palette: storm-blue + slate + copper with electric cyan - the only copper-metal caster; versus the orc shaman (also pale-cyan lightning) it is a tall robed human elder with a copper rod staff rather than a green-skinned orc with wraps and feathers.

## Evidence
- `storm_herald_rest_iso.png`: T-pose front/back, idle_staff at 4 yaws, head close-ups, gameplay camera 54 deg at 16 / 22 m.
- `storm_herald_clips.png`: idle_staff, every attack clip, hit_heavy, death_back.
- `logs/storm_herald_metrics.json`: worst absolute edge growth 0.057 m (staff_1 / staff_heavy, sleeve at the shoulder); the mantles stay under 0.055 m.
- `logs/godot_check_storm_herald.txt`: scratch Godot 4.7.2 project, 0 import errors, all 48 clips present with the meta lengths, `block_loop` keeps its name; loops applied at runtime from the meta.

## Build log
```
[storm_herald] mesh 15584 tris, 135 parts, 1.4s
[storm_herald] baked 48 actions in 22.2s
00:49:41 | INFO: Finished glTF 2.0 export in 3.7133374214172363 s
[storm_herald] clip lengths verified (48 clips)
[storm_herald] -> A:\Python\beyond-heroes\game\assets\characters\storm_herald.glb (3.3 MB)
[build] done in 27.8s
```

## Revision passes
1. The kit hair cap sat flat and boxy on the narrowed head, and the grey skin merged with the white hair into one grey block. Switched to the bloodbinder's domed hair cap and warmed the skin tone. The first sleeve (`bell_sleeve` with a short end) folded back on itself and was replaced by a short slate sleeve with a copper cuff, so the coiled bare forearms show.

## Known limitations
- The mantles are weighted chest -> shoulder/upper arm. In arms-overhead clips (cast_ultimate, staff_heavy wind-up) the outer mantle points lift with the arm and stretch a little at the shoulder.
- The copper hem trim follows the jagged hem only on its outside, so from some angles it reads as separate copper chevrons instead of one continuous edge.
- The spark is a static emissive shape (a ball plus jagged shards) rigid on the staff. Any flicker or light has to come from the game (e.g. an OmniLight3D at the staff tip).
