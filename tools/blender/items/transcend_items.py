"""Class Transcendence item models: the thirty-six class pieces (game/src/data/data_transcendence_gear.gd) as item specs
for build_items.py (dropped and held models, icon renders). Each piece is in its class's metals and colours; the
worn armours themselves are tools/blender/hero/hero_wear_transcend.py, the jewellery is shared with it (JEWELS).
"""
import artisan_weapons as AW
import item_gear as G
import item_weapons as IW

WEAPONS = {
    "tc_crownward_longsword": (IW.sword, {"len": 0.86, "blade": "bright", "guard": "winged", "guard_half": 0.13, "guard_mat": "gold",
                                          "grip_mat": "navy", "pommel": "disc", "pommel_mat": "gold", "gem": "sapphire"}),
    "tc_dreadmarshal_greatsword": (IW.sword, {"len": 1.2, "z0": 0.135, "w": (0.08, 0.055), "thick": 0.009, "blade": "blackiron",
                                              "guard": "winged", "guard_half": 0.2, "guard_curve": 0.04, "guard_mat": "darksteel",
                                              "grip_mat": "redleather", "pommel_mat": "darksteel", "gem": "ruby", "serrate": True}),
    "tc_dawnstar_longsword": (IW.sword, {"len": 0.9, "blade": "bright", "shape": "waisted", "guard": "winged", "guard_half": 0.14,
                                         "guard_mat": "gold", "grip_mat": "white", "pommel_mat": "gold", "gem": "topaz", "glow": "holy"}),
    "tc_trailkeeper_bow": (IW.bow, {"len": 0.78, "bend": 0.12, "recurve": 0.06, "limb_mat": "darkwood", "orn": "brass"}),
    "tc_briarheart_bow": (IW.bow, {"len": 0.82, "bend": 0.13, "recurve": 0.03, "limb_mat": "wood", "orn": "emerald"}),
    "tc_starfall_crossbow": (AW.crossbow, {"design": 8}),
    "tc_runebound_staff": (IW.staff, {"wood": "darkwood", "head": "prongs", "metal": "silver", "gem": "amethyst"}),
    "tc_prismatic_staff": (IW.staff, {"wood": "ash", "head": "star", "metal": "gold", "gem": "sapphire"}),
    "tc_eventide_staff": (IW.staff, {"wood": "darkwood", "head": "shards", "metal": "blackiron", "gem": "amethyst"}),
    "tc_gloamfang_dagger": (IW.dagger, {"len": 0.3, "blade": "darksteel", "guard_mat": "silver", "gem": "amethyst"}),
    "tc_wraithedge_dagger": (IW.dagger, {"len": 0.31, "shape": "crescent", "blade": "moonsteel", "guard_mat": "silver", "gem": "pearl"}),
    "tc_crimson_oath_dagger": (IW.dagger, {"len": 0.29, "blade": "steel", "guard_mat": "gold", "gem": "ruby", "grip_mat": "redleather"}),
}

ARMOR = {
    "tc_royal_guard_cuirass": (G.chest, {"kind": "plate", "mat": "blued", "trim": "gold", "belt": "darkleather", "glow": "sapphire"}),
    "tc_black_dominion_plate": (G.chest, {"kind": "plate", "mat": "blackiron", "trim": "crimson", "belt": "redleather", "glow": "ruby"}),
    "tc_sanctified_plate": (G.chest, {"kind": "plate", "mat": "bright", "trim": "gold", "belt": "white", "glow": "holy"}),
    "tc_trackers_leathers": (G.chest, {"kind": "brigandine", "mat": "forest", "rivet": "brass", "belt": "leather", "trim": "tan"}),
    "tc_livingwood_leathers": (G.chest, {"kind": "brigandine", "mat": "forest", "rivet": "bronze", "belt": "leather", "trim": "ash"}),
    "tc_constellation_leathers": (G.chest, {"kind": "robe", "mat": "navy", "trim": "silver", "len": 0.8, "stars": "pearl", "belt": "darkleather"}),
    "tc_arcanist_vestments": (G.chest, {"kind": "robe", "mat": "violet", "trim": "silver", "len": 0.95, "glow": "amethyst", "belt": "paleg"}),
    "tc_archmage_robes": (G.chest, {"kind": "robe", "mat": "navy", "trim": "gold", "len": 0.95, "glow": "sapphire", "belt": "white"}),
    "tc_riftwoven_robes": (G.chest, {"kind": "robe", "mat": "black", "trim": "paleg", "len": 0.95, "glow": "amethyst", "belt": "violet"}),
    "tc_nightstalker_leathers": (G.chest, {"kind": "brigandine", "mat": "violet", "rivet": "silver", "belt": "darkleather", "trim": "darkleather"}),
    "tc_afterimage_mantle": (G.chest, {"kind": "robe", "mat": "silk", "trim": "silver", "len": 0.85, "belt": "darkleather"}),
    "tc_sanguine_leathers": (G.chest, {"kind": "robe", "mat": "crimson", "trim": "black", "len": 0.8, "glow": "ruby", "belt": "crimson"}),
}

JEWELS = {
    "tc_oathkeeper_seal": (G.ring, {"mat": "gold", "kind": "crown", "gem": "sapphire", "band": 0.0026}),
    "tc_dread_command_signet": (G.ring, {"mat": "blackiron", "kind": "spiked", "spike": "darksteel", "gem": "ruby"}),
    "tc_sunward_reliquary": (G.amulet, {"kind": "sun", "mat": "gold", "inner": "sunsteel", "gem": "topaz", "chain": "gold"}),
    "tc_quarry_compass": (G.charm, {"kind": "talisman", "mat": "brass", "gem": "topaz", "cord": "leather"}),
    "tc_wildroot_pendant": (G.amulet, {"kind": "medallion", "mat": "darkwood", "gem": "emerald", "chain": "rope"}),
    "tc_comet_lens": (G.charm, {"kind": "rune", "mat": "moonsteel", "glow": "ice", "cord": "darkleather"}),
    "tc_runic_focus": (G.charm, {"kind": "rune", "mat": "slate", "glow": "portal", "cord": "darkleather"}),
    "tc_convergence_prism": (G.amulet, {"kind": "cage", "mat": "gold", "chain": "gold"}),
    "tc_horizon_core": (G.charm, {"kind": "idol", "mat": "slate", "glow": "portal", "band": "silver", "cord": "darkleather"}),
    "tc_silent_trail_charm": (G.charm, {"kind": "knot", "mat": "darksteel", "gem": "amethyst", "cord": "black"}),
    "tc_reapers_glass": (G.charm, {"kind": "hourglass", "mat": "silver", "sand": "ice", "cord": "darkleather"}),
    "tc_bloodmoon_signet": (G.ring, {"mat": "darksteel", "kind": "moonstone", "gem": "ruby"}),
}

IW.SPECS.update(WEAPONS)
G.GEAR.update(ARMOR)
G.GEAR.update(JEWELS)
