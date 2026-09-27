# War Totem (war_totem.glb)

Generator: `tools/blender/creatures/build_war_totem.py` -> `game/assets/characters/war_totem.glb`

- Size: 2.2 m (horn tips 2.22 m, skull crown ~2.05 m); crossbar 0.92 m + tusk tips; base mound 0.84 m across.
- Triangles: 5284; vertices 2874; bones 9 (root non-deform).
- Materials: BH_Bone__war_totem, BH_Cloth_Primary__war_totem, BH_Cloth_Secondary__war_totem, BH_DarkSteel__war_totem, BH_Emissive__war_totem, BH_Fur__war_totem, BH_Gold__war_totem, BH_Hair__war_totem, BH_Horn__war_totem, BH_Leather__war_totem, BH_Shadow__war_totem, BH_Stone__war_totem, BH_Wood__war_totem
- Bones: `root`, `base`, `pole`, `top`, `rune`, `cord.1`, `cord.2`, `cord.3`, `cord.4`
- Stationary (no locomotion clips). `rune` bone scales the emissive rune stone for flares; cords hang toward world-down with per-cord swing.
- Death end pose: lowest pole/top bone point z 0.000 m (lies on the ground, skull cracked off).

## Clips

| clip | frames | length (s) | loop | hits (s) | ground_speed (m/s) |
|---|---|---|---|---|---|
| `idle` | 90 | 3.000 | yes | - | - |
| `totem_pulse` | 24 | 0.800 | no | - | - |
| `hit_light` | 12 | 0.400 | no | - | - |
| `hit_heavy` | 18 | 0.600 | no | - | - |
| `death` | 45 | 1.500 | no | - | - |
| `alert` | 18 | 0.600 | no | - | - |
