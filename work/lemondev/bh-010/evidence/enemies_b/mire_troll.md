# mire_troll: Mire Troll (bh-010, Builder B)

- Module: `tools/blender/characters/enemy_mire_troll.py` (kit: tools/blender/creatures/greenskin_kit.py). GLB: `game/assets/characters/mire_troll.glb` (3.3 MB, 48 clips, clip lengths verified)
- Height: 2.81 m rest, 2.79 m idle (T-pose span 4.55 m). Knuckles hang at about knee height in idle.
- Tris: 15,908 (8,465 verts, 237 parts)
- Attack clips: axe_1, axe_2, boss_slam, cast_heavy, boss_roar, boss_charge (+ base set)
- Palette (`mire_troll`): grey-green hide (Skin), dark mottling blotches (Flesh), moss (Fur), hanging swamp weed and hair (Hair), wet mud up the shins, on the forearms and on the hands (Ichor), roots and vine belt (Wood), rotten-hide loin wrap (Leather), tusks and bone trophies (Bone), claws and toenails (Horn). BH_Emissive = tiny yellow-green eyes only.
- Shape: lean waist and ribbed flanks. A high moss-covered hump rises above and behind a small head that is thrust forward and down (hump weighted to the chest; the neck tube blends chest > neck > head). Long drooping nose, underbite with two jutting lower tusks, drooping ears, tooth necklace, skull and long-bone trophies on the belt. Huge half-open four-fingered clawed hands, thick legs, flat four-toed feet.
- Distinct from the Ogre Crusher: no chains, collar, shackles or club; leaner, longer-limbed, hunched with the head forward, mossy and wet. See the lineup tiles in mire_troll_rest_iso.png.
- Deformation (mire_troll_audit.txt): worst stretch 2.78x, dL 19.9 cm at the hip wrap under the thighs in deep crouch / run. Ogre Crusher baseline on the same audit is 7.45x / 58.4 cm (baseline_ogre_crusher_audit.txt). Loin flaps are split per leg (front halves follow their thigh; back halves stay mostly on the hips).
- Evidence: mire_troll_rest_iso.png, mire_troll_head_closeup.png, mire_troll_clips.png (idle, 6 attacks, hit_heavy, death_back), mire_troll_audit.txt
- Limitations: all clips are the shared upright humanoid clips, so the hunch comes from the model (hump + forward head) rather than a hunched pose. The head sits 0.36 m in front of the head joint, so head rotations in roar and hits swing it through a wider arc. boss_slam dips 9 cm below z=0 at impact.
