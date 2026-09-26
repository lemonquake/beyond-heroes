# orc_reaver (Builder C)

- Source: `tools/blender/characters/enemy_orc_reaver.py`
- GLB: `game/assets/characters/orc_reaver.glb` (exported with `build.py -- orc_reaver`; "clip lengths verified (46 clips)")
- Standing height: **~1.95 m** at the skull, **2.07 m** to the tip of the topknot
- Triangles: **8,486**
- Materials (`__orc_reaver`): BH_Skin (green-grey), BH_Leather, BH_Bone, BH_Cloth_Primary (Sulvane red: arm band and war-paint), BH_Cloth_Secondary (trousers), BH_DarkSteel, BH_Steel (axe bits), BH_Wood (haft), BH_Hair (topknot), BH_Emissive (small eye glints), BH_Shadow
- Clips: base set plus `axe_1 axe_3 axe_heavy war_cry` (idle stance: `idle_2h`)
- Features: broad shoulders with big deltoids, a leather harness crossing chest and back, a rib-bone chest plate with a skull boss, a leather war-kilt (7 tassets), bone knee guards, leather-wrapped shins and boots, bone-studded bracers, a spiked (3 bone spikes) layered pauldron on the left shoulder, a red Sulvane cloth knotted on the right upper arm with hanging tails, a red war-paint band across the eyes, lower tusks, pointed ears with iron rings, and a topknot on a shaved skull. The heavy two-bladed war-axe (haft -0.46 to +1.0 m around the grip) is rigid to `weapon.R`; the left hand's two-handed grip lands on the haft.
- Evidence: `orc_reaver_rest_iso.png`, `orc_reaver_clips.png` (idle_2h, walk, axe_heavy, death_crumple)
- Known issues: in `death_crumple` the axe stays in the hand and its haft points up from the ground; the knight's weapons behave the same way.
