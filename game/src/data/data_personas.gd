class_name DataPersonas
## bh-031: who everyone is on the hero's body (Persona). Every townsperson has their own face, figure, hair, clothes
## and colours; humanoid monsters are built from their family (bandits, the dead, cultists, orcs ...) with their own
## variations, bosses wear the regalia of a boss collection. Format: see Persona.
##
## Not drawn on the hero body (kept on their own models, they are not people): golems and sentinels, the fungal and
## thorn folk, the bloated abominations and the giants' spawn, the wirewright constructs, the Jade Guardian.

# ---------------------------------------------------------------------------------------------------- townsfolk
const NPCS := {
	# Class Transcendence: Grand Master Edran Vale of the Guild House
	"grand_master_edran": {"look": {"hair": "slick", "hair_color": "c9c6bf", "beard": "full", "beard_color": "bdb9b0", "skin": "c8916d",
		"eye": "keen", "eye_color": "4a5a6a", "brow": "bushy", "brow_color": "bdb9b0", "height": 1.03, "build": 0.2, "muscle": 0.3,
		"jaw_wide": 0.4, "marking": "scar", "marking_color": "7a4a3a"},
		"wear": ["magister_robe", "chain_shirt", "warden_greave", "gold_amulet"],
		"dye": {"cloth": "2b3550", "trim": "1d2236", "gold": "d8b46a", "metal": "c8c8cc", "leather": "3a2a1e"}, "main": "runed_sword"},
	"maelis": {"f": true, "look": {"hair": "topknot", "hair_color": "d8d6d0", "brow": "thin", "brow_color": "bdbab2", "skin": "c8916d",
		"eye": "sleepy", "eye_color": "5b4a3a", "cheeks": -0.6, "chin_long": 0.3, "nose_long": 0.4, "height": 0.9, "build": -0.5,
		"muscle": -0.6, "mouth_smile": 0.3},
		"wear": ["magister_robe", "silk_undershirt", "soft_boot", "star_pendant"],
		"dye": {"cloth": "6e2c22", "trim": "2f2420", "leather": "4a3426", "gold": "e0c080"}, "main": "pilgrims_staff"},
	"tovin": {"look": {"hair": "crop", "hair_color": "4a2f1d", "beard": "moustache", "skin": "d9a585", "belly": 1.4, "build": 0.6,
		"cheeks": 0.8, "nose_size": 0.6, "mouth_smile": 1.0, "eye": "round", "brow": "bushy", "height": 0.97},
		"wear": ["silk_undershirt", "traveler_coat", "scholars_breeches", "soft_boot", "copper_ring"],
		"dye": {"cloth": "8a6a3a", "trim": "3a3024", "leather": "6a4a30"}},
	"brannoc": {"look": {"hair": "bald", "beard": "full", "beard_color": "3a2414", "skin": "9b6a4f", "muscle": 1.3, "build": 0.7,
		"hands": 1.25, "jaw_wide": 0.8, "brow_heavy": 0.8, "marking": "scar", "marking_color": "6a3a2a", "height": 1.06},
		"wear": ["brigandine", "hide_leggings", "wayfarer_boot", "iron_gauntlet"],
		"dye": {"leather": "3a2618", "cloth": "5a3a28", "metal": "8a8a8a"}, "main": "smiths_warhammer"},
	"seris": {"f": true, "look": {"hair": "long", "hair_color": "e6e6e8", "hair_length": 1.3, "skin": "c9b8b0", "eye": "doe",
		"eye_color": "20c0d0", "eye_glow": 0.5, "brow": "arched", "marking": "rites", "marking_color": "2f4f8c", "ears_point": 0.6},
		"wear": ["sage_robe", "sage_leggings", "sage_boots", "seers_circlet", "tidecaller_moonstone"],
		"dye": {"cloth": "2c4c7a", "trim": "151a2e"}, "main": "storm_staff"},
	"hald": {"look": {"hair": "crop", "hair_color": "6b4423", "beard": "chops", "skin": "c8916d", "jaw_wide": 0.9, "brow_heavy": 0.5,
		"eye": "keen", "marking": "scar", "marking_color": "7a4a3a", "muscle": 0.7, "height": 1.05},
		"wear": ["warden_plate", "padded_gambeson", "warden_cuisses", "warden_greave", "iron_gauntlet"],
		"dye": {"cloth": "7a1a1a", "metal": "d0d4dc"}, "main": "knights_arming_sword", "off": "warden_kite_shield"},
	"stranger": {"look": {"hair": "slick", "hair_color": "0f0c0b", "skin": "b27e62", "eye": "fierce", "eye_color": "c89a2a",
		"beard": "goatee", "marking": "band", "marking_color": "14100e", "cheeks": -0.6},
		"wear": ["traveler_coat", "nightweave_leggings", "soft_boot", "linen_hood", "silk_glove", "viper_coil_ring"],
		"dye": {"cloth": "2a2430", "trim": "121014", "leather": "2a1e18"}},
	"hesta": {"f": true, "look": {"hair": "curly", "hair_color": "8c2f1a", "skin": "e8bfa2", "cheeks": 0.8, "belly": 0.8, "build": 0.5,
		"mouth_smile": 1.2, "marking": "rosy", "marking_color": "c2605a", "eye": "round", "eye_color": "3f6fa8"},
		"wear": ["apprentice_robe", "soft_boot", "copper_ring"],
		"dye": {"cloth": "3f5a3a", "trim": "e8e2d2", "leather": "5a3a28"}},
	"fennick": {"look": {"hair": "sidepart", "hair_color": "d4a853", "skin": "e8bfa2", "beard": "goatee", "eye": "keen",
		"eye_color": "5a7a3a", "mouth_smile": 1.4, "build": -0.5, "muscle": -0.3},
		"wear": ["traveler_coat", "silk_undershirt", "longstrider_leggings", "wayfarer_boot", "windrider_feather"],
		"dye": {"cloth": "7a2a6a", "trim": "2a1430", "leather": "6a4a30"}},
	"marrow": {"look": {"hair": "tonsure", "hair_color": "c8c8c8", "beard": "full", "beard_color": "d0d0d0", "skin": "9b6a4f",
		"cheeks": -0.3, "nose_size": 0.9, "nose_long": 0.4, "eye": "sleepy", "brow": "bushy", "brow_color": "d0d0d0", "height": 0.94,
		"belly": 0.5},
		"wear": ["padded_gambeson", "traveler_coat", "linen_trousers", "wayfarer_boot", "wayfarers_knot"],
		"dye": {"cloth": "4a5a6a", "trim": "2a3038", "leather": "5a4030"}},
	"venna": {"f": true, "look": {"hair": "crop", "hair_color": "8a8a8e", "skin": "80523a", "eye": "keen", "eye_color": "7a5a2c",
		"marking": "scar", "marking_color": "5a3a2a", "muscle": 0.6, "jaw_wide": 0.2, "height": 1.0},
		"wear": ["brigandine", "silk_undershirt", "riveted_legplates", "warden_greave", "war_talisman"],
		"dye": {"cloth": "2f4f6a", "leather": "3a2618"}, "main": "duelist_sabre"},
	"rhea": {"f": true, "look": {"hair": "braids", "hair_color": "2b1d14", "skin": "c8916d", "eye": "fierce", "eye_color": "3a7a6a",
		"brow": "straight", "jaw_wide": 0.1, "muscle": 0.5, "height": 1.02},
		"wear": ["warden_plate", "chain_shirt", "commander_cuisses", "warden_greave", "guardian_gauntlets", "bulwark_locket"],
		"dye": {"cloth": "1f3f7a", "metal": "e0e6f0", "gold": "e0c080"}, "main": "sunsteel_blade"},
	"dax": {"look": {"hair": "spiky", "hair_color": "6b4423", "beard": "goatee", "skin": "d9a585", "belly": 0.7, "nose_wide": 0.6,
		"ears_out": 0.8},
		"wear": ["chain_shirt", "iron_hauberk", "mail_chausses", "soft_boot"],
		"dye": {"cloth": "1f3f7a", "trim": "16223a"}},
	"oren": {"look": {"hair": "sidepart", "hair_color": "8a8a8e", "beard": "long", "beard_color": "9a9a9e", "beard_length": 0.6,
		"skin": "e8bfa2", "eye": "sleepy", "brow": "thin", "build": -0.6, "muscle": -0.6, "nose_long": 0.6, "chin_long": 0.3},
		"wear": ["magister_robe", "runeweave_vest", "magister_silks", "soft_boot", "gold_amulet"],
		"dye": {"cloth": "8a5a1a", "trim": "2a1a10"}, "main": "sunspire_staff"},
	"lio": {"look": {"hair": "bowl", "hair_color": "2b1d14", "skin": "9b6a4f", "eye": "round", "eye_color": "3a2a1c", "build": -0.6,
		"muscle": -0.5, "mouth_smile": 0.8, "marking": "freckles", "marking_color": "643d2a"},
		"wear": ["apprentice_robe", "silk_undershirt", "soft_boot"],
		"dye": {"cloth": "b07a3a", "trim": "3a2a1a"}},
	"tessaly": {"f": true, "look": {"hair": "ponytail", "hair_color": "4a2f1d", "skin": "b27e62", "eye_color": "5a7a3a",
		"marking": "freckles", "marking_color": "80523a", "hands": 1.1, "cheeks": 0.2},
		"wear": ["padded_gambeson", "brigandine", "trackers_breeches", "wayfarer_boot", "wayfarers_knot"],
		"dye": {"cloth": "5a6a5a", "trim": "2a302a", "leather": "5a4030"}},
	"aurand": {"look": {"hair": "curly", "hair_color": "6b4423", "skin": "c8916d", "beard": "handlebar", "eye": "keen", "eye_color": "3f6fa8",
		"brow": "arched", "nose_long": 0.5, "build": -0.3},
		"wear": ["traveler_coat", "runeweave_vest", "scholars_breeches", "wayfarer_boot"],
		"dye": {"cloth": "2f5f5a", "trim": "1a2a2a", "leather": "5a3a28"}},
	"ilvena": {"f": true, "look": {"hair": "long", "hair_color": "6b4423", "hair_length": 0.7, "skin": "c8916d", "eye": "sleepy",
		"eye_color": "5a7a3a", "jaw_wide": 0.3, "mouth_smile": -0.6, "cheeks": -0.3},
		"wear": ["magister_robe", "soft_boot", "linen_hood"],
		"dye": {"cloth": "1e1c22", "trim": "121014"}},
	"thadric": {"look": {"hair": "tonsure", "hair_color": "4a2f1d", "beard": "full", "skin": "d9a585", "belly": 0.6, "brow": "bushy",
		"nose_size": 0.4, "ears_size": 0.5},
		"wear": ["sage_robe", "sage_leggings", "sage_boots", "bone_amulet"],
		"dye": {"cloth": "5a4a2a", "trim": "2a2014"}},
	"zerin": {"look": {"hair": "wild", "hair_color": "0f0c0b", "skin": "80523a", "beard": "chops", "stubble": 0.7, "eye_color": "3a2a1c",
		"cheeks": -0.8, "build": -0.6, "marking": "scar", "marking_color": "5a3020"},
		"wear": ["traveler_coat", "linen_trousers", "soft_boot"],
		"dye": {"cloth": "6a5a48", "trim": "3a3028", "leather": "4a3a2a"}},
	"veyra": {"f": true, "look": {"hair": "braids", "hair_color": "c9c9cf", "skin": "d9a585", "eye": "glowing", "eye_color": "8eeaff",
		"eye_glow": 0.7, "marking": "rites", "marking_color": "2f6f8c", "height": 0.97, "cheeks": -0.3},
		"wear": ["sage_robe", "runeweave_vest", "sage_boots", "spirit_bell", "sands_of_tempo"],
		"dye": {"cloth": "3a4a6a", "trim": "181e2e"}, "main": "gloamspire_staff"},
	"hollis": {"f": true, "look": {"hair": "topknot", "hair_color": "6b4423", "skin": "e8bfa2", "eye": "keen", "brow": "thin",
		"cheeks": 0.3, "belly": 0.3, "height": 0.98, "mouth_smile": 0.4},
		"wear": ["magister_robe", "silk_undershirt", "soft_boot", "gold_amulet"],
		"dye": {"cloth": "5a2a3a", "trim": "2a1418", "gold": "e0c080"}},
	"corvin": {"look": {"hair": "topknot", "hair_color": "0f0c0b", "skin": "c8916d", "beard": "moustache", "eye": "keen", "eye_color": "3a2a1c",
		"jaw_wide": 0.4, "muscle": 0.5, "marking": "scar", "marking_color": "6a3a2a"},
		"wear": ["brigandine", "padded_gambeson", "riveted_legplates", "warden_greave"],
		"dye": {"cloth": "1a1a1a", "trim": "0f0f10", "leather": "3a2a20", "metal": "c0c0c0"}, "main": "bastard_sword"},
	"elsbeth": {"f": true, "look": {"hair": "sidepart", "hair_color": "d4a853", "skin": "f3d3bd", "eye": "doe", "eye_color": "3f6fa8",
		"brow": "arched", "lips_full": 0.4, "lip_amount": 0.5, "lip_color": "b0306a", "build": -0.3},
		"wear": ["silk_undershirt", "magister_robe", "soft_boot", "gold_amulet", "silver_ring", "starcluster_ring"],
		"dye": {"cloth": "2a5a5a", "trim": "0f2a2a", "gold": "f0d090"}},
	"aldous": {"look": {"hair": "crop", "hair_color": "4a4a4a", "skin": "9b6a4f", "beard": "goatee", "beard_color": "6a6a6a", "eye": "round",
		"eye_color": "3a2a1c", "belly": 0.7, "mouth_smile": 1.0, "cheeks": 0.4, "nose_wide": 0.5, "height": 0.95},
		"wear": ["padded_gambeson", "traveler_coat", "scholars_breeches", "soft_boot", "phial_of_last_light", "rune_charm"],
		"dye": {"cloth": "4a6a3a", "trim": "2a3a20", "leather": "5a3a28"}},
	"wren": {"look": {"hair": "spiky", "hair_color": "b07a3a", "skin": "c8916d", "beard": "chops", "eye_color": "3a7a6a", "muscle": 0.4,
		"marking": "freckles", "marking_color": "80523a"},
		"wear": ["padded_gambeson", "brigandine", "trackers_breeches", "wayfarer_boot", "silk_glove"],
		"dye": {"cloth": "2a4a6a", "trim": "14223a", "leather": "5a3a28"}},
	"pip": {"look": {"hair": "curly", "hair_color": "c0491f", "skin": "f3d3bd", "eye": "round", "eye_color": "5a7a3a", "mouth_smile": 1.6,
		"ears_size": 0.8, "height": 0.9, "build": -0.6, "marking": "freckles", "marking_color": "c8916d"},
		"wear": ["traveler_coat", "silk_undershirt", "windrunner_leggings", "soft_boot", "windrider_feather"],
		"dye": {"cloth": "c89a2a", "trim": "5a2a7a", "leather": "6a4a30"}},
	"aldric": {"look": {"hair": "slick", "hair_color": "4a2f1d", "beard": "full", "skin": "d9a585", "eye": "keen", "eye_color": "3f6fa8",
		"jaw_wide": 0.7, "chin_long": 0.3, "muscle": 0.6, "height": 1.04, "brow": "straight"},
		"wear": ["warden_plate", "chain_shirt", "commander_cuisses", "warden_greave", "guardian_gauntlets"],
		"dye": {"cloth": "1f3f7a", "metal": "e0e6f0"}, "main": "runed_sword", "off": "warden_kite_shield"},
	"gideon": {"look": {"hair": "crop", "hair_color": "8a8a8e", "beard": "full", "beard_color": "8a8a8e", "skin": "b27e62", "marking": "scar",
		"marking_color": "6a3a2a", "brow_heavy": 0.8, "jaw_wide": 0.9, "muscle": 1.0, "build": 0.4, "height": 1.06},
		"wear": ["iron_hauberk", "padded_gambeson", "iron_cuisses", "iron_sabaton", "spiked_gauntlet"],
		"dye": {"cloth": "4a3a2a", "metal": "9a9a9a"}, "main": "titan_greatsword"},
	"maren": {"f": true, "look": {"hair": "ponytail", "hair_color": "2b1d14", "skin": "9b6a4f", "eye": "keen", "eye_color": "5a7a3a",
		"marking": "freckles", "marking_color": "643d2a", "build": -0.3},
		"wear": ["traveler_coat", "runeweave_vest", "arcanist_legwraps", "wayfarer_boot"],
		"dye": {"cloth": "3a5a4a", "trim": "1a2a22"}, "main": "storm_staff"},
	"sabine": {"f": true, "look": {"hair": "braids", "hair_color": "e6e6e8", "skin": "e8bfa2", "eye": "doe", "eye_color": "6f8fb8",
		"eye_glow": 0.3, "brow": "arched", "lip_amount": 0.3, "lip_color": "2a6a8a"},
		"wear": ["magister_robe", "silk_undershirt", "magister_silks", "soft_boot", "seers_circlet"],
		"dye": {"cloth": "6a8ab8", "trim": "1f2f4a"}, "main": "frost_staff"},
	"odo": {"look": {"hair": "sidepart", "hair_color": "8c5a2b", "skin": "d9a585", "beard": "moustache", "eye": "keen", "eye_color": "5a7a3a",
		"build": -0.2, "ears_point": 0.4},
		"wear": ["brigandine", "hide_leggings", "wayfarer_boot", "silk_glove"],
		"dye": {"cloth": "3a5a2a", "leather": "4a3a2a"}, "main": "winged_spear"},
	"yorick": {"look": {"hair": "long", "hair_color": "6b4423", "hair_length": 0.5, "beard": "long", "beard_length": 0.5, "skin": "b27e62",
		"eye": "sleepy", "brow": "bushy", "height": 1.03, "cheeks": -0.3},
		"wear": ["traveler_coat", "staghide_chaps", "wayfarer_boot"],
		"dye": {"cloth": "4a4a2a", "trim": "22220f", "leather": "5a3a28"}, "main": "warden_longbow"},
	"tamsin": {"f": true, "look": {"hair": "mohawk", "hair_color": "8c2f1a", "skin": "c8916d", "eye": "fierce", "eye_color": "7a5a2c",
		"marking": "stripes", "marking_color": "14100e", "muscle": 0.6},
		"wear": ["brigandine", "chain_shirt", "hide_leggings", "wayfarer_boot", "silk_glove"],
		"dye": {"cloth": "6a2a1a", "leather": "2a1e18"}, "main": "hand_axe", "off": "sigil_buckler"},
	"nell": {"f": true, "look": {"hair": "pigtails", "hair_color": "b07a3a", "skin": "f3d3bd", "eye": "round", "eye_color": "3f6fa8",
		"eye_size": 1.2, "mouth_smile": 0.8, "marking": "freckles", "marking_color": "c8916d", "height": 0.9, "build": -0.6},
		"wear": ["apprentice_robe", "silk_undershirt", "soft_boot"],
		"dye": {"cloth": "7a6aa8", "trim": "2a2440"}, "main": "bone_wand"},
	"hobb": {"look": {"hair": "bald", "stubble": 0.6, "beard": "chops", "hair_color": "4a2f1d", "skin": "e8bfa2", "belly": 1.6, "build": 1.0,
		"cheeks": 1.0, "mouth_smile": 0.6, "eye": "round", "nose_size": 0.8},
		"wear": ["padded_gambeson", "brigandine", "linen_trousers", "wayfarer_boot"],
		"dye": {"cloth": "7a6a4a", "trim": "3a3024", "leather": "5a3a28"}},
	"greta": {"f": true, "look": {"hair": "braids", "hair_color": "b07a3a", "skin": "e8bfa2", "muscle": 1.0, "build": 0.5, "hands": 1.2,
		"marking": "freckles", "marking_color": "80523a", "eye": "keen", "eye_color": "5b4a3a", "height": 1.0},
		"wear": ["brigandine", "silk_undershirt", "hide_leggings", "iron_sabaton", "iron_gauntlet"],
		"dye": {"leather": "3a2618", "cloth": "6a4a3a"}, "main": "smiths_warhammer"},
	"ottilie": {"f": true, "look": {"hair": "topknot", "hair_color": "4a2f1d", "skin": "80523a", "eye": "doe", "eye_color": "3a2a1c",
		"mouth_smile": 0.7, "cheeks": 0.4},
		"wear": ["sage_robe", "sage_leggings", "sage_boots", "verdant_leaf_charm"],
		"dye": {"cloth": "e8e2d2", "trim": "7a1a1a"}, "main": "willow_wand"},
	"bram": {"look": {"hair": "crop", "hair_color": "0f0c0b", "beard": "full", "skin": "643d2a", "eye": "fierce", "eye_color": "3a2a1c",
		"muscle": 0.8, "jaw_wide": 0.6, "height": 1.05, "marking": "scar", "marking_color": "3a2015"},
		"wear": ["iron_hauberk", "padded_gambeson", "mail_chausses", "iron_sabaton", "iron_gauntlet"],
		"dye": {"cloth": "1f3f7a", "metal": "b0b4bc"}, "main": "iron_longsword"},
	"sabeth": {"f": true, "look": {"hair": "sidepart", "hair_color": "0f0c0b", "skin": "d9a585", "eye": "cat", "eye_color": "7a5a2c",
		"brow": "thin", "lip_amount": 0.3},
		"wear": ["apprentice_robe", "silk_undershirt", "soft_boot"],
		"dye": {"cloth": "8a5a1a", "trim": "2a1a10"}},
	"ysolde": {"f": true, "look": {"hair": "long", "hair_color": "0f0c0b", "hair_length": 0.8, "skin": "b27e62", "eye": "keen",
		"eye_color": "7a4aa8", "brow": "arched", "lip_amount": 0.4, "lip_color": "7a2a3a"},
		"wear": ["magister_robe", "runeweave_vest", "soft_boot", "sigil_ring", "twinmoon_band", "watchers_eye"],
		"dye": {"cloth": "4a2a6a", "trim": "1a1028", "gold": "e0c080"}},
	"anselm": {"look": {"hair": "bald", "beard": "long", "beard_color": "e6e6e8", "beard_length": 0.8, "skin": "d9a585", "eye": "sleepy",
		"brow": "bushy", "brow_color": "e6e6e8", "nose_size": 0.7, "height": 0.92, "cheeks": -0.4},
		"wear": ["sage_robe", "runeweave_vest", "sage_boots", "silver_ring"],
		"dye": {"cloth": "6a4a3a", "trim": "2a1e18"}},
	"dagna": {"f": true, "look": {"hair": "braids", "hair_color": "8c2f1a", "skin": "c8916d", "eye_color": "5a7a3a", "marking": "freckles",
		"marking_color": "643d2a", "muscle": 0.4, "build": 0.3, "height": 0.9, "hands": 1.15},
		"wear": ["traveler_coat", "padded_gambeson", "trackers_breeches", "wayfarer_boot", "silk_glove"],
		"dye": {"cloth": "7a5a3a", "trim": "3a2a1a", "leather": "4a3426"}, "main": "woodcutter_hatchet"},
	"lape": {"look": {"hair": "long", "hair_color": "e6e6e8", "hair_length": 1.5, "beard": "long", "beard_color": "e6e6e8", "beard_length": 2.0,
		"skin": "c9b8a0", "eye": "glowing", "eye_color": "e0a020", "eye_glow": 0.6, "brow": "bushy", "brow_color": "e6e6e8", "brow_thick": 1.8,
		"ears_size": 1.0, "ears_point": 0.6, "nose_long": 1.0, "nose_size": 0.6, "height": 0.86, "head": 1.15, "build": -0.6},
		"wear": ["magister_robe", "runeweave_vest", "magister_silks", "soft_boot", "sunforged_medallion", "kingsguard_crown_ring"],
		"dye": {"cloth": "4a1a5a", "trim": "1a0e20", "gold": "f0d090"}, "main": "pilgrims_staff"},
	"paul_david": {"look": {"hair": "slick", "hair_color": "2b1d14", "beard": "full", "beard_color": "2b1d14", "skin": "c8916d", "eye": "keen",
		"eye_color": "3f6fa8", "jaw_wide": 0.5, "muscle": 0.4, "height": 1.03, "marking": "scar", "marking_color": "6a3a2a"},
		"wear": ["chain_shirt", "traveler_coat", "riveted_legplates", "wayfarer_boot", "silk_glove"],
		"dye": {"cloth": "2a4a8a", "trim": "151a2e", "leather": "3a2618"}},
	"ilsa": {"f": true, "look": {"hair": "braids", "hair_color": "6b4423", "skin": "b27e62", "eye_color": "3f6fa8", "marking": "freckles",
		"marking_color": "643d2a", "mouth_smile": 0.4, "height": 1.0},
		"wear": ["traveler_coat", "silk_undershirt", "trackers_breeches", "wayfarer_boot", "silver_ring"],
		"dye": {"cloth": "2a3a6a", "trim": "7a1a1a", "leather": "3a2618", "gold": "d0a050"}, "main": "saltmarsh_cutlass"},
	"terax": {"size": 1.15, "look": {"hair": "mohawk", "hair_color": "0f0c0b", "skin": "80523a", "eye": "keen", "eye_color": "3a2a1c",
		"marking": "scar", "marking_color": "5a3020", "muscle": 1.2, "build": 0.6, "jaw_wide": 0.8},
		"wear": ["guardian_plate", "chain_shirt", "guardian_cuisses", "guardian_greaves", "guardian_gauntlets"],
		"dye": {"metal": "6a9a84", "cloth": "1a3a2a", "gold": "e0c080"}, "main": "partisan"},
	"wirekeeper": {"f": true, "look": {"hair": "long", "hair_color": "e6e6e8", "skin": "d9a585", "eye": "round", "eye_color": "5b8a9a",
		"brow": "thin", "brow_color": "e6e6e8", "cheeks": -0.4, "height": 0.93},
		"wear": ["magister_robe", "runeweave_vest", "soft_boot", "seers_circlet", "star_pendant"],
		"dye": {"cloth": "7a2a20", "trim": "1a6a6a", "gold": "e0c080"}, "main": "stormglass_wand"},
	"dorrit": {"look": {"hair": "crop", "hair_color": "0f0c0b", "skin": "643d2a", "beard": "goatee", "eye": "keen", "eye_color": "3a2a1c",
		"muscle": 0.7, "marking": "rites", "marking_color": "e8e4da"},
		"wear": ["brigandine", "padded_gambeson", "hide_leggings", "wayfarer_boot"],
		"dye": {"cloth": "1e1c22", "leather": "2a1e18", "metal": "3a3a40"}, "main": "rune_cleaver"},
	"brisa": {"f": true, "look": {"hair": "long", "hair_color": "0f0c0b", "skin": "9b6a4f", "eye_color": "3a2a1c", "mouth_smile": 0.8,
		"lip_amount": 0.3, "lip_color": "8c3a3a"},
		"wear": ["apprentice_robe", "silk_undershirt", "soft_boot", "linen_hood", "verdant_leaf_charm"],
		"dye": {"cloth": "c06a2a", "trim": "2a6a5a"}},
	"ysenne": {"f": true, "look": {"hair": "topknot", "hair_color": "f0f0f0", "skin": "80523a", "eye": "sleepy", "eye_color": "3a2a1c",
		"brow": "bushy", "brow_color": "f0f0f0", "cheeks": -0.3, "height": 0.88, "mouth_smile": 0.5},
		"wear": ["sage_robe", "sage_leggings", "sage_boots", "bone_amulet"],
		"dye": {"cloth": "2a7a6a", "trim": "7a1a2a"}, "main": "pilgrims_staff"},
	"toma": {"look": {"hair": "crop", "hair_color": "0f0c0b", "skin": "80523a", "eye_color": "3a2a1c", "muscle": 0.6, "mouth_smile": 0.3},
		"wear": ["traveler_coat", "linen_trousers", "wayfarer_boot", "iron_gauntlet"],
		"dye": {"cloth": "d8ccb0", "trim": "2a6a5a", "leather": "4a3426"}, "main": "smiths_warhammer"},
	"caius": {"look": {"hair": "long", "hair_color": "c9c9cf", "skin": "9b6a4f", "beard": "goatee", "beard_color": "c9c9cf", "eye": "sleepy",
		"eye_color": "3a2a1c", "height": 0.95, "cheeks": -0.3},
		"wear": ["magister_robe", "runeweave_vest", "magister_silks", "soft_boot", "sunforged_medallion"],
		"dye": {"cloth": "8a1a2a", "trim": "1a6a5a", "gold": "e0c080"}, "main": "sunspire_staff"},
	"quillan": {"look": {"hair": "ponytail", "hair_color": "2b1d14", "skin": "9b6a4f", "eye": "keen", "eye_color": "3a2a1c", "build": -0.4,
		"marking": "stripes", "marking_color": "e8e4da"},
		"wear": ["brigandine", "hide_leggings", "wayfarer_boot", "silk_glove"],
		"dye": {"cloth": "5a6a4a", "leather": "3a2618"}, "main": "hunting_spear"},
	"sorrel": {"f": true, "look": {"hair": "ponytail", "hair_color": "4a2f1d", "skin": "80523a", "eye_color": "3a2a1c", "mouth_smile": 0.6,
		"cheeks": 0.3, "hands": 1.1},
		"wear": ["padded_gambeson", "brigandine", "linen_trousers", "wayfarer_boot"],
		"dye": {"cloth": "3a6a7a", "trim": "1a3038", "leather": "5a3a28"}, "main": "skinning_knife"},
}
## The same person in two places.
const ALIASES := {"ilsa_agdao": "ilsa"}

static func npc(id: StringName) -> Dictionary:
	var k := String(id)
	k = String(ALIASES.get(k, k))
	return NPCS.get(k, {})

# ---------------------------------------------------------------------------------------------------- monsters
const NOT_PEOPLE := ["aether_sentinel", "rune_golem", "magma_golem", "obsidian_golem", "clockwork_sentry", "astrarch", "nocthea",
	"sporeling", "rootweaver", "mycelid_hulk", "rot_mother", "briar_lasher", "thornmother", "broodhost", "oblivore", "barnacle_hulk",
	"mossback_idol", "arc_sentinel", "span_warden", "deathspan_colossus", "engine_heart", "gigas_spawn", "vein_mother", "jade_guardian"]
## Families from Zarael: every glow there is pure white (bh-029).
const ZARAEL := ["wiresick", "wirewright", "kharvenn", "jade", "gigas"]
## Height of each humanoid monster's own model (m, before its def.model_scale): the hero body is sized to match.
const OLD_HEIGHT := {"hollow_soldier": 1.84, "bonewarden": 1.97, "grave_archer": 1.9, "ashen_cultist": 1.77, "ashen_acolyte": 1.7,
	"ghoul_brute": 2.01, "shade_stalker": 1.8, "bandit_cutthroat": 1.76, "bandit_marksman": 1.75, "goblin_skulker": 1.13,
	"orc_reaver": 2.08, "ogre_crusher": 3.0, "boss_warden": 2.29, "necromancer": 2.05, "goblin_summoner": 1.31, "orc_shaman": 2.14,
	"frost_revenant": 2.42, "plague_bloater": 2.0, "bandit_bombardier": 1.78, "mire_troll": 2.81, "drowned_deckhand": 1.8,
	"brinecaller": 2.04, "bell_warden": 2.35, "cinder_imp": 1.09, "forge_thrall": 1.91, "forgemaster": 2.37, "rime_husk": 1.82,
	"barrow_jarl": 2.28, "winter_crown": 2.48, "astral_duelist": 1.94, "void_seer": 1.96, "gravecaller": 2.59, "riftcaller": 2.2,
	"mirage_weaver": 1.83, "bloodbinder": 1.9, "aegis_acolyte": 2.02, "storm_herald": 2.0, "mirror_knight": 2.23,
	"warband_chieftain": 3.46, "soulbound_twin": 1.95, "goblin_sapper": 1.26, "treasure_gremlin": 1.04, "kethrax": 2.0,
	"glyphbound_warrior": 2.24, "coil_shaman": 2.11, "wiresick_husk": 1.77, "chain_priest": 2.17, "chain_bearer": 2.82,
	"wire_leaper": 2.06, "leash_knight": 2.14, "leash_abbot": 3.63, "jade_sleeper": 1.83, "serpent_oracle": 2.2, "jade_king": 4.54,
	"stoker_thrall": 2.23, "shardcaster": 2.17, "vein_knight": 2.1}

## Each monster's own touches over its family's (look overrides, clothes, colours, what it holds).
const ENEMIES := {
	"hollow_soldier": {"wear": ["iron_hauberk", "mail_chausses", "iron_sabaton", "iron_helm"]},
	"bone_thrall": {"wear": ["padded_gambeson", "linen_trousers"], "dye": {"cloth": "4a4238"}},
	"forsaken_legionnaire": {"wear": ["iron_hauberk", "iron_cuisses", "iron_sabaton", "barbute_helm"], "dye": {"cloth": "3a1a1a", "metal": "6a5a50"}},
	"bonewarden": {"wear": ["warden_plate", "iron_cuisses", "iron_sabaton", "visored_greathelm"], "off": "tower_shield"},
	"forsaken_chainguard": {"wear": ["warden_plate", "mail_chausses", "warden_greave", "barbute_helm"], "off": "warden_kite_shield",
		"dye": {"cloth": "3a1a1a", "metal": "6a5a50"}},
	"grave_archer": {"wear": ["traveler_coat", "hide_leggings", "soft_boot", "linen_hood"]},
	"rime_husk": {"look": {"skin": "b8c8d8", "eye_color": "8eeaff"}, "wear": ["chain_shirt", "mail_chausses", "iron_sabaton"],
		"dye": {"cloth": "3a4a5a", "metal": "a8c8e0"}},
	"barrow_jarl": {"look": {"beard": "braided", "beard_color": "c0c8d0", "skin": "a8b8c8", "eye_color": "8eeaff", "muscle": 1.0, "build": 0.6},
		"wear": ["iron_hauberk", "padded_gambeson", "iron_cuisses", "iron_sabaton", "iron_gauntlet"], "off": "warden_kite_shield",
		"dye": {"cloth": "2a3a4a", "metal": "8aa0b8"}},
	"frost_revenant": {"look": {"skin": "b8c8d8", "eye_color": "8eeaff", "muscle": 1.2, "build": 0.8, "hands": 1.3},
		"wear": ["warden_plate", "chain_shirt", "warden_cuisses", "warden_greave", "iron_gauntlet"], "dye": {"cloth": "1f2f4a", "metal": "a8c8e0"}},
	"soulbound_twin": {"look": {"pattern": "spectral", "pattern_color": "8dbafa", "pattern_amount": 0.6},
		"wear": ["brigandine", "silk_undershirt", "veilstalker_leggings", "soft_boot"], "dye": {"cloth": "2a2a4a", "leather": "1a1a24"}},
	"necromancer": {"wear": ["magister_robe", "runeweave_vest", "soft_boot", "arcanist_cowl", "bone_amulet"], "dye": {"cloth": "1a1a1e", "trim": "3a1a3a"}},
	"gravecaller": {"wear": ["sage_robe", "sage_boots", "sage_hood", "bone_amulet"], "dye": {"cloth": "2a2a26", "trim": "121210"}},
	"ashen_cultist": {"wear": ["apprentice_robe", "soft_boot", "linen_hood"]},
	"ashen_acolyte": {"wear": ["sage_robe", "sage_boots", "sage_hood"], "dye": {"cloth": "5a5450", "trim": "8a1a1a"}},
	"mirage_weaver": {"f": true, "look": {"hair": "long", "marking": "band", "marking_color": "6a2a8a", "pattern": "spectral",
		"pattern_color": "bc93ff", "pattern_amount": 0.35}, "wear": ["silk_undershirt", "nightweave_leggings", "soft_boot", "silk_glove"],
		"dye": {"cloth": "3a2a5a", "trim": "1a1428"}},
	"mirror_image": {"f": true, "look": {"hair": "long", "pattern": "spectral", "pattern_color": "bc93ff", "pattern_amount": 0.9},
		"wear": ["silk_undershirt", "nightweave_leggings", "soft_boot"], "dye": {"cloth": "3a2a5a", "trim": "1a1428"}},
	"bloodbinder": {"look": {"marking": "rites", "marking_color": "8c1410", "eye_color": "c02a2a"},
		"wear": ["magister_robe", "silk_undershirt", "soft_boot", "arcanist_cowl"], "dye": {"cloth": "6a0f14", "trim": "1a0a0a"}},
	"aegis_acolyte": {"wear": ["guardian_plate", "silk_undershirt", "guardian_cuisses", "guardian_greaves", "seers_circlet"],
		"dye": {"cloth": "e8e2d2", "metal": "f0e0b0"}, "off": "guardian_aegis"},
	"storm_herald": {"look": {"eye": "glowing", "eye_color": "82baff", "eye_glow": 0.8},
		"wear": ["magister_robe", "runeweave_vest", "magister_silks", "soft_boot", "arcanist_cowl"], "dye": {"cloth": "233b69", "trim": "0f182e"}},
	"bandit_cutthroat": {"wear": ["brigandine", "cutpurse_trousers", "soft_boot", "linen_hood"]},
	"bandit_marksman": {"wear": ["traveler_coat", "trackers_breeches", "wayfarer_boot", "silk_glove"]},
	"bandit_bombardier": {"look": {"belly": 1.0, "build": 0.6}, "wear": ["padded_gambeson", "hide_leggings", "wayfarer_boot", "iron_helm"],
		"off": "sigil_buckler"},
	"cellar_king": {"look": {"belly": 1.4, "build": 0.8, "beard": "full", "hair": "wild", "marking": "scar", "eye": "fierce"},
		"wear": ["brigandine", "silk_undershirt", "commander_cuisses", "warden_greave", "gold_amulet", "kingsguard_crown_ring", "seers_circlet"],
		"dye": {"cloth": "6a1a1a", "leather": "2a1a10", "gold": "f0c060"}, "off": "warden_kite_shield"},
	"goblin_skulker": {"wear": ["cutpurse_trousers", "silk_glove"]},
	"goblin_summoner": {"wear": ["apprentice_robe", "soft_boot", "bone_amulet"], "dye": {"cloth": "4a3a1a", "trim": "1a140a"}},
	"goblin_sapper": {"wear": ["padded_gambeson", "cutpurse_trousers", "iron_helm"]},
	"treasure_gremlin": {"look": {"belly": 1.6}, "wear": ["cutpurse_trousers", "gold_amulet", "gamblers_bones"]},
	"goblin_king": {"look": {"belly": 2.0, "build": 1.0}, "wear": ["magister_robe", "soft_boot", "gold_amulet", "seers_circlet", "kingsguard_crown_ring"],
		"dye": {"cloth": "6a1a5a", "trim": "1a0a14", "gold": "f0c060"}, "main": "gloamspire_staff"},
	"orc_reaver": {"wear": ["brigandine", "hide_leggings", "wayfarer_boot", "spiked_gauntlet"]},
	"orc_shaman": {"look": {"marking": "rites", "marking_color": "e8e4da"}, "wear": ["traveler_coat", "staghide_chaps", "wayfarer_boot", "bone_amulet", "wolfclaw_torc"],
		"dye": {"cloth": "5a3a1a", "trim": "2a1a0a"}},
	"warband_chieftain": {"wear": ["iron_hauberk", "padded_gambeson", "riveted_legplates", "iron_sabaton", "spiked_gauntlet", "wolfclaw_torc"],
		"dye": {"cloth": "5a1a10", "metal": "6a6058"}},
	"ironjaw": {"look": {"marking": "scar", "marking_color": "3a2a10", "jaw_wide": 1.5},
		"wear": ["warden_plate", "chain_shirt", "warden_cuisses", "warden_greave", "spiked_gauntlet", "visored_greathelm", "wolfclaw_torc"],
		"dye": {"cloth": "3a0f0a", "metal": "5a5048"}},
	"ogre_crusher": {"wear": ["hide_leggings", "spiked_gauntlet", "wolfclaw_torc"]},
	"mire_troll": {"wear": ["staghide_chaps"]},
	"ghoul_brute": {"wear": ["linen_trousers"], "dye": {"cloth": "3a3a30"}},
	"shade_stalker": {"look": {"skin": "2a2632", "pattern": "spectral", "pattern_color": "8a5ad0", "pattern_amount": 0.7, "eye_color": "c397ff",
		"hands": 1.2, "muscle": 0.2}, "wear": ["silk_undershirt", "nightweave_leggings", "silk_glove", "linen_hood"],
		"dye": {"cloth": "14101c", "trim": "0a080e", "inner": "201a2a", "legs": "100c16"}},
	"plague_bloater": {"wear": ["linen_trousers", "linen_hood"], "dye": {"cloth": "5a5a3a"}},
	"drowned_deckhand": {"wear": ["silk_undershirt", "linen_trousers"]},
	"brinecaller": {"wear": ["sage_robe", "sage_boots", "tidecaller_moonstone"], "dye": {"cloth": "205963", "trim": "0f2a30"}},
	"cinder_imp": {"wear": []},
	"forge_thrall": {"wear": ["brigandine", "hide_leggings", "iron_sabaton", "iron_gauntlet", "barbute_helm"], "off": "tower_shield"},
	"astral_duelist": {"f": true, "wear": ["brigandine", "silk_undershirt", "aethersilk_trousers", "soft_boot", "silk_glove"],
		"dye": {"cloth": "25334f", "leather": "1a2030", "metal": "d3d8ff"}},
	"void_seer": {"wear": ["magister_robe", "runeweave_vest", "soft_boot", "arcanist_cowl", "watchers_eye"], "dye": {"cloth": "2a1a4a", "trim": "0f0a1a"}},
	"riftcaller": {"f": true, "wear": ["sage_robe", "sage_leggings", "sage_boots", "seers_circlet"], "dye": {"cloth": "41335e", "trim": "1a1428"}},
	"mirror_knight": {"wear": ["guardian_plate", "chain_shirt", "guardian_cuisses", "guardian_greaves", "guardian_gauntlets", "guardian_helm"],
		"dye": {"metal": "f0f4ff", "cloth": "2a2a40"}, "off": "guardian_aegis"},
	"buried_sovereign": {"set": "obsidian_oath", "main": "oathkeeper_greatsword", "stance": "idle_2h"},
	"twin_regent": {"set": "eclipse_dancer", "main": "starfall_sabre"},
	"glyphbound_warrior": {"wear": ["brigandine", "hide_leggings", "wayfarer_boot"], "off": "sigil_buckler"},
	"coil_shaman": {"wear": ["apprentice_robe", "soft_boot", "rune_charm"], "dye": {"cloth": "6a6050", "trim": "2a2620"}},
	"wiresick_husk": {"wear": ["linen_trousers"], "dye": {"cloth": "5a5448"}},
	"wire_leaper": {"f": true, "wear": ["silk_undershirt", "veilstalker_leggings", "soft_boot"], "dye": {"cloth": "1f5a5a", "trim": "0f2a2a"}},
	"stoker_thrall": {"wear": ["brigandine", "hide_leggings", "iron_sabaton"], "dye": {"leather": "2a1e18"}},
	"shardcaster": {"wear": ["traveler_coat", "trackers_breeches", "wayfarer_boot", "silk_glove"], "dye": {"cloth": "23222b", "leather": "1a1418"}},
	"chain_priest": {"wear": ["magister_robe", "chain_shirt", "soft_boot", "arcanist_cowl"], "dye": {"cloth": "1a1a1e", "trim": "0a0a0c", "metal": "6a6a70"}},
	"chain_bearer": {"wear": ["iron_hauberk", "chain_shirt", "mail_chausses", "iron_sabaton", "spiked_gauntlet", "visored_greathelm"],
		"dye": {"cloth": "1a1a1e", "metal": "5a5a60"}},
	"leash_knight": {"wear": ["warden_plate", "chain_shirt", "warden_cuisses", "warden_greave", "iron_gauntlet", "visored_greathelm"],
		"dye": {"cloth": "1a1a1e", "metal": "4a4a52"}, "off": "tower_shield"},
	"leash_abbot": {"set": "ashfall_pilgrim", "main": "depth_voidcage_scepter"},
	"jade_sleeper": {"wear": ["silk_undershirt", "linen_trousers", "linen_hood", "silk_glove"], "dye": {"cloth": "c8bc98", "trim": "8a8068"}},
	"serpent_oracle": {"f": true, "wear": ["sage_robe", "sage_boots", "seers_circlet"], "dye": {"cloth": "194c40", "trim": "0a2a20", "gold": "c3a469"}},
	"jade_king": {"set": "serpent_veil", "main": "sunspire_staff"},
	"vein_knight": {"wear": ["warden_plate", "chain_shirt", "warden_cuisses", "warden_greave", "spiked_gauntlet", "visored_greathelm"],
		"dye": {"cloth": "4a0f14", "metal": "6a3a3a"}},
	"boss_warden": {"set": "obsidian_oath", "main": "gravewarden_axe", "stance": "idle_2h"},
	"ossuarch": {"set": "wailing_mistress"},
	"bell_warden": {"set": "sunken_crown", "main": "tideguard_trident"},
	"forgemaster": {"look": {"beard": "braided", "beard_color": "8c2f1a", "beard_length": 1.4, "height": 0.86, "build": 1.2, "muscle": 1.2},
		"set": "dragonforge", "main": "dragonspine_greatsword"},
	"solmara": {"f": true, "set": "ashfall_pilgrim", "main": "dawnspire_lance"},
	"winter_crown": {"f": true, "set": "winter_court", "main": "glaive"},
	"kethrax": {"set": "obsidian_oath", "look": {"eye": "glowing", "eye_color": "ff3020", "eye_glow": 1.0, "skin": "3a3438"}},
	"voltaric": {"set": "thunder_abbot"},
	"zephyrion": {"set": "gale_nomad", "main": "storm_staff"},
}

## What a monster holds when it has no weapon of its own: by the clip family of its attacks (first match wins).
const WEAPONS := {"sword": "iron_longsword", "axe": "bearded_axe", "gs": "rusted_claymore", "spear": "ash_spear", "dagger": "rondel_dagger",
	"dual": "rondel_dagger", "bow": "hunters_bow", "staff": "ashwood_staff", "wand": "bone_wand", "boss": "northman_greataxe"}
const FAMILY_WEAPONS := {
	"undead": {"sword": "gravewatch_longsword", "axe": "gravewarden_axe", "gs": "rusted_claymore", "staff": "depth_gravebell_wand"},
	"bandit": {"sword": "militia_shortsword", "dagger": "cutpurse_knife", "axe": "woodcutter_hatchet"},
	"cultist": {"sword": "riverguard_falchion", "dagger": "kukri", "staff": "gloamspire_staff", "dual": "moonshard_dagger"},
	"goblin": {"dagger": "skinning_knife", "staff": "knotwood_club", "axe": "woodcutter_hatchet"},
	"orc": {"axe": "raider_tomahawk", "gs": "tuskbreaker", "staff": "knotwood_club", "boss": "tuskbreaker"},
	"ogre": {"gs": "stumpsplitter", "boss": "stumpsplitter", "axe": "spiked_club"},
	"beast": {"axe": "spiked_club", "boss": "spiked_club"},
	"corrupted": {"axe": "bonecutter", "dagger": "bonebite", "boss": "spiked_club"},
	"drowned": {"spear": "corsair_harpoon", "staff": "deepwater_staff", "gs": "wavecrest_flamberge"},
	"infernal": {"axe": "emberheart_mace", "sword": "emberfang_dirk", "wand": "emberbrand_wand", "gs": "dragonspine_greatsword"},
	"aether": {"sword": "starfall_sabre", "staff": "depth_orrery_starstaff", "dagger": "aether_stiletto"},
	"wiresick": {"axe": "rune_cleaver", "dagger": "kukri", "staff": "depth_prismcoil_wand", "wand": "stormglass_wand"},
	"kharvenn": {"gs": "executioner_blade", "axe": "morning_star", "staff": "depth_voidcage_scepter"},
	"jade": {"axe": "crescent_axe", "staff": "depth_thornseed_branchstaff"},
	"gigas": {"gs": "nightfall_greatsword"},
	"construct": {"sword": "kingsbane"},
}

static func enemy(def: EnemyDef) -> Dictionary:
	var id := String(def.id)
	if def.body_shape != &"humanoid" or NOT_PEOPLE.has(id):
		return {}
	var model := def.model.get_file().get_basename()
	if not OLD_HEIGHT.has(model):
		return {}
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("persona:" + id)
	var p := _family(String(def.family), rng)
	var own: Dictionary = ENEMIES.get(id, {})
	for k in own:
		if k == "look":
			var lk: Dictionary = p.get("look", {})
			lk.merge(own.look, true)
			p["look"] = lk
		elif k == "dye":
			var dy: Dictionary = p.get("dye", {})
			dy.merge(own.dye, true)
			p["dye"] = dy
		else:
			p[k] = own[k]
	if ZARAEL.has(String(def.family)):
		p["look"]["eye_color"] = "ffffff"
	if not p.has("main"):
		var w := weapon_for(def)
		if w != "":
			p["main"] = w
	if def.weapon != "":
		p.erase("main")          # its own weapon model (EnemyDef.weapon) is attached by the Enemy
	p["size"] = clampf(float(OLD_HEIGHT[model]) / 1.9, 0.55, 2.6)
	return p

## The weapon for a monster's attack clips (the first clip family that names a weapon).
static func weapon_for(def: EnemyDef) -> String:
	var fam: Dictionary = FAMILY_WEAPONS.get(String(def.family), {})
	for a in def.attacks:
		var an := String(a.get("anim", ""))
		var pre := an.get_slice("_", 0)
		if an.begins_with("shield_bash") or an.begins_with("cast") or an in ["war_cry", "taunt", "whirlwind", "leap_slam"]:
			continue
		if WEAPONS.has(pre):
			return String(fam.get(pre, WEAPONS[pre]))
	return ""

const HAIRS := ["shaved", "crop", "sidepart", "slick", "spiky", "long", "ponytail", "topknot", "braids", "curly", "wild", "bowl"]

## A family's look, clothes and colours, varied by the monster's own seed.
static func _family(family: String, rng: RandomNumberGenerator) -> Dictionary:
	var pick := func(list: Array) -> Variant: return list[rng.randi_range(0, list.size() - 1)]
	var lk := {"hair": pick.call(HAIRS), "hair_color": pick.call(HeroLook.HAIR_TONES.slice(0, 10)),
		"skin": pick.call(HeroLook.SKIN_TONES.slice(0, 10)), "eye_color": pick.call(HeroLook.EYE_TONES.slice(0, 8)),
		"jaw_wide": rng.randf_range(-0.3, 0.6), "nose_size": rng.randf_range(-0.3, 0.6), "brow_heavy": rng.randf_range(-0.2, 0.8),
		"cheeks": rng.randf_range(-0.5, 0.3), "stubble": rng.randf_range(0.0, 0.7)}
	var p := {"look": lk, "wear": [], "dye": {}}
	match family:
		"bandit":
			lk.merge({"beard": pick.call(["none", "goatee", "chops", "full", "moustache"]), "marking": pick.call(["none", "scar", "scar", "band"]),
				"marking_color": "4a2a20", "eye": pick.call(["fierce", "keen", "natural"])}, true)
			p.dye = {"cloth": pick.call(["5a2a1a", "4a3a2a", "3a2a2a", "6a4a2a"]), "trim": "1a1410", "leather": pick.call(["3a2618", "2a1e18", "4a3426"])}
		"undead":
			lk.merge({"skin": pick.call(["8a9488", "a0a49a", "7a8478", "9a9890"]), "hair": pick.call(["bald", "wild", "long", "shaved"]),
				"hair_color": pick.call(["8a8a8e", "c8c8c8", "4a4a44"]), "eye": "glowing", "eye_color": "8dfaf0", "eye_glow": 0.9,
				"brow": "none", "cheeks": -1.0, "build": -0.8, "muscle": -0.8, "pattern": "stone", "pattern_color": "3a3a34",
				"pattern_amount": 0.45, "stubble": 0.0, "mouth_smile": -1.0, "eyes_pop": -0.8}, true)
			p.dye = {"cloth": "3a3530", "trim": "1a1814", "leather": "2a2420", "metal": "7a6658"}
		"cultist":
			lk.merge({"marking": "rites", "marking_color": "8c1410", "eye": pick.call(["fierce", "sleepy", "keen"]), "brow": "thin",
				"hair": pick.call(["shaved", "bald", "tonsure", "long"])}, true)
			p.dye = {"cloth": "5a5450", "trim": "8a1a1a", "leather": "2a2020"}
		"corrupted":
			lk.merge({"skin": pick.call(["6a7a5a", "7a8a6a", "5a6a50"]), "hair": pick.call(["bald", "wild"]), "hair_color": "2a2a24",
				"eye": "glowing", "eye_color": "b0ff60", "eye_glow": 0.7, "brow": "none", "cheeks": -1.0, "muscle": 0.8, "hands": 1.5,
				"pattern": "spots", "pattern_color": "3a4a2a", "pattern_amount": 0.5, "stubble": 0.0, "mouth_smile": -1.2}, true)
			p.dye = {"cloth": "3a3a30"}
		"goblin":
			lk.merge({"skin": pick.call(["5f8f4e", "6a9a50", "4f7a40", "7a9a5a"]), "hair": pick.call(["mohawk", "bald", "wild", "topknot"]),
				"hair_color": pick.call(["0f0c0b", "2b1d14", "2f8f5a"]), "eye": "cat", "eye_color": "e0a020", "eye_size": 1.6, "ears_size": 1.8,
				"ears_point": 2.2, "ears_out": 1.4, "nose_long": 1.8, "nose_size": 0.7, "mouth_wide": 1.0, "mouth_smile": rng.randf_range(0.5, 1.6),
				"head": 1.4, "hands": 1.4, "feet": 1.5, "belly": 0.8, "brow": "single", "stubble": 0.0}, true)
			p.dye = {"cloth": "4a3a1a", "trim": "1a140a", "leather": "3a2a1a"}
		"orc":
			lk.merge({"skin": pick.call(["6a7a4a", "5f7a50", "7a8a5a", "5a6a40"]), "hair": pick.call(["mohawk", "topknot", "wild", "braids"]),
				"hair_color": "0f0c0b", "eye": "fierce", "eye_color": "c02a2a", "jaw_wide": 1.4, "brow_heavy": 1.8, "nose_wide": 1.2,
				"nose_up": 1.0, "ears_point": 1.2, "muscle": 1.4, "build": 1.0, "hands": 1.3, "brow": "bushy", "stubble": 0.0,
				"marking": pick.call(["none", "stripes", "scar"]), "marking_color": "14100e"}, true)
			p.dye = {"cloth": "4a2a1a", "trim": "1a0f0a", "leather": "2a1e14", "metal": "6a6058"}
		"ogre":
			lk.merge({"skin": pick.call(["7a6a4a", "6a6248"]), "hair": "bald", "belly": 2.0, "build": 1.8, "muscle": 1.0, "hands": 1.8,
				"feet": 1.5, "head": 0.85, "jaw_wide": 1.5, "brow_heavy": 2.0, "nose_size": 1.4, "ears_size": 0.8, "eye": "sleepy",
				"brow": "single", "stubble": 0.6}, true)
			p.dye = {"cloth": "5a4a30", "leather": "3a2a1a"}
		"beast":
			lk.merge({"skin": "4f6a50", "pattern": "camo", "pattern_color": "2a3a2a", "hair": "wild", "hair_color": "2a3a24",
				"ears_point": 2.0, "ears_size": 1.0, "nose_long": 2.2, "nose_size": 1.0, "hands": 2.0, "feet": 1.8, "muscle": 1.2,
				"build": 0.6, "eye": "cat", "eye_color": "e0a020", "brow": "bushy", "mouth_wide": 1.2, "stubble": 0.0}, true)
			p.dye = {"cloth": "3a3a24", "leather": "2a2a1a"}
		"drowned":
			lk.merge({"skin": pick.call(["7a8f98", "8a9ea8", "6a8088"]), "hair": pick.call(["long", "wild", "bald"]), "hair_color": "2a3a3a",
				"eye": "glowing", "eye_color": "68edd7", "eye_glow": 0.8, "pattern": "scales", "pattern_color": "3a5a5a", "pattern_amount": 0.4,
				"cheeks": -0.8, "brow": "none", "beard": pick.call(["none", "full", "long"]), "beard_color": "2a3a3a", "stubble": 0.0}, true)
			p.dye = {"cloth": pick.call(["2a3a5a", "4a5a6a", "3a4a4a"]), "trim": "14202a", "leather": "2a2a24", "metal": "6a8a80"}
		"infernal":
			lk.merge({"skin": pick.call(["8a2a1a", "6a2014", "5a3028"]), "pattern": "molten", "pattern_color": "ff632d", "pattern_amount": 0.7,
				"hair": pick.call(["bald", "spiky", "mohawk"]), "hair_color": "1a0a08", "eye": "glowing", "eye_color": "ff7445", "eye_glow": 1.0,
				"ears_point": 1.8, "brow": "straight", "brow_color": "1a0a08", "stubble": 0.0, "muscle": 0.8}, true)
			p.dye = {"cloth": "3a2a20", "leather": "1a1410", "metal": "4a4040"}
		"aether":
			lk.merge({"skin": pick.call(["c9c9cf", "b8bcd8", "a8b0c8"]), "pattern": "stars", "pattern_color": "a4b9ff", "pattern_amount": 0.8,
				"hair": pick.call(["long", "slick", "topknot"]), "hair_color": "e6e6e8", "eye": "glowing", "eye_color": "a4b9ff", "eye_glow": 0.9,
				"ears_point": 1.0, "brow": "arched", "stubble": 0.0, "build": -0.4}, true)
			p.dye = {"cloth": "25334f", "trim": "0f1424"}
		"wiresick":
			lk.merge({"skin": pick.call(["8a8070", "9a9080", "7a7060"]), "pattern": "stripes", "pattern_color": "e8e4da", "pattern_amount": 0.5,
				"pattern_scale": 1.6, "hair": pick.call(["shaved", "wild", "crop", "long"]), "hair_color": "2a2620", "eye": "glowing",
				"eye_glow": 0.8, "cheeks": -0.7, "brow": "thin", "marking": "rites", "marking_color": "e8e4da", "stubble": 0.2}, true)
			p.dye = {"cloth": "6a6050", "trim": "2a2620", "leather": "3a3028", "metal": "a8a8b0"}
		"kharvenn":
			lk.merge({"skin": pick.call(["c8916d", "9b6a4f", "e8bfa2"]), "hair": pick.call(["shaved", "tonsure", "bald"]), "eye": "fierce",
				"marking": "rites", "marking_color": "14100e", "brow": "straight", "jaw_wide": 0.8, "muscle": 0.8, "beard": pick.call(["none", "full", "braided"])}, true)
			p.dye = {"cloth": "1a1a1e", "trim": "0a0a0c", "leather": "1a1414", "metal": "5a5a60"}
		"jade":
			lk.merge({"skin": pick.call(["8aa890", "7a9a80", "9ab8a0"]), "pattern": "scales", "pattern_color": "2a5a40", "pattern_amount": 0.5,
				"hair": "bald", "eye": "cat", "eye_glow": 0.6, "brow": "none", "cheeks": -0.6, "stubble": 0.0}, true)
			p.dye = {"cloth": "194c40", "trim": "0a2a20", "gold": "c3a469"}
		"gigas":
			lk.merge({"skin": "8a3a3a", "pattern": "molten", "pattern_color": "ffffff", "pattern_amount": 0.4, "hair": "bald", "muscle": 1.3,
				"build": 0.8, "jaw_wide": 1.0, "brow_heavy": 1.4, "eye": "glowing", "eye_glow": 0.9, "brow": "none", "stubble": 0.0}, true)
			p.dye = {"cloth": "4a0f14", "metal": "6a3a3a"}
		"construct":
			lk.merge({"skin": "c8ccd6", "pattern": "metal", "pattern_color": "d0d4e0", "hair": "bald", "eye": "glowing", "eye_color": "a4b9ff",
				"eye_glow": 1.0, "brow": "none", "jaw_wide": 0.8, "stubble": 0.0}, true)
			p.dye = {"cloth": "2a2a40", "metal": "f0f4ff"}
	if family in ["bandit", "cultist", "kharvenn", "wiresick", "aether", "drowned"] and rng.randf() < 0.35:
		p["f"] = true
	return p

# ---------------------------------------------------------------------------------------------------- cutscene extras
## The old generic bodies cutscenes asked for by model: the Registry's sealers (mage.glb) and a knightly spirit.
const EXTRAS := {
	"mage": {"look": {"hair": "crop", "hair_color": "4a2f1d", "beard": "goatee", "eye": "keen"},
		"wear": ["magister_robe", "chain_shirt", "magister_silks", "soft_boot", "seers_circlet"],
		"dye": {"cloth": "e8e6f0", "trim": "2a4a8a", "gold": "d0d8f0"}},
	"knight": {"look": {"hair": "crop", "hair_color": "6b4423", "beard": "chops", "jaw_wide": 0.6},
		"wear": ["warden_plate", "padded_gambeson", "warden_cuisses", "warden_greave", "iron_gauntlet"],
		"dye": {"cloth": "36557a", "metal": "d0d8e8"}},
}

## A persona for a model a cutscene names ("hollow_soldier", "res://assets/characters/mage.glb" ...), or {}.
static func for_model(model: String) -> Dictionary:
	var id := model.get_file().get_basename() if model.begins_with("res://") else model
	if EXTRAS.has(id):
		return EXTRAS[id]
	if NPCS.has(id):
		return NPCS[id]
	var e := DB.enemy(StringName(id))
	if e != null:
		var p := enemy(e)
		if not p.is_empty():
			p["size"] = float(p.get("size", 1.0)) * e.model_scale
		return p
	return {}

# ---------------------------------------------------------------------------------------------------- portraits
## Where an NPC's ID portrait is baked (tests/tools/bake_portraits.tscn renders every persona in NPCS).
const PORTRAIT_DIR := "res://assets/ui/portraits/npc/"

static func portrait_path(id: StringName) -> String:
	if npc(id).is_empty():
		return ""
	var k := String(ALIASES.get(String(id), String(id)))
	var p := PORTRAIT_DIR + k + ".png"
	return p if ResourceLoader.exists(p) else ""
