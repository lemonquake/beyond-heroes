# Barrow Jarl (`barrow_jarl`)
- Module: `tools/blender/characters/enemy_barrow_jarl.py` -> `game/assets/characters/barrow_jarl.glb` (+ `.glb.import`)
- Triangles 19526 (budget 20k); ~2.1 m to the helm crown (K 1.13, broadened torso), horns ~0.1 m higher
- Clips (47): base set + `shield_bash axe_1 axe_2 axe_heavy war_cry`
- Weapons: bearded axe rigid on weapon.R; round shield rigid on weapon.L, face -Y (weapon space), faded frost rune in BH_Emissive
- Palette (`__barrow_jarl`): iron scales (BH_DarkSteel), white rime (BH_Stone), frozen grey-brown fur (BH_Fur), white frozen braids (BH_Hair), gold rings (BH_Gold), bone skull, ivory horns (BH_Horn), faded frost-blue shield paint (BH_Cloth_Primary), cold blue eyes/rune (BH_Emissive x7)
- Distinct: broad horned-helm silhouette with spectacle face guard, skull face, braided white beard with gold rings and icicle tips, staggered iron scale coat + scale skirt, thick fur collar/mantle with icicle hem, belt of gold rings, big painted round shield.
- Evidence: `barrow_jarl_rest_iso.png` (idle_shield stance), `barrow_jarl_clips.png`, `logs/build_barrow_jarl.log`
- Limitations: fur collar/shoulder tufts are chest-rigid (upper arm passes under them when raised); beard is head->chest blended and can touch the chest on head pitch; scales are individually per-vertex weighted so the skirt split shows gaps in wide strides.
