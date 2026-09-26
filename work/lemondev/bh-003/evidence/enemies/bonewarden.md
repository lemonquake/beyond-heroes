# bonewarden (builder A)

- GLB: `game/assets/characters/bonewarden.glb`, module `enemy_bonewarden.py`
- Standing height: **1.95 m** to the helm comb (skeleton `proportions(1.9/1.8)`); suggested `model_scale` 1.0
- Tris: 13,096 (elite budget 10k–16k)
- Materials (`__bonewarden`): BH_Bone, BH_Rust, BH_DarkSteel (verdigris iron), BH_Wood (coffin wood), BH_Bronze (verdigris nameplate), BH_Cloth_Primary (drab), BH_Leather, BH_Shadow, BH_Emissive (teal eyes)
- Clips: base set + `shield_bash axe_1`; idle stance `idle_shield`
- Distinctive: broad rusted half-plate (dented breastplate with ridge, gorget, big layered pauldrons, couters, faulds, poleyns, greaves, iron boots, gauntlets) over a heavy skeleton; bare lumbar spine between breastplate and belt; **tower shield = coffin lid** (tapered coffin outline, plank grooves, three iron bands with rivets, bronze nameplate, iron oath-cross) on `weapon.L`, face outward; heavy bearded axe with back spike on `weapon.R`; bascinet with the visor broken off on the right side (teal eye visible, left eye behind the slit); three chains + padlock hanging from the belt; tattered tabard.
- Evidence: `bonewarden_rest_iso.png`, `bonewarden_clips.png` (idle_shield, shield_bash, axe_1, death_crumple), `bonewarden_closeup.png`
- Known issues: in `idle_shield` the raised axe is mostly hidden behind the tall lid from the front; chains are skinned (hips/thighs), not simulated; weapon sockets set to deform via `finish_mesh`.
