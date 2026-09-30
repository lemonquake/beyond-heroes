class_name DataLeggings
## bh-024: the Leggings slot's catalogue. Twenty class leggings on the drop tables and in the merchants' stock (knights
## plate, mages silk, rangers hide, shadowblades dark leather; five of each from level 1 to 30), the leg pieces of the
## Aether Guardian and Starbound Sage sets, and eight named uniques. The four depth leg pieces live with their groups in
## DataDepthEquipment and the fifteen boss Legguards in DataBossSets.
##
## Every base has its own item model and 3D icon (tools/blender/items/item_gear.py `legs`) and its own worn model
## (tools/blender/hero/hero_wear_legs.py).

const F := StatModifier.Op.FLAT
const I := StatModifier.Op.INC

## [id, name, weight class, class, level, defense, requirements, implicit [[stat, op, value]...], flavor]
const ROWS := [
	# ---- Knight: plate over mail (heavy)
	[&"iron_cuisses", "Iron Cuisses", &"heavy", &"knight", 1, 6, {&"str": 10}, [[&"max_hp", F, 6.0]],
		"Plain thigh plates buckled over quilted hose. Every recruit's first good pair."],
	[&"mail_chausses", "Mail Chausses", &"heavy", &"knight", 6, 10, {&"str": 16}, [[&"max_hp", F, 12.0]],
		"Riveted mail from hip to ankle, laced at the back of the leg."],
	[&"riveted_legplates", "Riveted Legplates", &"heavy", &"knight", 12, 17, {&"str": 24}, [[&"knockback_res", F, 0.04]],
		"Cuisses and knee cops riveted to a leather harness. They ring like a bell when you kneel."],
	[&"warden_cuisses", "Warden Cuisses", &"heavy", &"knight", 18, 26, {&"str": 34}, [[&"status_res", F, 0.04]],
		"Gate-warden pattern: fluted plates, a winged knee cop, and a gold line down the shin."],
	[&"commander_cuisses", "Knight-Commander's Cuisses", &"heavy", &"knight", 30, 38, {&"str": 50},
		[[&"knockback_res", F, 0.06], [&"max_hp", F, 30.0]],
		"Issued to those who hold a line with their own body. Heavy, and meant to be."],
	# ---- Mage: silk and wool (cloth)
	[&"linen_trousers", "Linen Trousers", &"cloth", &"mage", 1, 2, {}, [[&"max_mana", F, 8.0]],
		"Loose linen, gathered at the ankle. Easy to walk in, easy to mend."],
	[&"scholars_breeches", "Scholar's Breeches", &"cloth", &"mage", 6, 4, {&"int": 14}, [[&"mana_regen", F, 0.3]],
		"Wool breeches with a scholar's sash. The knees are shiny from kneeling over books."],
	[&"arcanist_legwraps", "Arcanist Legwraps", &"cloth", &"mage", 12, 7, {&"int": 22}, [[&"cast_speed", I, 0.03]],
		"Navy silk bound in gold thread from knee to ankle, stitched with small warding runes."],
	[&"magister_silks", "Magister Silks", &"cloth", &"mage", 18, 11, {&"int": 32}, [[&"magic_damage", I, 0.05]],
		"Full-cut silk trousers under a hanging panel. A magister does not run, but could."],
	[&"aethersilk_trousers", "Aethersilk Trousers", &"cloth", &"mage", 30, 16, {&"int": 48},
		[[&"magic_damage", I, 0.07], [&"max_mana", F, 30.0]],
		"Woven with a thread of Aether that glows faintly when a spell is near."],
	# ---- Ranger: hide and leather (cloth weight)
	[&"hide_leggings", "Hide Leggings", &"cloth", &"ranger", 1, 3, {&"dex": 8}, [[&"evasion", F, 6.0]],
		"Soft hide, laced up the outside of the leg. Quiet in the undergrowth."],
	[&"trackers_breeches", "Tracker's Breeches", &"cloth", &"ranger", 6, 5, {&"dex": 16}, [[&"accuracy", F, 8.0]],
		"Reinforced at the knee for long hours crouched over a trail."],
	[&"staghide_chaps", "Stag-Hide Chaps", &"cloth", &"ranger", 12, 8, {&"dex": 24}, [[&"evasion", F, 16.0]],
		"Thick stag leather over wool trousers, belted at the hip. Briars give up first."],
	[&"longstrider_leggings", "Longstrider Leggings", &"cloth", &"ranger", 18, 12, {&"dex": 34}, [[&"move_speed", I, 0.03]],
		"Cut for the long stride of the Wardens' scouts, with a leather guard on each thigh."],
	[&"windrunner_leggings", "Windrunner Leggings", &"cloth", &"ranger", 30, 17, {&"dex": 48},
		[[&"projectile_damage", I, 0.05], [&"evasion", F, 30.0]],
		"Feather-stitched leather that seems to lean into the wind."],
	# ---- Shadowblade: dark leather and wraps (cloth weight)
	[&"cutpurse_trousers", "Cutpurse Trousers", &"cloth", &"shadowblade", 1, 3, {&"dex": 6, &"agi": 6}, [[&"evasion", F, 8.0]],
		"Dark, close-fitting and full of hidden pockets. Most of them empty. For now."],
	[&"nightweave_leggings", "Nightweave Leggings", &"cloth", &"shadowblade", 6, 5, {&"dex": 10, &"agi": 10}, [[&"crit_chance", F, 0.01]],
		"Black wool so tightly woven it swallows lamplight."],
	[&"silentstep_breeches", "Silent-Step Breeches", &"cloth", &"shadowblade", 12, 8, {&"dex": 14, &"agi": 14}, [[&"evasion", F, 18.0]],
		"Wrapped from knee to ankle so nothing flaps, rustles or catches."],
	[&"duskrunner_leggings", "Duskrunner Leggings", &"cloth", &"shadowblade", 18, 12, {&"dex": 20, &"agi": 20}, [[&"attack_speed", I, 0.03]],
		"Leather plates sewn into dark cloth, shaped to the leg like a second shadow."],
	[&"veilstalker_leggings", "Veilstalker Leggings", &"cloth", &"shadowblade", 30, 17, {&"dex": 28, &"agi": 28},
		[[&"crit_damage", F, 0.08], [&"evasion", F, 30.0]],
		"The last thing a mark hears is nothing at all."],
]

## Set pieces: [id, name, set, weight class, class, level, defense, requirements, implicit]
const SET_ROWS := [
	[&"guardian_cuisses", "Aether Guardian Cuisses", &"aether_guardian", &"heavy", &"knight", 8, 16.0, {&"str": 20},
		[[&"knockback_res", F, 0.05]]],
	[&"sage_leggings", "Starbound Sage Leggings", &"starbound_sage", &"cloth", &"mage", 8, 6.0, {&"int": 20},
		[[&"mana_regen", F, 0.5]]],
]

## Named uniques: [id, kind (display type), unique name, rarity, weight class, class, level, defense, requirements,
## power ids, extra implicit, lore]
const UNIQUES := [
	[&"u_rimewalkers", "Legplates", "Rimewalkers", BH.Rarity.MYTHICAL, &"heavy", &"knight", 10, 18.0, {&"str": 22},
		[&"m_frostguard"], [[&"res_ice", F, 0.10]],
		"Forged in the Rimeglass Barrow. Frost creeps up the blade of anyone who strikes the wearer."],
	[&"u_windswift_breeches", "Breeches", "Windswift", BH.Rarity.MYTHICAL, &"cloth", &"ranger", 10, 8.0, {&"dex": 22},
		[&"m_swiftness"], [[&"evasion", F, 14.0]],
		"A courier's breeches from the old coast road. After a dodge the wind keeps pushing."],
	[&"u_oathbound_cuisses", "Cuisses", "Oathbound", BH.Rarity.LEGENDARY, &"heavy", &"knight", 16, 28.0, {&"str": 32},
		[&"valorous"], [[&"max_hp", F, 25.0]],
		"Every knight who wore them swore never to kneel. The knee cops were never scratched."],
	[&"u_echoing_legplates", "Legplates", "Echoing Bastion", BH.Rarity.LEGENDARY, &"heavy", &"knight", 20, 32.0, {&"str": 38},
		[&"echoing_guard"], [[&"block_strength", F, 0.05]],
		"Hollow steel tuned like a bell. A blocked blow rings out through the ground."],
	[&"u_stillwater_silks", "Silks", "Stillwater", BH.Rarity.LEGENDARY, &"cloth", &"mage", 14, 11.0, {&"int": 28},
		[&"stillwater"], [[&"max_mana", F, 25.0]],
		"Worn by the drowned chapel's monks for their long, motionless vigils."],
	[&"u_bloodrunner", "Leggings", "Bloodrunner", BH.Rarity.LEGENDARY, &"cloth", &"shadowblade", 16, 12.0, {&"dex": 18, &"agi": 18},
		[&"bloodthirst"], [[&"crit_chance", F, 0.015]],
		"Dyed three times, and never with anything as honest as madder."],
	[&"u_stormstriders", "Leggings", "Stormstriders", BH.Rarity.AETHER, &"cloth", &"ranger", 14, 12.0, {&"dex": 28},
		[&"stormstride"], [[&"move_speed", I, 0.04]],
		"Stitched with thread spun from a lightning-struck oak. They crackle when you run."],
	[&"u_riftwalker_legwraps", "Legwraps", "Riftwalker", BH.Rarity.AETHER, &"cloth", &"mage", 18, 12.0, {&"int": 34},
		[&"a_blink_nova"], [[&"cast_speed", I, 0.04]],
		"Wrapped around the legs of a mage who blinked once too often and left the cold behind."],
]

static func _mods(rows: Array) -> Array:
	var out := []
	for m in rows:
		out.append(StatModifier.new(m[0], m[1], float(m[2])))
	return out

static func bases() -> Array:
	var out := []
	for r in ROWS:
		var tier := 1 if r[4] < 6 else (2 if r[4] < 18 else 3)
		var b := DataItems._b(r[0], r[1], &"leggings", "", {"level_req": r[4], "defense": float(r[5]), "weight_class": r[2],
			"requirements": r[6], "implicit": _mods(r[7]), "value": 10 + int(r[4]) * 3, "class_hint": r[3], "tier": tier,
			"flavor": r[8]})
		out.append(_finish(b))
	for r in SET_ROWS:
		var b := DataItems._b(r[0], r[1], &"leggings", "", {"level_req": r[5], "defense": float(r[6]), "weight_class": r[3],
			"requirements": r[7], "implicit": _mods(r[8]), "value": 55, "set_id": r[2], "class_hint": r[4], "drop_weight": 0,
			"tier": 3})
		out.append(_finish(b))
	for r in UNIQUES:
		var b := DataItems._b(r[0], r[1], &"leggings", "", {"unique_name": r[2], "fixed_rarity": r[3], "weight_class": r[4],
			"class_hint": r[5], "level_req": r[6], "defense": float(r[7]), "requirements": r[8], "fixed_powers": r[9],
			"implicit": _mods(r[10]), "lore": r[11], "value": 110 + int(r[6]) * 3, "drop_weight": 0, "tier": 3})
		out.append(_finish(b))
	return out

static func _finish(b: ItemBaseDef) -> ItemBaseDef:
	b.icon = DataItems.ICON3D % b.id
	b.model = ItemBaseDef.ITEM_MODEL % b.id
	b.weight = DataItems.default_weight(b)
	return b

## Every leggings base id this catalogue defines (tests, tools).
static func ids() -> Array:
	var out := []
	for t in [ROWS, SET_ROWS, UNIQUES]:
		for r in t:
			out.append(r[0])
	return out
